import time
import numpy
cimport numpy

ctypedef numpy.int_t DTYPE_t



def fill_virtual_pixel(int vp_width,int vp_height,int r, int g,int b):
    cdef numpy.ndarray[numpy.int8_t, ndim=3]  img=numpy.empty([vp_width,vp_height,3],dtype=numpy.int8)
    img[:,:,0] = numpy.full([vp_width,vp_height],r)
    img[:,:,1] = numpy.full([vp_width,vp_height],g)
    img[:,:,2] = numpy.full([vp_width,vp_height],b)
    return img



