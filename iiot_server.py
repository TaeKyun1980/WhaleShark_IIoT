import asyncio
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

from net_socket.iiot_tcp_async_server import  AsyncServer

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

"""
grafana docker
docker run -d -p 3000:3000 grafana/grafana

influxdb
step1 : docker pull influxdb
step2 :
docker run -p 8086:8086 -v /Users/prismdata/Documents/1.Data_Centric/3.1.nipa_git/WhaleShark_IIoT/config:/var/lib/influxdb influxdb -config /var/lib/influxdb/influxdb.conf -e INFLUXDB_ADMIN_USER=whaleshark -e INFLUXDB_ADMIN_PASSWORD=whaleshark
Please refer https://www.open-plant.com/knowledge-base/how-to-install-influxdb-docker-for-windows-10/

"""

def connect_redis(host, port):
    """
    get connector for redis
    If you don't have redis, you can use docker.
    docker network create redis-net
    docker run --name whaleshark-redis -p 6379:6379 --network redis-net -d redis:alpine redis-server

    :param host: redis access host ip
    :param port: redis access port
    :return: redis connector
    """
    redis_obj = None
    try:
        conn_params = {
        "host":host,
        "port": port,
        }
        redis_obj = redis.StrictRedis(**conn_params)

    except Exception as e:
        logging.error(str(e))

    return redis_obj


def config_equip_desc(address, port):
    '''
    Configure redis for equipment sensor desc(sensor_cd)
    key : const sensor_cd
    value : dictionary or map has sensor_cd:sensor description
    :return: redis connector
    '''
    redis_con = None
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

    except Exception as e:
        logging.error(str(e))

    return redis_con


def get_messagequeue(address, port):
    '''
    If you don't have rabbitmq, you can use docker.
    docker run -d --hostname whaleshark --name whaleshark-rabbit -p 5672:5672 -p 8080:15672 -e RABBITMQ_DEFAULT_USER=whaleshark -e RABBITMQ_DEFAULT_PASS=whaleshark rabbitmq:3-management

    get message queue connector (rabbit mq) with address, port
    :param address: rabbit mq server ip
    :param port: rabbitmq server port(AMQP)
    :return: rabbitmq connection channel
    '''
    channel = None
    try:
        credentials = pika.PlainCredentials('whaleshark', 'whaleshark')
        param = pika.ConnectionParameters(address,port, '/',credentials )
        connection = pika.BlockingConnection(param)
        channel = connection.channel()

    except Exception as e:
        logging.exception(str(e))

    return channel

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

        redis_con = config_equip_desc(address=redis_host, port=redis_port)
        if redis_con == None:
            logging.error('redis configuration fail')
            sys.exit()

        mq_channel = get_messagequeue(address=rabbitmq_host, port=rabbitmq_port)
        if mq_channel == None:
            logging.error('rabbitmq configuration fail')
            sys.exit()
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setblocking(0)
        server_sock.bind(('', tcp_port))
        server_sock.listen(1)
        
        print('IIoT Client Ready ({ip}:{port})'.format(ip=tcp_host, port=tcp_port))
        msg_size = 27
        msg_queue = Queue()

        async_server = AsyncServer()
        event_manger = asyncio.get_event_loop()
        event_manger.run_until_complete(async_server.get_client(event_manger, server_sock, msg_size, msg_queue))
        
        mqtt_thread = threading.Thread(target=async_server.modbus_mqtt_publish, args=(msg_queue,redis_con,mq_channel))
        mqtt_thread.start()
        mqtt_thread.join()
       
    except Exception as e:
        print(str(e))

    
