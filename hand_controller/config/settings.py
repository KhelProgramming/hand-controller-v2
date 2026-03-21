from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TUNING_PATH = REPO_ROOT / "tuning.local.json"


@dataclass(slots=True, frozen=True)
class CameraConfig:
    index: int = 0
    width: int = 640
    height: int = 480


@dataclass(slots=True, frozen=True)
class MouseMotionConfig:
    sensitivity: float = 0.95
    smoothing_window: int = 2
    anchor_alpha: float = 1.0
    ema_alpha: float = 0.58
    wake_threshold_px: float = 3.20
    sleep_threshold_px: float = 1.25
    micro_jitter_px: float = 0.90
    gain_exponent: float = 1.02
    accel_start_px: float = 5.0
    fast_gain: float = 1.10
    spike_clamp_px: float = 48.0
    reanchor_distance_px: float = 140.0
    max_step_px: float = 30.0
    move_timeout: float = 0.35


@dataclass(slots=True, frozen=True)
class MouseClickConfig:
    left_pinch_threshold_px: float = 35.0
    left_press_multiplier: float = 0.72
    left_release_multiplier: float = 1.02
    right_pinch_threshold_px: float = 46.0
    right_press_multiplier: float = 0.88
    right_release_multiplier: float = 1.12
    click_cooldown: float = 0.08
    double_click_interval: float = 0.60
    double_click_assist_window: float = 0.38
    left_hold_drag_seconds: float = 0.38


@dataclass(slots=True, frozen=True)
class HandTrackerConfig:
    max_num_hands: int = 2
    min_detection_confidence: float = 0.7
    min_tracking_confidence: float = 0.7
    mirror_input: bool = True


@dataclass(slots=True, frozen=True)
class HandSelectorConfig:
    switch_margin: float = 0.18
    lost_grace_seconds: float = 0.30
    centroid_switch_px: float = 85.0


@dataclass(slots=True, frozen=True)
class MLConfig:
    enabled: bool = True
    accepted_action_labels: tuple[str, ...] = ("toggle", "hold", "undo", "redo")
    ignored_behavior_labels: tuple[str, ...] = ("left_click", "right_click", "idle")


@dataclass(slots=True, frozen=True)
class AppConfig:
    python_version: str
    camera: CameraConfig
    tracker: HandTrackerConfig
    selector: HandSelectorConfig
    mouse_motion: MouseMotionConfig
    mouse_click: MouseClickConfig
    ml: MLConfig
    tuning_path: str | None = None


def _replace_dataclass(config_obj: Any, overrides: dict[str, Any], *, section_name: str) -> Any:
    valid_field_names = {field.name for field in fields(config_obj)}
    unknown = sorted(set(overrides) - valid_field_names)
    if unknown:
        names = ", ".join(unknown)
        raise ValueError(f"Unknown fields in tuning section '{section_name}': {names}")
    return replace(config_obj, **overrides)


def _load_tuning_overrides(tuning_path: str | Path | None) -> tuple[dict[str, Any], str | None]:
    candidate = Path(tuning_path) if tuning_path else DEFAULT_TUNING_PATH
    candidate = candidate.expanduser().resolve()

    if not candidate.exists():
        return {}, None

    data = json.loads(candidate.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Tuning file must contain a top-level JSON object.")

    return data, str(candidate)


def _merge_config(base: AppConfig, overrides: dict[str, Any], tuning_path: str | None) -> AppConfig:
    remaining = dict(overrides)

    camera = base.camera
    tracker = base.tracker
    selector = base.selector
    mouse_motion = base.mouse_motion
    mouse_click = base.mouse_click
    ml = base.ml

    section_map = {
        "camera": camera,
        "tracker": tracker,
        "selector": selector,
        "mouse_motion": mouse_motion,
        "mouse_click": mouse_click,
        "ml": ml,
    }

    for section_name, section_obj in section_map.items():
        section_overrides = remaining.pop(section_name, None)
        if section_overrides is None:
            continue
        if not isinstance(section_overrides, dict):
            raise ValueError(f"Tuning section '{section_name}' must be a JSON object.")
        section_map[section_name] = _replace_dataclass(section_obj, section_overrides, section_name=section_name)

    if remaining:
        unknown = ", ".join(sorted(remaining))
        raise ValueError(f"Unknown top-level tuning sections: {unknown}")

    return AppConfig(
        python_version=base.python_version,
        camera=section_map["camera"],
        tracker=section_map["tracker"],
        selector=section_map["selector"],
        mouse_motion=section_map["mouse_motion"],
        mouse_click=section_map["mouse_click"],
        ml=section_map["ml"],
        tuning_path=tuning_path,
    )


def build_default_config(tuning_path: str | Path | None = None) -> AppConfig:
    base = AppConfig(
        python_version="3.11",
        camera=CameraConfig(),
        tracker=HandTrackerConfig(),
        selector=HandSelectorConfig(),
        mouse_motion=MouseMotionConfig(),
        mouse_click=MouseClickConfig(),
        ml=MLConfig(),
        tuning_path=None,
    )
    overrides, resolved_path = _load_tuning_overrides(tuning_path)
    return _merge_config(base, overrides, resolved_path)


def tuning_snapshot(config: AppConfig) -> dict[str, Any]:
    return {
        "tuning_path": config.tuning_path,
        "mouse_click": asdict(config.mouse_click),
        "mouse_motion": asdict(config.mouse_motion),
    }
