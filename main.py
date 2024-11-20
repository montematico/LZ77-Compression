import OffsetEncryption as off
import LZ77 as lz
import FileIO as fio
# Open the file in binary mode

if __name__ == "__main__":
   pass
   fs = fio.FileIO("LoremIpsum.txt")
   data = fs.read()
   LZobj = lz.LZ77_Compress(data)
   encoded = LZobj.encode()


