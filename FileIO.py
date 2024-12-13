import logging

class FileIO:
    def __init__(self, filename=None, debug=False):
        self.filename = filename
        self.debug = debug
        self.logger = logging.getLogger(self.__class__.__name__)
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    @staticmethod
    def read(filename):
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                return data
        except Exception as e:
            print(f"Failed to read from {filename}: {e}")
            raise RuntimeError(f"Failed to read from {filename}: {e}")

    @staticmethod
    def write(data, filename):
        try:
            with open(filename, 'wb') as f:
                f.write(data)
        except Exception as e:
            print(f"Failed to write to {filename}: {e}")
            raise RuntimeError(f"Failed to write to {filename}: {e}")

