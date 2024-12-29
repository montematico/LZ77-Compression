# Required Libraries
```
colorama==0.4.6
iniconfig==2.0.0
numpy==2.2.0
packaging==24.2
pluggy==1.5.0
pyasn1==0.6.1
PySimpleGUI==5.0.7
pytest==8.3.4
rsa==4.9
```
\*I've included a `requirements.txt` in my `submission.zip` file. You can recursively install the dependencies using
`pip install -r requirements.txt`

---
# Command Line Interface
From the start I envisioned this project as a Command Line Interface and it was duly implemented. 
it accepts 3 flags
- `-c --compress [source] [dest*]`  Compress a file
- `-d --decompress [source] [dest*]` Decompress a file
- `-cb --control-bytes [int]` range 1,15 byte "control bytes" which dictate length of literal runs or pointers. Larger control bytes are only really practical for *highly* repetitive patterns due to the increased overhead. Default is 3 bytes.
\*dest. is optional; if dest. is not provided compressed file is written to the same directory
```shell
#Compress a file with -c --compress
python LZ77.py -c [source] 

#decompress a file -d --decompress
python LZ77.py -d [source].Z77

#compress with custom control byte length -cb --control-bytes
python LZ77.py -c [source] [dest*] --control-bytes 2
```

<div style="page-break-after: always;"></div>
# GUI
My project also has a GUI to enable file compression. It uses pysimpleGUI to render the GUI
The GUI can be run using `python GUI.py`
## Initial State
In its initial state the user can use the file browser to find a file to either compress/decompress
![[Pasted image 20241215173932.png]]
Initial state of GUI

## File Compression

If the user selects a file that has not been compressed (determined by checking for a header) the GUI presents the Compress button and a counter to increment the amount of control bytes.


## File Decompression

If the user selects a file that is compressed (determined based off the header) the GUI will go into compression mode and display the appropriate controls.

The file type input box can be used to specify the decompressed filetype, although this option is disabled if the file type is detected in the header.



---

# Lil Demo in main.py
```shell
python main.py
```
will run a script in main compressing a sample file and returning the compression ratio
```python
#"Modern" Compression Loop using static methods  
if True:  
    fp = os.path.join("tests", "test_data", "Act1Scene1.txt")  
    file = fio.read(fp)  
  
    comp = LZ77.compress(file,2,os.path.splitext(fp)[1])  #compresses  
    decomp,_ = LZ77.decompress(comp)  
  
    print("Raw Size:" ,len(file))  
    print("Compressed Size:" , len(comp))  
    print("Decompressed Size:" , len(decomp))  
    print("Compression Ratio:", len(comp)/len(file))  
    print("Compressed and decompressed streams:")  
    print(comp)  
    print(decomp)
```
Expected output
```shell
Initialized LZ77 with extension: .txt
Encoding header with extension: .txt, code: 1
Initialized LZ77 with extension: 
Decoded extension code: 1, extension: .txt
Raw Size: 3639
Compressed Size: 2836
Decompressed Size: 3639
Compression Ratio: 0.7793349821379499
Compressed and decompressed streams:
"Compressed Stream -- Omitted for Clarity"
"Decompressed Stream -- Omitted for clarity"
Process finished with exit code 0
```


# Example Setup / Run
```shell
"Compression workflow"
pip install requirements.txt -r
python LZ77.py -c tests\test_data\Act1Scene1.txt Act1Scene1_comp
python LZ77.py -d Act1Scene1_comp.Z77

"Launch GUI"
python GUI.py

"Launch Demo in main.py"
"I set this up so it should find the right file in the test_data dir but if this fails specificy filepath manually in fp=[path\to\file]"
python main.py

```
