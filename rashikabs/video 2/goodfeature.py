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


class GoodFeature(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── TITLE ─────────────────────────────────────────────────────
        title = Text("What Makes a Good Feature?",
                     font_size=26, color=CREAM, font="Courier New")
        title.to_edge(UP, buff=0.4)
        self.play(FadeIn(title, shift=DOWN * 0.1), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 1 — OPENING STATEMENT + CHECKLIST
        # ═══════════════════════════════════════════════════════════════
        opening = Text(
            "Not every feature is useful\njust because it exists.",
            font_size=34, color=ACCENT, font="Courier New",
            line_spacing=1.2
        )
        opening.center().shift(UP * 0.8)
        self.play(Write(opening), run_time=0.9)
        self.wait(8)
        self.play(opening.animate.scale(0.55).to_edge(UP, buff=1.0),
                  run_time=0.6)

        # Checklist — four attributes
        attributes = [
            ("Relevant",                  "Tied to the target variable.",          GREEN),
            ("Informative",               "Actually varies and carries signal.",    GREEN),
            ("Consistent",                "Measured the same way every time.",      GREEN),
            ("Available at prediction",   "Can we know it when we need it?",        GOLD),
        ]

        check_items = VGroup()
        for attr, desc, color in attributes:
            tick   = Text("✔", font_size=20, color=color, font="Courier New")
            attr_t = Text(attr, font_size=19, color=color,
                          font="Courier New", weight=BOLD)
            desc_t = Text(f"  —  {desc}", font_size=16,
                          color=DIM_TEXT, font="Courier New")
            row = VGroup(tick, attr_t, desc_t).arrange(RIGHT, buff=0.18)
            check_items.add(row)

        check_items.arrange(DOWN, aligned_edge=LEFT, buff=0.32)
        check_items.center().shift(DOWN * 0.3)

        self.play(
            LaggedStart(
                *[FadeIn(row, shift=RIGHT * 0.1) for row in check_items],
                lag_ratio=0.3, run_time=1.4
            )
        )
        self.wait(14)
        self.play(FadeOut(VGroup(opening, check_items)), run_time=0.5)

        # ═══════════════════════════════════════════════════════════════
        #  PART 2 — STUDENT EXAM LEAKAGE EXAMPLE
        # ═══════════════════════════════════════════════════════════════
        exam_lbl = lbl_bg("Classic leakage example: Student Exam")
        self.play(FadeIn(exam_lbl), run_time=0.4)

        # Goal statement
        goal = Text("Goal: Predict whether a student will pass the exam.",
                    font_size=18, color=CREAM, font="Courier New")
        goal.center().shift(UP * 2.3)
        self.play(FadeIn(goal, shift=DOWN * 0.08), run_time=0.5)

        # Features list
        features_data = [
            ("Attendance",          GREEN,  "✔  Good feature"),
            ("Practice Test Score", GREEN,  "✔  Good feature"),
            ("Final Exam Marks",    WARN,   "✗  LEAKAGE"),
        ]

        feat_rows = VGroup()
        badges    = VGroup()
        for feat, color, badge_txt in features_data:
            feat_mob  = Text(f"  {feat}", font_size=19,
                             color=color, font="Courier New")
            badge_mob = Text(badge_txt, font_size=15,
                             color=color, font="Courier New")
            row = VGroup(feat_mob, badge_mob).arrange(RIGHT, buff=0.6)
            feat_rows.add(row)

        feat_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        feat_rows.center().shift(DOWN * 0.1)

        # Bullet dots
        dots = VGroup(*[
            Dot(radius=0.09,
                color=features_data[i][1],
                fill_opacity=0.9).next_to(feat_rows[i], LEFT, buff=0.15)
            for i in range(len(features_data))
        ])

        self.play(
            LaggedStart(
                *[FadeIn(VGroup(dots[i], feat_rows[i]), shift=RIGHT * 0.1)
                  for i in range(len(features_data))],
                lag_ratio=0.3, run_time=1.2
            )
        )
        self.wait(8)

        # Flash the leakage row
        leak_row = feat_rows[2]
        leak_dot = dots[2]
        self.play(
            Indicate(VGroup(leak_dot, leak_row),
                     color=WARN, scale_factor=1.12),
            run_time=0.6
        )

        # Leakage explanation box
        leak_box_txt = Text(
            "Final Exam Marks IS the answer.\n"
            "It cannot exist before the exam.",
            font_size=16, color=WARN, font="Courier New",
            line_spacing=1.2
        )
        leak_box_txt.next_to(feat_rows, DOWN, buff=0.4)
        leak_bg = BackgroundRectangle(leak_box_txt,
                                      color="#1A0000",
                                      fill_opacity=1, buff=0.18)
        leak_box = VGroup(leak_bg, leak_box_txt)
        self.play(FadeIn(leak_box, shift=UP * 0.08), run_time=0.5)
        self.wait(12)

        self.play(
            FadeOut(VGroup(goal, feat_rows, dots, leak_box, exam_lbl)),
            run_time=0.5
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 3 — HOUSE PRICE LEAKAGE EXAMPLE
        # ═══════════════════════════════════════════════════════════════
        house_lbl = lbl_bg(
            "Same problem in our house price dataset")
        self.play(FadeIn(house_lbl), run_time=0.4)

        goal2 = Text("Goal: Predict the price of a new listing.",
                     font_size=18, color=CREAM, font="Courier New")
        goal2.center().shift(UP * 2.3)
        self.play(FadeIn(goal2, shift=DOWN * 0.08), run_time=0.5)

        bad_feat = Text(
            "Bad feature:  \"Days on Market before sale\"",
            font_size=20, color=WARN, font="Courier New"
        )
        bad_feat.center().shift(UP * 0.9)

        reason = Text(
            "We are predicting before the listing sells.\n"
            "Days on Market is future information —\n"
            "it does not exist yet.",
            font_size=17, color=CREAM, font="Courier New",
            line_spacing=1.25
        )
        reason.next_to(bad_feat, DOWN, buff=0.45)
        reason_bg = BackgroundRectangle(reason, color="#0A0A0A",
                                        fill_opacity=1, buff=0.15)
        reason_box = VGroup(reason_bg, reason)

        self.play(FadeIn(bad_feat, shift=DOWN * 0.08), run_time=0.5)
        self.wait(5)
        self.play(FadeIn(reason_box, shift=UP * 0.08), run_time=0.5)
        self.wait(12)

        self.play(
            FadeOut(VGroup(goal2, bad_feat, reason_box, house_lbl)),
            run_time=0.5
        )

        # ═══════════════════════════════════════════════════════════════
        #  PART 4 — AVAILABILITY TEST (final checklist)
        # ═══════════════════════════════════════════════════════════════
        avail_lbl = lbl_bg(
            "The availability test: can we know this at prediction time?")
        self.play(FadeIn(avail_lbl), run_time=0.4)

        avail_title = Text(
            "For a new house listing — what do we know?",
            font_size=20, color=CREAM, font="Courier New"
        )
        avail_title.center().shift(UP * 2.2)
        self.play(FadeIn(avail_title, shift=DOWN * 0.08), run_time=0.5)

        avail_features = [
            ("Area (sq ft)",            "✔", GREEN,  True),
            ("Location",                "✔", GREEN,  True),
            ("Year Built",              "✔", GREEN,  True),
            ("Number of offers received","✗", WARN,   False),
            ("Final sale price",         "✗", WARN,   False),
        ]

        avail_rows = VGroup()
        for feat, mark, color, _ in avail_features:
            mark_mob = Text(mark,  font_size=22, color=color,
                            font="Courier New")
            feat_mob = Text(f"  {feat}", font_size=18, color=color,
                            font="Courier New")
            row = VGroup(mark_mob, feat_mob).arrange(RIGHT, buff=0.18)
            avail_rows.add(row)

        avail_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.30)
        avail_rows.center().shift(DOWN * 0.15)

        # Animate good features first, then bad
        good_rows = VGroup(*[avail_rows[i] for i in range(3)])
        bad_rows  = VGroup(*[avail_rows[i] for i in range(3, 5)])

        self.play(
            LaggedStart(
                *[FadeIn(r, shift=RIGHT * 0.1) for r in good_rows],
                lag_ratio=0.2, run_time=0.9
            )
        )
        self.wait(5)
        self.play(
            LaggedStart(
                *[FadeIn(r, shift=RIGHT * 0.1) for r in bad_rows],
                lag_ratio=0.3, run_time=0.8
            )
        )
        self.wait(4)

        # Flash the bad rows
        self.play(
            Indicate(bad_rows, color=WARN, scale_factor=1.08),
            run_time=0.6
        )

        self.wait(14)

        # Closing thought
        closing = lbl_bg(
            "This critical thinking about features is a hallmark of effective ML.",
            color=ACCENT, font_size=15)
        self.play(FadeOut(avail_lbl), FadeIn(closing), run_time=0.4)
        self.wait(12)

        # ── FADE OUT ──────────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(title, avail_title,
                           avail_rows, closing)),
            run_time=0.8
        )
        self.wait(0.3)