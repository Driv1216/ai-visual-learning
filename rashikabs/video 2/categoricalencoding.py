from manim import *

BG       = "#0F0F0F"
CREAM    = "#F2EFE7"
ACCENT   = "#4A9EFF"
DIM_TEXT = "#555555"
GOLD     = "#FFD166"
WARN     = "#FF6B6B"
GREEN    = "#06D6A0"
PURPLE   = "#C084FC"


# ── cleaned + imputed data (just Location & Furnished) ────────────────
LOCATIONS  = ["Mumbai", "Mumbai", "Mumbai", "Pune", "Pune", "Delhi", "Delhi"]
FURNISHED  = ["Yes",    "No",     "Yes",    "Yes",  "No",   "Yes",   "No"]
IDS        = ["101",    "102",    "103",    "104",  "105",  "106",   "107"]


def lbl_bg(text, color=GOLD):
    t = Text(text, font_size=17, color=color, font="Courier New")
    t.to_edge(DOWN, buff=0.45)
    bg = BackgroundRectangle(t, color="#000000", fill_opacity=1, buff=0.12)
    return VGroup(bg, t)


# ─────────────────────────────────────────────────────────────────────
#  HELPER: build a simple 2-column table  (ID | col_a | col_b)
# ─────────────────────────────────────────────────────────────────────
def build_two_col_table(col_a_header, col_b_header,
                        col_a_vals, col_b_vals,
                        col_a_colors=None, col_b_colors=None,
                        width=5.5):
    COL_WIDTHS = [0.60, 1.30, 1.30]
    ROW_HEIGHT = 0.50
    FONT_HDR   = 14
    FONT_CELL  = 13

    headers   = ["ID", col_a_header, col_b_header]
    data_rows = [[IDS[i], col_a_vals[i], col_b_vals[i]]
                 for i in range(len(IDS))]
    all_rows  = [headers] + data_rows

    TABLE_W = sum(COL_WIDTHS)
    TABLE_H = ROW_HEIGHT * len(all_rows)
    ox = -TABLE_W / 2
    oy =  TABLE_H / 2

    cell_grid = []
    line_mobs = []

    for r_idx, row in enumerate(all_rows):
        cell_row = []
        x_cur = ox
        for c_idx, txt in enumerate(row):
            cw = COL_WIDTHS[c_idx]
            cx = x_cur + cw / 2
            cy = oy - r_idx * ROW_HEIGHT - ROW_HEIGHT / 2
            is_hdr = (r_idx == 0)

            if is_hdr:
                color = ACCENT
            elif c_idx == 1 and col_a_colors:
                color = col_a_colors[r_idx - 1]
            elif c_idx == 2 and col_b_colors:
                color = col_b_colors[r_idx - 1]
            else:
                color = CREAM

            mob = Text(txt,
                       font_size=FONT_HDR if is_hdr else FONT_CELL,
                       color=color, font="Courier New")
            mob.move_to([cx, cy, 0])
            cell_row.append(mob)
            x_cur += cw
        cell_grid.append(cell_row)

    for r_idx in range(len(all_rows) + 1):
        y  = oy - r_idx * ROW_HEIGHT
        lw = 2.0 if r_idx in (0, 1) else 0.8
        c  = ACCENT if r_idx in (0, 1) else DIM_TEXT
        line_mobs.append(Line([ox, y, 0], [ox + TABLE_W, y, 0],
                               color=c, stroke_width=lw))
    x_cur = ox
    for c_idx in range(len(COL_WIDTHS) + 1):
        lw = 2.0 if c_idx in (0, len(COL_WIDTHS)) else 0.8
        c  = ACCENT if c_idx in (0, len(COL_WIDTHS)) else DIM_TEXT
        line_mobs.append(Line([x_cur, oy, 0], [x_cur, oy - TABLE_H, 0],
                               color=c, stroke_width=lw))
        if c_idx < len(COL_WIDTHS):
            x_cur += COL_WIDTHS[c_idx]

    header_bg = Rectangle(width=TABLE_W, height=ROW_HEIGHT,
                           fill_color="#0D1B2A", fill_opacity=1,
                           stroke_width=0)
    header_bg.move_to([0, oy - ROW_HEIGHT / 2, 0])

    all_lines = VGroup(*line_mobs)
    all_cells = VGroup(*[m for row in cell_grid for m in row])
    tbl = VGroup(header_bg, all_lines, all_cells)
    tbl.scale_to_fit_width(width).center()
    return tbl, cell_grid


