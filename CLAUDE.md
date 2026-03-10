# CLAUDE.md

## Project Overview

This repository contains Python automation scripts for farming tasks on **Hypixel SkyBlock** using the **Minescript mod** (not MineScript — the mod name is one word, all lowercase except the capital M).

The scripts simulate human-like player behavior while farming crops. Movement is designed to look natural while maintaining consistent harvesting efficiency.

**Core movement rule:** The player strafes sideways across rows using the A key. This keeps the camera oriented toward the crops throughout the pass and avoids the forward-drift that occurs when using W.

---

## Minescript API Reference

Scripts run inside Minecraft via the Minescript mod. The available API is imported with:

```python
from minescript import *
```

### Movement keys

```python
player_press_forward(bool)   # W key
player_press_back(bool)      # S key
player_press_left(bool)      # A key — primary strafe direction
player_press_right(bool)     # D key
player_press_attack(bool)    # left-click (break blocks / harvest)
```

### Player state

```python
x, y, z = player_position()  # returns (float, float, float)
```

### Commands and output

```python
execute("/command string")   # runs any in-game chat command
echo("message")              # prints to in-game console
```

### Camera control

Minescript has **no native yaw/pitch API**. Camera rotation is achieved by teleporting the player to their current position with an overridden facing angle:

```python
execute(f"/tp @p ~ ~ ~ {yaw:.2f} {pitch:.2f}")
```

`~ ~ ~` keeps the player in place. Only yaw and pitch change. Use `/tp @p` for single-player; use `/tp @s` if the executor context is the player themselves.

### Minecraft yaw conventions

| Yaw | Facing |
|-----|--------|
| 0   | South (+Z) |
| -90 | East (+X) |
| 90  | West (-X) |
| 180 / -180 | North (-Z) |

Pitch: positive values look down, negative look up. `0` is straight ahead.

---

## Current Project Structure

```
scripts/
    farm.py           # Wheat farming — strafes rows along Z axis
    mushroom_farm.py  # Mushroom farming — strafes Z=-290 to Z=290, smooth 180° turns
requirements.txt      # Empty — no external dependencies (Minescript is built-in)
```

Scripts are invoked in-game via `\script_name` in chat. They live in `minecraft/minescript/`.

---

## Intended Architecture (as the project grows)

```
scripts/
    farm.py
    mushroom_farm.py

utils/
    bezier.py       # Bézier easing helpers
    smoothing.py    # Timing jitter and randomisation utilities
    turning.py      # smooth_turn() implementation

config/
    farm_config.json
```

Keep modules small. Do not mix movement, farming, and utility logic in the same file.

---

## Movement Pattern

### Strafe direction — always use A key

The mushroom farm always presses **A** (strafe left). It does **not** alternate between A and D.

After a 180° turn, pressing A again moves the player in the **opposite absolute direction** — back along the row. The turn is what reverses direction, not the key.

```python
# Pass 1: facing yaw=110, A strafes toward -Z
player_press_left(True)
wait_until_z(Z_START, going_negative=True)
player_press_left(False)

# Turn 180° → now facing yaw=-70
smooth_turn(110, -70, duration)

# Pass 2: facing yaw=-70, A now strafes toward +Z
player_press_left(True)
wait_until_z(Z_END, going_negative=False)
player_press_left(False)
```

If A and D are alternated **without** turning, the player bounces back and forth without changing facing. Do not do this.

### Row endpoint detection

Use coordinate polling rather than time-based sleeps. Time-based movement drifts if the player is slowed or knocked.

```python
POLL = 0.05  # seconds between checks

def wait_until_z(target_z: float, going_negative: bool) -> None:
    while True:
        z = player_position()[2]
        if going_negative     and z <= target_z: break
        if not going_negative and z >= target_z: break
        time.sleep(POLL)
```

### Key release safety

Always wrap key presses in `try/finally` so keys are released even if an exception fires mid-pass.

```python
try:
    player_press_left(True)
    player_press_attack(True)
    wait_until_z(target_z, going_negative)
finally:
    player_press_attack(False)
    player_press_left(False)
```

---

## Turning Behavior

Turns must be smooth and curved — never instant yaw snaps.

### Implementation

Turns are implemented as a sequence of `/tp @p ~ ~ ~ <yaw> <pitch>` commands with Bézier-eased yaw interpolation:

```python
def bezier_ease(t: float) -> float:
    # Symmetric quadratic ease-in-out
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t

def smooth_turn(start_yaw, end_yaw, duration):
    delta = (end_yaw - start_yaw + 180) % 360 - 180  # shortest path
    steps = random.randint(TURN_STEPS_MIN, TURN_STEPS_MAX)
    delay = duration / steps
    for i in range(steps + 1):
        t   = i / steps
        yaw = start_yaw + delta * bezier_ease(t)
        execute(f"/tp @p ~ ~ ~ {yaw:.2f} {FARM_PITCH:.2f}")
        time.sleep(delay)
    execute(f"/tp @p ~ ~ ~ {end_yaw:.2f} {FARM_PITCH:.2f}")  # snap to exact target
```

