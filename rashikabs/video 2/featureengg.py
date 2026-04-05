from manim import *
import numpy as np

BG       = "#0F0F0F"
CREAM    = "#F2EFE7"
ACCENT   = "#4A9EFF"
DIM_TEXT = "#555555"
GOLD     = "#FFD166"
WARN     = "#FF6B6B"
GREEN    = "#06D6A0"
PURPLE   = "#C084FC"

# ── cleaned data ──────────────────────────────────────────────────────
IDS       = ["101", "102", "103", "104", "105", "106", "107"]
LOCATIONS = ["Mumbai","Mumbai","Mumbai","Pune","Pune","Delhi","Delhi"]
AREAS     = [1200, 950, 1100, 1500, 484, 1800, 1350]
BEDROOMS  = [3, 2, 3, 4, 3, 3, 3]
YR_BUILT  = [2010, 2015, 2015, 2008, 2012, 2005, 2024]
FURNISHED = ["Yes","No","Yes","Yes","No","Yes","No"]
PRICES    = [85, 62, 78, 91, 55, 74, 74]
CURRENT_YEAR = 2024


def lbl_bg(text, color=GOLD, font_size=16):
    t = Text(text, font_size=font_size, color=color, font="Courier New")
    t.to_edge(DOWN, buff=0.45)
    bg = BackgroundRectangle(t, color="#000000", fill_opacity=1, buff=0.12)
    return VGroup(bg, t)


def make_cell(txt, font_size=12, color=CREAM):
    return Text(txt, font_size=font_size, color=color, font="Courier New")


# ─────────────────────────────────────────────────────────────────────
#  Generic column-list table builder
#  cols: list of (header_str, [val_str, ...], color)
# ─────────────────────────────────────────────────────────────────────
def build_col_table(cols, col_width=1.15, row_height=0.46,
                    font_hdr=13, font_cell=12, scale_w=None):
    n_rows = len(cols[0][1]) + 1   # +1 for header
    n_cols = len(cols)
    TABLE_W = col_width * n_cols
    TABLE_H = row_height * n_rows
    ox = -TABLE_W / 2
    oy =  TABLE_H / 2

    cell_grid = []   # cell_grid[r][c]
    line_mobs = []

    for r_idx in range(n_rows):
        cell_row = []
        for c_idx, (hdr, vals, col_color) in enumerate(cols):
            cx = ox + c_idx * col_width + col_width / 2
            cy = oy - r_idx * row_height - row_height / 2
            is_hdr = (r_idx == 0)
            txt = hdr if is_hdr else vals[r_idx - 1]
            color = ACCENT if is_hdr else col_color
            mob = Text(txt,
                       font_size=font_hdr if is_hdr else font_cell,
                       color=color, font="Courier New")
            mob.move_to([cx, cy, 0])
            cell_row.append(mob)
        cell_grid.append(cell_row)

    # horizontal lines
    for r in range(n_rows + 1):
        y  = oy - r * row_height
        lw = 2.0 if r in (0, 1) else 0.7
        c  = ACCENT if r in (0, 1) else DIM_TEXT
        line_mobs.append(
            Line([ox, y, 0], [ox + TABLE_W, y, 0],
                 color=c, stroke_width=lw))
    # vertical lines
    for c in range(n_cols + 1):
        x  = ox + c * col_width
        lw = 2.0 if c in (0, n_cols) else 0.7
        col = ACCENT if c in (0, n_cols) else DIM_TEXT
        line_mobs.append(
            Line([x, oy, 0], [x, oy - TABLE_H, 0],
                 color=col, stroke_width=lw))

    header_bg = Rectangle(width=TABLE_W, height=row_height,
                           fill_color="#0D1B2A", fill_opacity=1,
                           stroke_width=0)
    header_bg.move_to([0, oy - row_height / 2, 0])

    all_lines = VGroup(*line_mobs)
    all_cells = VGroup(*[m for row in cell_grid for m in row])
    tbl = VGroup(header_bg, all_lines, all_cells)
    if scale_w:
        tbl.scale_to_fit_width(scale_w).center()
    return tbl, cell_grid


