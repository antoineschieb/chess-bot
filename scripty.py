from utils import wrapper_imshow
import numpy as np
import cv2

im = cv2.imread("capt.png")


def trouver_coords(im):
    seuil = cv2.inRange(im, (85, 149, 117), (87, 151, 119))
    kernel = np.ones((7, 7), np.uint8)
    opening = cv2.morphologyEx(seuil, cv2.MORPH_OPEN, kernel, iterations=1)

    (ind_x, ind_y) = np.nonzero(opening)

    return [np.amin(ind_x), np.amax(ind_x), np.amin(ind_y), np.amax(ind_y)]


op = trouver_coords(im)
print(op)
