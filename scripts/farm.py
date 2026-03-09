"""
Farm Automation
===============
Minescript-based farming automation. Harvests crops by strafing rows
while holding W (forward) and attack the entire time.

Player orientation: facing along the X axis.
  - A (strafe left)  → z increases (+Z)
  - D (strafe right) → z decreases (-Z)
  - W (forward)      → held continuously; advances player to next row
                       when A/D is released at end of each pass

Usage (in-game chat):
  \\farm wheat

Place this file in: minecraft/minescript/farm.py
"""

from minescript import *
import sys
import time

POLL = 0.05  # seconds between position checks during polling loops

# ---------------------------------------------------------------------------
# Crop configs
# ---------------------------------------------------------------------------

WHEAT = dict(
    z_start   = -238,
    z_end     =  238,
    passes    = 3,
    row_width = 5,           # blocks to advance in X between passes
    warp      = "/warp garden",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wait_until_z(target_z: float, going_left: bool) -> None:
    """Poll player Z until the pass endpoint is reached."""
    while True:
        z = player_position()[2]
        if going_left     and z >= target_z: break
        if not going_left and z <= target_z: break
        time.sleep(POLL)


def wait_for_row_advance(start_x: float, row_width: int) -> None:
    """Wait until W has walked the player row_width blocks in X."""
    while True:
        x = player_position()[0]
        if abs(x - start_x) >= row_width:
            break
        time.sleep(POLL)


# ---------------------------------------------------------------------------
# Crop routines
# ---------------------------------------------------------------------------

def farm_wheat(cfg: dict) -> None:
    echo("=== Farm: Wheat ===")
    echo(f"z {cfg['z_start']} \u2194 z {cfg['z_end']}  |  {cfg['passes']} passes  |  row width {cfg['row_width']}")

    player_press_forward(True)   # hold W for the entire run
    player_press_attack(True)    # hold attack for the entire run

    try:
        for pass_num in range(1, cfg["passes"] + 1):
            going_left = (pass_num % 2 == 1)   # odd → left (z+), even → right (z-)
            target_z   = cfg["z_end"] if going_left else cfg["z_start"]
            echo(f"Pass {pass_num}/{cfg['passes']} ({'left z+' if going_left else 'right z-'})")

            if going_left:
                player_press_left(True)
            else:
                player_press_right(True)

            wait_until_z(target_z, going_left)

            if going_left:
                player_press_left(False)
            else:
                player_press_right(False)

            # W is still held — garden advances player to next row
            if pass_num < cfg["passes"]:
                start_x = player_position()[0]
                wait_for_row_advance(start_x, cfg["row_width"])

    finally:
        # Always release keys, even if an error occurs
        player_press_attack(False)
        player_press_forward(False)
        player_press_left(False)
        player_press_right(False)

    execute(cfg["warp"])
    echo("Done!")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

CROPS = {
    "wheat": (farm_wheat, WHEAT),
}

crop = sys.argv[1] if len(sys.argv) > 1 else ""

if crop in CROPS:
    fn, cfg = CROPS[crop]
    fn(cfg)
else:
    known = ", ".join(CROPS.keys())
    echo(f"Unknown crop: '{crop}'. Usage: \\farm <crop>  (available: {known})")
