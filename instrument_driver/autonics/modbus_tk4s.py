import minimalmodbus
import math

class autonics_pid_tk4s:

    """
    init rs232 serial port
    """

    
    def __init__(self):
        self.instrument = minimalmodbus.Instrument('COM3', 1,
                                                       minimalmodbus.MODE_RTU)  # port name, slave address (in decimal), type
        self.instrument.serial.baudrate = 19200
        self.instrument.serial.bytesize = 8
        self.instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        self.instrument.serial.stopbits = 2
        self.instrument.serial.timeout = 1.5
        self.instrument.debug = True
        self.instrument.mode = minimalmodbus.MODE_RTU

        
    def scan_pv(self):
        """
        get pv value of pid controller (model name : AUTONICS tk4s)
        """
    
        try:
            pv_address = 1000
            prevision_address = 1001
            print('pv_address:', pv_address,'prevision_address:', prevision_address)
            pv = self.instrument.read_register(pv_address, 0, functioncode=int('0x04', 16))
            precision = self.instrument.read_register(prevision_address, 0, functioncode=int('0x04', 16))
            precision = math.pow(10, precision)
            pv = float(pv) / precision
            return pv, precision

        except Exception as e:
            print(e)


