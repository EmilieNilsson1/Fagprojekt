import PySimpleGUI as sg
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
from PIL import ImageOps
from scipy.io import wavfile
import os
import inspect
import pydub
import sys
import scipy
import sounddevice as sd

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import cuqi

from cuqi.distribution import Gaussian
sys.path.append("..")

def read(f, normalized=False):
    """MP3 to numpy array"""
    a = pydub.AudioSegment.from_mp3(f)
    y = np.array(a.get_array_of_samples())
    if a.channels == 2:
        y = y.reshape((-1, 2))
    if normalized:
        return a.frame_rate, np.float32(y) / 2**15
    else:
        return a.frame_rate, y

file_types = [("All files (*.*)", "*.*")]

sg.theme("DarkTeal2")
layout = [[sg.T("")], [sg.Text("Choose a file: "), 
            sg.Input(key="-FILE-"), 
            sg.FileBrowse(file_types=file_types)],
            [sg.Button("Submit")]]

###Building Window
window = sg.Window('My File Browser', layout, size=(600,150))
    
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event=="Exit":
        break
    elif event == "Submit":
        filename = values["-FILE-"]
        if os.path.exists(filename):
                samplerate, data = read(values["-FILE-"])
                dim = 2000
                sizeData = data[:,0].size//dim
                x = np.zeros((dim,2))
                a = 0
                for i in range(0,dim*sizeData,sizeData):
                    x[a,0] = data[i,0]
                    x[a,1] = data[i,1]
                    a = a + 1
                TP = cuqi.testproblem.Deconvolution1D(dim=dim, phantom=x[:,0], noise_std=0.05)
                TP.prior = getattr(cuqi.distribution, 'GaussianCov')(np.zeros(data.size), 0.1)

                sd.play(x, dim//1.5, blocking=True)
                sd.play(data,samplerate,blocking=True)