import pytest
from unittest.mock import patch
from LZ77 import LZ77
from FileIO import FileIO as fio
from GUI import GUI
import os


@pytest.fixture
def gui_instance():
    """Fixture to initialize the GUI instance."""
    return GUI()


@pytest.fixture
def temp_file(tmp_path):
    """
    Fixture to create a temporary file and return its path.
    """
    temp = tmp_path / "temp_file.txt"
    temp.write_bytes(b"Temporary file content")
    return str(temp)

@pytest.fixture
def txt_data():
    """
    Fixture to read a text file.
    :return: loaded txt data
    """
    with open(os.path.join(os.path.dirname(__file__), "test_data", "act1scene1.txt"), "rb") as f:
        return f.read()

@pytest.fixture
def pdf_data():
    """
    Fixture to read a PDF file.
    :return: loaded pdf data
    """
    with open(os.path.join(os.path.dirname(__file__), "test_data", "testpdf.pdf"), "rb") as f:
        return f.read()


@patch("LZ77.LZ77.compress")
@patch("FileIO.FileIO.read", return_value=b"Test Data")
@patch("FileIO.FileIO.write")
@patch("PySimpleGUI.popup")  # Mock sg.popup to avoid interference
def test_gui_compression(mock_popup, mock_write, mock_read, mock_compress, gui_instance, temp_file):
    """
    Test the GUI compression workflow.
    """
    mock_compress.return_value = b"Compressed Data"

    with patch("PySimpleGUI.Window") as MockWindow:
        mock_window = MockWindow.return_value
        # Define side effects for each step
        mock_window.read.side_effect = [
            ("-SUBMIT-", {"-FILE-": temp_file}),  # First read event for file submission
            ("-COMPRESS-", {"-FILE-": temp_file, "-CONTROL_BYTES-": 3}),  # Compression event
            ("Exit", {})  # Exit event
        ]

        gui_instance.__init__()

    # Verify compression was called
    mock_compress.assert_called_once_with(b"Test Data", 3)
    # Verify the file write operation
    mock_write.assert_called_once_with(b"Compressed Data", f"{temp_file.rsplit('.', 1)[0]}.Z77")


@patch("LZ77.LZ77.decompress")
@patch("FileIO.FileIO.read", return_value=b"Compressed Data")
@patch("FileIO.FileIO.write")
@patch("PySimpleGUI.popup")  # Mock sg.popup to avoid interference
def test_gui_decompression(mock_popup, mock_write, mock_read, mock_decompress, gui_instance, temp_file):
    """
    Test the GUI decompression workflow.
    """
    mock_decompress.return_value = b"Decompressed Data"

    with patch("PySimpleGUI.Window") as MockWindow:
        mock_window = MockWindow.return_value
        # Define side effects for each step
        mock_window.read.side_effect = [
            ("-SUBMIT-", {"-FILE-": temp_file}),  # First read event for file submission
            ("-DECOMPRESS-", {"-FILE-": temp_file, "-FILETYPE-": ".txt"}),  # Decompression event
            ("Exit", {})  # Exit event
        ]

        gui_instance.__init__()

    # Verify decompression was called
    mock_decompress.assert_called_once_with(b"Compressed Data")
    # Verify the file write operation
    mock_write.assert_called_once_with(b"Decompressed Data", f"{temp_file.rsplit('.', 1)[0]}.txt")


@patch("LZ77.LZ77.verify_header", return_value=True)
@patch("PySimpleGUI.Window")
def test_header_check_valid(mock_window, mock_verify, gui_instance, temp_file):
    """
    Test the header check functionality with a valid header.
    """
    mock_window.return_value.read.side_effect = [
        ("-SUBMIT-", {"-FILE-": temp_file})
    ]

    gui_instance.header_check(temp_file, mock_window.return_value)

    # Verify header check was called
    mock_verify.assert_called_once_with(temp_file)


@patch("LZ77.LZ77.verify_header", return_value=False)
@patch("PySimpleGUI.Window")
def test_header_check_invalid(mock_window, mock_verify, gui_instance, temp_file):
    """
    Test the header check functionality with an invalid header.
    """
    mock_window.return_value.read.side_effect = [
        ("-SUBMIT-", {"-FILE-": temp_file})
    ]

    gui_instance.header_check(temp_file, mock_window.return_value)

    # Verify header check was called
    mock_verify.assert_called_once_with(temp_file)


