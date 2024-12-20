import PySimpleGUI as sg
from LZ77 import LZ77
from FileIO import FileIO as fio
import os

class GUI:
    def __init__(self):
        """
        Main GUI loop, displays the main menu of the GUI and handles events.
        :return: None
        """
        self.extension = ".out"
        layout = [
            [sg.Text("Select a file to load")],
            [
                sg.Input(key="-FILE-", enable_events=True),
                sg.FileBrowse(initial_folder=".", key="-BROWSE-", tooltip="Select a file, any file!")
            ],
            [
                sg.Button("Compress", key="-COMPRESS-", visible=False),
                sg.Text("Control Bytes:",visible=False,k="-CbyteText-"),sg.Spin([i for i in range(1, 16)], initial_value=2, key="-CONTROL_BYTES-", visible=False)
            ],
            [
                sg.Button("Decompress", key="-DECOMPRESS-", visible=False),
                sg.Text("File Type:", visible=False, key="-FILETYPE_TEXT-"),
                sg.Input(default_text=".txt", key="-FILETYPE-", size=(10, 1), visible=False)
            ],
            [sg.Button("Submit",k="-SUBMIT-")],
            [sg.Button("Exit")]
        ]

        window = sg.Window("Mikas Super Cool File Compressor", layout)

        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == "Exit":
                break
            elif event == "-SUBMIT-":
                file_path = values["-FILE-"]
                if not file_path:
                    sg.popup("Please select a file.", title="Error")
                    continue
                # Perform header check and update GUI
                self.header_check(file_path, window)
            elif event == "-COMPRESS-":
                # Compression logic
                file_path = values["-FILE-"]
                control_bytes = values["-CONTROL_BYTES-"]
                root, extension = os.path.splitext(file_path)
                compressed = LZ77.compress(fio.read(file_path),control_bytes,extension)

                sg.popup("Compression complete!", title="Success")

                #Write the compressed data in the same directory as the original file

                fwrite_path = root + ".Z77"
                fio.write(compressed, fwrite_path)
                self.main_menu(window)
            elif event == "-DECOMPRESS-":
                # Decompression logic
                file_path = values["-FILE-"]
                decompressed, extension = LZ77.decompress(fio.read(file_path))
                sg.popup("Decompression complete!", title="Success")

                #Write the decompressed data in the same directory as the original file
                root, _ = os.path.splitext(file_path)
                fwrite_path = root + extension
                fio.write(decompressed, fwrite_path)
                self.main_menu(window)

        window.close()


    @staticmethod
    def header_check(file_path, window):
        """
        Checks the file header and updates the GUI by hiding or showing elements dynamically.
        :param file_path: The path to the file to check.
        :param window: The PySimpleGUI window object.
        """
        #Removing a bunch of elements we don't need anymore
        window["-SUBMIT-"].update(visible=False)
        window["-BROWSE-"].update(visible=False)
        #window["-FILE-"].update(visible=False)

        is_compressed, extension = LZ77.verify_header(file_path)
        #Adding the new elements based on if the file is compressed or not (reading the 2 byte header)
        if is_compressed:
            # File has a valid header: Hide "Compress" and "Encrypt" buttons, show "Decompress" and "Decrypt" buttons
            #Decompression window elements
            window["-DECOMPRESS-"].update(visible=True)
            window["-FILETYPE_TEXT-"].update(visible=True)
            window["-FILETYPE-"].update(visible=True)
            window["-FILETYPE-"].update(value=extension, visible=True, disabled=True)  # Set the value and disable the input

            #Compression elements
            window["-CbyteText-"].update(visible=False)
            window["-CONTROL_BYTES-"].update(visible=False)
            window["-COMPRESS-"].update(visible=False)
        else:
            # File does not have a valid header: Hide "Decompress" and "Decrypt" buttons, show "Compress" and "Encrypt" buttons
            window["-DECOMPRESS-"].update(visible=False)
            window["-FILETYPE_TEXT-"].update(visible=False)
            window["-FILETYPE-"].update(value=".txt", visible=False, disabled=False)  # Reset to default and re-enable

            window["-COMPRESS-"].update(visible=True)
            window["-CbyteText-"].update(visible=True)
            window["-CONTROL_BYTES-"].update(visible=True)

    def main_menu(self,window):
        window["-SUBMIT-"].update(visible=True)
        window["-BROWSE-"].update(visible=True)
        window["-FILE-"].update(visible=True)

        # Compression elements
        window["-CbyteText-"].update(visible=False)
        window["-CONTROL_BYTES-"].update(visible=False)
        window["-COMPRESS-"].update(visible=False)
        #Decompression Elements
        window["-DECOMPRESS-"].update(visible=False)
        window["-FILETYPE_TEXT-"].update(visible=False)
        window["-FILETYPE-"].update(value="",visible=False,disabled=False)


if __name__ == "__main__":
    g = GUI()