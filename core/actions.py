from manim import *

BG_COLOR = "#0b1020"
PRIMARY = BLUE_C
SECONDARY = TEAL_C
ACCENT = YELLOW_C
HIGHLIGHT = GREEN_C
WARNING = ORANGE
MUTED = GREY_B
TEXT_MAIN = WHITE
TEXT_SUB = GREY_A

ZONE_POSITIONS = {
    "title": UP * 3.15,
    "center": ORIGIN,
    "bottom": DOWN * 2.45,
    "left": LEFT * 4.4,
    "right": RIGHT * 4.4,
}


def place_in_zone(obj, zone: str):
    target = ZONE_POSITIONS.get(zone, ORIGIN)
    obj.move_to(target)
    return obj


def fit_to_width(obj, max_width: float):
    if obj.width > max_width:
        obj.scale(max_width / obj.width)
    return obj


def make_text_block(
    text: str,
    font_size: int,
    color=TEXT_MAIN,
    weight=NORMAL,
    max_width: float = 10.8,
    line_spacing: float = 0.92,
):
    obj = Text(
        text,
        font_size=font_size,
        color=color,
        weight=weight,
        line_spacing=line_spacing,
    )
    fit_to_width(obj, max_width)
    return obj


def make_show_title(params, zone):
    title = make_text_block(
        params["text"],
        font_size=42,
        color=TEXT_MAIN,
        weight=BOLD,
        max_width=11.8,
        line_spacing=0.9,
    )
    underline = Line(LEFT * 2.6, RIGHT * 2.6, color=TEXT_SUB, stroke_width=2)
    underline.next_to(title, DOWN, buff=0.18)
    obj = VGroup(title, underline)
    place_in_zone(obj, zone)
    return obj


def make_show_text(params, zone):
    text = make_text_block(
        params["text"],
        font_size=30,
        color=TEXT_MAIN,
        weight=MEDIUM,
        max_width=10.6,
    )
    place_in_zone(text, zone)
    return text


def make_highlight_text(params, zone):
    text = make_text_block(
        params["text"],
        font_size=34,
        color=ACCENT,
        weight=BOLD,
        max_width=11.0,
    )
    place_in_zone(text, zone)
    return text


def _flow_node(label: str, stroke_color):
    txt = Text(label, font_size=26, weight=MEDIUM, color=TEXT_MAIN)

    box = RoundedRectangle(
        corner_radius=0.16,
        width=max(2.4, txt.width + 0.8),
        height=max(1.15, txt.height + 0.55),
        stroke_color=stroke_color,
        stroke_width=3,
        fill_color="#151922",
        fill_opacity=1.0,
    )

    glow = RoundedRectangle(
        corner_radius=0.18,
        width=box.width + 0.12,
        height=box.height + 0.12,
        stroke_color=stroke_color,
        stroke_width=1,
    ).set_opacity(0.22)

    txt.move_to(box.get_center())
    return VGroup(glow, box, txt)


def make_flow_diagram(params, zone):
    left_text = params.get("left", "Input")
    middle_text = params.get("middle", "System")
    right_text = params.get("right", "Output")

    left = _flow_node(left_text, PRIMARY)
    middle = _flow_node(middle_text, ACCENT)
    right = _flow_node(right_text, SECONDARY)

    row = VGroup(left, middle, right).arrange(RIGHT, buff=1.0)

    arrow1 = Arrow(
        left.get_right(),
        middle.get_left(),
        buff=0.14,
        stroke_width=4,
        color=TEXT_SUB,
        max_stroke_width_to_length_ratio=10,
    )
    arrow2 = Arrow(
        middle.get_right(),
        right.get_left(),
        buff=0.14,
        stroke_width=4,
        color=TEXT_SUB,
        max_stroke_width_to_length_ratio=10,
    )

    full = VGroup(row, arrow1, arrow2)
    place_in_zone(full, zone)
    return full


