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
    "center_left_center": LEFT * 1.8,
    "center_span": ORIGIN,
    # FIX: added missing zone used by v18_rules_to_pattern
    "pattern_right_compact": RIGHT * 2.8,
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


def make_math_block(
    math: str,
    font_size: int = 60,
    color=TEXT_MAIN,
    max_width: float = 10.8,
):
    obj = MathTex(math, font_size=font_size, color=color)
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


def make_show_math(params, zone):
    math = make_math_block(
        params["math"],
        font_size=params.get("font_size", 60),
        color=params.get("color", TEXT_MAIN),
        max_width=params.get("max_width", 10.8),
    )
    math.set_opacity(params.get("opacity", 1.0))
    place_in_zone(math, zone)
    return math


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
        buff=0.22,
        stroke_width=4,
        color=TEXT_SUB,
        max_stroke_width_to_length_ratio=10,
    )
    arrow2 = Arrow(
        middle.get_right(),
        right.get_left(),
        buff=0.22,
        stroke_width=4,
        color=TEXT_SUB,
        max_stroke_width_to_length_ratio=10,
    )

    full = VGroup(arrow1, arrow2, row)
    place_in_zone(full, zone)
    return full


def make_show_function_flow(params, zone):
    left = make_math_block(
        params.get("left", "x"),
        font_size=params.get("font_size", 58),
        color=params.get("left_color", TEXT_MAIN),
        max_width=2.2,
    )
    right = make_math_block(
        params.get("right", "y"),
        font_size=params.get("font_size", 58),
        color=params.get("right_color", TEXT_MAIN),
        max_width=2.2,
    )

    middle_math = make_math_block(
        params.get("middle", "f"),
        font_size=params.get("middle_font_size", params.get("font_size", 58) - 4),
        color=params.get("middle_color", ACCENT),
        max_width=1.2,
    )
    middle_box = RoundedRectangle(
        corner_radius=0.18,
        width=max(params.get("middle_box_width", 1.8), middle_math.width + 0.7),
        height=max(params.get("middle_box_height", 1.2), middle_math.height + 0.55),
        stroke_color=params.get("middle_box_color", ACCENT),
        stroke_width=params.get("stroke_width", 3),
        fill_color=params.get("middle_fill_color", "#151922"),
        fill_opacity=params.get("middle_fill_opacity", 1.0),
    )
    middle_glow = RoundedRectangle(
        corner_radius=0.22,
        width=middle_box.width + 0.12,
        height=middle_box.height + 0.12,
        stroke_color=middle_box.get_stroke_color(),
        stroke_width=1.2,
    ).set_opacity(0.2)
    middle_math.move_to(middle_box.get_center())
    middle = VGroup(middle_glow, middle_box, middle_math)

    row = VGroup(left, middle, right).arrange(RIGHT, buff=params.get("node_buff", 1.05))

    arrow1 = Arrow(
        left.get_right(),
        middle.get_left(),
        buff=0.16,
        stroke_width=params.get("arrow_stroke_width", 4),
        color=params.get("arrow_color", TEXT_SUB),
        max_stroke_width_to_length_ratio=10,
    )
    arrow2 = Arrow(
        middle.get_right(),
        right.get_left(),
        buff=0.16,
        stroke_width=params.get("arrow_stroke_width", 4),
        color=params.get("arrow_color", TEXT_SUB),
        max_stroke_width_to_length_ratio=10,
    )

    group = VGroup(row, arrow1, arrow2)
    group.set_opacity(params.get("opacity", 1.0))
    place_in_zone(group, zone)
    return group


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
    """
    Draw link lines from from_obj to to_obj.
    FIX: flatten one level of submobjects so we get actual grid cells
    rather than hitting glow/halo wrapper layers.
    """
    link_count = max(1, params.get("link_count", 3))
    stroke_width = params.get("stroke_width", 3)
    stroke_opacity = params.get("stroke_opacity", 0.55)

    # FIX: flatten one level to get real leaf cells, not wrapper VGroups
    raw_subs = from_obj.submobjects
    flat_subs = []
    for child in raw_subs:
        if hasattr(child, "submobjects") and child.submobjects:
            flat_subs.extend(child.submobjects)
        else:
            flat_subs.append(child)

    subs = flat_subs if len(flat_subs) >= link_count else [from_obj] * link_count
    stride = max(1, len(subs) // link_count)
    sources = [subs[min(i * stride, len(subs) - 1)] for i in range(link_count)]

    to_height = to_obj.height
    spacing = to_height / (link_count + 1)
    lines = VGroup()
    for index in range(link_count):
        source = sources[index]
        source_point = source.get_right() if hasattr(source, "get_right") else from_obj.get_right()
        target_point = to_obj.get_left() + UP * (to_height / 2 - spacing * (index + 1))
        line = Line(source_point, target_point, color=TEXT_SUB, stroke_width=stroke_width)
        line.set_opacity(stroke_opacity)
        lines.add(line)
    return lines


def make_split_comparison(params, zone):
    """
    FIX: Complete rewrite of the layout sequencing.
    Key rules applied:
    1. Position objects BEFORE grouping them (VGroup bounding box freezes at creation).
    2. Never call move_to() on sub-objects after they've been added to a VGroup.
    3. Use arrange() on the parent group, then place_in_zone() once at the end.
    4. Build make_links() AFTER final layout so coordinates are correct.
    5. Add right_title from params (was silently ignored before).
    6. Add right_links to full so it gets cleared with the group.
    """
    font_size = params.get("font_size", 24)

    # --- Left panel ---
    left_steps = VGroup(
        *[
            _boxed_label(
                label,
                {
                    "box_width": 1.6,
                    "box_height": 0.72,
                    "font_size": font_size - 2,
                    "stroke_color": PRIMARY,
                },
            )
            for label in ("Step 1", "Step 2", "Step 3")
        ]
    ).arrange(DOWN, buff=0.24)

    # Build arrows while left_steps positions are still at arrange()'d coordinates
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

    steps_with_arrows = VGroup(left_steps, left_arrows)

    # FIX: position title BEFORE creating the panel VGroup
    left_title = Text(
        params.get("left_title", "Traditional"),
        font_size=font_size + 2,
        color=TEXT_MAIN,
        weight=BOLD,
    )
    left_title.next_to(steps_with_arrows, UP, buff=0.35)

    # Now group — bounding box is correct
    left_panel = VGroup(left_title, steps_with_arrows)

    # --- Right panel ---
    right_examples = make_examples_grid(
        {
            "examples": ["x1 -> y1", "x2 -> y2", "x3 -> y3", "x4 -> y4"],
            "grid_rows": 2,
            "grid_cols": 2,
            "font_size": font_size - 4,
            "cell_width": 1.45,
            "cell_height": 0.7,
        },
        "center",  # place_in_zone snaps to ORIGIN; arrange() below overrides
    )
    right_pattern = make_pattern_object(
        {"label": "Pattern", "font_size": font_size}, "center"
    )
    right_pattern.scale(0.58)

    # FIX: arrange right content WITHOUT any manual move_to()
    right_content = VGroup(right_examples, right_pattern).arrange(RIGHT, buff=0.72)

    # FIX: position right_title BEFORE grouping right_panel
    right_title = Text(
        params.get("right_title", "Machine Learning"),
        font_size=font_size + 2,
        color=TEXT_MAIN,
        weight=BOLD,
    )
    right_title.next_to(right_content, UP, buff=0.35)

    right_panel = VGroup(right_title, right_content)

    # --- Divider (no manual move_to — arrange handles it) ---
    divider = Line(UP * 2.2, DOWN * 2.2, color=TEXT_SUB, stroke_width=2).set_opacity(0.6)

    # --- FIX: arrange the full layout, THEN place once ---
    content = VGroup(left_panel, divider, right_panel).arrange(RIGHT, buff=0.55)
    place_in_zone(content, zone)

    # --- FIX: build links AFTER final layout so coords are correct ---
    right_links = make_links(
        {"link_count": 3, "stroke_width": 2.5, "stroke_opacity": 0.45},
        right_examples,
        right_pattern,
    )

    # Wrap in full so attribute assignments work and links travel with the group
    full = VGroup(content, right_links)
    full.left_steps = left_steps
    full.left_arrows = left_arrows
    full.right_panel = right_panel

    return full


def make_clean_flow(params, zone):
    left = _boxed_label(params.get("left_label", "Examples"), params)
    right = make_pattern_object(
        {
            "label": params.get("right_label", "Pattern"),
            "font_size": params.get("font_size", 30),
        },
        "center",
    )
    right.scale(0.86)
    arrow_length = params.get("arrow_length", 2.1)
    arrow = Arrow(
        LEFT * (arrow_length / 2),
        RIGHT * (arrow_length / 2),
        buff=0.0,
        stroke_width=4,
        color=TEXT_SUB,
    )
    arrow_label = Text(
        params.get("arrow_label", "learns"),
        font_size=params.get("font_size", 30) - 8,
        color=ACCENT,
        weight=MEDIUM,
    )
    arrow_label.next_to(arrow, UP, buff=0.16)

    group = VGroup(left, VGroup(arrow, arrow_label), right).arrange(RIGHT, buff=0.6)
    place_in_zone(group, zone)
    return group


def _training_card(data_label: str, answer_label: str | None, params, known=True):
    font_size = params.get("card_font_size", 21)
    data_text = Text(data_label, font_size=font_size, color=TEXT_MAIN, weight=MEDIUM)
    fit_to_width(data_text, 1.18)

    data_box = RoundedRectangle(
        corner_radius=0.12,
        width=1.38,
        height=0.68,
        stroke_color=SECONDARY,
        stroke_width=2,
        fill_color="#121925",
        fill_opacity=0.98,
    )
    data_text.move_to(data_box.get_center())
    data_part = VGroup(data_box, data_text)

    if answer_label is None:
        group = data_part
    else:
        answer_text = Text(answer_label, font_size=font_size, color=TEXT_MAIN, weight=MEDIUM)
        fit_to_width(answer_text, 1.18)
        answer_box = RoundedRectangle(
            corner_radius=0.12,
            width=1.38,
            height=0.68,
            stroke_color=HIGHLIGHT if known else MUTED,
            stroke_width=2,
            fill_color="#121925",
            fill_opacity=0.98,
        )
        answer_text.move_to(answer_box.get_center())
        answer_part = VGroup(answer_box, answer_text)
        divider = Line(UP * 0.28, DOWN * 0.28, color=TEXT_SUB, stroke_width=2).set_opacity(0.58)
        group = VGroup(data_part, divider, answer_part).arrange(RIGHT, buff=0.16)

    shell = RoundedRectangle(
        corner_radius=0.15,
        width=group.width + 0.3,
        height=group.height + 0.22,
        stroke_color=TEXT_SUB,
        stroke_width=1.2,
        fill_color="#0f1624",
        fill_opacity=0.8,
    ).set_opacity(0.72)
    group.move_to(shell.get_center())
    return VGroup(shell, group)


def _scene4_model_core(params, zone):
    progress = max(0.0, min(1.0, params.get("model_progress", 0.0)))
    phase = params.get("phase", "plastic")
    color = HIGHLIGHT if phase == "plastic" else SECONDARY if phase == "fixed" else ACCENT

    shell = Circle(
        radius=0.76,
        stroke_color=color,
        stroke_width=3.4,
        fill_color="#121926",
        fill_opacity=0.94,
    )
    glow = Circle(radius=0.86, stroke_color=color, stroke_width=9).set_opacity(0.08 + 0.08 * progress)

    rough = [
        LEFT * 0.44 + DOWN * 0.08,
        LEFT * 0.22 + UP * 0.25,
        RIGHT * 0.02 + DOWN * 0.18,
        RIGHT * 0.30 + UP * 0.16,
        RIGHT * 0.48 + DOWN * 0.02,
    ]
    smooth = [
        LEFT * 0.46 + DOWN * 0.22,
        LEFT * 0.25 + DOWN * 0.02,
        ORIGIN + UP * 0.08,
        RIGHT * 0.25 + UP * 0.18,
        RIGHT * 0.49 + UP * 0.30,
    ]
    pattern = VMobject()
    pattern.set_points_smoothly([a * (1 - progress) + b * progress for a, b in zip(rough, smooth)])
    pattern.set_stroke(ACCENT, width=3.2, opacity=0.56 + 0.34 * progress)

    label = Text(params.get("label", "model"), font_size=18, color=TEXT_SUB, weight=MEDIUM)
    label.move_to(UP * 0.48)
    label.set_opacity(params.get("label_opacity", 0.72 if phase == "plastic" else 0.0))

    lock = VGroup(
        Arc(radius=0.15, start_angle=0, angle=PI, color=TEXT_SUB, stroke_width=2.2),
        RoundedRectangle(
            corner_radius=0.03,
            width=0.38,
            height=0.24,
            stroke_color=TEXT_SUB,
            stroke_width=2,
            fill_color="#121926",
            fill_opacity=1.0,
        ).shift(DOWN * 0.17),
    ).move_to(DOWN * 0.38)
    lock.set_opacity(0.78 if phase == "fixed" else 0.0)

    fixed = Text("Fixed model", font_size=20, color=TEXT_SUB, weight=MEDIUM)
    fixed.next_to(shell, DOWN, buff=0.22)
    fixed.set_opacity(0.82 if phase == "fixed" and params.get("show_fixed_label", True) else 0.0)

    core = VGroup(glow, shell, pattern, label, lock, fixed)
    place_in_zone(core, zone)
    return core


def make_show_model_core(params, zone):
    return _scene4_model_core(params, zone)


def make_show_phase_labels(params, zone):
    title = Text(params.get("title", "Two lives of one system"), font_size=30, color=TEXT_MAIN, weight=MEDIUM)
    title.move_to(UP * 2.55)
    training = Text("Training", font_size=23, color=HIGHLIGHT, weight=MEDIUM).move_to(LEFT * 2.7 + UP * 2.0)
    inference = Text("Inference", font_size=23, color=SECONDARY, weight=MEDIUM).move_to(RIGHT * 2.7 + UP * 2.0)
    if params.get("active") == "training":
        inference.set_opacity(0.22)
    elif params.get("active") == "inference":
        training.set_opacity(0.22)
    if not params.get("show_title", True):
        title.set_opacity(0.0)
    group = VGroup(title, training, inference)
    group.set_opacity(params.get("opacity", 1.0))
    place_in_zone(group, zone)
    return group


def make_show_training_examples(params, zone):
    count = max(1, min(3, int(params.get("count", 3))))
    labels = params.get("examples", ["x1 -> y1", "x2 -> y2", "x3 -> y3"])
    rows = VGroup()
    for index in range(count):
        dot = Dot(ORIGIN, radius=0.055, color=HIGHLIGHT)
        text = Text(labels[index], font_size=17, color=TEXT_SUB, weight=MEDIUM)
        text.next_to(dot, RIGHT, buff=0.12)
        rows.add(VGroup(dot, text))
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.26)
    known = Text("Known answers", font_size=18, color=TEXT_SUB, weight=MEDIUM)
    known.next_to(rows, DOWN, buff=0.28)
    arrow = Arrow(
        rows.get_right() + RIGHT * 0.18,
        RIGHT * 1.65,
        buff=0.0,
        color=HIGHLIGHT,
        stroke_width=3.0,
        max_tip_length_to_length_ratio=0.08,
    )
    group = VGroup(rows, known, arrow)
    group.move_to(LEFT * 2.18 + DOWN * 0.05)
    group.set_opacity(params.get("opacity", 1.0))
    place_in_zone(group, zone)
    return group


