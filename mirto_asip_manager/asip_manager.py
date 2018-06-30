#!/usr/bin/python3
# -*- coding: <utf-8> -*-
__author__ = "Adam Jarzebak"
__copyright__ = "Copyright 2018, Middlesex University"
__license__ = "MIT License"
__version__ = "1.0.0"
__maintainer__ = "Adam Jarzebak"
__email__ = "adam@jarzebak.eu"
__status__ = "Production"

from mirto_asip_manager.serialConnector import SerialConnection
import threading
from mirto_asip_manager.services import *
from time import sleep
import time
from mirto_asip_manager.settings import logging as log


class SerialManager:
    def __init__(self):
        self.isReady = False
        self.conn = SerialConnection()
        self.ports = self.conn.list_available_ports()
        self.selected_port = self.ports[0]
        self.debug = True
        if self.debug:
            log.debug("Available ports: {}".format(self.ports))
        if not self.isReady:
            self.open_serial()
        log.info("Serial port: %s opened successfully" % self.selected_port)

    def on_open(self):
        if self.conn.is_open():
            self.close_serial()
        else:
            self.open_serial()

    def open_serial(self):
        baud_rate = 57600
        my_port = self.selected_port
        timeout = 1
        self.conn.open(my_port, baud_rate, timeout)
        if self.debug:
            log.debug("Open serial port. %s" % self.conn.ser)
        if self.conn.is_open():
            if self.conn.send(asip.INFO_REQUEST.encode()):
                self.isReady = True
        else:
            log.error("Failed to open serial port")

    def close_serial(self):
        self.conn.close()
        self.isReady = False
        log.info("Closing serial port %s" % self.selected_port)

    def send_request(self, request_string: str) -> None:
        """
        Example request string: str(svc_id + ',' + asip.tag_AUTOEVENT_REQUEST + ',' + str(value) + '\n')
        :param request_string:
        :return:
        """
        if self.isReady:
            request_string = request_string.encode()
            if self.debug:
                log.debug("Request msg: %s" % (request_string.decode().strip('\n')))
            successfully_sent_message = self.conn.send(request_string)
            if not successfully_sent_message:
                # If send failed so close port
                self.close_serial()
        else:
            log.error('Serial port is not connected')


class AsipManager:
    def __init__(self):
        self.serial_manager = SerialManager()
        self.run_event = None
        self.all_services = {}
        self.all_threads = []
        self.debug = True

    def msg_dispatcher(self, msg) -> None:
        if len(msg) > 0:
            msg_head = msg[0]
        else:
            # TODO Fix problem with incorrect message type
            msg_head = ""
            log.error("Problem with with message dispatching")
        if msg_head == asip.EVENT_HEADER:
            self.event_dispatcher(msg)
        elif msg_head == asip.DEBUG_MSG_HEADER:
            log.debug(msg[1:])
        elif msg_head == asip.ERROR_MSG_HEADER:
            log.error('Err: ' + msg[1:])

    def event_dispatcher(self, msg):
        service_id = msg[1]
        if service_id == asip.id_ENCODER_SERVICE:
            encoders = self.all_services.get('encoders')
            if encoders is not None:
                encoders.process_response(msg)
        elif service_id == asip.id_BUMP_SERVICE:
            print('Bump')
        elif service_id == asip.SYSTEM_MSG_HEADER:
            sys_info_service = self.all_services.get("sys_info")
            sys_info_service.process_response(msg)
        elif service_id == asip.id_IR_REFLECTANCE_SERVICE:
            print('Reflectance')

    def run_services(self, run_event):
        while run_event.is_set():
            received_message = self.serial_manager.conn.get_buffer()
            # print (received_message)
            self.msg_dispatcher(received_message)
            sleep(0.001)

    def initialize_services(self) -> None:
        """
        :return:
        """
        # Add version info service
        sys_info = SystemInfo(name="System Info", serial_manager=self.serial_manager)
        sys_info.initialize()
        self.all_services.update({'sys_info': sys_info})

        # Add encoders service
        encoders = Encoders(name="Encoders", svc_id=asip.id_ENCODER_SERVICE,
                            serial_manager=self.serial_manager, debug=False)
        encoders.initialize()
        self.all_services.update({'encoders': encoders})

        # Add motors service
        motor_1 = Motor(name="Left Motor", svc_id=asip.tag_SET_MOTOR, motor_id=0,
                        serial_manager=self.serial_manager, debug=False)
        motor_2 = Motor(name="Right Motor", svc_id=asip.tag_SET_MOTOR, motor_id=1,
                        serial_manager=self.serial_manager, debug=False)
        self.all_services.update({'motor_1': motor_1})
        self.all_services.update({'motor_2': motor_2})

        # Print all services available
        log.info("Initialing services: %s" % self.all_services.keys())
        sleep(0.5)

    def initialize_main(self) -> None:
        self.run_event = threading.Event()
        self.run_event.set()
        main_thread = threading.Thread(name='Teensy msgs receiver', target=self.serial_manager.conn.receive_data,
                                       args=(self.run_event,))
        run_services_thread = threading.Thread(name='Services process', target=self.run_services,
                                               args=(self.run_event,))
        self.all_threads = [main_thread, run_services_thread]
        # Start all threads
        for thread in self.all_threads:
            try:
                thread.start()
                time.sleep(1)
                log.info("Thread: %s set up successfully" % thread.getName())
            except Exception as error:
                log.error("Could not create a thread %s" % error)
        # Init all services
        self.initialize_services()

    def terminate_all(self) -> None:
        self.run_event.clear()
        for thread in self.all_threads:
            thread.join()
            log.info("Thread run status: {}: Status: {}".format(thread.getName(), str(thread.is_alive())))
        self.serial_manager.close_serial()

# motors = Motor(root,'Motor Control', ('Left', 'Right'))
# encoders = Encoder(root,'Encoders',asip.id_ENCODER_SERVICE, ('Left', 'Right'))
# bump = Service(root,'Bump Sensors',asip.id_BUMP_SERVICE, ('Left', 'Right'))
# reflectance = Service(root,'Reflectance Sensors',asip.id_IR_REFLECTANCE_SERVICE,('Left', 'Center','Right'))

# def showInfo(msg):
#     info = msg.split(',')
#     msg = 'ASIP version %s.%s running on %s using sketch: %s' % (info[0], info[1], info[2], info[4])
#     logMsg(msg)