### Randomisation ranges (mushroom_farm.py defaults)

```python
TURN_STEPS_MIN    = 25    # smoothest allowed (fewest /tp calls)
TURN_STEPS_MAX    = 60    # most granular
TURN_DURATION_MIN = 0.8   # fastest turn (seconds)
TURN_DURATION_MAX = 2.0   # slowest turn (seconds)
```

Both values are re-rolled fresh on every turn so no two turns are identical.

---

## Humanisation Layer

Small randomness should be applied to avoid perfectly mechanical patterns. Keep changes small enough that farm alignment is preserved.

```python
# Pitch micro-adjustment during strafing (~every 0.3s)
pitch = FARM_PITCH + random.uniform(-2.0, 2.0)
execute(f"/tp @p ~ ~ ~ {current_yaw:.2f} {pitch:.2f}")

# Per-step timing jitter during turns
time.sleep(delay + random.uniform(-0.005, 0.005))

# Pitch jitter during each turn step
pitch = FARM_PITCH + random.uniform(-1.5, 1.5)
```

Do not apply large random offsets to yaw during strafing — this will cause the player to face away from the crop row.

---

## Coding Conventions

- **Language:** Python (Minescript's embedded interpreter)
- **Imports:** `from minescript import *`, `import time`, `import random` — no external packages
- **Functions:** keep under ~60 lines; split if longer
- **Variable names:** descriptive (`going_negative`, `target_z`, `turn_duration`)
- **No libraries:** do not import `pyautogui`, `pynput`, `numpy`, or anything outside the standard library. Minescript cannot run them.
- **Global state:** use sparingly. A single `current_yaw` module variable is acceptable; avoid more.
- **Separation of concerns:** movement logic, farming logic, and humanisation should not be mixed into a single function.

---

## Typical Farm Loop

```python
while True:
    # Strafe across the row breaking crops
    walk_and_farm(target_z, going_negative)

    # Smooth 180° turn with randomised speed
    turn_duration = random.uniform(TURN_DURATION_MIN, TURN_DURATION_MAX)
    smooth_turn(current_yaw, (current_yaw + 180 + 180) % 360 - 180, turn_duration)
    going_negative = not going_negative

    time.sleep(random.uniform(0.2, 0.5))  # brief pause before next pass
```

---

## Safety Constraints

Current scripts handle:
- **Key release on error** — `try/finally` in `walk_and_farm` always releases A and attack
- **Manual interrupt** — `except KeyboardInterrupt` in `farm_row_loop` releases all four movement keys and prints a stop message

Not yet implemented (add when needed):
- Stall detection — if `player_position()` stops changing mid-pass, the player may be stuck
- Tool durability check — if the attack key is held but nothing breaks, tool may be broken
- Knockback recovery — detect if Z position jumps unexpectedly off the row path

---

## Performance Notes

- Use `time.sleep(POLL)` with `POLL = 0.05` (20 Hz) for position polling loops — do not busy-wait
- Avoid calling `execute()` or `player_position()` more than necessary in tight loops
- The script runs indefinitely; do not accumulate state (lists, counters) that grows unbounded

---

## Testing Checklist

Before committing new logic:

1. Run for at least 4 full farming cycles (2 complete back-and-forth passes)
2. Confirm strafing reaches both `Z_START` and `Z_END` accurately
3. Verify turns look smooth (no yaw snap visible in-game)
4. Ensure crops are harvested on both passes
5. Confirm all keys are released after `KeyboardInterrupt`
6. Confirm the player does not drift off the row over multiple cycles

---

## Common Pitfalls

- **Using W instead of A/D** — forward movement causes the player to drift perpendicular to the row
- **Alternating A/D without turning** — sends the player in the same absolute direction twice
- **Instant yaw assignment** — a single `/tp @p ~ ~ ~ new_yaw` looks like a snap; always interpolate
- **Ignoring yaw wrap-around** — normalise delta with `(delta + 180) % 360 - 180` to take the shortest path
- **Time-based row length** — player speed varies (potion effects, lag); use Z polling instead
- **Missing `global current_yaw`** — without the `global` declaration, assigning inside a function creates a local variable and the module state is not updated

---

## Instructions for Claude

When writing or modifying scripts:

1. Read this file before generating code.
2. Use only the Minescript API functions listed above — no external libraries.
3. Always use **A-key strafing** (not W-key forward movement) for row traversal.
4. Always use **Z-coordinate polling** (not time-based sleeps) to detect row endpoints.
5. Implement turns with **Bézier-eased `/tp` sequences**, never instant yaw assignments.
6. Wrap key presses in `try/finally`.
7. Do not rewrite existing modules unless the change is specifically requested.
8. Keep movement, farming, and utility logic in separate functions.

When this project adds new modules, update the **Current Project Structure** section above.
