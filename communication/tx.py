#!/usr/bin/env python
#coding=utf8
 
import serial
from time import sleep
 
if __name__=="__main__":
    serial = serial.Serial("/dev/pts/15", 115200, timeout=0.5)
    # serial = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.5)
    if serial.isOpen():
        print("open success")
    else:
        print("open failed")
 
    while True:
        serial.write("test1".encode('utf-8'))
        print("send: test")
        sleep(1)