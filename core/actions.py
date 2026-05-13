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
    "left-center": LEFT * 2.25,
    "center_band": ORIGIN,
    "center_left_center": LEFT * 1.8,
    "center_span": ORIGIN,
    # FIX: added missing zone used by v18_rules_to_pattern
    "pattern_right_compact": RIGHT * 2.8,
}


def _as_vector(value, default=ORIGIN):
    if value is None:
        return default
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        z = value[2] if len(value) > 2 else 0
        return np.array([value[0], value[1], z], dtype=float)
    return default


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


def _manual_rule_card_points(state: int, width: float, height: float):
    half_w = width / 2
    half_h = height / 2
    states = {
        0: [
            [-half_w, half_h, 0],
            [half_w, half_h, 0],
            [half_w, -half_h, 0],
            [-half_w, -half_h, 0],
        ],
        1: [
            [-half_w * 1.15, half_h * 0.98, 0],
            [half_w, half_h, 0],
            [half_w, -half_h, 0],
            [-half_w * 1.15, -half_h * 1.02, 0],
        ],
        2: [
            [-half_w * 1.15, half_h * 0.98, 0],
            [half_w * 0.98, half_h * 1.12, 0],
            [half_w, -half_h, 0],
            [-half_w * 1.15, -half_h * 1.02, 0],
        ],
        3: [
            [-half_w * 1.15, half_h * 0.98, 0],
            [half_w * 0.98, half_h * 1.12, 0],
            [half_w * 0.98, -half_h * 0.82, 0],
            [-half_w * 1.10, -half_h * 0.86, 0],
        ],
        4: [
            [-half_w * 1.12, half_h * 0.92, 0],
            [half_w * 0.95, half_h * 1.10, 0],
            [half_w * 1.08, -half_h * 0.78, 0],
            [-half_w * 0.92, -half_h * 0.96, 0],
        ],
    }
    return [np.array(point, dtype=float) for point in states.get(state, states[0])]


def make_manual_rule_card(params, zone):
    state = int(params.get("state", 0))
    width = params.get("width", 3.25)
    height = params.get("height", 1.22)
    color = params.get("color", TEXT_MAIN)
    fill_color = params.get("fill_color", "#111827")
    stroke_width = params.get("stroke_width", 3.0)
    fill_opacity = params.get("fill_opacity", 0.12)
    opacity = params.get("opacity", 1.0)

    card = Polygon(
        *_manual_rule_card_points(state, width, height),
        color=color,
        stroke_width=stroke_width,
    )
    card.set_fill(fill_color, opacity=fill_opacity)

    label = Text(
        params.get("label", 'IF "Winner" → SPAM'),
        font_size=params.get("font_size", 24),
        color=params.get("text_color", color),
        weight=params.get("weight", MEDIUM),
    )
    fit_to_width(label, width * 0.78)
    label.move_to(card.get_center())

    group = VGroup(card, label)
    group.set_opacity(opacity)
    group.scale(params.get("scale", 1.0))

    position = _as_vector(params.get("position"), ZONE_POSITIONS.get(zone, ORIGIN))
    group.move_to(position)
    group.manual_anchor = position
    group.current_scale = params.get("scale", 1.0)
    return group


def make_manual_rule_force_indicator(params, card_obj):
    direction = params.get("force_indicator")
    challenge_label = params.get("challenge_label")
    if not direction and not challenge_label:
        return None

    color = params.get("force_color", ACCENT)
    opacity = params.get("force_opacity", 0.72)

    if challenge_label:
        chip_color = params.get("challenge_color", color)
        chip_fill = params.get("challenge_fill_color", "#172033")
        chip_text = params.get("challenge_text_color", TEXT_MAIN)
        chip_width = params.get("challenge_width", 1.18)
        chip_height = params.get("challenge_height", 0.42)
        chip = RoundedRectangle(
            width=chip_width,
            height=chip_height,
            corner_radius=0.10,
            color=chip_color,
            stroke_width=params.get("challenge_stroke_width", 1.8),
        )
        chip.set_fill(chip_fill, opacity=params.get("challenge_fill_opacity", 0.82))
        label = Text(
            challenge_label,
            font_size=params.get("challenge_font_size", 16),
            color=chip_text,
            weight=params.get("challenge_weight", MEDIUM),
        )
        fit_to_width(label, chip_width * 0.78)
        label.move_to(chip.get_center())
        indicator = VGroup(chip, label)

        buff = params.get("challenge_buff", 0.22)
        if direction == "left":
            indicator.next_to(card_obj, LEFT, buff=buff)
        elif direction == "top_right":
            indicator.next_to(card_obj.get_corner(UR), normalize(UP + RIGHT), buff=buff)
        elif direction == "bottom":
            indicator.next_to(card_obj, DOWN, buff=buff)
        else:
            indicator.move_to(card_obj.get_center())
        indicator.set_opacity(opacity)
        return indicator

    stroke_width = params.get("force_stroke_width", 2.2)
    length = params.get("force_length", 0.62)
    buff = params.get("force_buff", 0.08)

    if direction == "left":
        end = card_obj.get_left() + LEFT * buff
        start = end + LEFT * length
    elif direction == "top_right":
        end = card_obj.get_corner(UR) + normalize(UP + RIGHT) * buff
        start = end + normalize(UP + RIGHT) * length
    elif direction == "bottom":
        end = card_obj.get_bottom() + DOWN * buff
        start = end + DOWN * length
    else:
        return None

    line = Line(start, end, color=color, stroke_width=stroke_width)
    line.set_opacity(opacity)
    return line


def make_manual_rule_ghosts(params, zone):
    labels = params.get("labels", ["Pedestrian", "Tumor", "Recommendation"])
    positions = params.get(
        "positions",
        [[-3.65, -1.05, 0], [0, -2.35, 0], [3.65, -1.05, 0]],
    )
    scale = params.get("scale", 0.4)
    opacity = params.get("opacity", 0.3)
    color = params.get("color", MUTED)

    ghosts = VGroup()
    ghost_items = {}
    for label_text, position in zip(labels, positions):
        key = label_text.lower()
        icon_color = params.get("icon_color", color)
        label_color = params.get("text_color", color)

        if key == "pedestrian":
            head = Circle(radius=0.10, color=icon_color, stroke_width=2.0)
            body = Line(UP * 0.02, DOWN * 0.32, color=icon_color, stroke_width=2.0)
            arm = Line(LEFT * 0.18 + DOWN * 0.10, RIGHT * 0.18 + DOWN * 0.10, color=icon_color, stroke_width=2.0)
            leg_l = Line(DOWN * 0.32, LEFT * 0.18 + DOWN * 0.60, color=icon_color, stroke_width=2.0)
            leg_r = Line(DOWN * 0.32, RIGHT * 0.18 + DOWN * 0.60, color=icon_color, stroke_width=2.0)
            road = Line(LEFT * 0.58 + DOWN * 0.72, RIGHT * 0.58 + DOWN * 0.72, color=icon_color, stroke_width=1.4)
            icon = VGroup(head, body, arm, leg_l, leg_r, road)
            head.shift(UP * 0.22)
        elif key == "tumor":
            scan = Circle(radius=0.42, color=icon_color, stroke_width=2.0)
            scan.set_fill("#111827", opacity=params.get("icon_fill_opacity", 0.10))
            tumor = Dot(point=RIGHT * 0.12 + UP * 0.06, radius=0.055, color=params.get("highlight_color", "#FCA5A5"))
            sweep = Arc(radius=0.30, start_angle=PI * 0.15, angle=PI * 0.70, color=icon_color, stroke_width=1.4)
            icon = VGroup(scan, sweep, tumor)
        elif key == "recommendation":
            tile = RoundedRectangle(width=0.82, height=0.56, corner_radius=0.08, color=icon_color, stroke_width=2.0)
            tile.set_fill("#111827", opacity=params.get("icon_fill_opacity", 0.10))
            play = Triangle(color=params.get("highlight_color", "#FDE68A"), stroke_width=1.5).scale(0.13)
            play.rotate(-PI / 2)
            star = Text("★", font_size=13, color=params.get("highlight_color", "#FDE68A"))
            star.next_to(tile, UR, buff=-0.05)
            icon = VGroup(tile, play, star)
        else:
            icon = Dot(radius=0.18, color=icon_color)

        label = Text(label_text, font_size=params.get("font_size", 20), color=label_color, weight=MEDIUM)
        label.next_to(icon, DOWN, buff=0.16)
        ghost = VGroup(icon, label)
        ghost.scale(scale)
        ghost.move_to(_as_vector(position))
        ghost.set_opacity(opacity)
        ghost.ghost_key = key
        ghost_items[key] = ghost
        ghosts.add(ghost)

    ghosts.ghost_items = ghost_items
    ghosts.set_opacity(opacity)
    return ghosts


