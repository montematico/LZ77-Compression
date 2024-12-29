A quick note: I experimented with creating my `Design.pdf` and `Documentation.pdf` using a Markdown notes editor. Although it has some advantages, I realized it also has drawbacks, especially when trying to export to PDF. So apologies ahead of time for the janky page-breaks.
I also noticed in Firefox the rendering of code snippets can get clipped. I have not noticed the issue in google-drive.

# Introduction
I've always thought that data compression was a cool concept, how can you take data of a certain length and make it smaller, while still preserving the data?
Since I had an interest in this topic since before I took ENAE380 I decided now was a good a time as any to give it a shot. I had explored a compression algorithm before, trying to implement it in C++, however, that project never really got off the ground. However, the research I did for that project informed this one and gave me a lot of the foundational knowledge to understand what was going on under the hood.

I looked through compression algorithms and eventually settled on the [LZ77 algorithm](https://en.wikipedia.org/wiki/LZ77_and_LZ78) This algorithm uses two sliding windows, one looking back and (the sliding window) and one looking forward (the lookahead buffer). The encoding algorithm at its most basic looks forward and tries to match patterns in the sliding window. If it finds a match it generates a pointer (which is smaller than the literal pattern). If no match is found (or a match+overhead would not reduce file size) the algorithm instead outputs a literal token which tells the algorithm that the next n-bytes will be a literal run. The entire algorithm works by replacing redundant information with metadata.

For the sake of clarity I have used [microsoft's vocab conventions](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-wusp/fb98aa28-5cd7-407f-8869-a6cef1ff1ccb) (pasted below) to describe my code:

**input stream**: The sequence of bytes to be compressed.

**byte**: The basic data element in the input stream.

**coding position**: The position of the byte in the input stream that is currently being coded (the beginning of the lookahead buffer).
p
**lookahead buffer**: The byte sequence from the coding position to the end of the input stream.

**window**: A buffer of size W that indicates the number of bytes from the coding position backward. The window is empty at the beginning of the compression, then grows to size W as the input stream is processed. Once it reaches size W, it then "slides" along with the coding position.

**pointer**: Information about the starting offset of the match in the window (referred to as "B" in the example later in this section) and its length (referred to as "L" in the example later in this section). The starting offset is expressed as the count of bytes from the coding position backwards into the 
window. The length is the number of bytes to read forward from the starting offset.


My  **LZ77** compression loop can be broken down into 5 steps
1. Set the **coding position** to the beginning of the **input stream**
2. Find the longest match in the window for the **lookahead buffer**
3. If a match is found output the pointer P. Move the coding position (and the window) L bytes forward. (L is the length of the matched pattern, in bytes)
4. If a match is not found, output byte to literal buffer, move the **coding position** (and the window) one byte forward
5. If lookahead buffer is not empty, return to step 2
Of course there are many intermediate steps involved with turning this algorithm theory into a workable example. These steps are roughly run in reverse to decode/decompress an **input stream**

#### Qualitative example
Consider the input stream we want to compress: `abracadabra`
![[1_lAxi1TrfT8UNKj0KSUo6JA-3535834024.jpeg]]
[source](https://medium.com/@vincentcorbee/lz77-compression-in-javascript-cd2583d2a8bd)
- Our algorithm begins at the first position, since the search buffer is empty a literal is outputted.
- repeat for 2nd and 3rd **CP**
- At the 4th character we see an `a` again, so instead of outputting a literal we instead output a pointer, it has a distance of 3 bytes and length of 1 byte, dutifully encoded in the pointer **P**
- `c` is encoded as a literal
- `abra` the final 4 bytes is a repetition of the first 4 bytes `abra` so we can just output a pointer instead of repeating the bytes.

<div style="page-break-after: always;"></div>
### Other Compression Algorithms
Data compression of course is not a new concept and algorithms have existed for a long time to reduce the size of data. Common filetypes like `.zip` are compressed archives although they usually implement multiple compression algorithms successively. 

## Other common compression algorithms through history:
#### Brotli Compression:
Brotli is a modern, highly efficient, and general-purpose lossless compression algorithm designed by Google. It is widely used in web protocols, such as HTTP/2, to reduce data transfer sizes and improve page load times.
	- Brotli combines dictionary-based models (like LZ77) with Huffman coding
	- Optimized for web data, with pre defined dictionaries for common patterns in `.HTML` `.CSS` and `.js` files.
#### Huffman Coding
If Brotli is the successful posterchild of modern compression then Huffman coding is akin to its great grandfather who set the stage. Huffman coding is an older algorithm (published in 1952) that was widely used for lossless data compression before dictionary-based methods like LZ77 became prevalent.
- Huffman (first published in 1952) predates dictionary compression methods and instead uses a binary tree to represent variable-length-codes
- In a modern context it is often used in combination with other methods. (e.g. in `.JPEG` compression)

#### Singlular Value Decomposition (SVD)
Techniques like **LU decomposition** or **SVD** (Singular Value Decomposition) are not typically used for general-purpose compression but are highly effective in specific contexts, such as image or audio compression.

Although this algorithm is less directly applicable I learned about many of the concepts of file compression by learning about **SVD** and **LU decomposition** in a numerical analysis class. This algorithm is *lossy* so it cannot be used to reconstruct the data perfectly.

<div style="page-break-after: always;"></div>
---
# Design Process
My original proposal was to implement public/private key encryption with compression as a stretch goal. However, I soon realized that a meaningful public/private key encryption was a very large undertaking and more importantly that the problem of compression was far more interesting to me personally to attempt to solve.

## What I did
1. **Initial Idea and Goals**
    - Focused on implementing an efficient LZ77 compression algorithm.
    - Prioritized modularity by creating distinct components: token classes (`MatchToken`, `LiteralToken`), compression, and decompression workflows.
    - Decided on using `numpy` for performance when handling large datasets.
    - Designed the sliding window and lookahead buffer logic to mimic the behavior of the LZ77 algorithm.
2. **Core Steps**
    - Started by defining `MatchToken` and `LiteralToken` dataclasses to represent encoded data.
    - Wrote the `tokenize` method to handle the core logic of matching substrings and creating tokens.
    - Implemented the `encode` method to serialize tokens into a byte stream.
    - Built the `decode` method to reverse the process and reconstruct the original data.
    - Integrated control byte calculations for dynamic compression control (allowing dynamic length control_bytes).
    - Implemented testing throughout my code using `pytest`
## What went wrong
During the development process, several significant challenges emerged:
1. **Inefficiencies in Early Iterations**
    -  Tokenization logic was *very* slow, particularly when handling large files like PDFs.
        - Reason: The naïve implementation of substring matching caused repetitive searches through the sliding window.
        - Resolution: Added a `_find_subarray` helper function and optimized the loop structure to reduce unnecessary comparisons.
    - Early versions failed to check for the smallest valid token size (`control_byte_length`), which resulted in redundant matches for small runs.
2. **Handling Large Literal Buffers**
    - Literal buffer handling overflowed in cases where literals exceeded the maximum length encodable by a token.
	- Resolution: Added a mechanism to split and flush literals dynamically once they reached the maximum allowable size.
1. **Serialization Challenges**
	Let me say this was probably the most annoying issue to solve, the combination of me not fully understanding bitwise operations and the difficulty in analyzing raw bytes to find errors meant this part took a **loooonggg** time to get working.
    - Encountered issues when converting tokens into byte streams due to incorrect bit manipulation.
	- Resolution: Redesigned the encoding logic with detailed bit masks for signal flags, lengths, and distances.
    - Mismatches in decoding logic initially led to data corruption, requiring the addition of stricter validations for match distances and lengths.
3. **Edge Cases**
    - Struggled with edge cases, such as:
        - Files with repetitive patterns (resulted in excessive match lengths).
        - Extremely short files where compression overhead was greater than the original size.
    - Resolution: Introduced a heuristic to allocate bits differently when `control_byte_length = 1` since the default allocations where subpar. Effectively this check rounds up the amount of length bits from 2 to 3 bits which allows for compression to occur.

## What worked
1. **Clear Tokenization Logic**
	This was one of the earliest decisions I made and saved a **TON** of time since it seperated the tokenization and encoding steps into two distinct operations which made debugging easier.
    - Dividing tokens into `MatchToken` and `LiteralToken` provided clarity and modularity in the design.
    - Encapsulating the token creation logic (`_createPointer`, `_createLiteral`) improved maintainability and debugging.
3. **Dynamic Control Byte Configuration**
	Initially I used a hardcoded 2 byte control_byte size. However after testing I wondered if the control token size affected the compression ratio, so I began dynamically setting the window size(s) and other associated parameters to allow for control_byte_length between 2-15 bytes
    - Allowing the control byte size to scale dynamically with the input improved compression efficiency and adaptability.
    - The `_var_init` function simplified the calculation of dependent parameters like window size, lookahead buffer size, and maximum distances.
4. **Efficient Literal Buffer Management**
    - Buffering literals and only flushing them when necessary reduced the number of redundant tokens.

<div style="page-break-after: always;"></div>

# Command Line Interface
From the start I envisioned this project as a Command Line Interface and it was duly implemented. 
it accepts 3 flags
- `-c --compress [source] [dest*]`  Compress a file
- `-d --decompress [source] [dest*]` Decompress a file
- `-cb --control-bytes [int]` range 1,15 byte "control bytes" which dictate length of literal runs or pointers. Larger control bytes are only really practical for *highly* repetitive patterns due to the increased overhead. Default is 3 bytes.
\*dest. is optional; if dest. is not provided compressed file is written to the same directory
```sh
#Compress a file with -c --compress
python LZ77.py -c [source] 

#decompress a file -d --decompress
python LZ77.py -d [source].Z77

#compress with custom control byte length -cb --control-bytes
python LZ77.py -c [source] --control-bytes 2
```

<div style="page-break-after: always;"></div>

---
## Header
The header is a 2 byte bit of data prepended to a compressed file. It contains a 1 byte magic number, 4 bits to encode the `control_byte_length` and the final 4 bits dedicated to encoding common filetypes.
In Summary it does 3 things:
- Identify itself as an LZ77 compressed file (magic number)
- Tells the decoder how many control bytes it was encoded with
- Tells the decoder the file extension
Challenges
    - As I'd already written a most of my code when I realized I needed headers the challenge was modifying the rest of my code as little as possible to implement this. I ended up accomplishing this on both ends by just injecting it into front of the encoded stream and 'hiding' it from the decoder.
	- Resolution: Used a fixed magic number for validation and encoded the `control_byte_length` dynamically in the header.

![[Pasted image 20241214191920.png]]
This was my original header generator. The reserved bits become important later.

What worked:
- Implementing the header was one of the final steps I did. I realized that without the initial conditions (namely the `control_byte_length`) I would not know how to parse control_bytes. To remedy this I designed a header to prepend to the data which in addition to storing the `control_byte_length` also stores metadata confirming the file is compressed (the magic byte).

- While I was designing the header I included 4 extra bits at the end, originally I left these to encode potential flags, but I realized a better use of them would be to use the 4 bits to encode the original filetype extension. However, with 4 bits I couldn't encode the filetype as plaintext which would be a few bytes. Instead with $2^4=16$ unique combinations I could map 15 common filetypes and encode that information, with 4 lows just outputting a `.out` file

![[Pasted image 20241216212503.png]]
This is my updated `__generate_header()` function. It uses the previously unused 4 bits at the end to encode filetypes. I have an extension map in my class definition that we use to encode/decode the header.
```python
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
    0xB: ".xml"  
    # Add up to 16 extensions as needed  
}
```
Extension map I used to encode filetype into 4 bits

<div style="page-break-after: always;"></div>

---

# Data Structure
I realized that to encode my data I needed to reduce the overhead as much as possible (add as little superfluous data as possible).  I eventually landed on an implementation described below:
Consider an input
```python
raw_data = b"the quick brown fox the quick"
```
The encoded data is structured as a combination of literal runs for new sequences and match tokens for repeated sequences. For this example, the outputted data might look like:
```python
compressed_data = [("LITERAL",length=20, "the quick brown fox "),   ("MATCH", offset=20, length=9)]
```
The `LITERAL` token represents a direct copy of data that has not been previously encountered, while the `MATCH` token efficiently encodes repeated sequences by specifying the offset (backwards distance from the current position) and length (number of characters matched).

Additionally for decompression, since the amount of control_bytes is not fixed I insert a 2byte header at the front of the compressed data which contains metadata
The header consists of 3 parts
- 1 byte "magic byte" which identifies it as a compressed file and a
- 4 bit "control_byte_length" parameter which lets the decoder know how many control bytes to read.
- 4 bit flags: These are currently not used but if I were to implement compression or something else it would allow me to encode extra metadata in the compressed output.
The end of file is detected by noting when the input stream ends.
### Example compressed stream
Consider we wanted to compress `raw_data` 
the "raw" uncompressed stream is shown above a sample compressed stream with `control_byte_length=2`:
```python
raw_data = b"the quick brown fox the quick"
compressed_data = b"(\xC7\x21)(\x80\x14)the quick brown fox (\x8A\x14)
```
- `(\xC7\x21)` is the 2 byte header, it gets prepended to every compressed file. It has the magic number `\xC7` and the `control_byte_length` and `filetype` encoded in the 2nd byte
	- `\x2` is the control byte length, two in this case. As you can see subsequent *control bytes* are 2 bytes long
	- `\x1` is the filetype. A `.txt` file in this case
- `(\x80\x14)` is a **Literal Token**. It has the MSB set to 0 to show that it is a **literal token**. All the remaining bits in the control_byte can be used to encode the length of the literal run `\x21` = 20 bytes
- `(\x8A\x14)` is a **Match Token**. Its MSB is 1 to show that it is a Match token. The next 5 bits are the length of the match. Finally the remaining (10) bits are used to encode the backwards distance (in bytes) of the match so `length = 9, distance = 20`. If we select bytes  $\left[ 0:9 \right]=\left[ \mathbf{\text{CP}}-\text{length}:\mathbf{\text{CP}}-\text{length}+\text{distance} \right]$  we get `the quick`. Recall that $\mathbf{\text{CP}}$ is the **Coding Position**, the encoders current position in the **input stream**
<div style="page-break-after: always;"></div>

---
## Tokens
My code relies heavily on so called 'tokens' to store the information about matches and literals *before* they are serialized in `LZ77.encode()`
### LZ77.Tokenize()
The `Tokenize()` function is responsible for identifying and creating tokens, whether they are `MATCH` tokens for repeated sequences or `LITERAL` tokens for new data. It processes the input data sequentially, updating the sliding window and lookahead buffer as it iterates.

The function starts by searching for a 1-byte match and then attempts to extend this match by comparing the sliding window with the lookahead buffer to find the longest possible match. Once the longest match is identified, its length is compared against a threshold, `self.control_byte_length`. This parameter determines the minimum length required for a match to be encoded as a `MATCH` token. If the match length is smaller than the token threshold, the match is rejected, and the unmatched data is treated as a `LITERAL`.

Literals accumulate in a buffer until their combined size approaches the encoding limit for a token. When this limit is reached—either due to an impending overflow or because a valid match has been found further along—the accumulated literals are written out as a `LITERAL` token. Afterward, the function continues processing the data, alternating between literal runs and matches as appropriate.

This approach ensured efficient encoding by minimizing the overhead of literal runs and ensuring that a match actually reduces data size

### Match Token
The `MatchToken` class encapsulates the information required to represent a match in the LZ77 compression algorithm. A match token is used when a sequence of data in the lookahead buffer can be found as a contiguous substring in the sliding window (search buffer). This reduces redundancy by referencing the previous occurrence rather than storing the data again.
```python
@dataclass  
"""pydoc comments have been omitted for clarity"""
class MatchToken:  
    def __init__(self):  
		pass  
    dist: np.uint32 #(backwards) distance from current position to start of match  
    length: np.uint32 #length of match, in bytes  
    type: bool = field(default=True) #flag to identify token type, will always be true for matches
```
#### Attributes:
- **`dist`** (`np.uint32`):  
    The distance (in bytes) from the current position to the start of the matching substring in the search buffer.  
    _(Example: If `dist=5`, the match starts 5 bytes behind the current position.)_
    
- **`length`** (`np.uint32`):  
    The length (in bytes) of the match. This represents how many bytes can be copied from the reference in the search buffer.  
    _(Example: If `length=3`, the matching substring is 3 bytes long.)_
    
- **`type`** (`bool`):  
    A flag indicating the token type. For `MatchToken`, this is always `True`, used to differentiate it from other token types during encoding or decoding.
#### Purpose:
The `MatchToken` reduces storage by replacing repetitive sequences with a reference (distance and length) to a prior occurrence, effectively compressing the data.
### Literal Token
The `LiteralToken` class represents a sequence of raw bytes (literal data) in the LZ77 compression algorithm. A literal token is used when no matching substring of sufficient length is found in the sliding window, or when literals need to be output directly (e.g., at the start or end of the stream).
```python
@dataclass  
"""pydoc comments have been omitted for clarity"""
class LiteralToken:  
def __init__(self):  
		pass  
    length: np.uint32 #length of literal run, in bytes  
    data: np.array([], dtype=np.uint32) #literal run data thats being encoded  
    type: bool = field(default=False) #flag to identify token type, will alawys be false for literals
```
#### Attributes:
- **`length`** (`np.uint32`):  
    The number of bytes in the literal run. This defines the size of the `data` array and indicates how many bytes to copy directly during decoding.
- **`data`** (`np.array([], dtype=np.uint32)`):  
    An array containing the raw byte values of the literal run. Each element represents one byte of uncompressed data.
- **`type`** (`bool`):  
    A flag indicating the token type. For `LiteralToken`, this is always `False`, used to differentiate it from other token types during encoding or decoding.
#### Purpose:
The `LiteralToken` provides a way to include raw, uncompressed data in the output, ensuring that non-redundant or unmatched data is preserved in its original form.

<div style="page-break-after: always;"></div>
---
## Encoding/Decoding
### LZ77.encode()
The `encode` method serializes the compressed tokens (generated during the `tokenize` phase) into a byte stream suitable for storage or transmission. It incorporates metadata, such as the header, alongside the compressed data.
#### Key Features:
1. **Header Generation**: A 2-byte header is prepended to the byte stream to identify the compression format and store critical metadata, such as the `control_byte_length`.
2. **Token Serialization**:
    - **Match Tokens**: Encodes match length and distance using the control byte structure. The signal bit (MSB) is set to `1` to distinguish these tokens.
    - **Literal Tokens**: Encodes literal run lengths and the corresponding literal data. The signal bit (MSB) is set to `0` to distinguish these tokens.
3. **Efficient Bit Masking**: Uses bitwise operations to pack signal flags, lengths, and distances into compact control bytes, minimizing overhead.
#### Returns:
A `bytes` object representing the serialized compressed data, including the header and all tokens.

### LZ77.decode()
The `decode` method reconstructs the original data from a compressed byte stream. It reads and interprets the tokens (match and literal) and outputs the decompressed data.
#### Key Features:
1. **Header Parsing**: Extracts metadata, including `control_byte_length`, from the header and dynamically adjusts internal configurations.
2. **Token Deserialization**:
    - **Match Tokens**: Reads match length and distance to copy data from previously decompressed output.
    - **Literal Tokens**: Reads literal run lengths and appends the corresponding literal data directly to the output.
3. **Error Handling**: Validates token structure, ensuring matches reference valid positions in the decompressed output.
#### Returns:
A `bytes` object representing the fully decompressed original data.

### LZ77.compress() and LZ77.decompress()
Both these function are simply static definitions of the compression/decompression loop.
So they will call all the appropriate internal class calls to do the entire compression process.

<div style="page-break-after: always;"></div>
---
# Results

### CLI
My code worked to compress files, as originally envisioned it has a Command Line Interface and additionally a GUI
![[Pasted image 20241215173623.png]]
Compressing a few pages of raw text I had a compression ratio of $0.78$ while still being able to restore the data perfectly on the other side.

### GUI
My project also has a GUI to enable file compression. It uses pysimpleGUI to render the GUI
The GUI can be run using `python GUI.py`
## Initial State
In its initial state the user can use the file browser to find a file to either compress/decompress
![[Pasted image 20241215173932.png]]
Initial state of GUI

## File Compression
![[Pasted image 20241215174055.png]]
If the user selects a file that has not been compressed (determined by checking for a header) the GUI presents the Compress button and a counter to increment the amount of control bytes.
![[Pasted image 20241215174203.png]]

## File Decompression
![[Pasted image 20241215174229.png]]
If the user selects a file that is compressed (determined based off the header) the GUI will go into compression mode and display the appropriate controls.

The file type input box can be used to specify the decompressed filetype, although this option is disabled (like shown) if the file type is detected in the header.

![[Pasted image 20241215174358.png]]

## Compression
Frankly, I was a little disappointed here, I was hoping to be able to compress larger files like `.pdf`s and such and although *technically* I can, the tokenization algorithm is very slow and as such takes a long time to compress large files. Additionally, while trying to encode these files about ~20% of the time there will be an overflow error, I am unsure where this bug occurs as I cannot recreate it with small files; but if I had to guess I think it would be related to my pointers overflowing for extended literal runs. My code is supposed to flush the literal buffer when it gets too large but if my hypothesis is correct it *is* possible to overflow it regardless.

Despite the poor performance for large files, for `.txt` files or other "raw" text my code was sufficiently fast to compress.
### Quantitative Results
I decided to focus my testing on how *well* I could compress files. I determined this using the compression ratio, defined as Compressed_length/Raw_Length:
All of my files were compressed using the default `control_byte_length=3` bytes.

**Shakespeare's Antony and Cleopatra**: Act 1 Scene 1
This is what I consider typical speech with regular repetition, which can be matched and compressed. Sourced from [here](http://shakespeare.mit.edu/cleopatra/cleopatra.1.1.html)
- Raw Length: 3639 bytes
- Compressed Length: 583 bytes
- Compression Ratio: 0.1602

**Lorem ipsum dolor**
This is another smaller text file, we have a compression ration of less than %10!
- Raw Length: 445 bytes
- Compressed Length: 42 bytes
- Compression Ratio: 0.0944

**A really small string**
While testing I had a short test file that I would use to validate my process. The (complete) contents of the text file where:
```
RepeatingCharacters diffstring RepeatingCharacters 
stew newline Repeating Repeat Repeat
```
We can see that for such a short string there are few opportunities to shorten the file, add onto that the overhead from the header and control bytes and the compression ratio gets worse.
- Raw Length: 92 bytes
- Compressed Length: 71 bytes
- Compression Ratio: 0.7717

**My Compressed, Compressible Aerodynamics notes**:
I thought this was a funny pun, so I decided to compress a page of my ENAE311 notes about airfoils to see how well it could handle a relatively large file. Additionally this file is a markdown file which means it has control characters of its own, a good test for my algorithm to make sure the I/O is sanitized.
- Raw Length: 8639
- Compressed Length: 1107
- Compression Ratio: 0.1281

**Average Results**
- Average Raw Length: 3203.75 bytes
- Average Compressed Length: 450.75 bytes
- Average Compression Ratio: 0.2866

Although by no means a comprehensive analysis of my compression algorithm I think this analysis shows some of the behavior of my code and validates that it does in fact compress files.

With more time (and a faster algorithm) I would have liked to do performance testing across a range of `control_byte_length`s, File sizes and file types.
<div style="page-break-after: always;"></div>
---
# Concepts Learned
- Bitwise operations
	- My project dealt with binary data/bytes directly and as such bitwise operations were often the *easiest* way to assign variables or pick out certain bits from headers/control_bytes
	- Many many hours were spent deciding if `>>` or `<<` was the appropriate operator.
- Pattern Matching
	- This was an important part of tokenizing my data as my compression relies on being able to effectively find and extend repeating patterns. A more fleshed out project would have put a lot more effort here as this was the single slowest part of my code. Who knew finding patterns was so hard?
- Argument Parsing
	- Can you believe this is the first time I've implemented argument parsing? Admittedly chat-GPT was invaluable for debugging the argument parsing, but still, I'm proud of having been able to create a CLI like originally envisioned and the Argument parsing was a key part of that.
- Pytests
	- Another thing I implemented for the first time in this project was pytests. I don't think I've discovered the full potential of this tool but even in the limited fashion I used it my tests were very valuable for being able to quickly test edge cases and isolate functions to test them.
	- With more time I would have refined the tests and used them to validate more parts of my code (testing argument parsing was wickedly hard and ended up stumping me)
```python
def test_tokenize_simple_pattern():  
    """  
    Test tokenization with a simple repeated pattern.    """    raw_data = b"coolcoolcool"  # Repeated pattern  
    lz = LZ77(raw_data, control_bytes=2)  
    lz.tokenize()  
  
    # Assert that the first token is a LiteralToken  
    first_token = lz.compressed_data[0]  
    assert isinstance(first_token, LiteralToken), "Expected the first token to be a LiteralToken."  
    assert first_token.length == 4, f"Expected first literal length of 4, got {first_token.length}."  
    assert first_token.data == list(b"cool"), "Expected literal data to be 'cool'."  
  
    # Assert that subsequent token is MatchTokens  
    second_token = lz.compressed_data[2]  
    assert isinstance(second_token, MatchToken), "Expected subsequent tokens to be MatchTokens."  
    assert second_token.length == 3, f"Expected match length of 3, got {second_token.length}."  
    assert second_token.dist > 0, f"Expected a non-zero distance, got {second_token.dist}."
```
Example pytest function, this example is testing the tokenization function to verify functionality.

- Pydoc
	- Obviously well commented code is important, but Pydoc helps simplify generating documentation for the functions within my code. Although you (the grader) likely won't end up needing the documentation even having spent the time to write them out in my code helped a lot when returning to old code and trying to decipher what exactly It does/returns.
	- ![[Pasted image 20241215180931.png]]
	Example pydoc generated documentation, the source comments are imbedded directly into my code.
---
# Retrospective
With the power of 20/20 hindsight I think I would have focused my efforts entirely on file compression. Encryption although interesting would have posed a far greater challenge because an 'old' Encryption scheme is likely to provide trivial security in a modern context while a more modern one, I realized, would have taken me significantly longer to accomplish without using an already publicly available encryption suite. Following the encryption quick-start guide seemed to not really be in spirit of the project so I dropped it. However, If I had more time to implement my project I would have liked to explore the Encryption side of the challenge more and implement a dual compression/encryption algorithm



#### Things I would have liked to do

- I would have also liked to optimize my compression and code more. The **Tokenization algorithm** is quite slow and file larger than a few kb would take uncomfortably long to compress. I think this was in part due to the amount of operation I was doing trying to match and extend patterns.

- One glaring inefficiency in my code is that `control_byte_length` is static throughout the compression algorithm, which means that often my controlbytes have *a lot* of zero's / unused bits. With more time I would have liked to make the `control_byte_length` a maximum upper limit rather than the only size. This would mean that I could encode short literals/matches in fewer bytes. I think the benefit from implementing this would be in files with many short spaced repeating patterns as smaller token size would be most felt in a file that needs many tokens to be compressed.

- Finally If I had started this project again I would have done a little bit more of the documentation/design process more throughout the semester rather than doing it all over this past weekend.

In short I would have liked to:
- Implement a more efficient substring search algorithms (e.g., KMP or Rabin-Karp) 
- Utilize dynamic programming techniques to reduce computational complexity 
- Explore adaptive control byte sizing to minimize encoding overhead