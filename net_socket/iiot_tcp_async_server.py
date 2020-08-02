import logging
import sys
import select
import math
import json
import calendar

from datetime import datetime
import datetime
from net_socket.signal_killer import GracefulInterruptHandler

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class AsyncServer:
    
    def convert(self, list):
        return tuple(i for i in list)
    
    
    def convert_hex2decimal(self, packet_bytes, readable_sock):
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
        status = 'ER'
        modbus_dict = {'equipment_id': '', 'meta': {'ip': '',
                                                             'port': '',
                                                             'time':'' ,
                                                             'sensor_cd':'' ,
                                                             'fun_cd':'' ,
                                                             'sensor_value': '',
                                                             'precision':''
                                                             }}
        try:
            byte_tuple = self.convert(list(packet_bytes))
            print(byte_tuple)
            if byte_tuple[0] == 2 and byte_tuple[16] == 3:
                group = chr(byte_tuple[5]) + chr(byte_tuple[6])
                group_code = int('0x{:02x}'.format(byte_tuple[7]) + '{:02x}'.format(byte_tuple[8]), 16)
                group_code = '{0:04d}'.format(group_code)
    
                sensor_code = int('0x{:02x}'.format(byte_tuple[9]) + '{:02x}'.format(byte_tuple[10]), 16)
                sensor_code = '{0:04d}'.format(sensor_code)
    
                pv = '0x{:02x}'.format(byte_tuple[13]) + '{:02x}'.format(byte_tuple[14])
                sensor_value = int(pv, 16)
                precision = int('0x{:02x}'.format(byte_tuple[15]), 16)
                
                d = datetime.datetime.utcnow()
                unixtime = calendar.timegm(d.utctimetuple())
                str_hex_utc_time = str(hex(unixtime)).replace('0x', '').encode()
                
                host, port = readable_sock.getpeername()
                modbus_dict = {'equipment_id': group+group_code, 'meta': {'ip': host,
                                                                    'port': port,
                                                                    'time': str_hex_utc_time,
                                                                    'sensor_cd': sensor_code,
                                                                    'fun_cd': 'PV',
                                                                    'sensor_value': sensor_value,
                                                                    'precision': precision
                                                                    }}
    
                status = 'OK'
            else:
                status = 'ER'
        except Exception as e:
            logging.exception(str(e))
        logging.debug(status + str(packet_bytes) + str(modbus_dict))
        return status, str(packet_bytes), modbus_dict
    
    
    async def get_client(self, event_manger, server_sock, msg_size, msg_queue):
        """
        It create client socket with server sockt
        event_manger        It has asyncio event loop
        server_socket       Socket corresponding to the client socket
        msg_size            It means the packet size to be acquired at a time from the client socket.
        msg_queue           It means the queue containing the message transmitted from the gateway.
        """
        with GracefulInterruptHandler() as h:
            while True:
                if not h.interrupted:
                    client, _ = await event_manger.sock_accept(server_sock)
                    event_manger.create_task(self.manage_client(event_manger,  client, msg_size, msg_queue))
                else:
                    client.close()
                    server_sock.close()
                    sys.exit(0)
    
    
    async def manage_client(self, event_manger, client, msg_size, msg_queue):
        """
            It receives modbus data from iiot gateway using client socket.
            event_manger        It has asyncio event loop
            client              It is a client socket that works with multiple iiot gateways.
            msg_size            It means the packet size to be acquired at a time from the client socket.
            msg_queue           It means the queue containing the message transmitted from the gateway.
            """
        with GracefulInterruptHandler() as h:
            while True:
                if not h.interrupted:
                    try:
                        packet = (await event_manger.sock_recv(client, msg_size))
                        if packet:
                            try:
                                logging.debug('try convert')
                                status, packet, modbus_udp = self.convert_hex2decimal(packet, client)
                                if status == 'OK':
                                    logging.debug('Queue put', str(modbus_udp))
                                    msg_queue.put(modbus_udp)
                                acq_message = status + packet + '\r\n'
                                client.sendall(acq_message.encode())
                            except Exception as e:
                                client.sendall(packet.encode())
                                logging.exception('message error:' + str(e))
                        else:
                            client.close()
            
                    except Exception as e:
                        logging.exception('manage client exception:' + str(e))
                        client.close()
                        break
                else:
                    client.close()
                    sys.exit(0)
                

    def apply_sensor_name(self, db_con, message):
        sensor_cd = message['meta']['facilities_info']
        sensor_cd_json = json.loads(db_con.get('facilities_info'))
        sensor_desc = sensor_cd_json[sensor_cd]
        message['meta']['facilities_info'] = sensor_desc
        return message
    
    
    def modbus_mqtt_publish(self, msg_queue, redis_con, mq_channel, u_test=False):
       while True:
           if msg_queue.qsize() > 0:
            if u_test == True:
                print('Test Mode')
            msg_json = msg_queue.get()
            if u_test == True:
                return msg_json
            else:
                logging.debug('mqtt publish', msg_json)
                msg_json = self.apply_sensor_name(db_con=redis_con, message=msg_json)
                
                routing_key = msg_json['facilities_info']
                msg_json = json.dumps(msg_json)
                logging.debug('facilities_info', routing_key)
                mq_channel.basic_publish(exchange='', routing_key=routing_key, body=msg_json)



