# MTConnet adapter sample for ME597 Lab5

import sys
import time
import datetime
from data_item import Event, Sample # load data_item package
from mtconnect_adapter import Adapter # load mtconnect_adapter package

import os
import glob
import random

import board
import busio
import adafruit_adxl34x

from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

# function for power meter
def readReg(client, address, length, slave=1):
    read = client.read_holding_registers(address, length, slave=1)
    reg = read.registers
    decoder = BinaryPayloadDecoder.fromRegisters(reg, byteorder=Endian.BIG, wordorder=Endian.BIG)
    value = decoder.decode_32bit_float()
    return value


class MTConnectAdapter(object): # MTConnect adapter object

    def __init__(self, host, port): # init of MTconnectAdapter class
        # MTConnect adapter connection info
        self.host = host # host arg of adapter
        self.port = port # port arg of adapter
        self.adapter = Adapter((host, port))

        # For samples
        self.a1 = Sample('a1') # self.a1 takes 'a1' sample data item id.
        self.adapter.add_data_item(self.a1) # adding self.a1 in adapter

        self.t1 = Sample('t1') # self.t1 takes 't1' sample data item id.
        self.adapter.add_data_item(self.t1) # adding self.t1 in adapter
        
        self.p1 = Sample('p1') # self.p1 takes 'p1' sample data item id.
        self.adapter.add_data_item(self.p1) # adding self.p1 in adapter
        ## Add more samples below, if needed.

        # For events
        self.ps = Event('ps') # self.ps takes 'ps' (power state) event data item id
        self.adapter.add_data_item(self.ps) # adding self.ps in adapter
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
                a = acc.acceleration # get acceleration
                a1 = a[0] # get only X-axis acceleration
                # a2 =
                # a3 =

                t1 = self.read_temp() # temperature
                # h1 = ? # Humidity (random input 50% - 70%)
                
                c = ModbusTcpClient("192.168.1.100",port = 502) # args: IP address, port number
                p1 = readReg(c, 1564, count = 2,slave=1) # true power, W
                
                ## logic to determine power state
                if p1 > 0:
                    ps = 'ON'
                else:
                    ps = 'OFF'
                ##                 

                now = datetime.datetime.now() # get current data time
                
                self.adapter.begin_gather() # start to collection

                self.a1.set_value(str(a1)) # set SAMPLE value of a1 (X-axis acceleration) data item
                self.t1.set_value(str(t1)) # set SAMPLE value of t1 (Temperature) data item
                
                self.p1.set_value(str(p1)) # set SAMPLE value of p1 (power, Watt) data item
                self.ps.set_value(str(ps)) # set EVENT value of ps (power state) data item

                self.adapter.complete_gather() # end of collection

                print("{} MTConnect data collection completed ... ".format(now)) # Printing out completed MTConnect collection
                print("ADXL345: Xacc={} mm/s^2".format(a1)) # Printing out ADXL345 measured values
                print("DS18B20: Temperature={} °C".format(t1)) # Printing out DS18B20 measured values
                print("Power meter: Machine is now {}, {} W\n".format(ps,p1)) # Printing out Power meter measured values
                
                c.close() # close the client in every measurement

                time.sleep(2) # wait for 2 seconds

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
