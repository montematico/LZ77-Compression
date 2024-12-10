from dataclasses import dataclass, field
import logging
from urllib.parse import to_bytes

import numpy as np


@dataclass
class MatchToken:
    dist: np.uint16
    length: np.uint8
    type: bool = field(default=True)

@dataclass
class LiteralToken:
    length: np.uint16 #length of literal run, in bytes
    data: np.array([], dtype=np.uint8) #stores up to a maximum of length bytes
    type: bool = field(default=False)

# class LZ77(object):
#     def __init__(self):
#         self.compressed = []
#         self.decompressed = []
#         # Initialize buffers as NumPy arrays
#         self.raw_data = np.array([], dtype=np.uint8)


class LZ77(object):
    #all these in bytes
    #todo set these to higher, more realistic values
    control_byte_length = 3 #how many bytes to use to encode either [signal,length] for literal or [signal, length, distance] for match
    #1 bit for signal, [signal+length].bits + [distance].bits = control_byte_length*8


    max_literal_length = 127 #max length of a run of literals to output (7 bits)
    window_size = 2**16-1 #16 bits is maximum distance from current position to search buffer, so window does not need to be larger
    lookahead_buffer = 2**7 -1 #7 bits used to store the length of a match
    min_pointer_size = 3 #pointers are 3 bytes long. So if a match is less than 3 bytes, it's not worth it

    literal_buffer = []
    compressed_data = []
    raw_data = None #gets initialized in __init__

    def decode(self, compressed_bytes):
        decompressed_data = bytearray()
        i = 0
        while i < len(compressed_bytes):
            signal_and_length = compressed_bytes[i]
            signal_flag = (signal_and_length & 0b10000000) >> 7
            length = signal_and_length & 0b01111111
            i += 1
            if signal_flag == 1:
                # MatchToken
                dist = int.from_bytes(compressed_bytes[i:i + 2], 'big')
                i += 2
                # Retrieve the matched data from the decompressed data
                start_idx = len(decompressed_data) - dist
                for _ in range(length):
                    decompressed_data.append(decompressed_data[start_idx])
                    start_idx += 1
            else:
                # LiteralToken
                literal_data = compressed_bytes[i:i + length]
                i += length
                decompressed_data.extend(literal_data)
        return bytes(decompressed_data)

    def __init__(self, data, window_size=None, lookahead_buffer=None):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Assume 'data' is a list or array of integers representing bytes
        #self.raw_data = np.array([bytes(i) for i in data], dtype=np.uint8)
        self.raw_data = np.frombuffer(data, dtype=np.uint8)
        self.window_size = window_size or self.window_size
        self.lookahead_buffer = lookahead_buffer or self.lookahead_buffer



    def encode(self):
        # Initialize a bytearray to collect the serialized tokens
        serialized_data = bytearray()
        #Bitmask does not change throughout encoding process so we can do it here to not recompute
        LiteralMask = _createBitMask(isLiteral = True)
        PointerMask = _createBitMask(isLiteral = False)

        # Iterate over the compressed data and serialize each token
        for token in self.compressed_data:
            if isinstance(token, MatchToken):
                # Signal flag is 1, represented in the most significant bit of the first byte
                # We'll pack the signal flag and length into a single byte
               signal_and_length = PointerMask(1) | (token.length & PointerMask(2))

                signal_and_length = 0b10000000 | (token.length & 0b01111111)  # 1-bit flag + 7-bit length
                serialized_data.append(signal_and_length)  # Add the signal and length byte
                # Add the distance (2 bytes)
                serialized_data.extend(token.dist.to_bytes(2, 'big'))
            elif isinstance(token, LiteralToken):
                # Signal flag is 0, represented in the most significant bit of the first byte
                # Length is up to max_literal_length (assumed to fit in 7 bits)
                signal_and_length = (token.length & 0b01111111)  # 1-bit flag is 0, so we only need the length
                serialized_data.append(signal_and_length)  # Add the signal and length byte
                # Add the literal data
                serialized_data.extend(token.data)
            else:
                raise ValueError("Unknown token type encountered during encoding")

        # Return the serialized byte stream
        return bytes(serialized_data)

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

            if best_match_length > self.min_pointer_size:
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

        self.logger.info(f"Literal: Length= {LiToken.length}, Data= {LiToken.data}")

    def _createPointer(self, distance, length):
        #creates a pointer token, empties literal buffer before
        if len(self.literal_buffer) > 0:
            self._createLiteral()

        PToken = MatchToken(distance, length)
        self.compressed_data.append(PToken)
        self.logger.info(f"Pointer: {PToken}")

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

