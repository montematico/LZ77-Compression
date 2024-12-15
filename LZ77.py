from dataclasses import dataclass, field
import logging
import numpy as np
import argparse
import os
#todo
# no, i didnt just delete this before submitting :)


def main():
    """
    Main; handles argument parsing if called from the command line.
    -c or --compress [source] [destination (optional)] Compresses the source file, if no destination is provided, the file is saved as [source].lz77
    -d or --decompress [source] [destination (optional)] Decompresses the source file, if no destination is provided, the file is saved as [source].lz77
    -cb or --control-bytes [int] Sets the number of control bytes to use for compression
    """
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="LZ77 Compression and Decompression Tool"
    )

    # Add arguments
    parser.add_argument(
        "-c", "--compress",
        metavar="input_file",
        nargs="+",
        help="Compress the input file. Optionally specify the output file."
    )
    parser.add_argument(
        "-d", "--decompress",
        metavar="input_file",
        nargs="+",
        help="Decompress the input file. Optionally specify the output file."
    )
    parser.add_argument(
        "-cb", "--control-bytes",
        type=int,
        default=3,
        help="Specify the control byte length for compression. Default is 3."
    )
    # Parse the arguments
    args = parser.parse_args()

    if args.compress:
        input_file = args.compress[0]
        output_file = args.compress[1] if len(args.compress) > 1 else f"{os.path.splitext(input_file)[0]}.Z77"
        file_extension = os.path.splitext(input_file)[1]  # Extract file extension
        try:
            with open(input_file, "rb") as f:
                raw_data = f.read()
            compressed_data = LZ77.compress(raw_data, control_bytes=args.control_bytes, extension=file_extension)
            with open(output_file, "wb") as f:
                f.write(compressed_data)
            print(f"Compression successful. File saved to {output_file}.")
            return 0
        except Exception as e:
            print(f"Error during compression: {e}")
            return 1

    elif args.decompress:
        input_file = args.decompress[0]
        output_file = args.decompress[1] if len(args.decompress) > 1 else os.path.splitext(input_file)[0]
        try:
            with open(input_file, "rb") as f:
                compressed_data = f.read()
            decompressed_data, file_extension = LZ77.decompress(compressed_data)
            output_file_with_extension = output_file + file_extension
            with open(output_file_with_extension, "wb") as f:
                f.write(decompressed_data)
            print(f"Decompression successful. File saved to {output_file_with_extension}.")
            return 0
        except Exception as e:
            print(f"Error during decompression: {e}")
            return 1

    else:
        parser.print_help()


@dataclass
class MatchToken:
    """
       Represents a match token in LZ77 compression.

       Attributes:
           dist (np.uint32):
               The distance from the current position to the start of the matching substring
               in the sliding window (search buffer). A smaller value indicates a closer match.
           length (np.uint32):
               The length of the matching substring (in bytes). Represents how many bytes
               can be copied from the reference in the search buffer.
           type (bool):
               A flag that identifies the token type. This is always `True` for MatchToken,
               differentiating it from LiteralToken.
       """
    dist: np.uint32 #(backwards) distance from current position to start of match
    length: np.uint32 #length of match, in bytes
    type: bool = field(default=True) #flag to identify token type, will always be true for matches

@dataclass
class LiteralToken:
    """
        Represents a literal token in LZ77 compression.

        Attributes:
            length (np.uint32):
                The number of bytes in the literal run. This indicates how many bytes
                will be copied directly to the output without referencing prior data.
            data (np.array):
                A NumPy array containing the raw byte values of the literal run. Each element
                represents one byte of uncompressed data.
            type (bool):
                A flag that identifies the token type. This is always `False` for LiteralToken,
                differentiating it from MatchToken.
        """
    #idk why but adding an __init__ function, even a dummy one breaks this
    length: np.uint32 #length of literal run, in bytes
    data: np.array([], dtype=np.uint32) #literal run data thats being encoded
    type: bool = field(default=False) #flag to identify token type, will alawys be false for literals



