import app_extension
import numpy
import cv2
#arr = numpy.arange(10000000, dtype=numpy.int32)


def fill_virtual_pixel_interface(context,pixel_id):
        
    vp_height=12
    vp_width=12
    r=0
    g=85
    b=255
    #img=numpy.reshape([vp_width,vp_height,3],dtype=numpy.int8)
    img=app_extension.fill_virtual_pixel(vp_width,vp_height,r,g,b)
    return

class Context(): #a packing class to pass context to parallel funcs
    def __init__(self,pixels,x,y,vp_width,vp_height,dirname):
        self.pixels=pixels.copy()
        self.x=x
        self.y=y
        self.virtual_pixel_size=[vp_width,vp_height]
        self.dirname=dirname