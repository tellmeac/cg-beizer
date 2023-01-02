import logging
import sys
from pathlib import Path

import cv2.cv2 as cv2
import numpy as np
import tkinter
import math
from tkinter.filedialog import askopenfilename


class Image:
    def __init__(self, path: Path):
        """
        :param path: image path
        """
        self._name = path.name
        self._img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        self._points = []

    @property
    def height(self):
        return self._img.shape[0]

    @property
    def width(self):
        return self._img.shape[1]

    def bilinear_filtering(self) -> np.ndarray:
        """
        :return: возвращает новое преобразованное изображение
        """
        if len(self._points) < 6:
            raise Exception("expected to have at least 6 points to work with")

        a = self._transform_matrix()
        ia = np.linalg.inv(a[:, :2])

        result = np.zeros(self._img.shape, np.uint8)
        for i in range(self.height):
            for j in range(self.width):
                # (1,1) shaped arrays
                x, y = np.dot(ia, np.array([[i], [j]]) - a[:, 2:])
                x, y = x[0], y[0]

                if not (0 <= x < self.height and 0 <= y < self.width):
                    continue

                # Barriers
                ceil_x = math.ceil(x)
                ceil_x = ceil_x if ceil_x < self.height else math.floor(x)

                ceil_y = math.ceil(y)
                ceil_y = ceil_y if ceil_y < self.width else math.floor(y)

                top_right = np.array(self._img[math.floor(x), math.floor(y)])
                bot_right = np.array(self._img[ceil_x, math.floor(y)])
                top_left = np.array(self._img[math.floor(x), ceil_y])
                bot_left = np.array(self._img[ceil_x, ceil_y])

                result[i, j] = (
                    (ceil_x - x) * top_right + (x - math.floor(x)) * bot_right
                ) * (ceil_y - y) + (
                    (ceil_x - x) * top_left + (x - math.floor(x)) * bot_left
                ) * (
                    y - math.floor(y)
                )
        return result

    def simple_transform(self) -> np.ndarray:
        """
        Простая трансформация.
        :return: новое преобразованное изображение
        """
        if len(self._points) < 6:
            raise Exception("expected to have at least 6 points to work with")

        a = self._transform_matrix()
        ia = np.linalg.inv(a[:, :2])

        # For every (x`, y`) new pixel in result search (x, y) of old image with A^-1
        result = np.zeros(self._img.shape, np.uint8)
        for i in range(self.height):
            for j in range(self.width):
                x, y = np.dot(ia, np.array([[i], [j]]) - a[:, 2:])
                x, y = round(x[0]), round(y[0])

                if 0 <= x < self.height and 0 <= y < self.width:
                    result[i, j] = self._img[x, y]
        return result

    def show(self):
        cv2.namedWindow(self._name)
        cv2.setMouseCallback(self._name, self._draw_point)
        while True:
            cv2.imshow(self._name, self._img)
            if cv2.waitKey(20) == 13:
                break
        cv2.destroyAllWindows()

    def _transform_matrix(self) -> np.ndarray:
        """
        Генерирует матрицу трансформации по 3 входным точкам и 3 точкам соответствия.
        :return: Матрица трансформации (3x3)
        """

        input_cords = np.array([
            [self._points[0][0], self._points[1][0], self._points[2][0]],
            [self._points[0][1], self._points[1][1], self._points[2][1]],
            [0, 0, 1],
        ])

        out_points = np.array(
            [[self._points[3]], [self._points[4]], [self._points[5]]], np.float32
        )
        tr_points = np.array(
            (out_points[0].T, out_points[1].T, out_points[2].T), np.float32
        )

        c1 = (
            tr_points[0] * np.linalg.det(input_cords[1:, 1:])
            - tr_points[1]
            * np.linalg.det(np.hstack((input_cords[1:, :1], input_cords[1:, 2:])))
            + tr_points[2] * np.linalg.det(input_cords[1:, :2])
        )
        c2 = (
            tr_points[0]
            * np.linalg.det(np.vstack((input_cords[:1, 1:], input_cords[2:, 1:])))
            - tr_points[1]
            * np.linalg.det(
                np.array(
                    [
                        [input_cords[0, 0], input_cords[0, 2]],
                        [input_cords[2, 0], input_cords[2, 2]],
                    ]
                )
            )
            + tr_points[2]
            * np.linalg.det(np.vstack((input_cords[:1, :2], input_cords[2:, :2])))
        ) * -1
        c3 = (
            tr_points[0] * np.linalg.det(input_cords[:2, 1:])
            - tr_points[1]
            * np.linalg.det(np.hstack((input_cords[:2, :1], input_cords[:2, 2:])))
            + tr_points[2] * np.linalg.det(input_cords[:2, :2])
        )
        return np.hstack((c1, c2, c3)) / np.linalg.det(input_cords)

    def _draw_point(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self._points.append([x, y])
            cv2.circle(self._img, (x, y), 5, (255, 255, 0), -1)


class App(tkinter.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.window_height = 480
        self.window_width = 720
        self.pack(fill=tkinter.BOTH, expand=True)
        self.center_window()

        self._run()

    def _run(self):
        try:
            selected_path = askopenfilename()
            path = Path(selected_path)
        except (TypeError, IsADirectoryError) as exc:
            logging.error("failed to select image: %s", exc)
            sys.exit(1)

        img = Image(path)
        img.show()

        generated_img = img.simple_transform()
        self._apply_generated_image(generated_img)

    @staticmethod
    def _apply_generated_image(img_gen: np.ndarray):
        cv2.imwrite("result.jpg", img_gen)
        cv2.imshow("Result image", img_gen)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def center_window(self):
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()

        x = (sw - self.window_width) / 2
        y = (sh - self.window_height) / 2

        self.parent.geometry(
            "%dx%d+%d+%d" % (self.window_width, self.window_height, x, y)
        )


if __name__ == "__main__":
    root = tkinter.Tk()
    app = App(root)
    root.mainloop()
