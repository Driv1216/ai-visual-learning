from manim import *

BG = "#0F0F0F"
CREAM = "#F2EFE7"
ACCENT = "#4A9EFF"
DIM_TEXT = "#555555"

class DataInfoKnowledge(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ================================================================
        # INTRO - Center aligned, stays for 10 seconds
        # ================================================================
        
        intro = Text("Data → Information → Knowledge", font_size=40, color=ACCENT, weight=BOLD)
        intro.move_to(ORIGIN)  # Center
        self.play(FadeIn(intro, scale=0.95), run_time=1.0)
        self.wait(10)  # 10 seconds
        self.play(FadeOut(intro), run_time=0.8)

        # ================================================================
        # PART 1: DATA
        # ================================================================

        # Data box - smaller size
        data_box = Rectangle(height=1.6, width=4.8, color=DIM_TEXT, fill_opacity=0.12, stroke_width=1.5)
        data_box.move_to([-3.2, -3.0, 0])

        data_label = Text("DATA", font_size=32, color=CREAM, weight=BOLD)
        data_label.move_to(data_box.get_center())

        # Definition - single line
        data_def = Text("Raw observations. Unprocessed facts.", font_size=18, color=DIM_TEXT)
        data_def.next_to(data_box, RIGHT, buff=0.6)

        # Images - side by side (not up and down), scale 0.4
        temp_img = ImageMobject("media/images/dik/temperatures.png")
        temp_img.scale(0.4)
        temp_img.move_to([1.5, 0.2, 0])
        
        heights_img = ImageMobject("media/images/dik/studentheights.jpg")
        heights_img.scale(0.4)
        heights_img.next_to(temp_img, RIGHT, buff=0.5)

        # Quote - moved up so it doesn't go off screen
        quote = Text("Data is what the world leaves behind\nwhen it is measured.", 
                     font_size=16, color=ACCENT, line_spacing=1.2)
        quote.next_to(data_box, DOWN, buff=0.4)

        # Animate DATA
        self.play(FadeIn(data_box, shift=RIGHT * 0.3), run_time=0.8)
        self.play(FadeIn(data_label, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(data_def, shift=LEFT * 0.3), run_time=0.7)
        self.play(FadeIn(temp_img, shift=UP * 0.2), FadeIn(heights_img, shift=UP * 0.2), run_time=0.8)
        self.wait(4)
        
        self.play(FadeOut(temp_img), FadeOut(heights_img), run_time=0.6)
        self.play(FadeIn(quote, shift=UP * 0.2), run_time=0.8)
        self.wait(5.0)
        self.play(FadeOut(quote), run_time=0.6)
        self.wait(0.5)

        # ================================================================
        # PART 2: INFORMATION
        # ================================================================

        # Arrow - adjusted so it doesn't go inside next box
        arrow_up = Arrow(
            start=data_box.get_top() + DOWN * 0.05,
            end=data_box.get_top() + UP * 1.0,
            color=ACCENT,
            stroke_width=3,
            tip_length=0.12
        )

        info_box = Rectangle(height=1.6, width=4.8, color=DIM_TEXT, fill_opacity=0.12, stroke_width=1.5)
        info_box.move_to(data_box.get_center() + UP * 2.4)

        info_label = Text("INFORMATION", font_size=32, color=CREAM, weight=BOLD)
        info_label.move_to(info_box.get_center())

        info_def = Text("Structured, interpretable data.", font_size=18, color=DIM_TEXT)
        info_def.next_to(info_box, RIGHT, buff=0.6)

        # Images for information - side by side, below the definition line
        temp_graph = ImageMobject("media/images/dik/temperaturelg.jpg")
        temp_graph.scale(0.5)
        temp_graph.align_to(info_def, DOWN)
        temp_graph.move_to([1.2, -0.8, 0])
        
        student_graph = ImageMobject("media/images/dik/studentheightsgraph.jpg")
        student_graph.scale(0.4)
        student_graph.align_to(info_def, DOWN)
        student_graph.next_to(temp_graph, RIGHT, buff=0.5)

        self.play(FadeOut(data_def), run_time=0.5)
        self.play(Create(arrow_up), run_time=0.7)
        self.play(FadeIn(info_box, shift=DOWN * 0.3), run_time=0.8)
        self.play(FadeIn(info_label, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(info_def, shift=LEFT * 0.3), run_time=0.7)
        self.play(FadeIn(temp_graph, shift=UP * 0.2), FadeIn(student_graph, shift=UP * 0.2), run_time=0.8)
        
        self.wait(5.0)
        
        self.play(FadeOut(temp_graph), FadeOut(student_graph), run_time=0.6)
        self.wait(1.0)

        # ================================================================
        # PART 3: KNOWLEDGE
        # ================================================================

        arrow_up2 = Arrow(
            start=info_box.get_top() + DOWN * 0.05,
            end=info_box.get_top() + UP * 1.0,
            color=ACCENT,
            stroke_width=3,
            tip_length=0.12
        )

        know_box = Rectangle(height=1.6, width=4.8, color=DIM_TEXT, fill_opacity=0.12, stroke_width=1.5)
        know_box.move_to(info_box.get_center() + UP * 2.4)

        know_label = Text("KNOWLEDGE", font_size=32, color=CREAM, weight=BOLD)  # White/cream color
        know_label.move_to(know_box.get_center())

        know_def = Text("Patterns learned from information.", font_size=18, color=DIM_TEXT)
        know_def.next_to(know_box, RIGHT, buff=0.6)

        self.play(FadeOut(info_def), run_time=0.5)
        self.play(Create(arrow_up2), run_time=0.7)
        self.play(FadeIn(know_box, shift=DOWN * 0.3), run_time=0.8)
        self.play(FadeIn(know_label, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(know_def, shift=LEFT * 0.3), run_time=0.7)
        
        self.wait(10)

        # ================================================================
        # FADE OUT EVERYTHING - Complete fade of all elements
        # ================================================================

        self.play(
            FadeOut(know_def),
            FadeOut(info_def),
            FadeOut(data_def),
            FadeOut(arrow_up),
            FadeOut(arrow_up2),
            FadeOut(data_box),
            FadeOut(info_box),
            FadeOut(know_box),
            FadeOut(data_label),
            FadeOut(info_label),
            FadeOut(know_label),
            run_time=1.0
        )

        self.wait(1.0)

        # ================================================================
        # HOUSE PRICE PATTERNS
        # ================================================================

        house_title = Text("House Price Dataset", font_size=28, color=ACCENT)
        house_title.to_edge(UP, buff=0.6)

        # House price image
        house_img = ImageMobject("media/images/dik/housepricesnippet.PNG")
        house_img.scale_to_fit_width(5)
        house_img.move_to([-1.5, 0.3, 0])

        # Patterns title and patterns - stacked vertically, NOT overlapping image
        pattern_title = Text("Patterns that emerge:", font_size=18, color=DIM_TEXT)
        pattern_title.next_to(house_img, RIGHT, buff=0.1)
        pattern_title.align_to(house_img, UP)

        pattern1 = Text("📈 Larger area → Higher price", font_size=16, color=ACCENT)
        pattern2 = Text("📍 Certain locations cost more", font_size=16, color=ACCENT)
        pattern3 = Text("🏠 Newer houses command premium", font_size=16, color=ACCENT)

        patterns = VGroup(pattern1, pattern2, pattern3).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        patterns.next_to(pattern_title, DOWN, buff=0.2)  # Below the title, not over the image
        patterns.next_to(house_img, RIGHT, buff=1.0)
        patterns.shift(RIGHT * 0.3)

        self.play(FadeIn(house_title, shift=UP * 0.2), run_time=0.6)
        self.play(FadeIn(house_img, shift=UP * 0.2), run_time=0.7)
        self.play(FadeIn(pattern_title), run_time=0.5)
        self.play(LaggedStart(FadeIn(patterns, shift=LEFT * 0.1), lag_ratio=0.12), run_time=0.8)
        
        self.wait(5.0)
        
        self.play(FadeOut(house_title), FadeOut(house_img), FadeOut(pattern_title), FadeOut(patterns), run_time=0.7)

        self.wait(1.0)

        # ================================================================
        # RETURN - Fade in all elements
        # ================================================================

        # Recreate all boxes and labels
        data_box = Rectangle(height=1.6, width=4.8, color=DIM_TEXT, fill_opacity=0.12, stroke_width=1.5)
        data_box.move_to([-3.2, -3.0, 0])
        data_label = Text("DATA", font_size=32, color=CREAM, weight=BOLD)
        data_label.move_to(data_box.get_center())

        info_box = Rectangle(height=1.6, width=4.8, color=DIM_TEXT, fill_opacity=0.12, stroke_width=1.5)
        info_box.move_to(data_box.get_center() + UP * 2.4)
        info_label = Text("INFORMATION", font_size=32, color=CREAM, weight=BOLD)
        info_label.move_to(info_box.get_center())

        know_box = Rectangle(height=1.6, width=4.8, color=DIM_TEXT, fill_opacity=0.12, stroke_width=1.5)
        know_box.move_to(info_box.get_center() + UP * 2.4)
        know_label = Text("KNOWLEDGE", font_size=32, color=CREAM, weight=BOLD)
        know_label.move_to(know_box.get_center())

        data_def = Text("Raw observations. Unprocessed facts.", font_size=18, color=DIM_TEXT)
        data_def.next_to(data_box, RIGHT, buff=0.6)

        info_def = Text("Structured, interpretable data.", font_size=18, color=DIM_TEXT)
        info_def.next_to(info_box, RIGHT, buff=0.6)

        know_def = Text("Patterns learned from information.", font_size=18, color=DIM_TEXT)
        know_def.next_to(know_box, RIGHT, buff=0.6)

        # Fade in everything
        self.play(
            FadeIn(data_box), FadeIn(data_label), FadeIn(data_def),
            FadeIn(info_box), FadeIn(info_label), FadeIn(info_def),
            FadeIn(know_box), FadeIn(know_label), FadeIn(know_def),
            run_time=1.0
        )

        self.wait(3.0)

        # ================================================================
        # FINAL MESSAGE
        # ================================================================

        # Fade out everything except background
        self.play(
            FadeOut(data_box), FadeOut(data_label), FadeOut(data_def),
            FadeOut(info_box), FadeOut(info_label), FadeOut(info_def),
            FadeOut(know_box), FadeOut(know_label), FadeOut(know_def),
            run_time=0.8
        )

        # Final centered message
        final_line1 = Text("Machine learning models do not create", font_size=22, color=DIM_TEXT)
        final_line2 = Text("knowledge directly from chaos.", font_size=24, color=CREAM)
        final_line3 = Text("They require information-rich input.", font_size=26, color=ACCENT, weight=BOLD)

        final_group = VGroup(final_line1, final_line2, final_line3).arrange(DOWN, buff=0.2)
        final_group.move_to(ORIGIN)

        self.play(FadeIn(final_line1, shift=UP * 0.1), run_time=1.5)
        self.play(FadeIn(final_line2, shift=UP * 0.1), run_time=1.5)
        self.play(FadeIn(final_line3, shift=UP * 0.1), run_time=2.0)
        
        self.wait(3)

        bridge = Text("That bridge is called... Data Preprocessing", font_size=20, color=ACCENT)
        bridge.next_to(final_group, DOWN, buff=0.5)
        
        self.play(FadeIn(bridge, shift=UP * 0.1), run_time=0.6)
        self.wait(2)
        
        self.play(FadeOut(final_line1), FadeOut(final_line2), FadeOut(final_line3), FadeOut(bridge), run_time=0.8)
        self.wait(0.5)