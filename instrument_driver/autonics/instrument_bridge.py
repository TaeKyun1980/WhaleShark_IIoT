import minimalmodbus
import math
import yaml

class instruments:

	def __init__(self):
		pass


	def connect(self,slave_desc):
		self.instrument=minimalmodbus.Instrument(slave_desc['port'],
		                                         slave_desc['stationid'],
		                                         slave_desc['mode'])
		self.instrument.serial.baudrate=slave_desc['baudrate']
		self.instrument.serial.bytesize=slave_desc['databits']
		self.instrument.serial.parity=slave_desc['parity']
		self.instrument.serial.stopbits=slave_desc['stopbits']
		self.instrument.serial.timeout=slave_desc['timeout']
		self.instrument.mode=slave_desc['mode']

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


