from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


AllowedAction = Literal[
    "show_title",
    "show_text",
    "show_math",
    "show_flow_diagram",
    "show_function_flow",
    "show_plot",
    "show_bullet_list",
    "highlight_text",
    "show_shape",
    "square_stage_sequence",
    "transform_text",
    "show_manual_rule_card",
    "transform_manual_rule_card",
    "mutate_manual_rule_card",
    "show_manual_rule_ghosts",
    "pulse_manual_rule_ghost",
    "show_axis_free_curve",
    "pause",
    "fade_out",
    "show_box_label",
    "show_arrow",
    "hold",
    "highlight_group",
    "dim_group",
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
    "show_training_loop",
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
    "show_workflow_cycle",
    "mutate_workflow_cycle",
    "show_road_ahead_field",
    "mutate_road_ahead_field",
    "show_supervised_field",
    "mutate_supervised_field",
    "show_supervised_examples",
    "show_supervised_types_showcase",
    "show_supervised_resolution",
    "show_classification_regression_field",
    "mutate_classification_regression_field",
    "show_linear_regression_fit",
    "mutate_linear_regression_fit",
    "show_linear_formula_system",
    "mutate_linear_formula_system",
]

AllowedZone = Literal[
    "title",
    "top",
    "center",
    "bottom",
    "left",
    "right",
    "full",
    "center_left",
    "center_mid_left",
    "center_mid_right",
    "center_right",
    "left-center",
    "center_band",
    "center_left_center",
    "center_span",
    "pattern_right_compact",
]
AllowedTransition = Literal["fade", "write", "create", "grow", "transform", "none", "smooth"]


class VoiceConfig(BaseModel):
    language: str = "en-IN"
    speaker: str = "priya"
    model: str = "bulbul:v3"


class NarrationSegment(BaseModel):
    id: str
    text: str
    emphasis: Optional[str] = None


class VisualStep(BaseModel):
    id: str
    anchor: str
    action: AllowedAction
    params: Dict[str, Any] = Field(default_factory=dict)
    offset: float = 0.0

    zone: AllowedZone = "center"
    transition_in: AllowedTransition = "fade"
    transition_out: Optional[AllowedTransition] = "fade"
    persist: bool = True
    replace: Optional[AllowedZone] = None
    duration: Optional[float] = None
    camera_scale: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_scene_two_format(cls, raw: Any):
        if not isinstance(raw, dict):
            return raw

        data = dict(raw)
        params = dict(data.get("params") or {})

        if "content" in data:
            params.setdefault("content", data["content"])
        if "style" in data and isinstance(data["style"], dict):
            params.update(data["style"])
        if "notes" in data:
            params.setdefault("notes", data["notes"])

        action = data.get("action")
        content = data.get("content")

        if action == "show_text" and isinstance(content, str):
            params.setdefault("text", content)
        if action == "show_math" and isinstance(content, str):
            params.setdefault("math", content)
        if action == "transform_text" and isinstance(content, str):
            params.setdefault("to", content)
        if action in {"show_box_label", "transform_box_label", "transform_box_to_pattern"} and isinstance(content, str):
            params.setdefault("label", content)
        if action in {"show_arrow", "transform_arrow"} and isinstance(content, str):
            params.setdefault("direction", content)

        data["params"] = params
        return data


class SceneNotes(BaseModel):
    tone: str
    pacing: str
    animation_guidelines: str


class SceneSpec(BaseModel):
    scene_id: str
    video_title: str
    scene_title: str
    order: int
    duration_mode: Literal["audio_driven"] = "audio_driven"
    voice: VoiceConfig
    narration: List[NarrationSegment]
    visual_timeline: List[VisualStep]
    notes: SceneNotes | List[str]

    @model_validator(mode="after")
    def validate_scene(self):
        narration_ids = [n.id for n in self.narration]
        if len(narration_ids) != len(set(narration_ids)):
            raise ValueError("Narration segment ids must be unique.")

        visual_ids = [v.id for v in self.visual_timeline]
        if len(visual_ids) != len(set(visual_ids)):
            raise ValueError("Visual step ids must be unique.")

        valid_anchors = set(narration_ids)
        for step in self.visual_timeline:
            if step.anchor not in valid_anchors:
                raise ValueError(
                    f"Visual step '{step.id}' references unknown anchor '{step.anchor}'."
                )

        if not self.narration:
            raise ValueError("Scene must contain at least one narration segment.")

        if not self.visual_timeline:
            raise ValueError("Scene must contain at least one visual step.")

        return self