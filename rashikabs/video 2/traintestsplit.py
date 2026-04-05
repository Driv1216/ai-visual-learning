from manim import *

BG       = "#0F0F0F"
CREAM    = "#F2EFE7"
ACCENT   = "#4A9EFF"
DIM_TEXT = "#555555"
GOLD     = "#FFD166"
WARN     = "#FF6B6B"
GREEN    = "#06D6A0"
PURPLE   = "#C084FC"

IDS      = ["101","102","103","104","105","106","107"]
AREAS    = ["1200","950","1100","1500","484","1800","1350"]
AGES     = ["14","9","9","16","12","19","0"]
BEDS     = ["3","2","3","4","3","3","3"]
FURN     = ["1","0","1","1","0","1","0"]
PRICES   = ["85","62","78","91","55","74","74"]


def lbl_bg(text, color=GOLD, font_size=16):
    t = Text(text, font_size=font_size, color=color, font="Courier New")
    t.to_edge(DOWN, buff=0.45)
    bg = BackgroundRectangle(t, color="#000000", fill_opacity=1, buff=0.12)
    return VGroup(bg, t)


def make_row_rect(label, row_ids, color, width=5.0, height=0.48):
    """A coloured rectangle row with ID labels inside."""
    rect = Rectangle(width=width, height=height,
                     fill_color=color, fill_opacity=0.18,
                     color=color, stroke_width=1.8)
    txt  = Text(f"Row {label}  ({row_ids})",
                font_size=13, color=color, font="Courier New")
    txt.move_to(rect.get_center())
    return VGroup(rect, txt)


