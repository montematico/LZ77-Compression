import pytest
import os
import logging

from Tools.demo.eiffel import Tests

from LZ77 import LZ77

import pytest
from LZ77 import LZ77, MatchToken, LiteralToken


@pytest.fixture
def txt_data():
    """
    Fixture to read a text file.
    :return: loaded txt data
    """
    with open(os.path.join(os.path.dirname(__file__), "test_data", "act1scene1.txt"), "rb") as f:
        return f.read()

@pytest.fixture
def data_short():
    """
    Fixture to read a text file.
    :return: loaded txt data
    """
    with open(os.path.join(os.path.dirname(__file__), "test_data", "short.txt"), "rb") as f:
        return f.read()

@pytest.fixture
def pdf_data():
    """
    Fixture to read a PDF file.
    :return: loaded pdf data
    """
    with open(os.path.join(os.path.dirname(__file__), "test_data", "testpdf.pdf"), "rb") as f:
        return f.read()

@pytest.fixture
def temp_file(tmp_path):
    """
    Fixture to create a temporary file and return its path.
    """
    temp = tmp_path / "temp_file.txt"
    temp.write_bytes(b"Temporary file content")
    return temp
@pytest.fixture(autouse=True)
def reset_lz77():
    """
       Reset the LZ77 class between tests to ensure no residual state is carried over.
       """
    # Reset class-level attributes
    LZ77.compressed_data = []
    LZ77.literal_buffer = []

    # Optionally reset other shared/global states (e.g., logging)
    logging.getLogger("LZ77").handlers.clear()
    logging.basicConfig(level=logging.WARNING)

    # Yield control for test execution
    yield

    # Final cleanup if needed (e.g., temporary file cleanup, etc.)


def test_first_token_is_literal(data_short):
    """
    Test that the first token generated by tokenize is always a LiteralToken.
    """
    raw_data = data_short
    lz = LZ77(raw_data, control_bytes=3)
    lz.tokenize()

    first_token = lz.compressed_data[0]

    assert isinstance(first_token, LiteralToken), "The first token should always be a LiteralToken."
    assert first_token.length > 0, "The first token should contain raw data."
    assert first_token.data[0] == raw_data[0], "The first token should contain the first byte of raw_data."


def test_tokenize_simple_pattern():
    """
    Test tokenization with a simple repeated pattern.
    """
    raw_data = b"coolcoolcool"  # Repeated pattern
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


