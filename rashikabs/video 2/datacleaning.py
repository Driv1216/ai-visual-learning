from manim import *

BG       = "#0F0F0F"
CREAM    = "#F2EFE7"
ACCENT   = "#4A9EFF"
DIM_TEXT = "#555555"
GOLD     = "#FFD166"
WARN     = "#FF6B6B"
GREEN    = "#06D6A0"


# ─────────────────────────────────────────────────────────────────────
#  SHARED TABLE BUILDER
#  Returns: (table_group, cell_grid, all_lines, header_bg)
#   - table_group : single VGroup you can FadeIn/FadeOut/shift
#   - cell_grid   : cell_grid[r][c] → the Text mobject (for targeting)
#   - all_lines   : VGroup of grid lines (separate so you can redraw)
#   - header_bg   : the dark header rectangle
# ─────────────────────────────────────────────────────────────────────
def build_table(color_problems=True):
    headers = [
        "ID", "Location", "Area\n(sq ft)", "Beds",
        "Yr Built", "Furnished", "Phone", "Price\n(Rs.L)"
    ]
    rows = [
        ["101", "Mumbai", "1200", "3",   "2010", "Yes", "982-001", "85"],
        ["102", "mumbai", "950",  "2",   "2015", "No",  "982-009", "62"],
        ["103", "MUMBAI", "1100", "3",   "2015", "Yes", "971-123", "78"],
        ["104", "Pune",   "1500", "4",   "2008", "Yes", "880-001", "91"],
        ["105", "Pune",   "45",   "3",   "2012", "No",  "880-009", "55"],
        ["106", "Delhi",  "1800", "N/A", "2005", "Yes", "991-005", "N/A"],
        ["107", "Delhi",  "1350", "3",   "N/A",  "No",  "991-004", "74"],
        ["108", "Mumbai", "1200", "3",   "2010", "Yes", "982-001", "85"],
    ]
    all_rows = [headers] + rows

    COL_WIDTHS = [0.55, 1.10, 0.85, 0.65, 0.80, 1.00, 0.85, 0.80]
    ROW_HEIGHT = 0.52
    FONT_HDR   = 13
    FONT_CELL  = 12
    TABLE_W    = sum(COL_WIDTHS)
    TABLE_H    = ROW_HEIGHT * len(all_rows)

    MUMBAI_BAD   = {"mumbai", "MUMBAI"}
    MIXED_ROW    = 4       # row 5 in data (0-indexed), area = 45
    MISSING_CELLS = {(5, 3), (5, 7), (6, 4)}   # (data_row_idx, col_idx)
    DUPLICATE_ROWS = {0, 7}                      # data row indices

    origin_x = -TABLE_W / 2
    origin_y =  TABLE_H / 2

    cell_grid = []
    line_mobs = []

    for r_idx, row in enumerate(all_rows):
        cell_row = []
        x_cursor = origin_x
        for c_idx, cell_text in enumerate(row):
            cw = COL_WIDTHS[c_idx]
            cx = x_cursor + cw / 2
            cy = origin_y - r_idx * ROW_HEIGHT - ROW_HEIGHT / 2
            is_header = (r_idx == 0)

            if is_header:
                color = ACCENT
            elif not color_problems:
                color = CREAM
            elif r_idx - 1 in DUPLICATE_ROWS:
                color = GOLD
            elif c_idx == 1 and cell_text in MUMBAI_BAD:
                color = WARN
            elif r_idx - 1 == MIXED_ROW and c_idx == 2:
                color = WARN
            elif (r_idx - 1, c_idx) in MISSING_CELLS:
                color = WARN
            else:
                color = CREAM

            txt = Text(cell_text,
                       font_size=FONT_HDR if is_header else FONT_CELL,
                       color=color,
                       font="Courier New")
            txt.move_to([cx, cy, 0])
            cell_row.append(txt)
            x_cursor += cw
        cell_grid.append(cell_row)

    # Horizontal lines
    for r_idx in range(len(all_rows) + 1):
        y  = origin_y - r_idx * ROW_HEIGHT
        lw = 2.0 if r_idx in (0, 1) else 0.8
        c  = ACCENT if r_idx in (0, 1) else DIM_TEXT
        line_mobs.append(Line([origin_x, y, 0],
                               [origin_x + TABLE_W, y, 0],
                               color=c, stroke_width=lw))
    # Vertical lines
    x_cursor = origin_x
    for c_idx in range(len(COL_WIDTHS) + 1):
        lw = 2.0 if c_idx in (0, len(COL_WIDTHS)) else 0.8
        c  = ACCENT if c_idx in (0, len(COL_WIDTHS)) else DIM_TEXT
        line_mobs.append(Line([x_cursor, origin_y, 0],
                               [x_cursor, origin_y - TABLE_H, 0],
                               color=c, stroke_width=lw))
        if c_idx < len(COL_WIDTHS):
            x_cursor += COL_WIDTHS[c_idx]

    header_bg = Rectangle(
        width=TABLE_W, height=ROW_HEIGHT,
        fill_color="#0D1B2A", fill_opacity=1, stroke_width=0
    )
    header_bg.move_to([0, origin_y - ROW_HEIGHT / 2, 0])

    all_lines  = VGroup(*line_mobs)
    all_cells  = VGroup(*[mob for row in cell_grid for mob in row])
    table_group = VGroup(header_bg, all_lines, all_cells)
    table_group.scale_to_fit_width(10.0).center()

    return table_group, cell_grid, all_lines, header_bg


