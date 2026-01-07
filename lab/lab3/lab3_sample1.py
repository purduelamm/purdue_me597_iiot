from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import datetime

host = "192.168.1.100"  # Online student with Cisco VPN: "10.165.67.146"
port = 502

client = ModbusTcpClient(host, port=port)

if not client.connect():
    raise RuntimeError(f"Connect failed: {host}:{port}")

now = datetime.datetime.now()

freq_read = client.read_holding_registers(1536, count=2, unit=1)

if freq_read.isError():
    client.close()
    raise RuntimeError(f"Modbus read error: {freq_read}")

freq_reg = freq_read.registers

decoder = BinaryPayloadDecoder.fromRegisters(
    freq_reg,
    byteorder=Endian.Big,
    wordorder=Endian.Big
)


freq_value = decoder.decode_32bit_float()

print(f"{now}: Frequency is {freq_value} Hz")

client.close()
