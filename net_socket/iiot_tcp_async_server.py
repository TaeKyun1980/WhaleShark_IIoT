import asyncio
import logging
import sys
import select
import math
import json
import calendar
import time
from datetime import datetime, timedelta
import datetime

import pika

from net_socket.signal_killer import GracefulInterruptHandler

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class AsyncServer:

    def convert(self, list):
        return tuple(i for i in list)


    def convert_hex2decimal(self, packet_bytes, host,port):
        """
        In the packet, the hexadecimal value is converted to a decimal value, structured in json format, and returned.

        packet           TCP Stream packet from IIot Gateway
        readable_sock       client socket object

        packet specification
        stx is the starting code, the hex value matching STX in the ascii code table
        utc time is the time when the sensor value is received from the iiot gate
        equipment id means the id of the equipment and is predefined in the database.
        sensor code is means the sensor's type like as tempeatur, pressure, voltage,...
        decimal_point means the accuracy of sensor value, decimal point.
        The sensor value means the sensor value installed in the facility.
        """
        status = 'ER'
        modbus_dict = {'equipment_id': '', 'meta': {'ip': '',
                                                             'port': '',
                                                             'time':'' ,
                                                             'sensor_cd':'' ,
                                                             'fun_cd':'' ,
                                                             'sensor_value': '',
                                                             'decimal_point':''
                                                             }}
        try:
            byte_tuple = self.convert(list(packet_bytes))
            logging.debug('byte message'+str(byte_tuple))
            if byte_tuple[0] == 2 and (byte_tuple[16] == 3 or byte_tuple[18] == 3):
                group = chr(byte_tuple[5]) + chr(byte_tuple[6])
                group_code = int('0x{:02x}'.format(byte_tuple[7]) + '{:02x}'.format(byte_tuple[8]), 16)
                group_code = '{0:04d}'.format(group_code)
                sensor_code = int('0x{:02x}'.format(byte_tuple[9]) + '{:02x}'.format(byte_tuple[10]), 16)
                sensor_code = '{0:04d}'.format(sensor_code)
                fn=chr(byte_tuple[11]) +chr(byte_tuple[12])
                logging.debug('function name:'+ fn)

                logging.debug('**8Byte pressure:'+str(sensor_code))
                fv='0x{:02x}'.format(byte_tuple[13])+'{:02x}'.format(byte_tuple[14])+'{:02x}'.format(
	                byte_tuple[15])+'{:02x}'.format(byte_tuple[16])
                decimal_point=int('0x{:02x}'.format(byte_tuple[17]),16)
                
                fv = int(fv, 16)
                timestamp = datetime.datetime.utcnow()+ timedelta(hours=9)
                str_hex_utc_time = str(timestamp)[0:len('2020-08-15 21:04:58')]
                modbus_dict = {'equipment_id': group+group_code, 'meta': {'ip': host,
                                                                    'port': port,
                                                                    'time': str_hex_utc_time,
                                                                    'sensor_cd': sensor_code,
                                                                    'fun_cd': 'PV',
                                                                    'sensor_value': fv,
                                                                    'decimal_point': decimal_point
                                                                    }}

                status = 'OK'
            else:
                status = 'ER'
        except Exception as e:
            logging.exception(str(e))
        logging.debug(status + str(packet_bytes) + str(modbus_dict))
        return status, str(packet_bytes), modbus_dict


    async def get_client(self, event_manger, server_sock, msg_size,redis_con, mq_channel):
        """
        It create client socket with server sockt
        event_manger        It has asyncio event loop
        server_socket       Socket corresponding to the client socket
        msg_size            It means the packet size to be acquired at a time from the client socket.
        msg_queue           It means the queue containing the message transmitted from the gateway.
        """
        self.redis_con = redis_con
        with GracefulInterruptHandler() as h:
            client = None
            while True:
                if not h.interrupted:
                    client, _ = await event_manger.sock_accept(server_sock)
                    event_manger.create_task(self.manage_client(event_manger,client,msg_size,mq_channel))
                else:
                    client.close()
                    server_sock.close()
                    sys.exit(0)


    async def manage_client(self, event_manger, client, msg_size, mq_channel):
        """
            It receives modbus data from iiot gateway using client socket.
            event_manger        It has asyncio event loop
            client              It is a client socket that works with multiple iiot gateways.
            msg_size            It means the packet size to be acquired at a time from the client socket.
            msg_queue           It means the queue containing the message transmitted from the gateway.
        """
        facilities_dict = {}
        facilities_info = json.loads(self.redis_con.get('facilities_info').decode())
        equipment_keys = facilities_info.keys()
        for equipment_key in equipment_keys:
            facilities_dict[equipment_key]={}
            for sensor_id in  facilities_info[equipment_key].keys():
                sensor_desc = facilities_info[equipment_key][sensor_id]
                if sensor_desc not in facilities_dict[equipment_key].keys():
                    facilities_dict[equipment_key][sensor_desc]=0.0

        with GracefulInterruptHandler() as h:
            while True:
                if not h.interrupted:
                    try:
                        packet = (await event_manger.sock_recv(client, msg_size))
                    except Exception as e:
                        logging.exception('manage client exception:'+str(e))
                        client.close()
                        break

                    if packet:
                        try:
                            logging.debug('try convert')
                            host,port=client.getpeername()
                            status, packet, modbus_udp = self.convert_hex2decimal(packet, host,port)
                            if status == 'OK':
                                str_modbus_udp = str(modbus_udp)
                                logging.debug('Queue put:' + str_modbus_udp)
                                equipment_id = modbus_udp['equipment_id']
                                sensor_code = modbus_udp['meta']['sensor_cd']
                                redis_sensor_info = json.loads(self.redis_con.get('facilities_info'))
                                if equipment_id in redis_sensor_info.keys():
                                    sensor_desc = redis_sensor_info[equipment_id][sensor_code]
                                    routing_key = modbus_udp['equipment_id']
                                    facilities_dict[equipment_key]['time']=modbus_udp['meta']['time']
                                    pv = modbus_udp['meta']['sensor_value']
                                    decimal_point=modbus_udp['meta']['decimal_point']
                                    pv = float(pv) * math.pow(10, float(decimal_point))
                                    decimal_point=math.pow(10, float(decimal_point))
                                    modbus_udp['meta']['sensor_value'] = pv / decimal_point
                                    logging.debug('redis:'+'gateway_cvt set')
                                    self.redis_con.set('remote_log:modbus_udp', json.dumps(modbus_udp))

                                    facilities_dict[equipment_key][sensor_desc] = modbus_udp['meta']['sensor_value']
                                    logging.debug('mq exchange:facility')
                                    logging.debug('mq routing_key:'+routing_key)
                                    logging.debug('mq body:'+str(json.dumps(facilities_dict)))

                                    if mq_channel.is_open == True:
                                        logging.debug('mqtt open')
                                        mq_channel.basic_publish(exchange='facility',routing_key=routing_key,
                                                                 body=json.dumps(facilities_dict))

                                        self.redis_con.set('remote_log:mqttpubish',json.dumps(facilities_dict))
                                    else:
                                        logging.debug('mqtt closed')
                                        logging.debug('reconnecting to queue')
                                        mq_channel.connect()
                                        mq_channel.basic_publish(exchange='facility',routing_key=routing_key,
                                                                 body=json.dumps(facilities_dict))
                                else:
                                    acq_message = status + packet + 'no exist key\r\n'
                                    client.sendall(acq_message.encode())
                                    continue
                            acq_message = status + packet + '\r\n'
                            logging.debug('rtn:'+ acq_message)
                            client.sendall(acq_message.encode())
                        except Exception as e:
                            client.sendall(packet.encode())
                            logging.exception('message error:' + str(e))
                    else:
                        client.close()
                else:
                    client.close()
                    sys.exit(0)