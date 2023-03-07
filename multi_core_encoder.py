from multiprocessing import Process
from pathlib import Path
import numpy as np
import cv2 as cv2
from datetime import datetime
import os
import time as time
import multiprocessing as mp


### Parallel Defs #####################################################################################################

def fill_virtual_pixel(context,pixel_id):
    rgb=context.pixels[pixel_id]
    img=np.empty([context.virtual_pixel_size[0],context.virtual_pixel_size[1],3],dtype=np.int8)
    img[:,:,0] = np.full([context.virtual_pixel_size[0],context.virtual_pixel_size[1]],rgb[0])
    img[:,:,1] = np.full([context.virtual_pixel_size[0],context.virtual_pixel_size[1]],rgb[1])
    img[:,:,2] = np.full([context.virtual_pixel_size[0],context.virtual_pixel_size[1]],rgb[2])
    return img


def craft_frame(context,frame_number,mp_var):
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
        #cv2.imwrite(context.dirname+"temp/"+str(frame_number)+".png", frame)
        #print(cv2.imread(context.dirname+"temp/"+str(frame_number)+".png"))
        
        var = np.reshape( np.frombuffer( mp_var, dtype=np.int8 ), (context.y,context.x,3) )
        np.copyto(var, frame, casting='same_kind') #IMPORTANT! YOU NEED COPY_TO SO THE VAR POINTER DOESNT CHANGE SO THE PARENT CAN STILL HAVE ACCESS (DONT USE NP.COPY())
        #print(var)
        #print(var)
        #print(type(var),type(frame))
        #print(var)
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
    def __init__(self,x,y,fps,initial_padding,initial_size,threads,batch_size): #initial_padding is the poadding done for the bytes to be multiple of 3
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
        
        self.virtual_pixel_size=[12,12] #[x,y]
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
        self.shared_vars=[]
        self.transcoded_frame_count=0
        self.batch_size=batch_size
    
    def context_giver(self):
        return Context(self.virtual_pixels,self.x,self.y,self.virtual_pixel_size[0],self.virtual_pixel_size[1],self.dirname)

    def color_distr(self,number):
        return number*self.color_quantum #take a number (e.g. between 1 and 4) and turn it to a distinct 0-255 level
    def safe(self,string):
        return string.zfill(8)
        
    def put_byte_batch_in(self,batch):

        
        if len(packet_str)!=24:
            print("error")
            exit()

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
            frame=self.retrieve_frame(self.shared_vars.pop(0))
            self.previous_batch.append(frame)
        ###
        #self.previous_batch = sorted(list(map( lambda s: int(s.replace(".png","")), os.listdir(self.dirname+'temp/') ))) #for sorting based on integer of 123.png rather than string (to avoid 118.png<27.png)


        self.transcode(self.previous_batch)
        
        
        self.video.release()
                
    def transcode(self,batch):
        #print("batch length:",len(batch))
        
        
        for img in batch:
            #print(img)
            #exit()
            #image=str(img)+".png"
            self.video.write(img)
            #os.remove(self.dirname+"temp/"+image)
        self.previous_batch=[]
        self.transcoded_frame_count+=len(batch)
        print("transcoded "+ str(self.transcoded_frame_count)+" frames so far")


    def context_giver(self):
        return Context(self.virtual_pixels,self.x,self.y,self.virtual_pixel_size[0],self.virtual_pixel_size[1],self.dirname)
    def retrieve_frame(self,shared_frame):
        var = np.reshape( np.frombuffer( shared_frame, dtype=np.int8 ), (self.y,self.x,3) )
        return var

    def add_virtual_pixel(self,rgb):
        
        self.virtual_pixels.append(rgb)
        self.current_virtual_pixel+=1
        if self.current_virtual_pixel==self.virtual_pixels_per_frame:
            #print()
            #print(self.frames,len(self.shared_vars))
            context=self.context_giver() 
            frame_number=self.frames

            #Parallel magic

            # check if already spawned enough processes to saturate cpu and if so wait for them and start video transcoding the previous ones
            if (len(self.childs)>=self.threads):
                self.transcode(self.previous_batch)
                #transcode self.shared_vars
                for kid in self.childs:
                    kid.join() #wait for each process
                    frame=self.retrieve_frame(self.shared_vars.pop(0))
                    self.previous_batch.append(frame)
                self.childs=[] #clear process list
                
                #self.previous_batch = sorted(list(map( lambda s: int(s.replace(".png","")), os.listdir(self.dirname+'temp/') ))) #for sorting based on integer of 123.png rather than string (to avoid 118.png<27.png)


            n_elements = self.x*self.y*3//4 # how many elements your numpy should have I DON'T KNOW WHY I HAVE TO ADD THE *2 AT THE END ????? it was because of float64 instead of int32....
            #print(n_elements)
            #buffer that contains the memory
            mp_var = mp.RawArray( 'i', n_elements )
            arguements=(context,frame_number,mp_var)
            self.shared_vars.append(mp_var)

            p=Process(target=craft_frame,args=arguements)
            p.start()
            #p.join()
            #print(mp_var)
            #exit()
            #var=self.retrieve_frame(mp_var)
            #print(var)
            #exit()
            self.childs.append(p)



            self.current_virtual_pixel=0
            #self.craft_frame(self.frames,pixels) #using https://docs.python.org/3/library/multiprocessing.html for windows
            self.virtual_pixels=[]

            #THIS IS FUCKING COOL https://stackoverflow.com/questions/59070175/pass-arguments-through-self-in-class-instance-while-multiprocessing-in-python 


        
            

                         

        
def bytes_from_file(filename, chunksize=3): #from https://stackoverflow.com/a/1035456 with minor modifications
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if len(chunk)==chunksize:
                yield tuple(chunk)
            else:
                chunk=list(chunk)
                chunk.extend([0]*((chunksize)-len(chunk)))
                yield tuple(chunk)
                break

        



def main(input_file):
    #data_combined_to_24_bits,initial_size,initial_padding=get_data(input_file)
    chunk_size=3
    initial_size=os.stat(input_file).st_size
    initial_padding=chunk_size-(initial_size % chunk_size)

    final_video=Result(3840,2160,6,initial_padding,initial_size,12) #anything bellow 6 fps is turned to 6 by youtube
    #args are x dimension of final video | y dimension of final video | fps of final video | file padding so it is multiple of batch_size (byte_size*chunk_size e.g. 8*3)|original file size | thread count to spawn

    t1=time.time()
    print("Starting transforming file with size " + str(initial_size) + " bytes")


    for packet in bytes_from_file(input_file,chunksize=chunk_size):
        #print("packet is: ",packet_of_24_bits)
        final_video.put_byte_batch_in(packet)
    final_video.finalize()


    t2=time.time()
    print("finished after "+str(t2-t1)+ " seconds")
    print("median speed:"+str(int(initial_size/(t2-t1)))+ " bytes/second")



input_file="tests/test_input.zip"
if __name__ == '__main__': #in the god you believe in https://stackoverflow.com/questions/18204782/runtimeerror-on-windows-trying-python-multiprocessing
    main(input_file)
    
