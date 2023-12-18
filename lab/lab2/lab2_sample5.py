#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ME597-IIoT Implmt. for Smrt Mfg.
Lab2 - sample code 5: Reading CSV file, signal processing, plotting
"""

import matplotlib
matplotlib.use('tkagg')
import matplotlib.pyplot as plt
import csv
import numpy as np

# You should change filename.
filename = "20220128_024155_lab3_part5.csv"

dt = [] # sampling period list, dt
t = [] # time list, t
a_x = [] # x-axis acceleration list, a_x
a_y = [] # y-axis acceleration list, a_y
a_z = [] # z-axis acceleration list, a_z

# Reading a CSV file and convert rows as data
with open(filename, 'r') as f:
    rows = csv.reader(f, delimiter = ',')
    header = next(rows)
    for row in rows:
        dt.append(float(row[0]))
        t.append(float(row[1]))
        a_x.append(float(row[2]))
        a_y.append(float(row[3]))
        a_z.append(float(row[4]))


N = int(len(dt)) # Number of sample = 1000
T = t[-1]/N # sampling period, assumed equally distributed

n = np.array(range(len(dt))) + 1 # measured sequence
dt = np.array(dt) # convert dt list to dt 1D array
t = np.array(t) # convert t list to t 1D array
a_x = np.array(a_x) # convert a_x list to a_x 1D array
a_y = np.array(a_y) # convert a_y list to a_y 1D array
a_z = np.array(a_z) # convert a_z list to a_z 1D array


fig1, ax1 = plt.subplots(3)
fig1.suptitle('Time domain')
ax1[0].plot(t,a_x,'tab:blue')
ax1[0].set_ylabel('a_x [m/s2]')
ax1[1].plot(t,a_y, 'tab:orange')
ax1[1].set_ylabel('a_y [m/s2]')
ax1[2].plot(t,a_z, 'tab:green')
ax1[2].set_ylabel('a_z [m/s2]')
ax1[2].set_xlabel('Time [sec]')


from scipy.fft import fft, fftfreq

# get_fft is a function to calculate FFT
# arguments are x(signal array, T(sampling period), N(number of Samples)
# returns are f(frequency array) and y_mag(FFT magnitude array)
def get_fft(x, T, N):
    f = fftfreq(N, T)[:N//2]
    y_mag = 2/N * np.abs(fft(x)[:N//2])
    y_mag[0] = 0
    return f, y_mag


f_x, y_x = get_fft(a_x, T, N)
# f_y, y_y = 
# f_z, y_z = 

fig2, ax2 = plt.subplots(3)
fig2.suptitle('Frequency domain')
ax2[0].plot(f_x,y_x,'tab:blue')
ax2[0].set_ylabel('|FFT| of a_x')
# ax2[1].plot(f_y,y_y,'tab:orange')
# ax2[1].set_ylabel('|FFT| of a_y')
# ax2[2].plot(f_z,y_z,'tab:green')
# ax2[2].set_ylabel('|FFT| of a_z')
ax2[2].set_xlabel('Frequency [Hz]')

plt.show()