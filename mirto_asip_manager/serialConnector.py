#!/usr/bin/python3
# -*- coding: <utf-8> -*-
__author__ = "Adam Jarzebak"
__copyright__ = "Copyright 2018, Middlesex University"
__license__ = "MIT License"
__maintainer__ = "Adam Jarzebak"
__email__ = "adam@jarzebak.eu"
__status__ = "Production"

import serial
from time import sleep
import sys
import glob
from mirto_asip_manager.settings import logging as log


class SerialConnection:
    def __init__(self):
        self.ser = serial.Serial()
        self.ser.timeout = 0  # Ensure non-blocking
        self.ser.writeTimeout = 0  # Ensure non-blocking
        self.debug = False

    def open(self, port, baud, timeout) -> None:
        """
        Function opens a serial port with given parameters
        :param port:
        :param baud:
        :param timeout:
        :return:
        """
        if self.ser.isOpen():
            self.ser.close()
        self.ser.port = port
        self.ser.baudrate = baud
        self.ser.timeout = timeout
        self.ser.open()
        # Toggle DTR to reset Arduino
        self.ser.setDTR(False)
        sleep(1)
        # Toss any data already received
        self.ser.flushInput()
        self.ser.setDTR(True)

    def close(self) -> None:
        self.ser.close()

    def is_open(self) -> None:
        return self.ser.isOpen()

    def send(self, msg: bytes) -> bool:
        if self.ser.isOpen():
            try:
                self.ser.write(msg)
                return True
            except (OSError, serial.SerialException):
                return False
        return False

    def receive_data(self, run_event, run_services, terminate_all) -> None:
        if not self.ser.isOpen():
            log.error("Connection dropped, please check serial")
        else:
            ser_buffer = ""
            while run_event.is_set():
                try:
                    c = self.ser.read()  # attempt to read a character from Serial
                    c = c.decode('utf-8', errors='ignore')
                    if len(c) == 0:  # was anything read?
                        pass
                    else:
                        if c == '\n' or c == '\n':
                            if len(ser_buffer) > 0:
                                ser_buffer += '\n'
                                run_services(ser_buffer)
                                if self.debug:
                                    log.debug("DEBUG: Complete message from serial: {}\n".format(ser_buffer))
                            ser_buffer = ""
                        else:
                            ser_buffer += c
                except serial.SerialTimeoutException:
                    continue  # Go to next iteration in case of serial timeout
                except serial.SerialException as e:
                    log.error("Caught SerialException in serial read: {}. Listener Thread will now stop".format(e))
                    terminate_all()
                except Exception as e:
                    sys.stdout.write("Caught exception: {} Listener Thread will NOT stop".format(e))

    def get_buffer(self) -> str:
        return self.serBuffer.decode('utf-8')

    def list_available_ports(self) -> list:
        """Lists self.serial ports

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of available self.serial ports
        """
        if sys.platform.startswith('win'):
            ports = ['COM' + str(i + 1) for i in range(256)]

        elif sys.platform.startswith('linux'):
            # this is to exclude your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')

        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')

        else:
            raise EnvironmentError('Unsupported platform')

        result = []

        for port in ports:
            try:
                self.ser.port = port
                self.ser.open()
                self.ser.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
            except IOError:
                pass

        return result
