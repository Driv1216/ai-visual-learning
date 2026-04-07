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
    "top": UP * 2.6,
    "center": ORIGIN,
    "bottom": DOWN * 2.45,
    "left": LEFT * 4.4,
    "right": RIGHT * 4.4,
    "full": ORIGIN,
    "center_left": LEFT * 3.2,
    "center_mid_left": LEFT * 1.5,
    "center_mid_right": RIGHT * 1.5,
    "center_right": RIGHT * 3.2,
    "center_band": ORIGIN,
    "center_left_center": LEFT * 1.0,
    "center_span": ORIGIN,
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
        font_size=params.get("font_size", 28 if zone == "top" else 30),
        color=params.get("color", TEXT_MAIN),
        weight=params.get("weight", MEDIUM),
        max_width=10.6,
    )
    text.set_opacity(params.get("opacity", 1.0))
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
        font_size=params.get("font_size", 34),
        color=params.get("color", TEXT_MAIN),
        weight=params.get("weight", BOLD),
        max_width=10.8,
    )
    obj.set_opacity(params.get("opacity", 1.0))
    place_in_zone(obj, zone)
    return obj


def make_square_stage_sequence(params, zone):
    stage = params.get("stage", "clean")

    def base_square(color=PRIMARY, stroke_width=4):
        square = Square(side_length=2.0, color=color, stroke_width=stroke_width)
        square.set_fill(color, opacity=0.06)
        return square

    def rule_chip(text, color=TEXT_SUB):
        chip_text = Text(text, font_size=18, color=TEXT_MAIN, weight=MEDIUM)
        chip_box = RoundedRectangle(
            corner_radius=0.12,
            width=chip_text.width + 0.34,
            height=chip_text.height + 0.22,
            stroke_color=color,
            stroke_width=1.5,
            fill_color="#141a26",
            fill_opacity=0.92,
        )
        chip_text.move_to(chip_box.get_center())
        return VGroup(chip_box, chip_text)

    def right_angle_marker(anchor, h_dir=RIGHT, v_dir=UP, size=0.18, color=ACCENT):
        return VMobject().set_points_as_corners(
            [
                anchor + h_dir * size,
                anchor,
                anchor + v_dir * size,
            ]
        ).set_stroke(color=color, width=3)

    def equal_side_ticks(start, end, count=2, length=0.18, color=ACCENT):
        line = Line(start, end)
        direction = line.get_unit_vector()
        normal = rotate_vector(direction, PI / 2)
        center = line.point_from_proportion(0.5)
        offsets = [0.0] if count == 1 else np.linspace(-0.12, 0.12, count)
        ticks = VGroup()
        for offset in offsets:
            point = center + direction * offset
            ticks.add(
                Line(
                    point - normal * (length / 2),
                    point + normal * (length / 2),
                    color=color,
                    stroke_width=3,
                )
            )
        return ticks

    clean = base_square()

    measured = base_square()
    measured_ticks = VGroup(
        equal_side_ticks(measured.get_corner(UL), measured.get_corner(UR)),
        equal_side_ticks(measured.get_corner(UR), measured.get_corner(DR)),
        equal_side_ticks(measured.get_corner(DR), measured.get_corner(DL)),
        equal_side_ticks(measured.get_corner(DL), measured.get_corner(UL)),
    )
    measured_angles = VGroup(
        right_angle_marker(measured.get_corner(UL), RIGHT, DOWN),
        right_angle_marker(measured.get_corner(UR), LEFT, DOWN),
        right_angle_marker(measured.get_corner(DR), LEFT, UP),
        right_angle_marker(measured.get_corner(DL), RIGHT, UP),
    )
    measured_rules = VGroup(
        rule_chip("equal sides", ACCENT).next_to(measured, UP, buff=0.36),
        rule_chip("90° corners", ACCENT).next_to(measured, RIGHT, buff=0.42),
    )
    measured_group = VGroup(measured, measured_ticks, measured_angles, measured_rules)

    tension = base_square(PRIMARY, stroke_width=3.5).rotate(PI / 18)
    tension_glow = tension.copy().set_stroke(color=HIGHLIGHT, width=8, opacity=0.12).set_fill(opacity=0.03)
    tension_rules = VGroup(
        rule_chip("real images complicate it", MUTED).next_to(tension, UP, buff=0.38),
        rule_chip("clean rules start bending", TEXT_SUB).next_to(tension, RIGHT, buff=0.44),
    )
    tension_group = VGroup(tension_glow, tension, tension_rules)

    rotated = base_square(HIGHLIGHT).rotate(PI / 6)
    rotated_rules = VGroup(
        rule_chip("still a square?", HIGHLIGHT).next_to(rotated, UP, buff=0.38),
        rule_chip("orientation changed", TEXT_SUB).next_to(rotated, RIGHT, buff=0.44),
    )
    rotated_group = VGroup(rotated, rotated_rules)

    distorted = Polygon(
        LEFT * 1.05 + UP * 1.0,
        RIGHT * 0.95 + UP * 1.22,
        RIGHT * 1.22 + DOWN * 0.82,
        LEFT * 1.18 + DOWN * 1.05,
        color=WARNING,
        stroke_width=4,
    )
    distorted.set_fill(WARNING, opacity=0.08)
    blur_halo = distorted.copy().set_stroke(width=10, opacity=0.16).set_fill(opacity=0.02)
    distorted_group = VGroup(
        blur_halo,
        distorted,
        rule_chip("blur + uneven edges", WARNING).next_to(distorted, UP, buff=0.4),
        rule_chip("rule exceptions pile up", TEXT_SUB).next_to(distorted, RIGHT, buff=0.42),
    )

    noisy = Polygon(
        LEFT * 1.12 + UP * 0.92,
        RIGHT * 0.82 + UP * 1.08,
        RIGHT * 1.18 + DOWN * 0.66,
        RIGHT * 0.22 + DOWN * 1.16,
        LEFT * 1.24 + DOWN * 0.88,
        LEFT * 1.36 + UP * 0.12,
        color=GREY_B,
        stroke_width=3,
    )
    noisy.set_fill(GREY_C, opacity=0.24)
    noisy_specks = VGroup(
        *[
            Dot(
                point,
                radius=0.04,
                color=GREY_A,
            )
            for point in (
                UP * 0.52 + LEFT * 0.2,
                UP * 0.12 + RIGHT * 0.48,
                DOWN * 0.32 + LEFT * 0.56,
                DOWN * 0.62 + RIGHT * 0.14,
            )
        ]
    )
    noisy_group = VGroup(
        noisy,
        noisy_specks,
        rule_chip("lighting noise", MUTED).next_to(noisy, UP, buff=0.4),
        rule_chip("shape ambiguity", MUTED).next_to(noisy, RIGHT, buff=0.42),
    )

    lighting = noisy.copy().set_stroke(color=GREY_A, width=3).set_fill(GREY_D, opacity=0.14)
    lighting_specks = VGroup(
        *[
            Dot(dot.get_center(), radius=0.04, color=GREY_B).set_opacity(0.55)
            for dot in noisy_specks
        ]
    )
    lighting_group = VGroup(
        lighting,
        lighting_specks,
        rule_chip("bad lighting", MUTED).next_to(lighting, UP, buff=0.4),
        rule_chip("edges get harder to read", MUTED).next_to(lighting, RIGHT, buff=0.42),
    )

    pressure_square = noisy.copy().set_fill(opacity=0.2)
    pressure_specks = noisy_specks.copy()
    top_left_card = rule_chip("if edge broken...", WARNING).next_to(
        pressure_square, UL, buff=0.38
    )
    top_right_card = rule_chip("if rotated...", HIGHLIGHT).next_to(
        pressure_square, UR, buff=0.38
    )
    bottom_left_card = rule_chip("if blur > threshold...", MUTED).next_to(
        pressure_square, DL, buff=0.38
    )
    bottom_right_card = rule_chip("if angle almost 90°...", ACCENT).next_to(
        pressure_square, DR, buff=0.38
    )
    bottom_card = rule_chip("if shadow present...", WARNING).next_to(
        pressure_square, DOWN, buff=0.54
    )
    pressure_cards = VGroup(
        top_left_card,
        top_right_card,
        bottom_left_card,
        bottom_right_card,
        bottom_card,
    )
    pressure_lines = VGroup(
        Line(
            top_left_card.get_edge_center(DR),
            pressure_square.get_edge_center(UL),
            color=TEXT_SUB,
            stroke_width=2,
        ),
        Line(
            top_right_card.get_edge_center(DL),
            pressure_square.get_edge_center(UR),
            color=TEXT_SUB,
            stroke_width=2,
        ),
        Line(
            bottom_left_card.get_edge_center(UR),
            pressure_square.get_edge_center(DL),
            color=TEXT_SUB,
            stroke_width=2,
        ),
        Line(
            bottom_right_card.get_edge_center(UL),
            pressure_square.get_edge_center(DR),
            color=TEXT_SUB,
            stroke_width=2,
        ),
        Line(
            bottom_card.get_edge_center(UP),
            pressure_square.get_edge_center(DOWN),
            color=TEXT_SUB,
            stroke_width=2,
        ),
    )
    pressure_group = VGroup(pressure_square, pressure_specks, pressure_cards, pressure_lines)
    pressure_group.scale(0.72)
    pressure_group.shift(pressure_square.get_center() - pressure_group.get_center())

    wall_square = noisy.copy().set_fill(opacity=0.16).scale(0.9)
    wall_barrier = Rectangle(
        width=0.7,
        height=3.4,
        stroke_color=WARNING,
        stroke_width=3,
        fill_color="#1a202c",
        fill_opacity=0.98,
    )
    wall_pair = VGroup(wall_square, wall_barrier).arrange(RIGHT, buff=1.0)
    wall_label = Text("too many rules", font_size=21, color=TEXT_MAIN, weight=MEDIUM)
    wall_label.next_to(wall_barrier, RIGHT, buff=0.28)
    blocked_arrow = Arrow(
        wall_square.get_right(),
        wall_barrier.get_left(),
        buff=0.12,
        stroke_width=4,
        color=WARNING,
        max_stroke_width_to_length_ratio=10,
    )
    blocked_cross = Cross(blocked_arrow, stroke_color=WARNING, stroke_width=5).scale(0.52)
    wall_group = VGroup(
        wall_square,
        wall_barrier,
        wall_label,
        blocked_arrow,
        blocked_cross,
    )

    stage_map = {
        "clean": (clean, "clean case"),
        "measured": (measured_group, "write the rules"),
        "tension": (tension_group, "then the real world intrudes"),
        "rotated": (rotated_group, "reality rotates it"),
        "distorted": (distorted_group, "then reality distorts it"),
        "noisy": (noisy_group, "the clean rule starts to wobble"),
        "lighting": (lighting_group, "visibility starts to fail"),
        "pressure": (pressure_group, "exceptions start surrounding it"),
        "wall": (wall_group, ""),
    }

    current, label_text = stage_map.get(stage, (clean, stage))
    if not label_text:
        place_in_zone(current, zone)
        return current

    label = Text(label_text, font_size=24, color=TEXT_SUB)
    label.next_to(current, DOWN, buff=0.48)

    group = VGroup(current, label)
    place_in_zone(group, zone)
    return group


