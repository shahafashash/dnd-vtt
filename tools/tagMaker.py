
import PySimpleGUI as sg
import json
from PIL import Image
from io import BytesIO
import base64

def load_image(path):
    if path.endswith('.png'):
        return path
    elif path.endswith('.jpg'):
        pil_image = Image.open(path)
        byte_io = BytesIO()
        pil_image.save(byte_io, format="PNG")
        byte_io.seek(0)
        byte_data = byte_io.getvalue()
        base64_image = base64.b64encode(byte_data)
        return base64_image

def update_window(index):
        map_thumbnail = map_collection[index]['thumbnail']
        window['IMAGE'].update(load_image(map_thumbnail))
        tags = ' '.join(map_collection[index]['tags'])
        window['TAGS'].update(tags)
        window['NAME'].update(map_collection[index]['name'])

def handle_events(event, values):
    global current_index, map_collection
    # print(event, values)
    
    if event == 'NEXT':
        current_index = (current_index + 1) % len(map_collection)
        update_window(current_index)

    if event == 'PREV':
        current_index = (current_index - 1) % len(map_collection)
        update_window(current_index)
    
    if event == 'ADD_TAG':
        map_collection[current_index]['tags'].append(values['NEW_TAG'])
        window['NEW_TAG'].update('')
        update_window(current_index)

with open('./maps.json', 'r') as file:
    map_collection = json.load(file)

current_index = 0

layout = [
    [sg.Input(map_collection[current_index]['name'], key='NAME', size=(50,0))],
    [sg.Image(load_image(map_collection[current_index]['thumbnail']), key='IMAGE')],
    [sg.Multiline(' '.join(map_collection[current_index]['tags']), key='TAGS', size=(100,5))],
    [sg.Input(key='NEW_TAG', size=(50,0))],
    [sg.Button(key='ADD_TAG', visible=False, bind_return_key=True)],
    [sg.Button('Previous', key='PREV'), sg.Button('Next', key='NEXT')]
]

window = sg.Window('Tag Maker', layout, element_justification='c')

while True:
    event, values = window.read()
    if event in (None, 'Exit'):
        break
    handle_events(event, values)
window.close()

json_object = json.dumps(map_collection, indent=4)
with open(f'maps.json', 'w') as outfile:
    outfile.write(json_object)

