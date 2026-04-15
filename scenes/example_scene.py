from manim import *


STROKE_WIDTH = 2
FONT_SIZE = 36
ANIMATION_RUN_TIME = 1.0


class ExampleScene(Scene):
    def construct(self):
        t = Text("Hello, Manim!", font_size=FONT_SIZE)
        t.move_to(ORIGIN)
        self.play(Write(t), run_time=ANIMATION_RUN_TIME)
        self.wait(1)
