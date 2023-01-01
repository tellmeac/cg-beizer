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

# 0 < t < 1
LINE_PRECISION_STEP = 0.001

WIDTH = 1024
HEIGHT = 768

POINT_SIZE = 4
LINE_SIZE = 2

SPLINE_COLOR = "gray"
SPLINE_POINT_COLOR = "green"
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

        self._reset_btn = tkinter.Button(self, text="Reset", command=self._reset)
        self._reset_btn.pack(side=tkinter.RIGHT, padx=5, pady=5)

        self._start_btn = tkinter.Button(self, text="Start", command=self._start)
        self._start_btn.pack(side=tkinter.RIGHT)

        # declare event bindings
        left_click_event = "<Button-1>"
        self._cnv.bind(left_click_event, self._set_point)

    def _set_point(self, event: tkinter.Event):
        """
        Event handler to set new point
        :param event: event
        """
        p = P(x=event.x, y=event.y)
        self._points.append(p)
        self._render_point(p, size=POINT_SIZE, color=SPLINE_POINT_COLOR)

    def _start(self):
        self._start_btn["state"] = tkinter.DISABLED
        self._reset_btn["state"] = tkinter.ACTIVE

        helpers_lines: list[(P, P)] = list()
        herlpers_points: list[P] = list()

        p4 = self._points[0] # used in two iterations
        for i in range(len(self._points) - 2):
            p1, p2, p3 = self._points[i], self._points[i+1], self._points[i+2]

            # Relation between two vectors (p1, p2) and (p2, p3)
            rel = math.hypot(p2.x - p1.x, p2.y - p1.y) / math.hypot(p3.x - p2.x, p3.y - p2.y)

            a1 = (p1 + p2) / 2
            a2 = (p2 + p3) / 2

            bj = (a1 + rel * a2) / (1 + rel);

            h1 = a1 - bj + p2
            h2 = a2 - bj + p2

            self._render_beizer_line(p1, p4, h1, p2)
            helpers_lines.append((h1, h2))
            herlpers_points.extend([p1, p4, h1, p2])

            p4 = h2

        # Render last, use last but one point twice.
        self._render_beizer_line(self._points[-2], p4, self._points[-1], self._points[-1])
        herlpers_points.extend([self._points[-2], p4, self._points[-1], self._points[-1]])

        # Render helpers at the end.
        for a, b in helpers_lines:
            self._render_line(a, b, width=LINE_SIZE, color="orange", tag="helpers")
        for a in herlpers_points:
            self._render_point(a, size=POINT_SIZE, color="red", tag="helpers")

    def _render_beizer_line(self, p0: P, p1: P, p2: P, p3: P):
        t = 0.001
        while t <= 1:
            current_point = self._beizer_point(p0, p1, p2, p3, t)

            self._render_point(current_point, size=LINE_SIZE - 2)

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
        self._start_btn["state"] = tkinter.ACTIVE
        self._reset_btn["state"] = tkinter.DISABLED
        self._cnv.delete("all")
        self._points = list()

    def _hide_helpers(self):
        self._cnv.itemconfig("helpers", state="hidden")

    def _show_helpers(self):
        self._cnv.itemconfig("helpers", state="normal")

    @staticmethod
    def _beizer_point(p1: P, p2: P, p3: P, p4: P, t: float) -> P:
        """
        Returns cubic beizer point by 4 base points and t in [0, 1] 
        """
        return t ** 3 * (p4 - 3 * p3 + 3 * p2 - p1) + t ** 2 * (3 * p1 - 6 * p2 + 3 * p3) + t * (3 * p2 - 3 * p1) + p1

if __name__ == '__main__':
    base = tkinter.Tk()
    beizer = BeizerSplines(base)
    base.mainloop()