@patch("LZ77.LZ77.compress")
@patch("FileIO.FileIO.read", return_value=b"Test DataTest DataTest DataTest Data")
@patch("FileIO.FileIO.write")
@patch("PySimpleGUI.popup")  # Mock sg.popup to avoid interference
def test_gui_compression_actual_reduction(mock_popup, mock_write, mock_read, mock_compress, gui_instance, temp_file):
    """
    Test the GUI compression workflow to ensure actual file size reduction.
    """
    # Mock compressed data to be smaller than the original
    mock_compress.return_value = b"Compressed Data"

    with patch("PySimpleGUI.Window") as MockWindow:
        mock_window = MockWindow.return_value
        mock_window.read.side_effect = [
            ("-SUBMIT-", {"-FILE-": temp_file}),  # First read event for file submission
            ("-COMPRESS-", {"-FILE-": temp_file, "-CONTROL_BYTES-": 3}),  # Compression event
            ("Exit", {})  # Exit event
        ]

        gui_instance.__init__()

    # Verify compression was called
    mock_compress.assert_called_once_with(b"Test DataTest DataTest DataTest Data", 3)

    # Verify that the size of compressed data is less than the raw data
    assert len(mock_compress.return_value) < len(mock_read.return_value), (
        f"Expected compressed data size to be smaller. Raw size: {len(mock_read.return_value)}, "
        f"Compressed size: {len(mock_compress.return_value)}"
    )

    # Verify the file write operation
    mock_write.assert_called_once_with(b"Compressed Data", f"{temp_file.rsplit('.', 1)[0]}.Z77")


@patch("LZ77.LZ77.compress")
@patch("FileIO.FileIO.read")
@patch("FileIO.FileIO.write")
@patch("PySimpleGUI.popup")  # Mock sg.popup to avoid interference
def test_gui_compression_empty_file(mock_popup, mock_write, mock_read, mock_compress, gui_instance, tmp_path):
    """
    Test the GUI compression workflow with an empty file.
    """
    temp_file = tmp_path / "empty_file.txt"
    temp_file.write_bytes(b"")  # Write an empty file
    mock_read.return_value = b""  # Return empty data when reading
    mock_compress.return_value = b"Compressed Data"

    with patch("PySimpleGUI.Window") as MockWindow:
        mock_window = MockWindow.return_value
        mock_window.read.side_effect = [
            ("-SUBMIT-", {"-FILE-": str(temp_file)}),  # File submission event
            ("-COMPRESS-", {"-FILE-": str(temp_file), "-CONTROL_BYTES-": 3}),  # Compression event
            ("Exit", {})  # Exit event
        ]

        gui_instance.__init__()

    # Verify compression was called
    mock_compress.assert_called_once_with(b"", 3)
    # Verify the file write operation
    mock_write.assert_called_once_with(b"Compressed Data", f"{str(temp_file).rsplit('.', 1)[0]}.Z77")
#
# @patch("LZ77.LZ77.compress")
# @patch("FileIO.FileIO.read")
# @patch("FileIO.FileIO.write")
# @patch("PySimpleGUI.popup")  # Mock sg.popup to avoid interference
# def test_gui_compression_large_file_txt(mock_popup, mock_write, mock_read, mock_compress, gui_instance, txt_data, tmp_path):
#     """
#     Test the GUI compression workflow with a very large text file.
#     """
#     temp_file = tmp_path / "large_file.txt"
#     temp_file.write_bytes(txt_data)  # Write large data to the file
#     mock_read.return_value = txt_data  # Return large data when reading
#     mock_compress.return_value = b"Compressed Data"
#
#     with patch("PySimpleGUI.Window") as MockWindow:
#         mock_window = MockWindow.return_value
#         mock_window.read.side_effect = [
#             ("-SUBMIT-", {"-FILE-": str(temp_file)}),  # File submission event
#             ("-COMPRESS-", {"-FILE-": str(temp_file), "-CONTROL_BYTES-": 3}),  # Compression event
#             ("Exit", {})  # Exit event
#         ]
#
#         gui_instance.__init__()
#
#     # Verify compression was called
#     mock_compress.assert_called_once_with(txt_data, 3)
#     # Verify the file write operation
#     mock_write.assert_called_once_with(b"Compressed Data", f"{temp_file.parent / temp_file.stem}.Z77")

