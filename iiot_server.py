import socket
import logging
import redis
import yaml
from queue import Queue
import threading
import sys
import os
import json
import pika

from net_socket.iiot_tcp_async_server import get_modbus_packet, modbus_mqtt_publish
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def connect_redis(host, port):
    try:
        conn_params = {
        "host":host,
        "port": port,
        }
        redis_obj = redis.StrictRedis(**conn_params)
        return redis_obj
    except Exception as e:
        print(str(e))


def config_equip_desc(address, port):
    '''
    configure redis for equipment sensor desc(sensor_cd)
    key : const sensor_cd
    value : dictionary or map has sensor_cd:sensor description
    :return: None
    '''
    try:
        redis_con = connect_redis(address, port)
        sensor_cd_json = redis_con.get('sensor_cd')

        if sensor_cd_json == None:
            sensor_cd_dict = {'0001':'Power#1 Volt',
                              '0002':'Power#1 Amp'
                              }
            sensor_cd_json = json.dumps(sensor_cd_dict)

            redis_con.set('sensor_cd', sensor_cd_json)
            sensor_cd_json = json.loads(redis_con.get('sensor_cd'))

            print(sensor_cd_json)
        return redis_con

    except Exception as e:
        print(str(e))


def get_messagequeue(address, port):
    '''
    rabbitmq docker container install
    docker run -d --hostname whaleshark --name whaleshark-rabbit -p 5672:5672 -p 8080:15672 -e RABBITMQ_DEFAULT_USER=whaleshark -e RABBITMQ_DEFAULT_PASS=whaleshark rabbitmq:3-management

    get message queue connector (rabbit mq) with address, port
    :param address: rabbit mq server ip
    :param port: rabbitmq server port(AMQP)
    :return: rabbitmq connection channel
    '''
    try:
        credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
        param = pika.ConnectionParameters(address,port, '/',credentials )
        connection = pika.BlockingConnection(param)
        channel = connection.channel()
        return channel

    except Exception as e:
        print(str(e))

if __name__ == '__main__':


    try:
        with open('config/config_server_develop.yaml', 'r') as file:
            config_obj = yaml.load(file, Loader=yaml.FullLoader)
            tcp_host = config_obj['iiot_server']['tcp_server']['ip_address']
            tcp_port = config_obj['iiot_server']['tcp_server']['port']

            redis_host = config_obj['iiot_server']['redis_server']['ip_address']
            redis_port = config_obj['iiot_server']['redis_server']['port']

            rabbitmq_host = config_obj['iiot_server']['rabbit_mq']['ip_address']
            rabbitmq_port = config_obj['iiot_server']['rabbit_mq']['port']

        # redis_con = config_equip_desc(address=redis_host, port=redis_port)
        redis_con = None
        # mq_channel = get_messagequeue(address=rabbitmq_host, port=rabbitmq_port)
        mq_channel = None
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setblocking(0)
        server_sock.bind((tcp_host, tcp_port))
        server_sock.listen(5)
        print('IIoT Client Ready ({ip}:{port})'.format(ip=tcp_host, port=tcp_port))

        service_socket_list = [server_sock]
        msg_size = 27
        msg_queue = Queue()
        socket_thread = threading.Thread(target=get_modbus_packet,
                                         args=(server_sock, service_socket_list, msg_size, msg_queue))
        mqtt_thread = threading.Thread(target=modbus_mqtt_publish, args=(msg_queue,redis_con,mq_channel))
        socket_thread.start()
        mqtt_thread.start()
        socket_thread.join()
        mqtt_thread.join()

    except Exception as e:
        print(str(e))

    
