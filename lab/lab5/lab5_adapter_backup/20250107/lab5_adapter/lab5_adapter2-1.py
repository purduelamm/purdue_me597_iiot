# MTConnet adapter sample for ME597 Lab5
# This code is for virtual sensor (random humidity value)
#          and temperature sensor (measure temperatrue)

import sys
import time
import datetime
from data_item import Event, Sample # load data_item package
from mtconnect_adapter import Adapter # load mtconnect_adapter package

import os
import glob
import random

class MTConnectAdapter(object): # MTConnect adapter object

    def __init__(self, host, port): # init of MTconnectAdapter class
        # MTConnect adapter connection info
        self.host = host # host arg of adapter
        self.port = port # port arg of adapter
        self.adapter = Adapter((host, port))

        # For samples
        self.t1 = Sample('t1') # self.t1 takes 't1' sample data item id.
        self.adapter.add_data_item(self.t1) # adding self.t1 in adapter
        ## Add more samples below, if needed.

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

    def read_temp_raw(self):
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*')[0]
        device_file = device_folder + '/w1_slave'
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def read_temp(self):
        lines = self.read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
        
    def adapter_stream(self):
        while True:
            try:
                # Do something here
                # To halt this loop, short-cut is CTRL+C
                t1 = self.read_temp() # temperature
                # h1 = ? # Humidity (random input 50% - 70%)

                now = datetime.datetime.now() # get current data time
                
                self.adapter.begin_gather() # start to collection
                self.t1.set_value(str(t1)) # set SAMPLE value of h1 (temperature) data item
                self.adapter.complete_gather() # end of collection

                print("{} MTConnect data collection completed ... ".format(now)) # Printing out completed MTConnect collection
                print("DS18B20: Temperature={}°C\n".format(t1)) # Printing out DS18B20 measured values
                # print("Virtual: Humidity={}RH%\n".format(h1))

                time.sleep(2) # wait for 2 seconds = sampling period

            except KeyboardInterrupt: # To stop MTConnect adapter, Ctrl + c
                print("Stopping MTConnect...")
                self.adapter.stop() # Stop adapter thread
                sys.exit() # Terminate Python

## ====================== MAIN ======================
if __name__ == "__main__":   
    # start MTConnect Adapter
    MTConnectAdapter('127.0.0.1', 7878) # Args: host ip, port number
