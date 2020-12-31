from Helper import main_function
import PySimpleGUI as sg
import os
import time
import threading
from src.utils.txtDatabaseHandling import dict_to_json
from src.utils.general import url_validator, artwork_url_verifier, image_counter, save_dir_global, successful_download_dict


root_dir = os.path.dirname(os.path.abspath(__file__))

class ProgVars:
    def __init__(self):
        self.url = None
        self.save_location = root_dir
        self.username = None
        self.password = None
        self.threads = 3


# Helper function for the collapsable section
def collapse(layout, key, visible):
    return sg.pin(sg.Column(layout, key=key, visible=visible))


# Threading Helper Functions
def call_main_function(arguments, _window):
    main_function(arguments)
    _window.write_event_value("-THREAD DONE-", '')


# Threading Helper Functions
def main_function_threading(arguments, _window):
    threading.Thread(target=call_main_function, args=(arguments, _window), name=main_function, daemon=True).start()


# Layout code starts here

SYMBOL_UP =    '▲'
SYMBOL_DOWN =  '▼'

sg.SetOptions(background_color='#262626',
           text_color='#CBCBCB',
           text_element_background_color='#262626',
           element_background_color='#2169B9',
           element_text_color='#CBCBCB',
           scrollbar_color=None,
           input_elements_background_color='#F7F3EC',
           progress_meter_color = ('#2169B9', '#DEECFB'),
           button_color=('#CBCBCB','#2169B9'))

_18_plus_Layout = [[sg.Text("Username", size=(15, 1)), sg.InputText('', key='username')],
                   [sg.Text('Password', size=(15, 1)), sg.InputText('', key='password', password_char='*')]]

debug_window_layout = [[sg.T("Debug Window", key="-DEBUG WINDOW-")],
                       [sg.Output(key="output_box", size=(75, 20))]]

download_button = [[sg.Button('Download')]]

progress_bar_layout = [[sg.ProgressBar(100, orientation='h', size=(50, 20), key="progress_bar")],
                       [sg.Text("0%", size=(4, 0), pad=((530, 0), (7, 0)), justification='left', key='counter')]]

layout = [[sg.Text("Please enter the Artist URL.")],
[sg.Text('Artist URL', size=(15, 1)), sg.InputText('', key="URL")],
[sg.Text('Output', size=(15, 1)), sg.Input(), sg.FolderBrowse(initial_folder=root_dir, key="save_dir")],
[sg.Text("Thread count", size=(15, 1)), sg.Slider(range=(1,7), orientation='h', size=(35, 15), default_value=3, key="threads")],
[sg.T(SYMBOL_DOWN, enable_events=True, k='-OPEN 18+-', text_color='white'), sg.T('18+ Section', enable_events=True, text_color='#ef3939', k='-OPEN 18+-TEXT')],
[collapse(_18_plus_Layout, '-18+-', False)],
[collapse(debug_window_layout, '-DEBUG-', False)],
[collapse(progress_bar_layout, '-PROGRESS BAR-', False)],
[collapse(download_button, '-DOWNLOAD-', True), sg.CloseButton('Close')]]

window = sg.Window('Artwork Downloader ʙʏ RᴇᴛR0', layout=layout, icon="icon/icon.ico", finalize=True)
progress_bar = window.Element("progress_bar")
# Layout Code Ends Here

# Main Event Loop

# Staring conditions of PINNED elements
opened = False
debug_window = False
download_button_bool = True
progress_bar_bool = False

while True:
    # Event Loop
    event, values = window.read(timeout=100)

    if event == sg.WIN_CLOSED or event == 'Close':
        if save_dir_global.save_dir is not "" and successful_download_dict:
            dict_to_json(successful_download_dict, save_dir_global.save_dir, 'successful_download.json')
        break

    if event.startswith('-OPEN 18+-'):
        opened = not opened
        window['-OPEN 18+-'].update(SYMBOL_DOWN if opened else SYMBOL_UP)
        window['-18+-'].update(visible=opened)

    if event == "Download":
        # Sanitization of Input :(
        if values["URL"] == '':
            sg.popup_error("Artist URL cannot be empty.")

        elif not url_validator(values["URL"]):
            sg.popup_error("Enter a Valid URL.")

        elif not artwork_url_verifier(values["URL"]):
            sg.popup_error("Enter a valid Artstation, DeviantArt or Pixiv URL.")

        elif values["username"] is "" and values["password"] is not "":
            sg.popup_error("Please enter a valid password")

        elif values["password"] is "" and values["username"] is not "":
            sg.popup_error("Please enter a valid username")

        else:
            # Opens the debug Window
            debug_window = not debug_window
            window['-DEBUG-'].update(visible=debug_window)

            # Hides the Download Button
            download_button_bool = not download_button_bool
            window['-DOWNLOAD-'].update(visible=download_button_bool)

            # Show The ProgressBar
            progress_bar_bool = not progress_bar_bool
            window['-PROGRESS BAR-'].update(visible=progress_bar_bool)

            user_vars = ProgVars()
            user_vars.url = values["URL"]
            user_vars.username = values["username"]
            user_vars.password = values["password"]

            if values["save_dir"] == "":
                user_vars.save_location = root_dir

            else:
                user_vars.save_location = values["save_dir"]

            user_vars.threads = int(values["threads"])
            main_function_threading(user_vars, window)

    if event == '-THREAD DONE-':
        sg.popup_ok("Images were successfully downloaded", keep_on_top=True)

        # Un-hides the Download Button
        download_button_bool = not download_button_bool
        window['-DOWNLOAD-'].update(visible=download_button_bool)

        # Closes the debug window
        debug_window = not debug_window
        window['-DEBUG-'].update(visible=debug_window)

        # Hides the ProgressBar
        progress_bar_bool = not progress_bar_bool
        window['-PROGRESS BAR-'].update(visible=progress_bar_bool)

        # Zero outs the progress_bar if the user wants to rerun the downloader
        image_counter.val = 0
        image_counter.max = 0

        # saves the progress in the json file
        dict_to_json(successful_download_dict, save_dir_global.save_dir, 'successful_download.json')

    #  Updates the progress bar at the end of each loop cycle
    progress_bar.UpdateBar(image_counter.val, image_counter.max)

    # Updates the completion ratio
    if image_counter.max is not 0:
        percentage = round((image_counter.val / image_counter.max)*100)
    else:
        percentage = 0

    window.FindElement('counter').Update(f"{percentage}%")
window.Close()





