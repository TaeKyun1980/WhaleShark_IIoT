import codecs
import socket
import struct
from datetime import datetime
from time import gmtime, strftime
import datetime
import calendar
import time
import minimalmodbus
import yaml

from instrument_driver.autonics.instrument_bridge import instruments

client_socket = socket.socket()
host = 'localhost'
port = 1233

class sock_client:

	def __init__(self):
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_socket.connect((host, port))
		pass

	def send_data(self,pv, precision):
		try:
			hex_stx='{:02x}'.format(2)
			timestamp=datetime.datetime.now()
			unixtime=calendar.timegm(timestamp.utctimetuple())
			str_hex_unixtime=str(hex(unixtime)).replace('0x','')
			full_message=bytearray.fromhex(hex_stx)
			full_message+=bytearray.fromhex('{:02x}'.format(0))
			full_message+=bytearray.fromhex('{:02x}'.format(0))
			full_message+=bytearray.fromhex('{:02x}'.format(0))
			full_message+=bytearray.fromhex('{:02x}'.format(0))
			equip_name=format(ord("T"),"x")+format(ord("S"),"x")
			full_message+=bytearray.fromhex(equip_name)
			equip_id='{:02x}'.format(0)+'{:02x}'.format(1)
			full_message+=bytearray.fromhex(equip_id)
			sensor_code='{:02x}'.format(0)+'{:02x}'.format(9)
			full_message+=bytearray.fromhex(sensor_code)
			function_code=format(ord("P"),"x")+format(ord("V"),"x")
			full_message+=bytearray.fromhex(function_code)
			function_value='{:04x}'.format(pv)
			full_message+=bytearray.fromhex(function_value)
			precision='{:02x}'.format(precision)
			full_message+=bytearray.fromhex(precision)
			hex_etx='{:02x}'.format(3)
			full_message+=bytearray.fromhex(hex_etx)
			print(full_message, len(full_message))
			self.client_socket.send(full_message)
			recv = self.client_socket.recv(1024)
			print("data is ",recv)
			time.sleep(0.5)

		except socket.error as e:
			print(str(e))
			self.client_socket.close()


if __name__ == '__main__':
	slaves_desc={}
	with open('instrument_driver/config/instrument_desc.yaml','r') as file:
		instrument_config=yaml.load(file,Loader=yaml.FullLoader)
		for slave in instrument_config['slaves']:
			slaves_desc[slave]=instrument_config[slave]

	slave_list=[]
	for slave_desc in slaves_desc.keys():
		instrument=instruments()
		print(slaves_desc[slave_desc])
		print(slaves_desc[slave_desc]['vendor'])
		print(slaves_desc[slave_desc]['model_name'])
		print(slaves_desc[slave_desc]['stationid'])
		instrument.connect(slaves_desc[slave_desc])
		slave_list.append(instrument)

	tcp_server=sock_client()
	while True:
		for slave_instrument in slave_list:
			pv, precision = slave_instrument.scan_pv()
			tcp_server.send_data(pv, precision)