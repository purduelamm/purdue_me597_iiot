from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import datetime

# define the gateway IP (host) and port
# normally Modbus TCP uses port number 502
host = "192.168.1.100" # For online student with Cisco VPN : 10.165.67.146
port = 502

# define client object of the host and port
client = ModbusTcpClient(host, port=port)
client.connect()

now = datetime.datetime.now()

# read the holding registers for frequency
# Refer to the Modbus address map
# the arguments are register starting register address (decimal), length, and slave=1.
freq_read = client.read_holding_registers(1536, count=2, slave=1)

# get received registers
freq_reg = freq_read.registers

# define decode the received register values
freq_decoder = BinaryPayloadDecoder.fromRegisters(freq_reg, byteorder=Endian.BIG, wordorder=Endian.BIG)

# get the frequency value by decoding it to 32bit float data.
freq_value = freq_decoder.decode_32bit_float()

# print out value
print("{}: Frequency is {} Hz".format(now, freq_value))

# gently close the client object.
client.close()