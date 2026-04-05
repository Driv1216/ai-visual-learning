from manim import *

BG       = "#0F0F0F"
CREAM    = "#F2EFE7"
ACCENT   = "#4A9EFF"
DIM_TEXT = "#555555"
GOLD     = "#F2EFE7"
WARN     = "#F2EFE7"


class RawDataTable(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── DATA ──────────────────────────────────────────────────────
        headers = [
            "ID", "Location", "Area\n(sq ft)", "Beds",
            "Yr Built", "Furnished", "Phone", "Price\n(Rs.L)"
        ]

        rows = [
            ["101", "Mumbai",  "1200", "3", "2010", "Yes", "982-001", "85"],
            ["102", "mumbai",  "950",  "2", "2015", "No",  "982-009", "62"],
            ["103", "MUMBAI",  "1100", "3", "2015", "Yes", "971-123", "78"],
            ["104", "Pune",    "1500", "4", "2008", "Yes", "880-001", "91"],
            ["105", "Pune",    "45",   "3", "2012", "No",  "880-009", "55"],
            ["106", "Delhi",   "1800", "—", "2005", "Yes", "991-005", "—"],
            ["107", "Delhi",   "1350", "3", "—",    "No",  "991-004", "74"],
            ["108", "Mumbai",  "1200", "3", "2010", "Yes", "982-001", "85"],
        ]

        all_rows = [headers] + rows

        # ── LAYOUT CONSTANTS ──────────────────────────────────────────
        COL_WIDTHS  = [0.55, 1.10, 0.85, 0.55, 0.80, 1.00, 0.85, 0.80]
        ROW_HEIGHT  = 0.52
        FONT_HEADER = 12
        FONT_CELL   = 10
        TABLE_W     = sum(COL_WIDTHS)
        TABLE_H     = ROW_HEIGHT * len(all_rows)

        # Problems we want to colour-flag
        MUMBAI_VARIANTS = {"mumbai", "MUMBAI"}   # rows 1,2 (0-indexed data rows)
        MIXED_UNIT_ROW  = 4                       # row index in `rows` (Pune/45)
        MISSING_CELLS   = {(5, 3), (5, 7), (6, 4)}  # (row_idx, col_idx) in `rows`
        DUPLICATE_ROWS  = {0, 7}                  # rows identical to each other

        # ── BUILD CELLS ───────────────────────────────────────────────
        cell_mobs   = []   # list of lists, parallel to all_rows
        line_mobs   = []   # all grid lines

        # Compute top-left origin so table is centred
        origin_x = -TABLE_W / 2
        origin_y =  TABLE_H / 2

        for r_idx, row in enumerate(all_rows):
            cell_row = []
            x_cursor = origin_x

            for c_idx, cell_text in enumerate(row):
                cw = COL_WIDTHS[c_idx]
                cx = x_cursor + cw / 2
                cy = origin_y - r_idx * ROW_HEIGHT - ROW_HEIGHT / 2

                is_header = (r_idx == 0)
                font_sz   = FONT_HEADER if is_header else FONT_CELL

                # Decide text colour
                color = CREAM
                if is_header:
                    color = ACCENT
                elif r_idx - 1 in DUPLICATE_ROWS and r_idx > 0:
                    color = GOLD                          # duplicate rows
                elif c_idx == 1 and cell_text in MUMBAI_VARIANTS:
                    color = WARN                          # bad spellings
                elif r_idx - 1 == MIXED_UNIT_ROW and c_idx == 2:
                    color = WARN                          # mixed unit (45)
                elif (r_idx - 1, c_idx) in MISSING_CELLS:
                    color = WARN                          # missing values

                txt = Text(
                    cell_text,
                    font_size=font_sz,
                    color=color,
                    font = "Georgia"
                )
                txt.move_to([cx, cy, 0])
                cell_row.append(txt)
                x_cursor += cw

            cell_mobs.append(cell_row)

        # ── GRID LINES ────────────────────────────────────────────────
        # Horizontal lines
        for r_idx in range(len(all_rows) + 1):
            y = origin_y - r_idx * ROW_HEIGHT
            lw = 2.0 if r_idx in (0, 1) else 0.8
            col = ACCENT if r_idx in (0, 1) else DIM_TEXT
            line_mobs.append(
                Line([origin_x, y, 0], [origin_x + TABLE_W, y, 0],
                     color=col, stroke_width=lw)
            )

        # Vertical lines
        x_cursor = origin_x
        for c_idx in range(len(COL_WIDTHS) + 1):
            lw  = 2.0 if c_idx in (0, len(COL_WIDTHS)) else 0.8
            col = ACCENT if c_idx in (0, len(COL_WIDTHS)) else DIM_TEXT
            line_mobs.append(
                Line([x_cursor, origin_y, 0],
                     [x_cursor, origin_y - TABLE_H, 0],
                     color=col, stroke_width=lw)
            )
            if c_idx < len(COL_WIDTHS):
                x_cursor += COL_WIDTHS[c_idx]

        # Header row background rectangle
        header_bg = Rectangle(
            width=TABLE_W, height=ROW_HEIGHT,
            fill_color="#0D1B2A", fill_opacity=1,
            stroke_width=0
        )
        header_bg.move_to([0, origin_y - ROW_HEIGHT / 2, 0])

        # ── FLATTEN INTO VGROUPS ──────────────────────────────────────
        all_cells = VGroup(*[mob for row in cell_mobs for mob in row])
        all_lines = VGroup(*line_mobs)
        table_group = VGroup(header_bg, all_lines, all_cells)

        # Scale to fit screen comfortably
        table_group.scale_to_fit_width(10.0).center()

        # ── TITLE ─────────────────────────────────────────────────────
        title = Text("Raw House Price Dataset", font_size=24,
                     color=CREAM, font="Courier New")
        title.to_edge(UP, buff=0.3)

        # Nudge table down so title has room
        table_group.shift(DOWN * 0.35)

        # ── LEGEND ────────────────────────────────────────────────────
        def legend_dot(color, label):
            dot = Dot(radius=0.09, color=color,
                      fill_color=color, fill_opacity=0.9)
            lbl = Text(label, font_size=13, color=DIM_TEXT,
                       font="Courier New")
            lbl.next_to(dot, RIGHT, buff=0.12)
            return VGroup(dot, lbl)

        leg1 = legend_dot(WARN, "inconsistent / missing / mixed unit")
        leg2 = legend_dot(GOLD, "duplicate row")
        legend = VGroup(leg1, leg2).arrange(RIGHT, buff=0.55)
        legend.to_edge(DOWN, buff=0.28)

        # ── ANIMATE IN ────────────────────────────────────────────────
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.6)
        self.play(
            FadeIn(header_bg),
            Create(all_lines),
            run_time=0.8
        )
        # Header row first
        self.play(
            LaggedStart(
                *[FadeIn(c, shift=UP * 0.08) for c in cell_mobs[0]],
                lag_ratio=0.08, run_time=0.7
            )
        )
        # Data rows, one by one
        self.play(
            LaggedStart(
                *[
                    LaggedStart(
                        *[FadeIn(c, shift=UP * 0.05) for c in row],
                        lag_ratio=0.04
                    )
                    for row in cell_mobs[1:]
                ],
                lag_ratio=0.18,
                run_time=1.8
            )
        )
        self.play(FadeIn(legend, shift=UP * 0.08), run_time=0.5)

        self.wait(2.0)

        # ── ANIMATE OUT ───────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(title, table_group, legend)),
            run_time=0.8
        )
        self.wait(0.2)