import logging

class FileIO:
    def __init__(self, filename=None, debug=False):
        """
        Initialize self, setting the filename and debug flag (if provided).
        :param filename: (optional) filename to load into FileIO object
        :param debug: (optional) weather or not to enable debug logging
        """
        self.filename = filename
        self.debug = debug
        self.logger = logging.getLogger(self.__class__.__name__)
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    @staticmethod
    def read(filename):
        """
        Reads the contents of a file and returns it as a byte array.
        :param filename: filename to read from
        :return: byte array
        """
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                return data
        except Exception as e:
            print(f"Failed to read from {filename}: {e}")
            raise RuntimeError(f"Failed to read from {filename}: {e}")

    @staticmethod
    def write(data, filename):
        """
        Writes the contents of a byte array to a file.
        :param data: data to write to filename
        :param filename: filepath/name to write to
        :return: None
        """
        try:
            with open(filename, 'wb') as f:
                f.write(data)
        except Exception as e:
            print(f"Failed to write to {filename}: {e}")
            raise RuntimeError(f"Failed to write to {filename}: {e}")
