# MTConnet adapter sample for ME597 Lab6

import sys
import time
import datetime
import board
import adafruit_dht
import psutil
from data_item import Event, Sample # load data_item package
from mtconnect_adapter import Adapter # load mtconnect_adapter package

# Kill libgpio process, if already used.
for p in psutil.process_iter():
    if p.name() == 'libgpiod_pulsei' or p.name() == 'libgpiod_pulsein':
        p.kill()


class MTConnectAdapter(object): # MTConnect adapter object

    def __init__(self, host, port): # init of MTconnectAdapter class
        # MTConnect adapter connection info
        self.host = host # host arg of adapter
        self.port = port # port arg of adapter
        self.adapter = Adapter((host, port))

        # For samples
        self.h1 = Sample('h1') # self.t1 takes 'h1' sample data item id.
        self.adapter.add_data_item(self.h1) # adding self.h1 in adapter
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


    def adapter_stream(self):
        while True:
            try:
                # Do something here
                # To halt this loop, short-cut is CTRL+C
                h1 = sensor.temperature # temperature
                # t1 = ?

                now = datetime.datetime.now() # get current data time
                
                self.adapter.begin_gather() # start to collection
                self.h1.set_value(str(h1)) # set SAMPLE value of h1 (humidity) data item
                self.adapter.complete_gather() # end of collection

                print("{} MTConnect data collection completed ... ".format(now)) # Printing out completed MTConnect collection
                print("DHT11: Humidity={}RH%\n".format(h1)) # Printing out DHT11 measured values

                time.sleep(2) # wait for 2 seconds = sampling period

            except KeyboardInterrupt: # To stop MTConnect adapter, Ctrl + c
                print("Stopping MTConnect...")
                self.adapter.stop() # Stop adapter thread
                sys.exit() # Terminate Python
                
            except RuntimeError as e: # exception for DHT11 sensor
                # DHT11 make errors often becuase of reading data.
                # print error and continue.
                print(e.args[0])
                time.sleep(2)
                pass
            
            except Exception as e: # exception for DHT11 sensor
                # If DHT is not detected, break and stop this script.
                sensor.exit()
                raise e

## ====================== MAIN ======================
if __name__ == "__main__":   
    #sensor object for DHT11 sensor, D23 means Pin23 of Raspberry Pi
    sensor = adafruit_dht.DHT11(board.D23)
    
    # start MTConnect Adapter
    MTConnectAdapter('127.0.0.1', 7878) # Args: host ip, port number
