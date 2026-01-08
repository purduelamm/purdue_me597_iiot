import sys
import time
import datetime
from data_item import Event, Sample  # load data_item package
from mtconnect_adapter import Adapter  # load mtconnect_adapter package

import os
import glob
import random

import board
import busio
import adafruit_adxl34x

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder


# function for power meter (MATCHED TO STANDALONE STYLE)
def readReg(client, address, count=2, unit=1):
    rr = client.read_holding_registers(address, count=count, unit=unit)

    if rr is None or rr.isError():
        raise RuntimeError(f"Modbus read error: {rr}")

    decoder = BinaryPayloadDecoder.fromRegisters(
        rr.registers,
        byteorder=Endian.Big,
        wordorder=Endian.Big
    )
    value = decoder.decode_32bit_float()
    return value


class MTConnectAdapter(object):  # MTConnect adapter object

    def __init__(self, host, port):  # init of MTconnectAdapter class
        # MTConnect adapter connection info
        self.host = host
        self.port = port
        self.adapter = Adapter((host, port))

        # For samples
        self.a1 = Sample('a1')  # X-axis acceleration
        self.adapter.add_data_item(self.a1)

        self.t1 = Sample('t1')  # Temperature
        self.adapter.add_data_item(self.t1)

        self.p1 = Sample('p1')  # Power (Wattage)
        self.adapter.add_data_item(self.p1)

        # For events
        self.ps = Event('ps')   # power state
        self.adapter.add_data_item(self.ps)

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
        with open(device_file, 'r') as f:
            lines = f.readlines()
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
                # ADXL345 acceleration (X-axis only)
                a = acc.acceleration
                a1 = a[0]

                # DS18B20 temperature
                t1 = self.read_temp()

                # Modbus TCP (Power meter)
                host = "192.168.1.100"
                port = 502
                c = ModbusTcpClient(host, port=port)

                if not c.connect():
                    c.close()
                    raise RuntimeError(f"Connect failed: {host}:{port}")

                try:
                    # Watt register (confirmed)
                    p1 = readReg(c, 1564, count=2, unit=1)
                finally:
                    c.close()

                # logic to determine power state
                ps = 'ON' if p1 > 0 else 'OFF'

                now = datetime.datetime.now()

                self.adapter.begin_gather()
                self.a1.set_value(str(a1))
                self.t1.set_value(str(t1))
                self.p1.set_value(str(p1))
                self.ps.set_value(str(ps))
                self.adapter.complete_gather()

                print("{} MTConnect data collection completed ... ".format(now))
                print("ADXL345: Xacc={} mm/s^2".format(a1))
                print("DS18B20: Temperature={} °C".format(t1))
                print("Power meter: Machine is now {}, {} W\n".format(ps, p1))

                time.sleep(2)

            except KeyboardInterrupt:
                print("Stopping MTConnect...")
                self.adapter.stop()
                sys.exit()


# ====================== MAIN ======================
if __name__ == "__main__":
    # i2c variable defines I2C interfaces and GPIO pins using busio and board modules
    i2c = busio.I2C(board.SCL, board.SDA)

    # acc object is instantiation using i2c of Adafruit ADXL34X library
    acc = adafruit_adxl34x.ADXL345(i2c)

    # start MTConnect Adapter
    MTConnectAdapter('127.0.0.1', 7878)
