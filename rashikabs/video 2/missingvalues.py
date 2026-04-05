from manim import *

BG       = "#0F0F0F"
CREAM    = "#F2EFE7"
ACCENT   = "#4A9EFF"
DIM_TEXT = "#555555"
GOLD     = "#FFD166"
WARN     = "#FF6B6B"
GREEN    = "#06D6A0"


# ─────────────────────────────────────────────────────────────────────
#  MINI TABLE BUILDER
#  Shows only the columns relevant to missing values:
#  ID | Price (Rs.L) | Year Built
#  Rows after cleaning (no duplicates, spellings fixed, unit fixed)
#  Row 106 has missing Price, Row 107 has missing Year Built
# ─────────────────────────────────────────────────────────────────────
def build_mini_table(price_106="N/A", year_107="N/A",
                     highlight_106_price=True,
                     highlight_107_year=True):
    """
    Returns (table_group, cell_grid)
    cell_grid[r][c] -> Text mobject
    Row 0 = header, rows 1-7 = data
    Cols: 0=ID, 1=Location, 2=Price, 3=Yr Built
    """
    headers = ["ID", "Location", "Price (Rs.L)", "Yr Built"]
    rows = [
        ["101", "Mumbai", "85",        "2010"],
        ["102", "Mumbai", "62",        "2015"],
        ["103", "Mumbai", "78",        "2015"],
        ["104", "Pune",   "91",        "2008"],
        ["105", "Pune",   "55",        "2012"],
        ["106", "Delhi",  price_106,   "2005"],
        ["107", "Delhi",  "74",        year_107],
    ]
    all_rows = [headers] + rows

    COL_WIDTHS = [0.60, 1.00, 1.20, 1.00]
    ROW_HEIGHT = 0.50
    FONT_HDR   = 14
    FONT_CELL  = 13
    TABLE_W    = sum(COL_WIDTHS)
    TABLE_H    = ROW_HEIGHT * len(all_rows)

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

            # colour logic
            if is_header:
                color = ACCENT
            elif r_idx == 6 and c_idx == 2 and highlight_106_price and price_106 == "N/A":
                color = WARN
            elif r_idx == 7 and c_idx == 3 and highlight_107_year and year_107 == "N/A":
                color = WARN
            elif r_idx == 6 and c_idx == 2 and price_106 != "N/A":
                color = GREEN
            elif r_idx == 7 and c_idx == 3 and year_107 != "N/A":
                color = GREEN
            else:
                color = CREAM

            txt = Text(cell_text,
                       font_size=FONT_HDR if is_header else FONT_CELL,
                       color=color, font="Courier New")
            txt.move_to([cx, cy, 0])
            cell_row.append(txt)
            x_cursor += cw
        cell_grid.append(cell_row)

    # horizontal lines
    for r_idx in range(len(all_rows) + 1):
        y  = origin_y - r_idx * ROW_HEIGHT
        lw = 2.0 if r_idx in (0, 1) else 0.8
        c  = ACCENT if r_idx in (0, 1) else DIM_TEXT
        line_mobs.append(Line([origin_x, y, 0],
                               [origin_x + TABLE_W, y, 0],
                               color=c, stroke_width=lw))
    # vertical lines
    x_cur = origin_x
    for c_idx in range(len(COL_WIDTHS) + 1):
        lw = 2.0 if c_idx in (0, len(COL_WIDTHS)) else 0.8
        c  = ACCENT if c_idx in (0, len(COL_WIDTHS)) else DIM_TEXT
        line_mobs.append(Line([x_cur, origin_y, 0],
                               [x_cur, origin_y - TABLE_H, 0],
                               color=c, stroke_width=lw))
        if c_idx < len(COL_WIDTHS):
            x_cur += COL_WIDTHS[c_idx]

    header_bg = Rectangle(
        width=TABLE_W, height=ROW_HEIGHT,
        fill_color="#0D1B2A", fill_opacity=1, stroke_width=0
    )
    header_bg.move_to([0, origin_y - ROW_HEIGHT / 2, 0])

    all_lines = VGroup(*line_mobs)
    all_cells = VGroup(*[mob for row in cell_grid for mob in row])
    table_group = VGroup(header_bg, all_lines, all_cells)
    table_group.scale_to_fit_width(7.0).center()

    return table_group, cell_grid


def lbl_with_bg(text, color=GOLD):
    """Step label with black background rectangle."""
    t = Text(text, font_size=17, color=color, font="Courier New")
    t.to_edge(DOWN, buff=0.45)
    bg = BackgroundRectangle(t, color="#000000", fill_opacity=1, buff=0.12)
    return VGroup(bg, t)


