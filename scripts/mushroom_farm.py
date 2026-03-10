"""
Mushroom Farm Automation
========================
Minescript-based mushroom row farming. The player strafes left (A key)
across the row while holding attack to break mushrooms, performs a smooth
humanlike 180° turn, then strafes left again (which now moves the opposite
absolute direction because the facing changed). Repeats indefinitely.

Movement model:
    Player faces perpendicular to the mushroom row.
    A key strafes left relative to the player's facing.
    After a 180° turn, pressing A again moves back along the row.
    W key is never used — this is pure strafe movement.

Camera / yaw conventions (Minecraft):
      0  = south  (+Z)
    -90  = east   (+X)   ← default INITIAL_YAW; A strafes toward -Z
     90  = west   (-X)
    180  = north  (-Z)
    Pitch: positive = look down (30° targets mushroom block height).

Camera rotation is achieved via rapid sequential:
    /tp @p ~ ~ ~ <yaw> <pitch>
which keeps the player at their current position while setting facing exactly.

Usage (in-game chat):
    \\mushroom_farm
    \\mushroom_farm 10.0      (override WALK_DURATION to 10 seconds)

Place this file in: minecraft/minescript/mushroom_farm.py
"""

from minescript import *
import sys
import time
import random

# ---------------------------------------------------------------------------
# Configuration  (tune these to your farm)
# ---------------------------------------------------------------------------

POLL          = 0.05    # seconds between loop iterations
WALK_DURATION = 8.0     # seconds to strafe one row pass (tune to row length)
INITIAL_YAW   = -90.0   # starting yaw: -90 = east/+X, so A strafes toward -Z
FARM_PITCH    = 30.0    # downward pitch in degrees while farming
TURN_STEPS    = 40      # base number of /tp steps per 180° turn
TURN_DURATION = 1.2     # base seconds for a full 180° turn

# ---------------------------------------------------------------------------
# Module-level state  (shared across functions)
# ---------------------------------------------------------------------------

current_yaw = INITIAL_YAW

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def bezier_ease(t: float) -> float:
    """Symmetric quadratic ease-in-out.

    Maps t in [0, 1] to a smoothed value in [0, 1]: slow at both ends,
    fast in the middle. C1-continuous at t=0.5.
    """
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t


def wait_until_z(target_z: float, going_negative: bool) -> None:
    """Poll player Z until the row endpoint is reached.

    going_negative=True  (A key toward -Z): stop when z <= target_z.
    going_negative=False (A key toward +Z): stop when z >= target_z.
    """
    while True:
        z = player_position()[2]
        if going_negative     and z <= target_z: break
        if not going_negative and z >= target_z: break
        time.sleep(POLL)

# ---------------------------------------------------------------------------
# Core routines
# ---------------------------------------------------------------------------

def smooth_turn(start_yaw: float, end_yaw: float, duration: float) -> None:
    """Rotate camera smoothly from start_yaw to end_yaw using Bézier easing.

    Fires a sequence of /tp @p ~ ~ ~ <yaw> <pitch> commands so the
    rotation looks like a real player moving their mouse. Slight
    randomisation in step count, step timing, and pitch keeps the
    movement organic. Updates module-level current_yaw when done.
    """
    global current_yaw

    # Shortest-path yaw delta normalised to (-180, 180]
    delta = (end_yaw - start_yaw + 180) % 360 - 180

    steps        = TURN_STEPS + random.randint(-3, 3)
    actual_dur   = duration + random.uniform(-0.1, 0.1)
    delay        = actual_dur / steps

    for i in range(steps + 1):
        t   = i / steps
        yaw = start_yaw + delta * bezier_ease(t)
        pitch = FARM_PITCH + random.uniform(-1.5, 1.5)
        execute(f"/tp @p ~ ~ ~ {yaw:.2f} {pitch:.2f}")
        time.sleep(max(0.0, delay + random.uniform(-0.005, 0.005)))

    # Snap to the exact target to eliminate floating-point drift
    execute(f"/tp @p ~ ~ ~ {end_yaw:.2f} {FARM_PITCH:.2f}")
    current_yaw = end_yaw


def walk_and_farm(duration: float) -> None:
    """Strafe left (A key) while holding attack for the given duration.

    Periodically sends tiny pitch adjustments via /tp to mimic a human
    operator making micro aim corrections. Keys are always released in
    the finally block, even if an exception interrupts the loop.
    """
    actual_duration = duration + random.uniform(-0.2, 0.2)

    try:
        player_press_left(True)    # A key — strafe left
        player_press_attack(True)  # hold left-click to break mushrooms

        start      = time.time()
        next_tweak = start + random.uniform(0.25, 0.35)

        while time.time() - start < actual_duration:
            if time.time() >= next_tweak:
                pitch = FARM_PITCH + random.uniform(-2.0, 2.0)
                execute(f"/tp @p ~ ~ ~ {current_yaw:.2f} {pitch:.2f}")
                next_tweak = time.time() + random.uniform(0.25, 0.35)
            time.sleep(POLL)

    finally:
        player_press_attack(False)
        player_press_left(False)


def farm_row_loop() -> None:
    """Main farming loop: strafe across row, turn 180°, repeat forever.

    Always presses A after each turn. Because the 180° turn reverses
    which absolute direction A moves in, this naturally alternates
    between the two ends of the row without ever switching keys.
    """
    echo("=== Mushroom Farm: Starting ===")
    execute(f"/tp @p ~ ~ ~ {INITIAL_YAW:.2f} {FARM_PITCH:.2f}")
    time.sleep(0.3)  # let the server apply the initial rotation

    try:
        pass_count    = 0
        going_negative = True  # first pass: A moves toward lower Z

        while True:
            pass_count += 1
            direction_label = "-Z" if going_negative else "+Z"
            echo(f"Pass {pass_count} — yaw {current_yaw:.0f}° | strafing {direction_label}")

            walk_and_farm(WALK_DURATION)

            # 180° turn; after this, pressing A moves in the opposite
            # absolute direction, so the player heads back across the row
            target_yaw = (current_yaw + 180 + 180) % 360 - 180
            smooth_turn(current_yaw, target_yaw, TURN_DURATION)
            going_negative = not going_negative

            time.sleep(random.uniform(0.2, 0.5))  # brief realistic pause

    except KeyboardInterrupt:
        echo("Mushroom farm stopped.")
        # Belt-and-suspenders: release all movement keys defensively
        player_press_attack(False)
        player_press_forward(False)
        player_press_left(False)
        player_press_right(False)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        WALK_DURATION = float(sys.argv[1])
    farm_row_loop()
