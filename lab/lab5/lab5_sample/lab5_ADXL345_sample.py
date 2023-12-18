import time
import board
import busio
import adafruit_adxl34x
import datetime

# i2c variable defines I2C interfaces and GPIO pins using busio and board modules
i2c = busio.I2C(board.SCL, board.SDA)

# acc object is instantiation using i2c of Adafruit ADXL34X library 
acc = adafruit_adxl34x.ADXL345(i2c)

while True: # To halt program, hit Ctrl + c or click Stop button
    now = datetime.datetime.now()
    x_acc, y_acc, z_acc = acc.acceleration
    print("{}: x-axis={:.4f}m/s^2, y-axis={:.4f}m/s^2, z-axis={:.4f}m/s^2".format(now, x_acc, y_acc, z_acc))
    time.sleep(1)