class MissingValues(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── TITLE ─────────────────────────────────────────────────────
        title = Text("Handling Missing Values", font_size=26,
                     color=CREAM, font="Courier New")
        title.to_edge(UP, buff=0.4)
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)

        # ── INITIAL TABLE  (missing values highlighted in red) ────────
        table, cg = build_mini_table("N/A", "N/A",
                                     highlight_106_price=True,
                                     highlight_107_year=True)
        table.shift(DOWN * 0.3)
        self.play(FadeIn(table), run_time=0.8)

        lbl0 = lbl_with_bg("Row 106: Price missing    Row 107: Year Built missing")
        self.play(FadeIn(lbl0), run_time=0.4)
        self.wait(12)
        self.play(FadeOut(lbl0), run_time=0.3)

        # ═══════════════════════════════════════════════════════════════
        #  STRATEGY 1 — REMOVE THE ROWS
        # ═══════════════════════════════════════════════════════════════
        lbl1 = lbl_with_bg("Strategy 1: Remove rows with missing values")
        self.play(FadeIn(lbl1), run_time=0.4)

        # Highlight the two bad rows
        bad_row_106 = VGroup(*cg[6])
        bad_row_107 = VGroup(*cg[7])
        rect_106 = SurroundingRectangle(bad_row_106, color=WARN,
                                         buff=0.04, stroke_width=2)
        rect_107 = SurroundingRectangle(bad_row_107, color=WARN,
                                         buff=0.04, stroke_width=2)
        self.play(Create(rect_106), Create(rect_107), run_time=0.5)
        self.wait(10)

        # Fade both rows out
        self.play(
            FadeOut(bad_row_106, shift=RIGHT * 0.4),
            FadeOut(bad_row_107, shift=RIGHT * 0.4),
            FadeOut(rect_106),
            FadeOut(rect_107),
            run_time=0.6
        )

        loss_note = lbl_with_bg(
            "Simple — but we lose data. 2 rows gone.", color=WARN)
        self.play(FadeOut(lbl1), FadeIn(loss_note), run_time=0.4)
        self.wait(10)
        self.play(FadeOut(loss_note), run_time=0.3)

        # Restore rows by rebuilding table
        self.play(FadeOut(table), run_time=0.4)
        table, cg = build_mini_table("N/A", "N/A")
        table.shift(DOWN * 0.3)
        self.play(FadeIn(table), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  STRATEGY 2 — FILL WITH MEAN
        # ═══════════════════════════════════════════════════════════════
        lbl2 = lbl_with_bg("Strategy 2: Fill with Mean  →  Price mean = 74")
        self.play(FadeIn(lbl2), run_time=0.4)

        # Highlight missing price cell
        missing_price = cg[6][2]
        self.play(Indicate(missing_price, color=WARN, scale_factor=1.2),
                  run_time=0.5)
        self.wait(10)

        # Replace with mean value
        new_mean = Text("74", font_size=13, color=GREEN, font="Courier New")
        new_mean.move_to(missing_price.get_center())
        self.play(FadeOut(missing_price, shift=UP*0.06), run_time=0.3)
        self.play(FadeIn(new_mean, shift=UP*0.06), run_time=0.3)
        cg[6][2] = new_mean

        mean_note = lbl_with_bg(
            "Works well for symmetric data — but sensitive to outliers",
            color=CREAM)
        self.play(FadeOut(lbl2), FadeIn(mean_note), run_time=0.4)
        self.wait(10)
        self.play(FadeOut(mean_note), run_time=0.3)

        # Restore
        self.play(FadeOut(table), run_time=0.4)
        table, cg = build_mini_table("N/A", "N/A")
        table.shift(DOWN * 0.3)
        self.play(FadeIn(table), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  STRATEGY 3 — FILL WITH MEDIAN
        # ═══════════════════════════════════════════════════════════════
        lbl3 = lbl_with_bg("Strategy 3: Fill with Median  →  Price median = 74")
        self.play(FadeIn(lbl3), run_time=0.4)

        missing_price2 = cg[6][2]
        self.play(Indicate(missing_price2, color=WARN, scale_factor=1.2),
                  run_time=0.5)
        self.wait(10)

        new_median = Text("74", font_size=13, color=GREEN, font="Courier New")
        new_median.move_to(missing_price2.get_center())
        self.play(FadeOut(missing_price2, shift=UP*0.06), run_time=0.3)
        self.play(FadeIn(new_median, shift=UP*0.06), run_time=0.3)
        cg[6][2] = new_median

        median_note = lbl_with_bg(
            "More robust than mean — handles outliers better", color=CREAM)
        self.play(FadeOut(lbl3), FadeIn(median_note), run_time=0.4)
        self.wait(10)
        self.play(FadeOut(median_note), run_time=0.3)

        # Restore
        self.play(FadeOut(table), run_time=0.4)
        table, cg = build_mini_table("N/A", "N/A")
        table.shift(DOWN * 0.3)
        self.play(FadeIn(table), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  STRATEGY 4 — FILL WITH MODE  (Year Built)
        # ═══════════════════════════════════════════════════════════════
        lbl4 = lbl_with_bg("Strategy 4: Fill with Mode  →  Year Built mode = 2015")
        self.play(FadeIn(lbl4), run_time=0.4)

        missing_year = cg[7][3]
        self.play(Indicate(missing_year, color=WARN, scale_factor=1.2),
                  run_time=0.5)
        self.wait(10)

        new_mode = Text("2015", font_size=13, color=GREEN, font="Courier New")
        new_mode.move_to(missing_year.get_center())
        self.play(FadeOut(missing_year, shift=UP*0.06), run_time=0.3)
        self.play(FadeIn(new_mode, shift=UP*0.06), run_time=0.3)
        cg[7][3] = new_mode

        mode_note = lbl_with_bg(
            "Best for categorical or discrete values", color=CREAM)
        self.play(FadeOut(lbl4), FadeIn(mode_note), run_time=0.4)
        self.wait(10)
        self.play(FadeOut(mode_note), run_time=0.3)

        # Restore
        self.play(FadeOut(table), run_time=0.4)
        table, cg = build_mini_table("N/A", "N/A")
        table.shift(DOWN * 0.3)
        self.play(FadeIn(table), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  STRATEGY 5 — FILL WITH CONSTANT / PLACEHOLDER
        # ═══════════════════════════════════════════════════════════════
        lbl5 = lbl_with_bg("Strategy 5: Fill with a constant placeholder  (-1)")
        self.play(FadeIn(lbl5), run_time=0.4)

        mp3 = cg[6][2]
        my3 = cg[7][3]
        self.play(Indicate(mp3, color=WARN), Indicate(my3, color=WARN),
                  run_time=0.5)
        self.wait(8)

        new_const_p = Text("-1", font_size=13, color=GOLD, font="Courier New")
        new_const_p.move_to(mp3.get_center())
        new_const_y = Text("-1", font_size=13, color=GOLD, font="Courier New")
        new_const_y.move_to(my3.get_center())

        self.play(FadeOut(mp3, shift=UP*0.06),
                  FadeOut(my3, shift=UP*0.06), run_time=0.3)
        self.play(FadeIn(new_const_p, shift=UP*0.06),
                  FadeIn(new_const_y, shift=UP*0.06), run_time=0.3)
        cg[6][2] = new_const_p
        cg[7][3] = new_const_y

        const_note = lbl_with_bg(
            "Explicitly flags missingness — useful when absence is informative",
            color=CREAM)
        self.play(FadeOut(lbl5), FadeIn(const_note), run_time=0.4)
        self.wait(10)
        self.play(FadeOut(const_note), run_time=0.3)

        # ═══════════════════════════════════════════════════════════════
        #  FINAL SPLIT SCREEN — BEFORE  vs  AFTER (median + mode)
        # ═══════════════════════════════════════════════════════════════
        self.play(FadeOut(table), run_time=0.5)

        # Before table (missing values in red)
        tbl_before, _ = build_mini_table("N/A", "N/A")
        tbl_before.scale(0.82).to_edge(LEFT, buff=0.5).shift(DOWN * 0.3)

        # After table (filled values in green)
        tbl_after, _ = build_mini_table("74", "2015",
                                        highlight_106_price=False,
                                        highlight_107_year=False)
        tbl_after.scale(0.82).to_edge(RIGHT, buff=0.5).shift(DOWN * 0.3)

        before_lbl = Text("BEFORE", font_size=20, color=WARN,
                           font="Courier New")
        before_lbl.next_to(tbl_before, UP, buff=0.2)
        after_lbl = Text("AFTER", font_size=20, color=GREEN,
                         font="Courier New")
        after_lbl.next_to(tbl_after, UP, buff=0.2)

        self.play(
            FadeIn(tbl_before, shift=RIGHT * 0.15),
            FadeIn(tbl_after,  shift=LEFT  * 0.15),
            FadeIn(before_lbl),
            FadeIn(after_lbl),
            run_time=0.8
        )

        final_note = lbl_with_bg(
            "Median for Price  |  Mode for Year Built  →  dataset complete",
            color=GREEN)
        self.play(FadeIn(final_note), run_time=0.4)
        self.wait(12)

        # ── FADE OUT EVERYTHING ───────────────────────────────────────
        self.play(
            FadeOut(VGroup(title, tbl_before, tbl_after,
                           before_lbl, after_lbl, final_note)),
            run_time=0.8
        )
        self.wait(0.3)