# MTConnet adapter sample for ME597 Lab5
# This code is for accelerometer sensor (measure acceleration)

import sys
import time
import datetime
from data_item import Event, Sample # load data_item package
from mtconnect_adapter import Adapter # load mtconnect_adapter package

import board
import busio
import adafruit_adxl34x

class MTConnectAdapter(object): # MTConnect adapter object

    def __init__(self, host, port): # init of MTconnectAdapter class
        # MTConnect adapter connection info
        self.host = host # host arg of adapter
        self.port = port # port arg of adapter
        self.adapter = Adapter((host, port))

        # For samples
        self.a1 = Sample('a1') # self.a1 takes 'a2' sample data item id.
        self.adapter.add_data_item(self.a1) # adding self.a2 in adapter
        self.a2 = Sample('a2') # self.a1 takes 'a1' sample data item id.
        self.adapter.add_data_item(self.a2) # adding self.a3 in adapter

        # For events
        ## Add more events below, if needed.

        # MTConnnect adapter availability
        self.avail = Event('avail')
        self.adapter.add_data_item(self.avail)

        # Start MTConnect
        self.adapter.start()
        self.adapter.begin_gather()
        self.avail.set_value("AVAILABLE")
        self.adapter.complete_gather()
        self.adapter_stream()


    def adapter_stream(self):
        while True:
            try:
                # Do something here
                # To halt this loop, short-cut is CTRL+C
                a = acc.acceleration # get acceleration
                # a1 = ?
                a2 = a[1] # get Y-axis acceleration
                a3 = a[2] # get Z-axis acceleration

                now = datetime.datetime.now() # get current data time
                
                self.adapter.begin_gather() # start to collection

                self.a2.set_value(str(a2)) # set SAMPLE value of a2 (Y-axis acceleration) data item
                self.a3.set_value(str(a3)) # set SAMPLE value of a3 (Z-axis acceleration) data item

                self.adapter.complete_gather() # end of collection

                print("{} MTConnect data collection completed ... ".format(now)) # Printing out completed MTConnect collection
                print("ADXL345: Yacc={}, Zacc={} mm/s^2\n".format(a2,a3)) # Printing out ADXL345 measured values

                time.sleep(1) # wait for 1 second = Sampling period

            except KeyboardInterrupt: # To stop MTConnect adapter, Ctrl + c
                print("Stopping MTConnect...")
                self.adapter.stop() # Stop adapter thread
                sys.exit() # Terminate Python


## ====================== MAIN ======================
if __name__ == "__main__":
    # i2c variable defines I2C interfaces and GPIO pins using busio and board modules
    i2c = busio.I2C(board.SCL, board.SDA)

    # acc object is instantiation using i2c of Adafruit ADXL34X library 
    acc = adafruit_adxl34x.ADXL345(i2c)
        
    # start MTConnect Adapter
    MTConnectAdapter('127.0.0.1', 7878) # Args: host ip, port number
