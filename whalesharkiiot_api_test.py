import sys
import unittest
import json
from iiot_server import TcpServer
from net_socket.iiot_tcp_async_server import AsyncServer


class Tcp_server_test(unittest.TestCase):

    def setUp(self):
        self.server_ip = ''
        self.server_port = 0

        server = TcpServer()
        server.redis_con = server.config_equip_desc(address=server.redis_host, port=server.redis_port)
        if server.redis_con is None:
            sys.exit()
        self.redis_con=server.get_redis_con()
        self.asncy_server = AsyncServer()

        rtn=self.redis_con.get('remote_log:iit_server_boot')
        boot_status=json.loads(rtn)
        self.server_ip=boot_status['ip']
        self.server_port=boot_status['port']
        self.server_stats=boot_status['status']
        self.assertEqual(self.server_stats,1)

    def make_packet(self, facility_id, sensor_code, pv):
        hd_fid1=ord(facility_id[0:1])
        hd_fid2=ord(facility_id[1:2])
        hd_fid3=int(facility_id[2:4])
        hd_fid4=int(facility_id[4:6])
        hd_sid1=int(sensor_code[0:2])
        hd_sid2=int(sensor_code[2:4])
        hex_pv=hex(pv)[2:].zfill(8)
        int_pv1=int(hex_pv[0:2],16)
        int_pv2=int(hex_pv[2:4],16)
        int_pv3=int(hex_pv[4:6],16)
        int_pv4=int(hex_pv[6:8],16)
        return (2, 0, 0, 0, 0,hd_fid1, hd_fid2, hd_fid3, hd_fid4, hd_sid1, hd_sid2, ord('P'),ord('V'), int_pv1, int_pv2, int_pv3, int_pv4, 1, 3)

    def test_01_hex_conversion(self):
        # packet=(2, 0, 0, 0, 0, 84, 83, 0, 1, 0, 9, 80, 86, 0, 0, 1, 74, 1, 3)
        packet = self.make_packet(facility_id='TS0001', sensor_code='0009', pv = 330)
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