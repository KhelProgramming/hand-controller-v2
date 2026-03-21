from __future__ import annotations

import argparse
import json

from .config.settings import AppConfig, build_default_config, tuning_snapshot
from .runtime.state import RuntimeState


def build_boot_message(config: AppConfig, state: RuntimeState) -> str:
    return "\n".join(
        [
            "Hand Controller Rewrite",
            f"python_target={config.python_version}",
            f"camera={config.camera.width}x{config.camera.height}@{config.camera.index}",
            f"mode={state.mode.value}",
            f"control_enabled={state.control_enabled}",
            f"tuning={config.tuning_path or 'defaults'}",
            f"ml_enabled={config.ml.enabled}",
            "status=phase-6-ready",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vision-smoke",
        action="store_true",
        help="Run the Phase 2 camera + hand-tracking smoke test.",
    )
    parser.add_argument(
        "--mouse-smoke",
        action="store_true",
        help="Run the Phase 6 mouse smoke test with movement, clicks, and ML command integration.",
    )
    parser.add_argument(
        "--tuning",
        type=str,
        default=None,
        help="Optional path to a JSON tuning file. Defaults to tuning.local.json in the repo root if present.",
    )
    args = parser.parse_args()

    config = build_default_config(args.tuning)
    state = RuntimeState()

    if args.vision_smoke:
        from .runtime.vision_baseline import run_vision_smoke

        run_vision_smoke(config)
        return

    if args.mouse_smoke:
        from .runtime.mouse_smoke import run_mouse_smoke

        print(build_boot_message(config, state))
        print(json.dumps(tuning_snapshot(config), indent=2))
        run_mouse_smoke(config)
        return

    print(build_boot_message(config, state))
    print("hint=run with --vision-smoke or --mouse-smoke for live testing")


if __name__ == "__main__":
    main()