def make_show_prediction_error(params, zone):
    pred = Dot(LEFT * 0.1 + UP * 0.34, radius=0.065, color=PRIMARY)
    pred_label = Text("Prediction", font_size=18, color=TEXT_SUB, weight=MEDIUM).next_to(pred, UP, buff=0.12)
    true = Dot(LEFT * 0.1 + DOWN * params.get("gap", 0.34), radius=0.065, color=ACCENT)
    true_label = Text("true", font_size=15, color=TEXT_SUB).next_to(true, DOWN, buff=0.08)
    arrow = Arrow(
        LEFT * 2.05 + UP * 0.08,
        pred.get_left() + LEFT * 0.12,
        buff=0.0,
        color=PRIMARY,
        stroke_width=3,
        max_tip_length_to_length_ratio=0.08,
    )
    gap = Line(pred.get_center(), true.get_center(), color=WARNING, stroke_width=3.4)
    error = Text("Error", font_size=18, color=WARNING, weight=MEDIUM).next_to(gap, RIGHT, buff=0.12)
    group = VGroup(arrow, pred, pred_label, true, true_label, gap, error)
    group.move_to(RIGHT * 2.12 + DOWN * 0.04)
    group.set_opacity(params.get("opacity", 1.0))
    place_in_zone(group, zone)
    return group