def _boxed_label(label: str, params):
    font_size = params.get("font_size", 32)
    box_width = params.get("box_width", 2.3)
    box_height = params.get("box_height", 1.0)

    txt = Text(label, font_size=font_size, weight=MEDIUM, color=TEXT_MAIN)
    fit_to_width(txt, box_width - 0.45)

    box = RoundedRectangle(
        corner_radius=0.18,
        width=max(box_width, txt.width + 0.6),
        height=max(box_height, txt.height + 0.42),
        stroke_color=params.get("stroke_color", PRIMARY),
        stroke_width=params.get("stroke_width", 3),
        fill_color=params.get("fill_color", "#151922"),
        fill_opacity=params.get("fill_opacity", 1.0),
    )
    halo = RoundedRectangle(
        corner_radius=0.22,
        width=box.width + 0.12,
        height=box.height + 0.12,
        stroke_color=box.get_stroke_color(),
        stroke_width=1.5,
    ).set_opacity(0.18)
    txt.move_to(box.get_center())

    group = VGroup(halo, box, txt)
    group.set_opacity(params.get("opacity", 1.0))
    return group


def make_show_box_label(params, zone):
    group = _boxed_label(params["label"], params)
    place_in_zone(group, zone)
    return group


def make_show_arrow(params, zone):
    direction = params.get("direction", "right")
    length = params.get("length", 2.0)
    start = LEFT * (length / 2)
    end = RIGHT * (length / 2)

    if direction == "left":
        start, end = end, start

    arrow = Arrow(
        start,
        end,
        buff=0.0,
        stroke_width=params.get("stroke_width", 5),
        color=params.get("color", TEXT_SUB),
        max_stroke_width_to_length_ratio=12,
    )
    arrow.set_opacity(params.get("opacity", 1.0))
    place_in_zone(arrow, zone)
    return arrow


