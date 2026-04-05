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

# ── house data (area sq ft, bedrooms) ────────────────────────────────
AREAS    = [950,  1100, 1200, 1350, 1500, 1800, 484]
BEDROOMS = [2,    3,    3,    3,    4,    3,    3  ]


def lbl_bg(text, color=GOLD, font_size=17):
    t = Text(text, font_size=font_size, color=color, font="Courier New")
    t.to_edge(DOWN, buff=0.45)
    bg = BackgroundRectangle(t, color="#000000", fill_opacity=1, buff=0.12)
    return VGroup(bg, t)


class FeatureScaling(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── TITLE ─────────────────────────────────────────────────────
        title = Text("Feature Scaling", font_size=28,
                     color=CREAM, font="Courier New")
        title.to_edge(UP, buff=0.4)
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 1 — UNSCALED SCATTER PLOT (distorted)
        # ═══════════════════════════════════════════════════════════════
        ax_raw = Axes(
            x_range=[0, 2500, 500],
            y_range=[0, 5, 1],
            x_length=7.0,
            y_length=4.5,
            axis_config={"color": DIM_TEXT, "stroke_width": 1.5,
                         "include_ticks": True,
                         "tick_size": 0.07},
            tips=False,
        )
        x_lbl_raw = Text("Area (sq ft)", font_size=16,
                         color=DIM_TEXT, font="Courier New")
        y_lbl_raw = Text("Bedrooms", font_size=16,
                         color=DIM_TEXT, font="Courier New").rotate(PI / 2)
        x_lbl_raw.next_to(ax_raw, DOWN, buff=0.2)
        y_lbl_raw.next_to(ax_raw, LEFT, buff=0.25)
        ax_raw_group = VGroup(ax_raw, x_lbl_raw, y_lbl_raw)
        ax_raw_group.center().shift(DOWN * 0.3)

        dots_raw = VGroup(*[
            Dot(ax_raw.c2p(AREAS[i], BEDROOMS[i]),
                radius=0.10, color=ACCENT, fill_opacity=0.85)
            for i in range(len(AREAS))
        ])

        self.play(FadeIn(ax_raw_group), run_time=0.7)
        self.play(
            LaggedStart(*[FadeIn(d, scale=0.4) for d in dots_raw],
                        lag_ratio=0.1, run_time=1.0)
        )

        intro = lbl_bg(
            "Area: 484–1800 sq ft     Bedrooms: 2–4     Very different scales!")
        self.play(FadeIn(intro), run_time=0.4)
        self.wait(15)

        # Draw a brace / annotation showing the narrow vertical strip
        brace = BraceBetweenPoints(
            ax_raw.c2p(0, 0), ax_raw.c2p(0, 5),
            direction=LEFT, color=WARN
        )
        brace_lbl = Text("tiny\nrange", font_size=13,
                         color=WARN, font="Courier New")
        brace_lbl.next_to(brace, LEFT, buff=0.1)

        brace2 = BraceBetweenPoints(
            ax_raw.c2p(0, 0), ax_raw.c2p(2500, 0),
            direction=DOWN, color=GOLD
        )
        brace2_lbl = Text("huge range", font_size=13,
                          color=GOLD, font="Courier New")
        brace2_lbl.next_to(brace2, DOWN, buff=0.1)

        self.play(
            Create(brace), FadeIn(brace_lbl),
            Create(brace2), FadeIn(brace2_lbl),
            run_time=0.7
        )
        self.wait(12)

        distort = lbl_bg(
            "1 bedroom change looks tiny vs 1 sq ft change — model gets confused",
            color=WARN)
        self.play(FadeOut(intro), FadeIn(distort), run_time=0.4)
        self.wait(12)
        self.play(
            FadeOut(VGroup(brace, brace_lbl, brace2, brace2_lbl,
                           distort, ax_raw_group, dots_raw)),
            run_time=0.6
        )

        # ═══════════════════════════════════════════════════════════════
        #  DEFINITION CARD
        # ═══════════════════════════════════════════════════════════════
        defn_title = Text("Feature Scaling", font_size=34,
                          color=ACCENT, font="Courier New")
        defn_body  = Text(
            "Adjusting the range and distribution of\n"
            "numerical features so they contribute equally.",
            font_size=20, color=CREAM, font="Courier New",
            line_spacing=1.3
        )
        defn = VGroup(defn_title, defn_body).arrange(DOWN, buff=0.4)
        defn.center()

        self.play(FadeIn(defn_title, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(defn_body,  shift=UP * 0.1), run_time=0.6)
        self.wait(12)
        self.play(FadeOut(defn), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 2 — NORMALIZATION
        # ═══════════════════════════════════════════════════════════════
        norm_title = Text("Method 1: Normalization  (Min-Max Scaling)",
                          font_size=22, color=GOLD, font="Courier New")
        norm_title.to_edge(UP, buff=0.45)

        formula_norm = MathTex(
            r"x' = \frac{x - x_{\min}}{x_{\max} - x_{\min}}",
            font_size=40, color=CREAM
        )
        formula_norm.center().shift(UP * 0.8)

        range_note = Text("All values mapped to  [0, 1]",
                          font_size=18, color=GREEN, font="Courier New")
        range_note.next_to(formula_norm, DOWN, buff=0.5)

        self.play(FadeIn(norm_title, shift=DOWN * 0.1), run_time=0.5)
        self.play(Write(formula_norm), run_time=0.8)
        self.play(FadeIn(range_note, shift=UP * 0.08), run_time=0.4)
        self.wait(10)

        # Show before/after small table for Area
        area_min, area_max = min(AREAS), max(AREAS)
        bed_min,  bed_max  = min(BEDROOMS), max(BEDROOMS)

        def norm(v, mn, mx):
            return round((v - mn) / (mx - mn), 2)

        norm_areas = [norm(a, area_min, area_max) for a in AREAS]
        norm_beds  = [norm(b, bed_min,  bed_max)  for b in BEDROOMS]

        # Small comparison: 3 rows sample
        sample_idx = [0, 3, 5]  # 950/2, 1350/3, 1800/3

        before_col = VGroup(*[
            Text(f"Area={AREAS[i]}  Beds={BEDROOMS[i]}",
                 font_size=15, color=CREAM, font="Courier New")
            for i in sample_idx
        ]).arrange(DOWN, buff=0.3)

        arrow_col = VGroup(*[
            Text("→", font_size=18, color=GOLD, font="Courier New")
            for _ in sample_idx
        ]).arrange(DOWN, buff=0.3)

        after_col = VGroup(*[
            Text(f"Area={norm_areas[i]}  Beds={norm_beds[i]}",
                 font_size=15, color=GREEN, font="Courier New")
            for i in sample_idx
        ]).arrange(DOWN, buff=0.3)

        comparison = VGroup(before_col, arrow_col, after_col).arrange(
            RIGHT, buff=0.4)
        comparison.next_to(range_note, DOWN, buff=0.4)

        self.play(
            LaggedStart(
                *[FadeIn(VGroup(before_col[j], arrow_col[j], after_col[j]),
                         shift=RIGHT * 0.08)
                  for j in range(len(sample_idx))],
                lag_ratio=0.25, run_time=1.2
            )
        )
        self.wait(12)
        self.play(
            FadeOut(VGroup(norm_title, formula_norm,
                           range_note, comparison)),
            run_time=0.5
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 3 — STANDARDIZATION
        # ═══════════════════════════════════════════════════════════════
        std_title = Text("Method 2: Standardization  (Z-Score)",
                         font_size=22, color=PURPLE, font="Courier New")
        std_title.to_edge(UP, buff=0.45)

        formula_std = MathTex(
            r"x' = \frac{x - \mu}{\sigma}",
            font_size=44, color=CREAM
        )
        formula_std.center().shift(UP * 0.8)

        std_props = VGroup(
            Text("mean  =  0", font_size=18,
                 color=GREEN, font="Courier New"),
            Text("standard deviation  =  1", font_size=18,
                 color=PURPLE, font="Courier New"),
        ).arrange(RIGHT, buff=0.8)
        std_props.next_to(formula_std, DOWN, buff=0.5)

        self.play(FadeIn(std_title, shift=DOWN * 0.1), run_time=0.5)
        self.play(Write(formula_std), run_time=0.8)
        self.play(
            LaggedStart(*[FadeIn(p, shift=UP * 0.08) for p in std_props],
                        lag_ratio=0.3, run_time=0.7)
        )
        self.wait(10)

        # sample values
        area_mean = np.mean(AREAS)
        area_std  = np.std(AREAS)
        bed_mean  = np.mean(BEDROOMS)
        bed_std   = np.std(BEDROOMS)

        def standardize(v, mu, sigma):
            return round((v - mu) / sigma, 2)

        std_areas = [standardize(a, area_mean, area_std) for a in AREAS]
        std_beds  = [standardize(b, bed_mean,  bed_std)  for b in BEDROOMS]

        before_col2 = VGroup(*[
            Text(f"Area={AREAS[i]}  Beds={BEDROOMS[i]}",
                 font_size=15, color=CREAM, font="Courier New")
            for i in sample_idx
        ]).arrange(DOWN, buff=0.3)

        arrow_col2 = VGroup(*[
            Text("→", font_size=18, color=PURPLE, font="Courier New")
            for _ in sample_idx
        ]).arrange(DOWN, buff=0.3)

        after_col2 = VGroup(*[
            Text(f"Area={std_areas[i]}  Beds={std_beds[i]}",
                 font_size=15, color=GREEN, font="Courier New")
            for i in sample_idx
        ]).arrange(DOWN, buff=0.3)

        comparison2 = VGroup(before_col2, arrow_col2, after_col2).arrange(
            RIGHT, buff=0.4)
        comparison2.next_to(std_props, DOWN, buff=0.4)

        self.play(
            LaggedStart(
                *[FadeIn(VGroup(before_col2[j], arrow_col2[j], after_col2[j]),
                         shift=RIGHT * 0.08)
                  for j in range(len(sample_idx))],
                lag_ratio=0.25, run_time=1.2
            )
        )
        self.wait(12)
        self.play(
            FadeOut(VGroup(std_title, formula_std,
                           std_props, comparison2)),
            run_time=0.5
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 4 — SCALED SCATTER PLOT (balanced)
        # ═══════════════════════════════════════════════════════════════
        ax_scaled = Axes(
            x_range=[0, 1.1, 0.2],
            y_range=[0, 1.1, 0.2],
            x_length=5.5,
            y_length=4.5,
            axis_config={"color": DIM_TEXT, "stroke_width": 1.5,
                         "include_ticks": True, "tick_size": 0.07},
            tips=False,
        )
        x_lbl_s = Text("Area (normalised)", font_size=15,
                       color=DIM_TEXT, font="Courier New")
        y_lbl_s = Text("Bedrooms (normalised)", font_size=15,
                       color=DIM_TEXT, font="Courier New").rotate(PI / 2)
        x_lbl_s.next_to(ax_scaled, DOWN, buff=0.2)
        y_lbl_s.next_to(ax_scaled, LEFT, buff=0.25)
        ax_s_group = VGroup(ax_scaled, x_lbl_s, y_lbl_s)
        ax_s_group.center().shift(DOWN * 0.3)

        dots_scaled = VGroup(*[
            Dot(ax_scaled.c2p(norm_areas[i], norm_beds[i]),
                radius=0.10, color=GREEN, fill_opacity=0.85)
            for i in range(len(AREAS))
        ])

        scaled_lbl = lbl_bg(
            "Both features now on equal footing — no distortion",
            color=GREEN)

        self.play(FadeIn(ax_s_group), run_time=0.6)
        self.play(
            LaggedStart(*[FadeIn(d, scale=0.4) for d in dots_scaled],
                        lag_ratio=0.1, run_time=1.0)
        )
        self.play(FadeIn(scaled_lbl), run_time=0.4)
        self.wait(12)
        self.play(
            FadeOut(VGroup(ax_s_group, dots_scaled, scaled_lbl)),
            run_time=0.6
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 5 — WHICH MODELS NEED SCALING
        # ═══════════════════════════════════════════════════════════════
        which_title = Text("Not every model needs scaling equally.",
                           font_size=24, color=CREAM, font="Courier New")
        which_title.to_edge(UP, buff=0.5)
        self.play(FadeIn(which_title, shift=DOWN * 0.1), run_time=0.5)

        # YES column
        yes_hdr = Text("Sensitive to scale", font_size=18,
                       color=WARN, font="Courier New")
        yes_items = VGroup(*[
            Text(t, font_size=16, color=CREAM, font="Courier New")
            for t in ["Linear Regression  ✔",
                      "KNN  ✔",
                      "SVM  ✔",
                      "Neural Networks  ✔"]
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        yes_col = VGroup(yes_hdr, yes_items).arrange(DOWN, buff=0.3,
                                                     aligned_edge=LEFT)
        yes_box = SurroundingRectangle(yes_col, color=WARN,
                                       stroke_width=1.5, buff=0.25,
                                       corner_radius=0.1)
        yes_panel = VGroup(yes_box, yes_col)

        # NO / LESS column
        no_hdr = Text("Less sensitive", font_size=18,
                      color=GREEN, font="Courier New")
        no_items = VGroup(*[
            Text(t, font_size=16, color=CREAM, font="Courier New")
            for t in ["Decision Trees  {…}",
                      "Random Forests  {…}",
                      "Gradient Boosting  {…}"]
        ]).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        no_col = VGroup(no_hdr, no_items).arrange(DOWN, buff=0.3,
                                                  aligned_edge=LEFT)
        no_box = SurroundingRectangle(no_col, color=GREEN,
                                      stroke_width=1.5, buff=0.25,
                                      corner_radius=0.1)
        no_panel = VGroup(no_box, no_col)

        panels = VGroup(yes_panel, no_panel).arrange(RIGHT, buff=1.2)
        panels.center().shift(DOWN * 0.2)

        self.play(
            FadeIn(yes_panel, shift=RIGHT * 0.15),
            run_time=0.7
        )
        self.wait(8)
        self.play(
            FadeIn(no_panel, shift=LEFT * 0.15),
            run_time=0.7
        )
        self.wait(10)

        nuance = lbl_bg(
            "Tree-based models split on thresholds — scale doesn't change the splits",
            color=DIM_TEXT)
        self.play(FadeIn(nuance), run_time=0.4)
        self.wait(12)

        # ── FINAL FADE OUT ────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(title, which_title,
                           yes_panel, no_panel, nuance)),
            run_time=0.8
        )
        self.wait(0.3)