def make_show_adjustment_loop(params, zone):
    start = RIGHT * 2.5 + DOWN * 0.28
    end = RIGHT * 0.52 + DOWN * 0.58
    arc = ArcBetweenPoints(start, end, angle=-PI / 2.8, color=WARNING, stroke_width=3)
    tip = Triangle(color=WARNING, fill_color=WARNING, fill_opacity=1.0).scale(0.08)
    tip.rotate(-PI / 3.5)
    tip.move_to(end)
    label = Text("Adjust", font_size=18, color=WARNING, weight=MEDIUM).move_to(RIGHT * 1.52 + DOWN * 1.0)
    group = VGroup(arc, tip, label)
    group.set_opacity(params.get("opacity", 1.0))
    place_in_zone(group, zone)
    return group


def make_show_repeat_learning(params, zone):
    progress = max(0.0, min(1.0, params.get("model_progress", 0.65)))
    example = Dot(LEFT * 2.6 + UP * 0.25, radius=0.055, color=HIGHLIGHT)
    pred = Dot(RIGHT * 2.15 + UP * (0.42 - 0.16 * progress), radius=0.055, color=PRIMARY)
    true = Dot(RIGHT * 2.15 + DOWN * (0.18 - 0.08 * progress), radius=0.055, color=ACCENT)
    in_arrow = Arrow(LEFT * 2.35 + UP * 0.2, LEFT * 0.85 + UP * 0.06, buff=0, color=HIGHLIGHT, stroke_width=2.7)
    out_arrow = Arrow(RIGHT * 0.85 + UP * 0.03, RIGHT * 1.95 + UP * (0.36 - 0.12 * progress), buff=0, color=PRIMARY, stroke_width=2.7)
    gap = Line(pred.get_center(), true.get_center(), color=WARNING, stroke_width=2.8).set_opacity(0.78 - 0.28 * progress)
    label = Text("again and again", font_size=18, color=TEXT_SUB, weight=MEDIUM).move_to(DOWN * 1.18)
    group = VGroup(example, in_arrow, out_arrow, pred, true, gap, label)
    group.set_opacity(params.get("opacity", 1.0))
    place_in_zone(group, zone)
    return group