def make_examples_grid(params, zone):
    examples = params.get("examples", [])
    rows = params.get("grid_rows", 2)
    cols = params.get("grid_cols", 3)
    cell_width = params.get("cell_width", 1.7)
    cell_height = params.get("cell_height", 0.8)
    font_size = params.get("font_size", 24)

    cells = VGroup()
    for example in examples:
        label = Text(example, font_size=font_size, color=TEXT_MAIN, weight=MEDIUM)
        fit_to_width(label, cell_width - 0.3)
        cell = RoundedRectangle(
            corner_radius=0.12,
            width=max(cell_width, label.width + 0.28),
            height=max(cell_height, label.height + 0.26),
            stroke_color=SECONDARY,
            stroke_width=2.2,
            fill_color="#121925",
            fill_opacity=0.96,
        )
        label.move_to(cell.get_center())
        cells.add(VGroup(cell, label))

    grid = cells.arrange_in_grid(rows=rows, cols=cols, buff=(0.24, 0.24))
    place_in_zone(grid, zone)
    return grid


def make_pattern_object(params, zone):
    label_text = params.get("label", "Pattern")
    font_size = params.get("font_size", 28)

    panel = RoundedRectangle(
        corner_radius=0.2,
        width=2.8,
        height=1.85,
        stroke_color=HIGHLIGHT,
        stroke_width=3,
        fill_color="#121925",
        fill_opacity=0.98,
    )
    axes = VGroup(
        Line(panel.get_corner(DL) + RIGHT * 0.35 + UP * 0.3, panel.get_corner(UL) + RIGHT * 0.35 + DOWN * 0.3, color=TEXT_SUB, stroke_width=2),
        Line(panel.get_corner(DL) + RIGHT * 0.35 + UP * 0.3, panel.get_corner(DR) + LEFT * 0.35 + UP * 0.3, color=TEXT_SUB, stroke_width=2),
    )
    curve = VMobject(color=HIGHLIGHT, stroke_width=4)
    curve.set_points_smoothly(
        [
            panel.get_corner(DL) + RIGHT * 0.55 + UP * 0.45,
            panel.get_center() + LEFT * 0.15 + DOWN * 0.05,
            panel.get_center() + RIGHT * 0.2 + UP * 0.15,
            panel.get_corner(UR) + LEFT * 0.45 + DOWN * 0.45,
        ]
    )
    label = Text(label_text, font_size=font_size, color=TEXT_MAIN, weight=MEDIUM)
    fit_to_width(label, panel.width - 0.45)
    label.next_to(panel, DOWN, buff=0.22)
    group = VGroup(panel, axes, curve, label)
    place_in_zone(group, zone)
    return group


