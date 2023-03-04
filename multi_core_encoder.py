from multiprocessing import Process
from pathlib import Path
import numpy as np
import cv2 as cv2
from datetime import datetime
import os
import time as time


### Parallel Defs #####################################################################################################

def fill_virtual_pixel(context,pixel_id):
    rgb=context.pixels[pixel_id]
    img=np.empty([context.virtual_pixel_size[0],context.virtual_pixel_size[1],3])
    img[:,:,0] = np.full([context.virtual_pixel_size[0],context.virtual_pixel_size[1]],rgb[0])
    img[:,:,1] = np.full([context.virtual_pixel_size[0],context.virtual_pixel_size[1]],rgb[1])
    img[:,:,2] = np.full([context.virtual_pixel_size[0],context.virtual_pixel_size[1]],rgb[2])
    return img


def craft_frame(context,frame_number):
    #print("started crafting frame No",frame_number )
    try:
        
        
        row_size=int(context.x/context.virtual_pixel_size[0])
        frame="empty"
        for row in range(int(context.y/context.virtual_pixel_size[1])):
            horizontal_line="empty"
            for column in range(int(context.x/context.virtual_pixel_size[0])):
                pixel_id=row*row_size+column
                if type(horizontal_line)!=str:
                    horizontal_line=np.hstack((horizontal_line,fill_virtual_pixel(context,pixel_id)))
                else:
                    horizontal_line=fill_virtual_pixel(context,pixel_id)


            if type(frame) != str:
                frame=np.vstack((frame,horizontal_line))
            else:
                frame=np.copy(horizontal_line)
        #cv2.imshow("image", frame)
        #cv2.waitKey()
        #print("writting")
        cv2.imwrite(context.dirname+"temp/"+str(frame_number)+".png", frame)
        #print("finished crafting frame No",frame_number )
        #context.video.write(cv2.imread(context.dirname+str(frame_number)+".png"))
        #os.remove(context.dirname+str(frame_number)+".png")
    except Exception as e:
        print(e)



class Context(): #a packing class to pass context to parallel funcs
    def __init__(self,pixels,x,y,vp_width,vp_height,dirname):
        self.pixels=pixels.copy()
        self.x=x
        self.y=y
        self.virtual_pixel_size=[vp_width,vp_height]
        self.dirname=dirname