def make_show_inference_pass(params, zone):
    new_data = Dot(LEFT * 0.0 + UP * 0.35, radius=0.07, color=SECONDARY)
    new_label = Text("New data", font_size=18, color=TEXT_SUB, weight=MEDIUM).next_to(new_data, UP, buff=0.12)
    pred = Dot(RIGHT * 1.95 + DOWN * 0.32, radius=0.065, color=PRIMARY)
    pred_label = Text("Prediction", font_size=18, color=TEXT_SUB, weight=MEDIUM).next_to(pred, DOWN, buff=0.12)
    in_arrow = Arrow(LEFT * 0.02 + UP * 0.26, LEFT * 1.62 + UP * 0.08, buff=0, color=SECONDARY, stroke_width=3)
    out_arrow = Arrow(LEFT * 1.72 + DOWN * 0.05, pred.get_left() + LEFT * 0.1, buff=0, color=PRIMARY, stroke_width=3)
    group = VGroup(new_data, new_label, in_arrow, out_arrow, pred, pred_label)
    group.move_to(RIGHT * 2.15)
    group.set_opacity(params.get("opacity", 1.0))
    place_in_zone(group, zone)
    return group


def make_show_build_use_summary(params, zone):
    build = Text("Training = build", font_size=23, color=HIGHLIGHT, weight=MEDIUM).move_to(LEFT * 2.2 + DOWN * 1.6)
    use = Text("Inference = use", font_size=23, color=SECONDARY, weight=MEDIUM).move_to(RIGHT * 2.2 + DOWN * 1.6)
    group = VGroup(build, use)
    group.set_opacity(params.get("opacity", 1.0))
    place_in_zone(group, zone)
    return group


