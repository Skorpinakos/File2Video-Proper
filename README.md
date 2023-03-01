Use the encoder to turn a file into a video (specify file path in variable input_file) (currently default extension is ".zip")

Use the decoder to turn a video into a file (specify video path in variable input_video) 

Results are placed in 'results' folder.


Example inputs are in 'tests' folder.


The from_youtube.mp4 is from https://youtu.be/xsKBArGZLgg, it is the exported.avi, uploaded to Youtube and downloaded again.The first file result is from decoding the exported.avi and the second from decoding from_youtube.mp4. They are identical proving that youtube compression is not altering results (for the given setting of encoder, decoder)


Password for example .zip file given is "iot".
