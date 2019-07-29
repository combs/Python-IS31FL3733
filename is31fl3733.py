from __future__ import print_function

from constants import *
from smbus2 import SMBus, i2c_msg
import time


class IS31FL3733(object):

    address = 0x50
    busnum = 1
    syncmode = REGISTER_FUNCTION_CONFIGURATION_SYNC_CLOCK_SINGLE
    breathing = 0
    softwareshutdown = 0
    currentPage = PAGE_LED_ON_OFF
    pixels = [[0] * 16 for i in range(12)]
    triggerOpenShortDetection = 1

    def __del__(self):
        # self.smbus.close()
        pass

    def __init__(self, *args, **kwargs):

        # Flags

        if type (args) is not None:
          for arg in args:
              setattr(self,arg,True)

        # key=value parameters

        if type (kwargs) is not None:
          for key, value in kwargs.iteritems():
              if type(value) is dict:
                  if getattr(self,key):
                        tempdict = getattr(self,key).copy()
                        tempdict.update(value)
                        value = tempdict
              setattr(self,key,value)

        self.smbus = SMBus(self.busnum)
        self.reset()
        self.setContrast(255)
        self.triggerOpenShortDetection = 1
        self.setConfiguration()

    def selectPage(self,value):
        if self.currentPage is not value:
            print("changing page to",value,"from",self.currentPage)
            self.write(REGISTER_COMMAND_WRITE_LOCK,COMMAND_WRITE_LOCK_DISABLE_ONCE)
            self.write(REGISTER_COMMAND,value)
            self.currentPage = value

    def setContrast(self,value):
        self.selectPage(PAGE_FUNCTION)
        self.write(REGISTER_FUNCTION_CURRENT_CONTROL,value)

    def reset(self):
        self.selectPage(PAGE_FUNCTION)
        self.currentPage = PAGE_LED_ON_OFF
        print("reset got",self.read(REGISTER_FUNCTION_RESET))

    def enableAllPixels(self):
        self.selectPage(PAGE_LED_ON_OFF)
        self.writeBlock(0, [ 255 ] * 0x18 )
        self.selectPage(PAGE_LED_PWM)
        for i in range(0,12):
            self.writeBlock(i*16,[ 255 ] * (16))

    def setPixelPower(self,row,col,val):
        address = row*2 + (col > 7)
# This needs work


    def setPixelPWM(self,row,col,val,immediate=True):
        pixel = row*16 + col
        self.pixels[row][col] = val
        # print(row*16,col,"=",row*16 + col)
        if immediate:
            self.selectPage(PAGE_LED_PWM)
            self.write(pixel,val)

    def setAllPixelsPWM(self,values):
        # print("length is",len(values))
        self.selectPage(PAGE_LED_PWM)

        # messageAddress = i2c_msg.write(self.address, [0])
        # messageToSend = i2c_msg.write(self.address, values)
        # self.smbus.i2c_rdwr(messageAddress,messageToSend)

        # TODO set the values in the array

        iter = 0
        messages = []

        for chunk in self.chunks(values,32):
            # self.writeBlock(iter*32,chunk)
            # dest = [iter * 32, *chunk]
            chunk.insert(0, iter * 32)
            messages.append(i2c_msg.write(self.address, chunk))
            # messages.append(i2c_msg.write(self.address, chunk))
            iter += 1

        self.smbus.i2c_rdwr(*messages)


    def setAllPixels(self,values):
        print("length is",len(values))
        self.selectPage(PAGE_LED_ON_OFF)
        self.writeBlock(0,values)

    def setConfiguration(self):
        self.selectPage(PAGE_FUNCTION)
        regvalue = ( self.breathing * REGISTER_FUNCTION_CONFIGURATION_BREATHING_ENABLE ) | ( self.syncmode ) | ( ( not self.softwareshutdown ) * REGISTER_FUNCTION_CONFIGURATION_SOFTWARE_SHUTDOWN ) | ( self.triggerOpenShortDetection * REGISTER_FUNCTION_CONFIGURATION_TRIGGER_OPEN_SHORT_DETECTION )
        self.triggerOpenShortDetection = False
        self.write(REGISTER_FUNCTION_CONFIGURATION, regvalue)

    def write(self,register,value):
        self.smbus.write_byte_data(self.address,register,value)

    def writeBlock(self,register,value):
        self.smbus.write_i2c_block_data(self.address,register,value)

    def read(self,register):
        return self.smbus.read_byte_data(self.address,register)

    def getOpenPixels(self):
        self.selectPage(PAGE_LED_ON_OFF)
        for i in range(0x18,0x2e):
            print(self.read(i))

    def getShortPixels(self):
        self.selectPage(PAGE_LED_ON_OFF)
        for i in range(0x30,0x47):
            print(self.read(i))

    def chunks(self, values, length):
        for i in range(0, len(values), length):
            yield values[i:i + length]

    def writeBuffer(self):
        flat_list = [item for sublist in self.pixels for item in sublist]
        self.setAllPixelsPWM(0,flat_list)

    def sevenSegment(self, row, col, value, brightness=0):
        if brightness:
            self.selectPage(PAGE_LED_PWM)
            self.writeBlock(0,[brightness]*8)
        self.selectPage(PAGE_LED_ON_OFF)
        bits = 0B00000000
        if value == 0:
            bits = 0B00111111
        elif value == 1:
            bits = 0B00000110
        elif value == 2:
            bits = 0B01011011
        elif value == 3:
            bits = 0B01001111
        elif value == 4:
            bits = 0B01100110
        elif value == 5:
            bits = 0B01101101
        elif value == 6:
            bits = 0B01111101
        elif value == 7:
            bits = 0B00000111
        elif value == 8:
            bits = 0B01111111
        elif value == 9:
            bits = 0B01101111
        print(value)
        print(str(bits))
        # bits = 0b11111111 - bits
        self.write(row*2 + col,bits)


if __name__ == '__main__':
    for address in range(0x55,0x60):
        print("trying",address)
        try:
            matrix = IS31FL3733(address=address)
            matrix.enableAllPixels()
            time.sleep(2)
            matrix.setAllPixelsPWM([0]*192)
            # for value in range(8):
            #     matrix.setPixelPWM(0,value,64)
            #     time.sleep(1)
            #
            # time.sleep(2)

            for value in range(10):
                matrix.sevenSegment(0,0,value)
                time.sleep(1)

            time.sleep(2)

            for value in range(10):
                # iter = 1

                matrix.setAllPixelsPWM([value]*192)
                #
                # for row in range(12):
                #     for col in range(16):
                #         matrix.setPixelPWM(row,col, value)
                #         iter += 1

            for row in range(12):
                for col in range(16):
                    matrix.setPixelPWM(row,col, 2)

            for i in range(11):
                matrix.setPixelPWM(i,i,40)
            for i in range(11):
                matrix.setPixelPWM(11-i,i,20)
            matrix.setPixelPWM(0,0,100)
            matrix.setPixelPWM(0,5,100)
            matrix.setPixelPWM(1,6,100)
            matrix.setPixelPWM(0,10,100)
            matrix.setPixelPWM(11,11,100)
            matrix.setPixelPWM(11,11,100)
            matrix.setPixelPWM(6,11,100)

            # matrix.setPixelPWM(3,12,3)
            time.sleep(1);
            print("missing pixels")
            matrix.getOpenPixels()
            print("short pixels")
            matrix.getShortPixels()
        except Exception as e:
            print("Address",address,"error:",e)
            time.sleep(0.1)
