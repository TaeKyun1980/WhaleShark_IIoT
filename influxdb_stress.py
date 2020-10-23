import unittest
import time
from influxdb import DataFrameClient
from datetime import datetime
import datetime
from iiot_mqtt_agent import Agent
from iiot_server import TcpServer
from net_socket.iiot_tcp_async_server import AsyncServer


class influxdb_stress(unittest.TestCase):
    
    def system_con(self):
        self.server_ip = 'localhost'
        self.server_port = 1234
        server = TcpServer()
        server.init_config()
        self.mq_channel = server.get_mq_channel()
        self.redis_con = server.get_redis_con()
        self.async_svr = AsyncServer(self.redis_con)
        self.mqtt_agent = Agent()
        self.mqtt_agent.resource_config()
    
    def test_stress(self):
        self.system_con()
        influxdb_host = 'localhost'
        influxdb_port = 8086
        influxdb_id = 'krmim'
        influxdb_pwd = 'krmin_2017'
        influxdb_db = 'facility'
        influxdb_client = self.mqtt_agent.get_influxdb_mgr()
        influxdb_Dfclient = DataFrameClient('localhost', 8086, 'krmim', 'krmim_2017', 'stress')
        influxdb_Dfclient.query('CREATE DATABASE stress')
        influxdb_Dfclient.query('DROP SERIES FROM insert_test')
        influx_json = []
        print('generate data')
        for idx in range(0, 40000):
            influx_json.append({
                'measurement': 'insert_test',
                'fields': {'m0': time.time()}
            })
        print('write data')
        try:
            start_time = datetime.datetime.now()
            if influxdb_client.write_points(influx_json) is True:
                print('influx write success')
                end_time = datetime.datetime.now()
                delta = end_time - start_time
                print(delta)
                duringtime = int(delta.total_seconds() * 1000)  # milliseconds
                print(str(duringtime) + 'ms')
            else:
                print('influx write fail')
        except Exception as e:
            print(str(e.args))
        influxdb_client.close()


if __name__ == '__main__':
    unittest.main()
