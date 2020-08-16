import socket
from datetime import datetime
import datetime
import calendar
import time
import math

from instrument_driver.autonics.modbus_tk4s import autonics_pid_tk4s

host = 'localhost'
port = 1233

class sock_client:

    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Waiting for connection')
        self.client_socket.connect((host, port))
        pass

    def send_data(self,pv, precision):
        try:
            timestamp = datetime.datetime.utcnow()
            unixtime = calendar.timegm(timestamp.utctimetuple())
            str_hex_utc_time = str(hex(unixtime)).replace('0x', '').encode()

            stx = str.encode('{:1x}'.format(2))
            equipment_id = str.encode('TK{:04x}'.format(1))
            function_code = str.encode('PV')
            precision = int(precision)

            pv = math.pow(10, precision) * int(pv)
            pv = int(pv)
            sensor_code = str.encode('{:04x}'.format(1))  ##sensor code 0001 (전압)
            sensor_value = str.encode('{:04x}'.format(pv))  # 측정 값에 10 ^ 소수점 자리수를 적용한 값
            precision = str.encode('{:01x}'.format(precision))  ## 소수점 자리수

            etx = str.encode('{:1x}'.format(3))
            modbus_packet = stx + str_hex_utc_time + equipment_id + sensor_code + function_code + sensor_value + precision + etx
            print(unixtime, str_hex_utc_time, modbus_packet, len(modbus_packet))
            try:
                self.client_socket.send(modbus_packet)
                message = self.client_socket.recv(29)
                print(message)
                time.sleep(1)
            except socket.error as e:
                print(str(e))
                self.client_socket.close()

        except socket.error as e:
            print(str(e))
            self.client_socket.close()


if __name__ == '__main__':
    client = sock_client()
    PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE = 'N', 'E', 'O', 'M', 'S'
    MODE_RTU = "rtu"
    MODE_ASCII = "ascii"
    widows_port = 'COM3'
    mac_port = '/dev/cu.usbserial-AQ00WOQH'
    tk4s = autonics_pid_tk4s(port=mac_port, station_id=1, baudrate=19200, databits=8, parity=PARITY_NONE, stopbits=2, mode=MODE_RTU)
    while True:
        pv, precision = tk4s.scan_pv()
        client.send_data(pv, precision)
