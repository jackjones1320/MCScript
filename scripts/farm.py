"""
Farm Automation
===============
Minescript-based farming automation. Harvests crops by strafing rows
with A/D, then pressing W briefly between passes to advance to the next row.

Player orientation: facing along the X axis.
  - A (strafe left)  → z decreases (-Z)
  - D (strafe right) → z increases (+Z)
  - W (forward)      → pressed only between passes to advance row_width in X

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
    z_start   = -238,   # lower z bound (A-key destination, odd passes)
    z_end     =  239,   # upper z bound (D-key destination, even passes / starting position)
    passes    = 3,
    row_width = 5,           # blocks to advance in X between passes
    warp      = "/warp garden",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wait_until_z(target_z: float, going_left: bool) -> None:
    """Poll player Z until the pass endpoint is reached.

    going_left (A key) → z decreases; stop when z <= target.
    not going_left (D key) → z increases; stop when z >= target.
    """
    while True:
        z = player_position()[2]
        if going_left     and z <= target_z: break
        if not going_left and z >= target_z: break
        time.sleep(POLL)


def wait_for_row_advance(start_x: float, row_width: int) -> None:
    """Wait until the player has moved row_width blocks in X.

    W is pressed before calling this and released after it returns.
    abs() handles either facing direction without needing to know which way X changes.
    """
    while True:
        x = player_position()[0]
        if abs(x - start_x) >= row_width - 0.5:
            break
        time.sleep(POLL)


# ---------------------------------------------------------------------------
# Crop routines
# ---------------------------------------------------------------------------

def farm_wheat(cfg: dict) -> None:
    echo("=== Farm: Wheat ===")
    echo(f"z {cfg['z_end']} \u2192 z {cfg['z_start']}  |  {cfg['passes']} passes  |  row width {cfg['row_width']}")

    player_press_attack(True)    # hold attack for the entire run

    try:
        for pass_num in range(1, cfg["passes"] + 1):
            # Odd passes: A key (z decreases to z_start); even passes: D key (z increases to z_end)
            going_left = (pass_num % 2 == 1)
            target_z   = cfg["z_start"] if going_left else cfg["z_end"]
            echo(f"Pass {pass_num}/{cfg['passes']} ({'A z-' if going_left else 'D z+'})")

            if going_left:
                player_press_left(True)
            else:
                player_press_right(True)

            wait_until_z(target_z, going_left)

            if going_left:
                player_press_left(False)
            else:
                player_press_right(False)

            # Press W only for the row advance between passes
            if pass_num < cfg["passes"]:
                start_x = player_position()[0]
                player_press_forward(True)
                wait_for_row_advance(start_x, cfg["row_width"])
                player_press_forward(False)

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
