import unittest

from instrument_driver.autonics.modbus_tk4s import autonics_pid_tk4s
from mqtt_agent.modbus_rabbitmq_agent import modbus_rabbitmq_agent


class mqtt_agent(unittest.TestCase):

    def setUp(self):
        # client = docker.from_env()
        #docker run -d --name rabbitmq -p 5672:5672 -p 8080:15672 --restart=unless-stopped -e RABBITMQ_DEFAULT_USER=add4sys -e RABBITMQ_DEFAULT_PASS=add4s rabbitmq:management
        # client.containers.run('alpine', 'echo hello world')
        pass

    #mqtt connection test
    def test_mqtt_connection(self):
        agent = modbus_rabbitmq_agent()
        connect_result =agent.connect_mqtt(virtual_host='tk1', queue_name='overtemp')
        self.assertEqual(True, connect_result, msg='mqtt ok')

    #tk4s pv scan test
    def test_instrument(self):
        tk4s = autonics_pid_tk4s(mode='emulation')
        pv, precision = tk4s.scan_pv()

        self.assertEqual(str(pv).isdigit(), True, msg='instrument pv ok')
        self.assertEqual(str(precision).isdigit(), True, msg='instrument precision ok')

if __name__ == '__main__':
    unittest.main()
