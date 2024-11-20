import logging
from io import FileIO

class fileIO(object):
    debug = False #debug/verbose mode
    filename = ""
    FS = bytearray() #file stream. Contains the file to be read/written as a bytearray
    def __init__(self, filename):
        self.filename = filename
        self.logger = logging.getLogger(self.__class__.__name__) #logging i hope

    def read(self,filename):
        self.filename = filename or self.filename #if filename is not provided, use the default filename
        with open(filename, 'rb') as f:
            self.FS = bytearray(f.read())
            self.logger.info("Read " + str(len(FS)) + " bytes from " + filename) #logging
            return FS
    def write(self,FS, filename):
        self.filename = filename or self.filename
        with open(self.filename, 'wb') as f:
            f.write(FS)
            self.logger.info("Wrote " + str(len(FS)) + " bytes to " + self.filename) #logging
            return FS
