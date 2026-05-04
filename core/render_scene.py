import json
import os
from pathlib import Path

import numpy as np
from manim import *
from manim import ReplacementTransform
from scene_schema import SceneSpec
from actions import (
    ACCENT,
    BG_COLOR,
    TAXONOMY_COLORS,
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
    # Scene 5 zones — bypass generic focus-dimming so the rule card
    # is never auto-dimmed when ghosts or curve appear in adjacent zones
    "left-center",
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
        "show_taxonomy_field",
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

        def taxonomy_point_flash(dot, color, radius_scale=2.85, opacity=0.28):
            flash = Dot(dot.get_center(), radius=max(dot.width, dot.height) * 0.5 * radius_scale, color=color)
            flash.set_opacity(opacity)
            return flash

        def taxonomy_label_tick(dot, color):
            center = dot.get_center()
            size = 0.070
            tick = VMobject()
            tick.set_points_as_corners([
                center + np.array([-size * 0.55, -size * 0.05, 0]),
                center + np.array([-size * 0.15, -size * 0.42, 0]),
                center + np.array([size * 0.62, size * 0.48, 0]),
            ])
            tick.set_stroke(color=color, width=1.65, opacity=0.82)
            return tick

        def taxonomy_anchor_ring(dot, color):
            ring = Circle(radius=0.145, color=color, stroke_width=1.35)
            ring.move_to(dot.get_center())
            ring.set_stroke(color=color, opacity=0.46)
            ring.set_fill(opacity=0)
            return ring

        def taxonomy_anchor_burst(dot, color):
            center = dot.get_center()
            burst = VGroup(taxonomy_anchor_ring(dot, color))
            for angle in (35, 145, 235, 325):
                direction = np.array([np.cos(angle * DEGREES), np.sin(angle * DEGREES), 0])
                line = Line(center + direction * 0.100, center + direction * 0.185)
                line.set_stroke(color=color, width=1.05, opacity=0.38)
                burst.add(line)
            return burst

        def taxonomy_cluster_ghosts(params, held=False):
            clusters = params.get("clusters", [])
            ghosts = VGroup()
            for cluster_index, cluster in enumerate(clusters):
                center = vector_from_param(cluster.get("center"))
                radius = cluster.get("radius", 1.0) * 0.86
                phase = cluster_index * 0.73
                cloud_group = VGroup()
                for layer_index, scale in enumerate((1.0, 0.78, 0.55)):
                    points = []
                    steps = 22
                    for step_index in range(steps):
                        theta = TAU * step_index / steps
                        wobble = 1.0 + 0.13 * np.sin(3 * theta + phase + layer_index * 0.61) + 0.07 * np.cos(5 * theta - phase)
                        x_scale = 1.12 + 0.04 * np.sin(phase)
                        y_scale = 0.82 + 0.05 * np.cos(phase)
                        point = center + np.array([
                            np.cos(theta) * radius * scale * wobble * x_scale,
                            np.sin(theta) * radius * scale * wobble * y_scale,
                            0,
                        ])
                        points.append(point)

                    cloud = VMobject()
                    cloud.set_points_smoothly(points + [points[0]])
                    # These are soft luminance fields, not drawn cluster borders.
                    # Keep the stroke invisible so the viewer reads density, not blobs.
                    cloud.set_stroke(TAXONOMY_COLORS["cluster"], width=0.0, opacity=0.0)
                    cloud.set_fill(
                        TAXONOMY_COLORS["cluster"],
                        opacity=(0.064 if held else 0.095) * (1.0 - layer_index * 0.26),
                    )
                    cloud_group.add(cloud)
                ghosts.add(cloud_group)
            return ghosts

        def taxonomy_density_glints(params, max_lines=56):
            # The beat map asks for hidden structure as soft luminance, not line
            # networks. Keeping this as an empty group prevents fast blinking
            # connector clutter while preserving the existing call sites.
            return VGroup()

        def taxonomy_broken_wavefronts(anchor_center, color, max_radius=1.55, rings=4):
            stages = []
            for ring_index in range(rings):
                radius = max_radius * (ring_index + 1) / rings
                softness = VGroup()
                for layer_index, layer_scale in enumerate((1.00, 0.68, 0.38)):
                    glow = Dot(anchor_center, radius=radius * layer_scale, color=color)
                    glow.set_opacity(max(0.018, 0.070 - ring_index * 0.010 - layer_index * 0.014))
                    softness.add(glow)
                stages.append(softness)
            return stages

        def taxonomy_influence_territories(params, held=False):
            anchors = params.get("anchors", [])
            points = params.get("points", [])
            territories = VGroup()
            for anchor_index, anchor in enumerate(anchors):
                point_index = anchor.get("index")
                if point_index is None or not 0 <= point_index < len(points):
                    continue
                color = TAXONOMY_COLORS["amber"] if anchor.get("class", "a") == "a" else TAXONOMY_COLORS["blue"]
                center = vector_from_param(points[point_index])
                phase = anchor_index * 0.49
                territory = VGroup()
                for layer_index, scale in enumerate((1.0, 0.68)):
                    loop_points = []
                    steps = 18
                    radius = 1.05 * scale
                    for step_index in range(steps):
                        theta = TAU * step_index / steps
                        wobble = 1.0 + 0.16 * np.sin(2 * theta + phase) + 0.10 * np.cos(5 * theta - phase)
                        loop_points.append(center + np.array([
                            np.cos(theta) * radius * wobble,
                            np.sin(theta) * radius * wobble * 0.82,
                            0,
                        ]))
                    patch = VMobject()
                    patch.set_points_smoothly(loop_points + [loop_points[0]])
                    patch.set_stroke(color=color, width=0.0, opacity=0.0)
                    patch.set_fill(color, opacity=(0.046 if held else 0.068) * (1.0 - layer_index * 0.32))
                    territory.add(patch)
                territories.add(territory)
            return territories

        def taxonomy_reward_residue(point, color, amount=1.0):
            residue = Dot(point, radius=0.070 + 0.035 * amount, color=color)
            residue.set_opacity(0.070 * amount)
            return residue

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
            "show_axis_free_curve",
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
            "show_taxonomy_field",
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
                    # CRITICAL: set stable anchor at creation time.
                    # This must be ORIGIN (zone center) — never get_center() on
                    # distorted geometry. All subsequent transforms preserve this.
                    new_obj.manual_anchor = np.array([0.0, 0.0, 0.0])
                    new_obj.current_scale = merged_params.get("scale", 1.0)

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
                    # Defensive: set tracking attributes on ghost group
                    # (individual ghost items already have these from make_manual_rule_card)
                    new_obj.manual_anchor = np.array([0.0, 0.0, 0.0])
                    new_obj.current_scale = merged_params.get("scale", 0.4)

                    replace_zone = step.replace
                    outgoing_anims = []
                    if replace_zone is not None:
                        existing = active_objects.get(replace_zone)
                        if existing is not None:
                            outgoing = transition_out_for(existing, step.transition_out or "fade")
                            if outgoing is not None:
                                outgoing_anims.append(outgoing)
                            clear_zone(replace_zone)

                    # FadeIn directly — do NOT touch any other active objects.
                    # The rule card must remain at its current opacity throughout.
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
                    # CRITICAL: always use the stored manual_anchor — never get_center()
                    # on distorted polygon geometry. The anchor is set at card creation
                    # and must remain ORIGIN throughout all transforms.
                    source_anchor = getattr(source_obj, "manual_anchor", np.array([0.0, 0.0, 0.0]))
                    source_scale = getattr(source_obj, "current_scale", 1.0)
                    new_params["position"] = source_anchor.tolist()
                    new_params.setdefault("scale", source_scale)
                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": new_params,
                            "zone": source_zone,
                        }
                    )
                    # Preserve ORIGIN anchor — never overwrite with distorted get_center()
                    new_obj.manual_anchor = source_anchor.copy()
                    new_obj.current_scale = source_scale

                    force_indicator = make_manual_rule_force_indicator(step.params, new_obj)
                    if force_indicator is not None:
                        # The force indicator must read as the cause of deformation,
                        # not as an annotation after the fact. Draw it during the
                        # card transform, then let it vanish as the deformation lands.
                        indicator_in = FadeIn(force_indicator, run_time=run_time * 0.16)
                        card_transform = ReplacementTransform(source_obj, new_obj)
                        indicator_out = FadeOut(force_indicator, run_time=run_time * 0.24)
                        indicator_hold = Wait(max(run_time * 0.40, 0.01))
                        self.play(
                            AnimationGroup(
                                Succession(indicator_in, indicator_hold, indicator_out),
                                card_transform,
                                lag_ratio=0.0,
                            ),
                            run_time=run_time,
                        )
                        current_time += run_time
                    else:
                        self.play(ReplacementTransform(source_obj, new_obj), run_time=run_time)
                        current_time += run_time

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
                        if "target_text_opacity" in step.params and hasattr(obj, "submobjects") and len(obj.submobjects) >= 2:
                            card_shape = obj.submobjects[0]
                            label = obj.submobjects[1]
                            if "target_opacity" in step.params:
                                anim = card_shape.animate.set_opacity(step.params["target_opacity"])
                            extra_anims.append(label.animate.set_opacity(step.params["target_text_opacity"]))
                        elif "target_opacity" in step.params:
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

                elif step.action == "show_axis_free_curve":
                    merged_params = dict(step.params)
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
                    # Use Create so the curve draws itself left-to-right
                    # Do NOT touch any other active objects — card must remain at current opacity
                    if outgoing_anims:
                        self.play(AnimationGroup(*outgoing_anims, lag_ratio=0.0), run_time=0.3)
                        current_time += 0.3
                    pattern_points = getattr(new_obj, "pattern_points", None)
                    pattern_curve = getattr(new_obj, "pattern_curve", new_obj)
                    pattern_glow = getattr(new_obj, "pattern_glow", None)
                    pattern_title = getattr(new_obj, "pattern_title", None)
                    pattern_guides = getattr(new_obj, "pattern_guides", None)
                    if pattern_points is not None and len(pattern_points) > 0 and pattern_curve is not new_obj:
                        intro_anims = []
                        if pattern_guides is not None and len(pattern_guides) > 0:
                            intro_anims.append(FadeIn(pattern_guides))
                        if pattern_title is not None:
                            intro_anims.append(FadeIn(pattern_title))
                        intro_anims.append(FadeIn(pattern_points))
                        curve_anims = []
                        if pattern_glow is not None:
                            curve_anims.append(FadeIn(pattern_glow))
                        curve_anims.append(Create(pattern_curve))
                        intro_time = min(0.35, run_time * 0.28)
                        self.play(AnimationGroup(*intro_anims, lag_ratio=0.08), run_time=intro_time)
                        self.play(
                            AnimationGroup(
                                *curve_anims,
                                lag_ratio=0.0,
                            ),
                            run_time=max(run_time - intro_time, 0.1),
                        )
                    else:
                        simple_anims = []
                        if pattern_guides is not None and len(pattern_guides) > 0:
                            simple_anims.append(FadeIn(pattern_guides))
                        if pattern_title is not None:
                            simple_anims.append(FadeIn(pattern_title))
                        if pattern_glow is not None:
                            simple_anims.append(FadeIn(pattern_glow))
                        simple_anims.append(Create(pattern_curve))
                        self.play(AnimationGroup(*simple_anims, lag_ratio=0.08), run_time=run_time)
                    current_time += run_time
                    register_object(step.id, step.zone, new_obj)
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

                elif step.action == "show_taxonomy_field":
                    source_id = step.params.get("source_id")
                    source_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)
                    base_params = dict(getattr(source_obj, "taxonomy_params", {})) if source_obj is not None else {}
                    merged_params = {**base_params, **step.params}
                    merged_params.pop("source_id", None)
                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": merged_params,
                            "zone": step.zone,
                        }
                    )
                    stage = merged_params.get("stage", "field_intro")

                    if source_obj is None:
                        field_points = getattr(new_obj, "taxonomy_points", None)
                        labels = getattr(new_obj, "taxonomy_labels", VGroup())
                        if field_points is not None and getattr(new_obj, "taxonomy_stage", None) == "field_intro":
                            self.add(new_obj)
                            self.play(FadeIn(field_points), run_time=run_time * 0.62)
                            self.wait(run_time * 0.38)
                        else:
                            self.play(FadeIn(new_obj), run_time=run_time)
                        current_time += run_time
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "supervised_full":
                        dot_items = list(getattr(getattr(source_obj, "taxonomy_points", VGroup()), "dot_items", []))
                        classes = merged_params.get("classes", [])
                        points = merged_params.get("points", [])
                        labels = list(getattr(source_obj, "taxonomy_labels", VGroup()))
                        label_anims = [
                            label.animate.set_opacity(opacity)
                            for label, opacity in zip(labels, [0.88, 0.04, 0.04, 0.04])
                        ]
                        ordered = sorted(range(len(dot_items)), key=lambda index: points[index][0] if index < len(points) else 0)
                        waves = []
                        wave_count = 3
                        for wave_index in range(wave_count):
                            wave_indices = ordered[
                                wave_index * len(ordered) // wave_count:
                                (wave_index + 1) * len(ordered) // wave_count
                            ]
                            wave_anims = []
                            flashes = VGroup()
                            for point_index in wave_indices:
                                if point_index >= len(classes):
                                    continue
                                color = TAXONOMY_COLORS["amber"] if classes[point_index] == "a" else TAXONOMY_COLORS["blue"]
                                wave_anims.append(dot_items[point_index].animate.set_color(color).set_opacity(0.98).scale(1.18))
                                flashes.add(taxonomy_point_flash(dot_items[point_index], color, radius_scale=2.85, opacity=0.28))
                                flashes.add(taxonomy_label_tick(dot_items[point_index], color))
                            if wave_anims:
                                tick = Succession(FadeIn(flashes, scale=1.05), Wait(run_time * 0.012), FadeOut(flashes, scale=1.35)) if len(flashes) else Wait(0)
                                waves.append(AnimationGroup(AnimationGroup(*wave_anims, lag_ratio=0.0), tick, lag_ratio=0.0))
                        sheen = Rectangle(width=1.75, height=7.2, stroke_width=0)
                        sheen.set_fill(TAXONOMY_COLORS["cluster"], opacity=0.050)
                        sheen.move_to(LEFT * 6.2)
                        leading_edge = Rectangle(width=0.035, height=7.2, stroke_width=0)
                        leading_edge.set_fill(TAXONOMY_COLORS["cluster"], opacity=0.16)
                        leading_edge.move_to(LEFT * 5.65)
                        self.add(sheen, leading_edge)
                        self.play(
                            AnimationGroup(
                                sheen.animate.shift(RIGHT * 12.4).set_opacity(0.0),
                                leading_edge.animate.shift(RIGHT * 11.3).set_opacity(0.0),
                                Succession(*waves),
                                *label_anims,
                                lag_ratio=0.0,
                            ),
                            run_time=run_time * 0.44,
                        )
                        self.remove(sheen, leading_edge)
                        confirmation = VGroup()
                        held_label_ticks = VGroup()
                        for point_index, dot in enumerate(dot_items):
                            if point_index >= len(classes):
                                continue
                            color = TAXONOMY_COLORS["amber"] if classes[point_index] == "a" else TAXONOMY_COLORS["blue"]
                            confirm_tick = taxonomy_label_tick(dot, color)
                            confirm = VGroup(
                                taxonomy_point_flash(dot, color, radius_scale=2.25, opacity=0.16),
                                confirm_tick,
                            )
                            confirmation.add(confirm)
                            # Keep a sparse subset of label marks readable during the hold so
                            # the frame says "labeled examples", not only "colored dots".
                            if point_index % 6 == 0:
                                held_tick = taxonomy_label_tick(dot, color)
                                held_tick.set_stroke(color=color, width=1.55, opacity=0.62)
                                held_label_ticks.add(held_tick)
                        if len(confirmation) != 0:
                            self.play(
                                FadeIn(confirmation, scale=0.82),
                                run_time=run_time * 0.10,
                            )
                            if len(held_label_ticks) != 0:
                                self.add(held_label_ticks)
                            self.play(
                                FadeOut(confirmation, scale=1.22),
                                run_time=run_time * 0.08,
                            )
                            self.wait(run_time * 0.40)
                        else:
                            self.wait(run_time * 0.12)
                        self.wait(run_time * 0.08)
                        if len(held_label_ticks) != 0:
                            new_obj.add(held_label_ticks)
                            new_obj.taxonomy_label_marks = held_label_ticks
                        current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "supervised_boundary":
                        labels = list(getattr(source_obj, "taxonomy_labels", VGroup()))
                        source_glows = getattr(source_obj, "taxonomy_glows", VGroup())
                        target_glows = getattr(new_obj, "taxonomy_glows", VGroup())
                        label_anims = [
                            label.animate.set_opacity(opacity)
                            for label, opacity in zip(labels, [0.88, 0.04, 0.04, 0.04])
                        ]
                        if len(source_glows) != 0:
                            self.play(FadeOut(source_glows), run_time=run_time * 0.10)
                            current_time += run_time * 0.10
                        if len(target_glows) != 0:
                            ordered_glows = sorted(list(target_glows), key=lambda glow: (glow.get_center()[0], glow.get_center()[1]))
                            for glow in ordered_glows:
                                glow.set_opacity(0)
                            self.add(target_glows)
                            pulse_groups = []
                            pulse_count = 6
                            for pulse_index in range(pulse_count):
                                group_items = ordered_glows[
                                    pulse_index * len(ordered_glows) // pulse_count:
                                    (pulse_index + 1) * len(ordered_glows) // pulse_count
                                ]
                                if not group_items:
                                    continue
                                local_points = VGroup()
                                for halo in group_items:
                                    ping = halo.copy()
                                    ping.set_opacity(0.12)
                                    local_points.add(ping)
                                pulse_groups.append(
                                    AnimationGroup(
                                        FadeIn(local_points, scale=1.05),
                                        AnimationGroup(*[halo.animate.set_opacity(0.035) for halo in group_items], lag_ratio=0.0),
                                        FadeOut(local_points, scale=1.85),
                                        lag_ratio=0.0,
                                    )
                                )
                            self.play(
                                AnimationGroup(Succession(*pulse_groups), *label_anims, lag_ratio=0.0),
                                run_time=run_time * 0.76,
                            )
                            self.play(target_glows.animate.set_opacity(0.0), run_time=run_time * 0.14)
                            current_time += run_time * 0.90
                        else:
                            self.play(AnimationGroup(*label_anims, lag_ratio=0.0), run_time=run_time)
                            current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        target_new_glows = getattr(new_obj, "taxonomy_glows", VGroup())
                        source_label_marks = getattr(source_obj, "taxonomy_label_marks", VGroup())
                        if len(source_label_marks) != 0:
                            new_obj.add(source_label_marks)
                            new_obj.taxonomy_label_marks = source_label_marks
                        if len(target_new_glows) != 0:
                            target_new_glows.set_opacity(0.0)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "label_intro":
                        labels = list(getattr(source_obj, "taxonomy_labels", VGroup()))
                        label_targets = [0.16, 0.16, 0.16, 0.16]
                        label_anims = [
                            label.animate.set_opacity(opacity)
                            for label, opacity in zip(labels, label_targets)
                        ]
                        if label_anims:
                            intro_steps = []
                            for anim in label_anims:
                                intro_steps.append(anim)
                                intro_steps.append(Wait(0.12))
                            self.play(Succession(*intro_steps), run_time=run_time)
                            current_time += run_time
                        source_obj.taxonomy_params = merged_params
                        source_obj.taxonomy_stage = stage
                        object_registry[step.id] = source_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = source_obj
                        handled = True
                        continue

                    if stage == "unsupervised_neutral":
                        dot_items = list(getattr(getattr(source_obj, "taxonomy_points", VGroup()), "dot_items", []))
                        labels = list(getattr(source_obj, "taxonomy_labels", VGroup()))
                        glows = getattr(source_obj, "taxonomy_glows", VGroup())
                        label_marks = getattr(source_obj, "taxonomy_label_marks", VGroup())
                        ordered = sorted(range(len(dot_items)), key=lambda index: dot_items[index].get_center()[0])
                        drain_groups = []
                        group_count = 6
                        for group_index in range(group_count):
                            group_indices = ordered[
                                group_index * len(ordered) // group_count:
                                (group_index + 1) * len(ordered) // group_count
                            ]
                            if not group_indices:
                                continue
                            drain_groups.append(
                                AnimationGroup(
                                    *[
                                        Succession(
                                            dot_items[index].animate.set_opacity(0.10),
                                            dot_items[index].animate.set_color(TAXONOMY_COLORS["neutral"]).set_opacity(0.24),
                                        )
                                        for index in group_indices
                                    ],
                                    lag_ratio=0.0,
                                )
                            )
                        label_anims = [
                            label.animate.set_opacity(opacity)
                            for label, opacity in zip(labels, [0.055, 0.88, 0.055, 0.055])
                        ]
                        glow_anims = [FadeOut(glows)] if len(glows) != 0 else []
                        label_mark_anims = [FadeOut(label_marks)] if len(label_marks) != 0 else []
                        self.play(
                            AnimationGroup(Succession(*drain_groups), *label_anims, *glow_anims, *label_mark_anims, lag_ratio=0.0),
                            run_time=run_time,
                        )
                        current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "unsupervised_clusters":
                        point_source = getattr(source_obj, "taxonomy_points", None)
                        point_target = getattr(new_obj, "taxonomy_points", None)
                        glows = getattr(new_obj, "taxonomy_glows", VGroup())
                        glints = taxonomy_density_glints(merged_params)
                        ghosts = taxonomy_cluster_ghosts(merged_params)
                        anims = []
                        if point_source is not None and point_target is not None:
                            source_dots = list(getattr(point_source, "dot_items", []))
                            target_dots = list(getattr(point_target, "dot_items", []))
                            staged = []
                            clusters = merged_params.get("clusters", [])
                            points = merged_params.get("points", [])
                            for cluster in clusters:
                                center = vector_from_param(cluster.get("center"))
                                radius = cluster.get("radius", 1.0)
                                local = []
                                for index, (source_dot, target_dot) in enumerate(zip(source_dots, target_dots)):
                                    if index >= len(points):
                                        continue
                                    distance = np.linalg.norm(vector_from_param(points[index]) - center)
                                    if distance <= radius * 0.98:
                                        local.append((distance, Transform(source_dot, target_dot)))
                                local.sort(key=lambda item: item[0])
                                if local:
                                    core_count = max(3, len(local) // 3)
                                    neighbor_count = max(core_count + 1, (len(local) * 2) // 3)
                                    staged.append(AnimationGroup(*[anim for _, anim in local[:core_count]], lag_ratio=0.0))
                                    if len(local) > core_count:
                                        staged.append(AnimationGroup(*[anim for _, anim in local[core_count:neighbor_count]], lag_ratio=0.0))
                                    if len(local) > neighbor_count:
                                        staged.append(AnimationGroup(*[anim for _, anim in local[neighbor_count:]], lag_ratio=0.0))
                            staged_indices = set()
                            for cluster in clusters:
                                center = vector_from_param(cluster.get("center"))
                                radius = cluster.get("radius", 1.0)
                                for index, _point in enumerate(points):
                                    if np.linalg.norm(vector_from_param(_point) - center) <= radius * 0.98:
                                        staged_indices.add(index)
                            remaining = [
                                Transform(source_dot, target_dot)
                                for index, (source_dot, target_dot) in enumerate(zip(source_dots, target_dots))
                                if index not in staged_indices
                            ]
                            if staged:
                                anims.append(Succession(*staged, AnimationGroup(*remaining, lag_ratio=0.0) if remaining else Wait(0)))
                            elif remaining:
                                anims.append(AnimationGroup(*remaining, lag_ratio=0.0))
                        if len(glows) != 0:
                            self.add(glows)
                            anims.append(FadeIn(glows, scale=1.06))
                        if len(ghosts) != 0:
                            held_ghosts = taxonomy_cluster_ghosts(merged_params, held=True)
                            self.add(ghosts)
                            anims.append(
                                Succession(
                                    LaggedStart(*[FadeIn(ghost, scale=0.94) for ghost in ghosts], lag_ratio=0.18),
                                    Wait(run_time * 0.22),
                                    Transform(ghosts, held_ghosts),
                                )
                            )
                        else:
                            held_ghosts = VGroup()
                        if len(glints) != 0:
                            self.add(glints)
                            anims.append(
                                Succession(
                                    Wait(run_time * 0.16),
                                    FadeIn(glints),
                                    Wait(run_time * 0.46),
                                    glints.animate.set_opacity(0.18),
                                )
                            )
                        if anims:
                            self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=run_time * 0.74)
                            self.wait(run_time * 0.26)
                            current_time += run_time
                        self.remove(source_obj)
                        if len(ghosts) != 0:
                            self.remove(ghosts)
                        if len(glints) != 0:
                            self.remove(glints)
                        if len(held_ghosts) != 0:
                            new_obj.add(held_ghosts)
                            new_obj.taxonomy_cluster_clouds = held_ghosts
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "unsupervised_hold":
                        source_glows = getattr(source_obj, "taxonomy_glows", VGroup())
                        target_glows = getattr(new_obj, "taxonomy_glows", VGroup())
                        source_clouds = getattr(source_obj, "taxonomy_cluster_clouds", VGroup())
                        if len(source_clouds) != 0:
                            new_obj.add(source_clouds)
                            new_obj.taxonomy_cluster_clouds = source_clouds
                        hold_anims = []
                        if len(source_glows) != 0:
                            pulse_glows = source_glows.copy()
                            for glow in pulse_glows:
                                if hasattr(glow, "set_fill") and hasattr(glow, "get_fill_opacity"):
                                    glow.set_fill(opacity=min(glow.get_fill_opacity() * 1.14, glow.get_fill_opacity() + 0.025))
                            hold_anims.append(Succession(Transform(source_glows, pulse_glows), Transform(source_glows, target_glows)))
                        if len(source_clouds) != 0:
                            cloud_breath = source_clouds.copy()
                            cloud_breath.set_opacity(0.40)
                            hold_anims.append(Succession(Transform(source_clouds, cloud_breath), source_clouds.animate.set_opacity(0.34)))
                        if hold_anims:
                            self.play(AnimationGroup(*hold_anims, lag_ratio=0.0), run_time=run_time * 0.38)
                            self.wait(run_time * 0.62)
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage in {"semi_neutral", "rl_neutral"}:
                        dot_items = list(getattr(getattr(source_obj, "taxonomy_points", VGroup()), "dot_items", []))
                        labels = list(getattr(source_obj, "taxonomy_labels", VGroup()))
                        glows = getattr(source_obj, "taxonomy_glows", VGroup())
                        influence = getattr(source_obj, "taxonomy_influence", VGroup())
                        cluster_clouds = getattr(source_obj, "taxonomy_cluster_clouds", VGroup())
                        influence_territories = getattr(source_obj, "taxonomy_influence_territories", VGroup())
                        label_targets = [0.04, 0.04, 0.88, 0.04] if stage == "semi_neutral" else [0.04, 0.04, 0.04, 0.88]
                        dot_anims = [
                            dot.animate.set_color(TAXONOMY_COLORS["neutral"]).set_opacity(0.24)
                            for dot in dot_items
                        ]
                        label_anims = [
                            label.animate.set_opacity(opacity)
                            for label, opacity in zip(labels, label_targets)
                        ]
                        cleanup_anims = []
                        if len(glows) != 0:
                            cleanup_anims.append(FadeOut(glows))
                        if len(influence) != 0:
                            cleanup_anims.append(FadeOut(influence))
                        if len(cluster_clouds) != 0:
                            cleanup_anims.append(FadeOut(cluster_clouds))
                        if len(influence_territories) != 0:
                            cleanup_anims.append(FadeOut(influence_territories))
                        self.play(
                            AnimationGroup(*dot_anims, *label_anims, *cleanup_anims, lag_ratio=0.0),
                            run_time=run_time * 0.82,
                        )
                        self.wait(run_time * 0.18)
                        current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "semi_anchors":
                        dot_items = list(getattr(getattr(source_obj, "taxonomy_points", VGroup()), "dot_items", []))
                        labels = list(getattr(source_obj, "taxonomy_labels", VGroup()))
                        label_anims = [
                            label.animate.set_opacity(opacity)
                            for label, opacity in zip(labels, [0.04, 0.04, 0.88, 0.04])
                        ]
                        anchor_steps = []
                        anchors = merged_params.get("anchors", [])
                        for pair_start in range(0, len(anchors), 2):
                            pair_anims = []
                            rings = VGroup()
                            for anchor in anchors[pair_start:pair_start + 2]:
                                anchor_index = anchor.get("index")
                                if anchor_index is None or not 0 <= anchor_index < len(dot_items):
                                    continue
                                color = TAXONOMY_COLORS["amber"] if anchor.get("class", "a") == "a" else TAXONOMY_COLORS["blue"]
                                rings.add(taxonomy_anchor_burst(dot_items[anchor_index], color))
                                pair_anims.append(dot_items[anchor_index].animate.set_color(color).set_opacity(0.98).scale(2.0))
                            if pair_anims:
                                anchor_steps.append(
                                    AnimationGroup(
                                        AnimationGroup(*pair_anims, lag_ratio=0.0),
                                        Succession(FadeIn(rings, scale=0.72), Wait(run_time * 0.040), rings.animate.scale(1.22).set_opacity(0.0)),
                                        lag_ratio=0.0,
                                    )
                                )
                        if anchor_steps or label_anims:
                            self.play(AnimationGroup(Succession(*anchor_steps), *label_anims, lag_ratio=0.0), run_time=run_time * 0.46)
                            self.wait(run_time * 0.54)
                            current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "semi_influence":
                        influence = getattr(new_obj, "taxonomy_influence", VGroup())
                        point_source = getattr(source_obj, "taxonomy_points", None)
                        point_target = getattr(new_obj, "taxonomy_points", None)
                        anchors = merged_params.get("anchors", [])
                        points = merged_params.get("points", [])
                        territories = taxonomy_influence_territories(merged_params)
                        held_territories = taxonomy_influence_territories(merged_params, held=True)
                        anims = []
                        wave_steps = []
                        for anchor in anchors:
                            anchor_index = anchor.get("index")
                            if anchor_index is None or not 0 <= anchor_index < len(points):
                                continue
                            color = TAXONOMY_COLORS["amber"] if anchor.get("class", "a") == "a" else TAXONOMY_COLORS["blue"]
                            waves = taxonomy_broken_wavefronts(vector_from_param(points[anchor_index]), color)
                            for wave_group in waves:
                                wave_steps.append(Succession(FadeIn(wave_group, scale=0.86), Wait(run_time * 0.020), FadeOut(wave_group, scale=1.18)))
                        if point_source is not None and point_target is not None:
                            source_dots = list(getattr(point_source, "dot_items", []))
                            target_dots = list(getattr(point_target, "dot_items", []))
                            anchor_indices = {anchor.get("index") for anchor in anchors}
                            anchor_anims = []
                            propagation_groups = []
                            for index, (source_dot, target_dot) in enumerate(zip(source_dots, target_dots)):
                                if index in anchor_indices:
                                    anchor_anims.append(Transform(source_dot, target_dot))
                                    continue
                                nearest_distance = None
                                for anchor in anchors:
                                    anchor_index = anchor.get("index")
                                    if anchor_index is None or not 0 <= anchor_index < len(points):
                                        continue
                                    distance = np.linalg.norm(vector_from_param(points[index]) - vector_from_param(points[anchor_index]))
                                    nearest_distance = distance if nearest_distance is None else min(nearest_distance, distance)
                                if nearest_distance is None or nearest_distance > 1.35:
                                    continue
                                propagation_groups.append((nearest_distance, Transform(source_dot, target_dot)))
                            propagation_groups.sort(key=lambda item: item[0])
                            staged = []
                            ring_count = 4
                            for ring_index in range(ring_count):
                                ring_anims = [
                                    anim for distance, anim in propagation_groups
                                    if ring_index / ring_count * 1.35 <= distance < (ring_index + 1) / ring_count * 1.35
                                ]
                                if ring_anims:
                                    wave_stage = AnimationGroup(*wave_steps[ring_index::ring_count], lag_ratio=0.10) if wave_steps else Wait(0)
                                    staged.append(
                                        Succession(
                                            wave_stage,
                                            AnimationGroup(*ring_anims, lag_ratio=0.0),
                                            Wait(run_time * 0.035),
                                        )
                                    )
                            if anchor_anims:
                                anims.append(AnimationGroup(*anchor_anims, lag_ratio=0.0))
                            if staged:
                                anims.append(Succession(*staged))
                        if len(influence) != 0:
                            ordered_influence = sorted(list(influence), key=lambda halo: min(
                                [np.linalg.norm(halo.get_center() - vector_from_param(points[anchor.get("index")])) for anchor in anchors if anchor.get("index") is not None and 0 <= anchor.get("index") < len(points)] or [0]
                            ))
                            for halo in ordered_influence:
                                halo.set_opacity(0)
                            self.add(influence)
                            halo_stages = []
                            halo_count = 4
                            for stage_index in range(halo_count):
                                group_items = ordered_influence[
                                    stage_index * len(ordered_influence) // halo_count:
                                    (stage_index + 1) * len(ordered_influence) // halo_count
                                ]
                                if group_items:
                                    halo_stages.append(AnimationGroup(*[halo.animate.set_opacity(0.115) for halo in group_items], lag_ratio=0.0))
                            if halo_stages:
                                anims.append(Succession(*halo_stages))
                        if len(territories) != 0:
                            for territory in territories:
                                territory.set_opacity(0)
                            self.add(territories)
                            anims.append(
                                Succession(
                                    Wait(run_time * 0.18),
                                    territories.animate.set_opacity(1.0),
                                    Wait(run_time * 0.18),
                                    Transform(territories, held_territories),
                                )
                            )
                        if anims:
                            self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=run_time * 0.72)
                            self.wait(run_time * 0.28)
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        self.remove(source_obj)
                        if len(territories) != 0:
                            self.remove(territories)
                        if len(held_territories) != 0:
                            new_obj.add(held_territories)
                            new_obj.taxonomy_influence_territories = held_territories
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "semi_hold":
                        dot_items = list(getattr(getattr(source_obj, "taxonomy_points", VGroup()), "dot_items", []))
                        anchors = merged_params.get("anchors", [])
                        source_territories = getattr(source_obj, "taxonomy_influence_territories", VGroup())
                        if len(source_territories) != 0:
                            new_obj.add(source_territories)
                            new_obj.taxonomy_influence_territories = source_territories
                        anchor_anims = []
                        for anchor in anchors:
                            anchor_index = anchor.get("index")
                            if anchor_index is not None and 0 <= anchor_index < len(dot_items):
                                anchor_anims.append(
                                    Succession(
                                        dot_items[anchor_index].animate.scale(1.10).set_opacity(1.0),
                                        dot_items[anchor_index].animate.scale(1 / 1.10).set_opacity(0.96),
                                    )
                                )
                        hold_parts = []
                        if anchor_anims:
                            hold_parts.append(AnimationGroup(*anchor_anims, lag_ratio=0.08))
                        if len(source_territories) != 0:
                            steady_territories = source_territories.copy()
                            steady_territories.set_opacity(0.88)
                            hold_parts.append(Transform(source_territories, steady_territories))
                        if hold_parts:
                            self.play(AnimationGroup(*hold_parts, lag_ratio=0.0), run_time=run_time * 0.36)
                            self.wait(run_time * 0.64)
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "rl_agent":
                        labels = list(getattr(source_obj, "taxonomy_labels", VGroup()))
                        agent = getattr(new_obj, "taxonomy_agent", VGroup())
                        label_anims = [
                            label.animate.set_opacity(opacity)
                            for label, opacity in zip(labels, [0.04, 0.04, 0.04, 0.88])
                        ]
                        anims = [*label_anims]
                        if len(agent) != 0:
                            self.add(agent)
                            arrival = agent.copy()
                            arrival.set_opacity(0.24)
                            self.add(arrival)
                            anims.append(Succession(FadeIn(arrival, scale=1.55), FadeOut(arrival, scale=2.2)))
                            anims.append(FadeIn(agent, shift=RIGHT * 0.08))
                        if anims:
                            self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=run_time)
                            current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "rl_resolution":
                        labels = list(getattr(source_obj, "taxonomy_labels", VGroup()))
                        source_glows = getattr(source_obj, "taxonomy_glows", VGroup())
                        target_glows = getattr(new_obj, "taxonomy_glows", VGroup())
                        source_agent = getattr(source_obj, "taxonomy_agent", VGroup())
                        target_agent = getattr(new_obj, "taxonomy_agent", VGroup())
                        anims = [
                            label.animate.set_opacity(opacity)
                            for label, opacity in zip(labels, [0.0, 0.0, 0.0, 0.0])
                        ]
                        if len(source_glows) != 0 and len(target_glows) != 0:
                            anims.append(Transform(source_glows, target_glows))
                        elif len(target_glows) != 0:
                            self.add(target_glows)
                            anims.append(FadeIn(target_glows))
                        if len(source_agent) != 0 and len(target_agent) != 0:
                            anims.append(Transform(source_agent, target_agent))
                        if anims:
                            self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=run_time * 0.72)
                            self.wait(run_time * 0.28)
                            current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    if stage == "rl_navigation":
                        path_points = [vector_from_param(point) for point in merged_params.get("agent_path", [])]
                        if len(path_points) >= 2:
                            path_curve = VMobject()
                            path_curve.set_points_smoothly(path_points)
                            trail = getattr(new_obj, "taxonomy_trail", VGroup())
                            agent = getattr(source_obj, "taxonomy_agent", None)
                            destination_glow = getattr(new_obj, "taxonomy_glows", VGroup())
                            flash_anims = []
                            reward_residues = VGroup()
                            for flash in merged_params.get("feedback_flashes", []):
                                flash_color = TAXONOMY_COLORS["reward"] if flash.get("kind") == "reward" else TAXONOMY_COLORS["penalty"]
                                flash_point = vector_from_param(flash.get("point"))
                                flash_dot = Dot(flash_point, radius=flash.get("radius", 0.18), color=flash_color)
                                flash_dot.set_opacity(flash.get("opacity", 0.22))
                                delay = max(0.0, min(0.95, flash.get("at", 0.0)))
                                flash_anims.append(
                                    Succession(
                                        Wait(run_time * delay),
                                        FadeIn(flash_dot, scale=1.25, run_time=0.10),
                                        Wait(0.08),
                                        FadeOut(flash_dot, scale=1.65, run_time=0.34),
                                    )
                                )
                                if flash.get("kind") == "reward":
                                    residue = taxonomy_reward_residue(flash_point, flash_color, amount=0.75 + delay * 0.45)
                                    residue.set_opacity(0)
                                    reward_residues.add(residue)
                                    flash_anims.append(
                                        Succession(
                                            Wait(run_time * min(0.97, delay + 0.035)),
                                            residue.animate.set_opacity(0.085),
                                        )
                                    )
                            moving_agent = agent.copy() if agent is not None else None
                            parts = [Create(trail)]
                            if moving_agent is not None:
                                self.add(moving_agent)
                                parts.append(MoveAlongPath(moving_agent, path_curve, rate_func=rate_functions.ease_in_out_sine))
                            if len(reward_residues) != 0:
                                self.add(reward_residues)
                            if len(destination_glow) != 0:
                                destination_glows = list(destination_glow)
                                for glow in destination_glows:
                                    glow.set_opacity(0)
                                self.add(destination_glow)
                                reward_times = [flash.get("at", 0.0) for flash in merged_params.get("feedback_flashes", []) if flash.get("kind") == "reward"]
                                accumulation = []
                                for reward_index, reward_at in enumerate(reward_times):
                                    visible_fraction = (reward_index + 1) / max(1, len(reward_times))
                                    target_opacity = min(1.0, 0.32 + visible_fraction * 0.68)
                                    accumulation.append(
                                        Succession(
                                            Wait(run_time * max(0.0, min(0.95, reward_at + 0.02))),
                                            AnimationGroup(*[glow.animate.set_opacity(target_opacity) for glow in destination_glows], lag_ratio=0.0),
                                        )
                                    )
                                if accumulation:
                                    parts.extend(accumulation)
                            parts.extend(flash_anims)
                            self.add(trail)
                            self.play(AnimationGroup(*parts, lag_ratio=0.0), run_time=run_time)
                            if moving_agent is not None:
                                self.remove(moving_agent)
                            current_time += run_time
                        else:
                            self.play(ReplacementTransform(source_obj, new_obj), run_time=run_time)
                            current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        forget_object(source_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True
                        continue

                    self.play(ReplacementTransform(source_obj, new_obj), run_time=run_time)
                    current_time += run_time
                    forget_object(source_obj)
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
