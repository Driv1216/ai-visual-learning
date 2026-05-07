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
    _as_vector,
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
            size = 0.078
            tick = VMobject()
            tick.set_points_as_corners([
                center + np.array([-size * 0.55, -size * 0.05, 0]),
                center + np.array([-size * 0.15, -size * 0.42, 0]),
                center + np.array([size * 0.62, size * 0.48, 0]),
            ])
            tick.set_stroke(color=color, width=1.85, opacity=0.88)
            return tick

        def taxonomy_label_marks(dot, color):
            # Persistent, tiny "known answer" marks. These are not decorative
            # flashes; they are the held semantic cue that the point is labeled.
            mark = VGroup()
            badge = Dot(dot.get_center(), radius=0.058, color=color)
            badge.set_opacity(0.18)
            mark.add(badge)
            tick = taxonomy_label_tick(dot, color)
            tick.set_stroke(color=color, width=1.55, opacity=0.70)
            mark.add(tick)
            return mark

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
                radius = cluster.get("radius", 1.0)
                phase = cluster_index * 0.73
                cloud_group = VGroup()
                # Use stacked translucent discs instead of closed blob outlines.
                # The viewer should read atmospheric density, not drawn regions.
                layer_specs = (
                    (0.78, 0.105 if held else 0.135, np.array([0.00, 0.00, 0.0])),
                    (0.54, 0.082 if held else 0.108, np.array([0.18 * np.cos(phase), 0.10 * np.sin(phase), 0.0])),
                    (0.38, 0.066 if held else 0.086, np.array([-0.16 * np.sin(phase), 0.12 * np.cos(phase), 0.0])),
                    (0.24, 0.050 if held else 0.068, np.array([0.11 * np.cos(phase + 1.7), -0.09 * np.sin(phase + 0.4), 0.0])),
                )
                for scale, opacity, offset in layer_specs:
                    glow = Dot(center + offset, radius=radius * scale, color=TAXONOMY_COLORS["cluster"])
                    glow.set_opacity(opacity)
                    cloud_group.add(glow)
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
                layer_specs = (
                    (0.92, 0.050 if held else 0.072, np.array([0.00, 0.00, 0.0])),
                    (0.60, 0.042 if held else 0.060, np.array([0.10 * np.cos(phase), 0.07 * np.sin(phase), 0.0])),
                    (0.34, 0.033 if held else 0.048, np.array([-0.08 * np.sin(phase), 0.06 * np.cos(phase), 0.0])),
                )
                for scale, opacity, offset in layer_specs:
                    patch = Dot(center + offset, radius=1.03 * scale, color=color)
                    patch.set_opacity(opacity)
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
            "show_workflow_cycle",
            "mutate_workflow_cycle",
            "mutate_road_ahead_field",
            "show_supervised_field",
            "mutate_supervised_field",
            "show_supervised_examples",
            "show_supervised_resolution",
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

                elif step.action == "show_workflow_cycle":
                    # ── Build the cycle diagram object ────────────────────
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

                    node_list = getattr(new_obj, "cycle_nodes",  [])
                    arrows    = getattr(new_obj, "cycle_arrows", VGroup())
                    ret_arrow = getattr(new_obj, "cycle_return",  VGroup())
                    is_unlabeled = merged_params.get("unlabeled", False)

                    if outgoing_anims:
                        self.play(AnimationGroup(*outgoing_anims, lag_ratio=0.0), run_time=0.28)
                        current_time += 0.28

                    if node_list:
                        # Each node: Create ring (pen-draw), then FadeIn glow + label.
                        # When unlabeled=True the label text opacity is 0 at build time —
                        # so FadeIn(label) is a no-op and label stays hidden until a later
                        # mutate step reveals it.
                        node_draw_time = min(0.75, run_time * 0.60)
                        node_anims = []
                        for node in node_list:
                            # structure: [outer_glow(0), ring(1), txt(2), optional warn_halo(3)]
                            ring_obj  = node[1] if len(node) > 1 else node
                            label_obj = node[2] if len(node) > 2 else None
                            extras    = list(node)[3:] if len(node) > 3 else []
                            if is_unlabeled:
                                # Only draw the ring — label is opacity 0, leave it hidden
                                node_anims.append(
                                    Succession(
                                        Create(ring_obj, run_time=node_draw_time * 0.60),
                                        FadeIn(node[0], run_time=node_draw_time * 0.40),
                                    )
                                )
                            else:
                                node_anims.append(
                                    Succession(
                                        Create(ring_obj, run_time=node_draw_time * 0.55),
                                        AnimationGroup(
                                            FadeIn(node[0]),
                                            FadeIn(label_obj) if label_obj is not None else Wait(0),
                                            *[FadeIn(e) for e in extras],
                                            lag_ratio=0.0,
                                            run_time=node_draw_time * 0.45,
                                        ),
                                    )
                                )
                        self.play(
                            AnimationGroup(*node_anims, lag_ratio=0.20),
                            run_time=node_draw_time,
                        )
                        current_time += node_draw_time

                        if len(arrows) > 0:
                            arrow_time = max(0.18, run_time - node_draw_time)
                            self.play(
                                AnimationGroup(*[Create(a) for a in arrows], lag_ratio=0.25),
                                run_time=arrow_time,
                            )
                            current_time += arrow_time

                        if len(ret_arrow) > 0:
                            self.play(Create(ret_arrow), run_time=min(1.4, run_time * 0.55))
                            current_time += min(1.4, run_time * 0.55)
                    else:
                        self.play(FadeIn(new_obj), run_time=run_time)
                        current_time += run_time

                    register_object(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "show_supervised_field":
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

                    dots = list(getattr(new_obj, "supervised_dots", VGroup()))
                    for dot in dots:
                        dot.set_opacity(0.0)
                    self.add(new_obj)
                    if outgoing_anims:
                        self.play(AnimationGroup(*outgoing_anims, lag_ratio=0.0), run_time=min(0.35, run_time * 0.25))
                    if dots:
                        ordered = sorted(dots, key=lambda dot: (dot.get_center()[0] * 0.55 + dot.get_center()[1] * 0.18))
                        self.play(
                            LaggedStart(
                                *[
                                    dot.animate.set_opacity(getattr(new_obj, "supervised_dot_opacity", 0.62))
                                    for dot in ordered
                                ],
                                lag_ratio=0.045,
                            ),
                            run_time=run_time,
                            rate_func=rate_functions.ease_out_sine,
                        )
                    else:
                        self.wait(run_time)
                    current_time += run_time
                    register_object(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "mutate_supervised_field":
                    source_id = step.params.get("source_id")
                    field_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)

                    if field_obj is None:
                        print(
                            f"[mutate_supervised_field] WARNING: source_id={source_id} not found. Skipping."
                        )
                        handled = True
                        continue

                    mode = step.params.get("mode", "color_wave_in")
                    dots = list(getattr(field_obj, "supervised_dots", VGroup()))
                    boundary = getattr(field_obj, "supervised_boundary", None)
                    boundary_glow = getattr(field_obj, "supervised_boundary_glow", None)
                    neutral_color = step.params.get("neutral_color", getattr(field_obj, "supervised_neutral_color", "#6F7786"))
                    colored_opacity = step.params.get("colored_opacity", getattr(field_obj, "supervised_colored_opacity", 0.96))
                    dot_opacity = step.params.get("dot_opacity", getattr(field_obj, "supervised_dot_opacity", 0.62))
                    dim_opacity = step.params.get("dim_opacity", getattr(field_obj, "supervised_dim_opacity", 0.55))
                    line_opacity = step.params.get("line_opacity", 0.96)
                    glow_opacity = step.params.get("line_glow_opacity", 0.16)

                    def register_same_field():
                        object_registry[step.id] = field_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = field_obj

                    if mode in {"color_wave_in", "color_wave_out"}:
                        reverse = mode == "color_wave_out"
                        ordered = sorted(dots, key=lambda dot: dot.get_center()[0], reverse=reverse)
                        wave_count = step.params.get("wave_count", 6)
                        wave_groups = []
                        for wave_index in range(wave_count):
                            group_dots = ordered[
                                wave_index * len(ordered) // wave_count:
                                (wave_index + 1) * len(ordered) // wave_count
                            ]
                            if not group_dots:
                                continue
                            if mode == "color_wave_in":
                                wave_groups.append(
                                    AnimationGroup(
                                        *[
                                            dot.animate.set_color(getattr(dot, "supervised_target_color", "#F2A65A")).set_opacity(colored_opacity)
                                            for dot in group_dots
                                        ],
                                        lag_ratio=0.0,
                                    )
                                )
                            else:
                                wave_groups.append(
                                    AnimationGroup(
                                        *[
                                            dot.animate.set_color(neutral_color).set_opacity(dot_opacity)
                                            for dot in group_dots
                                        ],
                                        lag_ratio=0.0,
                                    )
                                )
                        if wave_groups:
                            self.play(Succession(*wave_groups), run_time=run_time, rate_func=rate_functions.ease_in_out_sine)
                        else:
                            self.wait(run_time)
                        current_time += run_time
                        register_same_field()
                        handled = True

                    elif mode == "declare_rule":
                        for dot in dots:
                            dot.set_color(getattr(dot, "supervised_target_color", "#F2A65A"))
                            dot.set_opacity(colored_opacity)
                        if boundary_glow is not None:
                            boundary_glow.set_stroke(opacity=glow_opacity)
                        if boundary is not None:
                            boundary.set_stroke(opacity=line_opacity)
                        self.wait(max(0.01, run_time))
                        current_time += run_time
                        register_same_field()
                        handled = True

                    elif mode == "infer_rule":
                        fade_time = min(0.5, run_time * 0.18)
                        pause_time = min(0.5, max(0.0, run_time * 0.14))
                        grow_time = max(0.1, run_time - fade_time - pause_time)
                        fade_anims = []
                        if boundary is not None:
                            fade_anims.append(boundary.animate.set_stroke(opacity=0.0))
                        if boundary_glow is not None:
                            fade_anims.append(boundary_glow.animate.set_stroke(opacity=0.0))
                        fade_anims.extend([dot.animate.set_opacity(dim_opacity) for dot in dots])
                        if fade_anims:
                            self.play(AnimationGroup(*fade_anims, lag_ratio=0.0), run_time=fade_time)
                        if pause_time > 0:
                            self.wait(pause_time)

                        if boundary is not None:
                            center = boundary.point_from_proportion(0.5)
                            left_target = boundary.get_start()
                            right_target = boundary.get_end()
                            boundary.put_start_and_end_on(center, center)
                            boundary.set_stroke(opacity=line_opacity)
                            grow_anims = [
                                boundary.animate.put_start_and_end_on(left_target, right_target).set_stroke(opacity=line_opacity),
                                *[dot.animate.set_opacity(colored_opacity) for dot in dots],
                            ]
                            if boundary_glow is not None:
                                boundary_glow.put_start_and_end_on(center, center)
                                boundary_glow.set_stroke(opacity=glow_opacity)
                                grow_anims.append(
                                    boundary_glow.animate.put_start_and_end_on(left_target, right_target).set_stroke(opacity=glow_opacity)
                                )
                            self.play(AnimationGroup(*grow_anims, lag_ratio=0.0), run_time=grow_time, rate_func=rate_functions.ease_in_out_sine)
                        else:
                            self.wait(grow_time)
                        current_time += run_time
                        register_same_field()
                        handled = True

                    elif mode == "curve_suggestion":
                        if boundary is not None:
                            start = boundary.get_start()
                            end = boundary.get_end()
                            center = boundary.point_from_proportion(0.5)
                            bow = step.params.get("bow", 0.28)
                            curved = VMobject(color=boundary.get_color())
                            curved.set_points_smoothly([
                                start,
                                center + np.array([0.0, bow, 0.0]),
                                end,
                            ])
                            curved.set_stroke(width=boundary.get_stroke_width(), opacity=boundary.get_stroke_opacity())
                            self.play(Transform(boundary, curved), run_time=run_time * 0.38, rate_func=rate_functions.ease_in_out_sine)
                            self.play(Transform(boundary, Line(start, end, color=boundary.get_color()).set_stroke(width=boundary.get_stroke_width(), opacity=boundary.get_stroke_opacity())), run_time=run_time * 0.32, rate_func=rate_functions.ease_in_out_sine)
                            fade_anims = [boundary.animate.set_stroke(opacity=0.0)]
                            if boundary_glow is not None:
                                fade_anims.append(boundary_glow.animate.set_stroke(opacity=0.0))
                            self.play(AnimationGroup(*fade_anims, lag_ratio=0.0), run_time=run_time * 0.30)
                        else:
                            self.wait(run_time)
                        current_time += run_time
                        register_same_field()
                        handled = True

                    elif mode == "hold":
                        self.wait(run_time)
                        current_time += run_time
                        register_same_field()
                        handled = True

                    else:
                        print(f"[mutate_supervised_field] WARNING: unknown mode={mode}. Skipping.")
                        handled = True

                elif step.action == "show_supervised_examples":
                    source_id = step.params.get("source_id")
                    field_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)
                    labels = step.params.get("labels")
                    pairs = step.params.get("pairs")
                    font_size = step.params.get("font_size", 28)
                    color = step.params.get("color", "#F5F7FB")
                    text_opacity = step.params.get("text_opacity", 0.92)

                    if labels:
                        overlays = VGroup()
                        for item in labels:
                            txt = Text(item.get("text", ""), font_size=item.get("font_size", font_size), color=item.get("color", color), weight=MEDIUM)
                            txt.set_opacity(0.0)
                            txt.move_to(vector_from_param(item.get("position", [0, 0, 0])))
                            overlays.add(txt)
                        self.add(overlays)
                        self.play(AnimationGroup(*[txt.animate.set_opacity(text_opacity) for txt in overlays], lag_ratio=0.0), run_time=min(0.4, run_time * 0.18))
                        hold_time = max(0.0, run_time - min(0.8, run_time * 0.36))
                        if hold_time > 0:
                            self.wait(hold_time)
                        self.play(AnimationGroup(*[txt.animate.set_opacity(0.0) for txt in overlays], lag_ratio=0.0), run_time=min(0.4, run_time * 0.18))
                        self.remove(overlays)
                    elif pairs:
                        fade_time = step.params.get("fade_time", 0.3)
                        hold_time = step.params.get("hold_time", 2.0)
                        for pair in pairs:
                            txt = Text(pair, font_size=font_size, color=color, weight=MEDIUM)
                            txt.set_opacity(0.0)
                            txt.move_to(vector_from_param(step.params.get("position", [0.0, 0.08, 0.0])))
                            self.add(txt)
                            self.play(txt.animate.set_opacity(text_opacity), run_time=fade_time)
                            self.wait(hold_time)
                            self.play(txt.animate.set_opacity(0.0), run_time=fade_time)
                            self.remove(txt)
                    else:
                        self.wait(run_time)
                    current_time += run_time
                    if field_obj is not None:
                        object_registry[step.id] = field_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = field_obj
                    handled = True

                elif step.action == "show_supervised_resolution":
                    source_id = step.params.get("source_id")
                    field_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)
                    title = Text(
                        step.params.get("text", "Supervised Learning"),
                        font_size=step.params.get("font_size", 38),
                        color=step.params.get("color", "#F5F7FB"),
                        weight=MEDIUM,
                    )
                    title.set_opacity(0.0)
                    title.move_to(vector_from_param(step.params.get("position", [0.0, -3.0, 0.0])))
                    self.add(title)
                    self.play(title.animate.set_opacity(step.params.get("opacity", 0.95)), run_time=run_time, rate_func=rate_functions.ease_out_sine)
                    current_time += run_time
                    if field_obj is not None:
                        field_obj.add(title)
                        object_registry[step.id] = field_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = field_obj
                    else:
                        register_object(step.id, step.zone, title)
                    handled = True

                elif step.action == "mutate_road_ahead_field":
                    source_id = step.params.get("source_id")
                    road_obj = object_registry.get(source_id)

                    if road_obj is None:
                        print(
                            f"[mutate_road_ahead_field] WARNING: source_id={source_id} not found. Skipping."
                        )
                        handled = True
                        continue

                    mode = step.params.get("mode", "settle")
                    lower_lines = getattr(road_obj, "road_lower_lines", VGroup())
                    upper_ambient = getattr(road_obj, "road_upper_ambient", None)
                    horizon_glow = getattr(road_obj, "road_horizon_glow", None)
                    horizon_core = getattr(road_obj, "road_horizon_core", None)
                    horizon_left = getattr(road_obj, "road_horizon_left", None)
                    horizon_right = getattr(road_obj, "road_horizon_right", None)
                    point = getattr(road_obj, "road_point", None)
                    point_halo = getattr(road_obj, "road_point_halo", None)
                    horizon_y = getattr(road_obj, "road_horizon_y", step.params.get("horizon_y", -0.18))
                    horizon_half_width = step.params.get(
                        "horizon_half_width",
                        getattr(road_obj, "road_horizon_half_width", 5.5),
                    )

                    if mode == "settle":
                        shift_down = step.params.get("shift_down", 0.26)
                        target_opacity = step.params.get("target_opacity", 0.38)
                        anims = []
                        for index, line in enumerate(lower_lines):
                            line_shift = shift_down * (0.78 + 0.08 * (index % 3))
                            anims.append(line.animate.shift(DOWN * line_shift).set_stroke(opacity=target_opacity))
                        if anims:
                            self.play(
                                AnimationGroup(*anims, lag_ratio=0.0),
                                run_time=run_time,
                                rate_func=rate_functions.ease_out_sine,
                            )
                        else:
                            self.wait(run_time)
                        current_time += run_time
                        object_registry[step.id] = road_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = road_obj
                        handled = True

                    elif mode == "emerge_horizon":
                        core_opacity = step.params.get("core_opacity", 1.0)
                        wing_opacity = step.params.get("wing_opacity", 0.92)
                        glow_opacity = step.params.get("glow_opacity", 0.16)
                        compress_shift = step.params.get("compress_shift", 0.18)
                        anims = []
                        if lower_lines:
                            anims.extend([
                                line.animate.shift(DOWN * compress_shift).set_stroke(opacity=step.params.get("lower_opacity", 0.30))
                                for line in lower_lines
                            ])
                        if horizon_core is not None:
                            anims.append(horizon_core.animate.set_stroke(opacity=core_opacity))
                        if horizon_left is not None:
                            anims.append(
                                horizon_left.animate.put_start_and_end_on(
                                    np.array([0.0, horizon_y, 0.0]),
                                    np.array([-horizon_half_width, horizon_y, 0.0]),
                                ).set_stroke(opacity=wing_opacity)
                            )
                        if horizon_right is not None:
                            anims.append(
                                horizon_right.animate.put_start_and_end_on(
                                    np.array([0.0, horizon_y, 0.0]),
                                    np.array([horizon_half_width, horizon_y, 0.0]),
                                ).set_stroke(opacity=wing_opacity)
                            )
                        if horizon_glow is not None:
                            anims.append(horizon_glow.animate.set_stroke(opacity=glow_opacity))
                        if anims:
                            self.play(
                                AnimationGroup(*anims, lag_ratio=0.0),
                                run_time=run_time,
                                rate_func=rate_functions.ease_out_sine,
                            )
                        else:
                            self.wait(run_time)
                        current_time += run_time
                        object_registry[step.id] = road_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = road_obj
                        handled = True

                    elif mode == "warm_upper_field":
                        if upper_ambient is not None:
                            self.play(
                                upper_ambient.animate.set_fill(
                                    step.params.get("target_color", "#182135"),
                                    opacity=step.params.get("target_opacity", 0.10),
                                ),
                                run_time=run_time,
                                rate_func=linear,
                            )
                        else:
                            self.wait(run_time)
                        current_time += run_time
                        object_registry[step.id] = road_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = road_obj
                        handled = True

                    elif mode == "cross_point":
                        if point is not None:
                            start = _as_vector(step.params.get("start", [0.0, horizon_y - 0.46, 0.0]))
                            cross = _as_vector(step.params.get("cross", [0.0, horizon_y + 0.02, 0.0]))
                            rest = _as_vector(step.params.get("rest", [0.0, 1.02, 0.0]))
                            cross_at = max(0.05, min(run_time - 0.05, step.params.get("cross_at", run_time * 0.40)))
                            remaining = max(0.05, run_time - cross_at)
                            point.move_to(start)
                            point.set_opacity(step.params.get("point_opacity", 1.0))
                            first_anims = [point.animate.move_to(cross)]
                            if point_halo is not None:
                                point_halo.move_to(start)
                                point_halo.set_stroke(opacity=step.params.get("point_halo_opacity", 0.22))
                                first_anims.append(point_halo.animate.move_to(cross))
                            self.play(
                                AnimationGroup(*first_anims, lag_ratio=0.0),
                                run_time=cross_at,
                                rate_func=linear,
                            )
                            response_anims = [point.animate.move_to(rest)]
                            if point_halo is not None:
                                response_anims.append(point_halo.animate.move_to(rest).set_stroke(opacity=step.params.get("rest_halo_opacity", 0.14)))
                            if horizon_core is not None:
                                response_anims.append(horizon_core.animate.set_stroke(opacity=step.params.get("line_response_opacity", 1.0), width=step.params.get("response_stroke_width", 2.5)))
                            if horizon_left is not None:
                                response_anims.append(horizon_left.animate.set_stroke(opacity=step.params.get("line_response_opacity", 1.0), width=step.params.get("response_stroke_width", 2.3)))
                            if horizon_right is not None:
                                response_anims.append(horizon_right.animate.set_stroke(opacity=step.params.get("line_response_opacity", 1.0), width=step.params.get("response_stroke_width", 2.3)))
                            if horizon_glow is not None:
                                response_anims.append(horizon_glow.animate.set_stroke(opacity=step.params.get("response_glow_opacity", 0.22)))
                            self.play(
                                AnimationGroup(*response_anims, lag_ratio=0.0),
                                run_time=remaining,
                                rate_func=rate_functions.ease_out_sine,
                            )
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        object_registry[step.id] = road_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = road_obj
                        handled = True

                    elif mode == "final_hold":
                        self.wait(run_time)
                        current_time += run_time
                        object_registry[step.id] = road_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = road_obj
                        handled = True

                    else:
                        print(f"[mutate_road_ahead_field] WARNING: unknown mode={mode}. Skipping.")
                        handled = True

                elif step.action == "mutate_workflow_cycle":
                    # ── Mutate an existing cycle diagram in-place ─────────
                    # Supported modes:
                    #   "add_nodes"     — add new node(s) + arrow to existing without rebuilding
                    #   "warn_node"     — warm-colour the named node with a bloom + pulse
                    #   "noise_node"    — jitter animation on named node to signal messy data
                    #   "internal_node" — convergence animation inside a single named node
                    #   "close_loop"    — animate only the closing arc; leave nodes untouched
                    #   "pulse_all"     — unified brightness pulse across all nodes

                    source_id = step.params.get("source_id")
                    cycle_obj = object_registry.get(source_id)

                    if cycle_obj is None:
                        print(
                            f"[mutate_workflow_cycle] WARNING: source_id={source_id} not found. Skipping."
                        )
                        handled = True
                        continue

                    mode = step.params.get("mode", "pulse_all")

                    if mode == "add_nodes":
                        # Build the full new object (correct arc positions for n+1 nodes),
                        # then move existing nodes to their new positions via animate.move_to,
                        # and Create the new node + connecting arrow.
                        # This preserves identity — existing nodes are never destroyed.
                        merged_params = dict(step.params)
                        new_obj = build_object(
                            {
                                "id": step.id,
                                "action": "show_workflow_cycle",
                                "params": merged_params,
                                "zone": step.zone,
                            }
                        )
                        new_node_list         = getattr(new_obj, "cycle_nodes",  [])
                        new_arrows            = getattr(new_obj, "cycle_arrows", VGroup())
                        old_labels            = getattr(cycle_obj, "cycle_labels", [])
                        n_existing            = len(old_labels)
                        arriving_nodes        = new_node_list[n_existing:]
                        new_connecting_arrows = list(new_arrows)[max(0, n_existing - 1):]

                        # Phase 1 — reposition existing nodes to their new arc positions.
                        # Also restore opacity of any noise-dimmed node (DATA cleanup beat).
                        old_nodes = getattr(cycle_obj, "cycle_nodes", [])
                        reposition_anims = []
                        for old_node, new_node in zip(old_nodes, new_node_list[:n_existing]):
                            target_pos = new_node.get_center()
                            # Always restore to full opacity — clears residual noise dimming
                            reposition_anims.append(
                                old_node.animate.move_to(target_pos).set_opacity(1.0)
                            )
                            # Fade out any attached noise specks
                            noise_specks = getattr(old_node, "noise_specks", None)
                            if noise_specks is not None:
                                reposition_anims.append(noise_specks.animate.set_opacity(0.0))
                        old_arrows = getattr(cycle_obj, "cycle_arrows", VGroup())
                        for old_arr, new_arr in zip(list(old_arrows), list(new_arrows)[:max(0, n_existing - 1)]):
                            reposition_anims.append(
                                old_arr.animate.put_start_and_end_on(
                                    new_arr.get_start(), new_arr.get_end()
                                )
                            )

                        reposition_time = run_time * 0.30 if reposition_anims else 0.0
                        if reposition_anims:
                            self.play(
                                AnimationGroup(*reposition_anims, lag_ratio=0.0),
                                run_time=reposition_time,
                            )
                            current_time += reposition_time

                        # Phase 2 — Create new node(s) and connecting arrow(s)
                        arrive_time  = run_time - reposition_time
                        arrive_anims = []
                        for node in arriving_nodes:
                            ring_obj  = node[1] if len(node) > 1 else node
                            label_obj = node[2] if len(node) > 2 else None
                            extras    = list(node)[3:] if len(node) > 3 else []
                            arrive_anims.append(
                                Succession(
                                    Create(ring_obj, run_time=arrive_time * 0.50),
                                    AnimationGroup(
                                        FadeIn(node[0]),
                                        FadeIn(label_obj) if label_obj is not None else Wait(0),
                                        *[FadeIn(e) for e in extras],
                                        lag_ratio=0.0,
                                        run_time=arrive_time * 0.30,
                                    ),
                                )
                            )
                        connecting_arrow_anims = [Create(a) for a in new_connecting_arrows]
                        all_arrive = arrive_anims + connecting_arrow_anims
                        if all_arrive:
                            self.play(
                                AnimationGroup(*all_arrive, lag_ratio=0.18),
                                run_time=max(0.20, arrive_time),
                            )
                            current_time += max(0.20, arrive_time)

                        # Swap registry: new_obj is now the authoritative cycle object.
                        self.add(new_obj)
                        self.remove(cycle_obj)
                        forget_object(cycle_obj)
                        register_object(step.id, step.zone, new_obj)
                        handled = True

                    elif mode == "warn_node":
                        # Warm-colour bloom + pulse on the named node.
                        # The cycle_obj stays on screen; we only animate the target ring.
                        node_label  = step.params.get("node_label", "EVALUATION")
                        node_labels = getattr(cycle_obj, "cycle_labels", [])
                        node_list   = getattr(cycle_obj, "cycle_nodes",  [])
                        try:
                            idx         = node_labels.index(node_label)
                            target_node = node_list[idx]
                        except (ValueError, IndexError):
                            target_node = None

                        if target_node is not None:
                            # node[0]=outer_glow, node[1]=main_ring, node[2]=txt
                            outer = target_node[0] if len(target_node) > 0 else None
                            ring  = target_node[1] if len(target_node) > 1 else target_node
                            amber = "#E8A838"
                            # Step 1: colour bloom
                            bloom_anims = [ring.animate.set_stroke(color=amber, opacity=1.0).set_fill(color="#1a1006")]
                            if outer is not None:
                                bloom_anims.append(outer.animate.set_stroke(color=amber, opacity=0.38))
                            self.play(
                                AnimationGroup(*bloom_anims, lag_ratio=0.0),
                                run_time=run_time * 0.36,
                            )
                            # Step 2: single pulse — widen stroke then settle
                            self.play(
                                ring.animate.set_stroke(width=5.2, opacity=1.0),
                                run_time=run_time * 0.26,
                            )
                            self.play(
                                ring.animate.set_stroke(width=2.6, opacity=0.88),
                                run_time=run_time * 0.38,
                            )
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time

                        object_registry[step.id] = cycle_obj
                        step_zone_map[step.id] = step.zone
                        handled = True

                    elif mode == "reveal_label":
                        # Fade in the label text on the named node.
                        # Used for Beat 2: the DATA circle already exists unlabeled;
                        # this step makes the label appear "as if it was always there."
                        node_label  = step.params.get("node_label", "DATA")
                        node_labels = getattr(cycle_obj, "cycle_labels", [])
                        node_list   = getattr(cycle_obj, "cycle_nodes",  [])
                        try:
                            idx         = node_labels.index(node_label)
                            target_node = node_list[idx]
                        except (ValueError, IndexError):
                            target_node = None

                        if target_node is not None:
                            # node structure: [outer(0), ring(1), txt(2), ...]
                            label_obj = target_node[2] if len(target_node) > 2 else None
                            if label_obj is not None:
                                # Gentle settle-in — not a pop
                                self.play(
                                    label_obj.animate.set_opacity(1.0),
                                    run_time=run_time,
                                )
                                current_time += run_time
                            else:
                                self.wait(run_time)
                                current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time

                        object_registry[step.id] = cycle_obj
                        step_zone_map[step.id] = step.zone
                        handled = True

                    elif mode == "noise_node":
                        # Internal noise specks appear inside the DATA node —
                        # signals that raw data is imperfect.
                        # AUDIT FIX: replaced whole-node jitter with internal speck animation.
                        # Jitter felt cartoonish. Specks inside the node feel like
                        # "the data has noise in it," not "the diagram is shaking."
                        node_label  = step.params.get("node_label", "DATA")
                        node_labels = getattr(cycle_obj, "cycle_labels", [])
                        node_list   = getattr(cycle_obj, "cycle_nodes",  [])
                        try:
                            idx         = node_labels.index(node_label)
                            target_node = node_list[idx]
                        except (ValueError, IndexError):
                            target_node = None

                        if target_node is not None:
                            center = target_node.get_center()
                            node_r = step.params.get("node_radius", 0.42)
                            # Six small irregular specks scattered inside the node
                            speck_offsets = [
                                np.array([ 0.16,  0.10, 0]),
                                np.array([-0.18,  0.05, 0]),
                                np.array([ 0.05, -0.16, 0]),
                                np.array([-0.08,  0.18, 0]),
                                np.array([ 0.20, -0.06, 0]),
                                np.array([-0.14, -0.12, 0]),
                            ]
                            specks = VGroup(
                                *[
                                    Dot(center + off, radius=0.026, color=MUTED).set_opacity(0.0)
                                    for off in speck_offsets
                                ]
                            )
                            self.add(specks)
                            # Fade specks in with stagger — they appear like data noise
                            self.play(
                                AnimationGroup(
                                    *[s.animate.set_opacity(0.52) for s in specks],
                                    lag_ratio=0.10,
                                ),
                                run_time=run_time * 0.45,
                            )
                            # Hold briefly — data is messy
                            self.wait(run_time * 0.20)
                            # Dim slightly but leave residue — the imperfection persists
                            self.play(
                                AnimationGroup(
                                    *[s.animate.set_opacity(0.22) for s in specks],
                                    lag_ratio=0.0,
                                ),
                                run_time=run_time * 0.35,
                            )
                            current_time += run_time
                            # Attach specks to the node so they travel with it
                            target_node.add(specks)
                            target_node.noise_specks = specks
                        else:
                            self.wait(run_time)
                            current_time += run_time

                        object_registry[step.id] = cycle_obj
                        step_zone_map[step.id] = step.zone
                        handled = True

                    elif mode == "internal_node":
                        # Convergence animation inside a single named node.
                        # Used for TRAINING beat — "something learning inside here."
                        # Three faint dots converge toward center, then fade out.
                        # AUDIT FIX: color changed from ACCENT to MUTED (dim white).
                        # Brief says color restraint — only amber for evaluation warning.
                        node_label  = step.params.get("node_label", "TRAINING")
                        node_labels = getattr(cycle_obj, "cycle_labels", [])
                        node_list   = getattr(cycle_obj, "cycle_nodes",  [])
                        try:
                            idx         = node_labels.index(node_label)
                            target_node = node_list[idx]
                        except (ValueError, IndexError):
                            target_node = None

                        if target_node is not None:
                            center      = target_node.get_center()
                            node_r_val  = step.params.get("node_radius", 0.42)
                            angles      = [PI * 0.18, PI * 0.78, PI * 1.45]
                            inner_dots  = VGroup(
                                *[
                                    Dot(
                                        center + np.array([
                                            np.cos(a) * node_r_val * 0.60,
                                            np.sin(a) * node_r_val * 0.60,
                                            0,
                                        ]),
                                        radius=0.030,
                                        color=MUTED,        # dim white — no color drama
                                    ).set_opacity(0.0)
                                    for a in angles
                                ]
                            )
                            self.add(inner_dots)
                            self.play(
                                AnimationGroup(*[d.animate.set_opacity(0.65) for d in inner_dots], lag_ratio=0.14),
                                run_time=run_time * 0.24,
                            )
                            self.play(
                                AnimationGroup(
                                    *[d.animate.move_to(center + (d.get_center() - center) * 0.15)
                                      for d in inner_dots],
                                    lag_ratio=0.12,
                                ),
                                run_time=run_time * 0.44,
                            )
                            self.play(
                                inner_dots.animate.set_opacity(0.0),
                                run_time=run_time * 0.32,
                            )
                            self.remove(inner_dots)
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time

                        object_registry[step.id] = cycle_obj
                        step_zone_map[step.id] = step.zone
                        handled = True

                    elif mode == "close_loop":
                        # ISSUE 5 FIX: Do NOT ReplacementTransform the existing diagram.
                        # The existing cycle_obj stays on screen exactly as-is.
                        # We only build the return arc geometry and Create it on top.
                        merged_params = dict(step.params)
                        merged_params["complete"] = True
                        arc_obj = build_object(
                            {
                                "id": step.id,
                                "action": "show_workflow_cycle",
                                "params": merged_params,
                                "zone": step.zone,
                            }
                        )
                        ret_arrow = getattr(arc_obj, "cycle_return", VGroup())

                        if len(ret_arrow) > 0:
                            # Add only the return arc — the existing diagram nodes stay untouched
                            self.add(ret_arrow)
                            self.play(
                                Create(ret_arrow),
                                run_time=run_time,
                            )
                            current_time += run_time
                            # Attach the arc to the existing cycle_obj so future pulses find it
                            cycle_obj.add(ret_arrow)
                            cycle_obj.cycle_return = ret_arrow
                        else:
                            self.wait(run_time)
                            current_time += run_time

                        # Keep cycle_obj as the registered object — only arc was added
                        object_registry[step.id] = cycle_obj
                        step_zone_map[step.id]   = step.zone
                        active_objects[step.zone] = cycle_obj
                        handled = True

                    elif mode == "pulse_all":
                        # Unified brightness pulse — scene resolution beat.
                        nodes = getattr(cycle_obj, "cycle_nodes", [])
                        if nodes:
                            self.play(
                                AnimationGroup(
                                    *[n.animate.set_opacity(1.0) for n in nodes],
                                    lag_ratio=0.0,
                                ),
                                run_time=run_time * 0.35,
                            )
                            self.play(
                                AnimationGroup(
                                    *[n.animate.set_opacity(0.88) for n in nodes],
                                    lag_ratio=0.0,
                                ),
                                run_time=run_time * 0.65,
                            )
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time

                        object_registry[step.id] = cycle_obj
                        step_zone_map[step.id] = step.zone
                        handled = True

                    else:
                        print(f"[mutate_workflow_cycle] WARNING: unknown mode={mode}. Skipping.")
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
                            # Keep marks on enough points that the pause-frame reads as
                            # labeled data, while avoiding a noisy tick on every dot.
                            if point_index % 3 == 0:
                                held_label_ticks.add(taxonomy_label_marks(dot, color))
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
                                        FadeIn(local_points, scale=1.03),
                                        AnimationGroup(*[halo.animate.set_opacity(0.060) for halo in group_items], lag_ratio=0.0),
                                        FadeOut(local_points, scale=1.45),
                                        lag_ratio=0.0,
                                    )
                                )
                            self.play(
                                AnimationGroup(Succession(*pulse_groups), *label_anims, lag_ratio=0.0),
                                run_time=run_time * 0.46,
                            )
                            self.play(target_glows.animate.set_opacity(0.42), run_time=run_time * 0.10)
                            self.wait(run_time * 0.34)
                            current_time += run_time * 0.90
                        else:
                            self.play(AnimationGroup(*label_anims, lag_ratio=0.0), run_time=run_time)
                            current_time += run_time
                        self.remove(source_obj)
                        self.add(new_obj)
                        target_new_glows = getattr(new_obj, "taxonomy_glows", VGroup())
                        target_dot_items = list(getattr(getattr(new_obj, "taxonomy_points", VGroup()), "dot_items", []))
                        carried_label_marks = VGroup()
                        supervised_classes = merged_params.get("classes", [])
                        for point_index, dot in enumerate(target_dot_items):
                            if point_index >= len(supervised_classes) or point_index % 3 != 0:
                                continue
                            color = TAXONOMY_COLORS["amber"] if supervised_classes[point_index] == "a" else TAXONOMY_COLORS["blue"]
                            carried_label_marks.add(taxonomy_label_marks(dot, color))
                        if len(carried_label_marks) != 0:
                            new_obj.add(carried_label_marks)
                            new_obj.taxonomy_label_marks = carried_label_marks
                        if len(target_new_glows) != 0:
                            target_new_glows.set_opacity(0.42)
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
                            self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=run_time * 0.58)
                            self.wait(run_time * 0.42)
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
                            cloud_breath.set_opacity(0.92)
                            hold_anims.append(Succession(Transform(source_clouds, cloud_breath), source_clouds.animate.set_opacity(0.82)))
                        if hold_anims:
                            self.play(AnimationGroup(*hold_anims, lag_ratio=0.0), run_time=run_time * 0.22)
                            self.wait(run_time * 0.78)
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
                            self.play(AnimationGroup(Succession(*anchor_steps), *label_anims, lag_ratio=0.0), run_time=run_time * 0.30)
                            self.wait(run_time * 0.70)
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
                                anims.append(Succession(*halo_stages, AnimationGroup(*[halo.animate.set_opacity(0.72) for halo in ordered_influence], lag_ratio=0.0)))
                        if len(territories) != 0:
                            for territory in territories:
                                territory.set_opacity(0)
                            self.add(territories)
                            anims.append(
                                Succession(
                                    Wait(run_time * 0.10),
                                    territories.animate.set_opacity(1.0),
                                    Wait(run_time * 0.24),
                                    Transform(territories, held_territories),
                                )
                            )
                        if anims:
                            self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=run_time * 0.52)
                            self.wait(run_time * 0.48)
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        self.remove(source_obj)
                        if len(territories) != 0:
                            self.remove(territories)
                        if len(influence) != 0:
                            influence.set_opacity(0.72)
                            new_obj.add(influence)
                            new_obj.taxonomy_influence = influence
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
                        source_influence = getattr(source_obj, "taxonomy_influence", VGroup())
                        source_territories = getattr(source_obj, "taxonomy_influence_territories", VGroup())
                        if len(source_influence) != 0:
                            new_obj.add(source_influence)
                            new_obj.taxonomy_influence = source_influence
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
                            steady_territories.set_opacity(1.0)
                            hold_parts.append(Transform(source_territories, steady_territories))
                        if len(source_influence) != 0:
                            steady_influence = source_influence.copy()
                            steady_influence.set_opacity(0.88)
                            hold_parts.append(Transform(source_influence, steady_influence))
                        if hold_parts:
                            self.play(AnimationGroup(*hold_parts, lag_ratio=0.0), run_time=run_time * 0.24)
                            self.wait(run_time * 0.76)
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