class FeatureEngineering(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── TITLE ─────────────────────────────────────────────────────
        title = Text("Feature Selection & Engineering",
                     font_size=26, color=CREAM, font="Courier New")
        title.to_edge(UP, buff=0.4)
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  OPENING — transition phrase
        # ═══════════════════════════════════════════════════════════════
        phrase = Text("From repairing data\nto improving representation.",
                      font_size=32, color=ACCENT, font="Courier New",
                      line_spacing=1.2)
        phrase.center()
        self.play(Write(phrase), run_time=1.0)
        self.wait(12)
        self.play(FadeOut(phrase), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 1 — FEATURE SELECTION: drop irrelevant columns
        # ═══════════════════════════════════════════════════════════════
        sel_lbl = lbl_bg("Feature Selection — keep only what matters")
        self.play(FadeIn(sel_lbl), run_time=0.4)

        # Show all original column names as a vertical list
        all_cols = [
            ("Listing ID",            WARN),
            ("Location",              CREAM),
            ("Area (sq ft)",          CREAM),
            ("Bedrooms",              CREAM),
            ("Year Built",            CREAM),
            ("Furnished",             CREAM),
            ("Owner Phone Number",    WARN),
            ("Listing Description",   WARN),
        ]

        col_mobs = VGroup(*[
            Text(f"  {name}", font_size=18, color=col,
                 font="Courier New")
            for name, col in all_cols
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        col_mobs.center().shift(DOWN * 0.15)

        # Dot bullets
        bullets = VGroup(*[
            Dot(radius=0.07, color=col,
                fill_opacity=0.9).next_to(col_mobs[i], LEFT, buff=0.12)
            for i, (_, col) in enumerate(all_cols)
        ])

        self.play(
            LaggedStart(
                *[FadeIn(VGroup(bullets[i], col_mobs[i]), shift=RIGHT * 0.1)
                  for i in range(len(all_cols))],
                lag_ratio=0.12, run_time=1.4
            )
        )
        self.wait(10)

        # Strikethrough the irrelevant ones
        drop_indices = [0, 6, 7]   # Listing ID, Phone, Description
        strikes = VGroup()
        for idx in drop_indices:
            mob = col_mobs[idx]
            s = Line(mob.get_left() + LEFT * 0.05,
                     mob.get_right() + RIGHT * 0.05,
                     color=WARN, stroke_width=2)
            strikes.add(s)
            self.play(Create(s), run_time=0.35)

        drop_note = lbl_bg(
            "Listing ID, Phone, Description — no predictive value  →  dropped",
            color=WARN)
        self.play(FadeOut(sel_lbl), FadeIn(drop_note), run_time=0.4)
        self.wait(10)

        # Fade out dropped items
        drop_group = VGroup(
            *[VGroup(bullets[i], col_mobs[i]) for i in drop_indices],
            strikes
        )
        self.play(FadeOut(drop_group, shift=RIGHT * 0.4), run_time=0.6)
        self.wait(8)
        self.play(
            FadeOut(VGroup(col_mobs, bullets, drop_note)),
            run_time=0.5
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 2 — FEATURE EXTRACTION: House Age
        # ═══════════════════════════════════════════════════════════════
        ext_lbl = lbl_bg("Feature Extraction — transform raw data into better signals")
        self.play(FadeIn(ext_lbl), run_time=0.4)

        # Show Year Built column + calculation → House Age
        yr_vals  = [str(y) for y in YR_BUILT]
        age_vals = [str(CURRENT_YEAR - y) for y in YR_BUILT]

        yr_col = VGroup(*[
            Text(f"Yr Built: {y}", font_size=17, color=CREAM,
                 font="Courier New")
            for y in YR_BUILT
        ]).arrange(DOWN, buff=0.22)

        calc_arrows = VGroup(*[
            Text(f"2024 - {YR_BUILT[i]} =", font_size=14,
                 color=GOLD, font="Courier New")
            for i in range(len(IDS))
        ]).arrange(DOWN, buff=0.22)

        age_col = VGroup(*[
            Text(f"Age: {a} yrs", font_size=17, color=GREEN,
                 font="Courier New")
            for a in age_vals
        ]).arrange(DOWN, buff=0.22)

        calc_group = VGroup(yr_col, calc_arrows, age_col).arrange(
            RIGHT, buff=0.5)
        calc_group.center().shift(DOWN * 0.15)

        self.play(FadeIn(yr_col, shift=RIGHT * 0.1), run_time=0.6)
        self.wait(6)

        self.play(
            LaggedStart(
                *[FadeIn(VGroup(calc_arrows[i], age_col[i]),
                         shift=RIGHT * 0.08)
                  for i in range(len(IDS))],
                lag_ratio=0.1, run_time=1.2
            )
        )

        age_note = lbl_bg(
            "House Age is more meaningful to a model than a raw year",
            color=GREEN)
        self.play(FadeOut(ext_lbl), FadeIn(age_note), run_time=0.4)
        self.wait(12)
        self.play(FadeOut(VGroup(calc_group, age_note)), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 3 — FEATURE EXTRACTION: Price per sq ft
        # ═══════════════════════════════════════════════════════════════
        ppsf_lbl = lbl_bg(
            "New feature: Price per sq ft  =  Price / Area")
        self.play(FadeIn(ppsf_lbl), run_time=0.4)

        ppsf_vals = [round(PRICES[i] / AREAS[i] * 100, 2)
                     for i in range(len(IDS))]

        price_col = VGroup(*[
            Text(f"Price={PRICES[i]}L  Area={AREAS[i]}",
                 font_size=16, color=CREAM, font="Courier New")
            for i in range(len(IDS))
        ]).arrange(DOWN, buff=0.20)

        arr2 = VGroup(*[
            Text("→", font_size=16, color=GOLD, font="Courier New")
            for _ in IDS
        ]).arrange(DOWN, buff=0.20)

        ppsf_col = VGroup(*[
            Text(f"PricePerSqft: {ppsf_vals[i]}",
                 font_size=16, color=PURPLE, font="Courier New")
            for i in range(len(IDS))
        ]).arrange(DOWN, buff=0.20)

        ppsf_group = VGroup(price_col, arr2, ppsf_col).arrange(
            RIGHT, buff=0.4)
        ppsf_group.center().shift(DOWN * 0.15)

        self.play(FadeIn(price_col), run_time=0.6)
        self.wait(4)
        self.play(
            LaggedStart(
                *[FadeIn(VGroup(arr2[i], ppsf_col[i]),
                         shift=RIGHT * 0.08)
                  for i in range(len(IDS))],
                lag_ratio=0.1, run_time=1.2
            )
        )
        self.wait(12)
        self.play(FadeOut(VGroup(ppsf_group, ppsf_lbl)), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 4 — FEATURE EXTRACTION: Room Density
        # ═══════════════════════════════════════════════════════════════
        rd_lbl = lbl_bg(
            "New feature: Room Density  =  Bedrooms / Area")
        self.play(FadeIn(rd_lbl), run_time=0.4)

        rd_vals = [round(BEDROOMS[i] / AREAS[i] * 1000, 3)
                   for i in range(len(IDS))]

        bed_col = VGroup(*[
            Text(f"Beds={BEDROOMS[i]}  Area={AREAS[i]}",
                 font_size=16, color=CREAM, font="Courier New")
            for i in range(len(IDS))
        ]).arrange(DOWN, buff=0.20)

        arr3 = VGroup(*[
            Text("→", font_size=16, color=GOLD, font="Courier New")
            for _ in IDS
        ]).arrange(DOWN, buff=0.20)

        rd_col = VGroup(*[
            Text(f"RoomDensity: {rd_vals[i]}",
                 font_size=16, color=PURPLE, font="Courier New")
            for i in range(len(IDS))
        ]).arrange(DOWN, buff=0.20)

        rd_group = VGroup(bed_col, arr3, rd_col).arrange(RIGHT, buff=0.4)
        rd_group.center().shift(DOWN * 0.15)

        self.play(FadeIn(bed_col), run_time=0.6)
        self.wait(4)
        self.play(
            LaggedStart(
                *[FadeIn(VGroup(arr3[i], rd_col[i]), shift=RIGHT * 0.08)
                  for i in range(len(IDS))],
                lag_ratio=0.1, run_time=1.2
            )
        )
        self.wait(12)
        self.play(FadeOut(VGroup(rd_group, rd_lbl)), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 5 — FINAL EXPANDED TABLE
        # ═══════════════════════════════════════════════════════════════
        final_lbl = lbl_bg(
            "Engineered dataset — richer, more meaningful representation",
            color=GREEN)
        self.play(FadeIn(final_lbl), run_time=0.4)

        # Build final table:
        # ID | Area | Beds | Furnished | House Age | PricePerSqft | RoomDensity
        cols_def = [
            ("ID",          [str(i) for i in IDS],         CREAM),
            ("Area",        [str(a) for a in AREAS],        CREAM),
            ("Beds",        [str(b) for b in BEDROOMS],     CREAM),
            ("Furnished",   FURNISHED,                      CREAM),
            ("House Age",   [str(CURRENT_YEAR - y)
                             for y in YR_BUILT],            GREEN),
            ("Pr/sqft",     [str(round(PRICES[i]/AREAS[i]*100, 1))
                             for i in range(len(IDS))],     PURPLE),
            ("RoomDens",    [str(round(BEDROOMS[i]/AREAS[i]*1000, 2))
                             for i in range(len(IDS))],     PURPLE),
        ]

        final_tbl, final_cg = build_col_table(
            cols_def, col_width=1.10,
            row_height=0.44, font_hdr=12, font_cell=11,
            scale_w=12.5
        )
        final_tbl.shift(DOWN * 0.25)

        # Animate: base columns first, engineered columns after
        base_cells  = VGroup(*[final_cg[r][c]
                                for r in range(len(final_cg))
                                for c in range(4)])
        eng_cells   = VGroup(*[final_cg[r][c]
                                for r in range(len(final_cg))
                                for c in range(4, 7)])

        # Extract lines and bg from final_tbl children
        header_bg_f = final_tbl[0]
        lines_f     = final_tbl[1]

        self.play(
            FadeIn(header_bg_f),
            Create(lines_f),
            run_time=0.7
        )
        self.play(FadeIn(base_cells, shift=UP * 0.05), run_time=0.8)
        self.wait(4)

        # Engineered columns grow in with highlight
        self.play(
            LaggedStart(
                *[FadeIn(eng_cells[i], shift=LEFT * 0.08)
                  for i in range(len(eng_cells))],
                lag_ratio=0.03, run_time=1.4
            )
        )

        eng_note = lbl_bg(
            "House Age, Price/sqft, Room Density — all derived, all more useful",
            color=GREEN)
        self.play(FadeOut(final_lbl), FadeIn(eng_note), run_time=0.4)
        self.wait(14)

        # Closing thought
        closing = lbl_bg(
            "ML often depends not just on data — but on how we represent it.",
            color=ACCENT)
        self.play(FadeOut(eng_note), FadeIn(closing), run_time=0.4)
        self.wait(12)

        # ── FADE OUT ──────────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(title, final_tbl, closing)),
            run_time=0.8
        )
        self.wait(0.3)