def make_show_generalization_pattern(params, zone):
    show_text = params.get("show_text", False)
    points = VGroup(
        Dot(LEFT * 1.9 + DOWN * 0.95, radius=0.045, color=SECONDARY),
        Dot(LEFT * 0.95 + DOWN * 0.28, radius=0.045, color=SECONDARY),
        Dot(RIGHT * 0.15 + UP * 0.08, radius=0.045, color=SECONDARY),
        Dot(RIGHT * 1.1 + UP * 0.34, radius=0.045, color=SECONDARY),
        Dot(RIGHT * 1.9 + UP * 0.98, radius=0.06, color=ACCENT),
    )
    points.set_opacity(0.34 if not show_text else 0.72)
    curve = VMobject()
    curve.set_points_smoothly([p.get_center() for p in points])
    curve.set_stroke(ACCENT, width=4.0, opacity=0.88)
    glow = curve.copy().set_stroke(ACCENT, width=12, opacity=0.10)
    arrow = Arrow(RIGHT * 2.15 + UP * 0.95, RIGHT * 2.72 + UP * 0.95, buff=0.0, color=PRIMARY, stroke_width=3)
    prediction = Dot(RIGHT * 2.9 + UP * 0.95, radius=0.06, color=PRIMARY)
    title = Text("Generalization", font_size=32, color=TEXT_MAIN, weight=BOLD)
    subtitle = Text("works on new examples", font_size=22, color=TEXT_SUB, weight=MEDIUM)
    text = VGroup(title, subtitle).arrange(DOWN, buff=0.12).move_to(DOWN * 2.35)
    text.set_opacity(1.0 if show_text else 0.0)
    group = VGroup(glow, curve, points, arrow, prediction, text)
    group.set_opacity(params.get("opacity", 1.0))
    place_in_zone(group, zone)
    return group


