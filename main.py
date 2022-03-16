#%%
#!/usr/bin/env python
# Basic packages
from email.policy import default
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

# hejsa nu har jeg skrevet noget!


# Main method
def main():

    # Define the GUI layout
    layout = [[sg.Text('CUQIpy interactive demo', size=(40, 1), justification='center', font='Helvetica 20')],
              [sg.Canvas(size=(640, 480), key='-CANVAS-')],
              [sg.Text('Prior std:', font = 'Helvetica 12')],
              [sg.Slider(range=(0.01, 1.0), default_value=0.1, resolution=0.01, size=(40, 10), orientation='h', key='-SLIDER-DATAPOINTS-')],
              [sg.Text('Sample size:', font = 'Helvetica 12')],
              [sg.Slider(range=(100, 5000), default_value=1000, resolution=100, size=(40, 10), orientation='h', key='-SLIDER-SAMPLE-')],
              [sg.Text('Enter confidence interval'), sg.InputText(key = '-TEXT-CONF-', size =(10,10))],
              [sg.Combo(["Gaussian", "Uniform", "Laplace_diff"], default_value = 'Gaussian', key = '-DROP-DIST-')],
              [sg.Button('Update', size=(10, 1), pad=((280, 0), 3), font='Helvetica 14')],
              [sg.Button('Exit', size=(10, 1), pad=((280, 0), 3), font='Helvetica 14')]]

    # Create the GUI and show it without the plot
    window = sg.Window('CUQIpy interactive demo', layout, finalize=True)
    window.Maximize()

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

            # Get values from slider input
            std = float(values['-SLIDER-DATAPOINTS-']) # std            
            Dist = values['-DROP-DIST-']
            sampsize = int(values['-SLIDER-SAMPLE-'])
            conf = int(values['-TEXT-CONF-'])

            # Define and compute posterior to Deconvolution problem
            TP = cuqi.testproblem.Deconvolution() # Default values
            if Dist == "Gaussian":  
                TP.prior = getattr(cuqi.distribution, Dist)(np.zeros(128), std) # Set prior
            if Dist == "Laplace_diff":
                TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(128), scale = 0.5, bc_type = 'periodic')
            xs = TP.sample_posterior(sampsize) # Sample posterior

            # Update plot
            fig.clear()
            #xs.plot_ci(95, exact=TP.exactSolution)
            xs.plot_ci(conf, exact=TP.exactSolution)
            plt.ylim([-0.5,1.5])
            
            # Draw plot in GUI
            fig_agg.draw()
            
            # Print update in console
            print(" Figure updated!")

if __name__ == '__main__':
    sg.change_look_and_feel('BlueMono') #Theme
    main() #Runs main method

# %%