class TrainTestSplit(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── TITLE ─────────────────────────────────────────────────────
        title = Text("Train-Test Split & Evaluation",
                     font_size=26, color=CREAM, font="Courier New")
        title.to_edge(UP, buff=0.4)
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 1 — FULL PREPROCESSED DATASET (compact table)
        # ═══════════════════════════════════════════════════════════════
        ready_lbl = lbl_bg(
            "Dataset: clean, encoded, scaled, engineered — ready?")
        self.play(FadeIn(ready_lbl), run_time=0.4)

        # Build compact table
        col_defs = [
            ("ID",   IDS,    CREAM),
            ("Area", AREAS,  CREAM),
            ("Age",  AGES,   CREAM),
            ("Beds", BEDS,   CREAM),
            ("Furn", FURN,   CREAM),
            ("Price",PRICES, GOLD),
        ]
        COL_W  = 0.90
        ROW_H  = 0.44
        N_COLS = len(col_defs)
        N_ROWS = len(IDS) + 1
        TW     = COL_W * N_COLS
        TH     = ROW_H * N_ROWS
        ox     = -TW / 2
        oy     =  TH / 2

        cell_grid = []
        line_mobs = []

        for r in range(N_ROWS):
            row_cells = []
            for c, (hdr, vals, col) in enumerate(col_defs):
                cx = ox + c * COL_W + COL_W / 2
                cy = oy - r * ROW_H - ROW_H / 2
                is_hdr = (r == 0)
                txt = hdr if is_hdr else vals[r - 1]
                color = ACCENT if is_hdr else col
                mob = Text(txt, font_size=12 if is_hdr else 11,
                           color=color, font="Courier New")
                mob.move_to([cx, cy, 0])
                row_cells.append(mob)
            cell_grid.append(row_cells)

        for r in range(N_ROWS + 1):
            y  = oy - r * ROW_H
            lw = 2.0 if r in (0, 1) else 0.7
            c  = ACCENT if r in (0, 1) else DIM_TEXT
            line_mobs.append(Line([ox, y, 0], [ox + TW, y, 0],
                                   color=c, stroke_width=lw))
        x_cur = ox
        for c in range(N_COLS + 1):
            lw = 2.0 if c in (0, N_COLS) else 0.7
            col = ACCENT if c in (0, N_COLS) else DIM_TEXT
            line_mobs.append(Line([x_cur, oy, 0], [x_cur, oy - TH, 0],
                                   color=col, stroke_width=lw))
            if c < N_COLS:
                x_cur += COL_W

        hdr_bg = Rectangle(width=TW, height=ROW_H,
                            fill_color="#0D1B2A", fill_opacity=1,
                            stroke_width=0)
        hdr_bg.move_to([0, oy - ROW_H / 2, 0])

        all_lines = VGroup(*line_mobs)
        all_cells = VGroup(*[m for row in cell_grid for m in row])
        full_tbl  = VGroup(hdr_bg, all_lines, all_cells)
        full_tbl.scale_to_fit_width(7.5).center().shift(DOWN * 0.25)

        self.play(FadeIn(hdr_bg), Create(all_lines), run_time=0.6)
        self.play(
            LaggedStart(
                *[FadeIn(cell_grid[0][c], shift=UP * 0.05)
                  for c in range(N_COLS)],
                lag_ratio=0.07, run_time=0.5
            )
        )
        self.play(
            LaggedStart(
                *[LaggedStart(
                    *[FadeIn(cell_grid[r][c], shift=UP * 0.04)
                      for c in range(N_COLS)],
                    lag_ratio=0.04)
                  for r in range(1, N_ROWS)],
                lag_ratio=0.12, run_time=1.2
            )
        )
        self.wait(10)

        almost = lbl_bg("Almost ready — but first, we need to split honestly.",
                        color=ACCENT)
        self.play(FadeOut(ready_lbl), FadeIn(almost), run_time=0.4)
        self.wait(8)
        self.play(FadeOut(VGroup(full_tbl, almost)), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 2 — WHY SPLIT? (student exam analogy)
        # ═══════════════════════════════════════════════════════════════
        analogy_lbl = lbl_bg(
            "Would you give a student the exam paper to study from?")
        self.play(FadeIn(analogy_lbl), run_time=0.4)

        student = Text("Student", font_size=20, color=CREAM,
                       font="Courier New")
        exam    = Text("Exam Paper", font_size=20, color=GOLD,
                       font="Courier New")
        student.center().shift(LEFT * 3 + UP * 0.5)
        exam.center().shift(RIGHT * 3 + UP * 0.5)

        bad_arrow = Arrow(student.get_right(), exam.get_left(),
                          color=WARN, buff=0.15, stroke_width=2.5)
        bad_lbl   = Text("trains on", font_size=14,
                         color=WARN, font="Courier New")
        bad_lbl.next_to(bad_arrow, UP, buff=0.1)

        self.play(FadeIn(student), FadeIn(exam), run_time=0.5)
        self.play(GrowArrow(bad_arrow), FadeIn(bad_lbl), run_time=0.5)

        result = Text("Aces it — but learned nothing.",
                      font_size=18, color=WARN, font="Courier New")
        result.center().shift(DOWN * 0.6)
        self.play(FadeIn(result, shift=UP * 0.08), run_time=0.5)
        self.wait(10)

        ml_equiv = Text(
            "Same with ML:  train & test on the same data\n"
            "→  memorises answers, fails on new data.",
            font_size=17, color=CREAM, font="Courier New",
            line_spacing=1.2
        )
        ml_equiv.next_to(result, DOWN, buff=0.35)
        ml_bg = BackgroundRectangle(ml_equiv, color="#0A0A0A",
                                    fill_opacity=1, buff=0.14)
        self.play(FadeIn(VGroup(ml_bg, ml_equiv), shift=UP * 0.08),
                  run_time=0.5)
        self.wait(10)
        self.play(
            FadeOut(VGroup(student, exam, bad_arrow,
                           bad_lbl, result, ml_bg, ml_equiv,
                           analogy_lbl)),
            run_time=0.5
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 3 — PROPER TRAIN / TEST SPLIT VISUAL
        # ═══════════════════════════════════════════════════════════════
        split_lbl = lbl_bg(
            "Split first — train only sees training data")
        self.play(FadeIn(split_lbl), run_time=0.4)

        # Full dataset bar
        full_bar = Rectangle(width=10.0, height=0.80,
                             fill_color=DIM_TEXT, fill_opacity=0.35,
                             color=CREAM, stroke_width=1.5)
        full_bar.center().shift(UP * 1.8)
        full_lbl = Text("Full Dataset  (7 rows)",
                        font_size=16, color=CREAM, font="Courier New")
        full_lbl.next_to(full_bar, UP, buff=0.14)

        self.play(FadeIn(full_bar), FadeIn(full_lbl), run_time=0.5)
        self.wait(3)

        # Split into 70 / 30
        train_bar = Rectangle(width=7.0, height=0.80,
                              fill_color=ACCENT, fill_opacity=0.25,
                              color=ACCENT, stroke_width=2.0)
        test_bar  = Rectangle(width=3.0, height=0.80,
                              fill_color=PURPLE, fill_opacity=0.25,
                              color=PURPLE, stroke_width=2.0)

        train_bar.next_to(full_bar.get_left(), RIGHT, buff=0).shift(RIGHT * 3.5)
        test_bar.next_to(train_bar, RIGHT, buff=0)

        train_pct = Text("Train  70%", font_size=15,
                         color=ACCENT, font="Courier New")
        test_pct  = Text("Test  30%", font_size=15,
                         color=PURPLE, font="Courier New")
        train_pct.move_to(train_bar.get_center())
        test_pct.move_to(test_bar.get_center())

        # Animate bar splitting
        self.play(
            Transform(full_bar, VGroup(train_bar, test_bar)),
            run_time=0.7
        )
        self.play(
            FadeIn(train_pct), FadeIn(test_pct), run_time=0.4
        )

        # Row allocation below
        train_rows = VGroup(*[
            make_row_rect(f"{i+1}", IDS[i], ACCENT, width=5.8)
            for i in range(5)
        ]).arrange(DOWN, buff=0.08)
        train_rows.shift(LEFT * 2.8 + DOWN * 0.5)

        test_rows = VGroup(*[
            make_row_rect(f"{i+1}", IDS[i], PURPLE, width=3.2)
            for i in range(5, 7)
        ]).arrange(DOWN, buff=0.08)
        test_rows.shift(RIGHT * 3.3 + DOWN * 0.3)

        train_tag = Text("Training Set", font_size=15,
                         color=ACCENT, font="Courier New")
        test_tag  = Text("Test Set", font_size=15,
                         color=PURPLE, font="Courier New")
        train_tag.next_to(train_rows, UP, buff=0.14)
        test_tag.next_to(test_rows,  UP, buff=0.14)

        self.play(
            LaggedStart(
                *[FadeIn(r, shift=DOWN * 0.08) for r in train_rows],
                lag_ratio=0.12, run_time=0.9
            ),
            FadeIn(train_tag), run_time=0.9
        )
        self.play(
            LaggedStart(
                *[FadeIn(r, shift=DOWN * 0.08) for r in test_rows],
                lag_ratio=0.2, run_time=0.6
            ),
            FadeIn(test_tag), run_time=0.6
        )

        honest = lbl_bg(
            "Model trains on Train Set.  Evaluated only on Test Set.",
            color=GREEN)
        self.play(FadeOut(split_lbl), FadeIn(honest), run_time=0.4)
        self.wait(12)

        self.play(
            FadeOut(VGroup(full_bar, full_lbl, train_bar, test_bar,
                           train_pct, test_pct,
                           train_rows, test_rows,
                           train_tag, test_tag, honest)),
            run_time=0.6
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 4 — LEAKAGE DURING SPLITTING  (wrong vs right path)
        # ═══════════════════════════════════════════════════════════════
        leak2_lbl = lbl_bg(
            "Watch out: preprocessing order matters too", color=WARN)
        self.play(FadeIn(leak2_lbl), run_time=0.4)

        # ── WRONG path ───────────────────────────────────────────────
        wrong_title = Text("✗  WRONG", font_size=18,
                           color=WARN, font="Courier New")
        wrong_title.to_edge(LEFT, buff=1.0).shift(UP * 1.8)

        wrong_steps = VGroup(*[
            Text(t, font_size=15, color=WARN, font="Courier New")
            for t in ["Full Dataset",
                      "↓  Preprocess  (scale, impute)",
                      "↓  Split  →  Train / Test"]
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        wrong_steps.next_to(wrong_title, DOWN, buff=0.25, aligned_edge=LEFT)

        wrong_box = SurroundingRectangle(
            VGroup(wrong_title, wrong_steps),
            color=WARN, stroke_width=1.5, buff=0.22, corner_radius=0.1
        )

        # ── RIGHT path ───────────────────────────────────────────────
        right_title = Text("✔  RIGHT", font_size=18,
                           color=GREEN, font="Courier New")
        right_title.to_edge(RIGHT, buff=1.0).shift(UP * 1.8)

        right_steps = VGroup(*[
            Text(t, font_size=15, color=GREEN, font="Courier New")
            for t in ["Full Dataset",
                      "↓  Split  →  Train / Test",
                      "↓  Preprocess Train only",
                      "↓  Apply same params to Test"]
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        right_steps.next_to(right_title, DOWN, buff=0.25,
                             aligned_edge=LEFT)

        right_box = SurroundingRectangle(
            VGroup(right_title, right_steps),
            color=GREEN, stroke_width=1.5, buff=0.22, corner_radius=0.1
        )

        # Divider
        divider = DashedLine(UP * 2.8, DOWN * 2.2,
                             color=DIM_TEXT, stroke_width=1.0,
                             dash_length=0.15)
        divider.center()

        self.play(Create(divider), run_time=0.4)
        self.play(
            FadeIn(wrong_title),
            LaggedStart(*[FadeIn(s, shift=DOWN * 0.06)
                          for s in wrong_steps], lag_ratio=0.2,
                        run_time=0.8),
            Create(wrong_box),
            run_time=0.8
        )
        self.wait(6)
        self.play(
            FadeIn(right_title),
            LaggedStart(*[FadeIn(s, shift=DOWN * 0.06)
                          for s in right_steps], lag_ratio=0.2,
                        run_time=0.9),
            Create(right_box),
            run_time=0.9
        )
        self.wait(6)

        # Explain the why
        why = Text(
            "Test set mean/min/max must not influence training.\n"
            "Split first — then fit preprocessing on Train only.",
            font_size=16, color=CREAM, font="Courier New",
            line_spacing=1.2
        )
        why.center().shift(DOWN * 1.8)
        why_bg = BackgroundRectangle(why, color="#0A0A0A",
                                     fill_opacity=1, buff=0.14)
        self.play(FadeIn(VGroup(why_bg, why), shift=UP * 0.08),
                  run_time=0.5)
        self.wait(12)

        # ── FADE OUT ──────────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(title, divider,
                           wrong_title, wrong_steps, wrong_box,
                           right_title, right_steps, right_box,
                           why_bg, why, leak2_lbl)),
            run_time=0.8
        )
        self.wait(0.3)