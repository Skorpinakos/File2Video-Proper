import numpy as numpy
from app_extension import cython_sub_frame_crafter as cython_sub_frame_crafter
import cv2


def to_be_cythonized_sub_frame_crafter(var,row_size,x,y,pixels,vp_width,vp_height):
    

    for row in range(int(y/vp_height)):
        
        for column in range(int(x/vp_width)):
            pixel_id=row*row_size+column
            start_x=column*vp_width
            start_y=row*vp_height
            var[  start_y:start_y+vp_height  ,  start_x:start_x+vp_width  ]=pixels[pixel_id]





pixels=numpy.array([[230,21,5],[10,0,190],[10,0,190],[230,21,5]],dtype=numpy.int8)
out=numpy.empty((24,24,3),dtype=numpy.int8)
#to_be_cythonized_sub_frame_crafter(out,2, 24,12,pixels,12,12)
#cv2.imshow("img",out)
#cv2.waitKey()
#exit()
cython_sub_frame_crafter(out,2, 24,24,pixels,12,12)
cv2.imshow("img",out)
cv2.waitKey()