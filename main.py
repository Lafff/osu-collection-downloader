import PySimpleGUI as sg
import json
import os
from collector import get_beatmaps_from_collection
from maps_downloader import download_beatmapsets
import asyncio
import pathlib
from db import update_collections

def _onKeyRelease(event):
    ctrl  = (event.state & 0x4) != 0
    if event.keycode==88 and  ctrl and event.keysym.lower() != "x":
        event.widget.event_generate("<<Cut>>")

    if event.keycode==86 and  ctrl and event.keysym.lower() != "v":
        event.widget.event_generate("<<Paste>>")

    if event.keycode==67 and  ctrl and event.keysym.lower() != "c":
        event.widget.event_generate("<<Copy>>")
    
    if event.keycode==65 and  ctrl and event.keysym.lower() != "a":
        event.widget.event_generate("<<SelectAll>>")

def create_configuration_file():
    configuration = {'osu_songs_path':''
                     }
    with open(os.getcwd()+'/configuration.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(configuration))
    return configuration

def get_configuration():
    try:
        with open(os.getcwd()+'/configuration.json', 'r', encoding='utf-8') as file:
            configuration = json.loads(file.read())
    except Exception:
        configuration = create_configuration_file()
    return configuration


def check_update_configuration(configuration, values_dict:dict):
    for key in configuration:
        new_value = values_dict.get(key, None)
        if configuration[key] != new_value and new_value is not None:
            configuration[key] = new_value
    with open(os.getcwd()+'/configuration.json', 'w', encoding='utf-8') as file:
        file.write(json.dumps(configuration))


def add_osu_path_layouts(layouts):
    layouts += [[sg.Text('Specify the path to the folder with Osu! maps')],
              [sg.InputText(key='osu_songs_path', enable_events=True, default_text=osu_songs_path), sg.FolderBrowse(button_text='Open')], 
              ]
    return layouts

def add_collection_layouts(layouts):
    layouts += [[sg.Text('Provide a link to the collection')],
                [sg.InputText(key='link_to_collection')],
                [sg.Button(button_text='Download the collection')]
               ]
    return layouts

def add_progress_bar_layout(layouts):
    layouts += [[sg.ProgressBar(max_value=0, key='progress_bar', size=(30,15), auto_size_text=True, visible=False)]
               ]
    return layouts

def add_finish_text_layout(layouts):
    layouts += [[sg.Text('Upload completed', visible=False, key='Finish')]]
    return layouts


def validate_path(path):
    if not path:
        return False
    path = pathlib.Path(path)
    if not path.exists() or not path.is_dir():
        return False
    return True


if __name__ == '__main__':
    configuration = get_configuration()
    osu_songs_path = configuration.get('osu_songs_path')
    layouts = []
    progress_dict = {'downloaded': 0, 'total':0}
    folder_path = None
    layouts = add_osu_path_layouts(layouts)
    layouts = add_collection_layouts(layouts)
    layouts = add_progress_bar_layout(layouts)
    layouts = add_finish_text_layout(layouts)
    window = sg.Window('Osu! Collection Downloader', layouts, finalize=True)
    window.TKroot.bind_all("<Key>", _onKeyRelease, "+")
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == 'osu_songs_path':
            folder_path = values['osu_songs_path']
            validate_path(folder_path)
        elif event == 'Download the collection':
            folder_path = values['osu_songs_path']
            validate_path(folder_path)
            if folder_path != osu_songs_path:
                check_update_configuration(configuration, values)
            osu_songs_path = pathlib.Path(r''+folder_path)
            link_to_collection = values['link_to_collection']
            if link_to_collection and osu_songs_path:
                window['progress_bar'].update(visible=True)
                window['Finish'].update(visible=False)
                collection_information = get_beatmaps_from_collection(link_to_collection)
                progress_dict['total'] = len(collection_information[1])
                window['progress_bar'].update(current_count=0, max=progress_dict['total'])
                asyncio.run(download_beatmapsets(collection_information[1], osu_songs_path, progress_dict, window))
                update_collections(osu_songs_path.parent, collection_information[0], collection_information[2])
                window['Finish'].update(visible=True)
    window.close()