def make_links(params, from_obj, to_obj):
    link_count = max(1, params.get("link_count", 3))
    stroke_width = params.get("stroke_width", 3)
    stroke_opacity = params.get("stroke_opacity", 0.55)

    sources = from_obj.submobjects if len(from_obj.submobjects) >= link_count else [from_obj] * link_count
    lines = VGroup()
    for index in range(link_count):
        source = sources[min(index, len(sources) - 1)]
        source_point = source.get_right() if hasattr(source, "get_right") else from_obj.get_right()
        target_point = to_obj.get_left() + UP * (0.35 - index * 0.35)
        line = Line(source_point, target_point, color=TEXT_SUB, stroke_width=stroke_width)
        line.set_opacity(stroke_opacity)
        lines.add(line)
    return lines


def make_split_comparison(params, zone):
    font_size = params.get("font_size", 24)

    divider = Line(UP * 2.2, DOWN * 2.2, color=TEXT_SUB, stroke_width=2).set_opacity(0.6)

    left_title = Text(params.get("left_title", "Traditional"), font_size=font_size + 2, color=TEXT_MAIN, weight=BOLD)
    left_steps = VGroup(
        *[_boxed_label(label, {"box_width": 1.6, "box_height": 0.72, "font_size": font_size - 2, "stroke_color": PRIMARY}) for label in ("Step 1", "Step 2", "Step 3")]
    ).arrange(DOWN, buff=0.24)
    left_arrows = VGroup(
        *[
            Arrow(
                left_steps[i].get_bottom(),
                left_steps[i + 1].get_top(),
                buff=0.08,
                stroke_width=3,
                color=TEXT_SUB,
            )
            for i in range(2)
        ]
    )
    left_panel = VGroup(left_title, VGroup(left_steps, left_arrows))
    left_title.next_to(left_steps, UP, buff=0.35)
    left_panel.move_to(LEFT * 2.8)

    right_title = Text(params.get("right_title", "Machine Learning"), font_size=font_size + 2, color=TEXT_MAIN, weight=BOLD)
    right_examples = make_examples_grid(
        {
            "examples": ["x1 -> y1", "x2 -> y2", "x3 -> y3", "x4 -> y4"],
            "grid_rows": 2,
            "grid_cols": 2,
            "font_size": font_size - 4,
            "cell_width": 1.45,
            "cell_height": 0.7,
        },
        "center",
    )
    right_pattern = make_pattern_object({"label": "Pattern", "font_size": font_size}, "center")
    right_examples.move_to(RIGHT * 1.8)
    right_pattern.scale(0.78)
    right_pattern.move_to(RIGHT * 3.6)
    right_links = make_links({"link_count": 3, "stroke_width": 2.5, "stroke_opacity": 0.45}, right_examples, right_pattern)
    right_title.move_to(RIGHT * 2.7 + UP * 1.8)
    right_panel = VGroup(right_title, right_examples, right_pattern, right_links)

    full = VGroup(divider, left_panel, right_panel)
    full.left_steps = left_steps
    full.left_arrows = left_arrows
    full.right_panel = right_panel
    place_in_zone(full, zone)
    return full


