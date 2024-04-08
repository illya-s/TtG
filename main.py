from turtle import *
import turtle
from togif import init, GIFCreator

init(gs_windows_binary=r'C:\Program Files\gs\gs10.03.0\bin\gswin64c.exe')


class TaiwanFlag(GIFCreator):
    DURATION = 200
    # REBUILD = False

    def __init__(self, ratio, **kwargs):
        """
        ratio: 0.5 (40*60)  1 (80*120)  2 (160*240) ...
        """
        self.ratio = ratio
        GIFCreator.__init__(self, **kwargs)

    def show_size(self):
        print(f'width:{self.ratio * 120}\nheight:{self.ratio * 80}')

    @property
    def size(self):  # w, h
        return self.ratio * 200, self.ratio * 150

    def draw(self):
        def draw_square(size):
            for _ in range(4):
                turtle.speed(0.1)
                turtle.forward(size)
                turtle.right(90)

        # Set up turtle
        turtle.speed(1)  # Set turtle speed (1 is slowest)
        for i in range(36):
            draw_square(100)
            turtle.right(10)

        # turtle.tracer(True)
        turtle.hideturtle()


taiwan_flag = TaiwanFlag(2, name='abc2')
turtle.Screen().setup(taiwan_flag.size[0] + 40, taiwan_flag.size[1] + 40)  # margin = 40
# taiwan_flag.draw()
taiwan_flag.record(end_after=2500, fps=20)
