from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import datetime
import time


# define the gateway IP (host) and port
# normally Modbus TCP uses port number 502
# The IP address is 100 but if not working, please let TA know.
host = "192.168.1.100"
port = 502

# readReg function is returning decoded power meter data
# Args are address:str = starting register address to read, length:Int = Consequtive length of the register to read

def readReg(address, length, slave=1):
    read = client.read_holding_registers(address, length, slave=1)
    reg = read.registers
    decoder = BinaryPayloadDecoder.fromRegisters(reg, byteorder=Endian.BIG, wordorder=Endian.BIG)
    value = decoder.decode_32bit_float()
    return value


while True:
    try:
        # define client object of the host and port
        client = ModbusTcpClient(host, port)
        client.connect()
        
        now = datetime.datetime.now()
        
        # This is true power in unit of W
        power = readReg(1564, 2, slave=1)
        # if you want to read other data, please try to use readReg function.
        
        # printing out current timestamp and the measurement
        print("{}: power consumption is {} W".format(now, power))
        
        # gently close the client in every measurement
        client.close()
        
        time.sleep(1)

    except Exception as e:
        print(e)
        raise e