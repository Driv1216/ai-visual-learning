from manim import *

BG    = "#0F0F0F"
CREAM = "#F2EFE7"
ACCENT = "#4A9EFF"
DIM_TEXT = "#555555"

class OpeningTitle(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── EPISODE BADGE ─────────────────────────────────────────────
        badge = Text("Video  2 / 5", font_size=22, color=DIM_TEXT)
        badge.to_edge(UP, buff=0.5)

        # ── MAIN TITLE ────────────────────────────────────────────────
        line1 = Text("Data Preprocessing", font_size=64,
                     color=CREAM)
        line2 = Text("& Preparation", font_size=64,
                     color=ACCENT)
        title = VGroup(line1, line2).arrange(DOWN, buff=0.3).center()

        # ── FADE IN ───────────────────────────────────────────────────
        self.play(FadeIn(badge, shift=DOWN * 0.1), run_time=0.6)
        self.play(
            FadeIn(line1, shift=UP * 0.15),
            run_time=0.8
        )
        self.play(
            FadeIn(line2, shift=UP * 0.15),
            run_time=0.8
        )

        # ── HOLD FOR 20 SECONDS ───────────────────────────────────────
        self.wait(20)

        self.play(
            FadeOut(badge),
            FadeOut(title),
            run_time=0.9
            )
        self.wait(0.3)