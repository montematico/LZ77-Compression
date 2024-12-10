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

    def read(self, filename=None):
        # Use the provided filename, or default to self.filename
        filename = filename or self.filename
        if not filename:
            self.logger.error("No filename provided for reading.")
            raise ValueError("Filename must be provided.")
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                self.logger.info(f"Read {len(data)} bytes from {filename}")
                return data  # Return data as bytes
        except Exception as e:
            self.logger.error(f"Failed to read from {filename}: {e}")
            raise

    def write(self, data, filename=None):
        # Use the provided filename, or default to self.filename
        filename = filename or self.filename
        if not filename:
            self.logger.error("No filename provided for writing.")
            raise ValueError("Filename must be provided.")
        try:
            with open(filename, 'wb') as f:
                f.write(data)
                self.logger.info(f"Wrote {len(data)} bytes to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to write to {filename}: {e}")
            raise
