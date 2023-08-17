from numpy import True_, product, uint8
import pyautogui
import win32gui
import cv2
import numpy as np
import sys
import string
from focus import WindowMgr


rook_template = cv2.imread("./pieces/rook.png").astype(int)
knight_template = cv2.imread("./pieces/knight.png").astype(int)
bishop_template = cv2.imread("./pieces/bishop.png").astype(int)
queen_template = cv2.imread("./pieces/queen.png").astype(int)
king_template = cv2.imread("./pieces/king.png").astype(int)
pawn_template = cv2.imread("./pieces/pawn.png").astype(int)

templates = [
    ["R", rook_template],
    ["N", knight_template],
    ["B", bishop_template],
    ["Q", queen_template],
    ["K", king_template],
    ["P", pawn_template],
]
i = 0
for t in templates:  # t = ['R', rook_template]
    autres_pieces = [
        p[:2] for p in templates if p[0] != t[0]
    ]  # = [['N',knight_template],['B',bishop_template],['Q',queen_template],['K',king_template],['P',pawn_template] ]

    addition_templates = np.zeros_like(t[1])
    for [_, p] in autres_pieces:
        p = np.array(p / 255).astype(int)
        addition_templates += p
    addition_templates = -addition_templates
    addition_templates += 6 * np.array(t[1] / 255).astype(int)
    templates[i].append(addition_templates)
    i += 1

i = 0
for _, _, t in templates:
    t -= np.amin(t)
    t += np.amax(t)
    templates[i][1] = t.astype(np.uint8)
    i += 1

templates = [x[:2] for x in templates]


def standard_notation(the_move, rows_list):
    pos_lettre = string.ascii_lowercase.index(the_move[0])
    pos_num = int(the_move[1])
    piece = rows_list[8 - pos_num][pos_lettre].upper()
    if piece == "P":
        return the_move[2:4]
    else:
        return piece + the_move[2:4]


# OK
def create_inside_mask(edges):
    # d'abord de g à d
    w, h = edges.shape
    for line in range(h):
        for x in range(w):
            if edges[line, x] > 0:
                break
            else:
                edges[line, x] = 255
        for x in reversed(range(w)):
            if edges[line, x - 1] > 0:
                break
            else:
                edges[line, x] = 255
    return edges


# OK (a voir si ya des pb sur d'autres pieces a l'avenir)
def correlate(edges, template):
    template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
    if edges.shape != template.shape:
        edges = cv2.resize(edges, template.shape)
    diviseur = np.sum(edges) / 255

    product = cv2.bitwise_and(edges, template)
    aff = False
    while aff:
        cv2.imshow("edges", edges)  # [haut:bas,gauche:droite]
        cv2.imshow("template", template)
        cv2.imshow("product", product)
        key = cv2.waitKey(1)
        if key == ord("q"):
            break
        if key == ord("p"):
            cv2.waitKey(-1)

    if np.amax(product) == 0:
        wrapper_imshow(edges, template, product)

    score = np.sum(product) / (np.amax(product) * diviseur)
    return score


# OK
def screenshot(window_title=None):
    if window_title:
        hwnd = win32gui.FindWindow(None, window_title)
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            x, y, x1, y1 = win32gui.GetClientRect(hwnd)
            x, y = win32gui.ClientToScreen(hwnd, (x, y))
            x1, y1 = win32gui.ClientToScreen(hwnd, (x1 - x, y1 - y))
            im = pyautogui.screenshot(region=(x, y, x1, y1))
            return im
        else:
            print("Window not found!")
    else:
        im = pyautogui.screenshot()
        return im


# OK
def simplify_line_str(line):
    simplified_line = line  # init
    for c in range(len(line) - 1):
        if line[c + 0].isnumeric() and line[c + 1].isnumeric():
            simplified_line = (
                line[:c] + str(int(line[c + 0]) + int(line[c + 1])) + line[c + 2 :]
            )
            break
    if simplified_line == line:
        return line
    else:
        return simplify_line_str(simplified_line)


#
def trouver_coords(im):
    im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
    seuil = cv2.inRange(im, (85, 149, 117), (87, 151, 119))  # couleur des dark squares
    wrapper_imshow(seuil, aff=False)
    kernel = np.ones((7, 7), np.uint8)
    opening = cv2.morphologyEx(seuil, cv2.MORPH_OPEN, kernel, iterations=1)
    (ind_x, ind_y) = np.nonzero(opening)
    return [np.amin(ind_x), np.amax(ind_x), np.amin(ind_y), np.amax(ind_y)]


# OK
def wrapper_imshow(*args, aff=True, title=""):
    if not aff:
        return
    i = 0
    for img in args:
        i += 1
        cv2.imshow(title + " " + str(i), img)
    while aff:
        key = cv2.waitKey(1)
        if key == ord("p"):
            break
        if key == ord("q"):
            sys.exit()
    return


# OK
def get_piece_code(square):
    is_black = bool()
    edges = cv2.Canny(square, 100, 200)
    edges[0:10, :] = 0  # haut
    edges[-10:, :] = 0  # bas
    edges[:, 0:10] = 0  # gauche
    edges[:, -10:] = 0  # droite
    wrapper_imshow(edges, aff=False)

    # edges_mieux = cv2.Canny(square,100,200)

    # first, find piece type (pawn, king, ... , or empty)
    ## check for empty square first
    if np.sum(edges[5:-5, 5:-5]) == 0:
        return "1"
    L = list()
    for lettre, t in templates:
        score = correlate(edges, t)
        L.append([lettre, score])
    L = np.array(L)
    scores_list = list(L[:, 1])
    # print([round(float(x),4) for x in scores_list])
    idx = scores_list.index(max(scores_list))
    piece_found = list(L[:, 0])[idx]

    # then, find the color
    my_mask = create_inside_mask(edges)
    my_mask = cv2.bitwise_not(my_mask)

    assert square.shape == my_mask.shape

    wrapper_imshow(square, aff=False, title="avf")

    my_mask = np.divide(my_mask, 255).astype(uint8)

    masqued = np.multiply(square, my_mask)

    filtered_vals = [v for v in np.ravel(masqued).tolist() if v != 0]
    average = sum(filtered_vals) / len(filtered_vals)

    if average < 150:
        piece_found = piece_found.lower()

    wrapper_imshow(masqued, aff=False, title="fin")

    return piece_found


def str_of_casting_rights(L):
    ret = ""
    if L == []:
        return "-"
    else:
        if "K" in L:
            ret += "K"
        if "Q" in L:
            ret += "Q"
        if "k" in L:
            ret += "k"
        if "q" in L:
            ret += "q"

    return ret
