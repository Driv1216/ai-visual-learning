import json
import os
from pathlib import Path

from manim import *
from manim import ReplacementTransform
from scene_schema import SceneSpec
from actions import (
    ACCENT,
    BG_COLOR,
    ZONE_POSITIONS,
    build_object,
    make_manual_rule_force_indicator,
    make_links,
    place_in_zone,
    transition_in_for,
    transition_out_for,
)


COMPOSITE_ZONES = {
    "top",
    "full",
    "center_left",
    "center_mid_left",
    "center_mid_right",
    "center_right",
    "center_band",
    "center_left_center",
    "pattern_right_compact",
    "center_span",
}


def load_scene(scene_path: Path) -> SceneSpec:
    with scene_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return SceneSpec(**raw)


def load_timestamps(timestamp_path: Path):
    with timestamp_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        return raw

    if isinstance(raw, dict) and "timeline" in raw and isinstance(raw["timeline"], list):
        return raw["timeline"]

    raise ValueError(
        f"Unsupported timestamp format in {timestamp_path}. "
        f"Expected a list or a dict with a 'timeline' field."
    )


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_timestamp_path(scene: SceneSpec, repo_root: Path) -> Path:
    return (
        repo_root
        / "courses"
        / "machine-learning"
        / "generated"
        / "timestamps"
        / f"{scene.scene_id}.json"
    )


def get_default_run_time(step, segment_duration: float) -> float:
    if step.duration is not None:
        return step.duration

    action = step.action

    if action == "show_title":
        return min(1.15, max(0.8, segment_duration * 0.16))
    if action == "show_math":
        return min(1.0, max(0.7, segment_duration * 0.14))
    if action == "show_flow_diagram":
        return min(1.55, max(0.9, segment_duration * 0.18))
    if action == "show_function_flow":
        return min(1.25, max(0.8, segment_duration * 0.16))
    if action == "show_plot":
        return min(1.2, max(0.8, segment_duration * 0.16))
    if action == "show_training_loop":
        return min(1.15, max(0.75, segment_duration * 0.15))
    if action in {
        "show_model_core",
        "show_phase_labels",
        "show_training_examples",
        "show_prediction_error",
        "show_adjustment_loop",
        "show_repeat_learning",
        "show_inference_pass",
        "show_build_use_summary",
        "show_generalization_pattern",
    }:
        return min(1.0, max(0.6, segment_duration * 0.14))
    if action == "highlight_text":
        return min(0.95, max(0.6, segment_duration * 0.12))
    if action == "square_stage_sequence":
        return min(1.15, max(0.75, segment_duration * 0.14))
    if action == "transform_text":
        return min(1.2, max(0.8, segment_duration * 0.16))
    if action == "fade_out":
        return 0.7

    return min(1.0, max(0.65, segment_duration * 0.14))


