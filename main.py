#    Copyright 2022 Lipatov Alexander
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import tkinter
import math

LINE_PRECISION_STEP = 0.01

WIDTH = 1024
HEIGHT = 768

POINT_SIZE = 3
LINE_SIZE = 2

SPLINE_COLOR = "gray"
SPLINE_POINT_COLOR = "orange"
BACKGROUND_COLOR = "white"


class P:
    """
    Point value object
    """
    x: float
    y: float

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other: "P") -> "P":
        return P(x=self.x+other.x, y=self.y + other.y)

    def __sub__(self, other: "P") -> "P":
        return P(x=self.x-other.x, y=self.y-other.y)
    
    def __mul__(self, k) -> "P":
        return P(x=self.x * k, y=self.y * k)
    
    def __rmul__(self, k) -> "P":
        return self.__mul__(k)

    def __truediv__(self, k) -> "P":
        return P(x=self.x / k, y=self.y / k)

    def __pow__(self, k: float) -> "P":
        return P(x=self.x ** k, y=self.y ** k)

    def __repr__(self) -> str:
        return f"Point<x={self.x}, y={self.y}>"


class BeizerSplines(tkinter.Frame):

    def __init__(self, parent: tkinter.Tk):
        super().__init__()

        self._parent = parent

        self._points: list[P] = list()

        self._cnv = tkinter.Canvas(self, bg=BACKGROUND_COLOR, width=WIDTH, height=HEIGHT)
        self._cnv.pack(fill=tkinter.BOTH, expand=True)

        self.pack(fill=tkinter.BOTH, expand=True)

        # attach action buttons
        show_helpers_btn = tkinter.Button(self, text="Show helpers", command=self._show_helpers)
        show_helpers_btn.pack(side=tkinter.RIGHT, padx=5, pady=5)

        hide_btn = tkinter.Button(self, text="Hide helpers", command=self._hide_helpers)
        hide_btn.pack(side=tkinter.RIGHT, padx=5, pady=5)

        reset_btn = tkinter.Button(self, text="Reset", command=self._reset)
        reset_btn.pack(side=tkinter.RIGHT, padx=5, pady=5)

        start_btn = tkinter.Button(self, text="Start", command=self._start)
        start_btn.pack(side=tkinter.RIGHT)

        # declare event bindings
        left_click_event = "<Button-1>"
        self._cnv.bind(left_click_event, self._set_point)

    def _center(self):
        center_x = (self.winfo_screenwidth() - WIDTH) / 2
        center_y = (self.winfo_screenheight() - HEIGHT) / 2

        self._parent.geometry('%dx%d+%d+%d' % (WIDTH, HEIGHT, center_x, center_y))

    def _set_point(self, event: tkinter.Event):
        """
        Event handler to set new point
        :param event: event
        """
        p = P(x=event.x, y=event.y)

        self._points.append(p)

        self._render_point(p, size=POINT_SIZE, color=SPLINE_POINT_COLOR)

    def _start(self):
        start_point = self._points[0]
        for i in range(len(self._points) - 2):
            p1, p2, p3 = self._points[i], self._points[i+1], self._points[i+2]

            aj1 = (p1 + p2) / 2
            aj2 = (p2 + p3) / 2

            lam = self._ratio_of_segments(p1, p2, p3)

            bj = (aj1 + lam * aj2) / (1 + lam);

            pi1 = aj1 - bj + p2
            pi2 = aj2 - bj + p2

            self._render_beizer_line(p1, start_point, pi1, p2)

            start_point = pi2

            # helpers
            self._render_point(aj1, size=3, color="blue", tag="helpers")
            self._render_point(aj2, size=3, color="blue", tag="helpers")
            self._render_point(bj, size=3, color="green", tag="helpers")
            self._render_point(pi1, size=3, color="purple", tag="helpers")
            self._render_point(pi2, size=3, color="purple", tag="helpers")

            self._render_line(aj1, aj2, width=LINE_SIZE, color="green", tag="helpers")
            self._render_line(pi1, pi2, width=LINE_SIZE, color="purple", tag="helpers")
            # straight between two points
            self._render_line(p1, p2, width=LINE_SIZE, color="blue", tag="helpers")

        # render last two
        self._render_beizer_line(self._points[-2], start_point, self._points[-1], self._points[-1])
        self._render_line(self._points[-2], self._points[-1], width=LINE_SIZE, color="blue", tag="helpers")

        # prevent starting from the whole start
        self._points = self._points[-1:]

    def _render_beizer_line(self, p1: P, p2: P, p3: P, p4: P):
        t = 0.001
        while t <= 1:
            new_point = self._beizer_next_point(p1, p2, p3, p4, t)

            self._render_point(new_point, size=LINE_SIZE)

            t += LINE_PRECISION_STEP

            self.after(1)
            self.update()

    def _render_point(self, p: P, size: float, color: str = SPLINE_POINT_COLOR, tag: str | None = None):
        x1, y1 = p.x - size + 1, p.y - size + 1
        x2, y2 = p.x + size - 1, p.y + size - 1

        self._cnv.create_oval(x1, y1, x2, y2, fill=color, tags=tag)

    def _render_line(self, a: P, b: P, width: float, color: str = "black", tag: str | None = None):
        self._cnv.create_line(a.x, a.y, b.x, b.y, fill=color, width=width, tags=tag)

    def _reset(self):
        self._cnv.delete("all")
        self._points = []

    def _hide_helpers(self):
        self._cnv.itemconfig("helpers", state="hidden")

    def _show_helpers(self):
        self._cnv.itemconfig("helpers", state="normal")

    @staticmethod
    def _ratio_of_segments(p1: P, p2: P, p3: P) -> float:
        return math.hypot(p2.x - p1.x, p2.x - p1.x) / math.hypot(p3.x - p2.x, p3.x - p2.x)

    @staticmethod
    def _beizer_next_point(c1: P, c2: P, c3: P, c4: P, t: float) -> P:
        return t ** 3 * (c4 - 3 * c3 + 3 * c2 - c1) + t ** 2 * (3 * c1 - 6 * c2 + 3 * c3) + t * (3 * c2 - 3 * c1) + c1

if __name__ == '__main__':
    base = tkinter.Tk()
    beizer = BeizerSplines(base)
    base.mainloop()
