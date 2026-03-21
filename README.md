# Hand Controller Rewrite

Clean rewrite of the hand-based mouse and keyboard controller.

This repo intentionally starts from a frozen contract instead of merging the two older codebases directly.

Current status:
- Phase 0 complete: gesture contract and architecture contract are frozen.
- Phase 1 complete: minimal runnable package skeleton exists.
- Phase 2 complete: camera wrapper, MediaPipe hand tracker, structured hand output, and a validated vision smoke runner.
- Confirmed locally by the user: left and right hands are both detected.
- Phase 3 complete: active-hand selection and palm-facing safety detection passed local validation.
- Phase 4 complete: stable mouse movement passed local validation on the user's machine.
- Phase 5 click/drag refactor code exists: tap-based left click, easier double-click behavior, down-triggered right click, hold-to-drag, and a JSON tuning override file.
- Phase 6 baseline code exists: MLP adapter for `toggle`, `hold`, `undo`, and `redo`, with artifact fallback to the existing `touch-v15` model files.

## Baseline
- Python 3.11
- MediaPipe for hand tracking
- Existing MLP artifacts can be reused later through an adapter layer
- Mouse clicks remain rule-based

## First principles for this rewrite
- Stable mouse movement is the highest priority.
- Clicking must stay accurate and predictable.
- The MLP only owns a small set of high-level commands.
- The keyboard flow will follow the cleaner design from codebase 1.
- Every phase must be testable before moving to the next one.

## Docs
- `docs/gesture-spec.md`
- `docs/architecture.md`
- `docs/phase-plan.md`

## Setup
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
pip install mediapipe==0.10.21 --no-deps
python -m hand_controller
```

The app automatically loads `tuning.local.json` from the repo root if it exists.
Edit that file to experiment with click thresholds and timing without changing Python code.
If you want a clean known-good starting point, use `tuning.recommended.json`.

If disk space is too tight for a fresh rewrite venv, you can temporarily reuse
an existing project venv that already has the stack installed. For example:

```powershell
& 'C:\Users\acer\school\self-study\programming\projects\computer-vision-mouse-control\touch-v15\.venv\Scripts\python.exe' -m hand_controller
```

## Phase 2 smoke run
```powershell
python -m hand_controller --vision-smoke
```

Press `q` to close the OpenCV preview window.

Phase 3 behavior now visible in that same smoke run:
- active controlling hand is highlighted
- palm-facing status is shown per hand
- top status line shows the selected active hand and its palm-facing gate

## Phase 4 mouse smoke run
Install the extra packages for real cursor movement:

```powershell
pip install -r requirements-phase4.txt
```

Then run:

```powershell
python -m hand_controller --mouse-smoke
```

What it does:
- uses the active hand selected in Phase 3
- allows movement only when the active hand is palm-facing
- moves the real cursor using relative movement
- adds rule-based thumb-index left click and thumb-middle right click
- treats quick thumb-index pinch-and-release as a left click
- makes double click easier by allowing the second click to fire as the second pinch begins
- triggers right click on middle-pinch down instead of waiting for release
- supports hold-to-drag after the configured left-hold threshold
- freezes cursor only before drag starts, so targeting stays stable without blocking drag
- shows pinch-state debug info on the preview window

## Click Tuning
The easiest way to experiment is to edit `tuning.local.json` and rerun `--mouse-smoke`.

Most useful fields:
- `left_pinch_threshold_px`
- `right_pinch_threshold_px`
- `double_click_interval`
- `double_click_assist_window`
- `click_cooldown`
- `left_hold_drag_seconds`
- `left_press_multiplier`
- `left_release_multiplier`
- `right_press_multiplier`
- `right_release_multiplier`

ML control fields live under the `ml` section:
- `confirm_frames`
- `toggle_hold_seconds`
- `toggle_cooldown`
- `shortcut_cooldown`
- `gate_min_p1`
- `gate_min_margin`

You can also point to another file explicitly:

```powershell
python -m hand_controller --mouse-smoke --tuning .\tuning.local.json
```

Recommended preset test:

```powershell
python -m hand_controller --mouse-smoke --tuning .\tuning.recommended.json
```

## Later-phase packages
When we reach ML integration and the desktop UI phases, install the heavier
packages separately:

```powershell
pip install -r requirements-later.txt
```

Phase 6 needs those later packages. If they are not installed yet, `--mouse-smoke`
will still run, but the ML overlay will show that ML is unavailable.

## Phase 6 ML behavior
When the ML artifacts and dependencies are available:
- `toggle` must be held briefly before it flips `control_enabled`
- `hold` freezes movement and disables rule-based clicks
- `undo` sends `Ctrl+Z`
- `redo` sends `Ctrl+Y`
- ignored MLP labels like `left_click` and `right_click` do not drive behavior

Artifact lookup order:
1. `hand-controller-rewrite/artifacts/`
2. fallback to `touch-v15/hand_controller/artifacts/`
