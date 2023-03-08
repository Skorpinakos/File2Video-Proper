import time
import numpy
cimport numpy

ctypedef numpy.int_t DTYPE_t
def do_calc(numpy.ndarray[DTYPE_t, ndim=1] arr):
    cdef int maxval
    cdef unsigned long long int total = 0
    cdef int k
    cdef double t1, t2, t
    
    t1 = time.time()

    for k in arr:
        total = total + k
    print("Total = ", total)
    
    t2 = time.time()
    t = t2 - t1
    print(t)



def fill_virtual_pixel(int vp_width,int vp_height,int r, int g,int b):
    img=numpy.empty([vp_width,vp_height,3],dtype=numpy.int8)
    img[:,:,0] = numpy.full([vp_width,vp_height],r)
    img[:,:,1] = numpy.full([vp_width,vp_height],g)
    img[:,:,2] = numpy.full([vp_width,vp_height],b)
    return img






