from dataclasses import dataclass, field
import logging
from urllib.parse import to_bytes

import numpy as np


@dataclass
class MatchToken:
    dist: np.uint32
    length: np.uint32
    type: bool = field(default=True)

@dataclass
class LiteralToken:
    length: np.uint32 #length of literal run, in bytes
    data: np.array([], dtype=np.uint32) #stores up to a maximum of length bytes
    type: bool = field(default=False)



class LZ77(object):
    #all these in bytes


    def _var_init(self):
        #todo set these to higher, more realistic values
        #self.control_byte_length = 2 #how many bytes to use to encode either [signal,length] for literal or [signal, length, distance] for match
        #1 bit for signal, [signal+length].bits + [distance].bits = control_byte_length*8
        # Total bits in the control bytes
        self.total_bits = self.control_byte_length * 8

        # Reserve 1 bit for the signal
        usable_bits = self.total_bits - 1
        self.literal_length_bits = usable_bits; #for literal runs all bits are used for length (- 1 for signal)
        # Allocate 1/3 of the usable bits to length (rounded down)
        self.max_pointer_length_bits = usable_bits // 3
        # Remaining bits are for the distance
        self.pointer_distance_bits = usable_bits - self.max_pointer_length_bits

        # Calculate the actual limits
        self.max_literal_length = (1 << self.max_pointer_length_bits) - 1
        self.max_distance = (1 << self.pointer_distance_bits) - 1
        self.max_pointer_length = (1 << self.max_pointer_length_bits) - 1

        #Set the window size and lookahead buffer size based off of the control byte length
        self.window_size = 2**self.pointer_distance_bits-1 #maximum distance from current position to search buffer, (2/3rd of control byte)
        self.lookahead_buffer = 2**self.max_pointer_length_bits -1 #7 bits used to store the length of a match


    literal_buffer = []
    compressed_data = []
    raw_data = None #gets initialized in __init__

    # Determine bit allocations based on control_byte_length
    #total_bits = self.control_byte_length * 8
    #length_bits = total_bits // 3
    #distance_bits = total_bits - length_bits - 1  # Remaining bits after signal and length


    def __init__(self, data, control_bytes = 3):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.control_byte_length = control_bytes #Assigns this so _var_init can work it.

        # Assume 'data' is a list or array of integers representing bytes
        #self.raw_data = np.array([bytes(i) for i in data], dtype=np.uint8)
        self.raw_data = np.frombuffer(data, dtype=np.uint8)
        self._var_init()

    def encode(self):
        #init serialized data array
        serialized_data = bytearray()
        # Generate header, and prepend to data
        header = self._generate_header()
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
        # Parse the header
        control_byte_length, compressed_bytes = self.parse_header(compressed_bytes)

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
                pos = self._find_subarray(search_buffer, substring)
                if pos != -1:
                    # Update the best match found so far
                    best_match_distance = len(search_buffer) - pos + 1 #idk why +1 but everything was off by one
                    best_match_length = j
                else:
                    # No further match; break out of the loop
                    break

            if best_match_length > self.control_byte_length:
                self._createPointer(best_match_distance, best_match_length)
                i += best_match_length
            else:
                # No match found; output a literal byte to the literal buffer
                self.literal_buffer.append(self.raw_data[i])
                if len(self.literal_buffer)>=self.max_literal_length:
                    self._createLiteral()
                i += 1

        # After processing, check if there are remaining literals and create token if neccecary
        if len(self.literal_buffer) > 0:
            self._createLiteral()

        self.logger.info(f"idx: {i}, data_length: {data_length}")
        return self.compressed_data

    def _createBitMask(self, isLiteral=True):
        """
        Creates a bitmask used for encoding/decoding based on whether the token is a literal or pointer.
        For literals, the bitmask is used to encode the signal flag and length.
        For pointers, the bitmask is used to encode the signal flag, length, and distance.
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
    def _createLiteral(self):
        #empties literal buffer and creates a literal token
        if len(self.literal_buffer) == 0: return #no literal to output

        LiToken = LiteralToken(len(self.literal_buffer), self.literal_buffer) #creates a literal token
        self.literal_buffer = [] #empties the literal buffer
        self.compressed_data.append(LiToken) #appends the literal token to the compressed data

        #self.logger.info(f"Literal: Length= {LiToken.length}, Data= {LiToken.data}")

    def _createPointer(self, distance, length):
        #creates a pointer token, empties literal buffer before
        if len(self.literal_buffer) > 0:
            self._createLiteral()

        PToken = MatchToken(distance, length)
        self.compressed_data.append(PToken)
        #self.logger.info(f"Pointer: {PToken}")

    def _find_subarray(self, array, subarray):
        """Helper function to find a subarray within an array."""
        len_sub = len(subarray)
        if len_sub == 0:
            return -1
        len_array = len(array)
        for k in range(len_array - len_sub + 1):
            if np.array_equal(array[k:k + len_sub], subarray):
                return k
        return -1

    def _generate_header(self):
        """
        Generates a 2-byte header for the compressed stream.
        Byte 1: Magic number (0xC7 for LZ77-compressed stream).
        Byte 2: High 4 bits encode the control_byte_length (1–15), low 4 bits reserved.
        """
        if not (1 <= self.control_byte_length <= 15):
            raise ValueError("control_byte_length must be between 1 and 15.")

        magic_number = 0xC7  # Arbitrary identifier for compressed stream
        control_byte_length_encoded = (self.control_byte_length & 0x0F) << 4  # High nibble
        reserved = 0x00  # Low nibble reserved for future use
        header = bytearray([magic_number, control_byte_length_encoded | reserved])
        return header

    @staticmethod
    def parse_header(compressed_stream):
        """
        Parses the 2-byte header from the compressed stream.
        Returns the control_byte_length and the remaining stream.
        """
        if len(compressed_stream) < 2:
            raise ValueError("Compressed stream is too short to contain a valid header.")

        magic_number = compressed_stream[0]
        if magic_number != 0xC7:
            raise ValueError("Invalid magic number. Not an LZ77-compressed stream.")

        # Extract control_byte_length from the high nibble of the second byte
        control_byte_length = (compressed_stream[1] >> 4) & 0x0F
        if not (1 <= control_byte_length <= 15):
            raise ValueError("Invalid control_byte_length in header.")

        # Return control_byte_length and the rest of the stream
        return control_byte_length, compressed_stream[2:]

    #not used within the class, but by other elements to verify the header
    @staticmethod
    def verify_header(file_path):
        """
        Reads the first 2 bytes of the file and checks for a valid header.
        Returns True if the header is valid, False otherwise.
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(2)
            # Check for the magic number 0xC7 and validate header
            return len(header) == 2 and header[0] == 0xC7
        except Exception as e:
            print(f"Error checking header: {e}")
            return False