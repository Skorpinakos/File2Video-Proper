import cv2
import os
import numpy as np
from datetime import datetime

class Decoding():
    def __init__(self,filename,output_path,output_name,extension):
        now = datetime.now()
        dt_string = "File-Output "+now.strftime("%d-%m-%Y %H-%M-%S")+"/"
        os.mkdir(output_path+dt_string)
        self.output_path=output_path+dt_string
        self.ext=extension
        self.output_filename=output_name
        _ = cv2.VideoCapture(filename)
        self.y = _.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.x = _.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.cam = cv2.VideoCapture(filename)
        self.current_frame=-1
        self.virtual_pixel_size=[12,12] #[x,y]
        self.virtual_pixels=[]
        self.current_virtual_pixel=0
        self.byte_buffer=""
        self.byte_buffer_size=24000 #must be multiple of both 6 and 8
        if (self.x % self.virtual_pixel_size[0])!=0 or (self.y % self.virtual_pixel_size[0])!=0:
            print("x or y not a multiple of virtual pixel size, exiting...")
            exit(1)
        self.virtual_pixels_per_frame=int((self.x/self.virtual_pixel_size[0])*(self.y/self.virtual_pixel_size[1]))
        self.color_quantum=85
    def get_new_frame(self):
        ret,frame = self.cam.read()
        if ret:
            status=True
            self.current_frame+=1
            return frame,status
        else:
            return self.end()
        
    def end(self):
        self.add_bytes("000000",mode="final_push")
        status=False
        return np.array(()),status
    def store_error_factor(self,diff_list):
        pass
    def quantize_color(self,color):
        hidden_meaning=np.arange(0,4,1, dtype=float)*self.color_quantum #[0,85,170,255] for color quantum =85
        #print(hidden_meaning)
        real_color=[]
        for value in color:
            diffs=np.abs(hidden_meaning-value)
            minimum=min(diffs)
            #print(hidden_meaning[np.where(diffs==minimum)])
            #print(value)
            val=hidden_meaning[np.where(diffs==minimum)]
            if len(val)!=1:
                print(val)
                print(diffs)
                val=val[0]
                print("possible error")
            real_color.append(int(val))
            self.store_error_factor(diffs)
        return np.array(real_color)
    def virtual_pixels_to_bytes(self,color):
        bin_value=""
        for value in color:
            bin_value+=str(bin(value//self.color_quantum)[2:].zfill(2)) #from 170 to 2 to b10
        self.add_bytes(bin_value)
    def add_bytes(self,bits_to_add,mode="not_final_push"):
        if len(bits_to_add)!=6:
            print("bits to add not right size")
            exit(1)
        if mode!="final_push":
            self.byte_buffer+=bits_to_add
        if (len(self.byte_buffer)>=self.byte_buffer_size) or mode=="final_push":
            if len(self.byte_buffer)!=self.byte_buffer_size and mode!="final_push":
                print("byte buffer not right size")
                exit(1)
            n=8
            chunks = [self.byte_buffer[i:i+n] for i in range(0, len(self.byte_buffer), n)]
            self.byte_buffer=""
            #print("writting to file...")
            #print(self.output_path)
            with open(self.output_path+self.output_filename+"."+self.ext,"ab") as output_file:
                for byte in chunks:
                    temp=hex(int(byte,2))[2:].zfill(2)
                    #print(temp)
                    to_write=bytes.fromhex(temp)
                    
                    output_file.write(to_write)
            



            
    def frame_to_virtual_pixels(self,frame):
        first_vp=frame[0:self.virtual_pixel_size[0],0:self.virtual_pixel_size[1]]
        color_first_vp=first_vp.mean(axis=(0,1))
        real_color_first_vp=self.quantize_color(color_first_vp)
        #print("frame with parity vp:",real_color_first_vp)

        for virtual_pixel in range(1,self.virtual_pixels_per_frame): #first virtual pixel is parity
            start_x=int(self.virtual_pixel_size[0]*(virtual_pixel % (self.x/self.virtual_pixel_size[0])))
            start_y=int(self.virtual_pixel_size[1]*(virtual_pixel // (self.x/self.virtual_pixel_size[0])))
            vp= frame[start_y+1:start_y+self.virtual_pixel_size[1]-1,start_x+1:start_x+self.virtual_pixel_size[0]-1]
            #cv2.imshow("image "+str(virtual_pixel),vp)
            #cv2.waitKey()
            color=vp.mean(axis=(0,1))
            #print(color)
            real_color=self.quantize_color(color)
            #print(color)
            #print(real_color)
            self.virtual_pixels_to_bytes(real_color)
            

        




#main
input_video="tests/exported.avi"
dec=Decoding(input_video,"results/","exported","zip")
while True:
    frame,status=dec.get_new_frame()
    if status!=False:
        #cv2.imshow("image",frame)
        #cv2.waitKey()
        
        dec.frame_to_virtual_pixels(frame)
        print(dec.current_frame)
    else:
        break
    


