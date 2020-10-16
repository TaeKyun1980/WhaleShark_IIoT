import sys
import unittest
import json

import pika

from iiot_server import TcpServer
from net_socket.iiot_tcp_async_server import AsyncServer
from iiot_mqtt_agent import callback_mqreceive
from influxdb import DataFrameClient
import pandas


class Tcp_server_test(unittest.TestCase):
    
    def system_con(self):
        self.server_ip = 'localhost'
        self.server_port = 1234
        server = TcpServer()
        server.init_config()
        self.mq_channel = server.get_mq_channel()
        self.redis_con = server.get_redis_con()
        self.async_svr = AsyncServer()
        
    
    def setUp(self):
        self.mqtt_pub_json = None
        # rtn=self.redis_con.get('remote_log:iit_server_boot')
        # boot_status=json.loads(rtn)
        # self.server_ip=boot_status['ip']
        # self.server_port=boot_status['port']
        # self.server_stats=boot_status['status']
        # self.assertEqual(self.server_stats,1)

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
        self.system_con()
        # packet=(2, 0, 0, 0, 0, 84, 83, 0, 1, 0, 9, 80, 86, 0, 0, 1, 74, 1, 3)
        origian_msg = {'equipment_id': 'TS0001',
                       'meta': {'ip': 'localhost', 'port': 1234, 'time': '2020-09-30 13:51:13', 'sensor_cd': '0001',
                                'fun_cd': 'PV', 'sensor_value': 330, 'decimal_point': 1}}
        del origian_msg['meta']['time']
        packet = self.make_packet(facility_id='TS0001', sensor_code='0001', pv = 330)
        _, _, self.modbus_udp = self.async_svr.convert_hex2decimal(packet, self.server_ip, self.server_port)
        del self.modbus_udp['meta']['ms_time']
        
        is_equal= self.modbus_udp == origian_msg
        print(self.modbus_udp)
        
        self.assertEqual(True, is_equal)
        
    # def test_02_mqtt_publish(self):
    #     try:
    #         self.system_con()
    #         packet = self.make_packet(facility_id='TS0001', sensor_code='0001', pv=330)
    #         _, _, self.modbus_udp = self.async_svr.convert_hex2decimal(packet, self.server_ip, self.server_port)
    #         fac_daq = self.async_svr.get_fac_inf(self.redis_con)
    #         equipment_id = self.modbus_udp['equipment_id']
    #         redis_fac_info = json.loads(self.redis_con.get('facilities_info'))
    #         if equipment_id in redis_fac_info.keys():
    #             fac_msg = self.async_svr.config_fac_msg(equipment_id, fac_daq, self.modbus_udp, redis_fac_info)
    #             print(fac_msg)
    #             rtn_json = self.async_svr.publish_facility_msg(channel=self.mq_channel, exchange='facility', routing_key=equipment_id,
    #                                                            json_body=fac_msg)
    #             print(rtn_json)
    #             cmp = json.loads(fac_msg) == rtn_json
    #             self.mqtt_pub_json = rtn_json
    #             self.assertEqual(cmp, True)
    #     except Exception as e:
    #         print(str(e))
    #         self.assertEqual(0, 1)

    def callback(ch, method, properties, body):
        print("[x] %r" % (body,))
        
    def test_03_mqtt_pubscribe(self):
        credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
        param = pika.ConnectionParameters('localhost', 5672, '/', credentials)
        connection = pika.BlockingConnection(param)
        channel = connection.channel()
    
        channel.exchange_declare(exchange='logs', exchange_type='fanout')
    
        message = ' '.join(sys.argv[1:]) or "Logs..."
        channel.basic_publish(exchange='logs', routing_key='key', body=message)
        print("[x] Send %r" % (message,))
        connection.close()

        credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
        param = pika.ConnectionParameters('localhost', 5672, '/', credentials)
        connection = pika.BlockingConnection(param)
        channel = connection.channel()
        
        result = channel.queue_declare(queue='logs', exclusive=True)
        channel.queue_bind(exchange='logs', queue=result.method.queue)
        channel.basic_consume(on_message_callback=self.callback, queue=result.method.queue)

        print("[*] Waiting for logs. To exit press CTRL+C")
        channel.start_consuming()
    
        pass
if __name__ == '__main__':
    unittest.main()