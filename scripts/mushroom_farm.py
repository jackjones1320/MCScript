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

Row endpoints are detected by polling player Z position.

Camera / yaw conventions (Minecraft):
      0  = south  (+Z)
    -90  = east   (+X)
     90  = west   (-X)
    180  = north  (-Z)
    110  = default INITIAL_YAW (roughly south-east)

Camera rotation is achieved via rapid sequential:
    /tp @p ~ ~ ~ <yaw> <pitch>
which keeps the player at their current position while setting facing exactly.

Usage (in-game chat):
    \\mushroom_farm

Place this file in: minecraft/minescript/mushroom_farm.py
"""

from minescript import *
import sys
import time
import random

# ---------------------------------------------------------------------------
# Configuration  (tune these to your farm)
# ---------------------------------------------------------------------------

POLL     = 0.05    # seconds between position-poll iterations

Z_START  = -290.0  # z coordinate of the first row endpoint  (A-key, pass 1)
Z_END    =  290.0  # z coordinate of the second row endpoint (A-key, pass 2)

INITIAL_YAW  = 110.0  # starting yaw (110 ≈ south-east)
FARM_PITCH   =   0.0  # camera pitch while farming (0 = straight ahead)

# Turn randomisation ranges — both values are re-rolled fresh on every turn
TURN_STEPS_MIN    = 25    # fewest /tp steps allowed for a 180° turn
TURN_STEPS_MAX    = 60    # most   /tp steps allowed for a 180° turn
TURN_DURATION_MIN = 0.8   # fastest a turn can be  (seconds)
TURN_DURATION_MAX = 2.0   # slowest a turn can be  (seconds)

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
    rotation looks like a real player moving their mouse. Step count is
    re-rolled randomly on every call from [TURN_STEPS_MIN, TURN_STEPS_MAX].
    Per-step timing and pitch add further organic variation.
    Updates module-level current_yaw when done.
    """
    global current_yaw

    # Shortest-path yaw delta normalised to (-180, 180]
    delta = (end_yaw - start_yaw + 180) % 360 - 180

    # Both steps and delay are fully re-randomised each turn
    steps = random.randint(TURN_STEPS_MIN, TURN_STEPS_MAX)
    delay = duration / steps

    for i in range(steps + 1):
        t     = i / steps
        yaw   = start_yaw + delta * bezier_ease(t)
        pitch = FARM_PITCH + random.uniform(-1.5, 1.5)
        execute(f"/tp @p ~ ~ ~ {yaw:.2f} {pitch:.2f}")
        time.sleep(max(0.0, delay + random.uniform(-0.005, 0.005)))

    # Snap to exact target to eliminate floating-point drift
    execute(f"/tp @p ~ ~ ~ {end_yaw:.2f} {FARM_PITCH:.2f}")
    current_yaw = end_yaw


def walk_and_farm(target_z: float, going_negative: bool) -> None:
    """Strafe left (A key) while holding attack until target_z is reached.

    Polls player Z position each POLL interval and stops the moment the
    row endpoint is crossed. Periodically sends tiny pitch adjustments via
    /tp to mimic a human operator making micro aim corrections. Keys are
    always released in the finally block, even if an exception fires.
    """
    try:
        player_press_left(True)    # A key — strafe left
        player_press_attack(True)  # hold left-click to break mushrooms

        next_tweak = time.time() + random.uniform(0.25, 0.35)

        while True:
            z = player_position()[2]
            if going_negative     and z <= target_z: break
            if not going_negative and z >= target_z: break

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
    between Z_START and Z_END without ever switching strafe keys.
    Turn duration and step count are re-randomised on every turn.
    """
    echo("=== Mushroom Farm: Starting ===")
    execute(f"/tp @p ~ ~ ~ {INITIAL_YAW:.2f} {FARM_PITCH:.2f}")
    time.sleep(0.3)  # let the server apply the initial rotation

    try:
        pass_count     = 0
        going_negative = True  # first pass: A moves toward Z_START (-Z)

        while True:
            pass_count += 1
            target_z        = Z_START if going_negative else Z_END
            direction_label = f"-Z → {target_z}" if going_negative else f"+Z → {target_z}"
            echo(f"Pass {pass_count} — yaw {current_yaw:.0f}° | strafing {direction_label}")

            walk_and_farm(target_z, going_negative)

            # Re-roll turn speed and smoothness fresh each time
            turn_duration = random.uniform(TURN_DURATION_MIN, TURN_DURATION_MAX)
            target_yaw    = (current_yaw + 180 + 180) % 360 - 180
            echo(f"Turning {turn_duration:.2f}s → yaw {target_yaw:.0f}°")
            smooth_turn(current_yaw, target_yaw, turn_duration)
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
    farm_row_loop()
