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
    MUTED,
    SECONDARY,
    TEXT_MAIN,
    TEXT_SUB,
    WARNING,
    TAXONOMY_COLORS,
    ZONE_POSITIONS,
    _as_vector,
    build_object,
    make_manual_rule_force_indicator,
    make_links,
    make_linear_regression_fit,
    make_linear_formula_system,
    make_error_minimization_system,
    make_regularization_lasso_system,
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

        def workflow_loop_positions_for(params=None):
            params = params or {}
            raw_positions = params.get("positions", {})
            defaults = {
                "data": [-3.65, 0.62, 0],
                "preprocessing": [-1.34, 0.82, 0],
                "training": [1.02, 0.60, 0],
                "evaluation": [3.08, -0.44, 0],
                "improvement": [-1.62, -1.42, 0],
            }
            return {
                key: vector_from_param(raw_positions.get(key), vector_from_param(value))
                for key, value in defaults.items()
            }

        def workflow_loop_source_id(step):
            source_id = step.params.get("source_id")
            if source_id:
                return source_id
            for prior_id in reversed(list(object_registry.keys())):
                obj = object_registry.get(prior_id)
                if hasattr(obj, "workflow_loop_nodes"):
                    return prior_id
            return None

        def register_workflow_loop(step_id, zone_name, obj):
            register_object(step_id, zone_name, obj)

        def get_workflow_loop_source(source_id, zone_name):
            if source_id and source_id in object_registry:
                return object_registry[source_id]
            active = active_objects.get(zone_name)
            if active is not None and hasattr(active, "workflow_loop_nodes"):
                return active
            for obj in reversed(list(object_registry.values())):
                if hasattr(obj, "workflow_loop_nodes"):
                    return obj
            return None

        def workflow_loop_node(key, params=None):
            params = params or {}
            positions = workflow_loop_positions_for(params)
            labels = {
                "data": "DATA",
                "preprocessing": "PREPROCESSING",
                "training": "TRAINING",
                "evaluation": "EVALUATION",
                "improvement": "IMPROVEMENT",
            }
            pos = positions[key]
            radius = params.get("node_radius", 0.38)
            halo = Circle(radius=radius + 0.12, stroke_color=SECONDARY, stroke_width=1.0)
            halo.set_stroke(opacity=0.14)
            halo.move_to(pos)
            ring = Circle(radius=radius, stroke_color=SECONDARY, stroke_width=2.25)
            ring.set_fill("#0c1624", opacity=0.64)
            ring.move_to(pos)
            dot = Dot(pos, radius=0.040, color=SECONDARY).set_opacity(0.62)
            label = Text(labels[key], font_size=18, color=TEXT_MAIN, weight=MEDIUM)
            fit_width = 1.34 if key in {"preprocessing", "improvement"} else 1.10
            if label.width > fit_width:
                label.scale(fit_width / label.width)
            label.next_to(ring, DOWN, buff=0.18)
            label.set_opacity(0.90)
            node = VGroup(halo, ring, dot, label)
            node.workflow_key = key
            return node

        def workflow_loop_arrow(from_key, to_key, params=None, curved=False, reverse=False):
            params = params or {}
            positions = workflow_loop_positions_for(params)
            radius = params.get("node_radius", 0.38)
            start = positions[from_key]
            end = positions[to_key]
            direction = end - start
            norm = np.linalg.norm(direction)
            unit = direction / norm if norm else RIGHT
            start = start + unit * (radius + 0.08)
            end = end - unit * (radius + 0.10)
            if curved:
                angle = params.get("loop_angle", -TAU * 0.18 if reverse else -TAU * 0.11)
                arrow = CurvedArrow(start, end, angle=angle, color=SECONDARY, stroke_width=1.8, tip_length=0.13)
            else:
                arrow = Arrow(
                    start,
                    end,
                    buff=0.0,
                    color=SECONDARY,
                    stroke_width=1.8,
                    tip_length=0.13,
                    max_stroke_width_to_length_ratio=10,
                )
            arrow.set_opacity(0.82)
            return arrow

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
                # Soft density only. Opacities are intentionally lower on the
                # held state so the clusters do not bloom into bright white.
                layer_specs = (
                    (0.76, 0.040 if held else 0.060, np.array([0.00, 0.00, 0.0])),
                    (0.52, 0.032 if held else 0.046, np.array([0.18 * np.cos(phase), 0.10 * np.sin(phase), 0.0])),
                    (0.36, 0.026 if held else 0.036, np.array([-0.16 * np.sin(phase), 0.12 * np.cos(phase), 0.0])),
                )
                for scale, opacity, offset in layer_specs:
                    glow = Dot(center + offset, radius=radius * scale, color=TAXONOMY_COLORS["cluster"])
                    glow.set_opacity(opacity)
                    cloud_group.add(glow)
                ghosts.add(cloud_group)
            return ghosts

        def taxonomy_density_glints(params, max_lines=42):
            points = [vector_from_param(point) for point in params.get("points", [])]
            clusters = params.get("clusters", [])
            lines = VGroup()
            for cluster in clusters:
                center = vector_from_param(cluster.get("center"))
                radius = cluster.get("radius", 1.0)
                local = [point for point in points if np.linalg.norm(point - center) <= radius * 0.90]
                local.sort(key=lambda point: (point[0], point[1]))
                created = 0
                for index, point in enumerate(local):
                    candidates = sorted(
                        local[index + 1:],
                        key=lambda other: np.linalg.norm(point - other),
                    )
                    for other in candidates[:2]:
                        distance = np.linalg.norm(point - other)
                        if 0.18 <= distance <= radius * 0.55 and created < max_lines:
                            line = Line(point, other, color=TAXONOMY_COLORS["cluster"], stroke_width=0.85)
                            line.set_opacity(0.22)
                            lines.add(line)
                            created += 1
                        if created >= max_lines:
                            break
                    if created >= max_lines:
                        break
            return lines

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
            for anchor in anchors:
                point_index = anchor.get("index")
                if point_index is None or not 0 <= point_index < len(points):
                    continue
                color = TAXONOMY_COLORS["amber"] if anchor.get("class", "a") == "a" else TAXONOMY_COLORS["blue"]
                center = vector_from_param(points[point_index])
                local_points = []
                for other_index, raw_point in enumerate(points):
                    if other_index == point_index:
                        continue
                    point = vector_from_param(raw_point)
                    distance = np.linalg.norm(point - center)
                    if 0.20 < distance <= 1.25:
                        local_points.append((distance, point))
                local_points.sort(key=lambda item: item[0])
                influence_lines = VGroup()
                for distance, point in local_points[:9]:
                    amount = max(0.0, 1.0 - distance / 1.25)
                    line = Line(center, point, color=color, stroke_width=1.05)
                    line.set_opacity((0.18 if held else 0.24) * amount)
                    influence_lines.add(line)
                anchor_halo = Dot(center, radius=0.34 if held else 0.42, color=color)
                anchor_halo.set_opacity(0.045 if held else 0.065)
                territories.add(VGroup(anchor_halo, influence_lines))
            return territories

        def taxonomy_reward_residue(point, color, amount=1.0):
            residue = Dot(point, radius=0.070 + 0.035 * amount, color=color)
            residue.set_opacity(0.070 * amount)
            return residue

        def register_under_existing_id(source_id, zone_name, obj):
            object_registry[source_id] = obj
            step_zone_map[source_id] = zone_name
            active_objects[zone_name] = obj

        workflow_loop_positions = {
            "data": np.array([-4.15, 0.65, 0.0]),
            "preprocessing": np.array([-1.72, 1.08, 0.0]),
            "training": np.array([0.95, 0.82, 0.0]),
            "evaluation": np.array([3.45, -0.38, 0.0]),
            "improvement": np.array([-1.95, -1.65, 0.0]),
        }
        workflow_loop_labels = {
            "data": "DATA",
            "preprocessing": "PREPROCESSING",
            "training": "TRAINING",
            "evaluation": "EVALUATION",
            "improvement": "IMPROVEMENT",
        }

        def workflow_loop_node(key, warning=False):
            pos = workflow_loop_positions[key]
            radius = 0.36
            color = "#E8A838" if warning else "#56D7E6"
            fill = "#1a1006" if warning else "#0c1624"
            halo = Circle(radius=radius + 0.10, stroke_color=color, stroke_width=0.85)
            halo.set_stroke(opacity=0.10 if not warning else 0.17)
            halo.move_to(pos)
            ring = Circle(radius=radius, stroke_color=color, stroke_width=1.65)
            ring.set_fill(fill, opacity=0.55 if not warning else 0.62)
            ring.move_to(pos)
            center_dot = Dot(pos, radius=0.034, color=color).set_opacity(0.50)
            label = Text(workflow_loop_labels[key], font_size=14, color=TEXT_MAIN, weight=MEDIUM)
            if label.width > 1.28:
                label.scale(1.28 / label.width)
            label.next_to(ring, DOWN, buff=0.24)
            label.set_opacity(0.76)
            node = VGroup(halo, ring, center_dot, label)
            node.workflow_key = key
            return node

        def workflow_loop_arrow(from_key, to_key, curved=False, reverse=False):
            start = workflow_loop_positions[from_key]
            end = workflow_loop_positions[to_key]
            direction = end - start
            length = np.linalg.norm(direction)
            if length == 0:
                return VGroup()
            unit = direction / length
            start = start + unit * 0.50
            end = end - unit * 0.50
            if curved:
                arrow = CurvedArrow(
                    start,
                    end,
                    angle=-TAU * 0.09 if reverse else -TAU * 0.065,
                    color="#56D7E6",
                    stroke_width=1.15,
                    tip_length=0.085,
                )
                arrow.set_opacity(0.42 if reverse else 0.48)
                return arrow
            arrow = Arrow(start, end, buff=0.0, color="#9FB7C9", stroke_width=1.35, tip_length=0.10, max_stroke_width_to_length_ratio=10)
            arrow.set_opacity(0.56)
            return arrow

        def get_workflow_loop_source(source_id, fallback_zone="center"):
            workflow_obj = object_registry.get(source_id)
            if workflow_obj is None:
                workflow_obj = active_objects.get(fallback_zone)
            return workflow_obj

        def register_workflow_loop(step_id, zone_name, workflow_obj):
            object_registry[step_id] = workflow_obj
            step_zone_map[step_id] = zone_name
            active_objects[zone_name] = workflow_obj

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
            "show_workflow_loop",
            "mutate_workflow_loop",
            "mutate_road_ahead_field",
            "show_supervised_field",
            "mutate_supervised_field",
            "show_supervised_examples",
            "show_supervised_resolution",
            "show_supervised_types_showcase",
            "show_classification_regression_field",
            "mutate_classification_regression_field",
            "show_linear_regression_fit",
            "mutate_linear_regression_fit",
            "show_linear_formula_system",
            "mutate_linear_formula_system",
            "show_error_minimization_system",
            "mutate_error_minimization_system",
            "show_regularization_lasso_system",
            "mutate_regularization_lasso_system",
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

                elif step.action == "show_workflow_loop":
                    merged_params = dict(step.params)
                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": merged_params,
                            "zone": step.zone,
                        }
                    )
                    existing = active_objects.get(step.zone)
                    if existing is not None:
                        self.play(FadeOut(existing), run_time=min(0.25, run_time * 0.25))
                        clear_zone(step.zone)
                    node = list(new_obj)[0] if len(new_obj) else new_obj
                    ring = node[1] if hasattr(node, "__len__") and len(node) > 1 else node
                    halo = node[0] if hasattr(node, "__len__") and len(node) > 0 else None
                    dot = node[2] if hasattr(node, "__len__") and len(node) > 2 else None
                    anims = [Create(ring)]
                    if halo is not None:
                        anims.append(FadeIn(halo))
                    if dot is not None:
                        anims.append(FadeIn(dot, scale=1.15))
                    self.add(new_obj)
                    self.play(AnimationGroup(*anims, lag_ratio=0.12), run_time=run_time)
                    current_time += run_time
                    register_workflow_loop(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "mutate_workflow_loop":
                    source_id = workflow_loop_source_id(step)
                    workflow_obj = get_workflow_loop_source(source_id, step.zone)
                    if workflow_obj is None:
                        print(f"[mutate_workflow_loop] WARNING: source_id={source_id} not found. Skipping.")
                        handled = True
                        continue

                    if not hasattr(workflow_obj, "workflow_loop_nodes"):
                        workflow_obj.workflow_loop_nodes = {}
                    if not hasattr(workflow_obj, "workflow_loop_arrows"):
                        workflow_obj.workflow_loop_arrows = {}
                    if not hasattr(workflow_obj, "workflow_loop_effects"):
                        workflow_obj.workflow_loop_effects = VGroup()

                    mode = step.params.get("mode", "pulse_all")
                    nodes = workflow_obj.workflow_loop_nodes
                    arrows = workflow_obj.workflow_loop_arrows

                    if mode == "label_data":
                        data_node = nodes.get("data")
                        if data_node is not None:
                            label = Text("DATA", font_size=15, color=TEXT_MAIN, weight=MEDIUM)
                            label.next_to(data_node[1], DOWN, buff=0.24)
                            label.set_opacity(0.0)
                            data_node.add(label)
                            self.add(label)
                            self.play(
                                AnimationGroup(label.animate.set_opacity(0.78), Indicate(data_node[1], color="#56D7E6", scale_factor=1.04), lag_ratio=0.0),
                                run_time=run_time,
                            )
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        register_workflow_loop(step.id, step.zone, workflow_obj)
                        handled = True

                    elif mode == "data_noise":
                        data_node = nodes.get("data")
                        if data_node is not None:
                            center = data_node[1].get_center()
                            offsets = [
                                np.array([0.15, 0.11, 0]),
                                np.array([-0.16, 0.06, 0]),
                                np.array([0.07, -0.16, 0]),
                                np.array([-0.06, 0.18, 0]),
                                np.array([0.19, -0.05, 0]),
                            ]
                            specks = VGroup(*[Dot(center + off, radius=0.025, color="#AEB8C5").set_opacity(0.0) for off in offsets])
                            slash = Line(center + LEFT * 0.20 + DOWN * 0.17, center + RIGHT * 0.20 + DOWN * 0.11, color="#E8A838", stroke_width=1.5).set_opacity(0.0)
                            effect = VGroup(specks, slash)
                            self.add(effect)
                            self.play(
                                AnimationGroup(*[s.animate.set_opacity(0.55) for s in specks], slash.animate.set_opacity(0.50), lag_ratio=0.10),
                                run_time=run_time * 0.55,
                            )
                            self.play(effect.animate.set_opacity(0.22), run_time=run_time * 0.45)
                            data_node.add(effect)
                            workflow_obj.workflow_loop_effects.add(effect)
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        register_workflow_loop(step.id, step.zone, workflow_obj)
                        handled = True

                    elif mode in {"add_preprocessing", "add_training", "add_evaluation_neutral", "add_improvement_bend"}:
                        spec = {
                            "add_preprocessing": ("data", "preprocessing", False),
                            "add_training": ("preprocessing", "training", False),
                            "add_evaluation_neutral": ("training", "evaluation", True),
                            "add_improvement_bend": ("evaluation", "improvement", True),
                        }[mode]
                        from_key, to_key, curved = spec
                        new_arrow = workflow_loop_arrow(from_key, to_key, curved=curved)
                        new_node = workflow_loop_node(to_key)
                        arrows[f"{from_key}_{to_key}"] = new_arrow
                        nodes[to_key] = new_node
                        workflow_obj.add(new_arrow, new_node)
                        if from_key == "data" and "data" in nodes:
                            noise = getattr(nodes["data"], "noise_specks", None)
                            if noise is not None:
                                noise.set_opacity(0.10)
                        node_ring = new_node[1] if len(new_node) > 1 else new_node
                        node_label = new_node[3] if len(new_node) > 3 else None
                        self.add(new_arrow, new_node)
                        node_parts = [Create(node_ring), FadeIn(new_node[0]), FadeIn(new_node[2])]
                        if node_label is not None:
                            node_parts.append(FadeIn(node_label, shift=UP * 0.03))
                        self.play(Create(new_arrow), run_time=run_time * 0.42, rate_func=rate_functions.ease_out_sine)
                        self.play(AnimationGroup(*node_parts, lag_ratio=0.0), run_time=run_time * 0.38)
                        if to_key == "training":
                            center = node_ring.get_center()
                            dots = VGroup(
                                Dot(center + LEFT * 0.18 + UP * 0.08, radius=0.026, color="#AEB8C5"),
                                Dot(center + RIGHT * 0.17 + UP * 0.04, radius=0.026, color="#AEB8C5"),
                                Dot(center + DOWN * 0.17, radius=0.026, color="#AEB8C5"),
                            )
                            self.add(dots)
                            self.play(AnimationGroup(*[d.animate.move_to(center + (d.get_center() - center) * 0.18) for d in dots], lag_ratio=0.05), run_time=run_time * 0.20)
                            self.play(FadeOut(dots), run_time=run_time * 0.10)
                            current_time += run_time * 0.20 + run_time * 0.10
                        else:
                            self.wait(run_time * 0.20)
                            current_time += run_time * 0.20
                        current_time += run_time * 0.80
                        register_workflow_loop(step.id, step.zone, workflow_obj)
                        handled = True

                    elif mode == "evaluation_warning":
                        eval_node = nodes.get("evaluation")
                        if eval_node is not None:
                            ring = eval_node[1]
                            halo = eval_node[0]
                            warn = Circle(radius=0.50, stroke_color="#E8A838", stroke_width=1.05).move_to(ring.get_center()).set_stroke(opacity=0.0)
                            cue = VGroup(
                                Line(ring.get_center() + LEFT * 0.16 + DOWN * 0.04, ring.get_center() + LEFT * 0.02 + UP * 0.10, color="#56D7E6", stroke_width=1.15),
                                Line(ring.get_center() + RIGHT * 0.03 + UP * 0.09, ring.get_center() + RIGHT * 0.18 + DOWN * 0.08, color="#E8A838", stroke_width=1.25),
                            ).set_opacity(0.0)
                            self.add(warn, cue)
                            self.play(
                                AnimationGroup(
                                    ring.animate.set_stroke(color="#E8A838", width=1.9).set_fill(color="#1a1006", opacity=0.62),
                                    halo.animate.set_stroke(color="#E8A838", opacity=0.16),
                                    warn.animate.set_stroke(opacity=0.20),
                                    cue.animate.set_opacity(0.66),
                                    lag_ratio=0.0,
                                ),
                                run_time=run_time * 0.72,
                            )
                            self.play(warn.animate.set_stroke(opacity=0.09), run_time=run_time * 0.28)
                            eval_node.add(warn, cue)
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        register_workflow_loop(step.id, step.zone, workflow_obj)
                        handled = True

                    elif mode == "feedback_motion":
                        improve_node = nodes.get("improvement")
                        data_node = nodes.get("data")
                        if improve_node is not None and data_node is not None:
                            start = workflow_loop_positions["improvement"] + UP * 0.18
                            dots = VGroup(
                                Dot(start + RIGHT * 0.00 + UP * 0.02, radius=0.030, color="#56D7E6").set_opacity(0.0),
                                Dot(start + LEFT * 0.16 + UP * 0.08, radius=0.026, color="#56D7E6").set_opacity(0.0),
                                Dot(start + LEFT * 0.32 + UP * 0.14, radius=0.023, color="#56D7E6").set_opacity(0.0),
                            )
                            self.add(dots)
                            self.play(AnimationGroup(*[d.animate.set_opacity(0.38) for d in dots], lag_ratio=0.10), run_time=run_time * 0.35)
                            self.play(AnimationGroup(*[d.animate.shift(LEFT * 0.22 + UP * 0.04).set_opacity(0.14) for d in dots], lag_ratio=0.08), run_time=run_time * 0.45)
                            self.play(FadeOut(dots), run_time=run_time * 0.20)
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        register_workflow_loop(step.id, step.zone, workflow_obj)
                        handled = True

                    elif mode == "close_loop":
                        if "improvement_data" not in arrows:
                            loop_arrow = workflow_loop_arrow("improvement", "data", curved=True, reverse=True)
                            arrows["improvement_data"] = loop_arrow
                            workflow_obj.add(loop_arrow)
                            self.add(loop_arrow)
                            self.play(Create(loop_arrow), run_time=run_time * 0.72, rate_func=rate_functions.ease_out_sine)
                            pulse_targets = list(nodes.values()) + list(arrows.values())
                            self.play(AnimationGroup(*[Indicate(obj, color="#56D7E6", scale_factor=1.012) for obj in pulse_targets], lag_ratio=0.03), run_time=run_time * 0.28)
                            current_time += run_time
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        register_workflow_loop(step.id, step.zone, workflow_obj)
                        handled = True

                    elif mode == "final_hold":
                        self.wait(run_time)
                        current_time += run_time
                        register_workflow_loop(step.id, step.zone, workflow_obj)
                        handled = True

                    else:
                        print(f"[mutate_workflow_loop] WARNING: unknown mode={mode}. Skipping.")
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

                elif step.action == "show_linear_regression_fit":
                    # ── Beat 1: immediate topic setup + visible labeled data.
                    # This avoids the previous empty/abstract opening while keeping
                    # narration unchanged.
                    params = dict(step.params)
                    field_obj = make_linear_regression_fit(params, step.zone)

                    replace_zone = step.replace
                    outgoing_anims = []
                    if replace_zone is not None:
                        existing = active_objects.get(replace_zone)
                        if existing is not None:
                            outgoing = transition_out_for(existing, step.transition_out or "fade")
                            if outgoing is not None:
                                outgoing_anims.append(outgoing)
                            clear_zone(replace_zone)

                    if outgoing_anims:
                        out_rt = min(0.35, max(0.05, run_time * 0.12))
                        self.play(AnimationGroup(*outgoing_anims, lag_ratio=0.0), run_time=out_rt)
                        current_time += out_rt

                    vignette = getattr(field_obj, "lr_vignette", VGroup())
                    axes = getattr(field_obj, "lr_axes", VGroup())
                    x_axis = getattr(field_obj, "lr_x_axis", None)
                    y_axis = getattr(field_obj, "lr_y_axis", None)
                    live_line = getattr(field_obj, "lr_live_line", None)
                    residuals = list(getattr(field_obj, "lr_residuals", VGroup()))
                    dots = list(getattr(field_obj, "lr_dots", VGroup()))
                    sorted_dots = list(getattr(field_obj, "lr_point_order", dots))
                    trend_line = getattr(field_obj, "lr_trend_line", None)
                    axis_extras = [
                        getattr(field_obj, "lr_x_tip", None),
                        getattr(field_obj, "lr_y_tip", None),
                        getattr(field_obj, "lr_origin_dot", None),
                        getattr(field_obj, "lr_tick_marks", None),
                    ]

                    # Stash axis endpoints before collapsed intro state.
                    if x_axis is not None and y_axis is not None:
                        field_obj._lr_x_start = x_axis.get_start().copy()
                        field_obj._lr_x_end = x_axis.get_end().copy()
                        field_obj._lr_y_start = y_axis.get_start().copy()
                        field_obj._lr_y_end = y_axis.get_end().copy()
                        x_axis.put_start_and_end_on(field_obj._lr_x_start, field_obj._lr_x_start)
                        y_axis.put_start_and_end_on(field_obj._lr_y_start, field_obj._lr_y_start)

                    # Everything is added up-front in hidden/initial states so
                    # later mutations never rebuild or pop in randomly.
                    for extra in axis_extras:
                        if extra is not None:
                            extra.set_opacity(0.0)
                    if vignette is not None:
                        vignette.set_opacity(params.get("vignette_opacity", 0.13))
                        self.add(vignette)
                    self.add(axes)
                    if trend_line is not None:
                        trend_line.set_opacity(0.0)
                        self.add(trend_line)
                    if live_line is not None:
                        self.add(live_line)
                    for residual in residuals:
                        self.add(residual)
                    for dot in dots:
                        dot.set_fill(opacity=0.0)
                        dot.set_stroke(opacity=0.0)
                    self.add(*dots)

                    always_hidden = [
                        "lr_x_label", "lr_y_label", "lr_data_caption", "lr_trend_caption",
                        "lr_guess_label", "lr_adjust_label", "lr_residual_label",
                        "lr_best_fit_label", "lr_formula_teaser", "lr_formula_caption",
                    ]
                    title = getattr(field_obj, "lr_title", None)
                    subtitle = getattr(field_obj, "lr_subtitle", None)
                    for attr in always_hidden:
                        label = getattr(field_obj, attr, None)
                        if label is not None:
                            label.set_opacity(0.0)
                            self.add(label)
                    for label in (title, subtitle):
                        if label is not None:
                            label.set_opacity(0.0)
                            self.add(label)

                    # Immediate title/subtitle: first frame is never blank.
                    title_anims = []
                    if title is not None:
                        title_anims.append(FadeIn(title, shift=DOWN * 0.08))
                    if subtitle is not None:
                        title_anims.append(FadeIn(subtitle, shift=DOWN * 0.08))
                    if title_anims:
                        title_rt = params.get("title_duration", 0.75)
                        self.play(AnimationGroup(*title_anims, lag_ratio=0.08), run_time=title_rt)
                        current_time += title_rt

                    # Beat 1 stays as topic/concept setup only. The actual
                    # student dots appear in Beat 2, exactly when the unchanged
                    # narration introduces students and says the points appear.
                    hold_rt = params.get("beat1_hold", 0.35)
                    if hold_rt > 0:
                        self.wait(hold_rt)
                        current_time += hold_rt

                    register_object(step.id, step.zone, field_obj)
                    handled = True

                elif step.action == "mutate_linear_regression_fit":
                    # ── Beats 2-8: anchored mutations of one persistent labeled field.
                    source_id = step.params.get("source_id")
                    field_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)

                    if field_obj is None:
                        raise RuntimeError(f"mutate_linear_regression_fit could not find source_id={source_id!r}")

                    beat = step.params.get("beat", 2)
                    params = dict(step.params)
                    segment_duration = duration_map[step.anchor]

                    def capped(name, default, floor=0.15, reserve=0.25):
                        requested = float(params.get(name, default))
                        available = max(floor, segment_duration - float(step.offset) - reserve)
                        return max(floor, min(requested, available))

                    x_axis = getattr(field_obj, "lr_x_axis", None)
                    y_axis = getattr(field_obj, "lr_y_axis", None)
                    axes = getattr(field_obj, "lr_axes", VGroup())
                    dots = list(getattr(field_obj, "lr_dots", VGroup()))
                    slope = getattr(field_obj, "lr_slope", None)
                    intercept = getattr(field_obj, "lr_intercept", None)
                    line_progress = getattr(field_obj, "lr_line_progress", None)
                    line_width = getattr(field_obj, "lr_line_width", None)
                    line_opacity = getattr(field_obj, "lr_line_opacity", None)
                    line_color_mix = getattr(field_obj, "lr_line_color_mix", None)
                    residual_progress = getattr(field_obj, "lr_residual_progress", [])
                    residual_opacity = getattr(field_obj, "lr_residual_opacity", [])
                    residual_desaturation = getattr(field_obj, "lr_residual_desaturation", None)
                    point_bright_color = getattr(field_obj, "lr_point_bright_color", "#FFF3D8")

                    def lbl(name):
                        return getattr(field_obj, name, None)

                    def show_label(label, shift=UP * 0.04):
                        return FadeIn(label, shift=shift) if label is not None else Wait(0)

                    def hide_label(label):
                        return FadeOut(label) if label is not None else Wait(0)

                    def _register_lr():
                        object_registry[step.id] = field_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = field_obj

                    if beat == 2:
                        # Labeled axes + data meaning. This directly follows the
                        # unchanged narration about hours studied and marks achieved.
                        x_start = getattr(field_obj, "_lr_x_start", None)
                        x_end = getattr(field_obj, "_lr_x_end", None)
                        y_start = getattr(field_obj, "_lr_y_start", None)
                        y_end = getattr(field_obj, "_lr_y_end", None)
                        axes_rt = capped("beat2_duration", 1.0)
                        axis_anims = []
                        if x_axis is not None and y_axis is not None and x_start is not None:
                            axis_anims.extend([
                                x_axis.animate.put_start_and_end_on(x_start, x_end),
                                y_axis.animate.put_start_and_end_on(y_start, y_end),
                            ])
                        for extra in [getattr(field_obj, "lr_x_tip", None), getattr(field_obj, "lr_y_tip", None), getattr(field_obj, "lr_origin_dot", None), getattr(field_obj, "lr_tick_marks", None)]:
                            if extra is not None:
                                extra.set_opacity(0.0)
                                axis_anims.append(FadeIn(extra))
                        sorted_dots = list(getattr(field_obj, "lr_point_order", dots))
                        pulse_scale = float(getattr(field_obj, "lr_params", {}).get("point_pulse_scale", 1.24))
                        dot_anims = []
                        for dot in sorted_dots:
                            dot_anims.append(
                                Succession(
                                    dot.animate.set_fill(opacity=1.0).set_stroke(opacity=0.24).scale(pulse_scale),
                                    dot.animate.scale(1.0 / pulse_scale),
                                )
                            )
                        axis_anims.extend(dot_anims)
                        axis_anims.extend([show_label(lbl("lr_x_label")), show_label(lbl("lr_y_label")), show_label(lbl("lr_data_caption"))])
                        self.play(AnimationGroup(*axis_anims, lag_ratio=0.04), run_time=axes_rt, rate_func=rate_functions.ease_out_sine)
                        current_time += axes_rt
                        _register_lr()
                        handled = True

                    elif beat == 3:
                        # Trend recognition: brighter points + subtle diagonal cue.
                        trend_line = getattr(field_obj, "lr_trend_line", None)
                        trend_rt = capped("beat3_duration", 1.5)
                        anims = [dot.animate.set_color(point_bright_color).set_fill(opacity=1.0).set_stroke(opacity=0.28) for dot in dots]
                        if trend_line is not None:
                            anims.append(trend_line.animate.set_opacity(0.16))
                        anims.append(show_label(lbl("lr_trend_caption")))
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=trend_rt, rate_func=rate_functions.ease_in_out_sine)
                        current_time += trend_rt
                        _register_lr()
                        handled = True

                    elif beat == 4:
                        # Wrong line enters as an explained rough guess, not a random line.
                        draw_rt = capped("beat4_draw_duration", 0.75)
                        anims = []
                        if line_progress is not None:
                            anims.append(line_progress.animate.set_value(1.0))
                        if line_opacity is not None:
                            anims.append(line_opacity.animate.set_value(1.0))
                        if line_color_mix is not None:
                            anims.append(line_color_mix.animate.set_value(0.0))
                        anims.extend([hide_label(lbl("lr_data_caption")), hide_label(lbl("lr_trend_caption")), show_label(lbl("lr_guess_label"))])
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=draw_rt, rate_func=linear)
                        current_time += draw_rt
                        hold_rt = min(params.get("beat4_hold", 0.35), max(0.0, segment_duration - draw_rt - 0.2))
                        if hold_rt > 0:
                            self.wait(hold_rt)
                            current_time += hold_rt
                        _register_lr()
                        handled = True

                    elif beat == 5:
                        # Purposeful optimization path with label and color transition.
                        if slope is not None and intercept is not None:
                            if lbl("lr_adjust_label") is not None:
                                self.play(AnimationGroup(hide_label(lbl("lr_guess_label")), FadeIn(lbl("lr_adjust_label"), shift=UP * 0.04), lag_ratio=0.0), run_time=0.25)
                                current_time += 0.25
                            waypoints = params.get("waypoints", [
                                {"slope": 0.96, "intercept": 0.82, "duration": 0.75, "mix": 0.25},
                                {"slope": 0.78, "intercept": 1.05, "duration": 0.85, "mix": 0.45},
                                {"slope": 0.56, "intercept": 1.75, "duration": 0.90, "mix": 0.55},
                                {"slope": 0.82, "intercept": 0.90, "duration": 0.75, "mix": 0.62},
                                {"slope": getattr(field_obj, "lr_near_slope", 0.78), "intercept": getattr(field_obj, "lr_near_intercept", 0.95), "duration": 0.70, "mix": 0.68},
                            ])
                            total_requested = sum(float(w.get("duration", 0.7)) for w in waypoints)
                            available = capped("beat5_duration", 4.25, floor=0.8, reserve=0.15)
                            scale = available / max(total_requested, 0.01)
                            for i, wp in enumerate(waypoints):
                                wp_anims = [
                                    slope.animate.set_value(float(wp.get("slope", slope.get_value()))),
                                    intercept.animate.set_value(float(wp.get("intercept", intercept.get_value()))),
                                ]
                                if line_color_mix is not None:
                                    wp_anims.append(line_color_mix.animate.set_value(float(wp.get("mix", 0.5))))
                                if line_width is not None:
                                    wp_anims.append(line_width.animate.set_value(params.get("search_line_width", 3.0 if i % 2 == 0 else 2.75)))
                                self.play(
                                    AnimationGroup(*wp_anims, lag_ratio=0.0),
                                    run_time=max(0.12, float(wp.get("duration", 0.7)) * scale),
                                    rate_func=rate_functions.ease_in_out_sine,
                                )
                            current_time += available
                        else:
                            wait_rt = capped("beat5_duration", 4.25)
                            self.wait(wait_rt)
                            current_time += wait_rt
                        _register_lr()
                        handled = True

                    elif beat == 6:
                        # Residuals: settle first, explain one residual, then cascade.
                        lock_rt = min(params.get("beat6_lock_duration", 0.45), max(0.2, segment_duration * 0.18))
                        lock_anims = []
                        if slope is not None:
                            lock_anims.append(slope.animate.set_value(getattr(field_obj, "lr_near_slope", 0.78)))
                        if intercept is not None:
                            lock_anims.append(intercept.animate.set_value(getattr(field_obj, "lr_near_intercept", 0.95)))
                        if line_width is not None:
                            lock_anims.append(line_width.animate.set_value(2.85))
                        if lock_anims:
                            self.play(AnimationGroup(*lock_anims, lag_ratio=0.0), run_time=lock_rt, rate_func=rate_functions.ease_out_cubic)
                        else:
                            self.wait(lock_rt)
                        current_time += lock_rt

                        label_anim = show_label(lbl("lr_residual_label"), shift=UP * 0.05)
                        self.play(label_anim, run_time=0.25)
                        current_time += 0.25

                        residual_count = len(residual_progress)
                        first_index = min(residual_count - 1, residual_count // 2) if residual_count else -1
                        if first_index >= 0:
                            self.play(
                                AnimationGroup(
                                    residual_progress[first_index].animate.set_value(1.0),
                                    residual_opacity[first_index].animate.set_value(1.0),
                                    lag_ratio=0.0,
                                ),
                                run_time=params.get("single_residual_duration", 0.45),
                                rate_func=rate_functions.ease_out_sine,
                            )
                            current_time += params.get("single_residual_duration", 0.45)

                        residual_anims = []
                        for idx, (prog_tracker, opac_tracker) in enumerate(zip(residual_progress, residual_opacity)):
                            if idx == first_index:
                                continue
                            residual_anims.append(AnimationGroup(prog_tracker.animate.set_value(1.0), opac_tracker.animate.set_value(1.0), lag_ratio=0.0))
                        if residual_anims:
                            res_rt = min(params.get("beat6_residual_duration", 1.35), max(0.6, segment_duration - lock_rt - 0.8))
                            self.play(LaggedStart(*residual_anims, lag_ratio=params.get("residual_lag_ratio", 0.08)), run_time=res_rt, rate_func=rate_functions.ease_out_sine)
                            current_time += res_rt
                        _register_lr()
                        handled = True

                    elif beat == 7:
                        convergence_anims = []
                        if slope is not None and intercept is not None:
                            convergence_anims.extend([
                                slope.animate.set_value(getattr(field_obj, "lr_final_slope", 0.68)),
                                intercept.animate.set_value(getattr(field_obj, "lr_final_intercept", 1.35)),
                            ])
                        if line_width is not None:
                            convergence_anims.append(line_width.animate.set_value(params.get("final_line_width", 3.25)))
                        if line_color_mix is not None:
                            convergence_anims.append(line_color_mix.animate.set_value(1.0))
                        convergence_anims.extend([hide_label(lbl("lr_guess_label")), hide_label(lbl("lr_adjust_label")), show_label(lbl("lr_best_fit_label"))])
                        conv_rt = capped("beat7_duration", 3.2)
                        self.play(AnimationGroup(*convergence_anims, lag_ratio=0.0), run_time=conv_rt, rate_func=rate_functions.ease_out_cubic)
                        current_time += conv_rt
                        hold_rt = min(params.get("beat7_hold", 0.4), max(0.0, segment_duration - conv_rt - 0.15))
                        if hold_rt > 0:
                            self.wait(hold_rt)
                            current_time += hold_rt
                        _register_lr()
                        handled = True

                    elif beat == 8:
                        fade_anims = [tracker.animate.set_value(params.get("final_residual_opacity", 0.15)) for tracker in residual_opacity]
                        if residual_desaturation is not None:
                            fade_anims.append(residual_desaturation.animate.set_value(params.get("final_residual_desaturation", 0.75)))
                        fade_anims.extend([
                            hide_label(lbl("lr_residual_label")),
                            hide_label(lbl("lr_adjust_label")),
                            show_label(lbl("lr_formula_teaser"), shift=LEFT * 0.05),
                            show_label(lbl("lr_formula_caption"), shift=LEFT * 0.05),
                        ])
                        fade_rt = capped("beat8_duration", 1.5)
                        self.play(AnimationGroup(*fade_anims, lag_ratio=0.0), run_time=fade_rt, rate_func=rate_functions.ease_in_out_sine)
                        current_time += fade_rt
                        _register_lr()
                        handled = True

                    else:
                        print(f"[mutate_linear_regression_fit] Unknown beat={beat}. Skipping.")
                        handled = True

                elif step.action == "show_error_minimization_system":
                    # ── Video 3 Scene 5 Beat 1: open directly in the error-minimization graph world.
                    params = dict(step.params)
                    field_obj = make_error_minimization_system(params, step.zone)

                    replace_zone = step.replace
                    outgoing_anims = []
                    if replace_zone is not None:
                        existing = active_objects.get(replace_zone)
                        if existing is not None:
                            outgoing = transition_out_for(existing, step.transition_out or "fade")
                            if outgoing is not None:
                                outgoing_anims.append(outgoing)
                            clear_zone(replace_zone)
                    if outgoing_anims:
                        out_rt = min(0.35, max(0.05, run_time * 0.12))
                        self.play(AnimationGroup(*outgoing_anims, lag_ratio=0.0), run_time=out_rt)
                        current_time += out_rt

                    self.add(field_obj)
                    line_opacity = getattr(field_obj, "em_line_opacity", None)
                    focus_pulse = getattr(field_obj, "em_focus_pulse", None)
                    focus_ring_opacity = getattr(field_obj, "em_focus_ring_opacity", None)
                    intro = []
                    if line_opacity is not None:
                        intro.append(line_opacity.animate.set_value(1.0))
                    if intro:
                        self.play(AnimationGroup(*intro, lag_ratio=0.0), run_time=run_time * 0.28, rate_func=rate_functions.ease_out_sine)
                        current_time += run_time * 0.28
                    if focus_pulse is not None and focus_ring_opacity is not None:
                        self.play(
                            AnimationGroup(
                                focus_ring_opacity.animate.set_value(1.0),
                                focus_pulse.animate.set_value(1.0),
                                lag_ratio=0.0,
                            ),
                            run_time=run_time * 0.36,
                            rate_func=rate_functions.ease_out_cubic,
                        )
                        current_time += run_time * 0.36
                        self.play(focus_ring_opacity.animate.set_value(0.0), run_time=run_time * 0.12, rate_func=rate_functions.ease_in_sine)
                        current_time += run_time * 0.12
                        focus_pulse.set_value(0.0)
                    hold_rt = max(0.0, run_time * 0.24)
                    if hold_rt > 0:
                        self.wait(hold_rt)
                        current_time += hold_rt
                    register_object(step.id, step.zone, field_obj)
                    handled = True

                elif step.action == "mutate_error_minimization_system":
                    # ── Video 3 Scene 5 Beats 2-12: mutate one persistent graph/cost system.
                    source_id = step.params.get("source_id")
                    field_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)
                    if field_obj is None:
                        raise RuntimeError(f"mutate_error_minimization_system could not find source_id={source_id!r}")

                    beat = int(step.params.get("beat", 2))
                    params = dict(step.params)
                    segment_duration = duration_map[step.anchor]

                    def capped(name, default, floor=0.15, reserve=0.2):
                        requested = float(params.get(name, default))
                        available = max(floor, segment_duration - float(step.offset) - reserve)
                        return max(floor, min(requested, available))

                    focus_bar_progress = getattr(field_obj, "em_focus_bar_progress", None)
                    focus_bar_opacity = getattr(field_obj, "em_focus_bar_opacity", None)
                    focus_pulse = getattr(field_obj, "em_focus_pulse", None)
                    focus_ring_opacity = getattr(field_obj, "em_focus_ring_opacity", None)
                    sign_emphasis_opacity = getattr(field_obj, "em_sign_emphasis_opacity", None)
                    error_label = getattr(field_obj, "em_error_label", None)
                    y_labels = getattr(field_obj, "em_y_labels", None)
                    all_bar_progress = getattr(field_obj, "em_all_bar_progress", None)
                    all_bar_opacity = getattr(field_obj, "em_all_bar_opacity", None)
                    square_progress = getattr(field_obj, "em_square_progress", None)
                    square_opacity = getattr(field_obj, "em_square_opacity", None)
                    square_stroke_opacity = getattr(field_obj, "em_square_stroke_opacity", None)
                    square_fill_reveal = getattr(field_obj, "em_square_fill_reveal", None)
                    large_square_pulse = getattr(field_obj, "em_large_square_pulse", None)
                    formula = getattr(field_obj, "em_mse_formula", None)
                    vocab = getattr(field_obj, "em_vocab_group", None)
                    cost_group = getattr(field_obj, "em_cost_group", None)
                    cost_value = getattr(field_obj, "em_cost_value", None)
                    slope = getattr(field_obj, "em_slope", None)
                    intercept = getattr(field_obj, "em_intercept", None)
                    line_width = getattr(field_obj, "em_line_width", None)
                    overfit_hint_opacity = getattr(field_obj, "em_overfit_hint_opacity", None)
                    cost_steps = list(getattr(field_obj, "em_cost_steps", [18.7, 11.4, 6.8, 2.1, 1.4, 1.6]))

                    def _register_em():
                        object_registry[step.id] = field_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = field_obj

                    def set_opacity(obj, value):
                        return obj.animate.set_opacity(value) if obj is not None else None

                    if beat == 2:
                        rt = capped("beat2_duration", 2.2, floor=0.7)
                        anims = []
                        if focus_bar_opacity is not None:
                            anims.append(focus_bar_opacity.animate.set_value(1.0))
                        if focus_bar_progress is not None:
                            anims.append(focus_bar_progress.animate.set_value(1.0))
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=rt * 0.62, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.62
                        if error_label is not None:
                            self.play(error_label.animate.set_opacity(1.0), run_time=rt * 0.22, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.22
                        self.wait(rt * 0.16)
                        current_time += rt * 0.16
                        _register_em(); handled = True

                    elif beat == 3:
                        rt = capped("beat3_duration", 2.1, floor=0.7)
                        anims = []
                        if y_labels is not None:
                            anims.append(y_labels.animate.set_opacity(1.0))
                        if error_label is not None:
                            anims.append(error_label.animate.set_opacity(0.35))
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=rt * 0.70, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.70
                        self.wait(rt * 0.30)
                        current_time += rt * 0.30
                        _register_em(); handled = True

                    elif beat == 4:
                        rt = capped("beat4_duration", 2.2, floor=0.7)
                        anims = []
                        if all_bar_opacity is not None:
                            anims.append(all_bar_opacity.animate.set_value(1.0))
                        if all_bar_progress is not None:
                            anims.append(all_bar_progress.animate.set_value(1.0))
                        if y_labels is not None:
                            anims.append(y_labels.animate.set_opacity(0.0))
                        if error_label is not None:
                            anims.append(error_label.animate.set_opacity(0.0))
                        if focus_bar_opacity is not None:
                            anims.append(focus_bar_opacity.animate.set_value(0.0))
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=rt * 0.78, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.78
                        self.wait(rt * 0.22)
                        current_time += rt * 0.22
                        _register_em(); handled = True

                    elif beat == 5:
                        rt = capped("beat5_duration", 1.7, floor=0.5)
                        if sign_emphasis_opacity is not None:
                            self.play(sign_emphasis_opacity.animate.set_value(1.0), run_time=rt * 0.28, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.28
                            self.wait(rt * 0.38)
                            current_time += rt * 0.38
                            self.play(sign_emphasis_opacity.animate.set_value(0.0), run_time=rt * 0.22, rate_func=rate_functions.ease_in_out_sine)
                            current_time += rt * 0.22
                            self.wait(rt * 0.12)
                            current_time += rt * 0.12
                        else:
                            self.wait(rt)
                            current_time += rt
                        _register_em(); handled = True

                    elif beat == 6:
                        rt = capped("beat6_duration", 2.7, floor=0.9)
                        prep = []
                        if all_bar_opacity is not None:
                            prep.append(all_bar_opacity.animate.set_value(1.0))
                        if square_opacity is not None:
                            prep.append(square_opacity.animate.set_value(1.0))
                        if square_stroke_opacity is not None:
                            prep.append(square_stroke_opacity.animate.set_value(0.28))
                        if prep:
                            self.play(AnimationGroup(*prep, lag_ratio=0.0), run_time=rt * 0.18, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.18
                        grow = []
                        if square_progress is not None:
                            grow.append(square_progress.animate.set_value(1.0))
                        if square_stroke_opacity is not None:
                            grow.append(square_stroke_opacity.animate.set_value(1.0))
                        self.play(AnimationGroup(*grow, lag_ratio=0.0), run_time=rt * 0.46, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.46
                        if square_fill_reveal is not None:
                            self.play(square_fill_reveal.animate.set_value(1.0), run_time=rt * 0.18, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.18
                        self.wait(rt * 0.18)
                        current_time += rt * 0.18
                        _register_em(); handled = True

                    elif beat == 7:
                        rt = capped("beat7_duration", 1.8, floor=0.6)
                        if large_square_pulse is not None:
                            self.play(large_square_pulse.animate.set_value(1.0), run_time=rt * 0.42, rate_func=rate_functions.ease_out_cubic)
                            self.play(large_square_pulse.animate.set_value(0.0), run_time=rt * 0.34, rate_func=rate_functions.ease_in_out_sine)
                            current_time += rt * 0.76
                        self.wait(rt * 0.24)
                        current_time += rt * 0.24
                        _register_em(); handled = True

                    elif beat == 8:
                        rt = capped("beat8_duration", 2.4, floor=0.8)
                        intro = []
                        if formula is not None:
                            intro.append(formula.animate.set_opacity(1.0))
                        if vocab is not None:
                            intro.append(vocab.animate.set_opacity(1.0))
                        self.play(AnimationGroup(*intro, lag_ratio=0.18), run_time=rt * 0.48, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.48
                        self.wait(rt * 0.26)
                        current_time += rt * 0.26
                        outro = []
                        if formula is not None:
                            outro.append(formula.animate.set_opacity(0.0))
                        if vocab is not None:
                            outro.append(vocab.animate.set_opacity(0.0))
                        self.play(AnimationGroup(*outro, lag_ratio=0.0), run_time=rt * 0.26, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.26
                        _register_em(); handled = True

                    elif beat == 9:
                        rt = capped("beat9_duration", 1.6, floor=0.5)
                        anims = []
                        if cost_group is not None:
                            anims.append(cost_group.animate.set_opacity(1.0))
                        if cost_value is not None and cost_steps:
                            cost_value.set_value(float(cost_steps[0]))
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=rt * 0.58, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.58
                        self.wait(rt * 0.42)
                        current_time += rt * 0.42
                        _register_em(); handled = True

                    elif beat == 10:
                        rt = capped("beat10_duration", 4.0, floor=1.2)
                        states = [
                            (getattr(field_obj, "em_step1_slope", 0.55), getattr(field_obj, "em_step1_intercept", 1.25), cost_steps[1] if len(cost_steps) > 1 else 11.4),
                            (getattr(field_obj, "em_step2_slope", 0.64), getattr(field_obj, "em_step2_intercept", 1.02), cost_steps[2] if len(cost_steps) > 2 else 6.8),
                            (getattr(field_obj, "em_final_slope", 0.72), getattr(field_obj, "em_final_intercept", 0.82), cost_steps[3] if len(cost_steps) > 3 else 2.1),
                        ]
                        per = rt / max(1, len(states))
                        for m, b, c in states:
                            move = []
                            if slope is not None:
                                move.append(slope.animate.set_value(float(m)))
                            if intercept is not None:
                                move.append(intercept.animate.set_value(float(b)))
                            self.play(AnimationGroup(*move, lag_ratio=0.0), run_time=per * 0.58, rate_func=rate_functions.ease_in_out_sine)
                            current_time += per * 0.58
                            if cost_value is not None:
                                self.play(cost_value.animate.set_value(float(c)), run_time=per * 0.28, rate_func=rate_functions.ease_out_sine)
                                current_time += per * 0.28
                            self.wait(per * 0.14)
                            current_time += per * 0.14
                        _register_em(); handled = True

                    elif beat == 11:
                        rt = capped("beat11_duration", 2.6, floor=0.8)
                        anims = []
                        if slope is not None:
                            anims.append(slope.animate.set_value(getattr(field_obj, "em_final_slope", 0.72)))
                        if intercept is not None:
                            anims.append(intercept.animate.set_value(getattr(field_obj, "em_final_intercept", 0.82)))
                        if cost_value is not None:
                            anims.append(cost_value.animate.set_value(float(cost_steps[4] if len(cost_steps) > 4 else 1.4)))
                        if line_width is not None:
                            anims.append(line_width.animate.set_value(float(params.get("final_line_width", 3.35))))
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=rt * 0.68, rate_func=rate_functions.ease_out_cubic)
                        current_time += rt * 0.68
                        self.wait(rt * 0.32)
                        current_time += rt * 0.32
                        _register_em(); handled = True

                    elif beat == 12:
                        rt = capped("beat12_duration", 2.2, floor=0.8)
                        anims = []
                        if slope is not None:
                            anims.append(slope.animate.set_value(getattr(field_obj, "em_overfit_slope", 0.82)))
                        if intercept is not None:
                            anims.append(intercept.animate.set_value(getattr(field_obj, "em_overfit_intercept", 0.45)))
                        if cost_value is not None:
                            anims.append(cost_value.animate.set_value(float(cost_steps[5] if len(cost_steps) > 5 else 1.6)))
                        if overfit_hint_opacity is not None:
                            anims.append(overfit_hint_opacity.animate.set_value(1.0))
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=rt * 0.62, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.62
                        self.wait(rt * 0.38)
                        current_time += rt * 0.38
                        _register_em(); handled = True

                    else:
                        print(f"[mutate_error_minimization_system] Unknown beat={beat}. Skipping.")
                        handled = True

                elif step.action == "show_regularization_lasso_system":
                    # ── Video 3 Scene 6 Beat 1: familiar regression world before overfitting.
                    params = dict(step.params)
                    field_obj = make_regularization_lasso_system(params, step.zone)

                    replace_zone = step.replace
                    outgoing_anims = []
                    if replace_zone is not None:
                        existing = active_objects.get(replace_zone)
                        if existing is not None:
                            outgoing = transition_out_for(existing, step.transition_out or "fade")
                            if outgoing is not None:
                                outgoing_anims.append(outgoing)
                            clear_zone(replace_zone)
                    if outgoing_anims:
                        out_rt = min(0.35, max(0.05, run_time * 0.12))
                        self.play(AnimationGroup(*outgoing_anims, lag_ratio=0.0), run_time=out_rt)
                        current_time += out_rt

                    self.add(field_obj)
                    points_opacity = getattr(field_obj, "rl_points_opacity", None)
                    curve_opacity = getattr(field_obj, "rl_curve_opacity", None)
                    curve_draw = getattr(field_obj, "rl_curve_draw_progress", None)
                    intro = []
                    if points_opacity is not None:
                        intro.append(points_opacity.animate.set_value(1.0))
                    if intro:
                        self.play(LaggedStart(*intro, lag_ratio=0.0), run_time=run_time * 0.24, rate_func=rate_functions.ease_out_sine)
                        current_time += run_time * 0.24
                    draw_anims = []
                    if curve_opacity is not None:
                        draw_anims.append(curve_opacity.animate.set_value(1.0))
                    if curve_draw is not None:
                        draw_anims.append(curve_draw.animate.set_value(1.0))
                    if draw_anims:
                        self.play(AnimationGroup(*draw_anims, lag_ratio=0.0), run_time=run_time * 0.54, rate_func=rate_functions.ease_in_out_sine)
                        current_time += run_time * 0.54
                    hold_rt = max(0.0, run_time * 0.22)
                    if hold_rt > 0:
                        self.wait(hold_rt)
                        current_time += hold_rt
                    register_object(step.id, step.zone, field_obj)
                    handled = True

                elif step.action == "mutate_regularization_lasso_system":
                    # ── Video 3 Scene 6 Beats 2-10: mutate one persistent regularization/lasso system.
                    source_id = step.params.get("source_id")
                    field_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)
                    if field_obj is None:
                        raise RuntimeError(f"mutate_regularization_lasso_system could not find source_id={source_id!r}")

                    beat = int(step.params.get("beat", 2))
                    params = dict(step.params)
                    segment_duration = duration_map[step.anchor]

                    def capped(name, default, floor=0.15, reserve=0.2):
                        requested = float(params.get(name, default))
                        available = max(floor, segment_duration - float(step.offset) - reserve)
                        return max(floor, min(requested, available))

                    overfit_progress = getattr(field_obj, "rl_overfit_progress", None)
                    regularize_progress = getattr(field_obj, "rl_regularize_progress", None)
                    curve_opacity = getattr(field_obj, "rl_curve_opacity", None)
                    points_opacity = getattr(field_obj, "rl_points_opacity", None)
                    overfit_label = getattr(field_obj, "rl_overfit_label", None)
                    bar_chart_opacity = getattr(field_obj, "rl_bar_chart_opacity", None)
                    formula_terms = getattr(field_obj, "rl_formula_terms", VGroup())
                    lambda_group = getattr(field_obj, "rl_lambda_group", None)
                    lambda_opacity = getattr(field_obj, "rl_lambda_opacity", None)
                    lambda_value = getattr(field_obj, "rl_lambda_value", None)
                    final_dim = getattr(field_obj, "rl_final_dim", None)
                    bar_trackers = list(getattr(field_obj, "rl_bar_trackers", []))
                    ghost_opacities = list(getattr(field_obj, "rl_ghost_opacities", []))
                    initial_heights = list(getattr(field_obj, "rl_initial_heights", []))
                    compressed_heights = list(getattr(field_obj, "rl_compressed_heights", []))
                    final_heights = list(getattr(field_obj, "rl_final_heights", []))
                    collapse_order = list(getattr(field_obj, "rl_collapse_order", []))
                    lambda_mid = float(getattr(field_obj, "rl_lambda_mid", 0.9))
                    lambda_high = float(getattr(field_obj, "rl_lambda_high", 1.8))

                    def _register_rl():
                        object_registry[step.id] = field_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = field_obj

                    if beat == 2:
                        rt = capped("beat2_duration", 3.4, floor=1.0)
                        anims = []
                        if overfit_progress is not None:
                            anims.append(overfit_progress.animate.set_value(1.0))
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=rt * 0.86, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.86
                        self.wait(rt * 0.14)
                        current_time += rt * 0.14
                        _register_rl(); handled = True

                    elif beat == 3:
                        rt = capped("beat3_duration", 1.5, floor=0.5)
                        if overfit_label is not None:
                            self.play(FadeIn(overfit_label, shift=UP * 0.08), run_time=rt * 0.42, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.42
                            self.wait(rt * 0.58)
                            current_time += rt * 0.58
                        else:
                            self.wait(rt); current_time += rt
                        _register_rl(); handled = True

                    elif beat == 4:
                        rt = capped("beat4_duration", 3.4, floor=1.0)
                        if overfit_label is not None:
                            self.play(FadeOut(overfit_label), run_time=rt * 0.16, rate_func=rate_functions.ease_in_sine)
                            current_time += rt * 0.16
                        calm_anims = []
                        if regularize_progress is not None:
                            calm_anims.append(regularize_progress.animate.set_value(1.0))
                        if bar_chart_opacity is not None:
                            calm_anims.append(bar_chart_opacity.animate.set_value(1.0))
                        for tracker, height in zip(bar_trackers, initial_heights):
                            calm_anims.append(tracker.animate.set_value(float(height)))
                        self.play(AnimationGroup(*calm_anims, lag_ratio=0.0), run_time=rt * 0.48, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.48
                        fade_anims = []
                        if curve_opacity is not None:
                            fade_anims.append(curve_opacity.animate.set_value(0.0))
                        if points_opacity is not None:
                            fade_anims.append(points_opacity.animate.set_value(0.0))
                        self.play(AnimationGroup(*fade_anims, lag_ratio=0.0), run_time=rt * 0.24, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.24
                        self.wait(rt * 0.12)
                        current_time += rt * 0.12
                        _register_rl(); handled = True

                    elif beat == 5:
                        rt = capped("beat5_duration", 3.0, floor=0.9)
                        per = rt * 0.74 / max(1, len(formula_terms))
                        for term in formula_terms:
                            self.play(FadeIn(term, shift=UP * 0.05), run_time=per, rate_func=rate_functions.ease_out_sine)
                            current_time += per
                        self.wait(rt * 0.26)
                        current_time += rt * 0.26
                        _register_rl(); handled = True

                    elif beat == 6:
                        rt = capped("beat6_duration", 2.2, floor=0.7)
                        anims = []
                        for i, term in enumerate(formula_terms):
                            if i == len(formula_terms) - 1:
                                anims.append(term.animate.set_color("#FFD166").set_opacity(1.0))
                            else:
                                anims.append(term.animate.set_opacity(0.36))
                        if lambda_opacity is not None:
                            anims.append(lambda_opacity.animate.set_value(1.0))
                        if lambda_value is not None:
                            lambda_value.set_value(0.0)
                        self.play(AnimationGroup(*anims, lag_ratio=0.0), run_time=rt * 0.56, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.56
                        self.wait(rt * 0.44)
                        current_time += rt * 0.44
                        _register_rl(); handled = True

                    elif beat == 7:
                        rt = capped("beat7_duration", 3.0, floor=1.0)
                        fade_formula = [term.animate.set_opacity(0.0) for term in formula_terms]
                        if fade_formula:
                            self.play(AnimationGroup(*fade_formula, lag_ratio=0.0), run_time=rt * 0.18, rate_func=rate_functions.ease_in_out_sine)
                            current_time += rt * 0.18
                        pressure = []
                        if lambda_value is not None:
                            pressure.append(lambda_value.animate.set_value(lambda_mid))
                        for tracker, height in zip(bar_trackers, compressed_heights):
                            pressure.append(tracker.animate.set_value(float(height)))
                        self.play(AnimationGroup(*pressure, lag_ratio=0.0), run_time=rt * 0.66, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.66
                        self.wait(rt * 0.16)
                        current_time += rt * 0.16
                        _register_rl(); handled = True

                    elif beat == 8:
                        rt = capped("beat8_duration", 3.2, floor=1.1)
                        if lambda_value is not None:
                            self.play(lambda_value.animate.set_value(lambda_high), run_time=rt * 0.20, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.20
                        remaining_rt = rt * 0.62
                        per = remaining_rt / max(1, len(collapse_order))
                        for idx_c in collapse_order:
                            if 0 <= idx_c < len(bar_trackers):
                                near_zero = max(0.08, float(final_heights[idx_c]) + 0.12)
                                self.play(bar_trackers[idx_c].animate.set_value(near_zero), run_time=per * 0.42, rate_func=rate_functions.ease_in_out_sine)
                                current_time += per * 0.42
                                self.wait(per * 0.16)
                                current_time += per * 0.16
                                collapse = [bar_trackers[idx_c].animate.set_value(0.0)]
                                if idx_c < len(ghost_opacities):
                                    collapse.append(ghost_opacities[idx_c].animate.set_value(0.42))
                                self.play(AnimationGroup(*collapse, lag_ratio=0.0), run_time=per * 0.42, rate_func=rate_functions.ease_in_sine)
                                current_time += per * 0.42
                        survivor_anims = []
                        for i, tracker in enumerate(bar_trackers):
                            if i not in collapse_order and i < len(final_heights):
                                survivor_anims.append(tracker.animate.set_value(float(final_heights[i])))
                        if survivor_anims:
                            self.play(AnimationGroup(*survivor_anims, lag_ratio=0.0), run_time=rt * 0.12, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.12
                        self.wait(rt * 0.06)
                        current_time += rt * 0.06
                        _register_rl(); handled = True

                    elif beat == 9:
                        rt = capped("beat9_duration", 2.2, floor=0.7)
                        polish = []
                        if lambda_value is not None:
                            polish.append(lambda_value.animate.set_value(lambda_high))
                        for i, ghost in enumerate(ghost_opacities):
                            if i in collapse_order:
                                polish.append(ghost.animate.set_value(0.32))
                        self.play(AnimationGroup(*polish, lag_ratio=0.0), run_time=rt * 0.28, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.28
                        self.wait(rt * 0.72)
                        current_time += rt * 0.72
                        _register_rl(); handled = True

                    elif beat == 10:
                        rt = capped("beat10_duration", 3.0, floor=0.9)
                        dim_anims = []
                        if final_dim is not None:
                            dim_anims.append(final_dim.animate.set_value(float(params.get("final_dim", 0.62))))
                        self.play(AnimationGroup(*dim_anims, lag_ratio=0.0), run_time=rt * 0.58, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.58
                        self.wait(rt * 0.42)
                        current_time += rt * 0.42
                        _register_rl(); handled = True

                    else:
                        print(f"[mutate_regularization_lasso_system] Unknown beat={beat}. Skipping.")
                        handled = True

                elif step.action == "show_linear_formula_system":
                    # ── Video 3 Scene 4 Beat 1: formula arrives as the main object.
                    params = dict(step.params)
                    field_obj = make_linear_formula_system(params, step.zone)

                    replace_zone = step.replace
                    outgoing_anims = []
                    if replace_zone is not None:
                        existing = active_objects.get(replace_zone)
                        if existing is not None:
                            outgoing = transition_out_for(existing, step.transition_out or "fade")
                            if outgoing is not None:
                                outgoing_anims.append(outgoing)
                            clear_zone(replace_zone)

                    if outgoing_anims:
                        out_rt = min(0.35, max(0.05, run_time * 0.12))
                        self.play(AnimationGroup(*outgoing_anims, lag_ratio=0.0), run_time=out_rt)
                        current_time += out_rt

                    equation = getattr(field_obj, "lf_equation", None)
                    axes = getattr(field_obj, "lf_axes", VGroup())
                    live_line = getattr(field_obj, "lf_live_line", None)
                    real_point = getattr(field_obj, "lf_real_point", None)
                    prediction_drop = getattr(field_obj, "lf_prediction_drop", None)
                    prediction_dot = getattr(field_obj, "lf_prediction_dot", None)
                    x_tick = getattr(field_obj, "lf_x_tick", None)
                    x_rise = getattr(field_obj, "lf_x_rise", None)
                    intercept_marker = getattr(field_obj, "lf_intercept_marker", None)
                    scatter = getattr(field_obj, "lf_scatter", VGroup())
                    w_box = getattr(field_obj, "lf_w_box", None)
                    b_box = getattr(field_obj, "lf_b_box", None)
                    wb_connector = getattr(field_obj, "lf_wb_connector", None)

                    # Add persistent system elements up front so later beats mutate
                    # the same objects instead of replacing equation/line. Keep the
                    # equation invisible until Write starts to avoid an opening pop.
                    if equation is not None:
                        for term in equation:
                            term.set_opacity(0.0)
                        self.add(equation)
                    for obj in [axes, live_line, real_point, prediction_drop, prediction_dot, x_tick, x_rise, intercept_marker, scatter, w_box, b_box, wb_connector]:
                        if obj is not None:
                            obj.set_opacity(0.0) if hasattr(obj, "set_opacity") else None
                            self.add(obj)

                    if equation is not None:
                        rest_opacity = float(params.get("equation_rest_opacity", 0.58))
                        write_rt = run_time * 0.72
                        hold_rt = run_time * 0.12
                        dim_rt = run_time * 0.16
                        self.play(
                            LaggedStart(*[Write(term) for term in equation], lag_ratio=0.16),
                            run_time=write_rt,
                            rate_func=rate_functions.ease_in_out_sine,
                        )
                        current_time += write_rt
                        self.wait(hold_rt)
                        current_time += hold_rt
                        self.play(
                            AnimationGroup(*[term.animate.set_opacity(rest_opacity) for term in equation], lag_ratio=0.0),
                            run_time=dim_rt,
                            rate_func=rate_functions.ease_out_sine,
                        )
                        current_time += dim_rt
                    else:
                        self.wait(run_time)
                        current_time += run_time

                    register_object(step.id, step.zone, field_obj)
                    handled = True

                elif step.action == "mutate_linear_formula_system":
                    # ── Video 3 Scene 4 Beats 2-6: mutate one equation/line system.
                    source_id = step.params.get("source_id")
                    field_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)

                    if field_obj is None:
                        raise RuntimeError(f"mutate_linear_formula_system could not find source_id={source_id!r}")

                    beat = int(step.params.get("beat", 2))
                    params = dict(step.params)
                    segment_duration = duration_map[step.anchor]

                    def capped(name, default, floor=0.15, reserve=0.2):
                        requested = float(params.get(name, default))
                        available = max(floor, segment_duration - float(step.offset) - reserve)
                        return max(floor, min(requested, available))

                    equation = getattr(field_obj, "lf_equation", None)
                    terms = getattr(field_obj, "lf_terms", {})
                    axes = getattr(field_obj, "lf_axes", VGroup())
                    line_progress = getattr(field_obj, "lf_line_progress", None)
                    line_opacity = getattr(field_obj, "lf_line_opacity", None)
                    line_width = getattr(field_obj, "lf_line_width", None)
                    slope = getattr(field_obj, "lf_slope", None)
                    intercept = getattr(field_obj, "lf_intercept", None)
                    prediction_drop_progress = getattr(field_obj, "lf_prediction_drop_progress", None)
                    prediction_drop_opacity = getattr(field_obj, "lf_prediction_drop_opacity", None)
                    prediction_dot_opacity = getattr(field_obj, "lf_prediction_dot_opacity", None)
                    x_tick_opacity = getattr(field_obj, "lf_x_tick_opacity", None)
                    x_rise_progress = getattr(field_obj, "lf_x_rise_progress", None)
                    x_rise_opacity = getattr(field_obj, "lf_x_rise_opacity", None)
                    intercept_opacity = getattr(field_obj, "lf_intercept_opacity", None)
                    error_hint_opacity = getattr(field_obj, "lf_error_hint_opacity", None)
                    wb_cue_opacity = getattr(field_obj, "lf_wb_cue_opacity", None)
                    real_point = getattr(field_obj, "lf_real_point", None)
                    scatter = list(getattr(field_obj, "lf_scatter", VGroup()))
                    eq_color = getattr(field_obj, "lf_equation_color", "#F8FAFC")
                    dim_color = getattr(field_obj, "lf_dim_color", "#94A3B8")
                    yhat_color = getattr(field_obj, "lf_yhat_color", "#4A9EFF")
                    bias_color = getattr(field_obj, "lf_bias_color", "#FFD166")

                    def _term(name):
                        return terms.get(name)

                    rest_opacity = float(getattr(field_obj, "lf_params", {}).get("equation_rest_opacity", 0.58))

                    def set_terms_rest():
                        anims = []
                        for term in terms.values():
                            anims.append(term.animate.set_color(eq_color).set_opacity(rest_opacity))
                        return anims

                    def highlight_term(name, color=None):
                        anims = set_terms_rest()
                        term = _term(name)
                        if term is not None:
                            anims.append(term.animate.set_color(color or yhat_color).set_opacity(1.0))
                        return anims

                    def _register_lf():
                        object_registry[step.id] = field_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = field_obj

                    if beat == 2:
                        # ŷ: the equation becomes a graph and a prediction on the line.
                        rt = capped("beat2_duration", 2.8, floor=0.8)
                        intro_anims = highlight_term("yhat", yhat_color)
                        intro_anims.extend([axes.animate.set_opacity(1.0)])
                        if line_progress is not None:
                            intro_anims.append(line_progress.animate.set_value(1.0))
                        if line_opacity is not None:
                            intro_anims.append(line_opacity.animate.set_value(1.0))
                        self.play(AnimationGroup(*intro_anims, lag_ratio=0.0), run_time=rt * 0.38, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.38

                        real_anims = []
                        if real_point is not None:
                            real_anims.append(real_point.animate.set_opacity(1.0))
                        if prediction_drop_opacity is not None:
                            real_anims.append(prediction_drop_opacity.animate.set_value(1.0))
                        self.play(AnimationGroup(*real_anims, lag_ratio=0.0), run_time=rt * 0.16, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.16

                        drop_anims = []
                        if prediction_drop_progress is not None:
                            drop_anims.append(prediction_drop_progress.animate.set_value(1.0))
                        self.play(AnimationGroup(*drop_anims, lag_ratio=0.0), run_time=rt * 0.22, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.22

                        dot_anims = []
                        if prediction_dot_opacity is not None:
                            dot_anims.append(prediction_dot_opacity.animate.set_value(1.0))
                        self.play(AnimationGroup(*dot_anims, lag_ratio=0.0), run_time=rt * 0.08, rate_func=rate_functions.ease_out_cubic)
                        current_time += rt * 0.08

                        fade_anims = []
                        if real_point is not None:
                            fade_anims.append(real_point.animate.set_opacity(0.18))
                        ghost_opacity = float(params.get("prediction_ghost_opacity", 0.34))
                        if prediction_drop_opacity is not None:
                            fade_anims.append(prediction_drop_opacity.animate.set_value(ghost_opacity))
                        if prediction_dot_opacity is not None:
                            fade_anims.append(prediction_dot_opacity.animate.set_value(ghost_opacity))
                        fade_anims.extend(set_terms_rest())
                        self.play(AnimationGroup(*fade_anims, lag_ratio=0.0), run_time=rt * 0.16, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.16
                        _register_lf()
                        handled = True

                    elif beat == 3:
                        # w: slope changes by tracker only; the prediction ghost follows.
                        if slope is not None:
                            rt = capped("beat3_duration", 2.55, floor=0.9)
                            self.play(AnimationGroup(*highlight_term("w", yhat_color), lag_ratio=0.0), run_time=rt * 0.16)
                            current_time += rt * 0.16
                            self.play(
                                slope.animate.set_value(getattr(field_obj, "lf_demo_slope_high", 0.92)),
                                run_time=rt * 0.34,
                                rate_func=rate_functions.ease_in_out_sine,
                            )
                            self.wait(rt * 0.18)
                            self.play(
                                slope.animate.set_value(getattr(field_obj, "lf_initial_slope", 0.62)),
                                run_time=rt * 0.24,
                                rate_func=rate_functions.ease_out_cubic,
                            )
                            current_time += rt * 0.76
                            cleanup = set_terms_rest()
                            if prediction_drop_opacity is not None:
                                cleanup.append(prediction_drop_opacity.animate.set_value(0.0))
                            if prediction_dot_opacity is not None:
                                cleanup.append(prediction_dot_opacity.animate.set_value(0.0))
                            if real_point is not None:
                                cleanup.append(real_point.animate.set_opacity(0.0))
                            self.play(AnimationGroup(*cleanup, lag_ratio=0.0), run_time=rt * 0.10)
                            current_time += rt * 0.10
                        else:
                            self.wait(run_time)
                            current_time += run_time
                        _register_lf()
                        handled = True

                    elif beat == 4:
                        # x: a quick input lookup from the x-axis up to the line.
                        rt = capped("beat4_duration", 1.65, floor=0.55)
                        show_anims = highlight_term("x", yhat_color)
                        if x_tick_opacity is not None:
                            show_anims.append(x_tick_opacity.animate.set_value(1.0))
                        self.play(AnimationGroup(*show_anims, lag_ratio=0.0), run_time=rt * 0.24, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.24
                        rise_anims = []
                        if x_rise_opacity is not None:
                            rise_anims.append(x_rise_opacity.animate.set_value(1.0))
                        if x_rise_progress is not None:
                            rise_anims.append(x_rise_progress.animate.set_value(1.0))
                        self.play(AnimationGroup(*rise_anims, lag_ratio=0.0), run_time=rt * 0.46, rate_func=rate_functions.ease_in_out_sine)
                        current_time += rt * 0.46
                        hold_rt = rt * 0.14
                        self.wait(hold_rt)
                        current_time += hold_rt
                        cleanup = set_terms_rest()
                        if x_tick_opacity is not None:
                            cleanup.append(x_tick_opacity.animate.set_value(0.0))
                        if x_rise_opacity is not None:
                            cleanup.append(x_rise_opacity.animate.set_value(0.0))
                        self.play(AnimationGroup(*cleanup, lag_ratio=0.0), run_time=rt * 0.16)
                        current_time += rt * 0.16
                        _register_lf()
                        handled = True

                    elif beat == 5:
                        # b: intercept shifts vertically; slope is intentionally untouched.
                        rt = capped("beat5_duration", 2.65, floor=0.9)
                        intro = highlight_term("b", bias_color)
                        if intercept_opacity is not None:
                            intro.append(intercept_opacity.animate.set_value(1.0))
                        self.play(AnimationGroup(*intro, lag_ratio=0.0), run_time=rt * 0.22, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.22
                        if intercept is not None:
                            self.play(intercept.animate.set_value(getattr(field_obj, "lf_demo_intercept_high", 2.35)), run_time=rt * 0.36, rate_func=rate_functions.ease_in_out_sine)
                            self.wait(rt * 0.16)
                            self.play(intercept.animate.set_value(getattr(field_obj, "lf_initial_intercept", 1.35)), run_time=rt * 0.28, rate_func=rate_functions.ease_out_cubic)
                            current_time += rt * 0.80
                        cleanup = set_terms_rest()
                        if intercept_opacity is not None:
                            cleanup.append(intercept_opacity.animate.set_value(0.0))
                        self.play(AnimationGroup(*cleanup, lag_ratio=0.0), run_time=rt * 0.08)
                        current_time += rt * 0.08
                        _register_lf()
                        handled = True

                    elif beat == 6:
                        # Learning handoff: data appears first, then w and b become the pair to adjust.
                        rt = capped("beat6_duration", 3.0, floor=1.0)
                        scatter_sorted = sorted(scatter, key=lambda d: d.get_center()[0])
                        for dot in scatter_sorted:
                            dot.shift(UP * 0.18)
                        scatter_anims = [dot.animate.shift(DOWN * 0.18).set_opacity(0.88) for dot in scatter_sorted]
                        if scatter_anims:
                            self.play(LaggedStart(*scatter_anims, lag_ratio=float(params.get("scatter_lag_ratio", 0.12))), run_time=rt * 0.38, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.38
                        else:
                            self.wait(rt * 0.38)
                            current_time += rt * 0.38
                        error_anims = []
                        if error_hint_opacity is not None:
                            error_anims.append(error_hint_opacity.animate.set_value(1.0))
                        if line_width is not None:
                            error_anims.append(line_width.animate.set_value(float(params.get("final_line_width", 3.25))))
                        if error_anims:
                            self.play(AnimationGroup(*error_anims, lag_ratio=0.0), run_time=rt * 0.16, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.16
                        scatter_hold = rt * float(params.get("scatter_hold_ratio", 0.22))
                        self.wait(scatter_hold)
                        current_time += scatter_hold
                        pair_anims = set_terms_rest()
                        if _term("w") is not None:
                            pair_anims.append(_term("w").animate.set_color(eq_color).set_opacity(1.0))
                        if _term("b") is not None:
                            pair_anims.append(_term("b").animate.set_color(bias_color).set_opacity(1.0))
                        if wb_cue_opacity is not None:
                            pair_anims.append(wb_cue_opacity.animate.set_value(1.0))
                        self.play(AnimationGroup(*pair_anims, lag_ratio=0.0), run_time=rt * 0.22, rate_func=rate_functions.ease_out_sine)
                        current_time += rt * 0.22
                        _register_lf()
                        handled = True

                    elif beat == 7:
                        # Exit handoff: clean the equation, then fade it upward exactly
                        # when narration says to move toward error minimization.
                        rt = capped("beat7_duration", 2.0, floor=0.8)
                        clean_anims = []
                        if wb_cue_opacity is not None:
                            clean_anims.append(wb_cue_opacity.animate.set_value(0.0))
                        if equation is not None:
                            clean_anims.extend([term.animate.set_color(eq_color).set_opacity(1.0) for term in terms.values()])
                        if clean_anims:
                            self.play(AnimationGroup(*clean_anims, lag_ratio=0.0), run_time=rt * 0.22, rate_func=rate_functions.ease_out_sine)
                            current_time += rt * 0.22
                        exit_anims = []
                        if equation is not None:
                            exit_anims.append(equation.animate.shift(UP * 1.25).set_opacity(0.0))
                        if exit_anims:
                            self.play(AnimationGroup(*exit_anims, lag_ratio=0.0), run_time=rt * 0.78, rate_func=rate_functions.ease_in_out_sine)
                            current_time += rt * 0.78
                        _register_lf()
                        handled = True

                    else:
                        print(f"[mutate_linear_formula_system] Unknown beat={beat}. Skipping.")
                        handled = True

                elif step.action == "show_classification_regression_field":
                    new_obj = build_object(
                        {
                            "id": step.id,
                            "action": step.action,
                            "params": dict(step.params),
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

                    dots = list(getattr(new_obj, "cr_dots", VGroup()))
                    for dot in dots:
                        dot.set_opacity(0.0)
                    self.add(new_obj)
                    if outgoing_anims:
                        self.play(AnimationGroup(*outgoing_anims, lag_ratio=0.0), run_time=min(0.35, run_time * 0.25))
                    if dots:
                        cluster_count = step.params.get("cluster_count", 4)
                        ordered = sorted(dots, key=lambda dot: (dot.get_center()[0] + dot.get_center()[1] * 0.85))
                        cluster_anims = []
                        for cluster_index in range(cluster_count):
                            cluster_dots = ordered[
                                cluster_index * len(ordered) // cluster_count:
                                (cluster_index + 1) * len(ordered) // cluster_count
                            ]
                            if cluster_dots:
                                cluster_anims.append(AnimationGroup(*[
                                    dot.animate.set_opacity(getattr(new_obj, "cr_dot_opacity", 0.66))
                                    for dot in cluster_dots
                                ], lag_ratio=0.0))
                        self.play(Succession(*cluster_anims), run_time=run_time, rate_func=rate_functions.ease_out_sine)
                    else:
                        self.wait(run_time)
                    current_time += run_time
                    register_object(step.id, step.zone, new_obj)
                    handled = True

                elif step.action == "mutate_classification_regression_field":
                    source_id = step.params.get("source_id")
                    field_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)

                    if field_obj is None:
                        print(
                            f"[mutate_classification_regression_field] WARNING: source_id={source_id} not found. Skipping."
                        )
                        handled = True
                        continue

                    mode = step.params.get("mode", "drop_test_point")
                    dots = list(getattr(field_obj, "cr_dots", VGroup()))
                    test_dot = getattr(field_obj, "cr_test_dot", None)
                    boundary = getattr(field_obj, "cr_boundary", None)
                    x_axis = getattr(field_obj, "cr_x_axis", None)
                    y_axis = getattr(field_obj, "cr_y_axis", None)
                    ticks = getattr(field_obj, "cr_ticks", VGroup())
                    trend_line = getattr(field_obj, "cr_trend_line", None)
                    vertical_read = getattr(field_obj, "cr_vertical_read", None)
                    horizontal_read = getattr(field_obj, "cr_horizontal_read", None)
                    boundary_label = getattr(field_obj, "cr_boundary_label", None)
                    x_label = getattr(field_obj, "cr_x_label", None)
                    y_label = getattr(field_obj, "cr_y_label", None)
                    trend_label = getattr(field_obj, "cr_trend_label", None)
                    prediction_marker = getattr(field_obj, "cr_prediction_marker", None)
                    test_glow = getattr(field_obj, "cr_test_glow", None)
                    neutral_color = step.params.get("neutral_color", getattr(field_obj, "cr_neutral_color", "#7A8291"))
                    dot_opacity = step.params.get("dot_opacity", getattr(field_obj, "cr_dot_opacity", 0.66))
                    colored_opacity = step.params.get("colored_opacity", getattr(field_obj, "cr_colored_opacity", 0.94))
                    axis_opacity = step.params.get("axis_opacity", getattr(field_obj, "cr_axis_opacity", 0.52))
                    tick_opacity = step.params.get("tick_opacity", getattr(field_obj, "cr_tick_opacity", 0.45))
                    axis_label_opacity = step.params.get("axis_label_opacity", getattr(field_obj, "cr_axis_label_opacity", 0.68))
                    boundary_label_opacity = step.params.get("boundary_label_opacity", getattr(field_obj, "cr_boundary_label_opacity", 0.64))
                    trend_label_opacity = step.params.get("trend_label_opacity", getattr(field_obj, "cr_trend_label_opacity", 0.76))
                    test_glow_opacity = step.params.get("test_glow_opacity", getattr(field_obj, "cr_test_glow_opacity", 0.22))
                    prediction_marker_opacity = step.params.get("prediction_marker_opacity", getattr(field_obj, "cr_prediction_marker_opacity", 0.86))
                    boundary_opacity = step.params.get("boundary_opacity", getattr(field_obj, "cr_boundary_opacity", 0.84))
                    trend_opacity = step.params.get("trend_opacity", getattr(field_obj, "cr_trend_opacity", 0.92))
                    read_opacity = step.params.get("read_opacity", getattr(field_obj, "cr_read_opacity", 0.62))

                    def register_cr_field():
                        object_registry[step.id] = field_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = field_obj

                    if mode == "drop_test_point":
                        if test_dot is not None:
                            final_pos = test_dot.get_center()
                            drop = step.params.get("drop_distance", 0.38)
                            test_dot.move_to(final_pos + UP * drop)
                            test_dot.set_opacity(0.0)
                            if test_glow is not None:
                                test_glow.move_to(test_dot.get_center())
                                test_glow.set_stroke(opacity=0.0)
                            drop_anims = [
                                test_dot.animate.move_to(final_pos).set_opacity(step.params.get("test_opacity", 1.0))
                            ]
                            if test_glow is not None:
                                drop_anims.append(test_glow.animate.move_to(final_pos).set_stroke(opacity=test_glow_opacity))
                            self.play(
                                AnimationGroup(*drop_anims, lag_ratio=0.0),
                                run_time=run_time,
                                rate_func=rate_functions.ease_out_sine,
                            )
                        else:
                            self.wait(run_time)
                        current_time += run_time
                        register_cr_field()
                        handled = True

                    elif mode == "classification_color_wave":
                        boundary_x = step.params.get("boundary_x", 0.0)
                        wave_direction = step.params.get("wave_direction", "toward_boundary")
                        ordered = sorted(
                            dots,
                            key=lambda dot: abs(dot.get_center()[0] - boundary_x),
                            reverse=(wave_direction == "toward_boundary"),
                        )
                        wave_count = step.params.get("wave_count", 6)
                        waves = []
                        for wave_index in range(wave_count):
                            wave_dots = ordered[
                                wave_index * len(ordered) // wave_count:
                                (wave_index + 1) * len(ordered) // wave_count
                            ]
                            if wave_dots:
                                waves.append(AnimationGroup(*[
                                    dot.animate.set_color(getattr(dot, "cr_target_color", "#6EA8FE")).set_opacity(colored_opacity)
                                    for dot in wave_dots
                                ], lag_ratio=0.0))
                        if waves:
                            self.play(Succession(*waves), run_time=run_time, rate_func=rate_functions.ease_in_out_sine)
                        else:
                            self.wait(run_time)
                        current_time += run_time
                        register_cr_field()
                        handled = True

                    elif mode == "draw_boundary":
                        if boundary is not None:
                            start = boundary.get_start()
                            end = boundary.get_end()
                            center = boundary.point_from_proportion(0.5)
                            boundary.put_start_and_end_on(center, center)
                            boundary.set_stroke(opacity=step.params.get("start_opacity", 0.18))
                            boundary_anims = [
                                boundary.animate.put_start_and_end_on(start, end).set_stroke(opacity=boundary_opacity)
                            ]
                            if boundary_label is not None and step.params.get("show_boundary_label", True):
                                boundary_label.set_opacity(0.0)
                                boundary_anims.append(boundary_label.animate.set_opacity(boundary_label_opacity))
                            self.play(
                                AnimationGroup(*boundary_anims, lag_ratio=0.22),
                                run_time=run_time,
                                rate_func=rate_functions.ease_in_out_sine,
                            )
                        else:
                            self.wait(run_time)
                        current_time += run_time
                        register_cr_field()
                        handled = True

                    elif mode == "claim_test_point":
                        if test_dot is not None:
                            target = vector_from_param(step.params.get("target", getattr(test_dot, "cr_class_position", test_dot.get_center())))
                            drift_time = min(step.params.get("drift_time", run_time * 0.62), run_time)
                            color_time = min(step.params.get("color_time", 0.6), max(0.05, run_time - drift_time))
                            hold_time = max(0.0, run_time - drift_time - color_time)
                            drift_anims = [test_dot.animate.move_to(target)]
                            if test_glow is not None:
                                drift_anims.append(test_glow.animate.move_to(target).set_stroke(opacity=test_glow_opacity))
                            self.play(AnimationGroup(*drift_anims, lag_ratio=0.0), run_time=drift_time, rate_func=rate_functions.ease_in_out_sine)
                            color_anims = [test_dot.animate.set_color(step.params.get("target_color", getattr(field_obj, "cr_blue_color", "#6EA8FE")))]
                            if test_glow is not None:
                                color_anims.append(test_glow.animate.set_color(step.params.get("target_color", getattr(field_obj, "cr_blue_color", "#6EA8FE"))).set_stroke(opacity=step.params.get("claimed_glow_opacity", test_glow_opacity * 0.75)))
                            self.play(AnimationGroup(*color_anims, lag_ratio=0.0), run_time=color_time, rate_func=rate_functions.ease_in_out_sine)
                            if hold_time > 0:
                                self.wait(hold_time)
                        else:
                            self.wait(run_time)
                        current_time += run_time
                        register_cr_field()
                        handled = True

                    elif mode == "regression_reset":
                        drain_time = min(step.params.get("drain_time", 0.8), run_time * 0.55)
                        boundary_time = min(step.params.get("boundary_fade_time", 0.5), run_time * 0.35)
                        axes_time = max(0.05, run_time - drain_time - boundary_time)
                        drain_anims = [dot.animate.set_color(neutral_color).set_opacity(dot_opacity) for dot in dots]
                        if test_dot is not None:
                            axis_position = vector_from_param(step.params.get("test_hold_position", getattr(test_dot, "cr_axis_position", test_dot.get_center())))
                            drain_anims.append(test_dot.animate.set_color(getattr(field_obj, "cr_white_color", "#F8FBFF")).move_to(axis_position).set_opacity(step.params.get("test_opacity", 0.0)))
                        if test_glow is not None:
                            glow_target = vector_from_param(step.params.get("test_hold_position", getattr(test_dot, "cr_axis_position", test_glow.get_center()))) if test_dot is not None else test_glow.get_center()
                            drain_anims.append(test_glow.animate.move_to(glow_target).set_color(getattr(field_obj, "cr_white_color", "#F8FBFF")).set_stroke(opacity=step.params.get("test_glow_reset_opacity", 0.0)))
                        self.play(AnimationGroup(*drain_anims, lag_ratio=0.0), run_time=drain_time, rate_func=rate_functions.ease_in_out_sine)
                        fade_anims = []
                        if boundary is not None:
                            fade_anims.append(boundary.animate.set_stroke(opacity=0.0))
                        if boundary_label is not None:
                            fade_anims.append(boundary_label.animate.set_opacity(0.0))
                        if trend_label is not None:
                            trend_label.set_opacity(0.0)
                        if prediction_marker is not None:
                            prediction_marker.set_opacity(0.0)
                        if fade_anims:
                            self.play(AnimationGroup(*fade_anims, lag_ratio=0.0), run_time=boundary_time, rate_func=rate_functions.ease_in_out_sine)
                        elif boundary_time > 0:
                            self.wait(boundary_time)
                        if x_axis is not None and y_axis is not None:
                            x_start, x_end = x_axis.get_start(), x_axis.get_end()
                            y_start, y_end = y_axis.get_start(), y_axis.get_end()
                            x_axis.put_start_and_end_on(x_start, x_start)
                            y_axis.put_start_and_end_on(y_start, y_start)
                            x_axis.set_stroke(opacity=axis_opacity)
                            y_axis.set_stroke(opacity=axis_opacity)
                            self.play(
                                AnimationGroup(
                                    x_axis.animate.put_start_and_end_on(x_start, x_end),
                                    y_axis.animate.put_start_and_end_on(y_start, y_end),
                                    lag_ratio=0.18,
                                ),
                                run_time=axes_time,
                                rate_func=rate_functions.ease_in_out_sine,
                            )
                        else:
                            self.wait(axes_time)
                        current_time += run_time
                        register_cr_field()
                        handled = True

                    elif mode == "draw_trend_line":
                        intro_anims = []
                        if ticks:
                            intro_anims.extend([tick.animate.set_stroke(opacity=tick_opacity) for tick in ticks])
                        if x_label is not None and step.params.get("show_axis_labels", True):
                            intro_anims.append(x_label.animate.set_opacity(axis_label_opacity))
                        if y_label is not None and step.params.get("show_axis_labels", True):
                            intro_anims.append(y_label.animate.set_opacity(axis_label_opacity))
                        intro_time = min(0.45, run_time * 0.28) if intro_anims else 0.0
                        if intro_anims:
                            self.play(AnimationGroup(*intro_anims, lag_ratio=0.05), run_time=intro_time, rate_func=rate_functions.ease_in_out_sine)
                        label_time = 0.0
                        if trend_line is not None:
                            reveal_style = step.params.get("trend_reveal", "center_out")
                            trend_time = max(0.05, run_time - intro_time)
                            if trend_label is not None and step.params.get("show_trend_label", True):
                                label_time = min(0.35, trend_time * 0.25)
                                trend_time = max(0.05, trend_time - label_time)

                            if reveal_style == "center_out":
                                trend_color_value = getattr(field_obj, "cr_trend_color", "#F5E4A0")
                                trend_width_value = getattr(field_obj, "cr_trend_width", 4.0)
                                sample_count = max(7, int(step.params.get("trend_reveal_samples", 17)))
                                sampled_points = [
                                    trend_line.point_from_proportion(i / (sample_count - 1))
                                    for i in range(sample_count)
                                ]
                                if len(sampled_points) >= 2:
                                    midpoint_index = len(sampled_points) // 2
                                    left_points = list(reversed(sampled_points[: midpoint_index + 1]))
                                    right_points = sampled_points[midpoint_index:]
                                    left_half = VMobject(color=trend_color_value)
                                    left_half.set_points_smoothly(left_points)
                                    left_half.set_stroke(width=trend_width_value, opacity=trend_opacity)
                                    right_half = VMobject(color=trend_color_value)
                                    right_half.set_points_smoothly(right_points)
                                    right_half.set_stroke(width=trend_width_value, opacity=trend_opacity)
                                    trend_line.set_stroke(opacity=0.0)
                                    self.play(
                                        AnimationGroup(Create(left_half), Create(right_half), lag_ratio=0.0),
                                        run_time=trend_time,
                                        rate_func=rate_functions.ease_in_out_sine,
                                    )
                                    trend_line.set_stroke(opacity=trend_opacity)
                                    self.remove(left_half, right_half)
                                else:
                                    self.play(Create(trend_line), run_time=trend_time, rate_func=rate_functions.ease_in_out_sine)
                                    trend_line.set_stroke(opacity=trend_opacity)
                            else:
                                self.play(Create(trend_line), run_time=trend_time, rate_func=rate_functions.ease_in_out_sine)
                                trend_line.set_stroke(opacity=trend_opacity)

                            if trend_label is not None and step.params.get("show_trend_label", True):
                                self.play(trend_label.animate.set_opacity(trend_label_opacity), run_time=label_time, rate_func=rate_functions.ease_in_out_sine)
                        else:
                            self.wait(max(0.05, run_time - intro_time))
                        current_time += run_time
                        register_cr_field()
                        handled = True

                    elif mode == "measure_value":
                        if test_dot is None:
                            self.wait(run_time)
                        else:
                            axis_pos = vector_from_param(step.params.get("axis_position", getattr(test_dot, "cr_axis_position", test_dot.get_center())))
                            intersection = vector_from_param(step.params.get("intersection", getattr(test_dot, "cr_intersection", axis_pos + UP)))
                            vertical_time = min(step.params.get("vertical_time", 0.7), run_time * 0.3)
                            horizontal_time = min(step.params.get("horizontal_time", 0.6), run_time * 0.25)
                            move_time = min(step.params.get("move_time", 0.8), run_time * 0.35)
                            hold_time = max(0.0, run_time - vertical_time - horizontal_time - move_time)
                            test_dot.move_to(axis_pos)
                            test_dot.set_opacity(0.0)
                            if test_glow is not None:
                                test_glow.move_to(axis_pos)
                                test_glow.set_stroke(opacity=0.0)
                            reentry_anims = [
                                test_dot.animate.set_color(getattr(field_obj, "cr_white_color", "#F8FBFF")).set_opacity(1.0)
                            ]
                            if test_glow is not None:
                                reentry_anims.append(test_glow.animate.set_color(getattr(field_obj, "cr_white_color", "#F8FBFF")).set_stroke(opacity=test_glow_opacity))
                            self.play(AnimationGroup(*reentry_anims, lag_ratio=0.0), run_time=min(0.28, vertical_time * 0.35))
                            if vertical_read is not None:
                                vertical_read.put_start_and_end_on(axis_pos, intersection)
                                vertical_read.set_stroke(opacity=read_opacity)
                                self.play(Create(vertical_read), run_time=vertical_time, rate_func=rate_functions.ease_in_out_sine)
                            else:
                                self.wait(vertical_time)
                            if horizontal_read is not None:
                                y_axis_x = y_axis.get_start()[0] if y_axis is not None else -4.35
                                horizontal_end = np.array([y_axis_x, intersection[1], 0.0])
                                horizontal_read.put_start_and_end_on(intersection, horizontal_end)
                                horizontal_read.set_stroke(opacity=read_opacity)
                                self.play(Create(horizontal_read), run_time=horizontal_time, rate_func=rate_functions.ease_in_out_sine)
                            else:
                                self.wait(horizontal_time)
                            dot_move_anims = [test_dot.animate.move_to(intersection)]
                            if test_glow is not None:
                                dot_move_anims.append(test_glow.animate.move_to(intersection).set_stroke(opacity=test_glow_opacity))
                            self.play(AnimationGroup(*dot_move_anims, lag_ratio=0.0), run_time=move_time, rate_func=rate_functions.ease_in_out_sine)
                            if prediction_marker is not None and step.params.get("show_prediction_marker", True):
                                marker_pos = np.array([y_axis.get_start()[0], intersection[1], 0.0]) if y_axis is not None else np.array([-4.35, intersection[1], 0.0])
                                prediction_marker.move_to(marker_pos)
                                self.play(prediction_marker.animate.set_opacity(prediction_marker_opacity), run_time=min(0.28, max(0.05, hold_time * 0.45 + 0.08)), rate_func=rate_functions.ease_in_out_sine)
                                hold_time = max(0.0, hold_time - min(0.28, max(0.05, hold_time * 0.45 + 0.08)))
                            if hold_time > 0:
                                self.wait(hold_time)
                        current_time += run_time
                        register_cr_field()
                        handled = True

                    elif mode == "final_dual_frame":
                        fade_time = min(step.params.get("read_fade_time", 0.5), run_time * 0.24)
                        color_time = min(step.params.get("left_color_time", 1.2), run_time * 0.55)
                        boundary_fade_time = min(step.params.get("boundary_fade_time", 0.35), run_time * 0.2)
                        hold_time = max(0.0, run_time - fade_time - color_time - boundary_fade_time)
                        fades = []
                        if vertical_read is not None:
                            fades.append(vertical_read.animate.set_stroke(opacity=0.0))
                        if horizontal_read is not None:
                            fades.append(horizontal_read.animate.set_stroke(opacity=step.params.get("horizontal_final_opacity", 0.18)))
                        if boundary is not None:
                            fades.append(boundary.animate.set_stroke(opacity=0.0))
                        if boundary_label is not None:
                            fades.append(boundary_label.animate.set_opacity(0.0))
                        if trend_label is not None and step.params.get("fade_trend_label", True):
                            fades.append(trend_label.animate.set_opacity(step.params.get("trend_label_final_opacity", 0.0)))
                        if fades:
                            self.play(AnimationGroup(*fades, lag_ratio=0.0), run_time=fade_time, rate_func=rate_functions.ease_in_out_sine)
                        elif fade_time > 0:
                            self.wait(fade_time)
                        left_cutoff = step.params.get("left_cutoff", 0.35)
                        left_dots = [dot for dot in dots if dot.get_center()[0] <= left_cutoff]
                        if left_dots:
                            ordered = sorted(left_dots, key=lambda dot: abs(dot.get_center()[0] - left_cutoff))
                            self.play(LaggedStart(*[
                                dot.animate.set_color(getattr(dot, "cr_target_color", "#F06A5A")).set_opacity(colored_opacity)
                                for dot in ordered
                            ], lag_ratio=0.05), run_time=color_time, rate_func=rate_functions.ease_in_out_sine)
                        else:
                            self.wait(color_time)
                        if prediction_marker is not None and step.params.get("keep_prediction_marker", True):
                            prediction_marker.set_opacity(prediction_marker_opacity)
                        if boundary_fade_time > 0:
                            self.wait(boundary_fade_time)
                        if hold_time > 0:
                            self.wait(hold_time)
                        current_time += run_time
                        register_cr_field()
                        handled = True

                    elif mode == "hold":
                        self.wait(run_time)
                        current_time += run_time
                        register_cr_field()
                        handled = True

                    else:
                        print(f"[mutate_classification_regression_field] WARNING: unknown mode={mode}. Skipping.")
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

                    def dot_target_opacity(dot, fallback=colored_opacity):
                        current_color = dot.get_color()
                        neutral = getattr(field_obj, "supervised_neutral_color", neutral_color)
                        if str(current_color).lower() == str(neutral).lower():
                            return dot_opacity
                        return fallback

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
                        snap_flash = step.params.get("snap_flash", False)
                        flash_time = min(step.params.get("snap_duration", 0.16), max(0.01, run_time))
                        if snap_flash and boundary is not None:
                            flash_anims = [boundary.animate.set_stroke(opacity=min(1.0, line_opacity + 0.04))]
                            if boundary_glow is not None:
                                flash_anims.append(boundary_glow.animate.set_stroke(opacity=step.params.get("snap_glow_opacity", 0.34)))
                            self.play(AnimationGroup(*flash_anims, lag_ratio=0.0), run_time=flash_time * 0.45)
                            settle_anims = [boundary.animate.set_stroke(opacity=line_opacity)]
                            if boundary_glow is not None:
                                settle_anims.append(boundary_glow.animate.set_stroke(opacity=glow_opacity))
                            self.play(AnimationGroup(*settle_anims, lag_ratio=0.0), run_time=flash_time * 0.55)
                            remaining = max(0.0, run_time - flash_time)
                            if remaining > 0:
                                self.wait(remaining)
                        else:
                            self.wait(max(0.01, run_time))
                        current_time += run_time
                        register_same_field()
                        handled = True

                    elif mode == "infer_rule":
                        fade_time = min(step.params.get("fade_out_time", 0.5), run_time * 0.28)
                        pause_time = min(step.params.get("pause_time", 0.5), max(0.0, run_time - fade_time))
                        settle_time = min(step.params.get("settle_time", 0.38), max(0.0, run_time - fade_time - pause_time))
                        requested_grow_time = step.params.get("grow_time")
                        if requested_grow_time is None:
                            grow_time = max(0.1, run_time - fade_time - pause_time - settle_time)
                        else:
                            grow_time = min(requested_grow_time, max(0.1, run_time - fade_time - pause_time - settle_time))
                        remainder = max(0.0, run_time - fade_time - pause_time - grow_time - settle_time)
                        restore_dot_opacity = step.params.get("restore_dot_opacity", colored_opacity)
                        final_line_opacity = step.params.get("final_line_opacity", line_opacity)
                        final_glow_opacity = step.params.get("final_glow_opacity", glow_opacity)
                        fade_anims = []
                        if boundary is not None:
                            fade_anims.append(boundary.animate.set_stroke(opacity=0.0))
                        if boundary_glow is not None:
                            fade_anims.append(boundary_glow.animate.set_stroke(opacity=0.0))
                        fade_anims.extend([dot.animate.set_opacity(dim_opacity) for dot in dots])
                        if fade_anims:
                            self.play(AnimationGroup(*fade_anims, lag_ratio=0.0), run_time=fade_time, rate_func=rate_functions.ease_in_out_sine)
                        if pause_time > 0:
                            self.wait(pause_time)

                        near_boundary_dots = []
                        if boundary is not None:
                            center = boundary.point_from_proportion(0.5)
                            left_target = boundary.get_start()
                            right_target = boundary.get_end()
                            boundary.put_start_and_end_on(center, center)
                            boundary.set_stroke(opacity=step.params.get("grow_start_opacity", 0.62))
                            grow_anims = [
                                boundary.animate.put_start_and_end_on(left_target, right_target).set_stroke(opacity=line_opacity),
                                *[dot.animate.set_opacity(step.params.get("growth_dot_opacity", max(dim_opacity, restore_dot_opacity * 0.82))) for dot in dots],
                            ]
                            if step.params.get("dot_response", False):
                                response_distance = step.params.get("response_distance", 0.48)
                                response_opacity = step.params.get("response_opacity", 1.0)
                                line_vec = right_target - left_target
                                line_len = np.linalg.norm(line_vec[:2]) or 1.0
                                for dot in dots:
                                    dot_vec = dot.get_center() - left_target
                                    distance = abs(line_vec[0] * dot_vec[1] - line_vec[1] * dot_vec[0]) / line_len
                                    if distance <= response_distance:
                                        near_boundary_dots.append(dot)
                                        grow_anims.append(dot.animate.set_opacity(response_opacity))
                            if boundary_glow is not None:
                                boundary_glow.put_start_and_end_on(center, center)
                                boundary_glow.set_stroke(opacity=step.params.get("grow_start_glow_opacity", 0.06))
                                grow_anims.append(
                                    boundary_glow.animate.put_start_and_end_on(left_target, right_target).set_stroke(opacity=glow_opacity)
                                )
                            self.play(AnimationGroup(*grow_anims, lag_ratio=0.0), run_time=grow_time, rate_func=rate_functions.ease_in_out_sine)
                            settle_anims = [boundary.animate.set_stroke(opacity=final_line_opacity)]
                            if boundary_glow is not None:
                                settle_anims.append(boundary_glow.animate.set_stroke(opacity=final_glow_opacity))
                            settle_anims.extend([dot.animate.set_opacity(restore_dot_opacity) for dot in dots])
                            for dot in near_boundary_dots:
                                settle_anims.append(dot.animate.set_opacity(step.params.get("response_settle_opacity", restore_dot_opacity)))
                            self.play(AnimationGroup(*settle_anims, lag_ratio=0.0), run_time=settle_time, rate_func=rate_functions.ease_out_sine)
                        else:
                            self.wait(grow_time + settle_time)
                        if remainder > 0:
                            self.wait(remainder)
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

                    elif mode == "category_emphasis":
                        warm_boost = step.params.get("warm_boost", 1.0)
                        cool_boost = step.params.get("cool_boost", 1.0)
                        settle_opacity = step.params.get("settle_opacity", colored_opacity)
                        warm_anims = [dot.animate.set_opacity(warm_boost) for dot in dots if getattr(dot, "supervised_class", "warm") == "warm"]
                        cool_anims = [dot.animate.set_opacity(cool_boost) for dot in dots if getattr(dot, "supervised_class", "warm") == "cool"]
                        self.play(AnimationGroup(*(warm_anims + cool_anims), lag_ratio=0.0), run_time=run_time * 0.45, rate_func=rate_functions.ease_out_sine)
                        self.play(AnimationGroup(*[dot.animate.set_opacity(settle_opacity) for dot in dots], lag_ratio=0.0), run_time=run_time * 0.55, rate_func=rate_functions.ease_in_out_sine)
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
                    pair = step.params.get("pair")
                    if pair and not pairs:
                        pairs = [pair]
                    font_size = step.params.get("font_size", 28)
                    color = step.params.get("color", "#F5F7FB")
                    text_opacity = step.params.get("text_opacity", 0.92)

                    dots = list(getattr(field_obj, "supervised_dots", VGroup())) if field_obj is not None else []
                    dim_field = step.params.get("dim_field", False) and bool(dots)
                    dim_opacity = step.params.get("dim_opacity", 0.38)
                    restore_opacity = step.params.get("restore_opacity", getattr(field_obj, "supervised_colored_opacity", 0.96) if field_obj is not None else 0.96)
                    dim_time = min(step.params.get("dim_time", 0.22), max(0.01, run_time * 0.15))
                    haze = None

                    def maybe_dim_field():
                        nonlocal haze
                        if not dim_field:
                            return
                        dim_anims = [dot.animate.set_opacity(dim_opacity) for dot in dots]
                        if step.params.get("readability_haze", False):
                            haze = RoundedRectangle(
                                width=step.params.get("haze_width", 4.8),
                                height=step.params.get("haze_height", 0.82),
                                corner_radius=0.18,
                                stroke_width=0,
                                fill_color=step.params.get("haze_color", "#05070B"),
                                fill_opacity=0.0,
                            )
                            haze.move_to(vector_from_param(step.params.get("haze_position", step.params.get("position", [0.0, 0.08, 0.0]))))
                            self.add(haze)
                            dim_anims.append(haze.animate.set_fill(opacity=step.params.get("haze_opacity", 0.26)))
                        self.play(AnimationGroup(*dim_anims, lag_ratio=0.0), run_time=dim_time)

                    def maybe_restore_field():
                        if not dim_field:
                            return
                        restore_anims = [dot.animate.set_opacity(restore_opacity) for dot in dots]
                        if haze is not None:
                            restore_anims.append(haze.animate.set_fill(opacity=0.0))
                        self.play(AnimationGroup(*restore_anims, lag_ratio=0.0), run_time=dim_time)
                        if haze is not None:
                            self.remove(haze)

                    if labels:
                        maybe_dim_field()
                        overlays = VGroup()
                        for item in labels:
                            txt = Text(item.get("text", ""), font_size=item.get("font_size", font_size), color=item.get("color", color), weight=MEDIUM)
                            txt.set_opacity(0.0)
                            txt.move_to(vector_from_param(item.get("position", [0, 0, 0])))
                            overlays.add(txt)
                        self.add(overlays)
                        fade_time = min(0.4, run_time * 0.18)
                        self.play(AnimationGroup(*[txt.animate.set_opacity(text_opacity) for txt in overlays], lag_ratio=0.0), run_time=fade_time)
                        hold_time = max(0.0, run_time - (fade_time * 2.0) - (dim_time * 2.0 if dim_field else 0.0))
                        if hold_time > 0:
                            self.wait(hold_time)
                        self.play(AnimationGroup(*[txt.animate.set_opacity(0.0) for txt in overlays], lag_ratio=0.0), run_time=fade_time)
                        self.remove(overlays)
                        maybe_restore_field()
                    elif pairs:
                        fade_time = step.params.get("fade_time", 0.3)
                        hold_time = step.params.get("hold_time")
                        if hold_time is None:
                            total_fades = len(pairs) * fade_time * 2.0
                            hold_time = max(0.2, (run_time - total_fades - (dim_time * 2.0 if dim_field else 0.0)) / max(1, len(pairs)))
                        maybe_dim_field()
                        for pair_text in pairs:
                            txt = Text(pair_text, font_size=font_size, color=color, weight=MEDIUM)
                            txt.set_opacity(0.0)
                            txt.move_to(vector_from_param(step.params.get("position", [0.0, 0.08, 0.0])))
                            self.add(txt)
                            self.play(txt.animate.set_opacity(text_opacity), run_time=fade_time)
                            self.wait(hold_time)
                            self.play(txt.animate.set_opacity(0.0), run_time=fade_time)
                            self.remove(txt)
                        maybe_restore_field()
                    else:
                        self.wait(run_time)
                    current_time += run_time
                    if field_obj is not None:
                        object_registry[step.id] = field_obj
                        step_zone_map[step.id] = step.zone
                        active_objects[step.zone] = field_obj
                    handled = True

                elif step.action == "show_supervised_types_showcase":
                    source_id = step.params.get("source_id")
                    field_obj = object_registry.get(source_id) if source_id else active_objects.get(step.zone)

                    field_fade_time = min(step.params.get("field_fade_time", 0.75), run_time * 0.35)
                    showcase_in_time = min(step.params.get("showcase_in_time", 0.9), run_time * 0.45)
                    hold_time = max(0.0, run_time - field_fade_time - showcase_in_time)

                    if field_obj is not None:
                        self.play(FadeOut(field_obj, scale=0.985), run_time=field_fade_time, rate_func=rate_functions.ease_in_out_sine)
                        active_objects.pop(step.zone, None)

                    title = Text(
                        step.params.get("subtitle", "Two types of Supervised Learning"),
                        font_size=step.params.get("subtitle_font_size", 27),
                        color=step.params.get("subtitle_color", "#B9C4D6"),
                        weight=MEDIUM,
                    )
                    title.set_opacity(0.0)
                    title.move_to(vector_from_param(step.params.get("subtitle_position", [0.0, 2.25, 0.0])))

                    def make_type_card(kind, side):
                        cfg = step.params.get(kind, {})
                        x = cfg.get("x", -2.45 if side == "left" else 2.45)
                        accent = cfg.get("accent", "#F28A5B" if side == "left" else "#6EA8FE")
                        card = VGroup()
                        panel = RoundedRectangle(
                            width=cfg.get("width", 3.75),
                            height=cfg.get("height", 2.45),
                            corner_radius=0.18,
                            stroke_width=1.4,
                            stroke_color=accent,
                            fill_color=step.params.get("panel_fill", "#080B12"),
                            fill_opacity=step.params.get("panel_opacity", 0.58),
                        )
                        panel.set_stroke(opacity=cfg.get("stroke_opacity", 0.44))
                        heading = Text(
                            cfg.get("title", "Classification" if side == "left" else "Regression"),
                            font_size=cfg.get("title_font_size", 34),
                            color=cfg.get("title_color", "#F5F7FB"),
                            weight=BOLD,
                        )
                        heading.move_to(panel.get_center() + UP * 0.64)
                        caption = Text(
                            cfg.get("caption", "Predict a category" if side == "left" else "Predict a number"),
                            font_size=cfg.get("caption_font_size", 19),
                            color=cfg.get("caption_color", "#B9C4D6"),
                            weight=MEDIUM,
                        )
                        caption.move_to(panel.get_center() + DOWN * 0.72)

                        if side == "left":
                            mini = VGroup(
                                Dot([-0.36, 0.0, 0], radius=0.075, color="#F28A5B"),
                                Dot([-0.12, 0.18, 0], radius=0.075, color="#F28A5B"),
                                Dot([-0.02, -0.16, 0], radius=0.075, color="#F28A5B"),
                                Dot([0.34, 0.05, 0], radius=0.075, color="#6EA8FE"),
                                Dot([0.58, 0.22, 0], radius=0.075, color="#6EA8FE"),
                                Dot([0.68, -0.12, 0], radius=0.075, color="#6EA8FE"),
                            )
                        else:
                            curve = VMobject(color="#6EA8FE")
                            curve.set_points_smoothly([
                                np.array([-0.72, -0.18, 0.0]),
                                np.array([-0.30, -0.02, 0.0]),
                                np.array([0.12, 0.16, 0.0]),
                                np.array([0.70, 0.28, 0.0]),
                            ])
                            curve.set_stroke(width=3.0, opacity=0.9)
                            dots_line = VGroup(
                                Dot([-0.64, -0.24, 0], radius=0.052, color="#B9C4D6"),
                                Dot([-0.25, -0.02, 0], radius=0.052, color="#B9C4D6"),
                                Dot([0.18, 0.08, 0], radius=0.052, color="#B9C4D6"),
                                Dot([0.55, 0.33, 0], radius=0.052, color="#B9C4D6"),
                            )
                            mini = VGroup(curve, dots_line)
                        mini.move_to(panel.get_center() + DOWN * 0.03)
                        card.add(panel, heading, mini, caption)
                        card.move_to(np.array([x, 0.12, 0.0]))
                        card.set_opacity(0.0)
                        return card

                    classification = make_type_card("classification", "left")
                    regression = make_type_card("regression", "right")
                    connector = Line(classification.get_right() + RIGHT * 0.18, regression.get_left() + LEFT * 0.18, color=step.params.get("connector_color", "#40506A"), stroke_width=1.2)
                    connector.set_stroke(opacity=0.0)
                    showcase = VGroup(title, connector, classification, regression)
                    self.add(showcase)
                    self.play(
                        AnimationGroup(
                            title.animate.set_opacity(step.params.get("subtitle_opacity", 0.92)),
                            connector.animate.set_stroke(opacity=step.params.get("connector_opacity", 0.32)),
                            classification.animate.set_opacity(1.0).shift(UP * 0.04),
                            regression.animate.set_opacity(1.0).shift(UP * 0.04),
                            lag_ratio=0.12,
                        ),
                        run_time=showcase_in_time,
                        rate_func=rate_functions.ease_out_sine,
                    )
                    if hold_time > 0:
                        self.wait(hold_time)
                    current_time += run_time
                    register_object(step.id, step.zone, showcase)
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
                    path_bands = getattr(road_obj, "road_path_bands", lower_lines)
                    path_edges = getattr(road_obj, "road_path_edges", VGroup())
                    path_fill = getattr(road_obj, "road_path_fill", None)
                    path_glow = getattr(road_obj, "road_path_glow", None)
                    uncertainty_particles = getattr(road_obj, "road_uncertainty_particles", VGroup())
                    upper_ambient = getattr(road_obj, "road_upper_ambient", None)
                    horizon_glow = getattr(road_obj, "road_horizon_glow", None)
                    horizon_bloom = getattr(road_obj, "road_horizon_bloom", None)
                    horizon_core = getattr(road_obj, "road_horizon_core", None)
                    horizon_left = getattr(road_obj, "road_horizon_left", None)
                    horizon_right = getattr(road_obj, "road_horizon_right", None)
                    point = getattr(road_obj, "road_point", None)
                    point_halo = getattr(road_obj, "road_point_halo", None)
                    horizon_y = getattr(road_obj, "road_horizon_y", step.params.get("horizon_y", -0.18))
                    horizon_half_width = step.params.get(
                        "horizon_half_width",
                        getattr(road_obj, "road_horizon_half_width", 4.75),
                    )

                    if mode == "settle":
                        structure = step.params.get("structure", 0.45)
                        band_opacity = step.params.get("band_opacity", 0.20)
                        edge_opacity = step.params.get("edge_opacity", 0.32)
                        particle_opacity = step.params.get("particle_opacity", 0.12)
                        point_opacity = step.params.get("point_opacity", 0.0)
                        anims = []
                        for index, band in enumerate(path_bands):
                            # Small perspective-preserving shifts make the field visibly organize
                            # without becoming a busy road drawing.
                            shift = DOWN * step.params.get("band_shift", 0.08) * (1.0 - min(index, 5) * 0.08)
                            anims.append(band.animate.shift(shift).set_stroke(opacity=band_opacity * (1.0 - 0.05 * index)))
                        for edge in path_edges:
                            anims.append(edge.animate.set_stroke(opacity=edge_opacity))
                        if path_fill is not None:
                            anims.append(path_fill.animate.set_fill(opacity=step.params.get("path_fill_opacity", 0.15)))
                        if path_glow is not None:
                            anims.append(path_glow.animate.set_fill(opacity=step.params.get("path_glow_opacity", 0.075)))
                        for index, dot in enumerate(uncertainty_particles):
                            drift = np.array([0.0, -0.05 - 0.01 * (index % 3), 0.0]) * structure
                            anims.append(dot.animate.shift(drift).set_opacity(particle_opacity))
                        if point is not None and point_opacity > 0:
                            # Manim Dot does not expose get_opacity() consistently; set a tiny
                            # visible baseline before animating so fade-in works without crashing.
                            point.set_opacity(0.001)
                            anims.append(point.animate.set_opacity(point_opacity))
                        if point_halo is not None and step.params.get("point_halo_opacity", 0.0) > 0:
                            anims.append(point_halo.animate.set_stroke(opacity=step.params.get("point_halo_opacity", 0.06)))
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
                        core_opacity = step.params.get("core_opacity", 0.72)
                        wing_opacity = step.params.get("wing_opacity", 0.38)
                        glow_opacity = step.params.get("glow_opacity", 0.24)
                        bloom_opacity = step.params.get("bloom_opacity", 0.11)
                        lower_opacity = step.params.get("lower_opacity", 0.16)
                        anims = []
                        for index, band in enumerate(path_bands):
                            anims.append(band.animate.set_stroke(opacity=lower_opacity * (1.0 - 0.05 * index)))
                        for edge in path_edges:
                            anims.append(edge.animate.set_stroke(opacity=step.params.get("edge_opacity", 0.36)))
                        if uncertainty_particles:
                            anims.extend([dot.animate.set_opacity(step.params.get("particle_opacity", 0.055)) for dot in uncertainty_particles])
                        if horizon_bloom is not None:
                            anims.append(horizon_bloom.animate.set_fill(opacity=bloom_opacity))
                        if horizon_glow is not None:
                            anims.append(horizon_glow.animate.set_stroke(opacity=glow_opacity, width=step.params.get("glow_width", 18.0)))
                        if horizon_core is not None:
                            anims.append(horizon_core.animate.set_stroke(opacity=core_opacity, width=step.params.get("core_width", 1.35)))
                        if horizon_left is not None:
                            anims.append(
                                horizon_left.animate.put_start_and_end_on(
                                    np.array([-horizon_half_width * 0.40, horizon_y, 0.0]),
                                    np.array([-horizon_half_width, horizon_y, 0.0]),
                                ).set_stroke(opacity=wing_opacity, width=step.params.get("wing_width", 0.9))
                            )
                        if horizon_right is not None:
                            anims.append(
                                horizon_right.animate.put_start_and_end_on(
                                    np.array([horizon_half_width * 0.40, horizon_y, 0.0]),
                                    np.array([horizon_half_width, horizon_y, 0.0]),
                                ).set_stroke(opacity=wing_opacity, width=step.params.get("wing_width", 0.9))
                            )
                        if point is not None:
                            anims.append(point.animate.set_opacity(step.params.get("point_opacity", 0.36)))
                        if point_halo is not None:
                            anims.append(point_halo.animate.set_stroke(opacity=step.params.get("point_halo_opacity", 0.08)))
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
                        anims = []
                        if upper_ambient is not None:
                            anims.append(
                                upper_ambient.animate.set_fill(
                                    step.params.get("target_color", "#1A2740"),
                                    opacity=step.params.get("target_opacity", 0.16),
                                )
                            )
                        if horizon_bloom is not None:
                            anims.append(horizon_bloom.animate.set_fill(opacity=step.params.get("bloom_opacity", 0.15)))
                        if horizon_glow is not None:
                            anims.append(horizon_glow.animate.set_stroke(opacity=step.params.get("glow_opacity", 0.26)))
                        if path_glow is not None:
                            anims.append(path_glow.animate.set_fill(opacity=step.params.get("path_glow_opacity", 0.10)))
                        if point is not None:
                            anims.append(point.animate.set_opacity(step.params.get("point_opacity", 0.46)))
                        if point_halo is not None:
                            anims.append(point_halo.animate.set_stroke(opacity=step.params.get("point_halo_opacity", 0.10)))
                        if anims:
                            self.play(
                                AnimationGroup(*anims, lag_ratio=0.0),
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
                            start = _as_vector(step.params.get("start", [0.0, -1.02, 0.0]))
                            cross = _as_vector(step.params.get("cross", [0.0, horizon_y + 0.02, 0.0]))
                            rest = _as_vector(step.params.get("rest", [0.0, 1.06, 0.0]))
                            cross_at = max(0.05, min(run_time - 0.05, step.params.get("cross_at", run_time * 0.40)))
                            remaining = max(0.05, run_time - cross_at)
                            point.move_to(start)
                            point.set_opacity(step.params.get("point_opacity", 1.0))
                            if point_halo is not None:
                                point_halo.move_to(start)
                                point_halo.set_stroke(opacity=step.params.get("point_halo_opacity", 0.18))
                            approach_mid = _as_vector(step.params.get("approach_mid", [0.0, -0.48, 0.0]))
                            path_to_cross = VMobject()
                            path_to_cross.set_points_smoothly([start, approach_mid, cross])
                            first_anims = [MoveAlongPath(point, path_to_cross)]
                            if point_halo is not None:
                                first_anims.append(MoveAlongPath(point_halo, path_to_cross.copy()))
                            self.play(
                                AnimationGroup(*first_anims, lag_ratio=0.0),
                                run_time=cross_at,
                                rate_func=linear,
                            )
                            response_anims = [point.animate.move_to(rest)]
                            if point_halo is not None:
                                response_anims.append(point_halo.animate.move_to(rest).set_stroke(opacity=step.params.get("rest_halo_opacity", 0.14)))
                            if horizon_bloom is not None:
                                response_anims.append(horizon_bloom.animate.set_fill(opacity=step.params.get("response_bloom_opacity", 0.19)))
                            if horizon_core is not None:
                                response_anims.append(horizon_core.animate.set_stroke(opacity=step.params.get("line_response_opacity", 0.86), width=step.params.get("response_stroke_width", 1.55)))
                            if horizon_left is not None:
                                response_anims.append(horizon_left.animate.set_stroke(opacity=step.params.get("wing_response_opacity", 0.46), width=step.params.get("response_wing_width", 1.0)))
                            if horizon_right is not None:
                                response_anims.append(horizon_right.animate.set_stroke(opacity=step.params.get("wing_response_opacity", 0.46), width=step.params.get("response_wing_width", 1.0)))
                            if horizon_glow is not None:
                                response_anims.append(horizon_glow.animate.set_stroke(opacity=step.params.get("response_glow_opacity", 0.30)))
                            if upper_ambient is not None:
                                response_anims.append(upper_ambient.animate.set_fill(step.params.get("rest_upper_color", "#1C2E4B"), opacity=step.params.get("rest_upper_opacity", 0.18)))
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
                                    Wait(run_time * 0.18),
                                    glints.animate.set_opacity(0.22),
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
                        if len(glints) != 0:
                            glints.set_opacity(0.22)
                            new_obj.add(glints)
                            new_obj.taxonomy_cluster_lines = glints
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
                        source_lines = getattr(source_obj, "taxonomy_cluster_lines", VGroup())
                        held_lines = taxonomy_density_glints(merged_params)
                        if len(source_lines) != 0:
                            source_lines.set_opacity(0.22)
                            new_obj.add(source_lines)
                            new_obj.taxonomy_cluster_lines = source_lines
                        elif len(held_lines) != 0:
                            held_lines.set_opacity(0.22)
                            new_obj.add(held_lines)
                            new_obj.taxonomy_cluster_lines = held_lines
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
                            cloud_breath.set_opacity(0.42)
                            hold_anims.append(Succession(Transform(source_clouds, cloud_breath), source_clouds.animate.set_opacity(0.40)))
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
                                    halo_stages.append(AnimationGroup(*[halo.animate.set_opacity(0.32) for halo in group_items], lag_ratio=0.0))
                            if halo_stages:
                                anims.append(Succession(*halo_stages, AnimationGroup(*[halo.animate.set_opacity(0.42) for halo in ordered_influence], lag_ratio=0.0)))
                        if len(territories) != 0:
                            for territory in territories:
                                territory.set_opacity(0)
                            self.add(territories)
                            anims.append(
                                Succession(
                                    Wait(run_time * 0.10),
                                    territories.animate.set_opacity(0.82),
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
                            influence.set_opacity(0.42)
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