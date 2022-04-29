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

from GUI2D import *
#from GUI1D import *


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


def make_window1():
    layout = [[sg.Text('Menu'), ],
            [sg.Button('1D convolution'), sg.Button('2D convolution'), sg.Button('Exit')]]
    win = sg.Window('Window 1', layout, resizable=True, finalize=True)
    win.Maximize()
    return win

#def make_window1D():
#    layout = tab1_layout
#    return sg.Window('Window 1D', layout, finalize=True).Finalize()

def make_window2D():
    layout = tab2_layout
    return sg.Window('Window 2D', layout, finalize=True)

# Main method
def main():

    # look into enable_events = True
    # Define the GUI layout
    options_column = [
        [sg.Text('CUQIpy Interactive Demo', size=(40, 3), justification='center', font='Helvetica 20')],
        [sg.Text('Choose test signal', font = 'Helvetica 16')],
        [sg.Combo(['Gauss', 'sinc','vonMises','square','hat','bumps', 'derivGauss'],key = '-TESTSIG-' , default_value='Gauss')],
        [sg.Text('Noise std:'), sg.Slider(range=(0.01, 1), default_value=0.05, resolution=0.01, size=(20, 10), orientation='h', key='-SLIDER-NOISE-', enable_events = True, disable_number_display=True), 
        sg.T('0.05', key='-RIGHTn-', visible = True)],
        [sg.Text('Choose prior distribution', font = 'Helvetica 16')],
        [sg.Button('Gaussian', image_data = resize_base64_image("gauss.png", (150,300)), key = '-GAUSSIAN-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = 'Helvetica 14'), 
        sg.Button('Laplace', image_data = resize_base64_image("laplace.png", (150,300)), key = '-LAPLACE-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = 'Helvetica 14'), 
        sg.Button('Cauchy', image_data = resize_base64_image("cauchy.png", (150,300)), key = '-CAUCHY-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = 'Helvetica 14'), 
        sg.Button('Uniform', image_data = resize_base64_image("uniform.png", (150,300)), key = '-UNI-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = 'Helvetica 14')],
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
        [sg.Checkbox('Show true signal', default=True, key='TRUE_SIGNAL', enable_events = True), sg.Checkbox('Show confidence interval', default=True, key='PLOT-CONF', enable_events = True)],
        [sg.Button('Update', size=(10, 1), font='Helvetica 14'), sg.Button('Menu'),
        sg.Button('Exit', size=(10, 1), font='Helvetica 14'),
        sg.Text('Figure updated', visible = False, key = '-FIGUP-', text_color = 'white', font= 'Helvetica 14', enable_events = True)]
    ]

    plot_column = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS-')]
    ]

    # 1D layout:
    tab1_layout = [
        [sg.Column(options_column),
        sg.VSeperator(),
        sg.Column(plot_column),]
    ]
 
    # 2D layout:
    #tab2_layout = [ [sg.Column(options_column2),
    #    sg.VSeperator(),
    #    sg.Column(plot_column2),]]
     
    #layout = [[sg.TabGroup([[sg.Tab('1D convolution', tab1_layout, key='Tab1', title_color = 'black'),
    #                     sg.Tab('2D convolution', tab2_layout, key = 'Tab2')]],
    #                   key='-TABS-', title_color='black',
    #                   selected_title_color='white', tab_location='topleft', font = 'Helvetica 16')]]

    # Create the GUI and show it without the plot
    #window = sg.Window('CUQIpy interactive demo', layout, finalize=True, resizable=True, icon='cookieIcon.ico' ).Finalize()
    #window.Maximize()

    #window1, window2, window3 = make_window1(), None, None
    window1, window2, window3 = make_window1(), None, None
    #window2 = sg.Window('Window 1D', tab1_layout, finalize=True, resizable=True)
    #window2.Maximize()
    #window2.hide()
    #window3 = make_window2D()
    #window3.Maximize()
    #window3.hide()

 
    

    # Extract canvas element to attach plot to



    Dist = "Gaussian" # setting Gaussian as default
    while True:

        # Read current events and values from GUI
        #event, values = window.read()
        window, event, values = sg.read_all_windows()
        if window == window1 and event in (sg.WIN_CLOSED, 'Exit'):
            break
    
        if window == window1:
            if event == '2D convolution':
                window1.hide()
                window3 = make_window2D()
            elif event in (sg.WIN_CLOSED, 'Menu'):
                window3.close()
                window1.un_hide()

        if window == window3:
            if event == 'Menu':
                window3.close()
                window1.un_hide()

        if window == window2:
            if event == 'Menu':
                window2.close()
                window1.un_hide()

        if window == window1:
            if event == '1D convolution':
                test = True
                window1.hide()
                window2 = sg.Window('Window 1D', tab1_layout, finalize=True, resizable=True)
                window2.Maximize()
                canvas_elem = window2['-CANVAS-']
                canvas = canvas_elem.TKCanvas

                fig = plt.figure(figsize = (6,6))
                fig_agg = draw_figure(canvas, fig)
                
                while test == True:
                    if event == 'Menu':
                        test = False
                        window1.un_hide()
                        window2.close()

                    
                    #window2 = make_window1D()
                    #window2 = sg.Window('Window 1D', tab1_layout, finalize=True).Finalize()
                    #window2.Maximize()

                    #canvas_elem = window2['-CANVAS-']
                    #canvas = canvas_elem.TKCanvas

                    # Draw the initial figure in the window

                    #fig = plt.figure(figsize = (6,6))
                    #fig_agg = draw_figure(canvas, fig)
        

                    #if window == window3:
                    #    window3.close()

                    # Clicked exit button
                    if event in ('Exit', None):
                        exit()
                    
                    window, event, values = sg.read_all_windows()
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


                    # Clicked update button
                    if event in ('Update', None):
                        #window['-FIGUP-'].update(visible = True)
                        #window['-FIGUP-'].update('Loading...')

                        # Get values from input
                        par1 = float(values['-SLIDER1-'])
                        par2 = values['-BCTYPE-']
                        sampsize = int(values['-SLIDER-SAMPLE-'])
                        conf = int(values['-TEXT-CONF-'])
                        n_std = float(values['-SLIDER-NOISE-'])

                        # Define and compute posterior to Deconvolution problem
                        sig = values['-TESTSIG-']
                        TP = cuqi.testproblem.Deconvolution(phantom = sig, noise_std = n_std)
                        
                        if Dist == "Gaussian": 
                            TP.prior = getattr(cuqi.distribution, Dist)(np.zeros(128), par1) 
                        
                        if Dist == "Laplace_diff":
                            TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(128), scale = par1, bc_type = par2)
                            
                        if Dist == "Cauchy_diff":
                            TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(128), scale = par1, bc_type = par2)
                        
                        if Dist == "Uniform":
                            Low = 0-par1
                            High = 0+par1
                            TP.prior = getattr(cuqi.distribution, Dist)(low = Low, high = High)
                            
                        try:
                            xs = TP.sample_posterior(sampsize) # Sample posterior
                            samp = xs.samples
                            mean = np.mean(samp, axis=-1)
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
                            plt.plot(grid, TP.data, color = 'darkorange') # Noisy data
                            plt.legend(['Measured data'], loc = 1)
                            plt.subplot(212)
                            xs.plot_ci(conf, color = 'blue') # Solution
                            plt.ylim(-0.25, 1.25)
                            plt.xlim(0, 128)
                            fig_agg.draw()
                            
                            # Print update in console
                            print(" Figure updated!")

                    # Show true signal
                    show_true = values['TRUE_SIGNAL']
                    show_ci = values['PLOT-CONF']
                    if not show_ci and not show_true: # plot mean
                        try:
                            plt.subplot(212).clear()
                            samp = xs.samples
                            meansamp = np.mean(samp, axis = -1)
                            plt.plot(grid, meansamp, color = 'dodgerblue', label = 'Mean')
                            plt.xlabel('x')
                            plt.ylim(-0.25, 1.25)
                            plt.xlim(0, 128)
                            plt.legend()
                            fig_agg.draw()
                        except: pass
                    else: # plot_ci
                        try:
                            plt.subplot(212).clear()
                            xs.plot_ci(conf)
                            plt.ylim(-0.25, 1.25)
                            plt.xlim(0, 128)
                            fig_agg.draw()
                        except: pass
                    if show_true and show_ci:
                        try:
                            plt.subplot(212).clear()
                            xs.plot_ci(conf, exact=TP.exactSolution)
                            plt.ylim(-0.25, 1.25)
                            plt.xlim(0, 128)
                            fig_agg.draw()
                        except:
                            pass
                    if show_true and not show_ci:
                        try:
                            plt.subplot(212).clear()
                            samp = xs.samples
                            meansamp = np.mean(samp, axis = -1)
                            plt.plot(grid, meansamp, color = 'dodgerblue', label = 'Mean')
                            plt.plot(grid, TP.exactSolution, color = 'orange', label = 'Exact')
                            plt.xlabel('x')
                            plt.ylim(-0.25, 1.25)
                            plt.xlim(0, 128)
                            plt.legend()
                            fig_agg.draw()
                        except:
                            pass



if __name__ == '__main__':
    sg.change_look_and_feel('Dark Blue 12') #Theme
    main() #Runs main method

# %%

# %%
