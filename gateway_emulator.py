import socket
import time

def make_packet(facility_id,sensor_code,pv):
    hd_fid1=str(facility_id[0:1])
    hd_fid2=str(facility_id[1:2])
    hd_fid3=chr(int(facility_id[2:4]))
    hd_fid4=chr(int(facility_id[4:6]))

    hd_sid1=chr(int(sensor_code[0:2]))
    hd_sid2=chr(int(sensor_code[2:4]))
    hex_pv=hex(pv)[2:].zfill(8)
    int_pv1=chr(int(hex_pv[0:2],16))
    int_pv2=chr(int(hex_pv[2:4],16))
    int_pv3=chr(int(hex_pv[4:6],16))
    int_pv4=chr(int(hex_pv[6:8],16))
    packet = '\x02\x00\x00\x00\x00'+hd_fid1+hd_fid2+hd_fid3+hd_fid4+hd_sid1+hd_sid2+str('P')+str('V')+int_pv1+int_pv2+int_pv3+int_pv4+'\x01\x03'
    return packet

HOST = '127.0.0.1'
PORT = 1233
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
#Sample packet (2, 0, 0, 0, 0, 84, 83, 0, 1, 0, 9, 80, 86, 0, 0, 1, 74, 1, 3)
#facility_id 설비명 / 설비 ID, sensor_code : 센서에 대한 설명(iiot_server의 facilities_dict 참조)ㄴ, pv : 현재 센서 값

packet = make_packet(facility_id='TS0001', sensor_code='000'+str(2), pv = 330)
print(packet)
client_socket.send(packet.encode())
time.sleep(1)
data = client_socket.recv(1024)
print('Received', repr(data.decode()))

packet = make_packet(facility_id='TS0002', sensor_code='000'+str(2), pv = 330)
print(packet)
client_socket.send(packet.encode())
time.sleep(1)
data = client_socket.recv(1024)
print('Received', repr(data.decode()))

packet = make_packet(facility_id='TS003', sensor_code='000'+str(2), pv = 330)
print(packet)
client_socket.send(packet.encode())
time.sleep(1)
data = client_socket.recv(1024)
print('Received', repr(data.decode()))

packet = make_packet(facility_id='TS008', sensor_code='000'+str(2), pv = 330)
print(packet)
client_socket.send(packet.encode())
time.sleep(1)
data = client_socket.recv(1024)
print('Received', repr(data.decode()))
client_socket.close()