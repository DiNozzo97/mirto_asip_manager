#!/usr/bin/python3
# -*- coding: <utf-8> -*-
__author__ = "Adam Jarzebak"
__copyright__ = "Copyright 2018, Middlesex University"
__license__ = "MIT License"
__maintainer__ = "Adam Jarzebak"
__email__ = "adam@jarzebak.eu"
__status__ = "Production"

from mirto_asip_manager.asip_manager import AsipManager
from time import sleep
from mirto_asip_manager.settings import logging as log
import time


class MirtoRobot:
    def __init__(self, debug: bool, services_on: dict) -> None:
        self.robot = AsipManager(debug)
        self.robot.initialize_main(services_on)
        self.get_version_info()

    def terminate(self) -> None:
        """
        Function which is making all threads and ports terminated
        :return:
        """
        self.robot.terminate_all()

    def get_version_info(self):
        """
        Getting and displaying information about current system installed on mirto robot
        :return:
        """
        sys_info_service = self.robot.all_services.get("sys_info")
        if sys_info_service is not None:
            log.info("System version info: %s" % sys_info_service.system_version)
        else:
            log.warning("Service get_version_info is not enabled!")

    def get_left_encoder_values(self, delta: bool=False) -> list:
        """
        Retrieving left wheel encoder values. Please provide True or False if delta values required
        :param delta:
        :return:
        """
        encoders = self.robot.all_services.get('encoders')
        if encoders is not None:
            left_values_all = encoders.left_values
            if delta:
                return left_values_all
            else:
                return left_values_all[1]
        else:
            log.warning("Service encoders is not enabled!")

    def get_right_encoder_values(self, delta: bool=False) -> list:
        """
        Retrieving right wheel encoder values. Please provide True or False if delta values required
        :param delta:
        :return:
        """
        encoders = self.robot.all_services.get('encoders')
        if encoders is not None:
            right_values_all = encoders.right_values
            if delta:
                return right_values_all
            else:
                return right_values_all[1]
        else:
            log.warning("Service encoders is not enabled!")

    def get_encoders_values(self, delta: bool=False) -> list:
        """
        Function getting encoders count for both wheels. Please provide True if delta value is required.
        :return: Encoders counts
        :rtype: list
        """
        encoders = self.robot.all_services.get('encoders')
        if encoders is not None:
            values_all = encoders.all_values
            if delta:
                return values_all
            else:
                return [values_all[0][1], values_all[1][1]]
        else:
            log.warning("Service encoders is not enabled!")

    def set_motors(self, speed0: int, speed1: int) -> None:
        """
        Input is a speed value which is send to robot. Range: -100 -> 100
        :param speed0:
        :param speed1:
        :return:
        """
        motor_1 = self.robot.all_services.get('motor_1')
        motor_2 = self.robot.all_services.get('motor_2')
        if motor_1 or motor_1 is not None:
            motor_1.set_motor(speed0)
            motor_2.set_motor(speed1)
            log.info("Setting motor: '{}': {} motor:'{}': {}".format(motor_1.name, speed0, motor_2.name, speed1))
        else:
            log.warning("One of the motors is not enabled!")

    def stop_motors(self) -> None:
        """
        Sending speed value 0 to both motor will cause robot to stop
        :return:
        """
        motor_1 = self.robot.all_services.get('motor_1')
        motor_2 = self.robot.all_services.get('motor_1')
        if motor_1 or motor_1 is not None:
            motor_1.stop_motor()
            motor_2.stop_motor()
            log.info("Motors stopped")
        else:
            log.warning("One of the motors is not enabled!")

    def get_ir_sensors_values(self) -> list:
        """
        Receiving ir sensors values, then appending to the list and returning. Please amend the order list if sensors
        are positioned in different order.
        :return:
        """
        ir_sensors = self.robot.all_services.get('ir_sensors')
        if ir_sensors is not None:
            ir_sensors_order = [0, 1, 2]
            ir_all_values = []
            for num in ir_sensors_order:
                ir_all_values.append(ir_sensors.ir_all_values[num])
            return ir_all_values
        else:
            log.warning("Service IR sensors is not enabled!")

    def test_encoders(self, interval: float=0.1, time_to_finish: int=10) -> None:
        end_time = time.time() + time_to_finish
        while time.time() < end_time:
            print(self.get_left_encoder_values(True), self.get_right_encoder_values(True))
            sleep(interval)
        log.info("Finish encoder test")

    def test_motor(self, with_encoders: bool=False, period: time=5) -> None:
        self.set_motors(30, 30)
        if with_encoders:
            self.test_encoders(0.1, period)
        else:
            sleep(period)
        self.stop_motors()

    def test_ir_sensors(self, time_to_finish: int = 10, interval: float = 0.1) -> None:
        end_time = time.time() + time_to_finish
        while time.time() < end_time:
            print(self.get_ir_sensors_values())
            sleep(interval)


if __name__ == '__main__':
    services_on = {"encoders": [True, False], "motors": [True, False], "ir_sensors": [True, False]}
    # Run services test
    mirto = MirtoRobot(debug=False, services_on=services_on)
    mirto.test_encoders(0.1, 2)
    mirto.test_motor(True, 2)
    mirto.test_ir_sensors(2, 0.2)
    # This will stop all threads and close ports
    mirto.terminate()
