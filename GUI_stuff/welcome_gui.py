#%%
#!/usr/bin/env python
# Basic packages
from email.policy import default
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import base64
import io
from PIL import Image
import os
import sys
import inspect
import webbrowser

# Add PySimpeGUI
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
import cuqi

# Convenience method to draw figure
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def resize_base64_image(image, size):
    with open(image, "rb") as img_file:
        image64 = base64.b64encode(img_file.read())
    image_file = io.BytesIO(base64.b64decode(image64))
    img = Image.open(image_file)
    img.thumbnail(size, Image.ANTIALIAS)
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    imgbytes = bio.getvalue()
    return imgbytes

# So elements dont move when changing visibility
def place(elem): 
    return sg.Column([[elem]], pad=(0,0))

# Main method
def main():

    # look into enable_events = True
    # Define the GUI layout
    big_font = 'Courier 20 bold'
    medium_font = 'Courier 16'
    small_font = 'Helvetica 12'

    # create simple layout
    layout = [
        [sg.Text('Welcome to our CUQIpy Interactive Demo!', size=(40, 3), justification='center', font=big_font)],
        [sg.Text('By using this demo you will get an intuitive understanding of computational uncertainty quantification for inverse problems', font =small_font)],
        [sg.Text('The demo is split up in two sections; one for 1D and 2D deconvolution problems respectively. We recommend you start of by using the 1D section first',font =small_font)],
        [sg.Text('The idea is simple: You simply choose one of the given test signal which will be convoluted and added noise to simulate the measurement of real life data', font=small_font)],
        [sg.Text('From this deconvuluted signal we will then create our bayesian posterior which will be our recreation of the signal', font=small_font)],
        [sg.Text('To get the most out of the demo try choosing different prior distributions with various parameters to see how they affect the uncertainty in our recreation', font=small_font)],
        [sg.Text('After pressing "Update" various plots will be shown from which you can learn various informations about the signal and the bayesian recreation. Have fun!', font = small_font)],
        [sg.Text('For more information about the current work in CUQI done at DTU Compute, visit the following site:'),
        sg.Button('CUQI', enable_events = True, size=(10, 1), font=medium_font)],
        [sg.Image("gauss.png",size=(300,300))],
        [sg.Button('Exit', size=(10, 1), font=medium_font)]
    ]

    # Create the GUI window
    window = sg.Window('CUQIpy interactive demo', layout, finalize=True, resizable=True, icon='cookieIcon.ico' ).Finalize()
    window.Maximize()

    while True:

        # Read current events and values from GUI
        event, values = window.read()

        # Clicked exit button
        if event in ('Exit', None):
            exit()
        
        if event in ('CUQI', None):
            os.system("start \"\" https://www.compute.dtu.dk/english/cuqi")
        
if __name__ == '__main__':
    sg.change_look_and_feel('Dark Blue 12') #Theme
    main() #Runs main method

# %%

# %%