@pytest.mark.parametrize("control_bytes", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def test_tokenize_mixed_literals_and_patterns_short(data_short,control_bytes):
    """
    Test tokenization with a mix of literals and repeated patterns.
    """
    raw_data = data_short  # Mix of unique and repeated patterns
    lz = LZ77(raw_data, control_bytes=control_bytes)
    lz.tokenize()

    # Assert tokens are a mix of literals and matches
    assert len(lz.compressed_data) > 1, "Expected multiple tokens."
    print("Control Byte size:", control_bytes)
    assert isinstance(lz.compressed_data[0], LiteralToken), f"Expected the first token to be a LiteralToken \n Control Byte size:  {control_bytes}"
    for token in lz.compressed_data[1:]:
        assert isinstance(token, (LiteralToken,
                                  MatchToken)), f"Expected tokens to be either LiteralToken or MatchToken \n Control Byte size:  {control_bytes}"


@pytest.mark.parametrize("control_bytes", [1, 2, 3, 4])
def test_tokenize_mixed_literals_and_patterns_long(txt_data,control_bytes):
    """
    Test tokenization with a mix of literals and repeated patterns. longer test data
    """
    raw_data = txt_data  # Mix of unique and repeated patterns
    lz = LZ77(raw_data, control_bytes=control_bytes)
    lz.tokenize()

    # Assert tokens are a mix of literals and matches
    assert len(lz.compressed_data) > 1, "Expected multiple tokens."
    print("Control Byte size:", control_bytes)
    assert isinstance(lz.compressed_data[0], LiteralToken), f"Expected the first token to be a LiteralToken \n Control Byte size:  {control_bytes}"
    # Assert that subsequent tokens are either LiteralToken or MatchToken
    for token in lz.compressed_data[1:]:
        assert isinstance(token, (LiteralToken,
                                  MatchToken)), f"Expected tokens to be either LiteralToken or MatchToken \n Control Byte size:  {control_bytes}"


def test_tokenize_large_pattern_txt(txt_data):
    """
    Test tokenization with a large repeated pattern that exceeds control_byte_length.
    """
    raw_data = txt_data  # Large repeated pattern
    lz = LZ77(raw_data, control_bytes=3)
    lz.tokenize()

    # Assert that match tokens are created for repeated patterns
    assert len(lz.compressed_data) > 0, "Expected tokens to be created."
    for token in lz.compressed_data:
        assert isinstance(token, (MatchToken, LiteralToken)), "Expected tokens to be MatchToken or LiteralToken."

def test_tokenize_pdf(pdf_data):
    """
    Test tokenization of a pdf file (raw binary data).
    """
    raw_data = pdf_data  # Large repeated pattern
    lz = LZ77(raw_data, control_bytes=2)
    lz.tokenize()

    # Assert that match tokens are created for repeated patterns
    assert len(lz.compressed_data) > 0, "Expected tokens to be created."
    for token in lz.compressed_data:
        assert isinstance(token, (MatchToken, LiteralToken)), "Expected tokens to be MatchToken or LiteralToken."


def test_tokenize_no_patterns():
    """
    Test tokenization with no repeated patterns (all literals).
    """
    raw_data = b"ABCDEFGHIJKLMNOPabcdefghijklmnop"  # Unique data
    lz = LZ77(raw_data, control_bytes=3)
    lz.tokenize()

    # Assert that only literal tokens are created
    assert len(lz.compressed_data) == 1, "Expected a single literal token."
    token = lz.compressed_data[0]
    assert isinstance(token, LiteralToken), "Expected a LiteralToken."
    assert token.length == len(raw_data), f"Expected length {len(raw_data)}, got {token.length}."

def test_tokenize_minimum_match_length():
    """
    Test tokenization with a repeated pattern shorter than control_byte_length.
    """
    raw_data = b"AAB"  # Pattern shorter than control_byte_length
    lz = LZ77(raw_data, control_bytes=3)
    lz.tokenize()

    # Assert that the repeated pattern is treated as literals
    assert len(lz.compressed_data) == 1, "Expected a single literal token."
    token = lz.compressed_data[0]
    assert isinstance(token, LiteralToken), "Expected a LiteralToken."
    assert token.length == len(raw_data), f"Expected length {len(raw_data)}, got {token.length}."


def test_compress_decompress_valid(txt_data):
    """
    Test the compress and decompress functions with valid inputs.
    """
    raw_data = txt_data
    control_bytes = 3

    compressed = LZ77.compress(raw_data, control_bytes=control_bytes)
    decompressed = LZ77.decompress(compressed)

    assert decompressed == raw_data, "Decompressed data does not match the original data."

@pytest.mark.parametrize("control_bytes", [1, 2, 3, 4, 5,6,7,8,9,10])
def test_compression_ratio(txt_data,control_bytes):
    """
    Test that compression occurs for various control_byte_lengths
    """
    raw_data = txt_data
    compressed = LZ77.compress(raw_data, control_bytes=control_bytes)
    assert len(compressed) < len(raw_data), f"Expected compressed data to be smaller than raw data. Control Byte size:  {control_bytes}"

@pytest.mark.parametrize("control_bytes", [0, 16])
def test_invalid_control_byte_length(data_short,control_bytes):
    """
    Test invalid control_byte_length values.
    """
    raw_data = data_short
    with pytest.raises(ValueError, match="control_byte_length must be between 1 and 15."):
        LZ77.compress(raw_data, control_bytes=control_bytes)

@pytest.mark.parametrize("control_bytes", [1, 15, 13])
def test_edge_control_byte_length(data_short,control_bytes):
    """
    Test edge cases for control_byte_length.
    """
    raw_data = data_short
    compressed = LZ77.compress(raw_data, control_bytes=control_bytes)
    decompressed = LZ77.decompress(compressed)

    assert decompressed == raw_data, f"Decompressed data mismatch for control_bytes={control_bytes}"

def test_compress_empty_data():
    """
    Test compressing and decompressing empty data.
    """
    raw_data = b""
    compressed = LZ77.compress(raw_data, control_bytes=3)
    decompressed = LZ77.decompress(compressed)

    assert decompressed == raw_data, "Empty data compression/decompression failed."

def test_decompress_invalid_header():
    """
    Test decompressing data with an invalid header.
    """
    invalid_data = b"\x00\x00InvalidHeader"
    with pytest.raises(ValueError, match="Invalid magic number. Not an LZ77-compressed stream."):
        LZ77.decompress(invalid_data)

def test_decompress_truncated_data():
    """
    Test decompressing truncated data.
    """
    truncated_data = b"\xC7\x30"  # Valid header but missing compressed content
    with pytest.raises(ValueError, match="Compressed stream is too short to contain a valid header."):
        LZ77.decompress(truncated_data)

def test_verify_header():
    """
    Test the verify_header static method.
    """
    valid_data = b"\xC7\x30SomeCompressedData"
    invalid_data = b"\x00\x00InvalidHeader"

    # Mock a file for valid header
    with open("valid_compressed_file.bin", "wb") as f:
        f.write(valid_data)

    # Mock a file for invalid header
    with open("invalid_compressed_file.bin", "wb") as f:
        f.write(invalid_data)

    assert LZ77.verify_header("valid_compressed_file.bin") is True, "Valid header not recognized."
    assert LZ77.verify_header("invalid_compressed_file.bin") is False, "Invalid header not recognized."

    # Cleanup
    import os
    os.remove("valid_compressed_file.bin")
    os.remove("invalid_compressed_file.bin")
