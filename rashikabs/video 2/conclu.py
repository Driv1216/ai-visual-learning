from manim import *

BG       = "#0F0F0F"
CREAM    = "#F2EFE7"
ACCENT   = "#4A9EFF"
DIM_TEXT = "#555555"
GOLD     = "#FFD166"
WARN     = "#FF6B6B"
GREEN    = "#06D6A0"
PURPLE   = "#C084FC"


def lbl_bg(text, color=GOLD, font_size=16):
    t = Text(text, font_size=font_size, color=color, font="Courier New")
    t.to_edge(DOWN, buff=0.45)
    bg = BackgroundRectangle(t, color="#000000", fill_opacity=1, buff=0.12)
    return VGroup(bg, t)


class ConclusionScene(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── TITLE ─────────────────────────────────────────────────────
        title = Text("Why Preprocessing Affects the Model",
                     font_size=24, color=CREAM, font="Courier New")
        title.to_edge(UP, buff=0.4)
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 1 — PIPELINE PROGRESSION (horizontal stages)
        # ═══════════════════════════════════════════════════════════════
        stages = [
            ("Raw",       WARN,   "messy\ntable"),
            ("Cleaned",   GOLD,   "consistent"),
            ("Encoded",   ACCENT, "numerical"),
            ("Scaled",    PURPLE, "balanced"),
            ("Engineered",GREEN,  "richer\nfeatures"),
            ("Split",     CREAM,  "train /\ntest"),
        ]

        stage_nodes = VGroup()
        stage_labels = VGroup()

        for name, color, sub in stages:
            circle = Circle(radius=0.55, color=color,
                            fill_color=color, fill_opacity=0.15,
                            stroke_width=2)
            name_t = Text(name, font_size=13, color=color,
                          font="Courier New")
            sub_t  = Text(sub,  font_size=11, color=DIM_TEXT,
                          font="Courier New", line_spacing=0.85)
            name_t.move_to(circle.get_center() + UP * 0.15)
            sub_t.move_to(circle.get_center() + DOWN * 0.18)
            node = VGroup(circle, name_t, sub_t)
            stage_nodes.add(node)

        stage_nodes.arrange(RIGHT, buff=0.45)
        stage_nodes.center().shift(UP * 0.6)

        # Arrows between nodes
        arrows = VGroup()
        for i in range(len(stage_nodes) - 1):
            a = Arrow(
                stage_nodes[i].get_right()   + RIGHT * 0.05,
                stage_nodes[i+1].get_left()  + LEFT  * 0.05,
                buff=0.05, color=DIM_TEXT,
                stroke_width=1.8,
                max_tip_length_to_length_ratio=0.25
            )
            arrows.add(a)

        pipeline_lbl = lbl_bg(
            "From raw chaos to model-ready data", color=ACCENT)
        self.play(FadeIn(pipeline_lbl), run_time=0.4)

        # Animate pipeline stage by stage
        for i, node in enumerate(stage_nodes):
            anims = [FadeIn(node, shift=UP * 0.10)]
            if i > 0:
                anims.append(GrowArrow(arrows[i - 1]))
            self.play(*anims, run_time=0.4)

        self.wait(12)
        self.play(
            FadeOut(VGroup(stage_nodes, arrows, pipeline_lbl)),
            run_time=0.6
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 2 — THREE SCENARIOS SIDE BY SIDE
        # ═══════════════════════════════════════════════════════════════
        scenario_lbl = lbl_bg(
            "Three scenarios — same model, different preprocessing")
        self.play(FadeIn(scenario_lbl), run_time=0.4)

        def scenario_card(num, label, data_desc, result_desc,
                          bar_h, card_color):
            """Build a scenario card with a mini bar chart."""
            # Card box
            card = RoundedRectangle(width=3.6, height=5.2,
                                     corner_radius=0.15,
                                     color=card_color,
                                     fill_color="#0D0D0D",
                                     fill_opacity=1,
                                     stroke_width=1.8)
            # Scenario number
            num_t = Text(f"Scenario {num}", font_size=15,
                         color=card_color, font="Courier New",
                         weight=BOLD)
            num_t.move_to(card.get_top() + DOWN * 0.35)

            # Label
            lbl_t = Text(label, font_size=13, color=CREAM,
                         font="Courier New")
            lbl_t.next_to(num_t, DOWN, buff=0.18)

            # Data description
            data_t = Text(data_desc, font_size=11, color=DIM_TEXT,
                          font="Courier New", line_spacing=1.0)
            data_t.next_to(lbl_t, DOWN, buff=0.22)

            # Mini bar chart (accuracy proxy)
            bar_max_h = 1.2
            bar = Rectangle(width=0.65, height=bar_h * bar_max_h,
                             fill_color=card_color,
                             fill_opacity=0.85, stroke_width=0)
            bar_base = Line(LEFT * 0.5, RIGHT * 0.5,
                            color=DIM_TEXT, stroke_width=1.2)
            bar.next_to(bar_base, UP, buff=0)
            bar_area = VGroup(bar_base, bar)
            bar_area.move_to(card.get_center() + DOWN * 0.55)

            # Result description
            result_t = Text(result_desc, font_size=11,
                            color=card_color, font="Courier New",
                            line_spacing=0.95)
            result_t.move_to(card.get_bottom() + UP * 0.45)

            return VGroup(card, num_t, lbl_t, data_t, bar_area, result_t)

        cards = VGroup(
            scenario_card(
                1, "No Preprocessing",
                "Raw data\nduplicates\nmissing values\nmixed scales",
                "Poor\nunstable\npredictions",
                0.25, WARN
            ),
            scenario_card(
                2, "Minimal Preprocessing",
                "Duplicates removed\nspellings fixed\nno scaling\nno engineering",
                "Better but\nlimited\ninsights",
                0.55, GOLD
            ),
            scenario_card(
                3, "Full Preprocessing",
                "Cleaned, encoded\nscaled, engineered\nproper split",
                "Reliable\ngeneralizable\npredictions",
                0.92, GREEN
            ),
        )
        cards.arrange(RIGHT, buff=0.45)
        cards.center().shift(DOWN * 0.15)

        # Animate cards in one by one
        for card in cards:
            self.play(FadeIn(card, shift=UP * 0.12), run_time=0.6)
            self.wait(0.3)

        self.wait(12)
        self.play(FadeOut(VGroup(cards, scenario_lbl)), run_time=0.6)

        # ═══════════════════════════════════════════════════════════════
        #  PART 3 — CORE INSIGHT (what model actually learns from)
        # ═══════════════════════════════════════════════════════════════
        insight_lbl = lbl_bg(
            "A model learns from representation — not just raw data",
            color=ACCENT)
        self.play(FadeIn(insight_lbl), run_time=0.4)

        learns_title = Text("A model learns from:", font_size=22,
                            color=CREAM, font="Courier New")
        learns_title.center().shift(UP * 1.8)
        self.play(FadeIn(learns_title, shift=DOWN * 0.08), run_time=0.5)

        factors = [
            ("Quality",        "of the data",         GREEN),
            ("Structure",      "of the data",         ACCENT),
            ("Representation", "of the data",         PURPLE),
        ]

        factor_rows = VGroup()
        for word, rest, color in factors:
            w = Text(word, font_size=24, color=color,
                     font="Courier New", weight=BOLD)
            r = Text(f"  {rest}", font_size=22, color=DIM_TEXT,
                     font="Courier New")
            row = VGroup(w, r).arrange(RIGHT, buff=0.05)
            factor_rows.add(row)

        factor_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.38)
        factor_rows.center().shift(DOWN * 0.15)

        self.play(
            LaggedStart(
                *[FadeIn(r, shift=RIGHT * 0.12) for r in factor_rows],
                lag_ratio=0.35, run_time=1.2
            )
        )
        self.wait(12)
        self.play(
            FadeOut(VGroup(learns_title, factor_rows, insight_lbl)),
            run_time=0.5
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 4 — FINAL CLOSING STATEMENT
        # ═══════════════════════════════════════════════════════════════
        line1 = Text(
            "Better preprocessing does not guarantee a perfect model.",
            font_size=20, color=DIM_TEXT, font="Courier New"
        )
        line2 = Text(
            "But poor preprocessing almost guarantees a poor one.",
            font_size=20, color=WARN, font="Courier New"
        )
        closing = VGroup(line1, line2).arrange(DOWN, buff=0.4)
        closing.center().shift(UP * 0.5)

        self.play(FadeIn(line1, shift=UP * 0.1), run_time=0.7)
        self.wait(4)
        self.play(FadeIn(line2, shift=UP * 0.1), run_time=0.7)
        self.wait(10)

        # Next video teaser
        next_card = RoundedRectangle(width=8.0, height=1.6,
                                      corner_radius=0.15,
                                      color=ACCENT,
                                      fill_color="#0A1628",
                                      fill_opacity=1, stroke_width=1.8)
        next_card.to_edge(DOWN, buff=0.7)
        next_lbl = Text("Next:  Choosing the Right ML Algorithm",
                        font_size=20, color=ACCENT, font="Courier New")
        next_lbl.move_to(next_card.get_center())
        next_group = VGroup(next_card, next_lbl)

        self.play(FadeIn(next_group, shift=UP * 0.12), run_time=0.6)
        self.wait(10)

        # ── FINAL FADE OUT ────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(title, closing, next_group)),
            run_time=1.0
        )
        self.wait(0.5)