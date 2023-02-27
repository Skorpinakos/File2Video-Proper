import base64
from pathlib import Path
input_file="C:/Users/ioannis/Desktop/VS CODE/File2Video-Proper/tests/test_file.jpg"



class Result():
    def __init__(self,x,y,framerate,bitrate,padding,initial_size):
        self.x=x
        self.y=y
        self.framerate=framerate
        self.virtual_pixels=[[]]
        self.frames=0
        self.bitrate=bitrate
        self.virtual_pixel_size=[8,8]
        self.current_virtual_pixel=0
        self.padding=padding
        self.size=initial_size

    def color_distr(self,number):
        return number*63
    def safe(self,string):
        if string=='0':
            return '00000000'
        else:
            return string
    
    
    def put_packet_in(self,packet):
        packet_str=self.safe(bin(packet[0])[2:])+self.safe(bin(packet[1])[2:])+self.safe(bin(packet[2])[2:])
        print((packet_str))
        packet_1=packet_str[0:6]
        packet_2=packet_str[6:12]
        packet_3=packet_str[12:18]
        packet_4=packet_str[18:24]
        self.create_virtual_pixel(packet_1)
        self.create_virtual_pixel(packet_2)
        self.create_virtual_pixel(packet_3)
        self.create_virtual_pixel(packet_4)
        
    def create_virtual_pixel(self,color):
        print(color)
        rgb=[self.color_distr(int(color[0:2],2)),self.color_distr(int(color[2:4],2)),self.color_distr(int(color[4:],2))]
        
        print(rgb)
        


        


data = list(Path(input_file).read_bytes())
initial_size=len(data) #data is a list of 8 bit integers (0 to 255)
data.extend([0]*(len(data)%3)) #if not a multiple of 3 pad with zeros and include the information on the Result class
#print(data)

data_combined_to_24_bits=list(zip(*[iter(data)]*3)) #group bytes in groups of 3 (24 bits, so they can be splitted to packets of 6 bits)
#print(min(data),max(data))

final_video=Result(1920,1080,60,500000,(len(data)%3),initial_size)
for packet_of_24_bits in data_combined_to_24_bits:
    final_video.put_packet_in(packet_of_24_bits)
    print(packet_of_24_bits)