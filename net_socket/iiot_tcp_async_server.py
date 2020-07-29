import logging
import sys
import select
import math
import json
from datetime import datetime, timedelta
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class AsyncServer:
    def convert_hex2decimal(self, packet, readable_sock):
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
                modbus_dict = {'equipment_id': equipment_id, 'meta': {'ip': host,
                                                                    'port': port,
                                                                    'time': gmt_time,
                                                                    'sensor_cd': sensor_code,
                                                                    'fun_cd': function_code,
                                                                    'sensor_value': sensor_value,
                                                                    'precision': precision
                                                                    }}
    
                status = 'OK'
            else:
                status = 'ER'
        except Exception as e:
            print(str(e))
        logging.debug(status + str(packet))
        return status, str(packet), modbus_dict
    
    
    async def get_client(self, event_manger, server_sock, msg_size, msg_queue):
        """
        It create client socket with server sockt
        event_manger        It has asyncio event loop
        server_socket       Socket corresponding to the client socket
        msg_size            It means the packet size to be acquired at a time from the client socket.
        msg_queue           It means the queue containing the message transmitted from the gateway.
        """
        while True:
            client, _ = await event_manger.sock_accept(server_sock)
            event_manger.create_task(self.manage_client(event_manger,  client, msg_size, msg_queue))
    
    
    async def manage_client(self, event_manger, client, msg_size, msg_queue):
        """
            It receives modbus data from iiot gateway using client socket.
            event_manger        It has asyncio event loop
            client              It is a client socket that works with multiple iiot gateways.
            msg_size            It means the packet size to be acquired at a time from the client socket.
            msg_queue           It means the queue containing the message transmitted from the gateway.
            """
        while True:
            try:
                packet = (await event_manger.sock_recv(client, msg_size))
                packet = packet.decode('utf-8')
                if packet:
                    status, packet, modbus_udp = self.convert_hex2decimal(packet, client)
                    if status == 'OK':
                        msg_queue.put(modbus_udp)
                    acq_message = status + packet
                    client.sendall(acq_message.encode())
                else:
                    client.close()
    
            except Exception as e:
                logging.exception('manage client exception:' + str(e))
                client.close()
                break
        
                
    def apply_sensor_name(self, db_con, message):
        sensor_cd = message['meta']['sensor_cd']
        sensor_cd_json = json.loads(db_con.get('sensor_cd'))
        sensor_desc = sensor_cd_json[sensor_cd]
        message['meta']['sensor_cd'] = sensor_desc
        return message
    
    
    def modbus_mqtt_publish(self, msg_queue, redis_con, mq_channel, u_test=False):
       while True:
           if msg_queue.qsize() > 0:
            msg_json = msg_queue.get()
            if u_test == True:
                return msg_json
            else:
                pass
                # msg_json = apply_sensor_name(db_con=redis_con, message=msg_json)
                # routing_key = msg_json['equipment_id']
                # msg_json = json.dumps(msg_json)
                # mq_channel.basic_publish(exchange='', routing_key=routing_key, body=msg_json)



