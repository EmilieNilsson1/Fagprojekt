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
    options_column = [
        [sg.Text('CUQIpy Interactive Demo', size=(40, 3), justification='center', font='Helvetica 20')],
        [sg.Text('Choose test problem', font = 'Helvetica 16')],
        [sg.Combo(['Abel_1D', 'Deblur', 'Deconv_1D','Deconvolution'],key = '-TESTPROB-' , default_value='Deconvolution')], #'Heat_1D', 'Poisson_1D'
        [sg.Text('Choose prior distribution', font = 'Helvetica 16')],
        [sg.Button('Gaussian', image_data = resize_base64_image("gauss.png", (150,300)), key = '-GAUSSIAN-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = 'Helvetica 14'), 
        sg.Button('Laplace_diff', image_data = resize_base64_image("laplace.png", (150,300)), key = '-LAPLACE-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = 'Helvetica 14'), 
        sg.Button('Cauchy', image_data = resize_base64_image("cauchy.png", (150,300)), key = '-CAUCHY-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = 'Helvetica 14')],
        [sg.Text('Set prior parameters', font = 'Helvetica 16',key = 'PRIOR_TEXT')],
        [place(sg.Text('Par1', font = 'Helvetica 12', key = '-PAR1-', visible = False)), 
        place(sg.Slider(range=(0.01, 1.0), default_value=0.1, resolution = 0.01, orientation='h', enable_events = True, disable_number_display=True, key='-SLIDER1-', visible = False, size = (20,10))), 
        place(sg.T('0.1', key='-RIGHT1-', visible = False))],
        [place(sg.Text('Par2', font = 'Helvetica 12', key = '-PAR2-', visible=False)), 
        place(sg.Combo(['zero', 'periodic'], default_value = 'zero', key = '-BCTYPE-', visible=False, size = (10,1)))],
        [sg.Text('Sample size', font = 'Helvetica 12'), 
        sg.Slider(range=(100, 5000), default_value=100, resolution=100, size=(20, 10), orientation='h', key='-SLIDER-SAMPLE-', enable_events = True, disable_number_display=True),
        sg.T('1000', key='-RIGHT2-')],
        [sg.Text('Confidence interval', font = 'Helvetica 12'), sg.InputText(key = '-TEXT-CONF-', size =(10,10), default_text=90)],
        [sg.Checkbox('Show true signal', default=False, key='TRUE_SIGNAL')],
        [sg.Button('Update', size=(10, 1), font='Helvetica 14'),#pad=((280, 0), 3)
        sg.Button('Exit', size=(10, 1), font='Helvetica 14'),
        sg.Text('Figure updated', visible = False, key = '-FIGUP-', text_color = 'red', font= 'Helvetica 14')]
    ]

    plot_column = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS-')]
    ]

    layout = [
        [sg.Column(options_column),
        sg.VSeperator(),
        sg.Column(plot_column),]
    ]

    # Create the GUI and show it without the plot
    window = sg.Window('CUQIpy interactive demo', layout, finalize=True, resizable=True, ).Finalize()
    window.Maximize()

    # Extract canvas element to attach plot to

    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.TKCanvas

    # Draw the initial figure in the window

    fig = plt.figure(figsize = (6,6))
    fig_agg = draw_figure(canvas, fig)

    Dist = "Gaussian" # setting Gaussian as default
    while True:

        # Read current events and values from GUI
        event, values = window.read()

        # Clicked exit button
        if event in ('Exit', None):
            exit()
        
        window.Element('-RIGHT1-').update(values['-SLIDER1-']) # updates slider values
        window.Element('-RIGHT2-').update(int(values['-SLIDER-SAMPLE-'])) 

        # Select prior distribution
        # buttons change accordingly
        if event == '-GAUSSIAN-':
            Dist = "Gaussian"
            window['PRIOR_TEXT'].update('Set parameters for gaussian distribution')
            #window['-GAUSSIAN-'].update(button_color='white on green') # updates buttons
            window['-GAUSSIAN-'].update(button_color=(None,'green'))
            window['-CAUCHY-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-LAPLACE-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible = True)
            window['-SLIDER1-'].update(visible=True)
            window['-RIGHT1-'].update(visible=True)
            window['-PAR1-'].update('Prior std')
            window['-PAR2-'].update(visible = False) # removes buttons if other prior was chosen first
            window['-BCTYPE-'].update(visible = False)
        elif event == '-LAPLACE-':
            Dist = "Laplace_diff"
            window['PRIOR_TEXT'].update('Set parameters for laplace distribution')
            #window['-LAPLACE-'].update(button_color='white on green')
            window['-LAPLACE-'].update(button_color=(None,'green'))
            window['-GAUSSIAN-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-CAUCHY-'].update(button_color = sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible = True)
            window['-SLIDER1-'].update(visible=True)
            window['-RIGHT1-'].update(visible=True)
            window['-PAR1-'].update('Scale')
            window['-PAR2-'].update(visible = True) # add new parameter
            window['-PAR2-'].update('Boundary')
            window['-BCTYPE-'].update(visible = True)
        elif event == '-CAUCHY-':
            Dist = "Cauchy_diff"
            window['PRIOR_TEXT'].update('Set parameters for cauchy distribution')
            window['-CAUCHY-'].update(button_color=(None, 'green')) #'white on green')
            window['-GAUSSIAN-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible = True)
            window['-SLIDER1-'].update(visible=True)
            window['-RIGHT1-'].update(visible=True)
            window['-PAR1-'].update('Scale')
            window['-PAR2-'].update(visible = True)
            window['-PAR2-'].update('Boundary')
            window['-BCTYPE-'].update(visible = True)

        # Clicked update button
        if event in ('Update', None):

            # Get values from input
            par1 = float(values['-SLIDER1-'])
            par2 = values['-BCTYPE-']
            sampsize = int(values['-SLIDER-SAMPLE-'])
            conf = int(values['-TEXT-CONF-'])

            # Define and compute posterior to Deconvolution problem
            #TP = cuqi.testproblem.Deconvolution() # Default values
            prob = values['-TESTPROB-']
            TP = getattr(cuqi.testproblem, prob)()

            
            if Dist == "Gaussian": 
                TP.prior = getattr(cuqi.distribution, Dist)(np.zeros(128), par1) 
            
            if Dist == "Laplace_diff":
                TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(128), scale = par1, bc_type = par2)
                
            if Dist == "Cauchy_diff":
                TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(128), scale = par1, bc_type = par2)
           
            try:
                xs = TP.sample_posterior(sampsize) # Sample posterior
            except:
                window['-FIGUP-'].update(visible = True)
                window['-FIGUP-'].update(text_color = 'red')
                window['-FIGUP-'].update('Combination not supported')
            else:
                window['-FIGUP-'].update('Figure updated!')
                window['-FIGUP-'].update(text_color = 'green')
                window['-FIGUP-'].update(visible = True)
    
                # Update plot
                show_true = bool(values['TRUE_SIGNAL'])
                # Solution:
                fig.clear()
                plt.subplot(212)
                if show_true: xs.plot_ci(conf, exact=TP.exactSolution)
                else: xs.plot_ci(conf)
                
                # Noisy data:
                grid = np.linspace(0,128, 128)
                plt.subplot(211)
                plt.plot(grid, TP.data)
                plt.legend(['Noisy data'], loc = 1)
                fig_agg.draw()
                
                # Print update in console
                print(" Figure updated!")

if __name__ == '__main__':
    sg.change_look_and_feel('Dark Blue 12') #Theme
    main() #Runs main method

# %%

# %%
