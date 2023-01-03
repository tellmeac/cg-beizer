import logging
import math
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class TransformImage:
    def __init__(self, path: Path):
        self._name = path.name
        self._image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)

        self._src_points = []
        self._dst_points = []

    def affine_transform(self) -> np.ndarray:
        logger.info("Using simple transformation technique - affine transformation")

        result = np.zeros(self._image.shape, np.uint8)

        height = self._image.shape[0]
        width = self._image.shape[1]

        # Get warp matrix
        warp_mat = np.append(self._transformation_matrix(), [[0, 0, 1]], axis=0)
        # (3, 3) shape
        inv_mat = np.linalg.inv(warp_mat)

        for i in range(height):
            for j in range(width):
                # (1,1) shaped arrays
                next_p = np.dot(inv_mat, np.array([[i], [j], [1]])).flatten()[:2]
                x, y = round(next_p[0]), round(next_p[1])

                if not (0 <= x < height and 0 <= y < width):
                    continue

                result[i, j] = self._image[x, y]

        return result

    def bilinear_filtering(self) -> np.ndarray:
        result = np.zeros(self._image.shape, np.uint8)

        height = self._image.shape[0]
        width = self._image.shape[1]

        # (2, 3) shape
        warp_mat = np.append(self._transformation_matrix(), [[0, 0, 1]], axis=0)
        # (3, 3) shape
        inv_mat = np.linalg.inv(warp_mat)

        for i in range(height):
            for j in range(width):
                # (1,1) shaped arrays
                next_p = np.dot(inv_mat, np.array([[i], [j], [1]])).flatten()[:2]
                x, y = next_p[0], next_p[1]

                if not (0 <= x < height and 0 <= y < width):
                    continue

                cx = math.ceil(x)
                cx = cx if cx < height else math.floor(x)

                fx = math.floor(x)

                ceil_y = math.ceil(y)
                ceil_y = ceil_y if ceil_y < width else math.floor(y)

                fy = math.floor(y)
                # fy = fy if fy < width else math.ceil(y)

                tr = np.array(self._image[math.floor(x), math.floor(y)])
                br = np.array(self._image[cx, math.floor(y)])
                tl = np.array(self._image[math.floor(x), ceil_y])
                bl = np.array(self._image[cx, ceil_y])

                result[i, j] = (
                    (cx - x) * tr + (x - fx) * br
                ) * (ceil_y - y) + (
                        (cx - x) * tl + (x - fx) * bl
                ) * (y - fy)
        return result

    def display(self):
        cv2.namedWindow(self._name)
        # Event handles new points
        cv2.setMouseCallback(self._name, self._set_point)
        while True:
            cv2.imshow(self._name, self._image)
            if cv2.waitKey(20) == 13:
                break

    def _transformation_matrix(self) -> np.ndarray:
        """
        Returns transform matrix (2, 3) from source and destination points
        """
        src_p = np.array(self._src_points).astype(np.float32)
        dst_p = np.array(self._dst_points).astype(np.float32)
        return cv2.getAffineTransform(src_p, dst_p)

    def _set_point(self, event, x, y, flag, params):
        """
        Event handle for image setup
        """
        p = [x, y]

        match event:
            case cv2.EVENT_LBUTTONDOWN:
                self._src_points.append(p)
                cv2.circle(self._image, p, 3, (125, 125, 125), -1)

            case cv2.EVENT_RBUTTONDOWN:
                self._dst_points.append(p)
                cv2.circle(self._image, p, 3, (127, 255, 0), -1)

            case cv2.EVENT_MBUTTONDOWN:
                cv2.destroyAllWindows()

            case _:
                return


if __name__ == "__main__":
    img = TransformImage(Path("./sample.png"))
    img.display()

    simple_result = img.affine_transform()
    cv2.imshow("Simple result", simple_result)

    bilinear_result = img.bilinear_filtering()
    cv2.imshow("Bilinear result", bilinear_result)

    # Just to leave on any click :^)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
