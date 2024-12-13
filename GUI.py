import PySimpleGUI as sg
from LZ77 import LZ77
from FileIO import FileIO as fio

class GUI:
    def __init__(self):
        pass

    @staticmethod
    def header_check(file_path, window):
        """
        Checks the file header and updates the GUI by hiding or showing elements dynamically.
        """
        #Removing a bunch of elements we don't need anymore
        window["-SUBMIT-"].update(visible=False)
        window["-BROWSE-"].update(visible=False)
        #window["-FILE-"].update(visible=False)

        #Adding the new elements based on if the file is compressed or not (reading the 2 byte header)
        if LZ77.verify_header(file_path):
            # File has a valid header: Hide "Compress" and "Encrypt" buttons, show "Decompress" and "Decrypt" buttons
            window["-COMPRESS-"].update(visible=False)
            window["-ENCRYPT-"].update(visible=False)
            window["-DECOMPRESS-"].update(visible=True)
            window["-DECRYPT-"].update(visible=True)

            #Compression logic
            lz = LZ77.LZ77(fio.Read(file_path)) #inits LZ77 encoder
            lz.compress() #compresses the file



        else:
            # File does not have a valid header: Hide "Decompress" and "Decrypt" buttons, show "Compress" and "Encrypt" buttons
            window["-DECOMPRESS-"].update(visible=False)
            window["-DECRYPT-"].update(visible=False)
            window["-COMPRESS-"].update(visible=True)
            window["-ENCRYPT-"].update(visible=True)


    def main_menu(self):
        layout = [
            [sg.Text("Select a file to load")],
            [
                sg.Input(key="-FILE-", enable_events=True),
                sg.FileBrowse(initial_folder=".", key="-BROWSE-", tooltip="Select a file, any file!")
            ],
            [sg.Button("Compress", key="-COMPRESS-", visible=False)],
            [sg.Button("Encrypt", key="-ENCRYPT-", visible=False)],
            [sg.Button("Decompress", key="-DECOMPRESS-", visible=False)],
            [sg.Button("Decrypt", key="-DECRYPT-", visible=False)],
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

        window.close()


# Example usage
if __name__ == "__main__":
    gui = GUI()
    gui.main_menu()