def make_axis_free_curve(params, zone):
    raw_points = params.get(
        "points",
        [[-1.35, -0.55, 0], [-0.55, -0.10, 0], [0.35, 0.16, 0], [1.35, 0.70, 0]],
    )
    points = [_as_vector(point) for point in raw_points]
    if not params.get("absolute_points", False):
        min_corner = np.min(points, axis=0)
        max_corner = np.max(points, axis=0)
        local_center = (min_corner + max_corner) / 2
        points = [point - local_center for point in points]
    else:
        local_center = ORIGIN

    curve = VMobject()
    curve.set_points_smoothly(points)
    curve.set_stroke(
        params.get("color", ACCENT),
        width=params.get("stroke_width", 4.0),
        opacity=params.get("opacity", 1.0),
    )
    curve.scale(params.get("scale", 1.0))

    group = VGroup()

    guide_group = VGroup()
    if params.get("show_guides", False):
        guide_color = params.get("guide_color", "#334155")
        guide_opacity = params.get("guide_opacity", 0.20)
        guide_stroke_width = params.get("guide_stroke_width", 1.2)
        guide_width = params.get("guide_width", 4.25)
        guide_height = params.get("guide_height", 1.95)
        x_axis = Line(LEFT * guide_width / 2 + DOWN * guide_height / 2, RIGHT * guide_width / 2 + DOWN * guide_height / 2, color=guide_color, stroke_width=guide_stroke_width)
        y_axis = Line(LEFT * guide_width / 2 + DOWN * guide_height / 2, LEFT * guide_width / 2 + UP * guide_height / 2, color=guide_color, stroke_width=guide_stroke_width)
        guide_group.add(x_axis, y_axis)
        guide_group.set_opacity(guide_opacity)
        guide_group.scale(params.get("scale", 1.0))
        group.add(guide_group)

    data_points = VGroup()
    if params.get("show_points", False):
        point_color = params.get("point_color", "#94A3B8")
        point_opacity = params.get("point_opacity", 0.42)
        point_radius = params.get("point_radius", 0.045)
        raw_data_points = params.get(
            "data_points",
            [[-1.45, -0.48, 0], [-1.05, -0.30, 0], [-0.62, -0.08, 0], [-0.16, 0.04, 0], [0.35, 0.22, 0], [0.82, 0.40, 0], [1.32, 0.64, 0]],
        )
        normalized_data_points = [_as_vector(point) for point in raw_data_points]
        if not params.get("absolute_points", False):
            normalized_data_points = [point - local_center for point in normalized_data_points]
        point_glow = params.get("point_glow", False)
        point_glow_opacity = params.get("point_glow_opacity", 0.16)
        point_glow_scale = params.get("point_glow_scale", 2.4)
        for point in normalized_data_points:
            if point_glow:
                halo = Dot(point=point, radius=point_radius * point_glow_scale, color=point_color)
                halo.set_opacity(point_glow_opacity)
                data_points.add(halo)
            dot = Dot(point=point, radius=point_radius, color=point_color)
            dot.set_opacity(point_opacity)
            data_points.add(dot)
        data_points.scale(params.get("scale", 1.0))
        group.add(data_points)

    confidence_band = None
    if params.get("show_band", False):
        confidence_band = curve.copy()
        confidence_band.set_stroke(
            params.get("band_color", params.get("color", ACCENT)),
            width=params.get("band_width", params.get("stroke_width", 4.0) * 3.4),
            opacity=params.get("band_opacity", 0.10),
        )
        group.add(confidence_band)

    curve_glow = None
    if params.get("glow", False):
        curve_glow = curve.copy()
        curve_glow.set_stroke(
            params.get("glow_color", params.get("color", ACCENT)),
            width=params.get("glow_width", params.get("stroke_width", 4.0) * 2.6),
            opacity=params.get("glow_opacity", 0.16),
        )
        group.add(curve_glow)
    group.add(curve)

    title = None
    if params.get("title"):
        title = Text(
            params.get("title"),
            font_size=params.get("title_font_size", 28),
            color=params.get("title_color", TEXT_MAIN),
            weight=params.get("title_weight", MEDIUM),
        )
        fit_to_width(title, params.get("title_max_width", 5.2))
        title.next_to(group, UP, buff=params.get("title_buff", 0.42))
        group.add(title)

    if not params.get("absolute_points", False):
        position = _as_vector(params.get("position"), ZONE_POSITIONS.get(zone, ORIGIN))
        group.move_to(position)
    group.pattern_points = data_points
    group.pattern_curve = curve
    group.pattern_glow = curve_glow if params.get("glow", False) else None
    group.pattern_band = confidence_band
    group.pattern_title = title
    group.pattern_guides = guide_group
    return group


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
    Draw links from from_obj to to_obj. By default this keeps the older
    multi-line behavior, but Scene 2 can opt into a single centered arrow to
    avoid example-grid overlap.
    """
    mode = params.get("mode", "multi")
    stroke_width = params.get("stroke_width", 3)
    stroke_opacity = params.get("stroke_opacity", 0.55)
    color = params.get("color", TEXT_SUB)

    if mode in {"single", "single_arrow", "arrow"}:
        start = from_obj.get_right() + RIGHT * params.get("start_buff", 0.16)
        end = to_obj.get_left() + LEFT * params.get("end_buff", 0.16)
        arrow = Arrow(
            start,
            end,
            buff=0.0,
            stroke_width=stroke_width,
            color=color,
            max_tip_length_to_length_ratio=params.get("max_tip_length_to_length_ratio", 0.12),
            max_stroke_width_to_length_ratio=12,
        )
        arrow.set_opacity(stroke_opacity)
        return arrow

    link_count = max(1, params.get("link_count", 3))

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
    hide_internal_pattern = params.get("hide_internal_pattern", False)
    lock_opacity_override = params.get("lock_opacity", None)

    # Outer shell — slightly larger for more presence
    shell = Circle(
        radius=0.82,
        stroke_color=color,
        stroke_width=3.2,
        fill_color="#0f1720",
        fill_opacity=0.96,
    )
    # Subtle glow ring outside — grows as training progresses
    glow = Circle(
        radius=0.82 + 0.14,
        stroke_color=color,
        stroke_width=18,
    ).set_opacity(0.05 + 0.10 * progress)

    # Internal wave/pattern — the "brain" of the model
    # rough = noisy/unlearned; smooth = clean learned curve
    rough_pts = [
        LEFT * 0.52 + DOWN * 0.12,
        LEFT * 0.28 + UP * 0.22,
        ORIGIN + DOWN * 0.14,
        RIGHT * 0.26 + UP * 0.18,
        RIGHT * 0.52 + DOWN * 0.06,
    ]
    smooth_pts = [
        LEFT * 0.52 + DOWN * 0.06,
        LEFT * 0.26 + UP * 0.06,
        ORIGIN + UP * 0.12,
        RIGHT * 0.26 + UP * 0.22,
        RIGHT * 0.52 + UP * 0.34,
    ]
    blended = [a * (1 - progress) + b * progress for a, b in zip(rough_pts, smooth_pts)]
    pattern = VMobject()
    pattern.set_points_smoothly(blended)
    # Color shifts from dim gold → bright gold as it learns
    pattern_opacity = 0.0 if hide_internal_pattern else 0.45 + 0.45 * progress
    pattern.set_stroke(ACCENT, width=2.8 + 1.2 * progress, opacity=pattern_opacity)

    # "model" label — inside circle, top, only during plastic phase
    label = Text("model", font_size=17, color=TEXT_SUB, weight=MEDIUM)
    label.move_to(UP * 0.58)
    label.set_opacity(params.get("label_opacity", 0.65 if phase == "plastic" else 0.0))

    # Lock icon — inside circle bottom, only during fixed phase
    # Drawn cleanly so it doesn't overlap pattern
    lock_shackle = Arc(
        radius=0.13, start_angle=0, angle=PI,
        color=TEXT_SUB, stroke_width=2.0
    ).move_to(DOWN * 0.32 + UP * 0.13)
    lock_body = RoundedRectangle(
        corner_radius=0.04,
        width=0.34, height=0.22,
        stroke_color=TEXT_SUB, stroke_width=1.8,
        fill_color="#0f1720", fill_opacity=1.0,
    ).move_to(DOWN * 0.32)
    lock = VGroup(lock_shackle, lock_body)
    default_lock_opacity = 0.72 if phase == "fixed" else 0.0
    lock.set_opacity(default_lock_opacity if lock_opacity_override is None else lock_opacity_override)

    # "Fixed model" label — outside circle, below, only during fixed phase
    # Positioned well clear of the circle so it never crowds the pattern curve
    fixed_label = Text("Fixed model", font_size=16, color=TEXT_SUB, weight=MEDIUM)
    fixed_label.next_to(shell, DOWN, buff=0.45)
    fixed_label.set_opacity(
        0.72 if phase == "fixed" and params.get("show_fixed_label", True) else 0.0
    )

    core = VGroup(glow, shell, pattern, label, lock, fixed_label)
    place_in_zone(core, zone)
    return core


def make_show_model_core(params, zone):
    return _scene4_model_core(params, zone)


def make_show_phase_labels(params, zone):
    title = Text(params.get("title", "Two lives of one system"), font_size=28, color=TEXT_MAIN, weight=MEDIUM)
    title.move_to(UP * 3.0)
    training = Text("Training", font_size=22, color=HIGHLIGHT, weight=MEDIUM).move_to(LEFT * 3.4 + UP * 1.8)
    inference = Text("Inference", font_size=22, color=SECONDARY, weight=MEDIUM).move_to(RIGHT * 3.4 + UP * 1.8)
    if params.get("active") == "training":
        inference.set_opacity(0.22)
    elif params.get("active") == "inference":
        training.set_opacity(0.22)
    if not params.get("show_title", True):
        title.set_opacity(0.0)
    group = VGroup(title, training, inference)
    group.set_opacity(params.get("opacity", 1.0))
    # Do not call place_in_zone — these are absolute screen anchors
    return group


def make_show_training_examples(params, zone):
    count = max(1, min(3, int(params.get("count", 3))))
    labels = params.get("examples", ["x₁ → y₁", "x₂ → y₂", "x₃ → y₃"])
    rows = VGroup()
    for index in range(count):
        dot = Dot(ORIGIN, radius=0.055, color=HIGHLIGHT)
        text = Text(labels[index], font_size=17, color=TEXT_SUB, weight=MEDIUM)
        text.next_to(dot, RIGHT, buff=0.12)
        rows.add(VGroup(dot, text))
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.26)
    known = Text("Known answers", font_size=16, color=TEXT_SUB, weight=MEDIUM)
    known.next_to(rows, DOWN, buff=0.22)
    # Arrow: from right edge of rows toward ORIGIN (model center). 
    # We'll build this relative to rows center, then place_in_zone adjusts.
    content = VGroup(rows, known)
    content.move_to(LEFT * 2.8)
    arrow = Arrow(
        content.get_right() + RIGHT * 0.15,
        LEFT * 0.95,
        buff=0.0,
        color=HIGHLIGHT,
        stroke_width=2.8,
        max_tip_length_to_length_ratio=0.08,
    )
    group = VGroup(content, arrow)
    group.set_opacity(params.get("opacity", 1.0))
    return group


def make_show_prediction_error(params, zone):
    # These are positioned in absolute screen space, anchored to the right of the model at ORIGIN
    pred = Dot(RIGHT * 2.6 + UP * 0.34, radius=0.065, color=PRIMARY)
    pred_label = Text("Prediction", font_size=17, color=TEXT_SUB, weight=MEDIUM).next_to(pred, UP, buff=0.10)
    true = Dot(RIGHT * 2.6 + DOWN * params.get("gap", 0.34), radius=0.065, color=ACCENT)
    true_label = Text("true", font_size=14, color=TEXT_SUB).next_to(true, DOWN, buff=0.08)
    # Arrow from model right edge toward prediction
    arrow = Arrow(
        RIGHT * 0.88 + UP * 0.08,
        pred.get_left() + LEFT * 0.14,
        buff=0.0,
        color=PRIMARY,
        stroke_width=2.8,
        max_tip_length_to_length_ratio=0.08,
    )
    gap = Line(pred.get_center(), true.get_center(), color=WARNING, stroke_width=3.2)
    error = Text("Error", font_size=17, color=WARNING, weight=MEDIUM).next_to(gap, RIGHT, buff=0.12)
    group = VGroup(arrow, pred, pred_label, true, true_label, gap, error)
    group.set_opacity(params.get("opacity", 1.0))
    return group


def make_show_adjustment_loop(params, zone):
    # Arc from error side (right of model) back to model bottom-right — absolute coords
    start = RIGHT * 2.55 + DOWN * 0.32
    end = RIGHT * 0.6 + DOWN * 0.62
    arc = ArcBetweenPoints(start, end, angle=-PI / 2.6, color=WARNING, stroke_width=2.8)
    tip = Triangle(color=WARNING, fill_color=WARNING, fill_opacity=1.0).scale(0.08)
    tip.rotate(-PI / 3.5)
    tip.move_to(end)
    label = Text("Adjust", font_size=17, color=WARNING, weight=MEDIUM).move_to(RIGHT * 1.6 + DOWN * 1.1)
    group = VGroup(arc, tip, label)
    group.set_opacity(params.get("opacity", 1.0))
    return group


def make_show_repeat_learning(params, zone):
    progress = max(0.0, min(1.0, params.get("model_progress", 0.65)))
    # Example dot on the left
    example = Dot(LEFT * 2.8 + UP * 0.12, radius=0.058, color=HIGHLIGHT)
    # Prediction and true dots on the right — gap shrinks as progress grows
    pred_y = 0.42 - 0.32 * progress
    true_y = -0.18 + 0.14 * progress
    pred = Dot(RIGHT * 2.6 + UP * pred_y, radius=0.058, color=PRIMARY)
    true = Dot(RIGHT * 2.6 + UP * true_y, radius=0.058, color=ACCENT)
    # Arrows through model
    in_arrow = Arrow(
        LEFT * 2.55 + UP * 0.08, LEFT * 0.92 + UP * 0.04,
        buff=0, color=HIGHLIGHT, stroke_width=2.4,
        max_tip_length_to_length_ratio=0.09,
    )
    out_arrow = Arrow(
        RIGHT * 0.92 + UP * 0.04, pred.get_left() + LEFT * 0.08,
        buff=0, color=PRIMARY, stroke_width=2.4,
        max_tip_length_to_length_ratio=0.09,
    )
    # Error gap — visually shrinks
    gap = Line(
        pred.get_center(), true.get_center(),
        color=WARNING, stroke_width=3.0,
    ).set_opacity(max(0.1, 0.85 - 0.65 * progress))
    # Label goes ABOVE — clear of model's "Fixed model" label below
    label = Text("again and again", font_size=16, color=TEXT_SUB, weight=MEDIUM)
    label.move_to(UP * 1.55)
    group = VGroup(example, in_arrow, out_arrow, pred, true, gap, label)
    group.set_opacity(params.get("opacity", 1.0))
    return group


def make_show_inference_pass(params, zone):
    opacity = params.get("opacity", 1.0)

    # Clean horizontal pipeline — everything on one line:
    # [● New data] ────────► [model] ────────► [● Prediction]
    # New data comes from the LEFT, exits as prediction to the RIGHT.
    # This mirrors the training-examples layout (examples also from the left)
    # but without any feedback loop — purely one-directional.

    new_data_pos = LEFT * 2.8 + UP * 0.0
    pred_pos = RIGHT * 2.8 + UP * 0.0

    new_data = Dot(new_data_pos, radius=0.075, color=SECONDARY)
    new_label = Text("New data", font_size=16, color=SECONDARY, weight=MEDIUM)
    new_label.next_to(new_data, UP, buff=0.16)

    pred = Dot(pred_pos, radius=0.075, color=PRIMARY)
    pred_label = Text("Prediction", font_size=16, color=TEXT_SUB, weight=MEDIUM)
    pred_label.next_to(pred, UP, buff=0.16)

    # Arrow: new data → model left edge
    in_arrow = Arrow(
        new_data_pos + RIGHT * 0.12,
        LEFT * 0.88,
        buff=0.0,
        color=SECONDARY,
        stroke_width=2.6,
        max_tip_length_to_length_ratio=0.09,
    )
    # Arrow: model right edge → prediction
    out_arrow = Arrow(
        RIGHT * 0.88,
        pred_pos + LEFT * 0.12,
        buff=0.0,
        color=PRIMARY,
        stroke_width=2.6,
        max_tip_length_to_length_ratio=0.09,
    )

    group = VGroup(in_arrow, out_arrow, new_data, new_label, pred, pred_label)
    group.set_opacity(opacity)
    return group


def make_show_build_use_summary(params, zone):
    # Two lines, stacked, centered below the model.
    # Sit at DOWN * 1.9 — clear of the model circle bottom (~DOWN * 1.27 with label).
    build = Text("Training  ·  build the model", font_size=21, color=HIGHLIGHT, weight=MEDIUM)
    use = Text("Inference  ·  use the model", font_size=21, color=SECONDARY, weight=MEDIUM)
    group = VGroup(build, use).arrange(DOWN, buff=0.28)
    group.move_to(DOWN * 1.95)
    group.set_opacity(params.get("opacity", 1.0))
    return group


def make_show_generalization_pattern(params, zone):
    """Scene 4 — Generalization ending. Four staged beats driven by JSON params.

    Stage progression:
      memory      → dim old-example echoes orbit the model. No curve yet.
      pattern     → examples fade, smooth curve emerges to the RIGHT of model.
      new_example → a bright new dot enters from the left, passes through model,
                    lands ON the curve on the right. No error, no loop.
      final       → examples nearly gone, curve + new point remain, text appears.

    Spatial contract (model lives at ORIGIN, radius 0.82 + label to DOWN ~1.27):
      • Old examples:  scattered in a loose cloud LEFT of model, radius ~1.4–2.5
      • Learned curve: lives entirely to the RIGHT, starting at RIGHT * 1.25,
                       rising gently. Never touches the model circle.
      • New point:     enters from upper-left, exits right as a prediction dot
                       that sits exactly on the curve. Arrow is thin and clear.
      • Final text:    centered at DOWN * 2.55 — below the model label.
    """
    stage = params.get("stage", "final")
    show_text = params.get("show_text", stage == "final")

    examples_opacity = params.get("examples_opacity", {
        "memory": 0.28, "pattern": 0.14, "new_example": 0.07, "final": 0.03,
    }.get(stage, 0.07))
    pattern_opacity  = params.get("pattern_opacity",  0.0  if stage == "memory" else 0.88)
    new_point_opacity = params.get("new_point_opacity", 0.0 if stage in {"memory", "pattern"} else 0.94)

    # ── 1. OLD EXAMPLES ────────────────────────────────────────────────
    # Eight dim dots scattered in a cloud to the LEFT of the model.
    # They look like training data that has been seen and half-forgotten —
    # not stored, not labelled, just faint presences.
    echo_positions = [
        LEFT * 3.65 + UP * 0.92,
        LEFT * 3.15 + UP * 0.36,
        LEFT * 3.48 + DOWN * 0.28,
        LEFT * 2.82 + UP * 0.68,
        LEFT * 2.45 + DOWN * 0.06,
        LEFT * 2.90 + DOWN * 0.62,
        LEFT * 2.15 + UP * 0.38,
        LEFT * 3.28 + UP * 0.10,
    ]
    old_dots = VGroup(*[
        Dot(p, radius=0.042, color=SECONDARY).set_opacity(examples_opacity)
        for p in echo_positions
    ])
    # No label on these — they should feel like ghosts, not annotations
    old_examples_group = VGroup(old_dots)

    # ── 2. LEARNED CURVE ───────────────────────────────────────────────
    # A clean, gently rising curve that lives entirely to the RIGHT of
    # the model. The curve is the pattern — simple, smooth, singular.
    # It starts just beyond the model's right edge (RIGHT * 1.25).
    #
    # A very faint mini scatter of noisy dots sits BEHIND the curve
    # to visually communicate: "these noisy observations → this clean rule."
    # These are different from the old_dots (which are memories on the left).
    right_scatter = [
        RIGHT * 1.82 + DOWN * 0.46,
        RIGHT * 2.10 + DOWN * 0.20,
        RIGHT * 2.38 + UP * 0.10,
        RIGHT * 2.70 + DOWN * 0.02,
        RIGHT * 3.02 + UP * 0.34,
        RIGHT * 3.34 + UP * 0.22,
        RIGHT * 3.66 + UP * 0.62,
        RIGHT * 3.98 + UP * 0.48,
    ]
    scatter_dots = VGroup(*[
        Dot(p, radius=0.044, color=SECONDARY).set_opacity(
            0.0 if stage == "memory" else pattern_opacity * 0.40
        )
        for p in right_scatter
    ])

    curve_pts = [
        RIGHT * 1.68 + DOWN * 0.34,
        RIGHT * 2.10 + DOWN * 0.14,
        RIGHT * 2.56 + UP * 0.10,
        RIGHT * 3.02 + UP * 0.34,
        RIGHT * 3.52 + UP * 0.58,
        RIGHT * 4.02 + UP * 0.78,
    ]
    learned_curve = VMobject()
    learned_curve.set_points_smoothly(curve_pts)
    learned_curve.set_stroke(ACCENT, width=2.7, opacity=pattern_opacity)

    curve_glow = VMobject()
    curve_glow.set_points_smoothly(curve_pts)
    curve_glow.set_stroke(ACCENT, width=8, opacity=pattern_opacity * 0.045)

    # Faint axis lines to give the curve a clearer mini-graph context without
    # making the scene feel like a full chart slide.
    ax_origin = RIGHT * 1.58 + DOWN * 0.50
    x_ax = Line(ax_origin, ax_origin + RIGHT * 2.85, color=TEXT_SUB, stroke_width=1.05)
    y_ax = Line(ax_origin, ax_origin + UP * 1.55, color=TEXT_SUB, stroke_width=1.05)
    axes = VGroup(x_ax, y_ax).set_opacity(0.0 if stage == "memory" else pattern_opacity * 0.22)

    learned_pattern_group = VGroup(axes, scatter_dots, curve_glow, learned_curve)

    # ── 3. NEW EXAMPLE PASS ────────────────────────────────────────────
    # A single bright cyan dot enters from the upper-LEFT (distinct from
    # the dim grey echoes), passes through the fixed model, and exits as
    # a PRIMARY-colored prediction dot that lands exactly on the curve.
    # NO error. NO feedback. The model doesn't change.
    new_visible = stage in {"new_example", "final"}

    input_pos    = LEFT * 3.55 + UP * 1.02   # comes from upper-left, away from graph
    model_in     = LEFT * 1.02 + UP * 0.16
    model_out    = RIGHT * 1.02 + UP * 0.16
    landing_pos  = RIGHT * 3.02 + UP * 0.34  # sits exactly on curve_pts[3]

    input_dot = Dot(input_pos, radius=0.068, color=SECONDARY)
    input_dot.set_opacity(new_point_opacity)
    input_lbl = Text("new data", font_size=12, color=SECONDARY, weight=MEDIUM)
    input_lbl.next_to(input_dot, UP, buff=0.10)
    input_lbl.set_opacity(new_point_opacity * 0.82)

    in_arrow = Arrow(
        input_pos + RIGHT * 0.10 + DOWN * 0.08,
        model_in,
        buff=0.0, color=SECONDARY, stroke_width=2.0,
        max_tip_length_to_length_ratio=0.10,
    ).set_opacity(new_point_opacity * 0.72)

    out_arrow = Arrow(
        model_out,
        landing_pos + LEFT * 0.12,
        buff=0.0, color=PRIMARY, stroke_width=2.0,
        max_tip_length_to_length_ratio=0.10,
    ).set_opacity(new_point_opacity * 0.72)

    pred_dot = Dot(landing_pos, radius=0.072, color=PRIMARY)
    pred_dot.set_opacity(new_point_opacity)
    pred_lbl = Text("prediction", font_size=13, color=TEXT_MAIN, weight=MEDIUM)
    pred_lbl.next_to(pred_dot, UP + RIGHT, buff=0.12)
    pred_lbl.set_opacity(new_point_opacity * 0.90)

    # Tiny cross-hair tick on the landing dot to show it sits ON the curve
    tick_h = Line(landing_pos + LEFT*0.085, landing_pos + RIGHT*0.085,
                  color=ACCENT, stroke_width=1.2)
    tick_v = Line(landing_pos + DOWN*0.085, landing_pos + UP*0.085,
                  color=ACCENT, stroke_width=1.2)
    landing_tick = VGroup(tick_h, tick_v).set_opacity(new_point_opacity * 0.58)

    new_example_group = VGroup(
        input_dot, input_lbl, in_arrow,
        out_arrow, pred_dot, pred_lbl, landing_tick,
    )

    # ── 4. FINAL TEXT ──────────────────────────────────────────────────
    title    = Text("Generalization", font_size=34, color=TEXT_MAIN, weight=BOLD)
    subtitle = Text("new examples follow the learned pattern", font_size=18, color=TEXT_SUB, weight=MEDIUM)
    final_text = VGroup(title, subtitle).arrange(DOWN, buff=0.14)
    final_text.move_to(DOWN * 2.55)
    final_text.set_opacity(1.0 if show_text else 0.0)

    group = VGroup(
        old_examples_group,
        learned_pattern_group,
        new_example_group,
        final_text,
    )
    group.set_opacity(params.get("opacity", 1.0))
    return group


TAXONOMY_COLORS = {
    "background": BG_COLOR,
    "neutral": "#5D6470",
    "amber": "#F2A93B",
    "blue": "#5B8CFF",
    "cluster": "#D8CFA8",
    "agent": "#FFFFFF",
    "trail": "#FFFFFF",
    "reward": "#F6C453",
    "penalty": "#6F8FBF",
    "label": "#FFFFFF",
}


def _taxonomy_density_amount(point, params):
    base = _as_vector(point)
    clusters = params.get("clusters", [])
    if not clusters:
        return 0.0
    amount = 0.0
    for cluster in clusters:
        center = _as_vector(cluster.get("center"))
        radius = cluster.get("radius", 1.0)
        distance = np.linalg.norm(base - center)
        amount = max(amount, max(0.0, 1.0 - distance / radius))
    return amount


def _taxonomy_mixed_neighborhood_amount(index, params):
    points = params.get("points", [])
    classes = params.get("classes", [])
    if index >= len(points) or index >= len(classes):
        return 0.0
    base = _as_vector(points[index])
    own_class = classes[index]
    nearby_opposite = 0
    nearby_total = 0
    for other_index, other_point in enumerate(points):
        if other_index == index or other_index >= len(classes):
            continue
        distance = np.linalg.norm(base - _as_vector(other_point))
        if distance <= 0.82:
            nearby_total += 1
            if classes[other_index] != own_class:
                nearby_opposite += 1
    if nearby_total == 0:
        return 0.0
    ratio = nearby_opposite / nearby_total
    return max(0.0, min(1.0, ratio))


def _taxonomy_point_position(point, params, drift_factor=0.0):
    base = _as_vector(point)
    if drift_factor <= 0:
        return base

    clusters = params.get("clusters", [])
    if not clusters:
        return base

    nearest = min(
        clusters,
        key=lambda cluster: np.linalg.norm(base - _as_vector(cluster.get("center"))),
    )
    center = _as_vector(nearest.get("center"))
    return base + (center - base) * drift_factor


def _mix_hex(color_a, color_b, amount):
    amount = max(0.0, min(1.0, amount))

    def parts(color):
        color = color.lstrip("#")
        return np.array([int(color[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)

    mixed = parts(color_a) * (1 - amount) + parts(color_b) * amount
    return "#" + "".join(f"{int(round(value)):02X}" for value in mixed)


def _taxonomy_label_opacities(stage):
    dim = 0.16
    low = 0.04
    bright = 0.88
    states = {
        "field_intro": [0.0, 0.0, 0.0, 0.0],
        "label_intro": [dim, dim, dim, dim],
        "supervised_full": [bright, low, low, low],
        "supervised_boundary": [bright, low, low, low],
        "unsupervised_neutral": [low, bright, low, low],
        "unsupervised_clusters": [low, bright, low, low],
        "unsupervised_hold": [low, bright, low, low],
        "semi_neutral": [low, low, bright, low],
        "semi_anchors": [low, low, bright, low],
        "semi_influence": [low, low, bright, low],
        "semi_hold": [low, low, 0.46, low],
        "rl_neutral": [low, low, low, bright],
        "rl_agent": [low, low, low, bright],
        "rl_navigation": [low, low, low, bright],
        "rl_resolution": [0.0, 0.0, 0.0, 0.0],
    }
    return states.get(stage, [dim, dim, dim, dim])


def _taxonomy_labels(stage):
    names = [
        "supervised learning",
        "unsupervised learning",
        "semi-supervised learning",
        "reinforcement learning",
    ]
    positions = [
        LEFT * 4.75 + UP * 3.08,
        RIGHT * 4.55 + UP * 3.08,
        LEFT * 4.55 + DOWN * 3.08,
        RIGHT * 4.28 + DOWN * 3.08,
    ]
    labels = VGroup()
    label_items = {}
    for name, position, opacity in zip(names, positions, _taxonomy_label_opacities(stage)):
        label = Text(name, font_size=15, color=TAXONOMY_COLORS["label"], weight=MEDIUM)
        label.move_to(position)
        label.set_opacity(opacity)
        labels.add(label)
        label_items[name] = label
    labels.label_items = label_items
    return labels


def _taxonomy_glows(params, stage):
    glows = VGroup()

    if stage in {"unsupervised_clusters", "unsupervised_hold"}:
        points = params.get("points", [])
        drift = 0.028
        for point in points:
            density = _taxonomy_density_amount(point, params)
            if density < 0.38:
                continue
            position = _taxonomy_point_position(point, params, drift)
            halo_radius = 0.078 + density * 0.070
            halo = Dot(position, radius=halo_radius, color=TAXONOMY_COLORS["cluster"])
            halo.set_opacity((0.095 if stage == "unsupervised_clusters" else 0.080) * density)
            glows.add(halo)

    if stage == "supervised_boundary":
        points = params.get("points", [])
        for index, point in enumerate(points):
            mixed = _taxonomy_mixed_neighborhood_amount(index, params)
            if mixed < 0.42:
                continue
            p = _as_vector(point)
            halo = Dot(p, radius=0.078 + 0.046 * mixed, color=TAXONOMY_COLORS["cluster"])
            halo.set_opacity(0.036 * mixed)
            glows.add(halo)

    if stage in {"rl_navigation", "rl_resolution"}:
        points = params.get("points", [])
        clusters = params.get("clusters", [])
        destination_index = params.get("destination_cluster_index")
        if destination_index is not None and 0 <= destination_index < len(clusters):
            destination = clusters[destination_index]
            center = _as_vector(destination.get("center"))
            radius = destination.get("radius", 1.0)
            for point in points:
                p = _as_vector(point)
                distance = np.linalg.norm(p - center)
                if distance > radius * 0.92:
                    continue
                amount = max(0.0, 1.0 - distance / (radius * 0.92))
                halo = Dot(p, radius=0.060 + amount * 0.050, color=TAXONOMY_COLORS["reward"])
                base_opacity = 0.030 if stage == "rl_navigation" else 0.070
                halo.set_opacity(base_opacity * amount)
                glows.add(halo)

    return glows


def _taxonomy_influence(params, stage):
    if stage not in {"semi_influence", "semi_hold"}:
        return VGroup()

    anchors = params.get("anchors", [])
    anchor_map = {item["index"]: item.get("class", "a") for item in anchors}
    points = params.get("points", [])
    influence = VGroup()
    for point_index, point in enumerate(points):
        if point_index in anchor_map:
            continue
        strongest_amount = 0.0
        strongest_color = None
        for anchor_index, anchor_class in anchor_map.items():
            if not 0 <= anchor_index < len(points):
                continue
            distance = np.linalg.norm(_as_vector(point) - _as_vector(points[anchor_index]))
            amount = max(0.0, 1.0 - distance / 1.35)
            if amount > strongest_amount:
                strongest_amount = amount
                strongest_color = TAXONOMY_COLORS["amber"] if anchor_class == "a" else TAXONOMY_COLORS["blue"]
        if strongest_amount <= 0.18 or strongest_color is None:
            continue
        halo = Dot(_as_vector(point), radius=0.078 + strongest_amount * 0.060, color=strongest_color)
        halo.set_opacity((0.155 if stage == "semi_influence" else 0.145) * strongest_amount)
        influence.add(halo)
    return influence


def _taxonomy_points(params, stage):
    points = params.get("points", [])
    classes = params.get("classes", [])
    anchors = params.get("anchors", [])
    anchor_map = {item["index"]: item.get("class", "a") for item in anchors}
    anchor_indices = set(anchor_map)
    influence_stages = {"semi_influence", "semi_hold"}
    drift = 0.028 if stage in {"unsupervised_clusters", "unsupervised_hold"} else 0.0

    dots = VGroup()
    dot_items = []
    for index, point in enumerate(points):
        position = _taxonomy_point_position(point, params, drift)
        color = TAXONOMY_COLORS["neutral"]
        opacity = params.get("neutral_opacity", 0.24)
        radius = params.get("point_radius", 0.032)

        if stage in {"supervised_full", "supervised_boundary"}:
            color = TAXONOMY_COLORS["amber"] if classes[index] == "a" else TAXONOMY_COLORS["blue"]
            opacity = 0.88
            if stage == "supervised_boundary":
                opacity = min(0.96, opacity + _taxonomy_mixed_neighborhood_amount(index, params) * 0.08)
        elif stage in {"unsupervised_clusters", "unsupervised_hold"}:
            density = _taxonomy_density_amount(point, params)
            opacity = params.get("neutral_opacity", 0.24) + max(0.0, density - 0.22) * (0.24 if stage == "unsupervised_clusters" else 0.18)
            color = _mix_hex(TAXONOMY_COLORS["neutral"], TAXONOMY_COLORS["cluster"], max(0.0, density - 0.24) * 0.20)
        elif stage in {"semi_anchors", *influence_stages} and index in anchor_indices:
            color = TAXONOMY_COLORS["amber"] if anchor_map[index] == "a" else TAXONOMY_COLORS["blue"]
            opacity = 0.96
            radius = params.get("anchor_radius", 0.052)
        elif stage in influence_stages:
            nearest_amount = 0.0
            nearest_color = color
            for anchor_index, anchor_class in anchor_map.items():
                if not 0 <= anchor_index < len(points):
                    continue
                dist = np.linalg.norm(_as_vector(point) - _as_vector(points[anchor_index]))
                amount = max(0.0, 1.0 - dist / 1.35) * 0.50
                if amount > nearest_amount:
                    nearest_amount = amount
                    nearest_color = TAXONOMY_COLORS["amber"] if anchor_class == "a" else TAXONOMY_COLORS["blue"]
            if nearest_amount > 0:
                color = _mix_hex(TAXONOMY_COLORS["neutral"], nearest_color, nearest_amount)
                opacity = params.get("neutral_opacity", 0.24) + nearest_amount * 0.38

        dot = Dot(position, radius=radius, color=color)
        dot.set_opacity(opacity)
        dots.add(dot)
        dot_items.append(dot)

    dots.dot_items = dot_items
    return dots


def _taxonomy_trail(params, stage):
    if stage not in {"rl_navigation", "rl_resolution"}:
        return VGroup()
    path_points = [_as_vector(point) for point in params.get("agent_path", [])]
    if len(path_points) < 2:
        return VGroup()
    path = VMobject()
    path.set_points_smoothly(path_points)
    trail = DashedVMobject(path, num_dashes=params.get("trail_dashes", 54))
    trail.set_stroke(TAXONOMY_COLORS["trail"], width=1.45, opacity=0.26)
    return trail


def _taxonomy_agent(params, stage):
    if stage not in {"rl_agent", "rl_navigation", "rl_resolution"}:
        return VGroup()
    path_points = params.get("agent_path", [])
    if stage == "rl_agent" or not path_points:
        position = params.get("agent_start", [-5.25, -0.7, 0])
    else:
        position = path_points[-1]
    agent = Dot(_as_vector(position), radius=params.get("agent_radius", 0.075), color=TAXONOMY_COLORS["agent"])
    agent.set_opacity(0.98)
    agent_halo = Dot(_as_vector(position), radius=params.get("agent_radius", 0.075) * 2.25, color=TAXONOMY_COLORS["agent"])
    agent_halo.set_opacity(0.10 if stage != "rl_resolution" else 0.07)
    return VGroup(agent_halo, agent)


def make_taxonomy_field(params, zone):
    stage = params.get("stage", "field_intro")
    glows = _taxonomy_glows(params, stage)
    influence = _taxonomy_influence(params, stage)
    points = _taxonomy_points(params, stage)
    trail = _taxonomy_trail(params, stage)
    agent = _taxonomy_agent(params, stage)
    labels = _taxonomy_labels(stage)

    group = VGroup(glows, influence, points, trail, agent, labels)
    group.taxonomy_glows = glows
    group.taxonomy_influence = influence
    group.taxonomy_points = points
    group.taxonomy_trail = trail
    group.taxonomy_agent = agent
    group.taxonomy_labels = labels
    group.taxonomy_params = dict(params)
    group.taxonomy_stage = stage
    if "opacity" in params:
        group.set_opacity(params["opacity"])
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


def make_workflow_cycle(params, zone):
    """
    Scene 7 — Professional Workflow cycle diagram.

    KEY GEOMETRY DESIGN:
    All 5 nodes are pre-positioned on a flattened elliptical arc so that
    when the return arrow closes, the diagram reads as a genuine loop —
    not a horizontal pipeline with an underbelly arc.

    Nodes 1–3 appear to be on a straight line (the ellipse top is nearly
    flat). Node 4 dips slightly. Node 5 dips more. The closing arc from 5
    back to 1 is a short, tight curve — not a long sweeping belly — because
    the nodes are already curving toward each other.

    This is the key fix for the "too horizontal" audit finding.

    params:
      nodes           List[str]  — labels to include (subset of all 5).
      complete        bool       — draw the closing return arrow.
      unlabeled       bool       — if True, node text is hidden (Beat 1 state).
      warn_node       str|None   — label of node shown in amber warning state.
      node_radius     float      — circle radius (default 0.42).
    """
    ALL_LABELS = ["DATA", "PREPROCESSING", "TRAINING", "EVALUATION", "IMPROVEMENT"]

    requested   = params.get("nodes", ALL_LABELS)
    node_radius = params.get("node_radius", 0.42)
    warn_node   = params.get("warn_node",   None)
    unlabeled   = params.get("unlabeled",   False)
    complete    = params.get("complete", False) or params.get("curve_return", False)

    # ── GEOMETRY: fixed arc positions for all 5 slots ─────────────────────
    # Nodes sit on a wide, flat ellipse.
    # Horizontal semi-axis = 3.2, vertical semi-axis = 0.90.
    # We sample 5 evenly-spaced angles along the TOP arc (from ~200° to ~340°
    # in standard math convention, which maps to left→right visually).
    # This gives a gently curving path — left side nearly level, right side
    # dropping slightly — so the closing arrow only needs a short trip back.
    ELLIPSE_A = 3.20   # horizontal radius
    ELLIPSE_B = 0.82   # vertical radius  (controls how much curve)
    # Angles for 5 nodes: spread across the upper half of the ellipse,
    # biased so node 1 is upper-left and node 5 is upper-right but lower.
    # Using angles from 210° → 330° (in degrees, CCW from right).
    import math
    angle_start_deg = 210
    angle_end_deg   = 330
    all_angles = [
        math.radians(angle_start_deg + (angle_end_deg - angle_start_deg) * i / (len(ALL_LABELS) - 1))
        for i in range(len(ALL_LABELS))
    ]
    # all_angles[0] = left, all_angles[4] = right
    all_positions = [
        np.array([ELLIPSE_A * math.cos(a), ELLIPSE_B * math.sin(a), 0.0])
        for a in all_angles
    ]
    # Center the arc so its bounding box is at ORIGIN
    arc_center_y = (max(p[1] for p in all_positions) + min(p[1] for p in all_positions)) / 2.0
    all_positions = [p - np.array([0.0, arc_center_y, 0.0]) for p in all_positions]

    # Map from label to fixed arc position
    label_to_pos = {label: all_positions[i] for i, label in enumerate(ALL_LABELS)}

    # ── Node visual construction ──────────────────────────────────────────
    def make_node(label, is_warn=False):
        stroke_col   = "#E8A838" if is_warn else PRIMARY
        fill_col     = "#1a1006" if is_warn else "#0d1520"
        glow_opacity = 0.24 if is_warn else 0.14

        outer = Circle(
            radius=node_radius + 0.08,
            stroke_color=stroke_col,
            stroke_width=1.0,
            fill_opacity=0,
        ).set_stroke(opacity=glow_opacity)

        ring = Circle(
            radius=node_radius,
            stroke_color=stroke_col,
            stroke_width=2.6,
            fill_color=fill_col,
            fill_opacity=1.0,
        )

        # Label — hidden opacity when unlabeled=True (Beat 1 state)
        txt = Text(label, font_size=15, weight=MEDIUM, color=TEXT_MAIN)
        fit_to_width(txt, node_radius * 1.50)
        txt.move_to(ring.get_center())
        if unlabeled:
            txt.set_opacity(0.0)

        node_group = VGroup(outer, ring, txt)

        # Warn halo — second ring, amber, visible only for warn node
        if is_warn:
            warn_halo = Circle(
                radius=node_radius + 0.20,
                stroke_color="#E8A838",
                stroke_width=2.2,
                fill_opacity=0,
            ).set_stroke(opacity=0.35)
            node_group.add(warn_halo)

        return node_group

    # ── Build nodes at their fixed arc positions ──────────────────────────
    node_objects = []
    for label in requested:
        is_warn = (warn_node is not None and label == warn_node)
        node = make_node(label, is_warn=is_warn)
        node.move_to(label_to_pos[label])
        node_objects.append(node)

    group = VGroup(*node_objects)

    # ── Arrows between consecutive nodes ──────────────────────────────────
    # Because nodes are on a curve, arrow direction follows the curve
    # naturally — we just connect adjacent node edges.
    arrows = VGroup()
    for i in range(len(node_objects) - 1):
        start = node_objects[i].get_right()   + RIGHT * 0.08
        end   = node_objects[i + 1].get_left() + LEFT  * 0.08
        # For nodes on an arc the "right" and "left" edges are not perfectly
        # aligned — use center-to-center direction for cleaner arrows
        p_start = label_to_pos[requested[i]]
        p_end   = label_to_pos[requested[i + 1]]
        direction = p_end - p_start
        direction = direction / np.linalg.norm(direction)
        start = label_to_pos[requested[i]]     + direction * (node_radius + 0.12)
        end   = label_to_pos[requested[i + 1]] - direction * (node_radius + 0.12)
        arr = Arrow(
            start, end,
            buff=0.0,
            stroke_width=2.4,
            color=TEXT_SUB,
            max_stroke_width_to_length_ratio=10,
            tip_length=0.17,
        )
        arrows.add(arr)

    # ── Closing return arc ─────────────────────────────────────────────────
    # Because nodes are on an elliptical arc, the closing arrow from node 5
    # back to node 1 completes the ellipse — it is a short arc, not a long
    # underbelly sweep. This is what makes the final frame read as a loop.
    return_arrow = VGroup()
    if complete and len(requested) == len(ALL_LABELS):
        first_pos = label_to_pos[requested[0]]
        last_pos  = label_to_pos[requested[-1]]

        # Arc continues the ellipse from node 5 back around to node 1.
        # The angle of the bottom arc in our ellipse goes from ~330° back to ~210°
        # traveling clockwise (i.e. downward through the bottom).
        # We use ArcBetweenPoints with a positive angle to curve downward.
        arc_start = last_pos  + np.array([0.0, -(node_radius + 0.12), 0.0])
        arc_end   = first_pos + np.array([0.0, -(node_radius + 0.12), 0.0])

        closing_arc = ArcBetweenPoints(
            arc_start,
            arc_end,
            angle=PI * 0.85,    # curves downward — completes the ellipse
            color=SECONDARY,
            stroke_width=2.4,
        )
        closing_arc.set_stroke(opacity=0.90)

        # Arrowhead: a small tip pointing upward toward DATA node bottom
        tip = Triangle(
            color=SECONDARY,
            fill_color=SECONDARY,
            fill_opacity=1.0,
        ).scale(0.075)
        # Rotate to point roughly upward-right toward node 1
        tip.rotate(PI * 0.08)
        tip.move_to(arc_end + np.array([0.0, 0.05, 0.0]))

        return_arrow = VGroup(closing_arc, tip)

    full = VGroup(group, arrows, return_arrow)

    # Expose sub-structure for renderer mutations
    full.cycle_nodes  = node_objects
    full.cycle_arrows = arrows
    full.cycle_return = return_arrow
    full.cycle_labels = list(requested)

    place_in_zone(full, zone)
    return full


def make_workflow_pipeline(params, zone):
    """Scene 7 — clean card-based professional ML workflow pipeline.

    This intentionally avoids the older circular workflow mutation system.
    It builds a complete, readable state for each narration beat:
    DATA → CLEAN → TRAIN → EVAL → IMPROVE, then a restrained return loop.
    """
    stage = params.get("stage", "intro")
    labels = params.get("labels", ["DATA", "CLEAN", "TRAIN", "EVAL", "IMPROVE"])
    card_w = params.get("card_width", 1.62)
    card_h = params.get("card_height", 0.92)
    y = params.get("y", -0.12)
    xs = params.get("x_positions", [-4.05, -2.00, 0.05, 2.10, 4.15])

    stage_to_active = {
        "intro": -1,
        "data": 0,
        "messy": 0,
        "clean": 1,
        "train": 2,
        "eval": 3,
        "overfit": 3,
        "improve": 4,
        "monitor": 4,
        "loop": 4,
        "final": 4,
    }
    active_idx = stage_to_active.get(stage, -1)
    shown_count = 5 if stage == "intro" else max(1, active_idx + 1)
    if stage in {"loop", "final", "monitor"}:
        shown_count = 5

    def opacity_for(idx):
        if stage == "intro":
            return 0.25
        if idx <= active_idx:
            return 1.0 if idx == active_idx else 0.70
        return 0.20

    def stroke_for(idx):
        if stage == "overfit" and idx == 3:
            return "#E8A838"
        if idx <= active_idx:
            return SECONDARY
        return "#324057"

    def fill_for(idx):
        if stage == "overfit" and idx == 3:
            return "#1a1006"
        if idx <= active_idx:
            return "#0d1724"
        return "#0b1320"

    def make_card(idx, label):
        pos = np.array([xs[idx], y, 0.0])
        op = opacity_for(idx)
        stroke_col = stroke_for(idx)
        fill_col = fill_for(idx)

        shadow = RoundedRectangle(
            width=card_w + 0.12,
            height=card_h + 0.12,
            corner_radius=0.18,
            stroke_color=stroke_col,
            stroke_width=1.1,
            fill_opacity=0,
        ).set_stroke(opacity=0.13 if idx <= active_idx else 0.05)
        shadow.move_to(pos)

        card = RoundedRectangle(
            width=card_w,
            height=card_h,
            corner_radius=0.16,
            stroke_color=stroke_col,
            stroke_width=2.1 if idx == active_idx else 1.45,
            fill_color=fill_col,
            fill_opacity=0.86 if idx <= active_idx else 0.36,
        )
        card.set_stroke(opacity=0.92 if idx <= active_idx else 0.32)
        card.move_to(pos)

        text = Text(label, font_size=22, weight=MEDIUM, color=TEXT_MAIN)
        fit_to_width(text, card_w * 0.72)
        text.move_to(pos + UP * 0.18)
        text.set_opacity(0.95 if idx <= active_idx or stage == "intro" else 0.34)

        internals = VGroup()
        base_y = pos[1] - 0.21

        if idx == 0:
            if stage == "messy":
                dots = [
                    Dot(np.array([pos[0] - 0.38, base_y + 0.04, 0]), radius=0.025, color="#E8A838"),
                    Dot(np.array([pos[0] - 0.08, base_y - 0.06, 0]), radius=0.018, color=TEXT_SUB),
                    Cross(Dot(np.array([pos[0] + 0.24, base_y + 0.02, 0]), radius=0.026), stroke_color="#E8A838", stroke_width=1.4).scale(0.35),
                    Line(np.array([pos[0] - 0.44, base_y - 0.16, 0]), np.array([pos[0] + 0.42, base_y - 0.11, 0]), color=TEXT_SUB, stroke_width=1.0).set_opacity(0.45),
                ]
            else:
                dots = [
                    Dot(np.array([pos[0] - 0.34 + j * 0.23, base_y, 0]), radius=0.022, color=TEXT_SUB).set_opacity(0.58)
                    for j in range(4)
                ]
            internals.add(*dots)

        elif idx == 1 and idx <= active_idx:
            rows = VGroup()
            for r in range(3):
                yy = base_y + (r - 1) * 0.085
                rows.add(Line(np.array([pos[0] - 0.42, yy, 0]), np.array([pos[0] + 0.42, yy, 0]), color=TEXT_SUB, stroke_width=1.25).set_opacity(0.58))
                rows.add(Dot(np.array([pos[0] - 0.52, yy, 0]), radius=0.015, color=SECONDARY).set_opacity(0.70))
            internals.add(rows)

        elif idx == 2 and idx <= active_idx:
            core = Circle(radius=0.11, stroke_color=SECONDARY, stroke_width=1.6, fill_color="#101d2b", fill_opacity=0.82)
            core.move_to(np.array([pos[0], base_y, 0]))
            spokes = VGroup(
                Line(core.get_center() + LEFT * 0.30, core.get_center() + LEFT * 0.13, color=TEXT_SUB, stroke_width=1.0).set_opacity(0.55),
                Line(core.get_center() + RIGHT * 0.13, core.get_center() + RIGHT * 0.30, color=TEXT_SUB, stroke_width=1.0).set_opacity(0.55),
                Line(core.get_center() + DOWN * 0.20, core.get_center() + DOWN * 0.33, color=TEXT_SUB, stroke_width=1.0).set_opacity(0.45),
            )
            internals.add(spokes, core)

        elif idx == 3 and idx <= active_idx:
            if stage == "overfit":
                good = Line(np.array([pos[0] - 0.42, base_y - 0.06, 0]), np.array([pos[0] - 0.05, base_y + 0.12, 0]), color=SECONDARY, stroke_width=2.0)
                weak = Line(np.array([pos[0] + 0.04, base_y + 0.10, 0]), np.array([pos[0] + 0.42, base_y - 0.10, 0]), color="#E8A838", stroke_width=2.0)
                warn = Text("train ≠ new", font_size=12, color="#E8A838", weight=MEDIUM).move_to(pos + DOWN * 0.31)
                internals.add(good, weak, warn)
            else:
                gauge = Arc(radius=0.26, start_angle=PI, angle=-PI * 0.82, color=TEXT_SUB, stroke_width=1.5).set_opacity(0.55)
                gauge.move_to(np.array([pos[0], base_y - 0.02, 0]))
                needle = Line(np.array([pos[0], base_y - 0.03, 0]), np.array([pos[0] + 0.20, base_y + 0.10, 0]), color=SECONDARY, stroke_width=1.6)
                internals.add(gauge, needle)

        elif idx == 4 and idx <= active_idx:
            monitor = RoundedRectangle(width=0.48, height=0.23, corner_radius=0.04, stroke_color=SECONDARY, stroke_width=1.2, fill_opacity=0)
            monitor.move_to(np.array([pos[0], base_y + 0.03, 0]))
            pulse = VMobject(color=SECONDARY, stroke_width=1.7)
            pulse.set_points_as_corners([
                np.array([pos[0] - 0.19, base_y + 0.02, 0]),
                np.array([pos[0] - 0.06, base_y + 0.02, 0]),
                np.array([pos[0] + 0.00, base_y + 0.12, 0]),
                np.array([pos[0] + 0.07, base_y - 0.04, 0]),
                np.array([pos[0] + 0.19, base_y - 0.04, 0]),
            ])
            internals.add(monitor, pulse)

        internals.set_opacity(op)
        return VGroup(shadow, card, text, internals)

    cards = VGroup()
    for i, label in enumerate(labels):
        card_group = make_card(i, label)
        if i >= shown_count and stage != "intro":
            card_group.set_opacity(0.0)
        cards.add(card_group)

    arrows = VGroup()
    for i in range(4):
        if stage == "intro" or i < shown_count - 1:
            start = np.array([xs[i] + card_w / 2 + 0.12, y, 0])
            end = np.array([xs[i + 1] - card_w / 2 - 0.12, y, 0])
            arr = Arrow(start, end, buff=0.0, color=TEXT_SUB, stroke_width=1.7, tip_length=0.14, max_stroke_width_to_length_ratio=10)
            arr.set_opacity(0.70 if i < active_idx else 0.22)
            arrows.add(arr)

    flows = VGroup()
    if stage in {"clean", "train", "eval", "improve", "monitor"}:
        from_i = max(0, min(active_idx - 1, 3))
        to_i = max(1, min(active_idx, 4))
        for k in range(3):
            dot = Dot(
                np.array([xs[from_i] + 0.55 + k * 0.20, y - 0.62 - 0.04 * (k % 2), 0]),
                radius=0.020,
                color=SECONDARY,
            ).set_opacity(0.62)
            flows.add(dot)
        flow_line = Line(np.array([xs[from_i] + 0.52, y - 0.62, 0]), np.array([xs[to_i] - 0.52, y - 0.62, 0]), color=SECONDARY, stroke_width=1.2).set_opacity(0.32)
        flows.add(flow_line)

    loop = VGroup()
    if stage in {"loop", "final"}:
        bottom_y = y - 1.03
        right_x = xs[4] + 0.40
        left_x = xs[0] - 0.40
        down = Line(np.array([right_x, y - card_h / 2 - 0.08, 0]), np.array([right_x, bottom_y, 0]), color=SECONDARY, stroke_width=1.8).set_opacity(0.72)
        across = Line(np.array([right_x, bottom_y, 0]), np.array([left_x, bottom_y, 0]), color=SECONDARY, stroke_width=1.8).set_opacity(0.72)
        up = Line(np.array([left_x, bottom_y, 0]), np.array([left_x, y - card_h / 2 - 0.08, 0]), color=SECONDARY, stroke_width=1.8).set_opacity(0.72)
        tip = Triangle(color=SECONDARY, fill_color=SECONDARY, fill_opacity=1.0).scale(0.070)
        tip.move_to(np.array([left_x, y - card_h / 2 - 0.05, 0]))
        loop_label = Text("continuous improvement", font_size=17, color=TEXT_SUB, weight=MEDIUM)
        loop_label.move_to(np.array([(left_x + right_x) / 2, bottom_y - 0.24, 0]))
        loop_label.set_opacity(0.68)
        loop.add(down, across, up, tip, loop_label)

    heading = VGroup()
    if params.get("show_heading", stage == "intro"):
        h_text = params.get("heading", "Machine learning is a workflow")
        title = Text(h_text, font_size=34, color=TEXT_MAIN, weight=MEDIUM)
        fit_to_width(title, 9.6)
        title.move_to(np.array([0.0, y + 1.55, 0.0]))
        subtitle = Text("not a one-step algorithm", font_size=20, color=TEXT_SUB)
        subtitle.move_to(title.get_center() + DOWN * 0.42)
        subtitle.set_opacity(0.72)
        heading.add(title, subtitle)

    group = VGroup(heading, arrows, cards, flows, loop)
    place_in_zone(group, zone)
    return group


def make_workflow_loop(params, zone):
    """Scene 7 persistent workflow loop seed.

    The renderer handles progressive mutations for this object. This builder only
    creates the initial unlabeled node so normal object construction remains
    schema-compatible and isolated from the older workflow-cycle/card systems.
    """
    node_pos = _as_vector(params.get("data_pos", [-4.15, 0.65, 0]))
    node_radius = params.get("node_radius", 0.36)

    halo = Circle(radius=node_radius + 0.10, stroke_color=SECONDARY, stroke_width=0.85)
    halo.set_stroke(opacity=0.12)
    halo.move_to(node_pos)

    ring = Circle(radius=node_radius, stroke_color=SECONDARY, stroke_width=1.75)
    ring.set_fill("#0c1624", opacity=0.56)
    ring.move_to(node_pos)

    center_dot = Dot(node_pos, radius=0.045, color=SECONDARY).set_opacity(0.65)
    node = VGroup(halo, ring, center_dot)
    node.workflow_key = "data"

    root = VGroup(node)
    root.workflow_loop_nodes = {"data": node}
    root.workflow_loop_arrows = {}
    root.workflow_loop_effects = VGroup()
    root.workflow_loop_params = params
    return root


def make_road_ahead_field(params, zone):
    horizon_y = params.get("horizon_y", -0.18)
    path_color = params.get("path_color", "#9FB6D8")
    horizon_color = params.get("horizon_color", "#F2F6FF")
    ambient_color = params.get("ambient_color", "#172033")
    point_color = params.get("point_color", "#F8FBFF")

    frame_width = config.frame_width
    frame_height = config.frame_height

    # Abstract perspective-path geometry.  The previous implementation used
    # disconnected horizontal fragments, which rendered as random lines rather
    # than a "road ahead".  This field is still minimal, but it gives the eye a
    # path, a threshold, and a subject to follow.
    vanishing = _as_vector(params.get("vanishing_point", [0.0, horizon_y, 0.0]))
    left_near = _as_vector(params.get("left_near", [-3.95, -3.08, 0.0]))
    right_near = _as_vector(params.get("right_near", [3.95, -3.08, 0.0]))
    left_far = _as_vector(params.get("left_far", [-0.34, horizon_y - 0.02, 0.0]))
    right_far = _as_vector(params.get("right_far", [0.34, horizon_y - 0.02, 0.0]))

    path_fill = Polygon(
        left_near,
        right_near,
        right_far,
        left_far,
        stroke_width=0,
        fill_color=params.get("path_fill_color", "#101A31"),
        fill_opacity=params.get("path_fill_opacity", 0.10),
    )

    path_glow = Polygon(
        left_near + LEFT * 0.18,
        right_near + RIGHT * 0.18,
        right_far + RIGHT * 0.06,
        left_far + LEFT * 0.06,
        stroke_width=0,
        fill_color=params.get("path_glow_color", "#172743"),
        fill_opacity=params.get("path_glow_opacity", 0.055),
    )

    left_edge = Line(left_near, left_far, color=path_color, stroke_width=params.get("edge_width", 1.25))
    right_edge = Line(right_near, right_far, color=path_color, stroke_width=params.get("edge_width", 1.25))
    left_edge.set_stroke(opacity=params.get("edge_opacity", 0.22))
    right_edge.set_stroke(opacity=params.get("edge_opacity", 0.22))

    def interp(a, b, t):
        return a + (b - a) * t

    path_bands = VGroup()
    band_count = params.get("band_count", 6)
    for i in range(band_count):
        t = (i + 1) / (band_count + 1)
        # Nonlinear spacing creates perspective depth: bands compress toward
        # the horizon and feel like structure, not random underlines.
        depth_t = t ** 1.58
        start = interp(left_near, left_far, depth_t)
        end = interp(right_near, right_far, depth_t)
        band = Line(start, end, color=path_color, stroke_width=params.get("band_width", 1.05))
        band.set_stroke(opacity=params.get("band_opacity", 0.13) * (1.0 - 0.08 * i))
        path_bands.add(band)

    uncertainty_particles = VGroup()
    particle_specs = params.get("particle_specs") or [
        [-2.85, -2.26, 0.0], [-1.55, -1.72, 0.0], [-0.62, -2.55, 0.0],
        [1.24, -1.88, 0.0], [2.65, -2.34, 0.0], [0.18, -1.34, 0.0],
        [-2.08, -2.82, 0.0], [2.12, -2.84, 0.0]
    ]
    for j, pos in enumerate(particle_specs):
        dot = Dot(_as_vector(pos), radius=params.get("particle_radius", 0.018), color=path_color)
        dot.set_opacity(params.get("particle_opacity", 0.20) * (0.75 + 0.08 * (j % 4)))
        uncertainty_particles.add(dot)

    upper_height = frame_height / 2 + abs(horizon_y) + 0.35
    upper_ambient = Rectangle(
        width=frame_width + 0.6,
        height=upper_height,
        stroke_width=0,
        fill_color=ambient_color,
        fill_opacity=params.get("upper_ambient_opacity", 0.0),
    )
    upper_ambient.move_to(np.array([0.0, horizon_y + upper_height / 2, 0.0]))

    horizon_half_width = params.get("horizon_half_width", 4.75)
    horizon_glow = Line(
        np.array([-horizon_half_width, horizon_y, 0.0]),
        np.array([horizon_half_width, horizon_y, 0.0]),
        color=horizon_color,
        stroke_width=params.get("horizon_glow_width", 16.0),
    ).set_stroke(opacity=params.get("horizon_glow_opacity", 0.0))
    horizon_bloom = Rectangle(
        width=horizon_half_width * 2.05,
        height=params.get("horizon_bloom_height", 0.52),
        stroke_width=0,
        fill_color=params.get("horizon_bloom_color", "#DDEBFF"),
        fill_opacity=params.get("horizon_bloom_opacity", 0.0),
    )
    horizon_bloom.move_to(np.array([0.0, horizon_y + 0.10, 0.0]))
    horizon_core = Line(
        np.array([-horizon_half_width * 0.40, horizon_y, 0.0]),
        np.array([horizon_half_width * 0.40, horizon_y, 0.0]),
        color=horizon_color,
        stroke_width=params.get("horizon_stroke_width", 1.45),
    ).set_stroke(opacity=params.get("horizon_core_opacity", 0.0))
    horizon_left = Line(
        np.array([-horizon_half_width * 0.40, horizon_y, 0.0]),
        np.array([-horizon_half_width * 0.40, horizon_y, 0.0]),
        color=horizon_color,
        stroke_width=params.get("horizon_wing_width", 1.05),
    ).set_stroke(opacity=params.get("horizon_wing_opacity", 0.0))
    horizon_right = Line(
        np.array([horizon_half_width * 0.40, horizon_y, 0.0]),
        np.array([horizon_half_width * 0.40, horizon_y, 0.0]),
        color=horizon_color,
        stroke_width=params.get("horizon_wing_width", 1.05),
    ).set_stroke(opacity=params.get("horizon_wing_opacity", 0.0))

    point_start = _as_vector(params.get("point_start", [0.0, -1.02, 0.0]))
    point = Dot(point_start, radius=params.get("point_radius", 0.060), color=point_color)
    point.set_opacity(params.get("point_opacity", 0.0))
    point_halo = Circle(radius=params.get("point_halo_radius", 0.20), color=point_color, stroke_width=1.1)
    point_halo.move_to(point_start)
    point_halo.set_stroke(opacity=params.get("point_halo_opacity", 0.0))
    point_halo.set_fill(point_color, opacity=0.0)

    field = VGroup(
        upper_ambient,
        path_glow,
        path_fill,
        path_bands,
        left_edge,
        right_edge,
        uncertainty_particles,
        horizon_bloom,
        horizon_glow,
        horizon_left,
        horizon_right,
        horizon_core,
        point_halo,
        point,
    )
    field.road_lower_lines = path_bands  # backward-compatible alias
    field.road_path_bands = path_bands
    field.road_path_edges = VGroup(left_edge, right_edge)
    field.road_path_fill = path_fill
    field.road_path_glow = path_glow
    field.road_uncertainty_particles = uncertainty_particles
    field.road_upper_ambient = upper_ambient
    field.road_horizon_glow = horizon_glow
    field.road_horizon_bloom = horizon_bloom
    field.road_horizon_core = horizon_core
    field.road_horizon_left = horizon_left
    field.road_horizon_right = horizon_right
    field.road_point = point
    field.road_point_halo = point_halo
    field.road_horizon_y = horizon_y
    field.road_horizon_half_width = horizon_half_width
    field.road_horizon_color = horizon_color
    field.road_line_color = path_color
    field.road_vanishing_point = vanishing
    # full maps to ORIGIN, but avoid moving this absolute-coordinate field for
    # the same reason as Scene 7: geometry and mutations share world coords.
    if zone != "full":
        place_in_zone(field, zone)
    return field


def make_supervised_field(params, zone):
    neutral_color = params.get("neutral_color", "#6F7786")
    warm_color = params.get("warm_color", "#F2A65A")
    cool_color = params.get("cool_color", "#6EA8FE")
    dot_radius = params.get("dot_radius", 0.055)
    dot_opacity = params.get("dot_opacity", 0.62)
    field_scale = params.get("field_scale", 1.0)

    default_points = [
        [-3.95, 1.95, 0], [-3.48, 2.42, 0], [-3.02, 1.56, 0], [-2.62, 2.08, 0],
        [-2.18, 1.18, 0], [-1.72, 2.34, 0], [-1.34, 1.62, 0], [-0.86, 2.02, 0],
        [-0.52, 1.08, 0], [-0.08, 1.70, 0], [0.34, 2.30, 0], [0.72, 1.36, 0],
        [1.18, 1.88, 0], [1.58, 1.06, 0], [2.06, 2.22, 0], [2.48, 1.52, 0],
        [2.94, 2.00, 0], [3.36, 1.18, 0], [3.76, 1.72, 0], [-3.74, 0.72, 0],
        [-3.22, 0.08, 0], [-2.78, 0.82, 0], [-2.24, -0.02, 0], [-1.78, 0.58, 0],
        [-1.22, -0.18, 0], [-0.74, 0.42, 0], [-0.28, -0.34, 0], [0.22, 0.36, 0],
        [0.66, -0.22, 0], [1.10, 0.62, 0], [1.62, -0.08, 0], [2.12, 0.74, 0],
        [2.62, 0.04, 0], [3.18, 0.58, 0], [3.64, -0.12, 0], [-3.52, -1.00, 0],
        [-3.02, -1.72, 0], [-2.42, -0.92, 0], [-1.86, -1.54, 0], [-1.28, -0.82, 0],
        [-0.76, -1.46, 0], [-0.18, -0.76, 0], [0.38, -1.34, 0], [0.92, -0.66, 0],
        [1.46, -1.48, 0], [2.04, -0.82, 0], [2.66, -1.58, 0], [3.24, -0.86, 0],
    ]
    default_classes = [
        "warm", "warm", "warm", "warm", "warm", "warm", "warm", "warm",
        "warm", "warm", "cool", "warm", "cool", "cool", "cool", "cool",
        "cool", "cool", "cool", "warm", "warm", "warm", "warm", "warm",
        "warm", "warm", "warm", "cool", "cool", "cool", "cool", "cool",
        "cool", "cool", "cool", "warm", "warm", "warm", "warm", "warm",
        "warm", "cool", "cool", "cool", "cool", "cool", "cool", "cool",
    ]

    points = params.get("points", default_points)
    classes = params.get("classes", default_classes)
    initial_state = params.get("initial_state", "neutral")

    dots = VGroup()
    for index, point in enumerate(points):
        cls = classes[index] if index < len(classes) else "warm"
        color = neutral_color
        if initial_state == "colored":
            color = warm_color if cls == "warm" else cool_color
        dot = Dot(_as_vector(point), radius=dot_radius, color=color)
        dot.set_opacity(dot_opacity if initial_state == "neutral" else params.get("colored_opacity", 0.96))
        dot.supervised_class = cls
        dot.supervised_neutral_color = neutral_color
        dot.supervised_target_color = warm_color if cls == "warm" else cool_color
        dots.add(dot)

    line_start = _as_vector(params.get("line_start", [-4.85, -2.72, 0]))
    line_end = _as_vector(params.get("line_end", [4.85, 1.62, 0]))
    boundary = Line(
        line_start,
        line_end,
        color=params.get("line_color", "#EAF1FF"),
        stroke_width=params.get("line_stroke_width", 3.0),
    )
    boundary.set_stroke(opacity=params.get("line_opacity", 0.0))
    boundary_glow = Line(
        line_start,
        line_end,
        color=params.get("line_glow_color", "#DCE9FF"),
        stroke_width=params.get("line_glow_width", 8.0),
    )
    boundary_glow.set_stroke(opacity=params.get("line_glow_opacity", 0.0))

    field = VGroup(dots, boundary_glow, boundary)
    field.scale(field_scale)
    place_in_zone(field, zone)

    field.supervised_dots = dots
    field.supervised_boundary = boundary
    field.supervised_boundary_glow = boundary_glow
    field.supervised_params = dict(params)
    field.supervised_points = points
    field.supervised_classes = classes
    field.supervised_neutral_color = neutral_color
    field.supervised_warm_color = warm_color
    field.supervised_cool_color = cool_color
    field.supervised_dot_opacity = dot_opacity
    field.supervised_colored_opacity = params.get("colored_opacity", 0.96)
    field.supervised_dim_opacity = params.get("dim_opacity", 0.55)
    field.supervised_line_start = line_start
    field.supervised_line_end = line_end
    return field

def make_classification_regression_field(params, zone):
    neutral_color = params.get("neutral_color", "#7A8291")
    red_color = params.get("red_color", "#F06A5A")
    blue_color = params.get("blue_color", "#6EA8FE")
    white_color = params.get("white_color", "#F8FBFF")
    axis_color = params.get("axis_color", "#7D8796")
    trend_color = params.get("trend_color", "#F5E4A0")
    boundary_color = params.get("boundary_color", "#EAF1FF")
    read_line_color = params.get("read_line_color", "#8E98A8")
    dot_radius = params.get("dot_radius", 0.058)
    test_radius = params.get("test_dot_radius", 0.125)
    dot_opacity = params.get("dot_opacity", 0.66)
    field_scale = params.get("field_scale", 1.0)
    label_color = params.get("label_color", axis_color)
    label_font_size = params.get("axis_label_font_size", 24)
    line_label_font_size = params.get("line_label_font_size", 22)

    default_points = [
        [-4.05, -1.72, 0], [-3.72, -1.08, 0], [-3.36, -0.48, 0], [-3.10, 0.22, 0], [-2.82, 0.78, 0],
        [-2.46, -1.38, 0], [-2.12, -0.78, 0], [-1.84, -0.12, 0], [-1.58, 0.54, 0], [-1.22, 1.08, 0],
        [-0.92, -1.02, 0], [-0.58, -0.36, 0], [-0.24, 0.28, 0], [0.04, 0.92, 0], [0.42, 1.42, 0],
        [0.72, -0.70, 0], [1.02, -0.04, 0], [1.36, 0.58, 0], [1.72, 1.10, 0], [2.02, 1.70, 0],
        [2.38, -0.30, 0], [2.72, 0.34, 0], [3.02, 0.94, 0], [3.34, 1.46, 0], [3.68, 2.04, 0],
        [-3.86, 0.88, 0], [-2.92, 1.46, 0], [-1.02, 0.10, 0], [1.86, 0.08, 0], [3.42, 0.52, 0],
        [4.02, 1.36, 0],
    ]
    default_classes = [
        "red", "red", "red", "red", "red",
        "red", "red", "red", "red", "red",
        "red", "red", "red", "blue", "blue",
        "blue", "blue", "blue", "blue", "blue",
        "blue", "blue", "blue", "blue", "blue",
        "red", "red", "red", "blue", "blue",
        "blue",
    ]
    points = params.get("points", default_points)
    classes = params.get("classes", default_classes)

    dots = VGroup()
    for index, point in enumerate(points):
        cls = classes[index] if index < len(classes) else ("red" if point[0] < 0 else "blue")
        dot = Dot(_as_vector(point), radius=dot_radius, color=neutral_color)
        dot.set_opacity(dot_opacity)
        dot.cr_class = cls
        dot.cr_neutral_color = neutral_color
        dot.cr_target_color = red_color if cls == "red" else blue_color
        dots.add(dot)

    boundary_start = _as_vector(params.get("boundary_start", [-0.55, -2.35, 0]))
    boundary_end = _as_vector(params.get("boundary_end", [0.72, 2.35, 0]))
    boundary = Line(boundary_start, boundary_end, color=boundary_color, stroke_width=params.get("boundary_width", 3.0))
    boundary.set_stroke(opacity=0.0)
    boundary_label_text = params.get("boundary_label", "decision boundary")
    boundary_label = Text(boundary_label_text, font_size=line_label_font_size, color=boundary_color, weight=MEDIUM)
    boundary_label.next_to(boundary_end, RIGHT, buff=0.16)
    boundary_label.set_opacity(0.0)

    origin = _as_vector(params.get("axis_origin", [-4.35, -2.2, 0]))
    x_end = _as_vector(params.get("x_axis_end", [4.45, -2.2, 0]))
    y_end = _as_vector(params.get("y_axis_end", [-4.35, 2.35, 0]))
    x_axis = Line(origin, x_end, color=axis_color, stroke_width=params.get("axis_width", 2.0))
    y_axis = Line(origin, y_end, color=axis_color, stroke_width=params.get("axis_width", 2.0))
    x_axis.set_stroke(opacity=0.0)
    y_axis.set_stroke(opacity=0.0)
    x_label = Text(params.get("x_axis_label", "Hours"), font_size=label_font_size, color=label_color, weight=MEDIUM)
    x_label.next_to(x_end, UP, buff=0.16)
    y_label = Text(params.get("y_axis_label", "Marks"), font_size=label_font_size, color=label_color, weight=MEDIUM)
    y_label.next_to(y_end, RIGHT, buff=0.16)
    x_label.set_opacity(0.0)
    y_label.set_opacity(0.0)

    ticks = VGroup()
    for x in params.get("x_ticks", [-2.8, -1.2, 0.4, 2.0, 3.6]):
        tick = Line([x, origin[1] - 0.07, 0], [x, origin[1] + 0.07, 0], color=axis_color, stroke_width=1.2)
        tick.set_stroke(opacity=0.0)
        ticks.add(tick)
    for y in params.get("y_ticks", [-1.15, -0.1, 0.95, 2.0]):
        tick = Line([origin[0] - 0.07, y, 0], [origin[0] + 0.07, y, 0], color=axis_color, stroke_width=1.2)
        tick.set_stroke(opacity=0.0)
        ticks.add(tick)

    trend_points = [_as_vector(p) for p in params.get("trend_points", [[-3.45, -1.30, 0], [-1.75, -0.52, 0], [0.05, 0.30, 0], [1.85, 1.03, 0], [3.45, 1.68, 0]])]
    trend_line = VMobject(color=trend_color)
    trend_line.set_points_smoothly(trend_points)
    trend_line.set_stroke(width=params.get("trend_width", 3.9), opacity=0.0)
    trend_label = Text(params.get("trend_label", "fit"), font_size=line_label_font_size, color=trend_color, weight=MEDIUM)
    trend_label.next_to(trend_points[-1], RIGHT, buff=0.18)
    trend_label.set_opacity(0.0)

    test_start = _as_vector(params.get("test_point", [-0.02, 0.20, 0]))
    test_dot = Dot(test_start, radius=test_radius, color=white_color)
    test_dot.set_opacity(0.0)
    test_glow = Circle(radius=params.get("test_glow_radius", test_radius * 2.15), color=white_color, stroke_width=params.get("test_glow_width", 2.0))
    test_glow.move_to(test_start)
    test_glow.set_stroke(opacity=0.0)
    test_glow.set_fill(opacity=0.0)
    test_dot.cr_glow = test_glow
    test_dot.cr_white_color = white_color
    test_dot.cr_blue_color = blue_color
    test_dot.cr_class_position = _as_vector(params.get("test_classified_point", [0.48, 0.22, 0]))
    test_dot.cr_axis_position = _as_vector(params.get("test_axis_point", [1.25, origin[1], 0]))
    test_dot.cr_intersection = _as_vector(params.get("test_intersection", [1.25, 0.88, 0]))

    vertical_read = DashedLine(test_dot.cr_axis_position, test_dot.cr_intersection, color=read_line_color, dash_length=0.09, stroke_width=params.get("read_line_width", 1.7))
    horizontal_read = DashedLine(test_dot.cr_intersection, [origin[0], test_dot.cr_intersection[1], 0], color=read_line_color, dash_length=0.09, stroke_width=params.get("read_line_width", 1.7))
    vertical_read.set_stroke(opacity=0.0)
    horizontal_read.set_stroke(opacity=0.0)
    prediction_marker = Dot([origin[0], test_dot.cr_intersection[1], 0], radius=params.get("prediction_marker_radius", 0.055), color=read_line_color)
    prediction_marker.set_opacity(0.0)

    field = VGroup(dots, boundary, boundary_label, x_axis, y_axis, x_label, y_label, ticks, trend_line, trend_label, vertical_read, horizontal_read, prediction_marker, test_glow, test_dot)
    field.scale(field_scale)
    place_in_zone(field, zone)

    field.cr_dots = dots
    field.cr_boundary = boundary
    field.cr_boundary_label = boundary_label
    field.cr_x_axis = x_axis
    field.cr_y_axis = y_axis
    field.cr_x_label = x_label
    field.cr_y_label = y_label
    field.cr_ticks = ticks
    field.cr_trend_line = trend_line
    field.cr_trend_points = trend_points
    field.cr_trend_color = trend_color
    field.cr_trend_width = params.get("trend_width", 3.9)
    field.cr_trend_label = trend_label
    field.cr_vertical_read = vertical_read
    field.cr_horizontal_read = horizontal_read
    field.cr_prediction_marker = prediction_marker
    field.cr_test_glow = test_glow
    field.cr_test_dot = test_dot
    field.cr_params = dict(params)
    field.cr_neutral_color = neutral_color
    field.cr_red_color = red_color
    field.cr_blue_color = blue_color
    field.cr_white_color = white_color
    field.cr_dot_opacity = dot_opacity
    field.cr_colored_opacity = params.get("colored_opacity", 0.94)
    field.cr_axis_opacity = params.get("axis_opacity", 0.52)
    field.cr_tick_opacity = params.get("tick_opacity", 0.45)
    field.cr_axis_label_opacity = params.get("axis_label_opacity", 0.68)
    field.cr_boundary_label_opacity = params.get("boundary_label_opacity", 0.64)
    field.cr_trend_label_opacity = params.get("trend_label_opacity", 0.76)
    field.cr_test_glow_opacity = params.get("test_glow_opacity", 0.22)
    field.cr_prediction_marker_opacity = params.get("prediction_marker_opacity", 0.86)
    field.cr_boundary_opacity = params.get("boundary_opacity", 0.84)
    field.cr_trend_opacity = params.get("trend_opacity", 0.92)
    field.cr_read_opacity = params.get("read_opacity", 0.62)
    return field


def transition_in_for(obj, transition_name: str):
    if transition_name in {"none", "smooth"}:
        return FadeIn(obj)
    if transition_name == "fade":
        return FadeIn(obj)
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


def make_linear_formula_system(params, zone):
    """Build the stateful visual system for Video 3 Scene 4.

    Scene 4 explains the formula as geometry: one persistent equation and one
    persistent line controlled by slope/weight and intercept/bias trackers.
    The renderer owns all timing and beat-specific mutation.
    """
    equation_color = params.get("equation_color", "#F8FAFC")
    dim_color = params.get("dim_color", "#94A3B8")
    axis_color = params.get("axis_color", "#7C8798")
    line_color = params.get("line_color", "#4A9EFF")
    yhat_color = params.get("yhat_color", "#4A9EFF")
    point_color = params.get("point_color", "#FF6B6B")
    bias_color = params.get("bias_color", "#FFD166")
    connector_color = params.get("connector_color", "#FFD166")
    label_color = params.get("label_color", "#CBD5E1")

    plot_width = float(params.get("plot_width", 7.8))
    plot_height = float(params.get("plot_height", 3.7))
    origin = _as_vector(params.get("origin", [-3.9, -2.55, 0.0]))
    x_min, x_max = params.get("x_range", [0.0, 10.0])
    y_min, y_max = params.get("y_range", [0.0, 10.0])

    def c2p(x, y):
        px = origin[0] + (float(x) - x_min) / (x_max - x_min) * plot_width
        py = origin[1] + (float(y) - y_min) / (y_max - y_min) * plot_height
        return np.array([px, py, 0.0])

    equation = MathTex(
        r"\hat{y}", "=", "w", "x", "+", "b",
        font_size=int(params.get("equation_font_size", 72)),
        color=equation_color,
    )
    equation.move_to(_as_vector(params.get("equation_home", [0.0, 2.35, 0.0])))
    fit_to_width(equation, float(params.get("equation_max_width", 6.7)))
    term_map = {
        "yhat": equation[0],
        "equals": equation[1],
        "w": equation[2],
        "x": equation[3],
        "plus": equation[4],
        "b": equation[5],
    }
    for term in equation:
        term.set_opacity(float(params.get("equation_rest_opacity", 0.58)))

    slope_tracker = ValueTracker(float(params.get("initial_slope", 0.62)))
    intercept_tracker = ValueTracker(float(params.get("initial_intercept", 1.35)))
    line_progress = ValueTracker(0.0)
    line_opacity = ValueTracker(0.0)
    line_width = ValueTracker(float(params.get("line_width", 3.0)))
    prediction_drop_progress = ValueTracker(0.0)
    prediction_drop_opacity = ValueTracker(0.0)
    prediction_dot_opacity = ValueTracker(0.0)
    x_tick_opacity = ValueTracker(0.0)
    x_rise_progress = ValueTracker(0.0)
    x_rise_opacity = ValueTracker(0.0)
    intercept_opacity = ValueTracker(0.0)
    error_hint_opacity = ValueTracker(0.0)
    wb_cue_opacity = ValueTracker(0.0)

    def model_y(x):
        return slope_tracker.get_value() * float(x) + intercept_tracker.get_value()

    def clipped_line_points():
        m = slope_tracker.get_value()
        b = intercept_tracker.get_value()
        candidates = []
        for x in (x_min, x_max):
            y = m * x + b
            if y_min <= y <= y_max:
                candidates.append((x, y))
        if abs(m) > 1e-8:
            for y in (y_min, y_max):
                x = (y - b) / m
                if x_min <= x <= x_max:
                    candidates.append((x, y))
        unique = []
        for item in candidates:
            if not any(abs(item[0] - other[0]) < 1e-6 and abs(item[1] - other[1]) < 1e-6 for other in unique):
                unique.append(item)
        if len(unique) < 2:
            unique = [(x_min, max(y_min, min(y_max, model_y(x_min)))), (x_max, max(y_min, min(y_max, model_y(x_max))))]
        unique.sort(key=lambda item: item[0])
        start = c2p(*unique[0])
        end = c2p(*unique[-1])
        progress = max(0.0, min(1.0, line_progress.get_value()))
        return start, start + (end - start) * progress

    def make_live_line():
        start, end = clipped_line_points()
        line = Line(start, end, color=line_color, stroke_width=line_width.get_value())
        line.set_opacity(line_opacity.get_value())
        return line

    live_line = always_redraw(make_live_line)

    x_axis = Line(c2p(x_min, y_min), c2p(x_max, y_min), color=axis_color, stroke_width=1.45)
    y_axis = Line(c2p(x_min, y_min), c2p(x_min, y_max), color=axis_color, stroke_width=1.45)
    x_tip = Triangle(color=axis_color, fill_opacity=0.8, stroke_width=0).scale(0.065).rotate(-90 * DEGREES).move_to(c2p(x_max, y_min))
    y_tip = Triangle(color=axis_color, fill_opacity=0.8, stroke_width=0).scale(0.065).move_to(c2p(x_min, y_max))
    ticks = VGroup()
    for tx in (2.5, 5.0, 7.5):
        ticks.add(Line(c2p(tx, y_min), c2p(tx, y_min) + UP * 0.065, color=axis_color, stroke_width=1.0).set_opacity(0.55))
    for ty in (2.5, 5.0, 7.5):
        ticks.add(Line(c2p(x_min, ty), c2p(x_min, ty) + RIGHT * 0.065, color=axis_color, stroke_width=1.0).set_opacity(0.55))
    x_label = Text(params.get("x_label_text", "Study Hours"), font_size=18, color=label_color)
    x_label.next_to(x_axis, DOWN, buff=0.18)
    y_label = Text(params.get("y_label_text", "Marks"), font_size=18, color=label_color).rotate(90 * DEGREES)
    y_label.next_to(y_axis, LEFT, buff=0.22)
    axes = VGroup(x_axis, y_axis, x_tip, y_tip, ticks, x_label, y_label)

    prediction_x = float(params.get("prediction_x", 6.2))
    real_y = float(params.get("real_y", 7.1))
    real_point = Dot(c2p(prediction_x, real_y), radius=0.095, color=point_color, fill_opacity=1.0)
    real_point.set_stroke(color="#FFFFFF", width=0.8, opacity=0.24)
    real_point.set_opacity(0.0)

    def make_prediction_drop():
        x = prediction_x
        start = c2p(x, real_y)
        target = c2p(x, max(y_min, min(y_max, model_y(x))))
        progress = max(0.0, min(1.0, prediction_drop_progress.get_value()))
        end = start + (target - start) * progress
        drop = DashedLine(start, end, dash_length=0.08, dashed_ratio=0.58, color=point_color, stroke_width=1.55)
        drop.set_opacity(prediction_drop_opacity.get_value())
        return drop

    def make_prediction_dot():
        dot = Dot(c2p(prediction_x, max(y_min, min(y_max, model_y(prediction_x)))), radius=0.105, color=yhat_color, fill_opacity=1.0)
        dot.set_stroke(color="#FFFFFF", width=0.8, opacity=0.20)
        dot.set_opacity(prediction_dot_opacity.get_value())
        return dot

    prediction_drop = always_redraw(make_prediction_drop)
    prediction_dot = always_redraw(make_prediction_dot)

    lookup_x = float(params.get("lookup_x", 4.7))

    def make_x_tick():
        tick = Line(c2p(lookup_x, y_min) + DOWN * 0.095, c2p(lookup_x, y_min) + UP * 0.14, color=equation_color, stroke_width=2.3)
        tick.set_opacity(x_tick_opacity.get_value() * 0.82)
        return tick

    def make_x_rise():
        start = c2p(lookup_x, y_min)
        target = c2p(lookup_x, max(y_min, min(y_max, model_y(lookup_x))))
        progress = max(0.0, min(1.0, x_rise_progress.get_value()))
        rise = Line(start, start + (target - start) * progress, color=equation_color, stroke_width=2.4)
        rise.set_opacity(x_rise_opacity.get_value() * 0.72)
        return rise

    def make_x_input_dot():
        dot = Dot(c2p(lookup_x, y_min), radius=0.065, color=equation_color, fill_opacity=1.0)
        dot.set_stroke(color=line_color, width=0.8, opacity=0.28)
        dot.set_opacity(x_tick_opacity.get_value() * 0.82)
        return dot

    x_tick = always_redraw(make_x_tick)
    x_rise = always_redraw(make_x_rise)
    x_input_dot = always_redraw(make_x_input_dot)

    def make_intercept_marker():
        y = max(y_min, min(y_max, intercept_tracker.get_value()))
        marker = Dot(c2p(x_min, y), radius=0.105, color=bias_color, fill_opacity=1.0)
        marker.set_stroke(color="#FFFFFF", width=0.8, opacity=0.22)
        marker.set_opacity(intercept_opacity.get_value())
        return marker

    intercept_marker = always_redraw(make_intercept_marker)

    raw_scatter = params.get("scatter_points", [
        [1.0, 2.0], [1.8, 2.9], [2.7, 3.2], [3.6, 4.6],
        [4.8, 4.5], [5.9, 5.9], [7.0, 6.2], [8.4, 7.6],
    ])
    scatter = VGroup(*[
        Dot(c2p(x, y), radius=0.085, color=point_color, fill_opacity=0.86).set_stroke(color="#FFFFFF", width=0.6, opacity=0.18)
        for x, y in raw_scatter
    ])
    for dot in scatter:
        dot.set_opacity(0.0)

    selected_error_points = raw_scatter[2:7:2]

    def make_error_hints():
        hints = VGroup()
        for x, y in selected_error_points:
            start = c2p(x, y)
            end = c2p(x, max(y_min, min(y_max, model_y(x))))
            hint = DashedLine(start, end, dash_length=0.055, dashed_ratio=0.55, color=point_color, stroke_width=1.1)
            hint.set_opacity(error_hint_opacity.get_value() * 0.42)
            hints.add(hint)
        return hints

    error_hints = always_redraw(make_error_hints)

    def make_term_box(term_name):
        box = SurroundingRectangle(term_map[term_name], buff=0.075, color=connector_color, corner_radius=0.04, stroke_width=1.8)
        box.set_opacity(wb_cue_opacity.get_value())
        return box

    w_box = always_redraw(lambda: make_term_box("w"))
    b_box = always_redraw(lambda: make_term_box("b"))

    def make_wb_connector():
        start = term_map["w"].get_bottom() + DOWN * 0.08
        end = term_map["b"].get_bottom() + DOWN * 0.08
        conn = CubicBezier(start, start + DOWN * 0.18, end + DOWN * 0.18, end)
        conn.set_stroke(color=connector_color, width=1.15, opacity=wb_cue_opacity.get_value() * 0.72)
        return conn

    wb_connector = always_redraw(make_wb_connector)

    field = VGroup(
        equation, axes, live_line, real_point, prediction_drop, prediction_dot,
        x_tick, x_rise, x_input_dot, intercept_marker, scatter, error_hints, w_box, b_box, wb_connector,
    )
    field.lf_equation = equation
    field.lf_terms = term_map
    field.lf_equation_home = equation.get_center().copy()
    field.lf_equation_final = _as_vector(params.get("equation_final", [0.0, 3.05, 0.0]))
    field.lf_dim_color = dim_color
    field.lf_equation_color = equation_color
    field.lf_yhat_color = yhat_color
    field.lf_line_color = line_color
    field.lf_point_color = point_color
    field.lf_bias_color = bias_color
    field.lf_axes = axes
    field.lf_x_axis = x_axis
    field.lf_y_axis = y_axis
    field.lf_axis_extras = VGroup(x_tip, y_tip, ticks, x_label, y_label)
    field.lf_live_line = live_line
    field.lf_slope = slope_tracker
    field.lf_intercept = intercept_tracker
    field.lf_initial_slope = float(params.get("initial_slope", 0.62))
    field.lf_initial_intercept = float(params.get("initial_intercept", 1.35))
    field.lf_demo_slope_high = float(params.get("demo_slope_high", 0.92))
    field.lf_demo_slope_low = float(params.get("demo_slope_low", 0.42))
    field.lf_demo_intercept_high = float(params.get("demo_intercept_high", 2.35))
    field.lf_demo_intercept_low = float(params.get("demo_intercept_low", 0.65))
    field.lf_line_progress = line_progress
    field.lf_line_opacity = line_opacity
    field.lf_line_width = line_width
    field.lf_prediction_drop_progress = prediction_drop_progress
    field.lf_prediction_drop_opacity = prediction_drop_opacity
    field.lf_prediction_dot_opacity = prediction_dot_opacity
    field.lf_x_tick_opacity = x_tick_opacity
    field.lf_x_rise_progress = x_rise_progress
    field.lf_x_rise_opacity = x_rise_opacity
    field.lf_intercept_opacity = intercept_opacity
    field.lf_error_hint_opacity = error_hint_opacity
    field.lf_wb_cue_opacity = wb_cue_opacity
    field.lf_real_point = real_point
    field.lf_prediction_drop = prediction_drop
    field.lf_prediction_dot = prediction_dot
    field.lf_x_tick = x_tick
    field.lf_x_rise = x_rise
    field.lf_x_input_dot = x_input_dot
    field.lf_intercept_marker = intercept_marker
    field.lf_scatter = scatter
    field.lf_error_hints = error_hints
    field.lf_w_box = w_box
    field.lf_b_box = b_box
    field.lf_wb_connector = wb_connector
    field.lf_c2p = c2p
    field.lf_model_y = model_y
    field.lf_params = params
    return field


def make_error_minimization_system(params, zone):
    """Build the stateful visual system for Video 3 Scene 5.

    Scene 5 explains error minimization with one persistent graph: data points,
    a live regression line, residual bars, squared-error areas, and a cost
    indicator. Renderer beat logic owns timing and mutation.
    """
    axis_color = params.get("axis_color", "#7C8798")
    point_color = params.get("point_color", "#E5E7EB")
    focus_color = params.get("focus_color", "#FFFFFF")
    line_color = params.get("line_color", "#4A9EFF")
    residual_color = params.get("residual_color", "#FF6B6B")
    square_color = params.get("square_color", "#FF6B6B")
    label_color = params.get("label_color", "#F8FAFC")
    muted_label_color = params.get("muted_label_color", "#CBD5E1")
    cost_color = params.get("cost_color", "#4A9EFF")
    warning_color = params.get("warning_color", "#FFD166")

    plot_width = float(params.get("plot_width", 8.6))
    plot_height = float(params.get("plot_height", 5.15))
    origin = _as_vector(params.get("origin", [-4.3, -2.55, 0.0]))
    x_min, x_max = params.get("x_range", [0.0, 10.0])
    y_min, y_max = params.get("y_range", [0.0, 10.0])

    raw_points = params.get("points", [
        [1.0, 2.0], [1.7, 3.0], [2.4, 2.7], [3.2, 4.5],
        [4.0, 4.0], [4.9, 5.7], [5.8, 5.4], [6.7, 6.9],
        [7.6, 6.8], [8.6, 8.2],
    ])
    focus_index = int(params.get("focus_index", 7))
    focus_index = max(0, min(len(raw_points) - 1, focus_index))
    largest_index = int(params.get("largest_square_index", 2))
    largest_index = max(0, min(len(raw_points) - 1, largest_index))

    def c2p(x, y):
        px = origin[0] + (float(x) - x_min) / (x_max - x_min) * plot_width
        py = origin[1] + (float(y) - y_min) / (y_max - y_min) * plot_height
        return np.array([px, py, 0.0])

    def clamp_y(y):
        return max(y_min, min(y_max, float(y)))

    slope_tracker = ValueTracker(float(params.get("initial_slope", 0.46)))
    intercept_tracker = ValueTracker(float(params.get("initial_intercept", 1.55)))
    line_opacity = ValueTracker(0.0)
    line_width = ValueTracker(float(params.get("line_width", 3.15)))
    focus_pulse = ValueTracker(0.0)
    focus_ring_opacity = ValueTracker(0.0)
    focus_bar_progress = ValueTracker(0.0)
    focus_bar_opacity = ValueTracker(0.0)
    error_label_opacity = ValueTracker(0.0)
    y_labels_opacity = ValueTracker(0.0)
    sign_emphasis_opacity = ValueTracker(0.0)
    all_bar_progress = ValueTracker(0.0)
    all_bar_opacity = ValueTracker(0.0)
    square_progress = ValueTracker(0.0)
    square_stroke_opacity = ValueTracker(0.0)
    square_fill_reveal = ValueTracker(0.0)
    square_opacity = ValueTracker(0.0)
    large_square_pulse = ValueTracker(0.0)
    formula_opacity = ValueTracker(0.0)
    vocab_opacity = ValueTracker(0.0)
    cost_opacity = ValueTracker(0.0)
    cost_value = ValueTracker(float(params.get("initial_cost", 18.7)))
    overfit_hint_opacity = ValueTracker(0.0)

    def model_y(x):
        return slope_tracker.get_value() * float(x) + intercept_tracker.get_value()

    def clipped_line_points():
        m = slope_tracker.get_value()
        b = intercept_tracker.get_value()
        candidates = []
        for x in (x_min, x_max):
            y = m * x + b
            if y_min <= y <= y_max:
                candidates.append((x, y))
        if abs(m) > 1e-8:
            for y in (y_min, y_max):
                x = (y - b) / m
                if x_min <= x <= x_max:
                    candidates.append((x, y))
        unique = []
        for item in candidates:
            if not any(abs(item[0] - other[0]) < 1e-6 and abs(item[1] - other[1]) < 1e-6 for other in unique):
                unique.append(item)
        if len(unique) < 2:
            unique = [(x_min, clamp_y(model_y(x_min))), (x_max, clamp_y(model_y(x_max)))]
        unique.sort(key=lambda item: item[0])
        return c2p(*unique[0]), c2p(*unique[-1])

    x_axis = Line(c2p(x_min, y_min), c2p(x_max, y_min), color=axis_color, stroke_width=1.35)
    y_axis = Line(c2p(x_min, y_min), c2p(x_min, y_max), color=axis_color, stroke_width=1.35)
    ticks = VGroup()
    for tx in (2.5, 5.0, 7.5):
        ticks.add(Line(c2p(tx, y_min), c2p(tx, y_min) + UP * 0.06, color=axis_color, stroke_width=0.9).set_opacity(0.45))
    for ty in (2.5, 5.0, 7.5):
        ticks.add(Line(c2p(x_min, ty), c2p(x_min, ty) + RIGHT * 0.06, color=axis_color, stroke_width=0.9).set_opacity(0.45))
    axes = VGroup(x_axis, y_axis, ticks).set_opacity(float(params.get("axis_opacity", 0.72)))

    dots = VGroup()
    for i, (x, y) in enumerate(raw_points):
        color = focus_color if i == focus_index else point_color
        radius = float(params.get("point_radius", 0.085)) * (1.15 if i == focus_index else 1.0)
        dot = Dot(c2p(x, y), radius=radius, color=color, fill_opacity=0.92)
        dot.set_stroke(color="#FFFFFF", width=0.65, opacity=0.22)
        dots.add(dot)

    def make_focus_ring():
        x, y = raw_points[focus_index]
        pulse = max(0.0, min(1.0, focus_pulse.get_value()))
        ring = Circle(radius=0.18 + 0.13 * pulse, color=focus_color, stroke_width=1.7)
        ring.move_to(c2p(x, y))
        ring.set_opacity(focus_ring_opacity.get_value() * (1.0 - pulse))
        return ring

    focus_ring = always_redraw(make_focus_ring)

    def make_live_line():
        start, end = clipped_line_points()
        line = Line(start, end, color=line_color, stroke_width=line_width.get_value())
        line.set_opacity(line_opacity.get_value())
        return line

    live_line = always_redraw(make_live_line)

    def residual_endpoints(index):
        x, y = raw_points[index]
        point = c2p(x, y)
        pred = c2p(x, clamp_y(model_y(x)))
        return point, pred

    def make_focus_bar():
        start, target = residual_endpoints(focus_index)
        progress = max(0.0, min(1.0, focus_bar_progress.get_value()))
        end = start + (target - start) * progress
        bar = Line(start, end, color=residual_color, stroke_width=2.7)
        bar.set_opacity(focus_bar_opacity.get_value())
        return bar

    focus_bar = always_redraw(make_focus_bar)

    focus_x, focus_y = raw_points[focus_index]
    error_label = Text(params.get("error_label_text", "Error"), font_size=22, color=residual_color)
    error_label.move_to(c2p(focus_x + 0.65, (focus_y + model_y(focus_x)) / 2.0))
    error_label.set_opacity(0.0)

    y_label = MathTex("y", font_size=30, color=label_color)
    yhat_label = MathTex(r"\hat{y}", font_size=30, color=line_color)
    error_expr = MathTex(r"y - \hat{y}", font_size=34, color=residual_color)
    y_label.move_to(c2p(focus_x - 0.35, focus_y + 0.28))
    yhat_label.move_to(c2p(focus_x - 0.42, clamp_y(model_y(focus_x)) - 0.32))
    error_expr.move_to(c2p(focus_x + 0.82, (focus_y + model_y(focus_x)) / 2.0))
    labels_group = VGroup(y_label, yhat_label, error_expr).set_opacity(0.0)

    residual_bars = VGroup()
    for index, (x, y) in enumerate(raw_points):
        def make_bar(i=index):
            start, target = residual_endpoints(i)
            progress = max(0.0, min(1.0, all_bar_progress.get_value()))
            end = start + (target - start) * progress
            emphasis = 1.0
            if i in (1, 7):
                emphasis += 0.45 * sign_emphasis_opacity.get_value()
            bar = Line(start, end, color=residual_color, stroke_width=1.55 + (0.75 * sign_emphasis_opacity.get_value() if i in (1, 7) else 0.0))
            bar.set_opacity(all_bar_opacity.get_value() * (0.65 if i != focus_index else 0.9) * emphasis)
            return bar
        residual_bars.add(always_redraw(make_bar))

    residual_squares = VGroup()
    square_fill_opacity = float(params.get("square_fill_opacity", 0.13))
    square_stroke_opacity_max = float(params.get("square_stroke_opacity", 0.62))
    for index, (x, y) in enumerate(raw_points):
        def make_square(i=index):
            start, target = residual_endpoints(i)
            h = abs(target[1] - start[1])
            direction = RIGHT if start[0] < origin[0] + plot_width * 0.55 else LEFT
            progress = max(0.0, min(1.0, square_progress.get_value()))
            width = h * progress
            y_low = min(start[1], target[1])
            y_high = max(start[1], target[1])
            if direction is RIGHT:
                pts = [np.array([start[0], y_low, 0]), np.array([start[0] + width, y_low, 0]), np.array([start[0] + width, y_high, 0]), np.array([start[0], y_high, 0])]
            else:
                pts = [np.array([start[0], y_low, 0]), np.array([start[0] - width, y_low, 0]), np.array([start[0] - width, y_high, 0]), np.array([start[0], y_high, 0])]
            poly = Polygon(*pts, color=square_color, stroke_width=1.05 + (0.9 * large_square_pulse.get_value() if i == largest_index else 0.0))
            opacity_boost = 0.28 * large_square_pulse.get_value() if i == largest_index else 0.0
            poly.set_fill(square_color, opacity=square_opacity.get_value() * square_fill_reveal.get_value() * (square_fill_opacity + opacity_boost))
            poly.set_stroke(square_color, opacity=square_opacity.get_value() * (square_stroke_opacity.get_value() * square_stroke_opacity_max + opacity_boost))
            return poly
        residual_squares.add(always_redraw(make_square))

    mse_formula = MathTex(r"\mathrm{MSE}=\frac{1}{n}\sum (y-\hat{y})^2", font_size=36, color=label_color)
    mse_formula.to_corner(UL, buff=0.48)
    mse_formula.set_opacity(0.0)
    loss_label = Text("Loss", font_size=22, color=muted_label_color)
    cost_word = Text("Cost", font_size=24, color=cost_color, weight=BOLD)
    loss_label.next_to(mse_formula, DOWN, aligned_edge=LEFT, buff=0.18)
    cost_word.next_to(loss_label, RIGHT, buff=0.45)
    vocab_group = VGroup(loss_label, cost_word).set_opacity(0.0)

    cost_label = Text("Cost", font_size=22, color=muted_label_color)
    cost_number = DecimalNumber(cost_value.get_value(), num_decimal_places=1, font_size=34, color=cost_color)
    cost_number.add_updater(lambda mob: mob.set_value(cost_value.get_value()))
    cost_group = VGroup(cost_label, cost_number).arrange(RIGHT, buff=0.18)
    cost_group.to_corner(UR, buff=0.52)
    cost_group.set_opacity(0.0)

    def make_overfit_hint():
        x, y = raw_points[-1]
        start = c2p(x, y)
        target = c2p(x, clamp_y(model_y(x)))
        hint = DashedLine(start, target, dash_length=0.055, dashed_ratio=0.58, color=warning_color, stroke_width=1.35)
        hint.set_opacity(overfit_hint_opacity.get_value() * 0.58)
        return hint

    overfit_hint = always_redraw(make_overfit_hint)

    field = VGroup(
        axes, residual_squares, residual_bars, dots, focus_ring, live_line, focus_bar,
        error_label, labels_group, mse_formula, vocab_group, cost_group, overfit_hint,
    )
    field.em_axes = axes
    field.em_dots = dots
    field.em_focus_ring = focus_ring
    field.em_live_line = live_line
    field.em_focus_bar = focus_bar
    field.em_error_label = error_label
    field.em_y_labels = labels_group
    field.em_residual_bars = residual_bars
    field.em_residual_squares = residual_squares
    field.em_mse_formula = mse_formula
    field.em_vocab_group = vocab_group
    field.em_cost_group = cost_group
    field.em_cost_number = cost_number
    field.em_overfit_hint = overfit_hint
    field.em_slope = slope_tracker
    field.em_intercept = intercept_tracker
    field.em_line_opacity = line_opacity
    field.em_line_width = line_width
    field.em_focus_pulse = focus_pulse
    field.em_focus_ring_opacity = focus_ring_opacity
    field.em_focus_bar_progress = focus_bar_progress
    field.em_focus_bar_opacity = focus_bar_opacity
    field.em_error_label_opacity = error_label_opacity
    field.em_y_labels_opacity = y_labels_opacity
    field.em_sign_emphasis_opacity = sign_emphasis_opacity
    field.em_all_bar_progress = all_bar_progress
    field.em_all_bar_opacity = all_bar_opacity
    field.em_square_progress = square_progress
    field.em_square_stroke_opacity = square_stroke_opacity
    field.em_square_fill_reveal = square_fill_reveal
    field.em_square_opacity = square_opacity
    field.em_large_square_pulse = large_square_pulse
    field.em_formula_opacity = formula_opacity
    field.em_vocab_opacity = vocab_opacity
    field.em_cost_opacity = cost_opacity
    field.em_cost_value = cost_value
    field.em_overfit_hint_opacity = overfit_hint_opacity
    field.em_initial_slope = float(params.get("initial_slope", 0.46))
    field.em_initial_intercept = float(params.get("initial_intercept", 1.55))
    field.em_step1_slope = float(params.get("step1_slope", 0.55))
    field.em_step1_intercept = float(params.get("step1_intercept", 1.25))
    field.em_step2_slope = float(params.get("step2_slope", 0.64))
    field.em_step2_intercept = float(params.get("step2_intercept", 1.02))
    field.em_final_slope = float(params.get("final_slope", 0.72))
    field.em_final_intercept = float(params.get("final_intercept", 0.82))
    field.em_overfit_slope = float(params.get("overfit_slope", 0.82))
    field.em_overfit_intercept = float(params.get("overfit_intercept", 0.45))
    field.em_cost_steps = params.get("cost_steps", [18.7, 11.4, 6.8, 2.1, 1.4, 1.6])
    field.em_params = params
    field.em_c2p = c2p
    field.em_model_y = model_y
    field.em_raw_points = raw_points
    return field


def make_regularization_lasso_system(params, zone):
    """Build the stateful visual system for Video 3 Scene 6.

    Scene 6 explains overfitting, regularization, and Lasso feature selection
    through one evolving system: a regression curve relaxes into a coefficient
    bar chart, lambda applies pressure, and weak bars collapse into ghosts.
    """
    axis_color = params.get("axis_color", "#7C8798")
    point_color = params.get("point_color", "#E5E7EB")
    line_color = params.get("line_color", "#4A9EFF")
    overfit_color = params.get("overfit_color", "#FF6B6B")
    bar_color = params.get("bar_color", "#4A9EFF")
    survivor_color = params.get("survivor_color", "#7DD3FC")
    ghost_color = params.get("ghost_color", "#CBD5E1")
    lambda_color = params.get("lambda_color", "#FFD166")
    label_color = params.get("label_color", "#F8FAFC")
    muted_color = params.get("muted_label_color", "#CBD5E1")

    plot_width = float(params.get("plot_width", 8.25))
    plot_height = float(params.get("plot_height", 4.55))
    origin = _as_vector(params.get("origin", [-4.15, -2.25, 0.0]))
    x_min, x_max = params.get("x_range", [0.0, 9.0])
    y_min, y_max = params.get("y_range", [0.0, 6.0])

    raw_points = params.get("points", [
        [0.8, 1.5], [1.6, 2.3], [2.4, 2.1], [3.2, 3.5], [4.2, 3.2],
        [5.1, 4.7], [6.0, 4.1], [7.1, 5.5], [8.0, 5.2],
    ])
    smooth_points = params.get("smooth_curve", [
        [0.45, 1.25], [1.6, 1.85], [2.8, 2.42], [4.0, 3.0], [5.2, 3.55], [6.5, 4.18], [8.35, 5.05],
    ])
    overfit_points = params.get("overfit_curve", [
        [0.45, 1.1], [0.8, 1.5], [1.25, 2.65], [1.6, 2.3], [2.05, 1.68], [2.4, 2.1],
        [2.95, 3.95], [3.2, 3.5], [3.75, 2.8], [4.2, 3.2], [4.65, 5.2], [5.1, 4.7],
        [5.55, 3.55], [6.0, 4.1], [6.55, 5.85], [7.1, 5.5], [7.55, 4.75], [8.0, 5.2], [8.35, 5.35],
    ])
    calm_points = params.get("calm_curve", [
        [0.45, 1.35], [1.9, 2.02], [3.3, 2.7], [4.8, 3.38], [6.3, 4.08], [8.35, 4.95],
    ])

    def c2p(x, y):
        px = origin[0] + (float(x) - x_min) / (x_max - x_min) * plot_width
        py = origin[1] + (float(y) - y_min) / (y_max - y_min) * plot_height
        return np.array([px, py, 0.0])

    def sample_path(points, n=72):
        pts = [np.array(p, dtype=float) for p in points]
        if len(pts) < 2:
            pts = [np.array([x_min, y_min], dtype=float), np.array([x_max, y_max], dtype=float)]
        seg_lengths = [float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(len(pts) - 1)]
        total = sum(seg_lengths) or 1.0
        samples = []
        for k in range(n):
            d = total * k / max(1, n - 1)
            acc = 0.0
            for i, seg in enumerate(seg_lengths):
                if acc + seg >= d or i == len(seg_lengths) - 1:
                    t = 0.0 if seg == 0 else (d - acc) / seg
                    point = pts[i] + (pts[i + 1] - pts[i]) * t
                    samples.append(point)
                    break
                acc += seg
        return samples

    smooth_samples = sample_path(smooth_points)
    overfit_samples = sample_path(overfit_points)
    calm_samples = sample_path(calm_points)

    points_opacity = ValueTracker(0.0)
    curve_opacity = ValueTracker(0.0)
    curve_draw_progress = ValueTracker(0.0)
    overfit_progress = ValueTracker(0.0)
    regularize_progress = ValueTracker(0.0)
    bar_chart_opacity = ValueTracker(0.0)
    formula_opacity = ValueTracker(0.0)
    lambda_value = ValueTracker(float(params.get("lambda_start", 0.0)))
    lambda_opacity = ValueTracker(0.0)
    final_dim = ValueTracker(1.0)
    overfit_label_opacity = ValueTracker(0.0)

    x_axis = Line(c2p(x_min, y_min), c2p(x_max, y_min), color=axis_color, stroke_width=1.2)
    y_axis = Line(c2p(x_min, y_min), c2p(x_min, y_max), color=axis_color, stroke_width=1.2)
    axes = VGroup(x_axis, y_axis).set_opacity(float(params.get("axis_opacity", 0.58)))

    dots = VGroup()
    for x, y in raw_points:
        dot = Dot(c2p(x, y), radius=float(params.get("point_radius", 0.075)), color=point_color, fill_opacity=0.9)
        dot.set_stroke("#FFFFFF", width=0.45, opacity=0.18)
        dots.add(dot)
    dots.set_opacity(0.0)
    dots.add_updater(lambda mob: mob.set_opacity(points_opacity.get_value() * final_dim.get_value()))

    def make_curve():
        overfit = max(0.0, min(1.0, overfit_progress.get_value()))
        regularize = max(0.0, min(1.0, regularize_progress.get_value()))
        draw = max(0.0, min(1.0, curve_draw_progress.get_value()))
        count = max(2, int(2 + draw * (len(smooth_samples) - 2)))
        coords = []
        for i in range(count):
            base = smooth_samples[i]
            bend = base + (overfit_samples[i] - base) * overfit
            calm = bend + (calm_samples[i] - bend) * regularize
            coords.append(c2p(calm[0], calm[1]))
        curve = VMobject()
        curve.set_points_smoothly(coords)
        color = interpolate_color(line_color, overfit_color, overfit * (1.0 - 0.55 * regularize))
        curve.set_stroke(color=color, width=float(params.get("curve_width", 3.2)), opacity=curve_opacity.get_value() * final_dim.get_value())
        return curve

    curve = always_redraw(make_curve)

    overfit_label = Text("Overfitting", font_size=30, color=overfit_color, weight=BOLD)
    overfit_label.move_to(_as_vector(params.get("overfit_label_pos", [2.6, 2.05, 0.0])))
    overfit_label.set_opacity(0.0)

    bar_origin = _as_vector(params.get("bar_origin", [-3.45, -2.22, 0.0]))
    bar_width = float(params.get("bar_width", 0.55))
    bar_gap = float(params.get("bar_gap", 0.42))
    bar_scale = float(params.get("bar_scale", 1.0))
    initial_heights = [float(v) for v in params.get("initial_bar_heights", [2.7, 1.4, 3.1, 0.9, 2.3, 1.1])]
    compressed_heights = [float(v) for v in params.get("compressed_bar_heights", [2.25, 0.75, 2.55, 0.38, 1.85, 0.55])]
    final_heights = [float(v) for v in params.get("final_bar_heights", [1.9, 0.0, 2.35, 0.0, 1.45, 0.0])]
    collapse_order = [int(i) for i in params.get("collapse_order", [3, 5, 1])]
    bar_trackers = [ValueTracker(0.0) for _ in initial_heights]
    ghost_opacities = [ValueTracker(0.0) for _ in initial_heights]
    survivor_indices = [i for i, value in enumerate(final_heights) if value > 0.0]

    baseline = Line(bar_origin + LEFT * 0.3, bar_origin + RIGHT * ((bar_width + bar_gap) * len(initial_heights) - bar_gap + 0.3), color=axis_color, stroke_width=1.25)
    baseline.set_opacity(0.0)
    baseline.add_updater(lambda mob: mob.set_opacity(bar_chart_opacity.get_value() * 0.72 * final_dim.get_value()))

    bars = VGroup()
    ghosts = VGroup()
    for i, height_tracker in enumerate(bar_trackers):
        x_left = bar_origin[0] + i * (bar_width + bar_gap)
        x_center = x_left + bar_width / 2.0

        def make_bar(index=i, tracker=height_tracker, x0=x_left):
            h = max(0.0, tracker.get_value()) * bar_scale
            rect = Rectangle(width=bar_width, height=max(0.001, h), stroke_width=0.0)
            rect.set_fill(survivor_color if index in survivor_indices else bar_color, opacity=0.88 * bar_chart_opacity.get_value() * final_dim.get_value())
            rect.move_to(np.array([x0 + bar_width / 2.0, bar_origin[1] + h / 2.0, 0.0]))
            return rect

        def make_ghost(index=i, x0=x_left):
            memory_h = max(initial_heights[index] * bar_scale, 0.18)
            ghost = Rectangle(width=bar_width, height=memory_h, color=ghost_color, stroke_width=1.25)
            ghost.set_fill(ghost_color, opacity=0.0)
            ghost.set_stroke(ghost_color, opacity=ghost_opacities[index].get_value() * final_dim.get_value())
            ghost.move_to(np.array([x0 + bar_width / 2.0, bar_origin[1] + memory_h / 2.0, 0.0]))
            return ghost

        bars.add(always_redraw(make_bar))
        ghosts.add(always_redraw(make_ghost))

    bar_labels = VGroup()
    for i in range(len(initial_heights)):
        label = Text(f"w{i + 1}", font_size=18, color=muted_color)
        label.move_to(np.array([bar_origin[0] + i * (bar_width + bar_gap) + bar_width / 2.0, bar_origin[1] - 0.28, 0.0]))
        bar_labels.add(label)
    bar_labels.set_opacity(0.0)
    bar_labels.add_updater(lambda mob: mob.set_opacity(bar_chart_opacity.get_value() * 0.62 * final_dim.get_value()))

    formula_terms = VGroup(
        MathTex("J=", font_size=38, color=label_color),
        MathTex(r"\mathrm{MSE}", font_size=38, color=label_color),
        MathTex("+", font_size=38, color=label_color),
        MathTex(r"\lambda\sum |w|", font_size=38, color=label_color),
    ).arrange(RIGHT, buff=0.18)
    formula_terms.move_to(_as_vector(params.get("formula_pos", [0.0, 2.58, 0.0])))
    formula_terms.set_opacity(0.0)

    lambda_label = MathTex(r"\lambda=", font_size=34, color=lambda_color)
    lambda_number = DecimalNumber(lambda_value.get_value(), num_decimal_places=1, font_size=34, color=lambda_color)
    lambda_number.add_updater(lambda mob: mob.set_value(lambda_value.get_value()))
    lambda_group = VGroup(lambda_label, lambda_number).arrange(RIGHT, buff=0.12)
    lambda_group.move_to(_as_vector(params.get("lambda_pos", [3.85, 2.25, 0.0])))
    lambda_group.set_opacity(0.0)
    lambda_group.add_updater(lambda mob: mob.set_opacity(lambda_opacity.get_value() * final_dim.get_value()))

    system = VGroup(axes, dots, curve, overfit_label, baseline, ghosts, bars, bar_labels, formula_terms, lambda_group)
    system.rl_axes = axes
    system.rl_dots = dots
    system.rl_curve = curve
    system.rl_overfit_label = overfit_label
    system.rl_baseline = baseline
    system.rl_bars = bars
    system.rl_ghosts = ghosts
    system.rl_bar_labels = bar_labels
    system.rl_formula_terms = formula_terms
    system.rl_lambda_group = lambda_group
    system.rl_points_opacity = points_opacity
    system.rl_curve_opacity = curve_opacity
    system.rl_curve_draw_progress = curve_draw_progress
    system.rl_overfit_progress = overfit_progress
    system.rl_regularize_progress = regularize_progress
    system.rl_bar_chart_opacity = bar_chart_opacity
    system.rl_formula_opacity = formula_opacity
    system.rl_lambda_value = lambda_value
    system.rl_lambda_opacity = lambda_opacity
    system.rl_final_dim = final_dim
    system.rl_overfit_label_opacity = overfit_label_opacity
    system.rl_bar_trackers = bar_trackers
    system.rl_ghost_opacities = ghost_opacities
    system.rl_initial_heights = initial_heights
    system.rl_compressed_heights = compressed_heights
    system.rl_final_heights = final_heights
    system.rl_collapse_order = collapse_order
    system.rl_lambda_mid = float(params.get("lambda_mid", 0.9))
    system.rl_lambda_high = float(params.get("lambda_high", 1.8))
    system.rl_params = params
    return system


def make_linear_regression_fit(params, zone):
    """Build the redesigned stateful visual system for Video 3 Scene 3.

    The renderer owns timing. This builder owns deterministic geometry,
    clipped line rendering, semantic colors, labels, captions, and trackers.
    """
    point_color = params.get("point_color", "#F5E6C8")
    point_bright_color = params.get("point_bright_color", "#FFF3D8")
    axis_color = params.get("axis_color", "#7C8798")
    wrong_line_color = params.get("wrong_line_color", "#F4A261")
    search_line_color = params.get("line_color", "#5BC0EB")
    final_line_color = params.get("final_line_color", "#38BDF8")
    residual_color = params.get("residual_color", "#FF6B8A")
    residual_final_color = params.get("residual_final_color", "#B98995")
    label_color = params.get("label_color", "#F8FAFC")
    caption_color = params.get("caption_color", "#CBD5E1")

    plot_width = float(params.get("plot_width", 8.2))
    plot_height = float(params.get("plot_height", 4.8))
    origin = _as_vector(params.get("origin", [-4.15, -2.25, 0.0]))
    x_min, x_max = params.get("x_range", [0.0, 10.0])
    y_min, y_max = params.get("y_range", [0.0, 10.0])

    raw_points = params.get("points", [
        [1.0, 2.0], [1.6, 2.7], [2.3, 3.1], [3.0, 3.0],
        [3.8, 4.4], [4.5, 4.1], [5.2, 5.2], [5.9, 5.0],
        [6.6, 6.4], [7.2, 6.2], [8.0, 7.4], [8.7, 7.1],
    ])

    def c2p(x, y):
        px = origin[0] + (float(x) - x_min) / (x_max - x_min) * plot_width
        py = origin[1] + (float(y) - y_min) / (y_max - y_min) * plot_height
        return np.array([px, py, 0.0])

    def p2c(point):
        x = x_min + (point[0] - origin[0]) / plot_width * (x_max - x_min)
        y = y_min + (point[1] - origin[1]) / plot_height * (y_max - y_min)
        return x, y

    def interpolate_hex(c1, c2, alpha):
        color_1 = ManimColor(c1).to_rgb()
        color_2 = ManimColor(c2).to_rgb()
        rgb = tuple((1 - alpha) * color_1[i] + alpha * color_2[i] for i in range(3))
        return ManimColor(rgb)

    point_radius = float(params.get("point_radius", 0.13))
    dots = VGroup(*[
        Dot(c2p(x, y), radius=point_radius, color=point_color, fill_opacity=1.0)
        .set_stroke(color="#FFFFFF", width=0.8, opacity=0.18)
        for x, y in raw_points
    ])

    axis_width = float(params.get("axis_width", 1.7))
    x_axis = Line(c2p(x_min, y_min), c2p(x_max, y_min), color=axis_color, stroke_width=axis_width)
    y_axis = Line(c2p(x_min, y_min), c2p(x_min, y_max), color=axis_color, stroke_width=axis_width)
    x_tip = Triangle(color=axis_color, fill_opacity=0.85, stroke_width=0).scale(0.075).rotate(-90 * DEGREES).move_to(c2p(x_max, y_min))
    y_tip = Triangle(color=axis_color, fill_opacity=0.85, stroke_width=0).scale(0.075).move_to(c2p(x_min, y_max))
    origin_dot = Dot(c2p(x_min, y_min), radius=0.035, color=axis_color, fill_opacity=0.85)
    tick_marks = VGroup()
    for tx in (2.5, 5.0, 7.5):
        tick_marks.add(Line(c2p(tx, y_min), c2p(tx, y_min) + UP * 0.07, color=axis_color, stroke_width=1.0).set_opacity(0.55))
    for ty in (2.5, 5.0, 7.5):
        tick_marks.add(Line(c2p(x_min, ty), c2p(x_min, ty) + RIGHT * 0.07, color=axis_color, stroke_width=1.0).set_opacity(0.55))
    axes = VGroup(x_axis, y_axis, x_tip, y_tip, origin_dot, tick_marks)

    title = Text(params.get("title_text", "Linear Regression"), font_size=38, weight=BOLD, color=label_color)
    title.to_corner(UL, buff=0.45)
    subtitle = Text(params.get("subtitle_text", "Finding the best-fit line"), font_size=21, color=caption_color)
    subtitle.next_to(title, DOWN, aligned_edge=LEFT, buff=0.12)
    x_label = Text(params.get("x_label_text", "Hours studied"), font_size=20, color=label_color)
    x_label.next_to(x_axis, DOWN, buff=0.25)
    y_label = Text(params.get("y_label_text", "Marks achieved"), font_size=20, color=label_color).rotate(90 * DEGREES)
    y_label.next_to(y_axis, LEFT, buff=0.26)
    data_caption = Text(params.get("data_caption_text", "Each dot = one student"), font_size=20, color=caption_color)
    data_caption.move_to(c2p(7.15, 1.05))
    trend_caption = Text(params.get("trend_caption_text", "Upward trend"), font_size=22, color=point_bright_color)
    trend_caption.move_to(c2p(7.15, 8.35))
    guess_label = Text(params.get("guess_label_text", "Rough guess"), font_size=22, color=wrong_line_color)
    guess_label.move_to(c2p(7.0, 8.9))
    adjust_label = Text(params.get("adjust_label_text", "Adjusting slope + intercept"), font_size=21, color=search_line_color)
    adjust_label.move_to(c2p(5.7, 8.65))
    residual_label = Text(params.get("residual_label_text", "Residual = error"), font_size=22, color=residual_color)
    residual_label.move_to(c2p(6.55, 1.35))
    best_fit_label = Text(params.get("best_fit_label_text", "Best-fit line"), font_size=22, color=final_line_color)
    best_fit_label.move_to(c2p(7.45, 7.2))
    formula_teaser = Text(params.get("formula_text", "y = mx + b"), font_size=30, color=label_color)
    formula_teaser.to_corner(UR, buff=0.55)
    formula_caption = Text(params.get("formula_caption_text", "Next: the equation behind the line"), font_size=17, color=caption_color)
    formula_caption.next_to(formula_teaser, DOWN, buff=0.12)
    labels = VGroup(title, subtitle, x_label, y_label, data_caption, trend_caption, guess_label, adjust_label, residual_label, best_fit_label, formula_teaser, formula_caption)

    slope_tracker = ValueTracker(float(params.get("initial_slope", 1.05)))
    intercept_tracker = ValueTracker(float(params.get("initial_intercept", 0.65)))
    line_progress = ValueTracker(0.0)
    line_opacity = ValueTracker(0.0)
    line_width = ValueTracker(float(params.get("line_width", 2.8)))
    line_color_mix = ValueTracker(0.0)  # 0=wrong amber, .5=search cyan, 1=final blue

    residual_progress = [ValueTracker(0.0) for _ in raw_points]
    residual_opacity = [ValueTracker(0.0) for _ in raw_points]
    residual_desaturation = ValueTracker(0.0)

    def model_y(x):
        return slope_tracker.get_value() * x + intercept_tracker.get_value()

    def clipped_line_points():
        m = slope_tracker.get_value()
        b = intercept_tracker.get_value()
        candidates = []
        for x in (x_min, x_max):
            y = m * x + b
            if y_min <= y <= y_max:
                candidates.append((x, y))
        if abs(m) > 1e-8:
            for y in (y_min, y_max):
                x = (y - b) / m
                if x_min <= x <= x_max:
                    candidates.append((x, y))
        unique = []
        for item in candidates:
            if not any(abs(item[0] - other[0]) < 1e-6 and abs(item[1] - other[1]) < 1e-6 for other in unique):
                unique.append(item)
        if len(unique) < 2:
            unique = [(x_min, max(y_min, min(y_max, model_y(x_min)))), (x_max, max(y_min, min(y_max, model_y(x_max))))]
        unique.sort(key=lambda item: item[0])
        start = c2p(*unique[0])
        end = c2p(*unique[-1])
        progress = max(0.0, min(1.0, line_progress.get_value()))
        current_end = start + (end - start) * progress
        return start, current_end

    def current_line_color():
        mix = max(0.0, min(1.0, line_color_mix.get_value()))
        if mix <= 0.5:
            return interpolate_hex(wrong_line_color, search_line_color, mix / 0.5)
        return interpolate_hex(search_line_color, final_line_color, (mix - 0.5) / 0.5)

    def make_live_line():
        start, end = clipped_line_points()
        line = Line(start, end, color=current_line_color(), stroke_width=line_width.get_value())
        line.set_opacity(line_opacity.get_value())
        return line

    live_line = always_redraw(make_live_line)

    residuals = VGroup()
    for index, (x, y) in enumerate(raw_points):
        def make_residual(i=index, px=x, py=y):
            start = c2p(px, py)
            target_y = max(y_min, min(y_max, model_y(px)))
            target = c2p(px, target_y)
            progress = max(0.0, min(1.0, residual_progress[i].get_value()))
            end = start + (target - start) * progress
            color = interpolate_hex(residual_color, residual_final_color, residual_desaturation.get_value())
            dash = DashedLine(
                start,
                end,
                dash_length=float(params.get("residual_dash_length", 0.09)),
                dashed_ratio=float(params.get("residual_dashed_ratio", 0.58)),
                color=color,
                stroke_width=float(params.get("residual_width", 1.25)),
            )
            dash.set_opacity(residual_opacity[i].get_value())
            return dash
        residuals.add(always_redraw(make_residual))

    trend_line = Line(c2p(1.0, 2.05), c2p(8.8, 7.35), color=point_bright_color, stroke_width=8)
    trend_line.set_opacity(0.0)

    if params.get("use_vignette", True):
        vignette = Ellipse(
            width=float(params.get("vignette_width", 9.8)),
            height=float(params.get("vignette_height", 6.0)),
            color=params.get("vignette_color", "#172238"),
            fill_color=params.get("vignette_color", "#172238"),
            fill_opacity=float(params.get("vignette_opacity", 0.13)),
            stroke_width=0,
        )
        vignette.move_to(c2p(5.0, 5.0))
    else:
        vignette = VGroup()

    field = VGroup(vignette, axes, trend_line, dots, live_line, residuals, labels)
    field.lr_vignette = vignette
    field.lr_axes = axes
    field.lr_x_axis = x_axis
    field.lr_y_axis = y_axis
    field.lr_x_tip = x_tip
    field.lr_y_tip = y_tip
    field.lr_origin_dot = origin_dot
    field.lr_tick_marks = tick_marks
    field.lr_dots = dots
    field.lr_point_order = sorted(list(dots), key=lambda d: (d.get_center()[0], d.get_center()[1]))
    field.lr_live_line = live_line
    field.lr_residuals = residuals
    field.lr_trend_line = trend_line
    field.lr_title = title
    field.lr_subtitle = subtitle
    field.lr_x_label = x_label
    field.lr_y_label = y_label
    field.lr_data_caption = data_caption
    field.lr_trend_caption = trend_caption
    field.lr_guess_label = guess_label
    field.lr_adjust_label = adjust_label
    field.lr_residual_label = residual_label
    field.lr_best_fit_label = best_fit_label
    field.lr_formula_teaser = formula_teaser
    field.lr_formula_caption = formula_caption
    field.lr_all_labels = labels
    field.lr_slope = slope_tracker
    field.lr_intercept = intercept_tracker
    field.lr_line_progress = line_progress
    field.lr_line_opacity = line_opacity
    field.lr_line_width = line_width
    field.lr_line_color_mix = line_color_mix
    field.lr_residual_progress = residual_progress
    field.lr_residual_opacity = residual_opacity
    field.lr_residual_desaturation = residual_desaturation
    field.lr_point_color = point_color
    field.lr_point_bright_color = point_bright_color
    field.lr_final_slope = float(params.get("final_slope", 0.68))
    field.lr_final_intercept = float(params.get("final_intercept", 1.35))
    field.lr_near_slope = float(params.get("near_slope", 0.78))
    field.lr_near_intercept = float(params.get("near_intercept", 0.95))
    field.lr_overshoot_slope = float(params.get("overshoot_slope", 0.58))
    field.lr_overshoot_intercept = float(params.get("overshoot_intercept", 1.65))
    field.lr_c2p = c2p
    field.lr_p2c = p2c
    field.lr_raw_points = raw_points
    field.lr_params = params
    return field

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

    if action in {"show_manual_rule_card", "transform_manual_rule_card"}:
        return make_manual_rule_card(params, zone)

    if action == "show_manual_rule_ghosts":
        return make_manual_rule_ghosts(params, zone)

    if action == "show_axis_free_curve":
        return make_axis_free_curve(params, zone)

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

    if action == "show_taxonomy_field":
        return make_taxonomy_field(params, zone)

    if action == "show_workflow_cycle":
        return make_workflow_cycle(params, zone)

    if action == "show_workflow_pipeline":
        return make_workflow_pipeline(params, zone)

    if action == "show_workflow_loop":
        return make_workflow_loop(params, zone)

    if action == "show_road_ahead_field":
        return make_road_ahead_field(params, zone)

    if action == "show_supervised_field":
        return make_supervised_field(params, zone)

    if action == "show_classification_regression_field":
        return make_classification_regression_field(params, zone)

    if action == "show_linear_regression_fit":
        return make_linear_regression_fit(params, zone)

    if action == "show_linear_formula_system":
        return make_linear_formula_system(params, zone)

    if action == "show_error_minimization_system":
        return make_error_minimization_system(params, zone)

    if action == "show_regularization_lasso_system":
        return make_regularization_lasso_system(params, zone)

    if action == "fade_out":
        return None

    raise ValueError(f"Unsupported action: {action}")