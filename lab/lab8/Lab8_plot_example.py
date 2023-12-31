import matplotlib.pyplot as plt
import csv
import numpy as np
import random
from scipy.fft import fft, fftfreq

# You should change filename.
# If the data is in the different location of this Python script,
# you have to specify the directory information as well.
filename = "20230216_112751_Test_lab8_data.csv" # input your filename
data = [] # initialize data
N = 1000 # number of sample
T = 1/N # sampling period
R = random.randint(0, 9) # randomly pick a integer number between 0 and 10
t = np.linspace(0, 1, N) # create time array for plotting

# Reading a CSV file and convert rows as data
with open(filename, 'r') as f:
    rows = csv.reader(f, delimiter = ',')
    header = next(rows)
    for row in rows:
        data.append(row)

data = np.array(data) #converting data as numpy array


def decompose(data): # decompose data from string (with space delimited) to a float array
    return np.fromstring(data, dtype=float, sep=" ")


a_x = decompose(data[R][1]) # X-axis acceleration array
a_y = decompose(data[R][2]) # Y-axis acceleration array
a_z = decompose(data[R][3]) # Z-axis acceleration array

condition = data[R][0] # get the condition string

your_name = "name" # input your name
Time_title = "Time domain, "+condition+", "+your_name
Freq_title = "Freq domain, "+condition+", "+your_name

fig1, ax1 = plt.subplots(3) # plotting time domain for 3-axis
fig1.suptitle(Time_title)
ax1[0].plot(t,a_x,'tab:blue')
ax1[0].set_ylabel('a_x [m/s2]')
ax1[1].plot(t,a_y, 'tab:orange')
ax1[1].set_ylabel('a_y [m/s2]')
ax1[2].plot(t,a_z, 'tab:green')
ax1[2].set_ylabel('a_z [m/s2]')
ax1[2].set_xlabel('Time [sec]')


def get_fft(x, T, N): # fft converting
    f = fftfreq(N, T)[:N//2]
    y_mag = 2/N * np.abs(fft(x)[:N//2])
    y_mag[0] = 0
    return f, y_mag

f_x, y_x = get_fft(a_x, T, N)
f_y, y_y = get_fft(a_y, T, N)
f_z, y_z = get_fft(a_z, T, N)

fig2, ax2 = plt.subplots(3) #plotting freq domain for 3-axis
fig2.suptitle(Freq_title)
ax2[0].plot(f_x,y_x,'tab:blue')
ax2[0].set_ylabel('|FFT| of a_x')
ax2[1].plot(f_y,y_y,'tab:orange')
ax2[1].set_ylabel('|FFT| of a_y')
ax2[2].plot(f_z,y_z,'tab:green')
ax2[2].set_ylabel('|FFT| of a_z')
ax2[2].set_xlabel('Frequency [Hz]')

plt.show()