class JsonDrivenScene(MovingCameraScene):
    def construct(self):
        self.camera.background_color = BG_COLOR

        scene_json = os.environ.get("AI_VL_SCENE_JSON")
        if not scene_json:
            raise ValueError(
                "Environment variable AI_VL_SCENE_JSON is not set.\n"
                "Set it before running manim."
            )

        scene_path = Path(scene_json).resolve()
        if not scene_path.exists():
            raise FileNotFoundError(f"Scene JSON not found: {scene_path}")

        repo_root = get_repo_root()
        scene = load_scene(scene_path)
        timestamp_path = get_timestamp_path(scene, repo_root)

        if not timestamp_path.exists():
            raise FileNotFoundError(f"Timestamp file not found: {timestamp_path}")

        timestamps = load_timestamps(timestamp_path)

        anchor_map = {item["id"]: item["start"] for item in timestamps}
        duration_map = {item["id"]: item["duration"] for item in timestamps}

        visual_steps = sorted(
            scene.visual_timeline,
            key=lambda step: anchor_map[step.anchor] + step.offset
        )

        current_time = 0.0

        active_objects = {zone: None for zone in ZONE_POSITIONS}
        object_registry = {}
        step_zone_map = {}

        default_frame_width = config.frame_width

        def register_object(step_id, zone_name, obj):
            if obj is None:
                return
            object_registry[step_id] = obj
            step_zone_map[step_id] = zone_name
            active_objects[zone_name] = obj

        def clear_step(step_id):
            obj = object_registry.pop(step_id, None)
            zone_name = step_zone_map.pop(step_id, None)
            if zone_name is not None and active_objects.get(zone_name) is obj:
                active_objects[zone_name] = None
            return obj

        def forget_object(obj):
            if obj is None:
                return
            for step_id, registered in list(object_registry.items()):
                if registered is obj:
                    clear_step(step_id)

        def clear_zone(zone_name):
            obj = active_objects.get(zone_name)
            active_objects[zone_name] = None
            if obj is not None:
                forget_object(obj)

        def unique_objects_from_ids(ids):
            seen = set()
            objects = []
            for ref_id in ids:
                obj = object_registry.get(ref_id)
                if obj is None:
                    continue
                key = id(obj)
                if key in seen:
                    continue
                seen.add(key)
                objects.append(obj)
            return objects

        def focus_camera_on(obj, scale_override=None):
            width = default_frame_width * (scale_override or 1.0)
            center = obj.get_center()
            if abs(center[1]) > 2.4:
                target = ORIGIN
            elif abs(center[0]) < 2.2:
                target = center
            else:
                target = ORIGIN
            return self.camera.frame.animate.move_to(target).set(width=width)

        def vector_from_param(value, default=ORIGIN):
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                z = value[2] if len(value) > 2 else 0
                return np.array([value[0], value[1], z], dtype=float)
            return default

        def register_under_existing_id(source_id, zone_name, obj):
            object_registry[source_id] = obj
            step_zone_map[source_id] = zone_name
            active_objects[zone_name] = obj

        def apply_manual_rule_display_color(obj, color):
            if hasattr(obj, "submobjects") and len(obj.submobjects) >= 2:
                card_shape = obj.submobjects[0]
                label = obj.submobjects[1]
                if hasattr(card_shape, "set_stroke"):
                    card_shape.set_stroke(color=color)
                if hasattr(label, "set_color"):
                    label.set_color(color)
            elif hasattr(obj, "set_color"):
                obj.set_color(color)

        def animate_manual_rule_display_color(obj, color):
            if hasattr(obj, "submobjects") and len(obj.submobjects) >= 2:
                card_shape = obj.submobjects[0]
                label = obj.submobjects[1]
                anims = []
                if hasattr(card_shape, "animate"):
                    anims.append(card_shape.animate.set_stroke(color=color))
                if hasattr(label, "animate"):
                    anims.append(label.animate.set_color(color))
                return anims
            return [obj.animate.set_color(color)]

        special_actions = {
            "hold",
            "highlight_group",
            "dim_group",
            "show_manual_rule_card",
            "show_manual_rule_ghosts",
            "transform_manual_rule_card",
            "mutate_manual_rule_card",
            "pulse_manual_rule_ghost",
            "transform_box_label",
            "transform_arrow",
            "camera_focus",
            "transform_group_to_examples",
            "transform_box_to_pattern",
            "show_links",
            "show_split_comparison",
            "animate_step_sequence",
            "highlight_inference_side",
            "transform_split_to_clean_flow",
        }

        for idx, step in enumerate(visual_steps):
            scheduled_time = anchor_map[step.anchor] + step.offset
            wait_time = scheduled_time - current_time

            if wait_time > 0:
                self.wait(wait_time)
                current_time += wait_time

            segment_duration = duration_map[step.anchor]
            run_time = get_default_run_time(step, segment_duration)

            if step.action == "fade_out":
                zones_to_fade = step.params.get("zones", ["title", "center", "bottom", "left", "right"])
                anims = []

                for zone_name in zones_to_fade:
                    obj = active_objects.get(zone_name)
                    if obj is not None:
                        anims.append(FadeOut(obj))
                        clear_zone(zone_name)

                if anims:
                    self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=run_time)
                    current_time += run_time
                continue

            if step.action in special_actions:
                handled = False

                if step.action == "hold":
                    current_obj = active_objects.get(step.zone)
                    if current_obj is not None:
                        object_registry[step.id] = current_obj
                        step_zone_map[step.id] = step.zone
                    handled = True

                elif step.action in {"highlight_group", "highlight_inference_side"}:
                    ref_ids = step.params.get("content", [])
                    objs = unique_objects_from_ids(ref_ids)
                    if not objs and step.action == "highlight_inference_side":
                        full_obj = active_objects.get("full")
                        if full_obj is not None and hasattr(full_obj, "right_panel"):
                            objs = [full_obj.right_panel]
                    if objs:
                        scale_factor = step.params.get("pulse_scale", 1.03)
                        anims = [Indicate(obj, scale_factor=scale_factor, color=None) for obj in objs]
                        self.play(AnimationGroup(*anims, lag_ratio=0.08), run_time=run_time)
                        current_time += run_time
                    handled = True

                elif step.action == "dim_group":
                    objs = unique_objects_from_ids(step.params.get("content", []))
                    if objs:
                        target_opacity = step.params.get("target_opacity", 0.72)
                        self.play(
                            AnimationGroup(
                                *[obj.animate.set_opacity(target_opacity) for obj in objs],
                                lag_ratio=0.0,
                            ),
                            run_time=run_time,
                        )
                        current_time += run_time
                    handled = True

                elif step.action == "show_manual_rule_card":
                    merged_params = dict(step.params)
                    if isinstance(getattr(step, "content", None), str):
                        merged_params.setdefault("label", step.content)
                    elif isinstance(getattr(step, "content", None), dict):
                        merged_params.update(step.content)
                    if isinstance(getattr(step, "style", None), dict):
                        merged_params.update(step.style)

                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": merged_params,
                            "zone": step.zone,
                        }
                    )

                    replace_zone = step.replace
                    outgoing_anims = []
                    if replace_zone is not None:
                        existing = active_objects.get(replace_zone)
                        if existing is not None:
                            outgoing = transition_out_for(existing, step.transition_out or "fade")
                            if outgoing is not None:
                                outgoing_anims.append(outgoing)
                            clear_zone(replace_zone)

                    self.play(
                        AnimationGroup(*outgoing_anims, FadeIn(new_obj), lag_ratio=0.0),
                        run_time=run_time,
                    )
                    current_time += run_time
                    register_object(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "show_manual_rule_ghosts":
                    merged_params = dict(step.params)
                    if isinstance(getattr(step, "content", None), dict):
                        merged_params.update(step.content)
                    if isinstance(getattr(step, "style", None), dict):
                        merged_params.update(step.style)

                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": merged_params,
                            "zone": step.zone,
                        }
                    )

                    replace_zone = step.replace
                    outgoing_anims = []
                    if replace_zone is not None:
                        existing = active_objects.get(replace_zone)
                        if existing is not None:
                            outgoing = transition_out_for(existing, step.transition_out or "fade")
                            if outgoing is not None:
                                outgoing_anims.append(outgoing)
                            clear_zone(replace_zone)

                    self.play(
                        AnimationGroup(*outgoing_anims, FadeIn(new_obj), lag_ratio=0.0),
                        run_time=run_time,
                    )
                    current_time += run_time
                    register_object(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "transform_manual_rule_card":
                    source_id = step.params.get("source_id")
                    source_obj = object_registry.get(source_id)
                    if source_obj is None:
                        print(
                            f"[transform_manual_rule_card] WARNING: source_id={source_id} not found. Skipping."
                        )
                        handled = True
                        continue

                    source_zone = step_zone_map.get(source_id, step.zone)
                    new_params = dict(step.params)
                    new_params.pop("source_id", None)
                    source_anchor = getattr(source_obj, "manual_anchor", source_obj.get_center())
                    source_scale = getattr(source_obj, "current_scale", 1.0)
                    new_params.setdefault("position", source_anchor.tolist())
                    new_params.setdefault("scale", source_scale)
                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": new_params,
                            "zone": source_zone,
                        }
                    )
                    new_obj.manual_anchor = source_anchor
                    new_obj.current_scale = source_scale

                    force_indicator = make_manual_rule_force_indicator(step.params, new_obj)
                    if force_indicator is not None:
                        self.play(ReplacementTransform(source_obj, new_obj), run_time=run_time * 0.78)
                        self.play(
                            Succession(
                                FadeIn(force_indicator),
                                FadeOut(force_indicator),
                            ),
                            run_time=run_time * 0.22,
                        )
                    else:
                        self.play(ReplacementTransform(source_obj, new_obj), run_time=run_time)
                    current_time += run_time
                    new_obj.manual_anchor = source_anchor.copy()

                    for ref_id, registered in list(object_registry.items()):
                        if registered is source_obj and ref_id != source_id:
                            object_registry.pop(ref_id, None)
                            step_zone_map.pop(ref_id, None)
                    register_under_existing_id(source_id, source_zone, new_obj)
                    object_registry[step.id] = new_obj
                    step_zone_map[step.id] = source_zone
                    handled = True

                elif step.action == "mutate_manual_rule_card":
                    source_id = step.params.get("source_id")
                    obj = object_registry.get(source_id)
                    if obj is None:
                        print(
                            f"[mutate_manual_rule_card] WARNING: source_id={source_id} not found. Skipping."
                        )
                        handled = True
                        continue

                    mode = step.params.get("mode", "dim")
                    if mode == "pulse":
                        peak_scale = step.params.get("peak_scale", 1.05)
                        current_scale = getattr(obj, "current_scale", 1.0)
                        settle_opacity = step.params.get("settle_opacity", step.params.get("opacity", 1.0))
                        peak_opacity = step.params.get("peak_opacity", settle_opacity)
                        anchor = getattr(obj, "manual_anchor", obj.get_center())
                        peak_obj = obj.copy()
                        if current_scale:
                            peak_obj.scale(peak_scale / current_scale, about_point=anchor)
                        peak_obj.set_opacity(peak_opacity)
                        if "peak_color" in step.params:
                            apply_manual_rule_display_color(peak_obj, step.params["peak_color"])
                        settle_obj = obj.copy()
                        settle_obj.set_opacity(settle_opacity)
                        if "settle_color" in step.params:
                            apply_manual_rule_display_color(settle_obj, step.params["settle_color"])
                        settle_obj.manual_anchor = anchor
                        self.play(
                            Succession(
                                Transform(obj, peak_obj),
                                Transform(obj, settle_obj),
                            ),
                            run_time=run_time,
                        )
                        obj.manual_anchor = anchor.copy()
                        obj.current_scale = current_scale
                        current_time += run_time
                        handled = True
                        continue

                    anim = obj.animate
                    color_anims = []
                    extra_anims = []
                    persistent_scale_factor = None
                    if mode == "dim":
                        if "target_opacity" in step.params:
                            anim = anim.set_opacity(step.params["target_opacity"])
                        if "target_color" in step.params:
                            color_anims = animate_manual_rule_display_color(obj, step.params["target_color"])
                        if "scale_factor" in step.params:
                            persistent_scale_factor = step.params["scale_factor"]
                            anchor = getattr(obj, "manual_anchor", obj.get_center())
                            anim = anim.scale(persistent_scale_factor, about_point=anchor)
                    elif mode == "drift":
                        current_anchor = getattr(obj, "manual_anchor", obj.get_center())
                        target_position = vector_from_param(
                            step.params.get("target_position"),
                            ZONE_POSITIONS.get(step.params.get("target_zone", step.zone), current_anchor),
                        )
                        anim = anim.move_to(target_position)
                        if "target_opacity" in step.params:
                            anim = anim.set_opacity(step.params["target_opacity"])
                    elif mode == "fade":
                        target_opacity = step.params.get("target_opacity", 0.03)
                        if "target_text_opacity" in step.params and hasattr(obj, "submobjects") and len(obj.submobjects) >= 2:
                            card_shape = obj.submobjects[0]
                            label = obj.submobjects[1]
                            anim = card_shape.animate.set_opacity(target_opacity)
                            extra_anims.append(label.animate.set_opacity(step.params["target_text_opacity"]))
                        else:
                            anim = anim.set_opacity(target_opacity)
                    else:
                        print(f"[mutate_manual_rule_card] WARNING: unsupported mode={mode}. Skipping.")
                        handled = True
                        continue

                    self.play(AnimationGroup(anim, *color_anims, *extra_anims, lag_ratio=0.0), run_time=run_time)
                    current_time += run_time

                    if mode == "drift":
                        obj.manual_anchor = target_position.copy()
                    if persistent_scale_factor is not None:
                        obj.current_scale = getattr(obj, "current_scale", 1.0) * persistent_scale_factor

                    if mode == "drift":
                        new_zone = step.params.get("target_zone")
                        if new_zone in active_objects:
                            old_zone = step_zone_map.get(source_id)
                            if old_zone is not None and active_objects.get(old_zone) is obj:
                                active_objects[old_zone] = None
                            active_objects[new_zone] = obj
                            step_zone_map[source_id] = new_zone
                    object_registry[step.id] = obj
                    step_zone_map[step.id] = step_zone_map.get(source_id, step.zone)
                    handled = True

                elif step.action == "pulse_manual_rule_ghost":
                    source_id = step.params.get("source_id")
                    ghost_key = step.params.get("ghost")
                    group = object_registry.get(source_id)
                    ghost_items = getattr(group, "ghost_items", {}) if group is not None else {}
                    ghost = ghost_items.get(ghost_key)
                    if ghost is None:
                        print(
                            f"[pulse_manual_rule_ghost] WARNING: source_id={source_id}, ghost={ghost_key} not found. Skipping."
                        )
                        handled = True
                        continue
                    base_opacity = step.params.get("base_opacity", 0.3)
                    peak_opacity = step.params.get("peak_opacity", 0.6)
                    self.play(
                        Succession(
                            ghost.animate.set_opacity(peak_opacity),
                            ghost.animate.set_opacity(base_opacity),
                        ),
                        run_time=run_time,
                    )
                    current_time += run_time
                    handled = True

                elif step.action in {"transform_box_label", "transform_arrow", "transform_box_to_pattern"}:
                    source_id = step.params.get("source_id")
                    source_obj = object_registry.get(source_id)
                    new_params = dict(step.params)
                    if isinstance(getattr(step, "content", None), str):
                        new_params.setdefault("text", step.content)
                        new_params.setdefault("label", step.content)
                    elif isinstance(getattr(step, "content", None), dict):
                        new_params.update(step.content)
                    if isinstance(getattr(step, "style", None), dict):
                        new_params.update(step.style)
                    if step.action == "transform_box_to_pattern":
                        new_params.update(step.params.get("style", {}))
                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": new_params,
                            "zone": step.zone,
                        }
                    )
                    if step.action == "transform_arrow":
                        if step.zone == "center_mid_left":
                            left_obj = active_objects.get("center_left")
                            right_obj = active_objects.get("center")
                        elif step.zone == "center_mid_right":
                            left_obj = active_objects.get("center")
                            right_obj = active_objects.get("center_right")
                        else:
                            left_obj = None
                            right_obj = None

                        if left_obj is not None and right_obj is not None:
                            start = left_obj.get_right() + RIGHT * 0.12
                            end = right_obj.get_left() + LEFT * 0.12
                            new_obj.put_start_and_end_on(start, end)
                        else:
                            place_in_zone(new_obj, step.zone)
                    obj_center = new_obj.get_center()
                    should_focus = step.camera_scale is not None and abs(obj_center[1]) <= 2.0
                    if source_obj is not None:
                        focus_parts = [ReplacementTransform(source_obj, new_obj)]
                        if should_focus:
                            focus_parts.append(focus_camera_on(new_obj, step.camera_scale))
                        self.play(
                            AnimationGroup(*focus_parts, lag_ratio=0.0),
                            run_time=run_time,
                        )
                        current_time += run_time
                        forget_object(source_obj)
                    else:
                        focus_parts = [transition_in_for(new_obj, step.transition_in)]
                        if should_focus:
                            focus_parts.append(focus_camera_on(new_obj, step.camera_scale))
                        self.play(
                            AnimationGroup(*focus_parts, lag_ratio=0.0),
                            run_time=run_time,
                        )
                        current_time += run_time
                    register_object(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "camera_focus":
                    objs = unique_objects_from_ids(step.params.get("content", []))
                    if objs:
                        focus_group = VGroup(*objs)
                        scale = step.params.get("scale", step.camera_scale or 1.0)
                        self.play(focus_camera_on(focus_group, scale), run_time=run_time)
                        current_time += run_time
                    handled = True

                elif step.action == "transform_group_to_examples":
                    content = step.params.get("content", {})
                    from_ids = content.get("from_ids", [])
                    new_params = dict(step.params)
                    new_params.update(content)
                    new_params.update(step.params.get("style", {}))
                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": new_params,
                            "zone": step.zone,
                        }
                    )
                    source_objs = unique_objects_from_ids(from_ids)
                    if source_objs:
                        source_group = VGroup(*source_objs)
                        self.play(
                            AnimationGroup(
                                ReplacementTransform(source_group, new_obj),
                                focus_camera_on(new_obj, step.camera_scale),
                                lag_ratio=0.0,
                            ),
                            run_time=run_time,
                        )
                        current_time += run_time
                        for obj in source_objs:
                            forget_object(obj)
                    else:
                        self.play(
                            AnimationGroup(
                                transition_in_for(new_obj, step.transition_in),
                                focus_camera_on(new_obj, step.camera_scale),
                                lag_ratio=0.0,
                            ),
                            run_time=run_time,
                        )
                        current_time += run_time
                    register_object(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "show_links":
                    content = step.params.get("content", {})
                    from_obj = object_registry.get(content.get("from"))
                    to_obj = object_registry.get(content.get("to"))
                    if from_obj is None or to_obj is None:
                        print(
                            f"[show_links] WARNING: from={content.get('from')} or to={content.get('to')} not found in registry. Skipping."
                        )
                        handled = True
                        continue
                    links_params = {**step.params, **step.params.get("style", {})}
                    new_obj = make_links(links_params, from_obj, to_obj)
                    self.play(transition_in_for(new_obj, step.transition_in), run_time=run_time)
                    current_time += run_time
                    register_object(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "show_split_comparison":
                    # FIX: merge step.content and step.style (not step.params.get("content"))
                    # because the JSON stores data in top-level content/style, not inside params.
                    new_params = dict(step.params)
                    if isinstance(getattr(step, "content", None), dict):
                        new_params.update(step.content)
                    elif isinstance(getattr(step, "content", None), str):
                        new_params.setdefault("text", step.content)
                    if isinstance(getattr(step, "style", None), dict):
                        new_params.update(step.style)

                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": new_params,
                            "zone": step.zone,
                        }
                    )
                    source_objs = [
                        obj
                        for zone_name, obj in active_objects.items()
                        if obj is not None and zone_name not in {"title", "top", "bottom", "full"}
                    ]
                    if source_objs:
                        self.play(
                            AnimationGroup(
                                ReplacementTransform(VGroup(*source_objs), new_obj),
                                focus_camera_on(new_obj, step.camera_scale),
                                lag_ratio=0.0,
                            ),
                            run_time=run_time,
                        )
                        current_time += run_time
                        for obj in source_objs:
                            forget_object(obj)
                    else:
                        self.play(
                            AnimationGroup(
                                transition_in_for(new_obj, step.transition_in),
                                focus_camera_on(new_obj, step.camera_scale),
                                lag_ratio=0.0,
                            ),
                            run_time=run_time,
                        )
                        current_time += run_time
                    register_object(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "animate_step_sequence":
                    split_obj = active_objects.get("full")
                    if split_obj is not None and hasattr(split_obj, "left_steps"):
                        steps = list(split_obj.left_steps)
                        # FIX: interleave step boxes and arrows so animation reads
                        # as Step1 → arrow → Step2 → arrow → Step3, not all boxes then all arrows.
                        anims = []
                        for i, mob in enumerate(steps):
                            anims.append(Indicate(mob, scale_factor=1.02, color=None))
                            if hasattr(split_obj, "left_arrows") and i < len(split_obj.left_arrows):
                                anims.append(
                                    Indicate(split_obj.left_arrows[i], scale_factor=1.0, color=ACCENT)
                                )
                        self.play(Succession(*anims), run_time=run_time)
                        current_time += run_time
                    handled = True

                elif step.action == "transform_split_to_clean_flow":
                    new_params = dict(step.params)
                    if isinstance(getattr(step, "content", None), str):
                        new_params.setdefault("text", step.content)
                        new_params.setdefault("label", step.content)
                    elif isinstance(getattr(step, "content", None), dict):
                        new_params.update(step.content)
                    if isinstance(getattr(step, "style", None), dict):
                        new_params.update(step.style)
                    new_params.update(step.params.get("content", {}))
                    new_params.update(step.params.get("style", {}))
                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": new_params,
                            "zone": step.zone,
                        }
                    )
                    source_obj = active_objects.get("full")
                    if source_obj is not None:
                        self.play(
                            AnimationGroup(
                                ReplacementTransform(source_obj, new_obj),
                                focus_camera_on(new_obj, step.camera_scale),
                                lag_ratio=0.0,
                            ),
                            run_time=run_time,
                        )
                        current_time += run_time
                        clear_zone("full")
                    else:
                        self.play(
                            AnimationGroup(
                                transition_in_for(new_obj, step.transition_in),
                                focus_camera_on(new_obj, step.camera_scale),
                                lag_ratio=0.0,
                            ),
                            run_time=run_time,
                        )
                        current_time += run_time
                    register_object(step.id, step.zone, new_obj)
                    handled = True

                if handled:
                    continue

            target_zone = step.zone

            merged_params = dict(step.params)
            if isinstance(getattr(step, "content", None), str):
                merged_params.setdefault("text", step.content)
                merged_params.setdefault("label", step.content)
                merged_params.setdefault("to", step.content)
            elif isinstance(getattr(step, "content", None), dict):
                merged_params.update(step.content)
            if isinstance(getattr(step, "style", None), dict):
                merged_params.update(step.style)

            new_obj = build_object(
                {
                    "id": step.id,
                    "anchor": step.anchor,
                    "action": step.action,
                    "params": merged_params,
                    "offset": step.offset,
                    "zone": step.zone,
                    "transition_in": step.transition_in,
                    "transition_out": step.transition_out,
                    "persist": step.persist,
                    "replace": step.replace,
                }
            )

            if step.action == "show_arrow":
                if step.zone == "center_mid_left":
                    left_obj = active_objects.get("center_left")
                    right_obj = active_objects.get("center")
                elif step.zone == "center_mid_right":
                    left_obj = active_objects.get("center")
                    right_obj = active_objects.get("center_right")
                else:
                    left_obj = None
                    right_obj = None

                if left_obj is not None and right_obj is not None:
                    start = left_obj.get_right() + RIGHT * 0.12
                    end = right_obj.get_left() + LEFT * 0.12
                    new_obj.put_start_and_end_on(start, end)
                else:
                    place_in_zone(new_obj, step.zone)

            outgoing_anims = []
            incoming_anim = None
            focus_anims = []

            replace_zone = step.replace
            if replace_zone is not None:
                existing = active_objects.get(replace_zone)
                if existing is not None:
                    if step.transition_in == "transform":
                        incoming_anim = ReplacementTransform(existing, new_obj)
                    else:
                        outgoing_anim = transition_out_for(existing, step.transition_out or "fade")
                        if outgoing_anim is not None:
                            outgoing_anims.append(outgoing_anim)
                    clear_zone(replace_zone)

            if incoming_anim is None and replace_zone is None:
                existing = active_objects.get(target_zone)
                if existing is not None:
                    outgoing_anim = transition_out_for(existing, step.transition_out or "fade")
                    if outgoing_anim is not None:
                        outgoing_anims.append(outgoing_anim)
                    clear_zone(target_zone)

            if incoming_anim is None:
                incoming_anim = transition_in_for(new_obj, step.transition_in)

            if target_zone not in COMPOSITE_ZONES:
                for zone_name, obj in active_objects.items():
                    if obj is not None and zone_name not in COMPOSITE_ZONES:
                        target_opacity = 1.0 if zone_name == target_zone else 0.25
                        focus_anims.append(obj.animate.set_opacity(target_opacity))
                focus_anims.append(new_obj.animate.set_opacity(1.0))

            camera_scale = step.camera_scale if step.camera_scale is not None else (0.9 if target_zone == "center" else 1.0)
            focus_anims.append(focus_camera_on(new_obj, camera_scale))

            self.play(
                AnimationGroup(*outgoing_anims, incoming_anim, *focus_anims, lag_ratio=0.0),
                run_time=run_time,
            )
            current_time += run_time
            register_object(step.id, target_zone, new_obj)

            if not step.persist:
                self.wait(0.1)
                current_time += 0.1
                obj = active_objects.get(target_zone)
                if obj is not None:
                    self.play(FadeOut(obj), run_time=0.4)
                    current_time += 0.4
                    clear_zone(target_zone)

        total_audio_duration = timestamps[-1]["end"]

        # keep last meaningful state on screen until the audio ends
        if total_audio_duration > current_time:
            self.wait(total_audio_duration - current_time)
            current_time = total_audio_duration


if __name__ == "__main__":
    print("This file is meant to be run through Manim.")
    print("Set AI_VL_SCENE_JSON, then run:")
    print("  manim --flush_cache --disable_caching -ql core/render_scene.py JsonDrivenScene")
