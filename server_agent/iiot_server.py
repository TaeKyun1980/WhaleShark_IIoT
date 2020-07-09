import socket
import yaml
from queue import Queue
import threading

from net_socket.iiot_tcp_async_server import get_modbus_packet, modbus_mqtt_publish

if __name__ == '__main__':
    try:
        with open('../net_socket/config_server_develop.yaml', 'r') as file:
            config_obj = yaml.load(file, Loader=yaml.FullLoader)
            host = config_obj['iiot_server']['tcp_server']['ip_address']
            port = config_obj['iiot_server']['tcp_server']['port']
    except Exception as e:
        print(str(e))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setblocking(0)
        server_sock.bind((host, port))
        server_sock.listen(5)
        print("Server started...")
        service_socket_list = [server_sock]
        msg_size = 25
        msg_queue = Queue()
        socket_thread = threading.Thread(target=get_modbus_packet, args=(server_sock, service_socket_list, msg_size, msg_queue))
        mqtt_thread = threading.Thread(target=modbus_mqtt_publish, args=(msg_queue, ))
        socket_thread.start()
        mqtt_thread.start()
        socket_thread.join()
        mqtt_thread.join()
