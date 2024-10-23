import OffsetEncryption as off
# Open the file in binary mode

if __name__ == "__main__":
    bytestream = bytearray()
    with open("Act1Scene1.txt", 'rb') as f:
        byte = f.read(1)  # Read byte-by-byte

        # Loop through the file until the end
        while byte:
            # Append each byte to the byte array
            bytestream.append(int.from_bytes(byte, byteorder='big'))
            byte = f.read(1)  # Read the next byte
    print("\nOriginal String:\n", bytestream)
    O = off.OffsetEncrypt(bytestream, 5,debug=False)


    print("\nEncrypted String:\n" , str(O.encrypt()))

    print("\nDecrypted String:\n" , str(O.decrypt()))