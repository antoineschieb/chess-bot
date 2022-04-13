import cv2 
import sys


from utils import wrapper_imshow

p = cv2.imread('petit_pion.png')
p = cv2.cvtColor(p,cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(p,1,240)

wrapper_imshow(p,edges)
