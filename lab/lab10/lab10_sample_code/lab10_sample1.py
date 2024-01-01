from xml.etree import ElementTree as ET
import requests
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import math


## == CONSTANT ==
SAMPLE = "sample" # sample string for MTConnect HTML sample method
CURRENT = "current" # current string for MTConnect HTML current method
SAMP_RATE = int(?) # sampling rate
CHUNK = int(?) # chunk size (ro Count/sequence)
AGENT = "http://?ip?:?port?/" # MTConnect agent ip:port

N = int(?) # number of sequence to take sound
N_FFT = int(?) # number of FFT
N_MELS = int(?) # number of Mel filter bank


# Note that %27 means ' (single quote) in ASCII encode. UTF-8 is default in HTML5
response = requests.get(AGENT+CURRENT+"?path=//DataItem[@id=%27sensor1%27]") # XML response from the MTConnect
# full HTML request is "http://ip:port/current?path=//DataItem[@id='sensor1']"
root = ET.fromstring(response.content) # XML parsing
MTCONNECT_STR = root.tag.split("}")[0]+"}" # Get MTConnect string (schema version)
header = root.find("./"+MTCONNECT_STR+"Header") # Parsing Header info
header_attribs = header.attrib # Header attribude
nextSeq = int(header_attribs["nextSequence"]) # next sequence
firstSeq = int(header_attribs["firstSequence"]) # first sequence
lastSeq = int(header_attribs["lastSequence"]) # last sequence

# get timestamp because the current request for a dataitemId (sensor1) was made, the number of same is 1.
for sample in root.iter(MTCONNECT_STR+"DisplacementTimeSeries"):
    timestamp = sample.get("timestamp")

# print out current sequence information
print("Current sequence info, timestamp: {}, firstSeq={}, nextSeq={}, lastSeq={}".format(timestamp,nextSeq,firstSeq,lastSeq))

# Get sound data for 1-second-long using sample method based on the sequence information above of MTConnect
response = requests.get(AGENT+SAMPLE+"?from="+str(int(lastSeq-N))+"&count="+str(N)+"&path=//DataItem[@id=%27sensor1%27]")
# full HTML request if "http://ip:port/sample?from=77&count=23&path=//DataItem[@id='sensor1']"
# in case lastSeq = 100 and N = 23
root = ET.fromstring(response.content) # XMl parsing
signal_array = [] # initialize siganl arry

for sample in root.iter(MTCONNECT_STR+"DisplacementTimeSeries"):
    chunk = np.fromstring(sample.text, dtype=np.int16, sep=' ') / (2 ** 15) # convert each sequence data (chunk) into signed 16 int array
    signal_array = np.append(signal_array, chunk) # append each chunk to signal_array

signal = np.array(signal_array, dtype=np.float32) # convert signal_array to float signal array
signal_rms = np.sqrt(np.mean(signal ** 2)) # signal rms
sound_level = 20*math.log10(signal_rms/9.9963e-7)-28.87 # sound pressure level in dB SPL
M_signal = librosa.feature.melspectrogram(y=signal, sr=SAMP_RATE, n_fft=N_FFT, hop_length=int(N_FFT/4), win_length=N_FFT, window='hann', n_mels=N_MELS) # Mel-spectrogram

print("signal SPL (sound pressure level) is {} dB.".format(sound_level)) # print out SPL
#print("Length of signal is ", len(?)/?, "[sec]") # signal length is second unit

fig, ax = plt.subplots(1,2, figsize=(12,4)) # plot time domain and mel-spectrogram of the sound signal
librosa.display.waveshow(signal, sr=SAMP_RATE, ax=ax[0], color="blue") # time domain plot
ax[0].text(0.1,0.7,str(round(sound_level,2))+" dB SPL") # add text (sound pressure level in time domain plot)
img = librosa.display.specshow(librosa.power_to_db(2*abs(M_signal)/N_FFT, ref=1), ax=ax[1], x_axis='time', y_axis='mel', sr=SAMP_RATE, vmin=-80, vmax=0) # Mel-spectrogram
ax[0].set(title=timestamp+": time domain", ylim=[-1, 1], ylabel="Amplitude [-]", xlabel="Times [sec]")
ax[1].set(title=timestamp+": Mel-spectrogram", ylabel="Log-frequency [Hz]", xlabel="Time [sec]")
cbar = fig.colorbar(img, ax=ax[1], format="%+2.0f dB")
fig.suptitle(AGENT+SAMPLE+" sound signal for 1 second")
plt.show()
# The program ends when you close the figure window.

