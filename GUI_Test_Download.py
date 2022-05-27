import PySimpleGUI as sg
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
from PIL import ImageOps
import os
import cuqi
import sys
import scipy
sys.path.append("..")

file_types = [("JPEG (*.jpg)", "*.jpg"),("PNG (*.png)", "*.png"),
              ("All files (*.*)", "*.*")]

sg.theme("DarkTeal2")
layout = [[sg.T("")], [sg.Text("Choose a file: "), 
            sg.Input(key="-FILE-"), 
            sg.FileBrowse(file_types=file_types)],
            [sg.Button("Submit"),sg.Checkbox("Resize", default=True)]]

###Building Window
window = sg.Window('My File Browser', layout, size=(600,150))
    
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event=="Exit":
        break
    elif event == "Submit":
        filename = values["-FILE-"]
        if os.path.exists(filename):
                image = Image.open(values["-FILE-"]).convert('RGB')
                if values[0] == True:
                    image = image.resize((128,128))
                phantom = cuqi.data.rgb2gray(image)