def make_clean_flow(params, zone):
    left = _boxed_label(params.get("left_label", "Examples"), params)
    right = make_pattern_object({"label": params.get("right_label", "Pattern"), "font_size": params.get("font_size", 30)}, "center")
    right.scale(0.86)
    arrow_length = params.get("arrow_length", 2.1)
    arrow = Arrow(LEFT * (arrow_length / 2), RIGHT * (arrow_length / 2), buff=0.0, stroke_width=4, color=TEXT_SUB)
    arrow_label = Text(params.get("arrow_label", "learns"), font_size=params.get("font_size", 30) - 8, color=ACCENT, weight=MEDIUM)
    arrow_label.next_to(arrow, UP, buff=0.16)

    group = VGroup(left, VGroup(arrow, arrow_label), right).arrange(RIGHT, buff=0.6)
    place_in_zone(group, zone)
    return group


def transition_in_for(obj, transition_name: str):
    if transition_name in {"none", "smooth"}:
        return FadeIn(obj)
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

    if transition_name in {"none", "smooth"}:
        return FadeOut(obj)
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

    if action == "show_box_label":
        return make_show_box_label(params, zone)

    if action == "show_arrow":
        return make_show_arrow(params, zone)

    if action == "transform_box_label":
        return make_show_box_label(params, zone)

    if action == "transform_arrow":
        return make_show_arrow(params, zone)

    if action == "transform_group_to_examples":
        return make_examples_grid(params, zone)

    if action == "transform_box_to_pattern":
        return make_pattern_object(params, zone)

    if action == "show_split_comparison":
        return make_split_comparison(params, zone)

    if action == "transform_split_to_clean_flow":
        return make_clean_flow(params, zone)

    if action == "fade_out":
        return None

    raise ValueError(f"Unsupported action: {action}")
