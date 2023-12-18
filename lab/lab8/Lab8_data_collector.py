import time
import board
import busio
import adafruit_adxl34x
from micropython import const
import csv
import datetime

i2c = busio.I2C(board.SCL, board.SDA) # i2c variable defines I2C interfaces and GPIO pins using busio and board modules

acc = adafruit_adxl34x.ADXL345(i2c) # acc object is instantiation using i2c of Adafruit ADXL34X library

acc.data_rate = const(0b1111) # change sampling rate as 3200 Hz

# ratedict=output rate dictionary
# See Table5 of Lab2 manual key=rate code (decimal), value=output data rate (Hz)
ratedict = {15:3200,14:1600,13:800,12:400,11:200,10:100,9:50,8:25,7:12.5,6:6.25,5:3.13,4:1.56,3:0.78,2:0.39,1:0.2,0:0.1}

print("Output data rate is {} Hz".format(ratedict[acc.data_rate])) # printing out data rate

def getData(sensor:object, N:int): # sensor: ADXL sensor object, N: The number of sample in each timestamp.
    t1 = time.time()
    data_x = [] # initialize data_x to contain x-axis acceleration
    data_y = [] # initialize data_y to contain y-axis acceleration
    data_z = [] # initialize data_z to contain z-axis acceleration
    for i in range(N):
        x_acc, y_acc, z_acc = sensor.acceleration
        data_x.append(str(x_acc))
        data_y.append(str(y_acc))
        data_z.append(str(z_acc))
    x_data = ' '.join(data_x)
    y_data = ' '.join(data_y)
    z_data = ' '.join(data_z)
    return x_data, y_data, z_data # each data returns space delimited string each element is measurement of acceleration

condition_identifier = "Test" # condition identifier
duration = 10 # data collection duration in second unit

filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+"_"+condition_identifier+"_lab8_data.csv"
header = ["Condition", "Xacc array [m/s2]", "Yacc array [m/s2]", "Zacc array [m/s2]"]
start = time.time()

print("== Data collection for {} measurements started. ==".format(duration))

with open(filename, 'w') as f: # Make and open file object
    write = csv.writer(f) # write object for the created file
    write.writerow(header) # write the first row (header)
    for j in range(duration): # for measurement durations
        x, y, z = getData(acc, 1000) # get x-, y-, z-axis acceleration array of 1000 data points (1 second) for each
        print('======= {}th of {} collection ======='.format(j+1, duration)) # Print out the progress 
        write.writerow([condition_identifier, x, y, z])
f.close()

print("== Data saving is done. == takes", time.time() - start)