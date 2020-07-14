import logging
import sys
import socket
import select
from queue import Queue
from datetime import datetime, timedelta
import math
import json
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def convert_hex2decimal(packet, readable_sock):
    """
    In the packet, the hexadecimal value is converted to a decimal value, structured in json format, and returned.
    
    packet           TCP Stream packet from IIot Gateway
    readable_sock       client socket object
    
    packet specification
    stx is the starting code, the hex value matching STX in the ascii code table
    utc time is the time when the sensor value is received from the iiot gate
    equipment id means the id of the equipment and is predefined in the database.
    sensor code is means the sensor's type like as tempeatur, pressure, voltage,...
    precision means the accuracy of sensor value, decimal point.
    The sensor value means the sensor value installed in the facility.
    """

    stx = packet[0:1]
    etx = packet[26:28]
    if stx == '2' and etx == '3':
        time_stamp = int(packet[1:9], 16)
        utc_time = datetime.utcfromtimestamp(time_stamp) + timedelta(hours=9)
        gmt_time = utc_time.strftime('%Y-%m-%d %H:%M:%S')
        equipment_id = packet[9:15]
        sensor_code = packet[15:19]
        function_code = packet[19:21]
        sensor_value = float(int(packet[21:25], 16))
        precision = float(packet[25:26])
        precision = math.pow(10, precision)
        sensor_value = sensor_value / precision
        etx = packet[26:28]
        host, port = readable_sock.getpeername()
        modbus_udp = {'equipment_id': equipment_id, 'meta': {'ip': host,
                                                            'port': port,
                                                            'time': gmt_time,
                                                            'sensor_cd': sensor_code,
                                                            'fun_cd': function_code,
                                                            'sensor_value': sensor_value,
                                                            'precision': precision
                                                            }}

        return modbus_udp


def get_modbus_packet(server_sock, service_socket_list, msg_size, msg_queue):
    """
    It receives modbus data from iiot gateway using client socket.
    
    server_sock          It is a server socket that works with multiple iiot gateways.
    service_socket_list  List of client sockets that have requested to connect to the server, including server sockets.
    msg_size             It means the packet size to be acquired at a time from the client socket.
    msg_queue            It means the queue containing the message transmitted from the gateway.
    """

    while service_socket_list:
       server_sock_desc = str(service_socket_list[0]).split()
       if 'closed' not in server_sock_desc[1]:
           readable, writable, exceptional = select.select(service_socket_list, [], [])
           for readable_sock in readable:
               if readable_sock is server_sock:
                   conn, address = readable_sock.accept()
                   service_socket_list.append(conn)
               else:
                   packet = readable_sock.recv(msg_size)
                   packet = packet.decode('utf-8')
                   if packet:
                       modbus_udp = convert_hex2decimal(packet, readable_sock)
                       msg_queue.put(modbus_udp)
                   else:
                       service_socket_list.remove(readable_sock)
                       readable_sock.close()


def apply_sensor_name(db_con, message):
    sensor_cd = message['meta']['sensor_cd']
    sensor_cd_json = json.loads(db_con.get('sensor_cd'))
    sensor_desc = sensor_cd_json[sensor_cd]
    message['meta']['sensor_cd'] = sensor_desc
    return message

def modbus_mqtt_publish(msg_queue, redis_con, mq_channel, u_test=False):
   while True:
       if msg_queue.qsize() > 0:
        msg_json = msg_queue.get()
        if u_test == True:
            return msg_json
        else:
            msg_json = apply_sensor_name(db_con=redis_con, message=msg_json)
            routing_key = msg_json['equipment_id']
            msg_json = json.dumps(msg_json)
            mq_channel.basic_publish(exchange='', routing_key=routing_key, body=msg_json)
            print(msg_json)


