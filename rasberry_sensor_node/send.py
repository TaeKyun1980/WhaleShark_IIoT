import pika
import yaml
from rasberry_sensor_node.sensors.mpu6050 import read_mp6050
from datetime import datetime

config_f = open("config_develop.yaml", 'r')
config_obj = yaml.load(config_f)

rabbitmq_server = config_obj['mqtt']['rabbitmq']['host']
rabbitmq_port = config_obj['mqtt']['rabbitmq']['port']
rabbitmq_id = config_obj['mqtt']['rabbitmq']['id']
rabbitmq_pwd = config_obj['mqtt']['rabbitmq']['pwd']

credentials = pika.PlainCredentials(rabbitmq_id, rabbitmq_pwd)
connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_server,rabbitmq_port, '/',  credentials))
channel = connection.channel()


# channel.queue_declare(queue='mp6050')
channel.queue_declare(queue='dht11')
import time
while True:
    now = datetime.now()
    dt_string=datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    try:
        gyro_xout, gyro_yout ,gyro_zout, accel_xout_scaled, accel_yout_scaled,accel_zout_scaled= read_mp6050()
        message='"mtime":"{m_time}","gyro_x":{gy_x},"gyro_y":{gy_y},"gyro_z":{gy_z},"acc_x":{acc_x},"acc_y":{acc_y},"acc_z":{acc_z}'.format(
                                                                                                        m_time=dt_string,
                                                                                                        gy_x=gyro_xout,
                                                                                                         gy_y=gyro_yout,
                                                                                                         gy_z=gyro_zout,
                                                                                                         acc_x=accel_xout_scaled,
                                                                                                         acc_y=accel_yout_scaled,
                                                                                                         acc_z=accel_zout_scaled)

        
        channel.basic_publish(exchange='',
                          routing_key='dht11',
                          body=message)
    except Exception as e:
        print(e)
    time.sleep(0.5)
connection.close()
