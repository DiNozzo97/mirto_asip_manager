#!/usr/bin/python3
# -*- coding: <utf-8> -*-
__author__ = "Adam Jarzebak"
__copyright__ = "Copyright 2018, Middlesex University"
__license__ = "MIT License"
__maintainer__ = "Adam Jarzebak"
__email__ = "adam@jarzebak.eu"
__status__ = "Production"

import mirto_asip_manager.asip as asip
from mirto_asip_manager.settings import logging as log
import sys


class SystemInfo:
    def __init__(self, name: str, serial_manager) -> None:
        self.name = name
        self.serial_manager = serial_manager
        self.header = asip.SYSTEM_MSG_HEADER
        self.tag = asip.tag_SYSTEM_GET_INFO
        self.system_version = None

    def request_sys_info(self):
        """
        Function sending request to device and asking for information about system
        :return:
        """
        request_string = str(self.header + ',' + self.tag + '\n')
        self.serial_manager.send_request(request_string)

    def process_response(self, message: str) -> None:
        """
        Received message is being processed and displayed to the console using logging
        :param message:
        :return:
        """
        if message[3] != self.tag:
            log.error("Unable to process received message: {}".format(message))
        else:
            self.system_version = message[5:-1]


class Encoders:
    def __init__(self, name: str, serial_manager, debug: bool = False):
        self.name = name
        self.header = asip.id_ENCODER_SERVICE
        self.debug = debug
        self.left_values = None
        self.right_values = None
        self.all_values = None
        self.serial_manager = serial_manager
        self.tag_autoevent_request = asip.tag_AUTOEVENT_REQUEST
        self.tag = asip.tag_SERVICE_EVENT

    def enable(self):
        """
        Sending value 0 will enable autoevent service on Arduino
        :return:
        """
        # Enable all encoders by writing value 1, if you wish to disable you can do it by writing 0
        request_string = str(self.header + ',' + self.tag_autoevent_request + ',' + str(1) + '\n')
        self.serial_manager.send_request(request_string)

    def process_response(self, message: str) -> None:
        """
        This function is taking an input, validating by comparing an service tag and id and extracts values
        A response for a message is something like "@E,e,2,{3000:110,3100:120}"
        :param message:
        :return:
        """
        if message[3] != self.tag:
            # We have received a message but it is not an encoder reporting event
            log.error("Unable to process received message: {}".format(message))
        else:
            enc_values = message[message.index("{") + 1: message.index("}")].split(",")
            self.left_values = [int(i) for i in enc_values[0].split(":")]
            self.right_values = [int(i) for i in enc_values[1].split(":")]
            self.all_values = [self.left_values, self.right_values]
            if self.debug:
                print("Encoders message: {}".format(message))


class Motor:
    def __init__(self, name: str, motor_id: int, serial_manager, debug: bool = False) -> None:
        self.name = name
        self.tag = asip.tag_SET_MOTOR
        self.debug = debug
        self.motor_id = motor_id
        self.header = asip.id_MOTOR_SERVICE
        self.serial_manager = serial_manager

    def send_request(self, motor_power: int) -> None:
        """
        Function is sending a serial request to Arduino, in order to set motor speed
        Example "M,m,0,50"
        :param motor_power:
        :return None:
        """
        request_string = str(self.header + ',' + self.tag + ',' + str(self.motor_id) + ',' +
                             str(motor_power) + '\n')
        self.serial_manager.send_request(request_string)

    def set_motor(self, speed: int) -> None:
        """
        Function in which speed value is being validate in terms of range and type, then send request is being made
        :param speed:
        :return:
        """
        # Speed should be between -100 and +100
        if speed > 100:
            speed = 100
        if speed < -100:
            speed = -100
        if self.debug:
            log.debug("Setting motor id:{} to speed:{}".format(self.motor_id, speed))
        self.send_request(speed)

    def stop_motor(self) -> None:
        """
        Stop motor by sending 0 value to a motor
        :return:
        """
        self.set_motor(0)


class IRSensors:
    def __init__(self, name: str, ir_id: int, serial_manager, debug: bool = False) -> None:
        self.ir_id = ir_id
        self.name = name
        self.serial_manager = serial_manager
        self.tag_autoevent_request = asip.tag_AUTOEVENT_REQUEST
        self.header = asip.id_IR_REFLECTANCE_SERVICE
        self.tag_response = asip.tag_SERVICE_EVENT
        self.debug = debug
        self.ir_left_value = None
        self.ir_center_value = None
        self.ir_right_value = None
        self.ir_all_values = None
        self.max_retries = 3

    def set_reporting_interval(self, interval: int) -> None:
        """
        :param interval:
        :return:
        """
        request_string = str(self.header + ',' + self.tag_autoevent_request + ',' + str(interval) + '\n')
        self.serial_manager.send_request(request_string)

    def process_response(self, message: str) -> bool:
        """
        This function is taking an input, validating by comparing an service tag and id and extracts values
        A response for a message is something like "@E,e,2,{3000:110,3100:120}"
        :param message:
        :return:
        """
        if message[3] != self.tag_response:
            # We have received a message but it is not an ir reporting event
            log.error("Unable to process received message: {}".format(message))
        else:
            for attempt in range(1, self.max_retries + 1):
                try:
                    if attempt == self.max_retries - 1:
                        log.error("Unable to process received message: {}".format(message))
                        sys.exit()
                    else:
                        ir_values = message[message.index("{") + 1: message.index("}")].split(",")
                        self.ir_left_value = int(ir_values[0])
                        self.ir_center_value = int(ir_values[1])
                        self.ir_right_value = int(ir_values[2])
                        self.ir_all_values = [self.ir_left_value, self.ir_center_value, self.ir_right_value]
                        if self.debug:
                            print("Message: {}".format(message))
                        return True
                except ValueError:
                    pass
