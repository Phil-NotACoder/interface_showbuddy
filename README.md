# Lighting Viz — Step 1 (Bootstrap)

**Purpose**: A lightweight Tkinter UI to visualize a small lighting rig, with future two-way OSC communication with Max 9 (READ & WRITE modes).  
This step provides the application skeleton and a smooth UI update loop (no I/O yet).

> This tool is for **composition/visualization**, not for live show control.

---

## What’s in Step 1 (Implemented)

- Tkinter window with:
  - a **FixturesView** placeholder (12 round fixtures in a grid),
  - a **status bar** showing FPS,
  - a **responsive layout** (resizes smoothly).
- Internal scheduler updating FPS every ~33ms.
- Basic project structure ready for next features.
- Templates for config files (`config/io.yml`, `config/fixtures.yml`).

There is **no OSC**, **no READ mode**, **no WRITE mode** yet (they arrive in Step 2).

---

## Project Structure (expected)