def make_training_loop(params, zone):
    phase = params.get("phase", "intro")
    training_phases = {"training_examples", "training_error", "adjust", "repeat"}
    inference_phases = {"fixed", "inference", "build_use", "generalization", "generalization_final"}
    model_progress = max(0.0, min(1.0, params.get("model_progress", 0.0)))
    loop_index = int(params.get("loop_index", 0))

    def phase_opacity(names, value=1.0):
        return value if phase in names else 0.0

    def soften(group, opacity=0.16):
        group.set_opacity(opacity)
        return group

    title = Text("Two lives of one system", font_size=30, color=TEXT_MAIN, weight=MEDIUM)
    title.move_to(UP * 2.55)
    title.set_opacity(0.92 if phase == "intro" else 0.0)

    training_label = Text("Training", font_size=23, color=HIGHLIGHT, weight=MEDIUM)
    inference_label = Text("Inference", font_size=23, color=SECONDARY, weight=MEDIUM)
    training_label.move_to(LEFT * 2.7 + UP * 2.0)
    inference_label.move_to(RIGHT * 2.7 + UP * 2.0)
    label_opacity = 0.84 if phase in {"split", "inference_hint", *training_phases, *inference_phases} else 0.0
    mode_labels = VGroup(training_label, inference_label).set_opacity(label_opacity)
    if phase in training_phases:
        inference_label.set_opacity(0.20)
    if phase == "inference_hint":
        training_label.set_opacity(0.20)
    if phase in {"fixed", "inference"}:
        training_label.set_opacity(0.20)

    core_radius = 0.72
    core_color = HIGHLIGHT if phase in training_phases else SECONDARY if phase in {"fixed", "inference"} else ACCENT
    core_fill = "#121926" if phase not in {"generalization", "generalization_final"} else "#101d20"
    shell = Circle(radius=core_radius, stroke_color=core_color, stroke_width=3.2, fill_color=core_fill, fill_opacity=0.94)
    glow = Circle(radius=core_radius + 0.08, stroke_color=core_color, stroke_width=8)
    glow.set_opacity(0.08 + 0.10 * model_progress)
    lock_line = Line(LEFT * 0.22, RIGHT * 0.22, color=TEXT_SUB, stroke_width=2.3).move_to(DOWN * 0.3)
    lock_line.set_opacity(0.0 if phase not in {"fixed", "inference", "build_use"} else 0.75)

    rough_points = [
        LEFT * 0.42 + DOWN * 0.06,
        LEFT * 0.20 + UP * 0.25,
        RIGHT * 0.05 + DOWN * 0.18,
        RIGHT * 0.32 + UP * 0.18,
        RIGHT * 0.48 + DOWN * 0.02,
    ]
    smooth_points = [
        LEFT * 0.45 + DOWN * 0.20,
        LEFT * 0.25 + DOWN * 0.02,
        ORIGIN + UP * 0.08,
        RIGHT * 0.25 + UP * 0.17,
        RIGHT * 0.47 + UP * 0.28,
    ]
    pattern_points = [
        rough * (1 - model_progress) + smooth * model_progress
        for rough, smooth in zip(rough_points, smooth_points)
    ]
    internal_pattern = VMobject()
    internal_pattern.set_points_smoothly(pattern_points)
    internal_pattern.set_stroke(ACCENT, width=3.0, opacity=0.58 + 0.32 * model_progress)
    model_word = Text("model", font_size=18, color=TEXT_SUB, weight=MEDIUM).move_to(UP * 0.46)
    model_word.set_opacity(0.72 if phase in {"intro", "split"} else 0.0)
    fixed_label = Text("Fixed model", font_size=20, color=TEXT_SUB, weight=MEDIUM)
    fixed_label.next_to(shell, DOWN, buff=0.2)
    fixed_label.set_opacity(0.82 if phase in {"fixed", "inference"} else 0.0)
    model_core = VGroup(glow, shell, internal_pattern, lock_line, model_word, fixed_label)

    example_offsets = [UP * 0.42, ORIGIN, DOWN * 0.42]
    example_labels = ["x1,y1", "x2,y2", "x3,y3"]
    examples = VGroup()
    for index, (offset, label) in enumerate(zip(example_offsets, example_labels)):
        dot = Dot(LEFT * 3.1 + offset, radius=0.055, color=HIGHLIGHT)
        text = Text(label, font_size=15, color=TEXT_SUB)
        text.next_to(dot, RIGHT, buff=0.12)
        item = VGroup(dot, text)
        item.set_opacity(1.0 if index <= loop_index else 0.22)
        examples.add(item)
    known = Text("Known answers", font_size=18, color=TEXT_SUB, weight=MEDIUM)
    known.next_to(examples, DOWN, buff=0.25)
    into_model = Arrow(
        LEFT * 2.05,
        LEFT * 0.83,
        buff=0.0,
        color=HIGHLIGHT,
        stroke_width=3,
        max_tip_length_to_length_ratio=0.08,
    )
    prediction_dot = Dot(RIGHT * 1.95 + UP * 0.24, radius=0.065, color=PRIMARY)
    prediction_text = Text("Prediction", font_size=18, color=TEXT_SUB, weight=MEDIUM)
    prediction_text.next_to(prediction_dot, UP, buff=0.12)
    out_arrow = Arrow(
        RIGHT * 0.82,
        RIGHT * 1.75 + UP * 0.18,
        buff=0.0,
        color=PRIMARY,
        stroke_width=3,
        max_tip_length_to_length_ratio=0.08,
    )
    training_flow = VGroup(examples, known, into_model, out_arrow, prediction_dot, prediction_text)
    training_flow.set_opacity(phase_opacity(training_phases))
    if phase in {"fixed", "inference", "build_use", "generalization", "generalization_final"}:
        soften(training_flow, 0.12)

    true_dot = Dot(RIGHT * 1.95 + DOWN * (0.25 - 0.13 * model_progress), radius=0.065, color=ACCENT)
    true_text = Text("true", font_size=15, color=TEXT_SUB).next_to(true_dot, DOWN, buff=0.1)
    error_line = Line(prediction_dot.get_center(), true_dot.get_center(), color=WARNING, stroke_width=3.4)
    error_text = Text("Error", font_size=18, color=WARNING, weight=MEDIUM)
    error_text.next_to(error_line, RIGHT, buff=0.12)
    adjust_arc = ArcBetweenPoints(
        RIGHT * 1.75 + DOWN * 0.28,
        RIGHT * 0.5 + DOWN * 0.58,
        angle=-PI / 2.8,
        color=WARNING,
        stroke_width=2.8,
    )
    adjust_tip = Triangle(color=WARNING, fill_color=WARNING, fill_opacity=1.0).scale(0.08)
    adjust_tip.rotate(-PI / 3.5)
    adjust_tip.move_to(RIGHT * 0.52 + DOWN * 0.58)
    adjust_text = Text("Adjust", font_size=18, color=WARNING, weight=MEDIUM)
    adjust_text.move_to(RIGHT * 1.35 + DOWN * 1.03)
    feedback_loop = VGroup(true_dot, true_text, error_line, error_text, adjust_arc, adjust_tip, adjust_text)
    if phase == "training_error":
        VGroup(adjust_arc, adjust_tip, adjust_text).set_opacity(0.0)
        feedback_loop.set_opacity(1.0)
    elif phase in {"adjust", "repeat"}:
        feedback_loop.set_opacity(1.0)
    else:
        feedback_loop.set_opacity(0.0)

    new_data = Dot(RIGHT * 3.18 + UP * 0.25, radius=0.07, color=SECONDARY)
    new_data_text = Text("New data", font_size=18, color=TEXT_SUB, weight=MEDIUM)
    new_data_text.next_to(new_data, UP, buff=0.12)
    infer_in = Arrow(
        RIGHT * 2.75 + UP * 0.18,
        RIGHT * 0.84 + UP * 0.06,
        buff=0.0,
        color=SECONDARY,
        stroke_width=3,
        max_tip_length_to_length_ratio=0.08,
    )
    infer_out = Arrow(
        RIGHT * 0.83 + DOWN * 0.08,
        RIGHT * 2.5 + DOWN * 0.35,
        buff=0.0,
        color=PRIMARY,
        stroke_width=3,
        max_tip_length_to_length_ratio=0.08,
    )
    infer_pred = Dot(RIGHT * 2.72 + DOWN * 0.38, radius=0.065, color=PRIMARY)
    infer_pred_text = Text("Prediction", font_size=18, color=TEXT_SUB, weight=MEDIUM)
    infer_pred_text.next_to(infer_pred, DOWN, buff=0.12)
    inference_flow = VGroup(new_data, new_data_text, infer_in, infer_out, infer_pred, infer_pred_text)
    if phase in {"inference", "generalization_final"}:
        inference_flow.set_opacity(1.0)
    elif phase == "inference_hint":
        inference_flow.set_opacity(0.32)
    else:
        inference_flow.set_opacity(0.0)

    build_text = Text("build the model", font_size=22, color=HIGHLIGHT, weight=MEDIUM)
    use_text = Text("use the model", font_size=22, color=SECONDARY, weight=MEDIUM)
    build_text.move_to(LEFT * 2.5 + DOWN * 1.75)
    use_text.move_to(RIGHT * 2.5 + DOWN * 1.75)
    build_use = VGroup(build_text, use_text)
    build_use.set_opacity(0.92 if phase == "build_use" else 0.0)

    pattern_points_outer = [
        LEFT * 1.9 + DOWN * 1.0,
        LEFT * 1.0 + DOWN * 0.32,
        ORIGIN + DOWN * 0.03,
        RIGHT * 1.1 + UP * 0.30,
        RIGHT * 2.0 + UP * 0.98,
    ]
    learned_pattern = VMobject()
    learned_pattern.set_points_smoothly(pattern_points_outer)
    learned_pattern.set_stroke(ACCENT, width=4.0, opacity=0.0)
    pattern_glow = learned_pattern.copy().set_stroke(ACCENT, width=12, opacity=0.0)
    if phase in {"generalization", "generalization_final"}:
        pattern_glow.set_stroke(ACCENT, width=12, opacity=0.10)
        learned_pattern.set_stroke(ACCENT, width=4.0, opacity=0.82)
    pattern_group = VGroup(pattern_glow, learned_pattern)

    final_title = Text("Generalization", font_size=32, color=TEXT_MAIN, weight=BOLD)
    final_subtitle = Text("works on new examples", font_size=22, color=TEXT_SUB, weight=MEDIUM)
    final_text = VGroup(final_title, final_subtitle).arrange(DOWN, buff=0.12)
    final_text.move_to(DOWN * 2.38)
    final_text.set_opacity(1.0 if phase == "generalization_final" else 0.0)

    full = VGroup(
        title,
        mode_labels,
        model_core,
        training_flow,
        feedback_loop,
        inference_flow,
        build_use,
        pattern_group,
        final_text,
    )
    place_in_zone(full, zone)
    full.set_opacity(params.get("opacity", 1.0))
    return full


