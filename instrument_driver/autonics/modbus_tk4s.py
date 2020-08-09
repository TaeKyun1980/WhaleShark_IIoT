import minimalmodbus
import math
import yaml

class autonics_pid_tk4s:

    """
    init rs232 serial port
    """
    
    def __init__(self, port, station_id, baudrate, databits, parity, stopbits, mode):
        with open('config/autonics_map.yaml', 'r') as file:
            config_obj = yaml.load(file, Loader=yaml.FullLoader)
            self.pv_address = config_obj['controller']['tk4s']['pv']
            self.precision_address = config_obj['controller']['tk4s']['precision']
            
            self.instrument = minimalmodbus.Instrument(port, station_id, mode)
            self.instrument.serial.baudrate = baudrate
            self.instrument.serial.bytesize = databits
            self.instrument.serial.parity = parity
            self.instrument.serial.stopbits = stopbits
            self.instrument.serial.timeout = 1.5
            self.instrument.mode = mode
        
        
    def scan_pv(self):
        """
        get pv value of pid controller (model name : AUTONICS tk4s)
        """
    
        try:
            pv = self.instrument.read_register(self.pv_address, 0, functioncode=int('0x04', 16))
            precision = self.instrument.read_register(self.precision_address, 0, functioncode=int('0x04', 16))
            precision = math.pow(10, precision)
            pv = float(pv) / precision
            return pv, precision

        except Exception as e:
            print(e)