# ─────────────────────────────────────────────────────────────────────
#  STEP LABEL  helper
# ─────────────────────────────────────────────────────────────────────
def step_label(text, color=GOLD):
    return Text(text, font_size=17, color=color,
                font="Courier New").to_edge(DOWN, buff=0.45)


# ─────────────────────────────────────────────────────────────────────
#  MAIN SCENE
# ─────────────────────────────────────────────────────────────────────
class DataCleaningAnimation(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── TITLE ─────────────────────────────────────────────────────
        title = Text("Data Cleaning", font_size=26,
                     color=CREAM, font="Courier New")
        title.to_edge(UP, buff=0.4)

        # ── BUILD TABLE ───────────────────────────────────────────────
        table_group, cell_grid, all_lines, header_bg = build_table(
            color_problems=True
        )
        # Nudge down so title doesn't overlap
        table_group.shift(DOWN * 0.3)

        # ── FADE IN ───────────────────────────────────────────────────
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)
        self.play(FadeIn(header_bg), Create(all_lines), run_time=0.7)
        # Header cells
        self.play(
            LaggedStart(*[FadeIn(c, shift=UP*0.06) for c in cell_grid[0]],
                        lag_ratio=0.07, run_time=0.6)
        )
        # Data rows
        self.play(
            LaggedStart(
                *[LaggedStart(*[FadeIn(c, shift=UP*0.04) for c in row],
                              lag_ratio=0.03)
                  for row in cell_grid[1:]],
                lag_ratio=0.15, run_time=1.6
            )
        )
        self.wait(10)

        # ═════════════════════════════════════════════════════════════
        #  STEP 1 — REMOVE DUPLICATE ROW (row 108 = cell_grid[8])
        # ═════════════════════════════════════════════════════════════
        lbl1 = step_label("Step 1: Remove duplicate rows")
        lbl1_bg = BackgroundRectangle(lbl1, color="#000000", fill_opacity=1, buff=0.1)
        lbl1 = VGroup(lbl1_bg, lbl1)
        self.play(FadeIn(lbl1, shift=UP*0.08), run_time=0.5)

        # Highlight duplicate pair (rows 1 and 8 in cell_grid → data rows 0 & 7)
        dup_highlight = SurroundingRectangle(
            VGroup(*cell_grid[1], *cell_grid[8]),
            color=GOLD, buff=0.05, stroke_width=2,
            fill_color=GOLD, fill_opacity=0.08, corner_radius=0.05
        )
        self.play(Create(dup_highlight), run_time=0.5)
        self.wait(12)

        # Fade out the duplicate (row 8 = last row)
        self.play(
            FadeOut(VGroup(*cell_grid[8]), shift=RIGHT * 0.3),
            FadeOut(dup_highlight),
            run_time=0.6
        )
        self.wait(0.4)
        self.play(FadeOut(lbl1), run_time=0.4)

        # ═════════════════════════════════════════════════════════════
        #  STEP 2 — STANDARDISE LOCATION SPELLINGS
        # ═════════════════════════════════════════════════════════════
        lbl2 = step_label("Step 2: Standardise inconsistent spellings")
        lbl2_bg = BackgroundRectangle(lbl2, color="#000000", fill_opacity=1, buff=0.1)
        lbl2 = VGroup(lbl2_bg, lbl2)
        self.play(FadeIn(lbl2, shift=UP*0.08), run_time=0.5)

        # cell_grid[2][1] = "mumbai",  cell_grid[3][1] = "MUMBAI"
        bad_cells = [cell_grid[2][1], cell_grid[3][1]]
        self.play(*[c.animate.set_color(WARN) for c in bad_cells],
                  run_time=0.4)
        self.wait(10)

        # Replace each bad cell with a corrected one
        for r_idx in [2, 3]:
            old = cell_grid[r_idx][1]
            new = Text("Mumbai", font_size=12, color=GREEN,
                       font="Courier New")
            new.move_to(old.get_center())
            self.play(FadeOut(old, shift=UP*0.08), run_time=0.3)
            self.play(FadeIn(new,  shift=UP*0.08), run_time=0.3)
            cell_grid[r_idx][1] = new  # keep reference updated
            self.wait(0.15)

        self.wait(0.5)
        self.play(FadeOut(lbl2), run_time=0.4)

        # ═════════════════════════════════════════════════════════════
        #  STEP 3 — FIX MIXED UNIT  (row 5, Area = 45)
        # ═════════════════════════════════════════════════════════════
        lbl3 = step_label("Step 3: Fix mixed units  (45 m2 -> 484 sq ft)")
        lbl3_bg = BackgroundRectangle(lbl3, color="#000000", fill_opacity=1, buff=0.1)
        lbl3 = VGroup(lbl3_bg, lbl3)    
        self.play(FadeIn(lbl3, shift=UP*0.08), run_time=0.5)

        # cell_grid[5][2] = "45"
        bad_area = cell_grid[5][2]
        self.play(bad_area.animate.set_color(WARN), run_time=0.3)
        self.wait(0.5)

        new_area = Text("484", font_size=12, color=GREEN,
                        font="Courier New")
        new_area.move_to(bad_area.get_center())
        self.play(FadeOut(bad_area, shift=UP*0.08), run_time=0.3)
        self.play(FadeIn(new_area,  shift=UP*0.08), run_time=0.3)
        cell_grid[5][2] = new_area
        self.wait(10)
        self.play(FadeOut(lbl3), run_time=0.4)

        # ═════════════════════════════════════════════════════════════
        #  STEP 4 — FLAG MISSING VALUES (N/A cells)
        # ═════════════════════════════════════════════════════════════
        lbl4 = step_label("Step 4: Identify missing values  →  handle next")
        self.play(FadeIn(lbl4, shift=UP*0.08), run_time=0.5)

        # Missing cells: (row 6, col 3), (row 6, col 7), (row 7, col 4)
        # In cell_grid that's [6][3], [6][7], [7][4]
        missing = [cell_grid[6][3], cell_grid[6][7], cell_grid[7][4]]
        for m in missing:
            self.play(m.animate.set_color(WARN), run_time=0.25)

        self.wait(12)
        self.play(FadeOut(lbl4), run_time=0.4)

        # ── HOLD & FADE OUT ───────────────────────────────────────────
        self.wait(8)
        self.play(
            FadeOut(VGroup(title, table_group)),
            run_time=0.8
        )
        self.wait(0.3)