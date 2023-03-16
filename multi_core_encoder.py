from multiprocessing import Process
from pathlib import Path
import numpy as np
import cv2 as cv2
from datetime import datetime
import os
import time as time
import multiprocessing as mp
from app_extension import cython_sub_frame_crafter as cython_sub_frame_crafter



def to_be_cythonized_sub_frame_crafter(var,row_size,x,y,pixels,vp_width,vp_height):
#all integers will be treadted as unsigned short integers in cython implementation, be carefull for bigger resolutions than 5k
    #print(pixels)

    ### new approach, reshape pixels into mini frame and rescale with cv2
    #pixels=np.reshape(pixels,((y//vp_height),(x//vp_width),3)) #this is actually kinda in place , don't worry about performance https://stackoverflow.com/questions/46574568/does-numpy-reshape-create-a-copy
    #frame = cv2.resize(pixels, (x,y), interpolation= cv2.INTER_NEAREST) 
    #np.copyto(var,frame,casting='same_kind')
    #return 
    ### it didn't give any performance improvement

    pixel_id=0
    for row in range(0,y,vp_height):
        for column in range(0,x,vp_width):
            var[  row:row+vp_height  ,  column:column+vp_width  ]=pixels[pixel_id]
            pixel_id+=1
        
            




def craft_frame(context,frame_number,mp_var):
    #print("started crafting frame No",frame_number )

    
    
    #cv2.imshow("image", frame)
    #cv2.waitKey()
    #print("writting")
    #cv2.imwrite(context.dirname+"temp/"+str(frame_number)+".png", frame)
    #print(cv2.imread(context.dirname+"temp/"+str(frame_number)+".png"))
    
    row_size=int(context.x/context.virtual_pixel_size[0])
    var = np.reshape( np.frombuffer( mp_var, dtype=np.uint8 ), (context.y,context.x,3) )
    to_be_cythonized_sub_frame_crafter(var,row_size,context.x,context.y,np.array(context.pixels,dtype=np.uint8),context.virtual_pixel_size[0],context.virtual_pixel_size[1])
    
    #np.copyto(var, frame, casting='same_kind') #IMPORTANT! YOU NEED COPY_TO SO THE VAR POINTER DOESNT CHANGE SO THE PARENT CAN STILL HAVE ACCESS (DONT USE NP.COPY())
    #print(var)
    #print(var)
    #print(type(var),type(frame))
    #print(var)
    #print("finished crafting frame No",frame_number )
    #context.video.write(cv2.imread(context.dirname+str(frame_number)+".png"))
    #os.remove(context.dirname+str(frame_number)+".png")




