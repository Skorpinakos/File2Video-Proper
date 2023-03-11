import time
import numpy
cimport numpy

ctypedef numpy.int_t DTYPE_t
numpy.import_array()


def cython_sub_frame_crafter(numpy.ndarray[numpy.int8_t, ndim=3] var,unsigned short row_size,unsigned short x,unsigned short y,numpy.ndarray[numpy.int8_t, ndim=2] pixels,unsigned short vp_width,unsigned short vp_height):
    cdef unsigned short row,column,start_x,start_y
    cdef int pixel_id,total_pixels
    total_pixels=(y//vp_height)*(x//vp_width)
    pixel_id=0
    while pixel_id<total_pixels:
            column=pixel_id % row_size
            row=pixel_id// row_size
            start_x=column*vp_width
            start_y=row*vp_height
            var[  start_y:start_y+vp_height  ,  start_x:start_x+vp_width  ]=pixels[pixel_id]
            pixel_id+=1
