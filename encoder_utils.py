import numpy as np
import cv2 as cv2

def fill_virtual_pixel(context,pixel_id):
    rgb=context.pixels[pixel_id]
    img=np.empty([context.virtual_pixel_size[0],context.virtual_pixel_size[1],3])
    img[:,:,0] = np.full([context.virtual_pixel_size[0],context.virtual_pixel_size[1]],rgb[0])
    img[:,:,1] = np.full([context.virtual_pixel_size[0],context.virtual_pixel_size[1]],rgb[1])
    img[:,:,2] = np.full([context.virtual_pixel_size[0],context.virtual_pixel_size[1]],rgb[2])
    return img


def craft_frame(context,frame_number):
    print(frame_number)
    row_size=int(context.x/context.virtual_pixel_size[0])
    frame="empty"
    for row in range(int(context.y/context.virtual_pixel_size[1])):
        horizontal_line="empty"
        for column in range(int(context.x/context.virtual_pixel_size[0])):
            id=row*row_size+column
            if type(horizontal_line)!=str:
                horizontal_line=np.hstack((horizontal_line,fill_virtual_pixel(context,id)))
            else:
                horizontal_line=fill_virtual_pixel(context,id)


        if type(frame) != str:
            frame=np.vstack((frame,horizontal_line))
        else:
            frame=np.copy(horizontal_line)
    #cv2.imshow("image", frame)
    #cv2.waitKey()
    #print("writting")
    cv2.imwrite(context.dirname+str(frame_number)+".png", frame)
    #context.video.write(cv2.imread(context.dirname+str(frame_number)+".png"))
    #os.remove(context.dirname+str(frame_number)+".png")
    
class Context(): #a packing class to pass context to parallel funcs
    def __init__(self,pixels,x,y,vp_width,vp_height,dirname):
        self.pixels=pixels.copy()
        self.x=x
        self.y=y
        self.virtual_pixel_size=[vp_width,vp_height]
        self.dirname=dirname

