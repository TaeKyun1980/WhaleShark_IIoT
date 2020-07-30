import minimalmodbus
import math

class autonics_pid_tk4s:

    """
    init rs232 serial port
    """

    
    def __init__(self, port, station_id, baudrate, databits, parity, stopbits, mode):
        self.instrument = minimalmodbus.Instrument(port, station_id,
                                                       mode)  # port name, slave address (in decimal), type
        self.instrument.serial.baudrate = baudrate
        self.instrument.serial.bytesize = databits
        self.instrument.serial.parity = parity
        self.instrument.serial.stopbits = stopbits
        self.instrument.serial.timeout = 1.5
        self.instrument.mode = mode

        
    def scan_pv(self, mem_address, mem_precision):
        """
        get pv value of pid controller (model name : AUTONICS tk4s)
        """
    
        try:
            pv_address = mem_address
            prevision_address = mem_precision
            pv = self.instrument.read_register(pv_address, 0, functioncode=int('0x04', 16))
            precision = self.instrument.read_register(prevision_address, 0, functioncode=int('0x04', 16))
            precision = math.pow(10, precision)
            pv = float(pv) / precision
            return pv, precision

        except Exception as e:
            print(e)