# ─────────────────────────────────────────────────────────────────────
#  HELPER: one-hot table  (ID | Loc_Mumbai | Loc_Pune | Loc_Delhi)
# ─────────────────────────────────────────────────────────────────────
def build_onehot_table(width=7.0):
    COL_WIDTHS = [0.50, 1.10, 1.00, 1.00]
    ROW_HEIGHT = 0.50
    FONT_HDR   = 13
    FONT_CELL  = 13

    headers = ["ID", "Loc_Mumbai", "Loc_Pune", "Loc_Delhi"]

    # one-hot encode LOCATIONS
    onehot = []
    for loc in LOCATIONS:
        onehot.append([
            "1" if loc == "Mumbai" else "0",
            "1" if loc == "Pune"   else "0",
            "1" if loc == "Delhi"  else "0",
        ])

    data_rows = [[IDS[i]] + onehot[i] for i in range(len(IDS))]
    all_rows  = [headers] + data_rows

    TABLE_W = sum(COL_WIDTHS)
    TABLE_H = ROW_HEIGHT * len(all_rows)
    ox = -TABLE_W / 2
    oy =  TABLE_H / 2

    cell_grid = []
    line_mobs = []

    for r_idx, row in enumerate(all_rows):
        cell_row = []
        x_cur = ox
        for c_idx, txt in enumerate(row):
            cw = COL_WIDTHS[c_idx]
            cx = x_cur + cw / 2
            cy = oy - r_idx * ROW_HEIGHT - ROW_HEIGHT / 2
            is_hdr = (r_idx == 0)

            if is_hdr:
                color = ACCENT
            elif c_idx > 0 and not is_hdr:
                color = GREEN if txt == "1" else DIM_TEXT
            else:
                color = CREAM

            mob = Text(txt,
                       font_size=FONT_HDR if is_hdr else FONT_CELL,
                       color=color, font="Courier New")
            mob.move_to([cx, cy, 0])
            cell_row.append(mob)
            x_cur += cw
        cell_grid.append(cell_row)

    for r_idx in range(len(all_rows) + 1):
        y  = oy - r_idx * ROW_HEIGHT
        lw = 2.0 if r_idx in (0, 1) else 0.8
        c  = ACCENT if r_idx in (0, 1) else DIM_TEXT
        line_mobs.append(Line([ox, y, 0], [ox + TABLE_W, y, 0],
                               color=c, stroke_width=lw))
    x_cur = ox
    for c_idx in range(len(COL_WIDTHS) + 1):
        lw = 2.0 if c_idx in (0, len(COL_WIDTHS)) else 0.8
        c  = ACCENT if c_idx in (0, len(COL_WIDTHS)) else DIM_TEXT
        line_mobs.append(Line([x_cur, oy, 0], [x_cur, oy - TABLE_H, 0],
                               color=c, stroke_width=lw))
        if c_idx < len(COL_WIDTHS):
            x_cur += COL_WIDTHS[c_idx]

    header_bg = Rectangle(width=TABLE_W, height=ROW_HEIGHT,
                           fill_color="#0D1B2A", fill_opacity=1,
                           stroke_width=0)
    header_bg.move_to([0, oy - ROW_HEIGHT / 2, 0])

    all_lines = VGroup(*line_mobs)
    all_cells = VGroup(*[m for row in cell_grid for m in row])
    tbl = VGroup(header_bg, all_lines, all_cells)
    tbl.scale_to_fit_width(width).center()
    return tbl, cell_grid


