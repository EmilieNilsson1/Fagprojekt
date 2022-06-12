import PySimpleGUI as sg
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
from PIL import ImageOps
from scipy.io import wavfile
import os
import inspect
import sys
import scipy
import sounddevice as sd
sys.path.append("..")

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import cuqi

file_types = [("All files (*.*)", "*.*")]

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
                samplerate, data = wavfile.read(values["-FILE-"])
                data1 = data[1,:]
                TP = cuqi.testproblem.Deconvolution1D(dim = data1.size, phantom=data1, noise_std=0.05)
                print(TP)
                sd.play(TP, data1.size, blocking=True)