class LZ77(object):
    literal_buffer = []
    compressed_data = []
    EXTENSION_MAP = {
        0x0: "",  # No extension
        0x1: ".txt",
        0x2: ".bin",
        0x3: ".jpg",
        0x4: ".png",
        0x5: ".pdf",
        0x6: ".zip",
        0x7: ".mp3",
        0x8: ".py",
        0x9: ".html",
        0xA: ".md",
        # Add up to 16 extensions as needed
    }
    def _var_init(self):
        """
        Inits All the object variables, kept in a function so they can be dynamically set.
        (and bc it gets called twice for encoding and decoding)
        :return: None
        """
        # Total bits in the control bytes
        self.total_bits = self.control_byte_length * 8

        # Reserve 1 bit for the signal
        usable_bits = self.total_bits - 1
        self.literal_length_bits = usable_bits #for literal runs all bits are used for length (- 1 for signal)

        if self.control_byte_length == 1:
           #For 1 byte control bytes we must set custom limits (allocating an extra bit for length and one less to pointer)
            self.max_pointer_length_bits = 3
            self.pointer_distance_bits = 4
        else:
            # Allocate 1/3 of the usable bits to length (rounded down)
            self.max_pointer_length_bits = usable_bits // 3
            # Remaining bits are for the distance
            self.pointer_distance_bits = usable_bits - self.max_pointer_length_bits

        # Calculate the actual limits
        self.max_literal_length = (1 << self.literal_length_bits) - 1
        self.max_distance = (1 << self.pointer_distance_bits) - 1
        self.max_pointer_length = (1 << self.max_pointer_length_bits) - 1
        # self.max_literal_length = 2**self.literal_length_bits -1
        # self.max_distance = 2**self.pointer_distance_bits -1
        # self.max_pointer_length = 2**self.max_pointer_length_bits -1

        #Set the window size and lookahead buffer size based off of the control byte length
        self.window_size = 2**self.pointer_distance_bits-1 #maximum distance from current position to search buffer, (2/3rd of control byte)
        self.lookahead_buffer = 2**self.literal_length_bits -1 #7 bits used to store the length of a match


    def __init__(self, data, control_bytes = 3,extension=""):
        """
        Initializes the LZ77 compressor with the raw data and control byte length.
        :param data: data to compress as bytes
        :param control_bytes: (optional) number of control bytes to use default is 3
        :param extension: (optional) file extension
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        if not (1 <= control_bytes <= 15):
            raise ValueError("control_byte_length must be between 1 and 15.")
        else: self.control_byte_length = control_bytes #Assigns this so _var_init can work it.
        self.extension = extension

        # Assume 'data' is a list or array of integers representing bytes
        #self.raw_data = np.array([bytes(i) for i in data], dtype=np.uint8)
        self.raw_data = np.frombuffer(data, dtype=np.uint8)
        self._var_init()

    @staticmethod
    def compress(data, control_bytes=3, extension=""):
        """
        Compresses the input data using LZ77.
        :param data: The raw data to compress (bytes-like).
        :param control_bytes: The number of bytes for control structures.
        :param extension: File extension to encode in the header.
        :return: Compressed data as bytes.
        """
        # Initialize an instance for variable setup and helper methods
        instance = LZ77(data, control_bytes,extension)
        instance.tokenize()  # Generate tokens
        return instance.encode()  # Serialize the compressed tokens

    @staticmethod
    def decompress(to_decompress):
        """
        Decompresses the compressed data using LZ77.
        :param to_decompress: The compressed data to decompress (bytes-like).
        :return: Tuple (decompressed data as bytes, file extension as string).
        """
        #Create an instance to decompress the data
        instance = LZ77(b"")  # Initialize with dummy data
        decompressed_data = instance.decode(to_decompress)
        return decompressed_data, instance.extension

    def encode(self):
        """
        Encodes the compressed data into a byte stream.
        :return: Serialized byte stream of the compressed data.
        """
        #init serialized data array
        serialized_data = bytearray()
        # Generate header, and prepend to data
        header = self.__generate_header()
        serialized_data.extend(header)

        # Generate bitmasks for literals and pointers
        signal_mask = 0b1 << (self.total_bits - 1)  # MSB is the signal bit
        length_mask = (1 << self.literal_length_bits) - 1
        distance_mask = (1 << self.pointer_distance_bits) - 1

        # Iterate over the compressed data and serialize each token
        for token in self.compressed_data:
            if isinstance(token, MatchToken):
                # Signal flag is 1
                signal_and_length = signal_mask | ((token.length & length_mask) << self.pointer_distance_bits)
                signal_and_length |= (token.dist & distance_mask)

                # Write exactly `control_byte_length` bytes for the control field
                control_bytes = signal_and_length.to_bytes(self.control_byte_length, 'big')
                serialized_data.extend(control_bytes)

            elif isinstance(token, LiteralToken):
                # Signal flag is 0
                signal_and_length = (token.length & ((1 << (self.total_bits - 1)) - 1))

                # Write exactly `control_byte_length` bytes for the control field
                control_bytes = signal_and_length.to_bytes(self.control_byte_length, 'big')
                serialized_data.extend(control_bytes)

                # Add the literal data
                serialized_data.extend(token.data)

            else:
                raise ValueError("Unknown token type encountered during encoding")

        # Return the serialized byte stream
        return bytes(serialized_data)

    def decode(self, compressed_bytes):
        """
        Decodes the compressed byte stream into the original data. Reads header to find control byte length.
        :param compressed_bytes: compressed LZ77 data as bytes
        :return: decoded data as bytes
        """
        # Parse the header
        control_byte_length, compressed_bytes = self.__parse_header(compressed_bytes)

        # Update the control_byte_length dynamically
        self.control_byte_length = control_byte_length
        self._var_init() #updates the rest of the vars accordingly

        decompressed_data = bytearray()
        i = 0

        while i < len(compressed_bytes):
            # Read exactly `control_byte_length` bytes for the control field
            signal_and_length = int.from_bytes(compressed_bytes[i:i + self.control_byte_length], 'big')
            i += self.control_byte_length

            # Extract the signal bit (MSB)
            signal_flag = (signal_and_length >> (self.total_bits - 1)) & 0b1

            if signal_flag == 1:
                # MatchToken: Extract length and distance
                length = (signal_and_length >> self.pointer_distance_bits) & ((1 << self.max_pointer_length_bits) - 1)
                dist = signal_and_length & ((1 << self.pointer_distance_bits) - 1)

                # Retrieve the matched data from the decompressed data
                start_idx = len(decompressed_data) - dist
                if start_idx < 0:
                    raise ValueError(f"Invalid start index {start_idx} during decoding.")

                for _ in range(length):
                    decompressed_data.append(decompressed_data[start_idx])
                    start_idx += 1

            else:
                # LiteralToken: Extract length and literal data
                length = signal_and_length & ((1 << (self.total_bits - 1)) - 1)

                # Read the literal data
                literal_data = compressed_bytes[i:i + length]
                i += length

                # Add to decompressed data
                decompressed_data.extend(literal_data)

        return bytes(decompressed_data)

    def tokenize(self):
        """
        Tokenizes the raw data using LZ77. Creating literal and match tokens
        :return: Compressed data as a list of tokens.
        """
        # Tokenize the raw data using LZ77. Tokens can then be used to create a compressed stream.
        i = 0
        data_length = self.raw_data.size
        while i < data_length:
            match_distance = 0
            match_length = 0
            next_symbol = None

            # Define the start of the search buffer
            start_idx = max(0, i - self.window_size)
            end_idx = max(0,i - 1)

            # Extract the search and lookahead buffers
            search_buffer = self.raw_data[start_idx:end_idx]
            lookahead_buffer = self.raw_data[i:i + self.lookahead_buffer]

            # Initialize variables to keep track of the best match
            best_match_distance = 0
            best_match_length = 0

            # Iterate over possible match lengths
            for j in range(1, len(lookahead_buffer)):
                # Current substring from the lookahead buffer
                substring = lookahead_buffer[:j]
                # Search for the substring in the search buffer
                pos = self.__find_subarray(search_buffer, substring)
                if pos != -1:
                    # Update the best match found so far
                    best_match_distance = len(search_buffer) - pos + 1 #idk why +1 but everything was off by one
                    best_match_length = j
                else:
                    # No further match; break out of the loop
                    break


            #checks min size requirement for match
            if best_match_length > self.control_byte_length:
                self.__createPointer(best_match_distance, best_match_length)
                i += best_match_length
            else:
                # No match found; output a literal byte to the literal buffer
                self.literal_buffer.append(self.raw_data[i])
                if len(self.literal_buffer)>=self.max_literal_length:
                    self.__createLiteral()
                i += 1

        # After processing, check if there are remaining literals and create token if neccecary
        if len(self.literal_buffer) > 0:
            self.__createLiteral()

        self.logger.info(f"idx: {i}, data_length: {data_length}")
        return self.compressed_data


    def __createBitMask(self, isLiteral=True):
        """
        Creates a bitmask used for encoding/decoding based on whether the token is a literal or pointer.
        For literals, the bitmask is used to encode the signal flag and length.
        For pointers, the bitmask is used to encode the signal flag, length, and distance.
        I don't think this is used anymore, in favor of generating bitmasks in situ
        """
        # The control_byte_length determines the size of the bitmask (in bits).
        total_bits = self.control_byte_length * 8

        if isLiteral:
            # Create a bitmask for literals
            # Signal flag (1 bit) + Length (remaining bits)
            signal_mask = 0b1 << (total_bits - 1)  # Signal flag occupies the MSB
            length_mask = (1 << (total_bits - 1)) - 1  # Remaining bits for the length
            return signal_mask, length_mask

        else:
            # Create a bitmask for pointers
            # Signal flag (1 bit) + Length (7 bits) + Distance (remaining bits)
            signal_mask = 0b1 << (total_bits - 1)  # Signal flag occupies the MSB
            length_bits = 7
            length_mask = ((1 << length_bits) - 1) << (total_bits - 1 - length_bits)  # Next 7 bits for length
            distance_mask = (1 << (total_bits - 1 - length_bits)) - 1  # Remaining bits for distance
            return signal_mask, length_mask, distance_mask


#create tokens for compressed stream
    def __createLiteral(self):
        """
        Creates a literal token from the literal buffer and appends it to the compressed data.
        :return: None
        """
        #empties literal buffer and creates a literal token
        if len(self.literal_buffer) == 0: return #no literal to output

        LiToken = LiteralToken(len(self.literal_buffer), self.literal_buffer) #creates a literal token
        self.literal_buffer = [] #empties the literal buffer
        self.compressed_data.append(LiToken) #appends the literal token to the compressed data

        #self.logger.info(f"Literal: Length= {LiToken.length}, Data= {LiToken.data}")

    def __createPointer(self, distance, length):
        """
        Creates a pointer token from the given distance and length, and appends it to the compressed data.
        :param distance: distance to match
        :param length: length of match
        :return: None
        """
        #creates a pointer token, empties literal buffer before
        if len(self.literal_buffer) > 0:
            self.__createLiteral()

        PToken = MatchToken(distance, length)
        self.compressed_data.append(PToken)
        #self.logger.info(f"Pointer: {PToken}")

    @staticmethod
    def __find_subarray(array, subarray):
        """
        Helper function to find a subarray within an array.
        :param array:
        :param subarray:
        :return:
        """
        len_sub = len(subarray)
        if len_sub == 0:
            return -1
        len_array = len(array)
        for k in range(len_array - len_sub + 1):
            if np.array_equal(array[k:k + len_sub], subarray):
                return k
        return -1

    def __generate_header(self):
        """
        Generates a 2-byte header for the compressed stream.
        Byte 1: Magic number (0xC7 for LZ77-compressed stream).
        Byte 2: High 4 bits encode the control_byte_length (1–15), low 4 bits reserved for file type encoding.
        :return: 2-byte header as bytes
        """
        magic_number = 0xC7  # Arbitrary identifier for compressed stream
        control_byte_length_encoded = (self.control_byte_length & 0x0F) << 4  # High nibble

        # Map the file extension to a 4-bit code
        extension_code = {v: k for k, v in self.EXTENSION_MAP.items()}.get(self.extension, 0x0)  # Default to 0 (no extension)
        header = bytearray([magic_number, control_byte_length_encoded | extension_code])
        return header


    def __parse_header(self, compressed_stream):
        """
        Parses the 2-byte header from the compressed stream.
        :param compressed_stream: Compressed stream as bytes.
        :return:  Returns the control_byte_length, filetype extension and the remaining stream:
        """
        if len(compressed_stream) < 2:
            raise ValueError("Compressed stream is too short to contain a valid header.")

        magic_number = compressed_stream[0]
        if magic_number != 0xC7:
            raise ValueError("Invalid magic number. Not an LZ77-compressed stream.")

        control_byte_length = (compressed_stream[1] >> 4) & 0x0F
        if not (1 <= control_byte_length <= 15):
            raise ValueError("Invalid control_byte_length in header.")

        extension_code = compressed_stream[1] & 0x0F
        extension = self.EXTENSION_MAP.get(extension_code, "")

        return control_byte_length, extension, compressed_stream[2:]

    #not used within the class, but by other elements to verify the header
    @staticmethod
    def verify_header(file_path):
        """
        Reads the first 2 bytes of the file and checks for a valid header.
        Returns True if the header is valid, False otherwise.
        :param file_path:
        :return: Bool, true if header is valid, false otherwise
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(2)
            # Check for the magic number 0xC7 and validate header
            return len(header) == 2 and header[0] == 0xC7
        except Exception as e:
            print(f"Error checking header: {e}")
            return False

if __name__ == "__main__":
    main()