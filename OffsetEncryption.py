#very simple encryption algorithm that takes a bytestream and offsets the bytes by n-bits
#n-bit offset is key % block_size. Where both are integers

# This should take a bytestream and encrypt it by offsetting bytes by n-bits
class OffsetEncrypt(object):
    #Function to encrypt and decrypt a bytestream by offsetting bytes by n-bits
    block_size = 8
    key = b""
    byte_stream = bytearray()
    debug = False #debug/verbose mode
    def __init__(self,byte_stream=None,key=None,debug = False):
        self.debug = debug
        self.key = key
        self.byte_stream = byte_stream
        self.offset = key % self.block_size # just a fixed offset for now. but can modify to vary this

    def __offset__(self):
        offset = self.key % self.block_size
    offset = staticmethod(__offset__)


    def encrypt(self, byte_stream = None, key = None):
        #priorize the passed in values, but if they are empty, use the class values
        byte_stream = byte_stream or self.byte_stream
        key = key or self.key

        for i in range(len(byte_stream)):
            if self.debug:
                print(byte_stream[i])
                print("\n")
            byte = byte_stream[i]
            byte_stream[i] = ((byte_stream[i] << self.offset) & 0xFF) | (byte_stream[i] >> (self.block_size - self.offset))
            if self.debug: print(byte_stream[i])
        return byte_stream

    def decrypt(self, byte_stream=None, key=None):
        #priorize the passed in values, but if they are empty, use the class values
        byte_stream = byte_stream or self.byte_stream
        key = key or self.key

        for i in range(len(byte_stream)):
            if self.debug:
                print(byte_stream[i])
                print("\n")

            byte_stream[i] = ((byte_stream[i] >> self.offset) | (byte_stream[i] << (8 - self.offset))) & 0xFF
            if self.debug: print(byte_stream[i])
        return byte_stream