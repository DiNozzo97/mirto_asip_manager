#!/usr/bin/python3
# -*- coding: <utf-8> -*-
__author__ = "Adam Jarzebak"
__copyright__ = "Copyright 2018, Middlesex University"
__license__ = "MIT License"
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
    def __init__(self, debug: bool=False) -> None:
        self.isReady = False
        self.conn = SerialConnection()
        self.ports = self.conn.list_available_ports()
        self.selected_port = self.ports[0]
        self.debug = debug
        if self.debug:
            log.debug("Available ports: {}".format(self.ports))
        if not self.isReady:
            self.open_serial()
        log.info("Serial port: %s opened successfully" % self.selected_port)

    def on_open(self) -> None:
        """
        Check if port is open or closed, in case if is open will close it, when is close will open it.
        :return: None
        """
        if self.conn.is_open():
            self.close_serial()
        else:
            self.open_serial()

    def open_serial(self) -> None:
        """
        Opens a serial port using specific parameters
        :return: None
        """
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

    def close_serial(self) -> None:
        self.conn.close()
        self.isReady = False
        log.info("Closing serial port %s" % self.selected_port)

    def send_request(self, request_string: str) -> None:
        """
        Example request string: str(svc_id + ',' + asip.tag_AUTOEVENT_REQUEST + ',' + str(value) + '\n')
        :param request_string:
        :type request_string: str
        :return: None
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
    def __init__(self, debug: bool=False):
        self.serial_manager = SerialManager(debug)
        self.run_event = None
        self.all_services = {}
        self.all_threads = []
        self.debug = debug

    def msg_dispatcher(self, msg: str) -> None:
        """
        Function is checking if the message header is an event message or an error message or
        informational or debug message. Based on the type, function will redirect it to the right functions
        :param msg:
        :type msg: str
        :return: None
        """
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
            log.error('Error: ' + msg[1:])

    def event_dispatcher(self, msg: str) -> None:
        """
        This function is responsible for identification of the header from messages. Based on a header will
        redirect a message to the right service
        :param msg:
        :type msg: str
        :return: None
        """
        service_id = msg[1]
        if service_id == asip.id_ENCODER_SERVICE:
            encoders = self.all_services.get('encoders')
            if encoders is not None:
                encoders.process_response(msg)
        elif service_id == asip.id_BUMP_SERVICE:
            print('Bump')
        elif service_id == asip.SYSTEM_MSG_HEADER:
            sys_info_service = self.all_services.get("sys_info")
            if sys_info_service is not None:
                sys_info_service.process_response(msg)
        elif service_id == asip.id_IR_REFLECTANCE_SERVICE:
            ir_sensor = self.all_services.get("ir_sensors")
            if ir_sensor is not None:
                ir_sensor.process_response(msg)

    def run_services(self, received_message: str) -> None:
        """
        Main loop in which continuously receiving messages from serial buffer, is passing buffer to the 'msg_dispatcher'
        :param received_message:
        :type received_message: str
        :return: None
        """
        # while run_event.is_set():
        #     received_message = self.serial_manager.conn.get_buffer()
        self.msg_dispatcher(received_message)

    def initialize_services(self, services_to_run: dict) -> None:
        """
        Function is taking input argument (services_to_run: dict) and based on these arguments is starting services
        :return:
        """
        # Add version info service
        sys_info = SystemInfo(name="System Info", serial_manager=self.serial_manager)
        sys_info.request_sys_info()
        self.all_services.update({'sys_info': sys_info})

        encoder_run_status = services_to_run.get("encoders")
        if encoder_run_status[0]:
            # Add encoders service
            encoders = Encoders(name="Encoders",
                                serial_manager=self.serial_manager, debug=encoder_run_status[1])
            encoders.enable()
            self.all_services.update({'encoders': encoders})
            log.info("Service encoders enabled. Debug mode: {}".format(encoder_run_status[1]))

        motors_run_status = services_to_run.get("motors")
        if motors_run_status[0]:
            # Add motors service
            motor_1 = Motor(name="Left Motor", motor_id=0,
                            serial_manager=self.serial_manager, debug=motors_run_status[1])
            motor_2 = Motor(name="Right Motor", motor_id=1,
                            serial_manager=self.serial_manager, debug=motors_run_status[1])

            self.all_services.update({'motor_1': motor_1})
            self.all_services.update({'motor_2': motor_2})
            log.info("Service motors enabled. Debug mode: {}".format(motors_run_status[1]))

        ir_sensors_run_status = services_to_run.get("ir_sensors")
        if ir_sensors_run_status[0]:
            # Add IR sensor service
            ir_sensors = IRSensors(name="IR Sensors", ir_id=1, serial_manager=self.serial_manager,
                                   debug=ir_sensors_run_status[1])
            ir_sensors.set_reporting_interval(10)
            self.all_services.update({'ir_sensors': ir_sensors})
            log.info("IR service enabled. Debug mode: {}".format(ir_sensors_run_status[1]))

    def initialize_main(self, services_to_run: dict) -> None:
        self.run_event = threading.Event()
        self.run_event.set()
        main_thread = threading.Thread(name='Teensy msgs receiver', target=self.serial_manager.conn.receive_data,
                                       args=(self.run_event, self.run_services, self.terminate_all))
        # run_services_thread = threading.Thread(name='Services process', target=self.run_services,
        #                                        args=(self.run_event,))
        self.all_threads = [main_thread]
        # Start all threads
        for thread in self.all_threads:
            try:
                thread.start()
                time.sleep(1)
                log.info("Thread: %s set up successfully" % thread.getName())
            except Exception as error:
                log.error("Could not create a thread %s" % error)
        # Init all services
        self.initialize_services(services_to_run)
        # This delay allows to make sure all background services will run, before any task
        sleep(2)

    def terminate_all(self) -> None:
        self.run_event.clear()
        for thread in self.all_threads:
            thread.join()
            log.info("Thread run status: {}: Status: {}".format(thread.getName(), str(thread.is_alive())))
        self.serial_manager.close_serial()
