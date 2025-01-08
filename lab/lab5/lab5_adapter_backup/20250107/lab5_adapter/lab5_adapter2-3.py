# MTConnet adapter sample for ME597 Lab5
# This code is for power meter

import sys
import time
import datetime
from data_item import Event, Sample # load data_item package
from mtconnect_adapter import Adapter # load mtconnect_adapter package

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


    def adapter_stream(self):
        while True:
            try:
                # Do something here
                # To halt this loop, short-cut is CTRL+C               
                c = ModbusTcpClient("192.168.1.100", port = 502) # args: IP address, port number
                # p1 = ?
                # ps = ?

                now = datetime.datetime.now() # get current data time
                
                self.adapter.begin_gather() # start to collection

                self.adapter.complete_gather() # end of collection

                print("{} MTConnect data collection completed ... ".format(now)) # Printing out completed MTConnect collectiones
                # print("Power meter: Machine is now {}, {} W\n".format(ps,p1)) # Printing out Power meter measured values
                
                c.close() # close the client in every measurement

                time.sleep(0.5) # wait for 0.5 seconds = sampling period

            except KeyboardInterrupt: # To stop MTConnect adapter, Ctrl + c
                print("Stopping MTConnect...")
                self.adapter.stop() # Stop adapter thread
                sys.exit() # Terminate Python


## ====================== MAIN ======================
if __name__ == "__main__":   
    # start MTConnect Adapter
    MTConnectAdapter('127.0.0.1', 7878) # Args: host ip, port number
