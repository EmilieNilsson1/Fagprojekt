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
        [sg.Text('Welcome to our CUQIpy Interactive Demo!', size=(60, 5), justification='center', font=big_font),
        sg.Button('Link', enable_events = True, size=(10, 1), font=medium_font),
        sg.Button('Exit', size=(10, 1), font=medium_font)]
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
        
        if event in ('Link', None):
            os.system("start \"\" https://www.compute.dtu.dk/english/cuqi")
        
    # Extract canvas element to attach plot to

    # canvas_elem = window['-CANVAS-']
    # canvas = canvas_elem.TKCanvas

    # Draw the initial figure in the window

    # fig = plt.figure(figsize = (6,6))
    # fig_agg = draw_figure(canvas, fig)

if __name__ == '__main__':
    sg.change_look_and_feel('Dark Blue 12') #Theme
    main() #Runs main method

# %%

# %%
