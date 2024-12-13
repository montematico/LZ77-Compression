import pytest
import os
from FileIO import FileIO

@pytest.fixture
def temp_file(tmp_path):
    """
    Fixture to create a temporary file and return its path.
    """
    temp = tmp_path / "temp_file.txt"
    temp.write_bytes(b"Temporary file content")
    return temp

def test_read_valid_file(temp_file):
    """
    Test reading a valid file.
    """
    data = FileIO.read(temp_file)
    assert data == b"Temporary file content", "File content does not match expected data."

def test_read_nonexistent_file():
    """
    Test attempting to read a nonexistent file.
    """
    with pytest.raises(RuntimeError, match="Failed to read from"):
        FileIO.read("nonexistent_file.txt")

def test_write_valid_file(tmp_path):
    """
    Test writing data to a file.
    """
    file_path = tmp_path / "output_file.txt"
    FileIO.write(b"Test data", file_path)

    # Verify the file was written
    with open(file_path, "rb") as f:
        content = f.read()
    assert content == b"Test data", "Written data does not match expected content."

def test_write_to_invalid_path():
    """
    Test attempting to write to an invalid path.
    """
    with pytest.raises(RuntimeError, match="Failed to write to"):
        FileIO.write(b"Test data", "/invalid_path/output_file.txt")

def test_read_empty_file(tmp_path):
    """
    Test reading from an empty file.
    """
    empty_file = tmp_path / "empty_file.txt"
    empty_file.write_bytes(b"")

    data = FileIO.read(empty_file)
    assert data == b"", "Expected empty data but got non-empty content."

def test_write_empty_data(tmp_path):
    """
    Test writing empty data to a file.
    """
    file_path = tmp_path / "empty_data_file.txt"
    FileIO.write(b"", file_path)

    # Verify the file was written as empty
    with open(file_path, "rb") as f:
        content = f.read()
    assert content == b"", "Expected empty file but got non-empty content."
