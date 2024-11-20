import NumPy as np

class LZ77(object):
    compressed = bytearray()
    decompressed = bytearray()
    def __init__(self):
        #add some function to initilize the buffer and load the file
        pass


class LZ77_Compress(LZ77):
    search_buffer = bytearray()
    raw_data = bytearray() #consider moving this up to LZ77 class

    def __init__(self,file, window_size = 20, lookahead_buffer = 15):
        super().__init__()
        self.raw_data  = file #unsanitized input, consider changing
        self.window_size = window_size #Max num of bytes to look back for
        self.lookahead_buffer = lookahead_buffer #Max num of bytes to look ahead for
        self.compressed = []
    def encode(self):
        #compress the bytestream, main loop hopefully
        #todo i is still uninitialized, find where to do it and how to update to idx
        i = 0
        while i < len(self.raw_data):
            match_distance = 0 #no of bytes backwards towards beggining of match
            match_length = 0 #no of bytes in match
            next_symbol = None

            start_idx = max(0,i-self.window_size) #define the start of the search buffer up to a maximum of window_size
            search_buffer = self.raw_data[start_idx:i]
            lookahead_buffer = self.raw_data[i:i+self.lookahead_buffer]

            for j in range(1,len(lookahead_buffer)+1):
                substring = lookahead_buffer[:j] #creates substring, gets 1 byte longer every iteration
                pos = search_buffer.rfind(substring) #searches for substring
                if pos != -1:
                    #match found condition
                    #iterate again to see if you can expand the match length
                    pass
                else:
                    #no match found condition
                    #if this condition is reached safe to assume that the match length is no longer increasing.
                    #append the match to the compressed data
                    pass
    def __createPointer(self,distance,length):
        #create a pointer to the match
        pass


class LZ77_Decompress(LZ77):
    def __init__(self):
        pass