# ═════════════════════════════════════════════════════════════════════
#  MAIN SCENE
# ═════════════════════════════════════════════════════════════════════
class CategoricalEncoding(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── TITLE ─────────────────────────────────────────────────────
        title = Text("Categorical Data & Encoding", font_size=26,
                     color=CREAM, font="Courier New")
        title.to_edge(UP, buff=0.4)
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  OPENING — show Location + Furnished table
        # ═══════════════════════════════════════════════════════════════
        tbl, cg = build_two_col_table(
            "Location", "Furnished",
            LOCATIONS, FURNISHED,
        )
        tbl.shift(DOWN * 0.3)

        intro = lbl_bg(
            "Models need numbers — not words like 'Yes' or 'Mumbai'")
        self.play(FadeIn(tbl), run_time=0.7)
        self.play(FadeIn(intro), run_time=0.4)
        self.wait(15)
        self.play(FadeOut(intro), run_time=0.3)

        # ═══════════════════════════════════════════════════════════════
        #  PART 1 — LABEL ENCODING: Furnished  (Yes→1, No→0)
        # ═══════════════════════════════════════════════════════════════
        lbl1 = lbl_bg("Label Encoding  —  Furnished:  Yes → 1,  No → 0")
        self.play(FadeIn(lbl1), run_time=0.4)

        # Highlight the Furnished column header
        furn_hdr = cg[0][2]
        self.play(furn_hdr.animate.set_color(GOLD), run_time=0.3)
        self.wait(10)

        # Animate each cell: fade out word, fade in number
        furn_map = {"Yes": "1", "No": "0"}
        furn_num_color = {"Yes": GREEN, "No": WARN}

        for r_idx, val in enumerate(FURNISHED, start=1):
            old_cell = cg[r_idx][2]
            num_str  = furn_map[val]
            new_cell = Text(num_str, font_size=13,
                            color=furn_num_color[val],
                            font="Courier New")
            new_cell.move_to(old_cell.get_center())
            self.play(FadeOut(old_cell, shift=UP * 0.07),
                      run_time=0.25)
            self.play(FadeIn(new_cell, shift=UP * 0.07),
                      run_time=0.25)
            cg[r_idx][2] = new_cell

        self.wait(12)
        self.play(FadeOut(lbl1), run_time=0.3)

        # ═══════════════════════════════════════════════════════════════
        #  PART 2 — LABEL ENCODING: Location  (Mumbai→0, Pune→1, Delhi→2)
        # ═══════════════════════════════════════════════════════════════
        lbl2 = lbl_bg(
            "Label Encoding  —  Location:  Mumbai→0,  Pune→1,  Delhi→2")
        self.play(FadeIn(lbl2), run_time=0.4)

        loc_hdr = cg[0][1]
        self.play(loc_hdr.animate.set_color(GOLD), run_time=0.3)
        self.wait(8)

        loc_map   = {"Mumbai": "0", "Pune": "1", "Delhi": "2"}
        loc_color = {"Mumbai": ACCENT, "Pune": PURPLE, "Delhi": GOLD}

        for r_idx, val in enumerate(LOCATIONS, start=1):
            old_cell = cg[r_idx][1]
            num_str  = loc_map[val]
            new_cell = Text(num_str, font_size=13,
                            color=loc_color[val],
                            font="Courier New")
            new_cell.move_to(old_cell.get_center())
            self.play(FadeOut(old_cell, shift=UP * 0.07), run_time=0.25)
            self.play(FadeIn(new_cell, shift=UP * 0.07),  run_time=0.25)
            cg[r_idx][1] = new_cell

        self.wait(8)

        # Show the problem with label encoding
        problem = lbl_bg(
            "Problem: implies Delhi(2) > Pune(1) > Mumbai(0) — but there is no order!",
            color=WARN)
        self.play(FadeOut(lbl2), FadeIn(problem), run_time=0.4)
        self.wait(14)
        self.play(FadeOut(problem), run_time=0.3)

        # ═══════════════════════════════════════════════════════════════
        #  PART 3 — ONE-HOT ENCODING  (split screen)
        # ═══════════════════════════════════════════════════════════════

        # Transition: move current table to left side, shrink
        self.play(
            tbl.animate.scale(0.78).to_edge(LEFT, buff=0.3).shift(DOWN * 0.2),
            FadeOut(title),
            run_time=0.7
        )

        # New title for this section
        title2 = Text("One-Hot Encoding", font_size=24,
                      color=ACCENT, font="Courier New")
        title2.to_edge(UP, buff=0.4)
        self.play(FadeIn(title2, shift=DOWN * 0.1), run_time=0.4)

        # Left label
        left_lbl = Text("Original", font_size=16,
                        color=DIM_TEXT, font="Courier New")
        left_lbl.next_to(tbl, UP, buff=0.15)

        # Right: one-hot table
        oh_tbl, oh_cg = build_onehot_table(width=6.8)
        oh_tbl.to_edge(RIGHT, buff=0.3).shift(DOWN * 0.2)
        oh_tbl.scale(0.78)

        right_lbl = Text("One-Hot Encoded", font_size=16,
                         color=ACCENT, font="Courier New")
        right_lbl.next_to(oh_tbl, UP, buff=0.15)

        # Divider
        divider = DashedLine(UP * 3.0, DOWN * 3.0,
                             color=DIM_TEXT, stroke_width=1.0,
                             dash_length=0.15)
        divider.center()

        lbl3 = lbl_bg(
            "One-Hot:  each category becomes its own 0/1 column")
        self.play(
            FadeIn(left_lbl),
            Create(divider),
            run_time=0.5
        )
        self.play(FadeIn(right_lbl), run_time=0.3)
        self.play(FadeIn(lbl3), run_time=0.3)

        # Animate one-hot rows appearing one by one
        # Header first
        self.play(
            LaggedStart(
                *[FadeIn(c, shift=LEFT * 0.08) for c in oh_cg[0]],
                lag_ratio=0.1, run_time=0.6
            )
        )
        # Data rows
        self.play(
            LaggedStart(
                *[LaggedStart(
                    *[FadeIn(c, shift=LEFT * 0.05) for c in oh_cg[r]],
                    lag_ratio=0.06)
                  for r in range(1, len(oh_cg))],
                lag_ratio=0.18, run_time=1.6
            )
        )

        # Add the grid lines & header bg for the one-hot table
        # (already inside oh_tbl VGroup — just needed the cells to animate)

        self.wait(14)

        # Highlight: point out that no false order is implied
        no_order = lbl_bg(
            "No false order — each city is independent.  Clean and safe.",
            color=GREEN)
        self.play(FadeOut(lbl3), FadeIn(no_order), run_time=0.4)
        self.wait(14)

        # ── FADE OUT ──────────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(title2, tbl, oh_tbl,
                           left_lbl, right_lbl,
                           divider, no_order)),
            run_time=0.8
        )
        self.wait(0.3)