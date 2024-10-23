class fileIO(object):
    debug = False #debug/verbose mode
    filename = ""
    FS = bytearray() #file stream. Contains the file to be read/written as a bytearray
        def __init__(self, filename):
            self.filename = filename
        def read(self,filename=self.filename):
            with open(filename, 'rb') as f:
                FS = bytearray(f.readlines())
                if debug: print("Read " + str(len(FS)) + " bytes from " + filename)
                return FS
        def write(self,FS, filename):
            self.filename = filename or self.filename
            with open(self.filename, 'wb') as f:
                f.writelines(FS)
                return FS