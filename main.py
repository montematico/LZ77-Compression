import OffsetEncryption as crypt
from LZ77 import LZ77
from FileIO import FileIO as fio
import os
import GUI as gui
import logging
import pydoc


if __name__ == "__main__":

    #Generate documentation
    if True:
        # Generate documentation for all modules
        modules = ["LZ77", "FileIO", "GUI"]  # Add your module names here
        combined_doc = "<html><head><title>Documentation</title></head><body>\n"

        # Iterate through each module and append its documentation
        for module in modules:
            doc_html = pydoc.HTMLDoc().docmodule(__import__(module))
            combined_doc += f"<h1>Documentation for {module}</h1>\n"
            combined_doc += doc_html
            combined_doc += "\n<hr>\n"  # Add a horizontal rule between module docs

        # Close the HTML structure
        combined_doc += "</body></html>"

        # Write the combined documentation to a single HTML file
        with open("documentation.html", "w") as f:
            f.write(combined_doc)

        print("Combined documentation written to documentation.html")

    #"Modern" Compression Loop using static methods
    if True:
        fp = "Act1Scene1.md"
        file = fio.read(fp)

        comp = LZ77.compress(file,2,os.path.splitext(fp)[1])  #compresses
        decomp,_ = LZ77.decompress(comp)

        print("Raw Size:" ,len(file))
        print("Compressed Size:" , len(comp))
        print("Decompressed Size:" , len(decomp))
        print("Compression Ratio:", len(comp)/len(file))

        print(comp)
        print(decomp)

#The Old Way of doing compression, involves creating an object and calling methods
    if True: #Compressing loop
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

    if True: #Encrypting loop
        #Encrpyt the compressed data
        off = crypt.OffsetEncrypt(compressed_bytes,18)
        compr_encrypted = off.encrypt(compressed_bytes)
        print("Encrypted Data:", compr_encrypted)

        raw_decrypted = off.decrypt(compr_encrypted)
        print("Decrypted Data:", raw_decrypted)

    if True: #GUI loop
        g = gui.GUI()
        g.__init__()