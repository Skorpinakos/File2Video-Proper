https://user-images.githubusercontent.com/82767099/222876239-d95c6cf6-146b-466c-9634-d8372c631b20.mp4


Example of Resulting Video ^^ (for older 16x16 Virtual Pixels and 720p resolution) 

Use the encoder to turn a file into a video (specify file path in variable input_file) (currently default extension is ".zip")

Use the decoder to turn a video into a file (specify video path in variable input_video) 

Results are placed in 'results' folder.


Example inputs are in 'tests' folder.


Password for example .zip file given is "lorem".

**Tested with Python 3.10.4 and with "opencv-python" & "numpy" installed (latest versions)**

**Now with efficient & scalable multiprocessing support for the encoder !**

**Youtube Safe, video2file ratio is around 10** (after converting to .webm manually or through youtube)


**single_core_encoder.py will not be supported after 7/2/2022**



*
An open source efficient file-2-video encoder (&decoder). The implementation allows the user to transform .zip files to .avi video format in a compression resistant encoding. The produced video can be uploaded to video streaming platforms with unlimited-upload policies (e.g. YouTube) and used as a free cloud storage method.

Each group of 3 Bytes from the .zip file translates to 4 virtual pixels (square patches of a video frame) each encoding 6 Bits (2 bits per RGB color channel). With sufficient virtual pixel size (12x12 was tested as zero transmission error) resistance to video compression is achieved. The python implementation is using multiple performance optimizations to support multiprocessing and alleviate interpreter overhead. Some versions implement performance critical functionality in Cython. 

Final encoding speed for a 3rd Ryzen Generation 6-core CPU was 120KB/s (~20 times faster from original version) with minimal memory/disk use and resulting encoding size ratio came to 1/10 (after .webm transcoding).*
