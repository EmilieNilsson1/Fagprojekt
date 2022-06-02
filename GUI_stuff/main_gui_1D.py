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
    options_column = [
        [sg.Text('CUQIpy Interactive Demo', size=(40, 3), justification='center', font=big_font)],
        [sg.Text('Choose test signal', font =medium_font)],
        [sg.Combo(['Gauss', 'sinc','vonMises','square','hat','bumps', 'derivGauss'],key = '-TESTSIG-' , default_value='Gauss')],
        [sg.Text('Noise std:'), sg.Slider(range=(0.01, 1), default_value=0.05, resolution=0.01, size=(20, 10), orientation='h', key='-SLIDER-NOISE-', enable_events = True, disable_number_display=True), 
        sg.T('0.05', key='-RIGHTn-', visible = True),sg.Image("info.png",(18,18),tooltip="Change standard deviation of the normally distributed noise. \nValues range from 0.01 to 1.")],
        [sg.Text('_'*120)],
        [sg.Text('Choose prior distribution', font =medium_font)],
        [sg.Button('Gaussian', image_data = resize_base64_image("gauss.png", (150,300)), key = '-GAUSSIAN-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font), 
        sg.Button('Laplace', image_data = resize_base64_image("laplace.png", (150,300)), key = '-LAPLACE-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font), 
        sg.Button('Cauchy', image_data = resize_base64_image("cauchy.png", (150,300)), key = '-CAUCHY-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font), 
        sg.Button('Uniform', image_data = resize_base64_image("uniform.png", (150,300)), key = '-UNI-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font)],
        [sg.Text('Set prior parameters', font =medium_font,key = 'PRIOR_TEXT')],
        [place(sg.Text('Par1', font = small_font, key = '-PAR1-', visible = False)), 
        place(sg.Slider(range=(0.01, 1.0), default_value=0.1, resolution = 0.01, orientation='h', enable_events = True, disable_number_display=True, key='-SLIDER1-', visible = False, size = (20,10))), 
        place(sg.T('0.1', key='-RIGHT1-', visible = False))],
        [place(sg.Text('Par2', font = small_font, key = '-PAR2-', visible=False)), 
        place(sg.Combo(['zero', 'periodic'], default_value = 'zero', key = '-BCTYPE-', visible=False, size = (10,1)))],
        [sg.Text('_'*120)],
        [sg.Text('Deconvolution dims dims', font = medium_font)],
        [sg.Text('Sample size', font = small_font), 
        sg.Slider(range=(100, 5000), default_value=100, resolution=100, size=(20, 10), orientation='h', key='-SLIDER-SAMPLE-', enable_events = True, disable_number_display=True),
        sg.T('1000', key='-RIGHT2-'),sg.Image("info.png",(18,18),tooltip="Change sample size. Choosing large values \nmay cause long computation time.")],
        [sg.Text('Confidence interval', font = small_font), sg.InputText(key = '-TEXT-CONF-', size =(10,10), default_text=90),
        sg.Image("info.png",(18,18),tooltip="Choose size of confidance interval of the reconstructed solution. \nThe confidence interval is computed as percentiles of the posterior samples. \nValues range from 0% to 100%. ")],
        [sg.Checkbox('Show true signal', default=False, key='TRUE_SIGNAL', enable_events = True, pad = (3, 10))],
        [sg.Button('Update', size=(10, 1), font=medium_font),
        sg.Button('Exit', size=(10, 1), font=medium_font),
        sg.Text('Figure updated', visible = False, key = '-FIGUP-', text_color = 'white', font= medium_font, enable_events = True)],
        [sg.Multiline(size=(20,1.5), no_scrollbar = True, auto_refresh = True, autoscroll = True, reroute_stdout = True, visible = False, key='-OUTPUT-')]
    ]

    plot_column = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS-')]
    ]

    # 1D layout:
    layout = [
        [sg.Column(options_column),
        sg.VSeperator(),
        sg.Column(plot_column),]
    ]

    # Create the GUI and show it without the plot
    window = sg.Window('CUQIpy interactive demo', layout, finalize=True, resizable=True, icon='cookieIcon.ico' ).Finalize()
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
        window.Element('-RIGHTn-').update(values['-SLIDER-NOISE-'])

        # Select prior distribution
        # buttons change accordingly
        if event == '-GAUSSIAN-':
            Dist = "Gaussian"
            window['PRIOR_TEXT'].update('Set parameters for gaussian distribution')
            #window['-GAUSSIAN-'].update(button_color='white on green') # updates buttons
            window['-GAUSSIAN-'].update(button_color=(None,'green'))
            window['-CAUCHY-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-LAPLACE-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-UNI-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible = True)
            window['-SLIDER1-'].update(visible=True)
            window['-RIGHT1-'].update(visible=True)
            window['-PAR1-'].update('Prior std')
            window['-PAR2-'].update(visible = False) # removes buttons if other prior was chosen first
            window['-BCTYPE-'].update(visible = False)
            window['-FIGUP-'].update(visible = False)
        elif event == '-LAPLACE-':
            Dist = "Laplace_diff"
            window['PRIOR_TEXT'].update('Set parameters for laplace distribution')
            #window['-LAPLACE-'].update(button_color='white on green')
            window['-LAPLACE-'].update(button_color=(None,'green'))
            window['-GAUSSIAN-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-CAUCHY-'].update(button_color = sg.TRANSPARENT_BUTTON)
            window['-UNI-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible = True)
            window['-SLIDER1-'].update(visible=True)
            window['-RIGHT1-'].update(visible=True)
            window['-PAR1-'].update('Scale')
            window['-PAR2-'].update(visible = True) # add new parameter
            window['-PAR2-'].update('Boundary')
            window['-BCTYPE-'].update(visible = True)
            window['-FIGUP-'].update(visible = True)
            window['-FIGUP-'].update('Might take a while')
        elif event == '-CAUCHY-':
            Dist = "Cauchy_diff"
            window['PRIOR_TEXT'].update('Set parameters for cauchy distribution')
            window['-CAUCHY-'].update(button_color=(None, 'green')) #'white on green')
            window['-GAUSSIAN-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-UNI-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible = True)
            window['-SLIDER1-'].update(visible=True)
            window['-RIGHT1-'].update(visible=True)
            window['-PAR1-'].update('Scale')
            window['-PAR2-'].update(visible = True)
            window['-PAR2-'].update('Boundary')
            window['-BCTYPE-'].update(visible = True)
            window['-FIGUP-'].update(visible = True)
            window['-FIGUP-'].update('Might take a while')
        elif event == '-UNI-':
            Dist == 'Uniform'
            window['-UNI-'].update(button_color=(None, 'green')) #'white on green')
            window['PRIOR_TEXT'].update('Set parameters for uniform distribution')
            window['-GAUSSIAN-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-CAUCHY-'].update(button_color = sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible = True)
            window['-SLIDER1-'].update(visible=True)
            window['-RIGHT1-'].update(visible=True)
            window['-PAR1-'].update('Spread')
            window['-FIGUP-'].update(visible = False)


        # Clicked update button
        if event in ('Update', None):

            # Get values from input
            par1 = float(values['-SLIDER1-'])
            par2 = values['-BCTYPE-']
            sampsize = int(values['-SLIDER-SAMPLE-'])
            conf = int(values['-TEXT-CONF-'])
            n_std = float(values['-SLIDER-NOISE-'])

            # Define and compute posterior to Deconvolution problem
            sig = values['-TESTSIG-']
            TP = cuqi.testproblem.Deconvolution1D(phantom = sig, noise_std = n_std)
            
            if Dist == "Gaussian":
                TP.prior = getattr(cuqi.distribution, Dist)(np.zeros(128), par1)

            
            
            if Dist == "Laplace_diff":
                TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(128), scale = par1, bc_type = par2)
                window['-OUTPUT-'].update(visible = True)

            if Dist == "Cauchy_diff":
                TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(128), scale = par1, bc_type = par2)
                window['-OUTPUT-'].update(visible = True)

            if Dist == "Uniform":
                Low = 0-par1
                High = 0+par1
                TP.prior = getattr(cuqi.distribution, Dist)(low = Low, high = High)
                
            try:
                xs = TP.sample_posterior(sampsize) # Sample posterior
            except:
                window['-FIGUP-'].update(visible = True)
                window['-FIGUP-'].update(text_color = 'red')
                window['-FIGUP-'].update('Sampler not implemented')
            else:
                window['-FIGUP-'].update('Figure updated!')
                window['-FIGUP-'].update(text_color = 'white')
                window['-FIGUP-'].update(visible = True)
    
                # Update plot
                grid = np.linspace(0,128, 128)
                fig.clear()
                plt.subplot(211)
                plt.plot(grid, TP.data) # Noisy data
                plt.legend(['Measured data'], loc = 1)
                plt.subplot(212)
                xs.plot_ci(conf) # Solution
                fig_agg.draw()
                
                # Remove output window
                window['-OUTPUT-'].update(visible=False)    
            

        # Show true signal
        show_true = values['TRUE_SIGNAL']
        if show_true:
            try:
                p1 = plt.plot(grid, TP.exactSolution, color = 'darkorange')
                fig_agg.draw()
            except:
                pass
        else:
            try:
                p = p1.pop(0)
                p.remove()
                fig_agg.draw()
            except:
                pass

if __name__ == '__main__':
    sg.change_look_and_feel('Dark Blue 12') #Theme
    main() #Runs main method

# %%

# %%
