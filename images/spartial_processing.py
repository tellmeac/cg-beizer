import cv2
import numpy as np

BLUR = np.array(([1, 2, 1], [2, 4, 2], [1, 2, 1]))
SHARPEN = np.array(([-1, -1, -1], [-1, 9, -1], [-1, -1, -1]))
EDGE_DETECTION = np.array(([0, 1, 0], [1, -4, 1], [0, 1, 0]))
SOBEL_EDGE_DETECTION = np.array(([0, -1, 0], [-1, 4, -1], [0, -1, 0]))
EMBOSS = np.array(([0, 1, 0], [1, 0, -1], [0, -1, 0]))


class Image:
    def __init__(self, filename: str):
        self._name = filename
        self._img = cv2.imread(self._name)

    @property
    def height(self):
        return self._img.shape[0]

    @property
    def width(self):
        return self._img.shape[1]

    def process(self, core: np.ndarray):
        result = self._convolution_rgb(core)
        cv2.imwrite(f"result_{self._name}", result)

    def _convolution_rgb(self, core: np.ndarray, offset=0) -> np.ndarray:
        """
        Performs a convolution according to the core
        :param core: matrix for convolution
        :return: processed RGB-image
        """

        blues, greens, reds = cv2.split(self._img)

        return cv2.merge([
            self._convolution(core, blues, offset),
            self._convolution(core, greens, offset),
            self._convolution(core, reds, offset)
        ])

    def _convolution(self, core: np.ndarray, img: np.ndarray, offset: int):
        """
        Центральный элемент ядра располагается над пикселом
        изображения. Новое значение пиксела вычисляется как сумма
        произведений соседних пикселов на элементы ядра.
        """
        result = np.zeros((self.height - 2, self.width - 2))

        core_sum = core.sum()
        for y in range(1, self.height - 2):
            for x in range(1, self.width - 2):
                data = (core[0, 0] * img[y - 1, x - 1] + core[0, 1] * img[y - 1, x] + core[0, 2] * img[y - 1, x + 1] +
                        core[1, 0] * img[y, x - 1] + core[1, 1] * img[y, x] + core[1, 2] * img[y, x + 1] +
                        core[2, 0] * img[y + 1, x - 1] + core[2, 1] * img[y + 1, x] + core[2, 2] * img[y + 1, x + 1] +
                        offset)
                if data < 0:
                    result[y - 1, x - 1] = 0
                    continue
                if core_sum > 0:
                    result[y - 1, x - 1] = data / core_sum
                    continue
                result[y - 1, x - 1] = data
        return result


if __name__ == "__main__":
    my_image = Image("sample.png")
    my_image.process(BLUR)