def make_transform_text(params, zone):
    obj = make_text_block(
        params["to"],
        font_size=34,
        color=PRIMARY,
        weight=BOLD,
        max_width=10.8,
    )
    place_in_zone(obj, zone)
    return obj


def make_square_stage_sequence(params, zone):
    stage = params.get("stage", "clean")

    clean = Square(side_length=1.95, color=PRIMARY, stroke_width=4)
    rotated = Square(side_length=1.95, color=HIGHLIGHT, stroke_width=4).rotate(PI / 6)
    distorted = Square(side_length=1.95, color=WARNING, stroke_width=4)
    distorted.stretch(1.35, 0)
    distorted.stretch(0.82, 1)

    noisy = Square(side_length=1.95, color=GREY_B, stroke_width=3)
    noisy.set_fill(GREY_C, opacity=0.32)

    if stage == "clean":
        current = clean
        ghosts = VGroup()
        label = Text("clean case", font_size=24, color=TEXT_SUB)
    elif stage == "rotated":
        current = rotated
        g1 = clean.copy().set_opacity(0.18).shift(LEFT * 2.8)
        ghosts = VGroup(g1)
        label = Text("reality rotates it", font_size=24, color=TEXT_SUB)
    elif stage == "distorted":
        current = distorted
        g1 = clean.copy().set_opacity(0.12).shift(LEFT * 3.1)
        g2 = rotated.copy().set_opacity(0.18).shift(LEFT * 1.4)
        ghosts = VGroup(g1, g2)
        label = Text("then it distorts", font_size=24, color=TEXT_SUB)
    elif stage == "noisy":
        current = noisy
        g1 = clean.copy().set_opacity(0.08).shift(LEFT * 3.3)
        g2 = rotated.copy().set_opacity(0.12).shift(LEFT * 1.7)
        g3 = distorted.copy().set_opacity(0.18).shift(LEFT * 0.1)
        ghosts = VGroup(g1, g2, g3)
        label = Text("the rule becomes fragile", font_size=24, color=TEXT_SUB)
    else:
        current = clean
        ghosts = VGroup()
        label = Text(stage, font_size=24, color=TEXT_SUB)

    current.shift(RIGHT * 1.9 if stage in {"rotated", "distorted", "noisy"} else ORIGIN)
    label.next_to(current, DOWN, buff=0.42)

    group = VGroup(ghosts, current, label)
    place_in_zone(group, zone)
    return group


def transition_in_for(obj, transition_name: str):
    if transition_name == "fade":
        return FadeIn(obj, shift=UP * 0.3, scale=0.96)
    if transition_name == "write":
        return Write(obj)
    if transition_name == "create":
        return Create(obj)
    if transition_name == "grow":
        return GrowFromCenter(obj)
    if transition_name == "transform":
        return FadeIn(obj)
    return FadeIn(obj)


def transition_out_for(obj, transition_name: str):
    if obj is None:
        return None

    if transition_name == "fade":
        return FadeOut(obj, shift=DOWN * 0.08)
    if transition_name == "write":
        return FadeOut(obj)
    if transition_name == "create":
        return FadeOut(obj)
    if transition_name == "grow":
        return FadeOut(obj, scale=0.96)
    if transition_name == "transform":
        return FadeOut(obj)
    return FadeOut(obj)


def build_object(step_dict):
    action = step_dict["action"]
    params = step_dict.get("params", {})
    zone = step_dict.get("zone", "center")

    if action == "show_title":
        return make_show_title(params, zone)

    if action == "show_text":
        return make_show_text(params, zone)

    if action == "highlight_text":
        return make_highlight_text(params, zone)

    if action == "show_flow_diagram":
        return make_flow_diagram(params, zone)

    if action == "transform_text":
        return make_transform_text(params, zone)

    if action == "square_stage_sequence":
        return make_square_stage_sequence(params, zone)

    if action == "fade_out":
        return None

    raise ValueError(f"Unsupported action: {action}")