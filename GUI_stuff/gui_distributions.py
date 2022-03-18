#!/usr/bin/env python
# Basic packages
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

# Add CUQIpy (assumed to be in ../cuqipy/)
import sys
sys.path.append("../cuqipy/")
import cuqi

# Add PySimpeGUI
import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Convenience method to draw figure
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


# Main method
def main():

    # Define the GUI layout
    layout = [[sg.Text('GUI for plotting distributions', size=(40, 1), justification='center', font='Helvetica 20')],
              [sg.Canvas(size=(640, 480), key='-CANVAS-')],
              [sg.Text('Choose distribution')],
              #[sg.Slider(range=(0.01, 1.0), default_value=0.1, resolution=0.01, size=(40, 10), orientation='h', key='-SLIDER-DATAPOINTS-')],
              [sg.Combo(["Normal", "Gamma"], default_value = 'Normal', key = '-DROP-DIST-')],
              [sg.Button('Update', size=(10, 1), pad=((280, 0), 3), font='Helvetica 14')],
              [sg.Button('Exit', size=(10, 1), pad=((280, 0), 3), font='Helvetica 14')]]

    # Create the GUI and show it without the plot
    window = sg.Window('CUQIpy interactive demo', layout, finalize=True)

    # Extract canvas element to attach plot to
    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.TKCanvas

    # Draw the initial figure in the window
    fig = plt.figure()
    fig_agg = draw_figure(canvas, fig)


    while True:

        # Read current events and values from GUI
        event, values = window.read()

        # Clicked exit button
        if event in ('Exit', None):
            exit()

        # Clicked update button
        if event in ('Update', None):

            # Get values from drop down
            Fun = values['-DROP-DIST-'] # chosen distribution
            
            X = getattr(cuqi.distribution,Fun)(mean=0, std=1) # creating cuqi.distribution object
            Xs = X.sample # extracting samples

            # Update plot
            fig.clear()
            grid = np.linspace(-10, 10, 1001)
            plt.plot(grid, X.pdf(grid))
            
            # Draw plot in GUI
            fig_agg.draw()
            
            # Print update in console
            print(" Figure updated!")
main()

# if __name__ == '__main__':
#     sg.change_look_and_feel('Reddit') #Theme
#     main() #Runs main method

         