def make_show_plot(params, zone):
    x_range = params.get("x_range", [0, 10, 2])
    y_range = params.get("y_range", [0, 10, 2])
    x_length = params.get("x_length", 7.2)
    y_length = params.get("y_length", 4.2)

    axes = Axes(
        x_range=x_range,
        y_range=y_range,
        x_length=x_length,
        y_length=y_length,
        tips=False,
        axis_config={
            "color": params.get("axis_color", TEXT_SUB),
            "stroke_width": params.get("axis_stroke_width", 3),
            "include_numbers": False,
            "include_ticks": params.get("show_ticks", False),
        },
    )

    title_group = VGroup()
    plot_title = params.get("plot_title")
    if plot_title:
        title = make_text_block(
            plot_title,
            font_size=params.get("plot_title_font_size", 32),
            color=params.get("plot_title_color", TEXT_MAIN),
            weight=params.get("plot_title_weight", BOLD),
            max_width=x_length * 1.05,
        )
        title.next_to(axes, UP, buff=params.get("plot_title_buff", 0.34))
        title_group.add(title)
        plot_subtitle = params.get("plot_subtitle")
        if plot_subtitle:
            subtitle = make_text_block(
                plot_subtitle,
                font_size=params.get("plot_subtitle_font_size", 22),
                color=params.get("plot_subtitle_color", TEXT_SUB),
                weight=MEDIUM,
                max_width=x_length * 1.05,
            )
            subtitle.next_to(title, DOWN, buff=0.13)
            title_group.add(subtitle)

    x_label_group = VGroup()
    y_label_group = VGroup()
    if params.get("show_axis_labels", True):
        x_label = Text(
            params.get("x_label", "x"),
            font_size=params.get("label_font_size", 24),
            color=params.get("label_color", TEXT_MAIN),
            weight=MEDIUM,
        )
        fit_to_width(x_label, x_length * 0.42)
        x_label.next_to(axes.x_axis, DOWN, buff=0.35)
        x_label_group.add(x_label)

        y_label = Text(
            params.get("y_label", "y"),
            font_size=params.get("label_font_size", 24),
            color=params.get("label_color", TEXT_MAIN),
            weight=MEDIUM,
        )
        fit_to_width(y_label, y_length * 0.7)
        y_label.rotate(PI / 2)
        y_label.next_to(axes.y_axis, LEFT, buff=0.4)
        y_label_group.add(y_label)

    points = params.get("points", [])
    point_group = VGroup(
        *[
            Dot(
                axes.c2p(*point),
                radius=params.get("point_radius", 0.07),
                color=params.get("point_color", SECONDARY),
            )
            for point in points
        ]
    )
    point_group.set_opacity(params.get("point_opacity", 1.0))

    fit_line_group = VGroup()
    fit_line_data = params.get("fit_line")
    if fit_line_data:
        fit_line = Line(
            axes.c2p(*fit_line_data["start"]),
            axes.c2p(*fit_line_data["end"]),
            color=fit_line_data.get("color", HIGHLIGHT),
            stroke_width=fit_line_data.get("stroke_width", 4),
        )
        fit_line.set_opacity(fit_line_data.get("opacity", 1.0))
        if fit_line_data.get("glow", True):
            fit_glow = fit_line.copy().set_stroke(
                width=fit_line_data.get("glow_width", 8),
                opacity=fit_line_data.get("glow_opacity", 0.14),
            )
            fit_line_group.add(fit_glow)
        fit_line_group.add(fit_line)

    residual_group = VGroup()
    residual_style = params.get("residual_style", {})
    residual_indices = params.get("residual_indices", [])
    if fit_line_data and residual_indices:
        x1, y1 = fit_line_data["start"]
        x2, y2 = fit_line_data["end"]
        slope = 0 if x2 == x1 else (y2 - y1) / (x2 - x1)
        for index in residual_indices:
            if not 0 <= index < len(points):
                continue
            px, py = points[index]
            predicted_y = y1 + slope * (px - x1)
            start_point = axes.c2p(px, py)
            end_point = axes.c2p(px, predicted_y)
            residual = DashedLine(
                start_point,
                end_point,
                dash_length=residual_style.get("dash_length", 0.08),
                color=residual_style.get("color", ACCENT),
                stroke_width=residual_style.get("stroke_width", 2.4),
            )
            residual.set_opacity(residual_style.get("opacity", 0.7))
            residual_group.add(residual)

    guide_group = VGroup()
    for guide in params.get("prediction_guides", []):
        actual = guide.get("actual")
        predicted_y = guide.get("predicted_y")
        if actual is None or predicted_y is None:
            continue
        px, py = actual
        predicted_point = axes.c2p(px, predicted_y)
        actual_point = axes.c2p(px, py)
        guide_line = DashedLine(
            predicted_point,
            actual_point,
            dash_length=guide.get("dash_length", 0.08),
            color=guide.get("color", ACCENT),
            stroke_width=guide.get("stroke_width", 2.2),
        )
        guide_line.set_opacity(guide.get("opacity", 0.62))
        predicted_dot = Dot(
            predicted_point,
            radius=guide.get("dot_radius", 0.06),
            color=guide.get("dot_color", HIGHLIGHT),
        )
        predicted_dot.set_opacity(guide.get("dot_opacity", 0.95))
        guide_group.add(guide_line, predicted_dot)
        if guide.get("show_actual_dot", False):
            actual_dot = Dot(
                actual_point,
                radius=guide.get("actual_dot_radius", guide.get("dot_radius", 0.06)),
                color=guide.get("actual_dot_color", guide.get("color", ACCENT)),
            )
            actual_dot.set_opacity(guide.get("actual_dot_opacity", 0.72))
            guide_group.add(actual_dot)

    parameter_group = VGroup()
    for label_data in params.get("parameter_labels", []):
        label = make_math_block(
            label_data["text"],
            font_size=label_data.get("font_size", 34),
            color=label_data.get("color", ACCENT),
            max_width=1.2,
        )
        label.move_to(axes.c2p(*label_data["point"]))
        label.set_opacity(label_data.get("opacity", 0.95))
        parameter_group.add(label)

    equation_group = VGroup()
    equation_text = params.get("equation")
    if equation_text:
        equation = make_math_block(
            equation_text,
            font_size=params.get("equation_font_size", 32),
            color=params.get("equation_color", TEXT_MAIN),
            max_width=x_length * 0.7,
        )
        equation.set_opacity(params.get("equation_opacity", 0.68))
        equation.next_to(axes, UP, buff=0.38)
        equation_group.add(equation)

    caption_group = VGroup()
    caption_text = params.get("caption")
    if caption_text:
        caption = make_text_block(
            caption_text,
            font_size=params.get("caption_font_size", 24),
            color=params.get("caption_color", TEXT_SUB),
            weight=params.get("caption_weight", MEDIUM),
            max_width=x_length * 1.05,
        )
        caption.set_opacity(params.get("caption_opacity", 0.92))
        caption.next_to(axes, DOWN, buff=0.42)
        caption_group.add(caption)

    plot = VGroup(
        axes,
        x_label_group,
        y_label_group,
        point_group,
        fit_line_group,
        residual_group,
        guide_group,
        parameter_group,
        equation_group,
        caption_group,
        title_group,
    )
    plot.set_opacity(params.get("opacity", 1.0))
    plot.shift(ZONE_POSITIONS.get(zone, ORIGIN) - axes.get_center())
    return plot


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

    if action == "show_math":
        return make_show_math(params, zone)

    if action == "highlight_text":
        return make_highlight_text(params, zone)

    if action == "show_flow_diagram":
        return make_flow_diagram(params, zone)

    if action == "show_function_flow":
        return make_show_function_flow(params, zone)

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

    if action == "show_plot":
        return make_show_plot(params, zone)

    if action == "show_training_loop":
        return make_training_loop(params, zone)

    if action == "show_model_core":
        return make_show_model_core(params, zone)

    if action == "show_phase_labels":
        return make_show_phase_labels(params, zone)

    if action == "show_training_examples":
        return make_show_training_examples(params, zone)

    if action == "show_prediction_error":
        return make_show_prediction_error(params, zone)

    if action == "show_adjustment_loop":
        return make_show_adjustment_loop(params, zone)

    if action == "show_repeat_learning":
        return make_show_repeat_learning(params, zone)

    if action == "show_inference_pass":
        return make_show_inference_pass(params, zone)

    if action == "show_build_use_summary":
        return make_show_build_use_summary(params, zone)

    if action == "show_generalization_pattern":
        return make_show_generalization_pattern(params, zone)

    if action == "fade_out":
        return None

    raise ValueError(f"Unsupported action: {action}")
