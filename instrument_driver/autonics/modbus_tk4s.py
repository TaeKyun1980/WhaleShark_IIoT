import minimalmodbus
import math
import yaml

class autonics_pid_tk4s:
	"""
	init rs232 serial port
	"""
	def __init__(self):
		with open('instrument_driver/autonics/config/autonics_map.yaml', 'r') as file:
			config_obj = yaml.load(file, Loader=yaml.FullLoader)
			self.pv_address = config_obj['controller']['tk4s']['pv']
			self.precision_address = config_obj['controller']['tk4s']['precision']


	def connect_tk4s(self,com_param):
		self.instrument=minimalmodbus.Instrument(com_param['port'],com_param['station_id'],com_param['mode'])
		self.instrument.serial.baudrate=com_param['baudrate']
		self.instrument.serial.bytesize=com_param['databits']
		self.instrument.serial.parity=com_param['parity']
		self.instrument.serial.stopbits=com_param['stopbits']
		self.instrument.serial.timeout=com_param['timeout']
		self.instrument.mode=com_param['mode']

	def scan_pv(self):
		"""
		get pv value of pid controller (model name : AUTONICS tk4s)
		"""
		try:
			pv = self.instrument.read_register(self.pv_address, 0, functioncode=int('0x04', 16))
			precision = self.instrument.read_register(self.precision_address, 0, functioncode=int('0x04', 16))
			if precision > 0:
				pv = float(pv) * math.pow(10, precision)
			return pv, precision

		except Exception as e:
			print(e)


