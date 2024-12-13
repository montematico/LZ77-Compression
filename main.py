import OffsetEncryption as crypt
from LZ77 import LZ77
from FileIO import FileIO as fio
import GUI as gui
from OffsetEncryption import OffsetEncrypt
import logging
# Open the file in binary mode

if __name__ == "__main__":

    if True:
        comp = LZ77.compress(fio.read("TESTDATA.txt"),3)  # inits LZ77 encoder
        print(comp)

        decomp = LZ77.decompress(comp)
        print(decomp)
    if False: #Compressing loop
        logging.basicConfig(level=logging.INFO)
        # Sample data
        #fs = fio.FileIO("TESTDATA.txt")
        data = FileIO.read("TESTDATA.txt")
        # Initialize the LZ77 compressor
        lz77 = LZ77.LZ77(data,control_bytes=3)
        lz77.tokenize()  # Generate tokens
        # Encode the tokens into a byte stream
        compressed_bytes = lz77.encode()
        # Print the compressed byte stream
        print("Compressed Data:", compressed_bytes)
        # Decompress the byte stream
        decompressed_data = lz77.decode(compressed_bytes)
        print("Decompressed Data:", decompressed_data)

    if False: #Encrypting loop
        #Encrpyt the compressed data
        off = crypt.OffsetEncrypt(compressed_bytes,18)
        compr_encrypted = off.encrypt(compressed_bytes)
        print("Encrypted Data:", compr_encrypted)

        raw_decrypted = off.decrypt(compr_encrypted)
        print("Decrypted Data:", raw_decrypted)

    if False: #GUI loop
        g = gui.GUI()
        g.main_menu()