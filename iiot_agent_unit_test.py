import math
import os
import subprocess
import sys
import time
import unittest
import socket
import json
from iiot_server import tcp_server
from net_socket.iiot_tcp_async_server import AsyncServer


class Tcp_server_test(unittest.TestCase):

    def memory_compare(self, packet_bytes, modbus_udp):
        host, port = self.client_socket.getsockname()
        info_tuple = self.AsyncServer.convert_hex2decimal(packet_bytes, host, port)
        packet_json = info_tuple[2]
        pv = float(packet_json['meta']['sensor_value'])
        precision = float(packet_json['meta']['precision'])
        precision = math.pow(10, precision)
        packet_json['meta']['sensor_value'] = pv/precision
        modbus_json = json.loads(modbus_udp)
        x1, x2 = json.dumps(packet_json, sort_keys = True), json.dumps(modbus_json, sort_keys = True)
        if x1 == x2:
            return True
        else:
            return False

    def setUp(self):
        self.server_ip = ''
        self.server_port = 0

        server=tcp_server()
        server.redis_con=server.config_equip_desc(address=server.redis_host,port=server.redis_port)
        if server.redis_con==None:
	        sys.exit()
        self.redis_con=server.get_redis_con()
        self.asncy_server = AsyncServer()

        rtn=self.redis_con.get('remote_log:iit_server_boot')
        boot_status=json.loads(rtn)
        self.server_ip=boot_status['ip']
        self.server_port=boot_status['port']
        self.server_stats=boot_status['status']
        self.assertEqual(self.server_stats,1)


    # def test_02_gateway_json(self):
    #     hex_stx= '{:02x}'.format(2)
    #     hex_timestamp= '{:02x}'.format(0) + '{:02x}'.format(0) + '{:02x}'.format(0) + '{:02x}'.format(0)
    #     equip_name = format(ord("T"), "x")+format(ord("S"), "x")
    #     equip_id =  '{:02x}'.format(0)+'{:02x}'.format(1)
    #     sensor_code = '{:02x}'.format(0)+'{:02x}'.format(7)
    #     function_code = format(ord("P"), "x")+format(ord("V"), "x")
    #     function_value = '{:08x}'.format(17)
    #     precision = '{:02x}'.format(1)
    #     etx = '{:02x}'.format(3)
    #     packet_sample= hex_stx+hex_timestamp+equip_name+equip_id+sensor_code+function_code + function_value+precision+etx
    #     packet_bytes= bytearray.fromhex(packet_sample)
    #     self.client_socket.send(packet_bytes)
    #     time.sleep(0.01)
    #     modbus_udp = self.redis_con.get('remote_log:modbus_udp')
    #     result = self.memory_compare(packet_bytes, modbus_udp)
    #     self.assertEqual(True, result)


    def test_02_hex_conversion(self):
        # function_value= (330).to_bytes(4, byteorder="big", signed=True)
        # test_pv = bytearray.fromhex(function_value)

        packet=(2, 0, 0, 0, 0, 84, 83, 0, 1, 0, 9, 80, 86, 0, 0, 1, 74, 1, 3)
        origian_msg = {'equipment_id': 'TS0001', 'meta': {'ip': 'localhost', 'port': 1234, 'time': '2020-09-30 13:51:13', 'sensor_cd': '0009', 'fun_cd': 'PV', 'sensor_value': 330, 'decimal_point': 1}}
        del origian_msg['meta']['time']
        hex_stx= '{:02x}'.format(packet[0])
        hex_timestamp= '{:02x}'.format(packet[1]) + '{:02x}'.format(packet[2]) + '{:02x}'.format(packet[3]) + '{:02x}'.format(packet[4])
        equip_name = format(ord("T"), "x")+format(ord("S"), "x")
        equip_id =  '{:02x}'.format(packet[7])+'{:02x}'.format(packet[8])
        sensor_code = '{:02x}'.format(packet[9])+'{:02x}'.format(packet[10])
        function_code = format(ord("P"), "x")+format(ord("V"), "x")
        function_value = '{:02x}'.format(packet[13])+'{:02x}'.format(packet[14])+'{:02x}'.format(
	                packet[15])+'{:02x}'.format(packet[16])
        precision = '{:02x}'.format(packet[17])
        etx = '{:02x}'.format(packet[18])
        packet_sample= hex_stx+hex_timestamp+equip_name+equip_id+sensor_code+function_code + function_value+precision+etx
        packet_bytes= bytearray.fromhex(packet_sample)
        _, _, modbus_dict = self.asncy_server.convert_hex2decimal(packet_bytes, self.server_ip, self.server_port)
        del modbus_dict['meta']['time']
        is_equal=modbus_dict == origian_msg
        print(modbus_dict)
        self.assertEqual(True, is_equal)

if __name__ == '__main__':
    unittest.main()