class Context(): #a packing class to pass context to parallel funcs
    def __init__(self,pixels,x,y,vp_width,vp_height,dirname):
        #print(pixels)
        self.pixels=pixels
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
        

        self.frames=0
        
        self.virtual_pixel_size=[12,12] #[x,y] this is the smallest virtual pixel size that survives video compression and is also a divider of most working video resolutions (no per-frame padding)
        self.current_virtual_pixel=0
        self.initial_padding=initial_padding
        self.last_frame_padding=None
        self.size=initial_size
        self.color_quantum=85
        if (self.x % self.virtual_pixel_size[0])!=0 or (self.y % self.virtual_pixel_size[0])!=0:
            print("during init: x (width) or y (height) not a multiple of virtual pixel size, exiting...")
            exit(1)
        self.virtual_pixels_per_frame=int((self.x/self.virtual_pixel_size[0])*(self.y/self.virtual_pixel_size[1]))
        self.childs=[]
        self.previous_batch=[]
        self.shared_vars=[]
        self.transcoded_frame_count=0
        self.batch_size=batch_size
        self.bits_per_virtual_pixel=6 ### that "6" is fundamental to the current architecture as it represents how many bits are encoded per virtual pixel (2 per color channel so 4 levels of intensity per color [0,85,170,255])
        self.virtual_pixels=np.empty((self.virtual_pixels_per_frame,3),dtype=np.uint8)
       
  
    
    def context_giver(self):
        print(self.virtual_pixels)
        return Context(self.virtual_pixels,self.x,self.y,self.virtual_pixel_size[0],self.virtual_pixel_size[1],self.dirname)
    def packet_to_str(self,packet):
        return f'{packet:b}'.zfill(8)

    def put_byte_batch_in(self,batch):

        #print(batch)
        #if len(batch)!=self.batch_size//8: 
            #print("during putting byte batch in: error, not correct batch size")
            #exit()

        packets_unified="".join(tuple(map(self.packet_to_str ,batch))) #for each byte , convert to string without leadin '0b' prefix and with 8 bit zero leading padding (methods have been performance tested here https://github.com/Skorpinakos/benchmark-01 compared to methods from https://stackoverflow.com/questions/37377982/remove-the-0b-in-binary & https://stackoverflow.com/questions/16926130/convert-to-binary-and-keep-leading-zeros  )
                                                                               #use map to apply to whole list efficiently and join all to unified string
        #print(packets_unified)
        for indx in range(0,self.batch_size,self.bits_per_virtual_pixel):
            color=packets_unified[indx:indx+self.bits_per_virtual_pixel]
            self.create_virtual_pixel(color)
        
    def create_virtual_pixel(self,color):
        #print(color)
        rgb=[int(color[0:2],2)*self.color_quantum,int(color[2:4],2)*self.color_quantum,int(color[4:6],2)*self.color_quantum]
    
        if self.current_virtual_pixel==0:
            self.add_parity_virtual_pixel(self.frames)
            self.add_virtual_pixel(rgb) #rgb is [r,g,b]
        else:
            self.add_virtual_pixel(rgb) #rgb is [r,g,b]
        #print(rgb)

            
    def add_parity_virtual_pixel(self,frame_number):
        ###Encodes frame number to the first virtual pixel 
        num=frame_number%64
        #print(frame_number)
        color=f'{num:b}'.zfill(6)
        rgb=[int(color[0:2],2)*self.color_quantum,int(color[2:4],2)*self.color_quantum,int(color[4:6],2)*self.color_quantum]
        #print(rgb)
        self.virtual_pixels[self.current_virtual_pixel]=rgb
        #print(self.current_virtual_pixel)
        self.current_virtual_pixel+=1
        self.frames+=1
    

    def finalize(self):
        ### ending padding for final frame
        if self.current_virtual_pixel==0:
            print("what a coincidence, the size of this file bugs out my code, maybe?")
        else:
            pass
        to_pad=self.virtual_pixels_per_frame-(self.current_virtual_pixel)
        #print(to_pad)
        for v_pixel in range(to_pad):
            self.create_virtual_pixel("000000")  ### add dummy pixels to fill last frame
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
        var = np.reshape( np.frombuffer( shared_frame, dtype=np.uint8 ), (self.y,self.x,3) )
        return var

    def add_virtual_pixel(self,rgb):
        #print(rgb)
        
        self.virtual_pixels[self.current_virtual_pixel]=rgb
        
        self.current_virtual_pixel+=1
        #print(self.current_virtual_pixel)
        if self.current_virtual_pixel==self.virtual_pixels_per_frame:
            #print()
           
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
            #self.virtual_pixels=[]

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
    chunk_size=240 #bytes #chunk_size*8 must be multiple of 6
    initial_size=os.stat(input_file).st_size
    initial_padding=chunk_size-(initial_size % chunk_size)

    final_video=Result(3840,2160,5,initial_padding,initial_size,5,chunk_size*8) #anything bellow 6 fps is turned to 6 by youtube
    #args are x dimension of final video | y dimension of final video | fps of final video | file padding so it is multiple of batch_size (byte_size*chunk_size e.g. 8*3)|original file size | thread count to spawn

    t1=time.time()
    print("Starting transforming file with size " + str(initial_size) + " bytes")


    for packet in bytes_from_file(input_file,chunksize=chunk_size):
        #print("packet is: ",packet_of_24_bits)
        final_video.put_byte_batch_in(packet)
    final_video.finalize()


    t2=time.time()
    print("finished after "+str(t2-t1)+ " seconds")
    print("median speed:"+str(int(initial_size/(t2-t1)))+ " Bytes/second")



input_file="tests/test_input.zip"
if __name__ == '__main__': #in the god you believe in https://stackoverflow.com/questions/18204782/runtimeerror-on-windows-trying-python-multiprocessing
    main(input_file)
    
