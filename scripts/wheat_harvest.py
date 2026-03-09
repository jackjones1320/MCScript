"""
Wheat Harvest Automation
========================
Automatically harvests wheat by walking 3 passes along the Z axis
(z -238 to z 238 and back), holding attack (left-click) the whole time.
After all passes, warps out of the garden.

Usage:
  1. Stand at the starting position (z ≈ -238) facing the +Z direction.
  2. Run this script.
  3. Click on the Minecraft window within STARTUP_DELAY seconds.
  4. The script takes over from there.

Adjust the config block below if your garden or walk speed differs.
"""

import pyautogui
import time

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

STARTUP_DELAY = 5          # seconds before automation starts (focus the window)
WALK_SPEED    = 4.3        # blocks per second (default survival walk speed)
Z_START       = -238       # starting Z coordinate
Z_END         =  238       # ending Z coordinate
PASSES        = 3          # total row passes to make
STRAFE_DURATION = 0.6      # seconds to hold the strafe key between passes
WARP_COMMAND  = "/warp garden"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS_DURATION = abs(Z_END - Z_START) / WALK_SPEED   # seconds per pass


def countdown(seconds: int) -> None:
    for i in range(seconds, 0, -1):
        print(f"  Starting in {i}...", end="\r", flush=True)
        time.sleep(1)
    print(" " * 30, end="\r")


def walk_pass(forward: bool, duration: float) -> None:
    """Hold move key + left-click for one full pass."""
    move_key = "w" if forward else "s"
    print(f"  {'Forward' if forward else 'Backward'} pass ({duration:.1f}s)...")
    pyautogui.keyDown(move_key)
    pyautogui.mouseDown(button="left")
    time.sleep(duration)
    pyautogui.mouseUp(button="left")
    pyautogui.keyUp(move_key)


def strafe_left(duration: float) -> None:
    """Shift one row to the left between passes."""
    print(f"  Strafing left ({duration}s)...")
    pyautogui.keyDown("a")
    time.sleep(duration)
    pyautogui.keyUp("a")


def warp(command: str) -> None:
    """Open chat and run a warp command."""
    print(f"  Warping: {command}")
    time.sleep(0.3)
    pyautogui.press("t")
    time.sleep(0.4)
    pyautogui.typewrite(command, interval=0.05)
    time.sleep(0.2)
    pyautogui.press("enter")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    pyautogui.FAILSAFE = True   # move mouse to top-left corner to abort

    print("=== Wheat Harvest Automation ===")
    print(f"Passes : {PASSES}")
    print(f"Z range: {Z_START} → {Z_END}  (~{PASS_DURATION:.0f}s per pass)")
    print(f"Warp   : {WARP_COMMAND}")
    print()
    print(f"Focus the Minecraft window now.")
    countdown(STARTUP_DELAY)
    print("Starting!\n")

    for pass_num in range(1, PASSES + 1):
        forward = (pass_num % 2 == 1)   # odd passes go forward, even go back
        print(f"Pass {pass_num}/{PASSES}")
        walk_pass(forward=forward, duration=PASS_DURATION)

        if pass_num < PASSES:
            strafe_left(duration=STRAFE_DURATION)

    print()
    warp(WARP_COMMAND)
    print("Done!")


if __name__ == "__main__":
    main()