################################################################################################################################
class Result():
    def __init__(self,x,y,initial_padding,initial_size,fps,threads): #initial_padding is the poadding done for the bytes to be multiple of 3
        self.threads=threads
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
        self.dirname="results/Video-Output "+dt_string+'/'
        try:
            os.mkdir(self.dirname)
            os.mkdir(self.dirname+"temp/")
        except:
            print("can't make dir, but maybe thats ok?")
        self.video= cv2.VideoWriter(self.dirname+"exported"+".avi", cv2.VideoWriter_fourcc(*"MJPG"), fps, (x,y))
        self.x=x
        self.y=y
        
        self.virtual_pixels=[]
        self.frames=0
        
        self.virtual_pixel_size=[16,16] #[x,y]
        self.current_virtual_pixel=0
        self.initial_padding=initial_padding
        self.last_frame_padding=None
        self.size=initial_size
        self.color_quantum=85
        if (self.x % self.virtual_pixel_size[0])!=0 or (self.y % self.virtual_pixel_size[0])!=0:
            print("x or y not a multiple of virtual pixel size, exiting...")
            exit(1)
        self.virtual_pixels_per_frame=int((self.x/self.virtual_pixel_size[0])*(self.y/self.virtual_pixel_size[1]))
        self.childs=[]
        self.previous_batch=[]
    
    def context_giver(self):
        return Context(self.virtual_pixels,self.x,self.y,self.virtual_pixel_size[0],self.virtual_pixel_size[1],self.dirname)

    def color_distr(self,number):
        return number*self.color_quantum #take a number (e.g. between 1 and 4) and turn it to a distinct 0-255 level
    def safe(self,string):
        return string.zfill(8)
        
    def put_packet_in(self,packet):
        packet_str=self.safe(bin(packet[0])[2:])+self.safe(bin(packet[1])[2:])+self.safe(bin(packet[2])[2:])
        #print((packet_str))
        #print(packet)
        
        if len(packet_str)!=24:
            print("error")
            exit()
        packet_1=packet_str[0:6]
        packet_2=packet_str[6:12]
        packet_3=packet_str[12:18]
        packet_4=packet_str[18:24]
        self.create_virtual_pixel(packet_1)
        self.create_virtual_pixel(packet_2)
        self.create_virtual_pixel(packet_3)
        self.create_virtual_pixel(packet_4)
        
    def create_virtual_pixel(self,color):
        #print(color)
        rgb=[self.color_distr(int(self.safe(color[0:2]),2)),self.color_distr(int(self.safe(color[2:4]),2)),self.color_distr(int(self.safe(color[4:]),2))]
        #print(rgb)
        if self.current_virtual_pixel==0:
            self.add_parity_virtual_pixel(self.frames)
            self.add_virtual_pixel(rgb) #rgb is [r,g,b]
        else:
            self.add_virtual_pixel(rgb) #rgb is [r,g,b]
        #print(rgb)

            
    def add_parity_virtual_pixel(self,frame_number):
        
        num=frame_number%64
        #print(frame_number)
        num=str(bin(num))[2:] #remove 0b from start
        num=(6-len(num))*"0"+num #pad for 6 bits
        rgb=[self.color_distr(int(num[0:2],2)),self.color_distr(int(num[2:4],2)),self.color_distr(int(num[4:],2))]
        #print(rgb)
        self.virtual_pixels.append(rgb)
        self.current_virtual_pixel+=1
        self.frames+=1
    

    def finalize(self):
        ### ending padding for final frame
        if len(self.virtual_pixels)==0:
            return
        to_pad=self.virtual_pixels_per_frame-len(self.virtual_pixels)
        for v_pixel in range(to_pad):
            self.create_virtual_pixel("000000")
        ######

        ### join parallels ###
        self.transcode(self.previous_batch)
        for kid in self.childs:
            kid.join()
        ###
        self.previous_batch = sorted(os.listdir(self.dirname+'temp/'))
        self.transcode(self.previous_batch)
        
        self.video.release()
                
    def transcode(self,batch):
        #print("transcoding the following:",batch)
        for image in batch:
            self.video.write(cv2.imread(self.dirname+"temp/"+image))
            os.remove(self.dirname+"temp/"+image)
        print("transcoded the ",batch)


    def context_giver(self):
        return Context(self.virtual_pixels,self.x,self.y,self.virtual_pixel_size[0],self.virtual_pixel_size[1],self.dirname)

    def add_virtual_pixel(self,rgb):
        self.virtual_pixels.append(rgb)
        self.current_virtual_pixel+=1
        if self.current_virtual_pixel==self.virtual_pixels_per_frame:
            context=self.context_giver() 
            frame_number=self.frames

            #Parallel magic

            # check if already spawned enough processes to saturate cpu and if so wait for them and start video transcoding the previous ones
            if (len(self.childs)>=self.threads):
                self.transcode(self.previous_batch)
                for kid in self.childs:
                    kid.join() #wait for each process
                self.childs=[] #clear process list

            self.previous_batch = sorted(os.listdir(self.dirname+'temp/'))
            


            arguements=(context,frame_number)
            p=Process(target=craft_frame,args=arguements)
            p.start()
            self.childs.append(p)



            self.current_virtual_pixel=0
            #self.craft_frame(self.frames,pixels) #using https://docs.python.org/3/library/multiprocessing.html for windows
            self.virtual_pixels=[]

            #THIS IS FUCKING COOL https://stackoverflow.com/questions/59070175/pass-arguments-through-self-in-class-instance-while-multiprocessing-in-python 


        
            

                         

        


        

def get_data(filename):
    data = list(Path(filename).read_bytes())
    initial_size=len(data) #data is a list of 8 bit integers (0 to 255)
    data.extend([0]*(3-len(data)%3)) #if not a multiple of 3 pad with zeros and include the information on the Result class

    data_combined_to_24_bits=list(zip(*[iter(data)]*3)) #group bytes in groups of 3 (24 bits, so they can be splitted to packets of 6 bits) in a tuple
    #print(min(data),max(data))
    initial_padding=(3-len(data)%3)
    return data_combined_to_24_bits,initial_size,initial_padding

def main(input_file):
    data_combined_to_24_bits,initial_size,initial_padding=get_data(input_file)
    final_video=Result(1280,720,initial_padding,initial_size,6,12) #anything bellow 6 fps is turned to 6 by youtube

    t1=time.time()
    print("Starting transforming file with size " + str(initial_size) + " bytes")


    for packet_of_24_bits in data_combined_to_24_bits[0:]:
        #print("packet is: ",packet_of_24_bits)
        final_video.put_packet_in(packet_of_24_bits)
    final_video.finalize()


    t2=time.time()
    print("finished after "+str(t2-t1)+ " seconds")
    print("median speed:"+str(int(initial_size/(t2-t1)))+ " bytes/second")



input_file="tests/exported.zip"
if __name__ == '__main__': #in the god you believe in https://stackoverflow.com/questions/18204782/runtimeerror-on-windows-trying-python-multiprocessing
    main(input_file)
    