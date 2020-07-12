import socket
from datetime import datetime
from time import gmtime, strftime
import datetime
import calendar
import time

client_socket = socket.socket()
host = 'localhost'
port = 9999


class sock_client:

    def __init__(self):

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Waiting for connection')
        self.client_socket.connect((host, port))

    def send_data(self):
        try:
                d = datetime.datetime.utcnow()
                unixtime = calendar.timegm(d.utctimetuple())
                
                str_hex_utc_time = str(hex(unixtime)).replace('0x', '').encode()
                
                stx = str.encode('{:1x}'.format(2))
                equipment_id = str.encode('TK{:02x}'.format(1))
                function_code = str.encode('PV')

                sensor_code = str.encode('{:04x}'.format(1))##sensor code 0001 (전압)
                sensor_value = str.encode('{:04x}'.format(2200)) #측정 값에 10 ^ 소수점 자리수를 적용한 값
                precision = str.encode('{:01x}'.format(1)) ## 소수점 자리수

                etx = str.encode('{:1x}'.format(3))
                modbus_packet = stx + str_hex_utc_time + equipment_id + sensor_code + function_code + sensor_value + precision + etx
                print(unixtime, str_hex_utc_time, modbus_packet, len(modbus_packet))
                try:
                    self.client_socket.send(modbus_packet)
                    time.sleep(0.5)
                except socket.error as e:
                    print(str(e))
                    self.client_socket.close()

        except socket.error as e:
            print(str(e))
            self.client_socket.close()

if __name__ == '__main__':
    client_list = []
    for idx in range(0, 10):
        client = sock_client()
        client_list.append(client)
    while True:
        for client in client_list:
            client.send_data()
