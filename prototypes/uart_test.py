import serial
import time

serialport = serial.Serial("serial0", baudrate=115200, timeout=3.0)

packet = bytearray([0x06, 0x85, 0x01, 0x02, 0x03, 0xFF, 0xFF, 0xFF, 0x11])
while True:
    serialport.write(packet)
    time.sleep(0.2)
