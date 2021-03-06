# %%
#!/usr/bin/env python
# Basic packages

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import PySimpleGUI as sg
import inspect
import sys
from PIL import Image
import io
import base64
import matplotlib.pyplot as plt
import scipy as sp
import numpy as np
from turtle import width
from email.policy import default
import os

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
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
    return sg.Column([[elem]], pad=(0, 0))

# Main method


def main():
    # initialising toggles for info buttons
    iNum = 4
    iTog = np.full((iNum,), False)

    # Keeping track of whether or not the update button has been clicked
    updated = False

    # look into enable_events = True
    # Define the GUI layout
    big_font = 'Courier 20 bold'
    medium_font = 'Courier 16'
    small_font = 'Helvetica 12'
    options_column = [
        [sg.Text('CUQIpy Interactive Demo', size=(40, 3),
                 justification='center', font=big_font)],
        [sg.Text('Test signal', font=medium_font)],
        [sg.Combo(['Gauss', 'sinc', 'vonMises', 'square', 'hat', 'bumps',
                   'derivGauss'], readonly=True, key='-TESTSIG-', default_value='Gauss')],
        [sg.Text('Noise std:'), sg.Slider(range=(0.01, 1), default_value=0.05, resolution=0.01, size=(20, 10), orientation='h', key='-SLIDER-NOISE-', enable_events=True, disable_number_display=True),
         sg.Input('0.05', key='-INPUT-NOISE-', visible=True,
                  enable_events=True, size=(5, 1)),
         sg.Button(image_data=resize_base64_image("info.png", (30, 30)), border_width=0, button_color=sg.theme_background_color(), key=('-IB-', 0))],
        [sg.pin(sg.Text('Change standard deviation of the normally distributed noise \nValues range from 0.01 to 1.',
                        text_color='black', background_color='light yellow', visible=bool(iTog[0]), key=('-ITX-', 0)))],
        [sg.Button('Show initial signal', key = '-SHOW1D-')],
        [sg.Text('_'*120)],
        [sg.Text('Prior distribution', font=medium_font),sg.Button(image_data=resize_base64_image("info.png", (30, 30)), border_width=0, button_color=sg.theme_background_color(), key=('-IB-', 3))], 
        [sg.pin(sg.Text('Choose the prior distribution used when solving the deconvolution problem \nNotice that laplace and cauchy is used on the difference between consecutive elements \nChoosing laplace, cauchy or uniform requires significantly more computation time than gaussian',
                        text_color='black', background_color='light yellow', visible=bool(iTog[0]), key=('-ITX-', 3)))],
        [sg.Button('Gaussian', image_data=resize_base64_image("gauss.png", (150, 300)), key='-GAUSSIAN-', button_color=('black', None), border_width=10, mouseover_colors=('black', 'black'), auto_size_button=True, font=medium_font),
         sg.Button('Laplace', image_data=resize_base64_image("laplace.png", (150, 300)), key='-LAPLACE-', button_color=(
             'black', None), border_width=10, mouseover_colors=('black', 'black'), auto_size_button=True, font=medium_font),
         sg.Button('Cauchy', image_data=resize_base64_image("cauchy.png", (150, 300)), key='-CAUCHY-', button_color=(
             'black', None), border_width=10, mouseover_colors=('black', 'black'), auto_size_button=True, font=medium_font),
         sg.Button('Uniform', image_data=resize_base64_image("uniform.png", (150, 300)), key='-UNI-', button_color=('black', None), border_width=10, mouseover_colors=('black', 'black'), auto_size_button=True, font=medium_font)],
        [sg.Text('Prior parameters', font=medium_font, key='PRIOR_TEXT')],
        [sg.pin(sg.Text('Par1', font=small_font, key='-PAR1-', visible=False)),
         sg.pin(sg.Slider(range=(0.01, 1.0), default_value=0.1, resolution=0.01, orientation='h',
                          enable_events=True, disable_number_display=True, key='-SLIDER1-', visible=False, size=(20, 10))),
         sg.Input('0.1', key='-INPUT-PAR1-', visible=True,
                  enable_events=True, size=(5, 1))],
        [sg.pin(sg.Text('Par2', font=small_font, key='-PAR2-', visible=False)),
         sg.pin(sg.Combo(['zero', 'periodic'], default_value='zero', key='-BCTYPE-', visible=False, size=(10, 1)))],
        [sg.Text('_'*120)],
        [sg.Text('Plot options', font=medium_font)],
        [sg.Text('Sample size', font=small_font),
         sg.Slider(range=(10, 3000), default_value=100, resolution=10, size=(
             20, 10), orientation='h', key='-SLIDER-SAMPLE-', enable_events=True, disable_number_display=True),
         sg.Input('100', key='-INPUT-SAMPLE-', visible=True,
                  enable_events=True, size=(5, 1)),
         sg.Button(image_data=resize_base64_image("info.png", (30, 30)), border_width=0, button_color=sg.theme_background_color(), key=('-IB-', 1))],
        [sg.pin(sg.Text('Choose the desired number of samples from the posterior. \nA larger number requires more computation time, but gives a smoother result. \nValues range from 10 to 3000.',
                        text_color='black', background_color='light yellow', visible=bool(iTog[1]), key=('-ITX-', 1)))],
        [sg.Text('Confidence interval', font=small_font),
         sg.Slider(range=(0, 100), default_value=95, resolution=5, size=(20, 10), orientation='h', key='-SLIDER-CONF-', enable_events=True, disable_number_display=True),
         sg.Input('95', key='-INPUT-CONF-', visible=True, enable_events=True, size=(5, 1)),
         sg.Button(image_data=resize_base64_image("info.png", (30, 30)), border_width=0, button_color=sg.theme_background_color(), key=('-IB-', 2))],
        [sg.pin(sg.Text('Choose size of confidence interval of the reconstructed solution. \nThe confidence interval is computed as percentiles of the posterior samples. \nValues range from 0% to 100%. ',
                        text_color='black', background_color='light yellow', visible=bool(iTog[2]), key=('-ITX-', 2)))],
        [sg.Checkbox('Show true signal', default=False, key='TRUE_SIGNAL', enable_events=True, pad=(3, 10)), sg.Checkbox(
            'Show confidence interval', default=True, key='PLOT-CONF', enable_events=True, pad=(3, 10))],
        [sg.Button('Run', size=(10, 1), font=medium_font, enable_events=True, key='-UPDATE-1D-'),
         sg.Button('Exit', size=(10, 1), font=medium_font),
         sg.Text('Figure updated', visible=False, key='-FIGUP-', text_color='white', font=medium_font, enable_events=True)],
         [sg.Text('Sampling in progress...', visible=False, key='-LOADTXT-',pad=(3, 10))],
        [sg.Multiline(size=(20, 1.5), no_scrollbar=True, auto_refresh=True,
                      autoscroll=True, reroute_stdout=True, visible=False, key='-OUTPUT-')]
    ]

    plot_column = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS-')]
    ]

    # 1D layout:
    layout = [
        [sg.Column(options_column),
         sg.VSeperator(),
         sg.Column(plot_column), ]
    ]

    # Create the GUI and show it without the plot
    window = sg.Window('CUQIpy interactive demo', layout, finalize=True,
                       resizable=True, icon='cookieIcon.ico').Finalize()
    window.Maximize()

    # Extract canvas element to attach plot to

    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.TKCanvas

    # Draw the initial figure in the window

    fig = plt.figure(figsize=(6, 6))
    fig_agg = draw_figure(canvas, fig)

    # setting Gaussian as default
    Dist = "Gaussian"
    window['PRIOR_TEXT'].update('Parameters for gaussian distribution')
    window['-GAUSSIAN-'].update(button_color=(None, 'green'))
    window['-CAUCHY-'].update(button_color=sg.TRANSPARENT_BUTTON)
    window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
    window['-UNI-'].update(button_color=sg.TRANSPARENT_BUTTON)
    window['-PAR1-'].update(visible=True)
    window['-SLIDER1-'].update(visible=True)
    window['-PAR1-'].update('Std')
    # removes buttons if other prior was chosen first
    window['-PAR2-'].update(visible=False)
    window['-BCTYPE-'].update(visible=False)
    window['-FIGUP-'].update(visible=False)

    # for input boxes
    test_1D = [True, True, True, True]

    while True:

        # Read current events and values from GUI
        event, values = window.read()

        # Clicked exit button
        if event in ('Exit', None):
            exit()

        orig_col = window['-INPUT-NOISE-'].BackgroundColor

        if event:
            window['-FIGUP-'].update(visible = False)
            

        if isinstance(event, str):
            # noise input box
            if event == '-INPUT-NOISE-':
                try:
                    if float(values['-INPUT-NOISE-']) >= window.Element('-SLIDER-NOISE-').Range[0] and float(values['-INPUT-NOISE-']) <= window.Element('-SLIDER-NOISE-').Range[1]:
                        window.Element(
                            '-SLIDER-NOISE-').update(value=values['-INPUT-NOISE-'])
                        window.Element(
                            '-INPUT-NOISE-').update(background_color=orig_col)
                        test_1D[0] = True
                    else:
                        window.Element('-SLIDER-NOISE-').update(value=0.05)
                        window.Element(
                            '-INPUT-NOISE-').update(background_color='red')
                        test_1D[0] = False
                except:
                    window.Element('-SLIDER-NOISE-').update(value=0.05)
                    window.Element(
                        '-INPUT-NOISE-').update(background_color='red')
                    test_1D[0] = False

            if event == '-SLIDER-NOISE-':
                window.Element(
                    '-INPUT-NOISE-').update(values['-SLIDER-NOISE-'])
                test_1D[0] = True
                window.Element(
                    '-INPUT-NOISE-').update(background_color=orig_col)
            # par1 input box
            if event == '-INPUT-PAR1-':
                try:
                    if float(values['-INPUT-PAR1-']) >= window.Element('-SLIDER1-').Range[0] and float(values['-INPUT-PAR1-']) <= window.Element('-SLIDER1-').Range[1]:
                        window.Element(
                            '-SLIDER1-').update(value=values['-INPUT-PAR1-'])
                        window.Element(
                            '-INPUT-PAR1-').update(background_color=orig_col)
                        test_1D[1] = True
                    else:
                        window.Element('-SLIDER1-').update(value=0.1)
                        window.Element(
                            '-INPUT-PAR1-').update(background_color='red')
                        test_1D[1] = False
                except:
                    window.Element('-SLIDER1-').update(value=0.1)
                    window.Element('-INPUT-PAR1-').update(background_color='red')
                    test_1D[1] = False

            if event == '-SLIDER1-':
                window.Element(
                    '-INPUT-PAR1-').update(values['-SLIDER1-'])
                test_1D[1] = True
                window.Element(
                    '-INPUT-PAR1-').update(background_color=orig_col)

            # sample input box
            if event == '-INPUT-SAMPLE-':
                try:
                    if int(values['-INPUT-SAMPLE-']) >= window.Element('-SLIDER-SAMPLE-').Range[0] and int(values['-INPUT-SAMPLE-']) <= window.Element('-SLIDER-SAMPLE-').Range[1]:
                        window.Element(
                            '-SLIDER-SAMPLE-').update(value=values['-INPUT-SAMPLE-'])
                        window.Element(
                            '-INPUT-SAMPLE-').update(background_color=orig_col)
                        test_1D[2] = True
                    else:
                        window.Element('-SLIDER-SAMPLE-').update(value=100)
                        window.Element(
                            '-INPUT-SAMPLE-').update(background_color='red')
                        test_1D[2] = False
                except:
                    window.Element('-SLIDER-SAMPLE-').update(value=100)
                    window.Element(
                        '-INPUT-SAMPLE-').update(background_color='red')
                    test_1D[2] = False

            if event == '-SLIDER-SAMPLE-':
                window.Element(
                    '-INPUT-SAMPLE-').update(int(values['-SLIDER-SAMPLE-']))
                test_1D[2] = True
                window.Element(
                    '-INPUT-SAMPLE-').update(background_color=orig_col)

            # conf input box
            if event == '-INPUT-CONF-':
                try:
                    if float(values['-INPUT-CONF-']) >= window.Element('-SLIDER-CONF-').Range[0] and float(values['-INPUT-CONF-']) <= window.Element('-SLIDER-CONF-').Range[1]:
                        window.Element(
                            '-SLIDER-CONF-').update(value=values['-INPUT-CONF-'])
                        window.Element(
                            '-INPUT-CONF-').update(background_color=orig_col)
                        test_1D[3] = True
                    else:
                        window.Element('-SLIDER-CONF-').update(value=95)
                        window.Element(
                            '-INPUT-CONF-').update(background_color='red')
                        test_1D[3] = False
                except:
                    window.Element('-SLIDER-CONF-').update(value=95)
                    window.Element(
                        '-INPUT-CONF-').update(background_color='red')
                    test_1D[3] = False

            if event == '-SLIDER-CONF-':
                window.Element(
                    '-INPUT-CONF-').update(int(values['-SLIDER-CONF-']))
                test_1D[3] = True
                window.Element(
                    '-INPUT-CONF-').update(background_color=orig_col)

        # show initial signal
        if event == '-SHOW1D-':
            updated = False
            n_std = float(values['-SLIDER-NOISE-'])
            sig = values['-TESTSIG-']
            TP = cuqi.testproblem.Deconvolution1D(phantom=sig, noise_std=n_std)
            grid = np.linspace(0, 128, 128)

            plt.subplot(212).clear()
            plt.subplot(212).axis('off')
            plt.subplot(211).clear()
            plt.subplot(211)
            
            plt.plot(grid, TP.data/max(TP.data),color='green') 
            plt.legend(['Initial signal'], loc=1)
            fig_agg.draw()

        # Select prior distribution
        # buttons change accordingly
        if event == '-GAUSSIAN-':
            Dist = "Gaussian"
            window['PRIOR_TEXT'].update('Parameters for gaussian distribution')
            # window['-GAUSSIAN-'].update(button_color='white on green') # updates buttons
            window['-GAUSSIAN-'].update(button_color=(None, 'green'))
            window['-CAUCHY-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-UNI-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible=True)
            window['-SLIDER1-'].update(visible=True)
            window['-PAR1-'].update('Std')
            # removes buttons if other prior was chosen first
            window['-PAR2-'].update(visible=False)
            window['-BCTYPE-'].update(visible=False)
            window['-FIGUP-'].update(visible=False)
        elif event == '-LAPLACE-':
            Dist = "Laplace_diff"
            window['PRIOR_TEXT'].update('Parameters for laplace distribution')
            window['-LAPLACE-'].update(button_color=(None, 'green'))
            window['-GAUSSIAN-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-CAUCHY-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-UNI-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible=True)
            window['-SLIDER1-'].update(visible=True)
            window['-PAR1-'].update('Scale')
            window['-PAR2-'].update(visible=True)  # add new parameter
            window['-PAR2-'].update('Boundary')
            window['-BCTYPE-'].update(visible=True)
        elif event == '-CAUCHY-':
            Dist = "Cauchy_diff"
            window['PRIOR_TEXT'].update('Parameters for cauchy distribution')
            window['-CAUCHY-'].update(button_color=(None, 'green'))
            window['-GAUSSIAN-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-UNI-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible=True)
            window['-SLIDER1-'].update(visible=True)
            window['-PAR1-'].update('Scale')
            window['-PAR2-'].update(visible=True)
            window['-PAR2-'].update('Boundary')
            window['-BCTYPE-'].update(visible=True)
        elif event == '-UNI-':
            Dist == 'Uniform'
            window['-UNI-'].update(button_color=(None, 'green'))
            window['PRIOR_TEXT'].update('Parameters for uniform distribution')
            window['-GAUSSIAN-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-CAUCHY-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-PAR1-'].update(visible=True)
            window['-SLIDER1-'].update(visible=True)
            window['-PAR1-'].update('Spread')
            # removes buttons if other prior was chosen first
            window['-PAR2-'].update(visible=False)
            window['-BCTYPE-'].update(visible=False)

        # Checking for errors in input boxes
        if sum(test_1D) != 4:
            window['-UPDATE-1D-'].update(disabled=True)
            window['-UPDATE-1D-'].update(button_color='gray')
        elif sum(test_1D) == 4:
            window['-UPDATE-1D-'].update(disabled=False)
            window['-UPDATE-1D-'].update(button_color=sg.theme_button_color())

        # Clicking info button: showing and removing information
        for i in range(iNum):
            if event == ('-IB-', i):
                for j in range(iNum):
                    if j == i:
                        iTog[j] = not iTog[j]
                        window[('-ITX-', j)].update(visible=bool(iTog[j]))
                        continue
                    iTog[j] = False
                    window[('-ITX-', j)].update(visible=bool(iTog[j]))

        # Clicked update button
        show_true = values['TRUE_SIGNAL']
        show_ci = values['PLOT-CONF']
        if event in ('-UPDATE-1D-', None):

            updated = True
            # Get values from input
            par1 = float(values['-SLIDER1-'])
            par2 = values['-BCTYPE-']
            sampsize = int(values['-SLIDER-SAMPLE-'])
            conf = int(values['-SLIDER-CONF-'])
            n_std = float(values['-SLIDER-NOISE-'])

            # Define and compute posterior to Deconvolution problem
            sig = values['-TESTSIG-']
            TP = cuqi.testproblem.Deconvolution1D(phantom=sig, noise_std=n_std)

            if Dist == "Gaussian":
                TP.prior = getattr(cuqi.distribution, Dist)(np.zeros(128), par1)

            if Dist == "Laplace_diff":
                TP.prior = getattr(cuqi.distribution, Dist)(location=np.zeros(128), scale=par1, bc_type=par2)
                window['-OUTPUT-'].update(visible=True)
                window['-LOADTXT-'].update(visible=True)

            if Dist == "Cauchy_diff":
                TP.prior = getattr(cuqi.distribution, Dist)(location=np.zeros(128), scale=par1, bc_type=par2)
                window['-OUTPUT-'].update(visible=True)
                window['-LOADTXT-'].update(visible=True)

            if Dist == "Uniform":
                Low = 0-par1
                High = 0+par1
                TP.prior = getattr(cuqi.distribution, Dist)(low=Low, high=High)
                window['-LOADTXT-'].update(visible=True)

            try:
                xs = TP.sample_posterior(sampsize)  # Sample posterior
            except:
                window['-FIGUP-'].update(visible=True)
                window['-FIGUP-'].update(text_color='red')
                window['-FIGUP-'].update('Sampler not implemented')
            else:
                window['-FIGUP-'].update('Figure updated!')
                window['-FIGUP-'].update(text_color='white')
                window['-FIGUP-'].update(visible=True)

                # Update plot
                grid = np.linspace(0, 128, 128)
                fig.clear()
                plt.subplot(211)
                plt.plot(grid, TP.data/max(TP.data),color='green')  # Noisy data
                plt.legend(['Initial signal'], loc=1)
                plt.subplot(212)
                if show_ci and not show_true:
                    xs.plot_ci(conf)
                elif show_ci and show_true:
                    xs.plot_ci(conf, exact=TP.exactSolution)
                elif not show_ci and not show_true:
                    samp = xs.samples
                    meansamp = np.mean(samp, axis=-1)
                    plt.plot(grid, meansamp, label='Mean') 
                elif not show_ci and show_true:
                    samp = xs.samples
                    meansamp = np.mean(samp, axis=-1)
                    plt.plot(grid, meansamp, label='Mean') 
                    plt.plot(grid, TP.exactSolution, color='orange', label='True Signal')

                fig_agg.draw()

                # Remove output window
                window['-OUTPUT-'].update(visible=False)
                window['-LOADTXT-'].update(visible=False)

        # Show true signal/confidence interval or not

        if ((event == 'TRUE_SIGNAL') or (event == 'PLOT-CONF') or (event == ('-UPDATE-1D-', None))) and updated == True:
            if not show_ci and not show_true:  # plot mean
                try:
                    plt.subplot(212).clear()
                    samp = xs.samples
                    meansamp = np.mean(samp, axis=-1)
                    plt.plot(grid, meansamp, label='Mean')
                    # plt.xlabel('x')
                    #plt.ylim(-0.25, 1.25)
                    plt.xlim(0, 128)
                    plt.legend()
                    fig_agg.draw()
                except:
                    pass
            else:  # plot_ci
                try:
                    samp = xs.samples
                    plt.subplot(212).clear()
                    xs.plot_ci(conf)
                    #plt.ylim(-0.25, 1.25)
                    plt.xlim(0, 128)
                    fig_agg.draw()
                except:
                    pass
            if show_true and show_ci:
                try:
                    plt.subplot(212).clear()
                    xs.plot_ci(conf, exact=TP.exactSolution)
                    #plt.ylim(-0.25, 1.25)
                    plt.xlim(0, 128)
                    fig_agg.draw()
                except:
                    pass
            if show_true and not show_ci:
                try:
                    plt.subplot(212).clear()
                    samp = xs.samples
                    meansamp = np.mean(samp, axis=-1)
                    plt.plot(grid, meansamp, label='Mean')
                    plt.plot(grid, TP.exactSolution, color='orange', label='True Signal')
                    # plt.xlabel('x')
                    #plt.ylim(-0.25, 1.25)
                    plt.xlim(0, 128)
                    plt.legend()
                    fig_agg.draw()
                except:
                    pass

if __name__ == '__main__':
    sg.change_look_and_feel('Dark Blue 12')  # Theme
    main()  # Runs main method
