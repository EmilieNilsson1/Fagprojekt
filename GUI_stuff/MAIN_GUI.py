#%%
#!/usr/bin/env python
# Basic packages
from argparse import FileType
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

# some functions
from matplotlib.colors import Normalize
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import ScalarMappable

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
    iNum = 5
    iTog = np.full((iNum,), False)
    updated_1D = False
    iNum2D = 6
    iTog2D = np.full((iNum2D,) , False )
    test = True
    file_types = [("JPEG (*.jpg)", "*.jpg"),("PNG (*.png)", "*.png"),
              ("All files (*.*)", "*.*")]
    file_types2 = ['.png','.PNG','.JPG', '.jpg', '.jpeg']
    # look into enable_events = True
    # Define the GUI layout
    big_font = 'Courier 20 bold'
    medium_font = 'Courier 16'
    medium2_font = 'Courier 14'
    small_font = 'Helvetica 12'
    options_column = [
        [sg.Text('Test signal', font=medium_font)],
        [sg.Text('From library', font = small_font), sg.Combo(['Gauss', 'sinc', 'vonMises', 'square', 'hat', 'bumps',
                   'derivGauss', 'two squares'], readonly=True, key='-TESTSIG-', default_value='Gauss')],
        [sg.Text('Noise std', font=small_font), sg.Slider(range=(0, 1), default_value=0.05, resolution=0.01, size=(20, 10), orientation='h', key='-SLIDER-NOISE-', enable_events=True, disable_number_display=True),
         sg.Input('0.05', key='-INPUT-NOISE-', visible=True,
                  enable_events=True, size=(5, 1)),
         sg.Button(image_data=resize_base64_image("info.png", (30, 30)), border_width=0, button_color=sg.theme_background_color(), key=('-IB-', 0))],
        [sg.pin(sg.Text('Change standard deviation of the normally distributed noise \nValues range from 0.01 to 1.',
                        text_color='black', background_color='light yellow', visible=bool(iTog[0]), key=('-ITX-', 0)))],
        [sg.Button('Show initial signal', key = '-SHOW1D-')],
        [sg.Text('_'*100)],
        [sg.Text('Prior distribution', font=medium_font),sg.Button(image_data=resize_base64_image("info.png", (30, 30)), border_width=0, button_color=sg.theme_background_color(), key=('-IB-', 3))], 
        [sg.pin(sg.Text('Choose the prior distribution used when solving the deconvolution problem. \nGaussian: Elements follow a Gaussian Markov Random Field \nLaplace: Difference between consecutive elements follow a Laplace Distribution. \nCauchy: Difference between consecutive elements follow a Cauchy Distribution',
                        text_color='black', background_color='light yellow', visible=bool(iTog[0]), key=('-ITX-', 3)))],
        [sg.Button('Gaussian', image_data=resize_base64_image("gauss.png", (160, 320)), key='-GAUSSIAN-', button_color=('black', None), border_width=10, mouseover_colors=('black', 'black'), auto_size_button=True, font=medium_font),
         sg.Button('Laplace', image_data=resize_base64_image("laplace.png", (156, 320)), key='-LAPLACE-', button_color=(
             'black', None), border_width=10, mouseover_colors=('black', 'black'), auto_size_button=True, font=medium_font),
         sg.Button('Cauchy', image_data=resize_base64_image("cauchy.png", (160, 320)), key='-CAUCHY-', button_color=(
             'black', None), border_width=10, mouseover_colors=('black', 'black'), auto_size_button=True, font=medium_font)],
        [sg.Text('Prior parameters', font=medium_font, key='PRIOR_TEXT')],
        [place(sg.Text('Par1', font=small_font, key='-PAR1-', visible=False)),
         place(sg.Slider(range=(0.01, 100), default_value=1, resolution=0.01, orientation='h',
                          enable_events=True, disable_number_display=True, key='-SLIDER1-', visible=False, size=(20, 10))),
         sg.Input('1', key='-INPUT-PAR1-', visible=True,
                  enable_events=True, size=(5, 1))],
        #[place(sg.Text('Par2', font=small_font, key='-PAR2-', visible=False)),
        [place(sg.Text('', font=small_font, key='-PAR2-', visible=True)),
         place(sg.Combo(['zero', 'periodic', 'neumann'], default_value='zero', key='-BCTYPE-', readonly= True, visible=False, size=(10, 1)))],
         [place(sg.Text('', font=small_font, key='-PAR3-', visible=True)),
         place(sg.Combo(['0', '1', '2'], default_value='0', key='-ORDER_1D-', readonly= True, visible=False, size=(2, 1)))],
        [sg.Text('_'*100)],
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
        [sg.Checkbox('Show true signal', default=False, key='TRUE_SIGNAL', enable_events=True, pad=(3, 10), font=small_font), sg.Checkbox(
            'Show confidence interval', default=True, key='PLOT-CONF', enable_events=True, pad=(3, 10), font=small_font), sg.Checkbox('Show RSS', default=True, key='RSS', enable_events=True, pad=(3, 10), font=small_font),
            sg.Button(image_data=resize_base64_image("info.png", (30, 30)), border_width=0, button_color=sg.theme_background_color(), key=('-IB-', 4))],
            [sg.pin(sg.Text('Choose what you want to see in the plot. The RSS is the residual sum of squares between the reconstruction and the true signal',
                        text_color='black', background_color='light yellow', visible=bool(iTog[4]), key=('-ITX-', 4)))],
        [sg.Button('Run', size=(10, 1), font=medium_font, enable_events=True, key='-UPDATE-1D-'),
         sg.Button('Exit', size=(10, 1), font=medium_font),
         sg.Text('Figure updated', visible=False, key='-FIGUP-', text_color='white', font=medium_font, enable_events=True)],
         [sg.Text('Sampling in progress...', visible=False, key='-LOADTXT-',pad=(3, 10))],
        [sg.Multiline(size=(20, 1.5), no_scrollbar=True, auto_refresh=True,
                      autoscroll=True, reroute_stdout=False, visible=False, key='-OUTPUT-', enable_events=True, do_not_clear = False)]
    ]

    plot_column = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS-')],
        #[sg.Push(),sg.Canvas(size=(1100, 620), key='-CANVAS-',pad = (30,0)),sg.Push()],
        #[sg.Text('', key = 'error1D')]
    ]

    # 1D layout:
    tab1_layout = [
        [sg.Column(options_column),
         sg.VSeperator(),
         sg.Column(plot_column)]
    ]
    options_column2D = [
        [sg.Text('Test signal', font =medium_font)],
        [sg.Text('From library', font = small_font),sg.Combo(['astronaut','cat','camera','satellite', 'grains', 'smooth', 'threephases','binary', 'fourphases', 'threephasessmooth', 'shepp_logan'],key = '-TESTSIG_2D-' , default_value='satellite', enable_events=True, readonly = True),
        sg.Text("or own file ", key = 'CF', visible = True, font=small_font), sg.Input(key='-FILE-', visible = True, size = (20,10), enable_events = True), 
        sg.FileBrowse(file_types=file_types, visible = True, enable_events = True, target = '-FILE-'), 
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',4)),
        sg.Text('error in image path', visible = False, enable_events = True, key = 'file_error', text_color = 'white', background_color = 'red', font = small_font)], #key = 'Browse'
        [sg.pin(sg.Text('Files must be PNG or JPEG.', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[4]), key= ('-ITX_2D-',4)))],
        [sg.Text('Image size', font = small_font), 
        sg.Slider(range=(8, 1024), default_value=128, resolution=8, size=(20, 10), orientation='h', key='-SLIDER-SIZE_2D-', enable_events = True, disable_number_display=True),
        sg.Input('128', key='-RIGHT_SIZE_2D-', visible = True, enable_events = True, size = (5,1)),
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), visible = False, key = ('-IB_2D-',5))],
        [sg.pin(sg.Text('Image Dimension: ( , )', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[5]), key= ('-ITX_2D-',5)))],
        [sg.Text('Noise std',font=small_font), sg.Slider(range=(0, 1), default_value=0.05, resolution=0.01, size=(20, 10), orientation='h', key='-SLIDER-NOISE_2D-', enable_events = True, disable_number_display=True), 
        sg.Input('0.05', key='-RIGHTn_2D-', visible = True, enable_events = True, size = (5,1)),
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',0))],
        [sg.pin(sg.Text('Change standard deviation of the normally distributed noise. \nValues range from 0.01 to 1.', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[0]), key= ('-ITX_2D-',0)))],
        [sg.Button('Show initial signal', key = 'show2D')],
        [sg.Text('_'*100)],
        [sg.Text('Prior distribution', font =medium_font), sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',3))], 
        [sg.pin(sg.Text('Choose the prior distribution used when solving the deconvolution problem. \nGaussian: Elements follow a Gaussian Markov Random Field \nLaplace: Difference between neighbouring elements follow a Laplace Distribution. \nCauchy: Difference between neighbouring elements follow a Cauchy Distribution', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[3]), key= ('-ITX_2D-',3)))],
        [sg.Button('Gaussian', image_data = resize_base64_image("gauss2d.png", (160,320)), key = '-GAUSSIAN_2D-', button_color=('black', 'Green'), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font), 
        sg.Button('Laplace', image_data = resize_base64_image("laplace2d.png", (160,320)), key = '-LAPLACE_2D-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font), 
        sg.Button('Cauchy', image_data = resize_base64_image("cauchy2d.png", (160,320)), key = '-CAUCHY_2D-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font)], 
        [sg.Text('Parameters for Gaussian Markov Random Field', font =medium_font, key = 'PRIOR_TEXT_2D', visible = True)],
        [place(sg.Text('Precision',key = 'ALPHA_TEXT', font = small_font)),place(sg.Slider((0.01,100),default_value=1, resolution=0.01, key = 'ALPHA',  size=(20, 10),orientation='h', disable_number_display=True,  enable_events = True)), 
        place(sg.InputText('1', key='-RIGHTA_2D-', visible = True, enable_events = True, size = (5,0.8), background_color = None))],
        [place(sg.Text('Boundary', key = 'BOUNDS_TEXT', font = small_font)),place(sg.Combo(['zero','periodic','neumann'],default_value = 'zero', readonly= True, key = 'BOUNDS_2D', size = (10,1)))],
        [place(sg.Text('Order', key = 'ORDER_TEXT', font = small_font)),place(sg.Combo([0,1,2],default_value = 0, readonly= True, key = 'ORDER_2D', size = (2,1)))],
        [sg.Text('_'*100)],
        [sg.Text('Plot options', font = medium_font)],
        [sg.Text('Sample size', font = small_font), 
        sg.Slider(range=(10, 1000), default_value=10, resolution=10, size=(20, 10), orientation='h', key='-SLIDER-SAMPLE_2D-', enable_events = True, disable_number_display=True),
        sg.Input('10', key='-RIGHT2_2D-', enable_events = True, size = (5,0.8)),
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',1))],
        [sg.pin(sg.Text('Change sample size. Choosing large values \nmay cause long computation time.', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[1]), key= ('-ITX_2D-',1)))],
        [sg.Checkbox('Add uncertainty overlay', default=False, key='Uncer', enable_events = True, font = small_font),
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',2))],
        [sg.pin(sg.Text('The uncertainty image is added as a red overlay on the reconstruction.\nThe values are scaled so the largest std value is red and smaller\nvalues become more transparent. A Gaussian prior will often result in\na completely red overlay.', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[2]), key= ('-ITX_2D-',2)))],
        [sg.Button('Run', size=(10, 1), font=medium_font, enable_events=True, key = 'up2d'),
        sg.Button('Exit', size=(10, 1), font=medium_font, key = '-EXIT_2D-'),
        sg.Text('Figure updated', visible = False, key = '-FIGUP_2D-', text_color = 'red', font= medium_font, enable_events = True)],
        [sg.Text('Sampling in progress...', visible=False, key='-LOADTXT2D-',pad=(3, 10))],
        [sg.Multiline(size=(20,1.5), no_scrollbar = True, auto_refresh = True, autoscroll = True, reroute_stdout = False, visible = False, key='-OUTPUT_2D-', enable_events= True, do_not_clear = False)]
    ]

    # 2D plot tabs
    plot2D_tab1_layout = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS_2D_1-')]
    ]

    plot2D_tab2_layout = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS_2D_2-')]
    ]

    plot2D_tab3_layout = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS_2D_3-')]
    ]

    plot2D_tab4_layout = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS_2D_4-')]
    ]

    plot2D_tab5_layout = [
        [sg.Canvas(size=(1100, 620), key='-CANVAS_2D_5-')]
    ]

    plot_column2D = [
        [sg.TabGroup([[sg.Tab('All plots', plot2D_tab1_layout, key='2DTab1'),
                         sg.Tab('True image', plot2D_tab2_layout, key = '2DTab2'),
                         sg.Tab('Blurred image', plot2D_tab3_layout, key = '2DTab3'),
                         sg.Tab('Reconstructed image', plot2D_tab4_layout, key = '2DTab4'),
                         sg.Tab('Uncertainty', plot2D_tab5_layout, key = '2DTab5')]],
                       key='-TABS2D-', title_color='black',
                       selected_title_color='white', tab_location='topleft', font = 'Helvetica 16')]
    ]

    # layout:
    tab2_layout = [
        [sg.Column(options_column2D),
        sg.VSeperator(),
        sg.Column(plot_column2D)]
    ]
    layCol_wel = [
        [sg.Text('\nWelcome to our CUQI Interactive Demo. By using this demo you will get an intuitive understanding of computational uncertainty quantification for inverse problems.', font =medium2_font)],
        [sg.Text('The demo is split up in two sections; one for 1D and 2D deconvolution problems respectively. We recommend you start by using the 1D section first.',font =medium2_font)],
        [sg.Text('The idea is simple: You simply choose one of the given test signal which will be convoluted. For 2D you can also choose your own picture!', font=medium2_font)],
        [sg.Text('Noise will then be added to simulate the measurement of real life data, and from this we will create our bayesian posterior which will be our recreation of the signal', font=medium2_font)],
        [sg.Text('To get the most out of the demo try choosing different prior distributions with various parameters to see how they affect the uncertainty in our recreation', font=medium2_font)],
        [sg.Text('After pressing "Update" various plots will be shown from which you can learn various informations about the signal and the bayesian recreation. Have fun!\n', font = medium2_font)],
        [sg.Image("Cookie-PNG.png",size=(300,300))],
        [sg.Text('For more information about the current work in CUQI done at DTU Compute, visit the following site:',font=small_font),
        sg.Button('CUQI at DTU', enable_events = True, size=(10, 2), font=medium_font)],
        [sg.Text('',font=big_font)],
        [sg.Text('Made by Oliver Birkmose Broager, Magnus Holm, Christian Deding Nielsen and Emilie Nilsson',font=small_font)],
        [sg.Text('DTU',font=medium_font)],
        [sg.Text('February-June 2022',font=small_font)]
    ]
    
    layout_wel = [
        [sg.Push(),sg.Column(layCol_wel,element_justification='c'),sg.Push()]
    ]

    layout = [
        [sg.Push(),sg.Text('CUQIpy Interactive Demo', size=(30, 1),justification='center', font=big_font),sg.Push()],
        [sg.TabGroup([[sg.Tab('Welcome',layout = layout_wel, key='Tab0', title_color = 'black'),
            sg.Tab('1D convolution', tab1_layout, key='Tab1', title_color = 'black'),
                         sg.Tab('2D convolution', tab2_layout, key = 'Tab2')]],
                       key='-TABS-', title_color='black',
                       selected_title_color='white', tab_location='topleft', font = 'Helvetica 16')]]

    
    # Create the GUI and show it without the plot
    window = sg.Window('CUQIpy interactive demo', layout, finalize=True, resizable=True, icon='cookieIcon.ico' ).Finalize()
    window.Maximize()

    # Extract canvas elements to attach plot to
    canvas_elem1 = window['-CANVAS_2D_1-']
    canvas1 = canvas_elem1.TKCanvas

    canvas_elem2 = window['-CANVAS_2D_2-']
    canvas2 = canvas_elem2.TKCanvas

    canvas_elem3 = window['-CANVAS_2D_3-']
    canvas3 = canvas_elem3.TKCanvas

    canvas_elem4 = window['-CANVAS_2D_4-']
    canvas4 = canvas_elem4.TKCanvas

    canvas_elem5 = window['-CANVAS_2D_5-']
    canvas5 = canvas_elem5.TKCanvas

    # Draw the initial figures in the window
    fig1, axs = plt.subplots(nrows = 2, ncols = 2,figsize = (7.2,7.2))
    fig_agg1 = draw_figure(canvas1, fig1)
    axs[0,0].axis('off')
    axs[0,1].axis('off')
    axs[1,0].axis('off')
    axs[1,1].axis('off')

    fig2 = plt.figure(2,figsize = (7.2,7.2))
    fig_agg2 = draw_figure(canvas2, fig2)

    fig3 = plt.figure(3,figsize = (7.2,7.2))
    fig_agg3 = draw_figure(canvas3, fig3)

    fig4 = plt.figure(4,figsize = (7.2,7.2))
    fig_agg4 = draw_figure(canvas4, fig4)

    fig5 = plt.figure(5,figsize = (7.2,7.2))
    fig_agg5 = draw_figure(canvas5, fig5)

    test = [True, True, True, True, True]
    Dist2D = "GaussianCov"
    updated = False

    canvas_elem = window['-CANVAS-']
    canvas = canvas_elem.TKCanvas

    # Draw the initial figure in the window
    fig = plt.figure(6, figsize=(7.2, 7.2))
    fig_agg = draw_figure(canvas, fig)

    # setting Gaussian as default
    Dist1D = "GMRF"
    window['PRIOR_TEXT'].update('Parameters for Gaussian Markov Random Field')
    # window['-GAUSSIAN-'].update(button_color='white on green') # updates buttons
    window['-GAUSSIAN-'].update(button_color=(None, 'green'))
    window['-CAUCHY-'].update(button_color=sg.TRANSPARENT_BUTTON)
    window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
    window['-PAR1-'].update(visible=True)

    window['-SLIDER1-'].update(visible=True)
    window['-PAR1-'].update('Precision')
    # removes buttons if other prior was chosen first
    window['-PAR2-'].update(visible=True)
    window['-BCTYPE-'].update(visible=True)
    window['-PAR2-'].update('Boundary')
    window['-PAR3-'].update(visible=True)
    window['-PAR3-'].update('Order')
    window['-ORDER_1D-'].update(visible=True)
    window['-FIGUP-'].update(visible=False)

    # for input boxes
    test_1D = [True, True, True, True]
    while True: 

        event, values = window.read()
        active_tab = window['-TABS-'].Get()

        if event == sg.WIN_CLOSED:
            break
        
        if active_tab == 'Tab0':
            if event in ('CUQI at DTU', None):
                webbrowser.open("https://www.compute.dtu.dk/english/cuqi", new=0, autoraise=True)
                #os.system("start \"\" https://www.compute.dtu.dk/english/cuqi")
        # 1D
        if active_tab == 'Tab1':

            # Clicked exit button
            if event in ('Exit', None):
                exit()
            
            window['-OUTPUT_2D-'].restore_stdout()
            window['-OUTPUT-'].reroute_stdout_to_here()

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
                            test_1D[3] = True
                        else:
                            window.Element('-SLIDER-SAMPLE-').update(value=100)
                            window.Element(
                                '-INPUT-SAMPLE-').update(background_color='red')
                            test_1D[3] = False
                    except:
                        window.Element('-SLIDER-SAMPLE-').update(value=100)
                        window.Element(
                            '-INPUT-SAMPLE-').update(background_color='red')
                        test_1D[3] = False

                if event == '-SLIDER-SAMPLE-':
                    window.Element(
                        '-INPUT-SAMPLE-').update(int(values['-SLIDER-SAMPLE-']))
                    test_1D[3] = True
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
                            test_1D[2] = True
                        else:
                            window.Element('-SLIDER-CONF-').update(value=95)
                            window.Element(
                                '-INPUT-CONF-').update(background_color='red')
                            test_1D[2] = False
                    except:
                        window.Element('-SLIDER-CONF-').update(value=95)
                        window.Element(
                            '-INPUT-CONF-').update(background_color='red')
                        test_1D[2] = False

                if event == '-SLIDER-CONF-':
                    window.Element(
                        '-INPUT-CONF-').update(int(values['-SLIDER-CONF-']))
                    test_1D[2] = True
                    window.Element(
                        '-INPUT-CONF-').update(background_color=orig_col)

            # show initial signal
            if event == '-SHOW1D-':
                updated_1D = False
                n_std_1D = float(values['-SLIDER-NOISE-'])
                sig_1D = values['-TESTSIG-']
                if sig_1D == "two squares":
                    x1,x2,x3,x4 = [0]*50,[1]*14,[-1]*14,[0]*50
                    sig_1D  = np.array(x1 +x2 +x3 +x4)
                TP_1D = cuqi.testproblem.Deconvolution1D(phantom=sig_1D, noise_std=n_std_1D)
                grid = np.linspace(0, 128, 128)

                plt.figure(6)
                plt.subplot(212).clear()
                plt.subplot(212).axis('off')
                plt.subplot(211).clear()
                plt.subplot(211)
                
                plt.plot(grid, TP_1D.data/max(TP_1D.data),color='green') 
                plt.legend(['Initial signal'], loc=1)
                fig_agg.draw()

            # Select prior distribution
            # buttons change accordingly
            if event == '-GAUSSIAN-':
                Dist1D = "GMRF"
                window['PRIOR_TEXT'].update('Parameters for Gaussian Markov Random Field')
                # window['-GAUSSIAN-'].update(button_color='white on green') # updates buttons
                window['-GAUSSIAN-'].update(button_color=(None, 'green'))
                window['-CAUCHY-'].update(button_color=sg.TRANSPARENT_BUTTON)
                window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
                window['-PAR1-'].update(visible=True)
                window['-SLIDER1-'].update(visible=True, range=(0.01,100))
                window['-PAR1-'].update('Precision')
                # removes buttons if other prior was chosen first
                window['-PAR2-'].update(visible=True)
                window['-BCTYPE-'].update(visible=True)
                window['-PAR2-'].update('Boundary')
                window['-PAR3-'].update(visible=True)
                window['-PAR3-'].update('Order')
                window['-ORDER_1D-'].update(visible=True)
                 #window['-FIGUP-'].update(visible=False)
            elif event == '-LAPLACE-':
                Dist1D = "Laplace_diff"
                window['PRIOR_TEXT'].update('Parameters for Laplace Distribution')
                window['-LAPLACE-'].update(button_color=(None, 'green'))
                window['-GAUSSIAN-'].update(button_color=sg.TRANSPARENT_BUTTON)
                window['-CAUCHY-'].update(button_color=sg.TRANSPARENT_BUTTON)
                window['-PAR1-'].update(visible=True)
                window['-SLIDER1-'].update(visible=True, range=(0.01,100))
                window['-PAR1-'].update('Scale')
                window['-PAR2-'].update(visible=True)  # add new parameter
                window['-PAR2-'].update('Boundary')
                window['-BCTYPE-'].update(visible=True)
                window['-PAR3-'].update(visible=False)
                window['-ORDER_1D-'].update(visible=False)
            elif event == '-CAUCHY-':
                Dist1D = "Cauchy_diff"
                window['PRIOR_TEXT'].update('Parameters for Cauchy Distribution')
                window['-CAUCHY-'].update(button_color=(None, 'green'))
                window['-GAUSSIAN-'].update(button_color=sg.TRANSPARENT_BUTTON)
                window['-LAPLACE-'].update(button_color=sg.TRANSPARENT_BUTTON)
                window['-PAR1-'].update(visible=True)
                window['-SLIDER1-'].update(visible=True,range=(0.01,100))
                window['-PAR1-'].update('Scale')
                window['-PAR2-'].update(visible=True)
                window['-PAR2-'].update('Boundary')
                window['-BCTYPE-'].update(visible=True)
                window['-PAR3-'].update(visible=False)
                window['-ORDER_1D-'].update(visible=False)

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
            show_RSS = values['RSS']
            if event in ('-UPDATE-1D-', None):
                updated_1D = True
                # Get values from input
                par1_1D = float(values['-SLIDER1-'])
                par2_1D = values['-BCTYPE-']
                par3_1D = int(values['-ORDER_1D-'])
                sampsize_1D = int(values['-SLIDER-SAMPLE-'])
                conf = int(values['-SLIDER-CONF-'])
                n_std_1D = float(values['-SLIDER-NOISE-'])

                # Define and compute posterior to Deconvolution problem
                sig = values['-TESTSIG-']
                if sig == "two squares":
                    x1,x2,x3,x4 = [0]*50,[1]*14,[-1]*14,[0]*50
                    sig  = np.array(x1 +x2 +x3 +x4)
                TP_1D = cuqi.testproblem.Deconvolution1D(phantom=sig, noise_std=n_std_1D)

                if Dist1D == "GMRF":
                    TP_1D.prior = getattr(cuqi.distribution, Dist1D)(np.zeros(128), prec = par1_1D, bc_type=par2_1D, order = par3_1D)
                    window['-OUTPUT-'].update(visible=True)
                    window['-LOADTXT-'].update(visible=True)

                if Dist1D == "Laplace_diff":
                    TP_1D.prior = getattr(cuqi.distribution, Dist1D)(location=np.zeros(128), scale=par1_1D, bc_type=par2_1D)
                    window['-OUTPUT-'].update(visible=True)
                    window['-LOADTXT-'].update(visible=True)

                if Dist1D == "Cauchy_diff":
                    TP_1D.prior = getattr(cuqi.distribution, Dist1D)(location=np.zeros(128), scale=par1_1D, bc_type=par2_1D)
                    window['-OUTPUT-'].update(visible=True)
                    window['-LOADTXT-'].update(visible=True)


                try:
                    xs_1D = TP_1D.sample_posterior(sampsize_1D)  # Sample posterior
                except:
                    window['-FIGUP-'].update(visible=True)
                    window['-FIGUP-'].update(text_color='red')
                    window['-FIGUP-'].update('Sampler not implemented')
                    window['-LOADTXT-'].update(visible=False)
                else:
                    window['-FIGUP-'].update('Figure updated!')
                    window['-FIGUP-'].update(text_color='white')
                    window['-FIGUP-'].update(visible=True)

                    samp = xs_1D.samples
                    meansamp = np.mean(samp, axis=-1)
                    error = sum((meansamp - TP_1D.exactSolution)**2)
                    etext = "{:.2e}".format(error)

                    # Update plot
                    grid = np.linspace(0, 128, 128)
                    fig.clear()
                    plt.figure(6)
                    plt.subplot(211)
                    plt.plot(grid, TP_1D.data/max(TP_1D.data),color='green')  # Noisy data
                    plt.legend(['Initial signal'], loc=1)
                    
                    if show_RSS == True:
                        plt.subplot(212)
                        plt.annotate("RSS: " +etext, xy=(0.05, 0.9), xycoords='axes fraction',bbox=dict(boxstyle="square", fc="w"))
                    else:
                        plt.subplot(212)
                  
                    if show_ci and not show_true:
                        xs_1D.plot_ci(conf)
                    elif show_ci and show_true:
                        xs_1D.plot_ci(conf, exact=TP_1D.exactSolution)
                    elif not show_ci and not show_true:
                        samp = xs_1D.samples
                        meansamp = np.mean(samp, axis=-1)
                        plt.plot(grid, meansamp, label='Mean') 
                    elif not show_ci and show_true:
                        samp = xs_1D.samples
                        meansamp = np.mean(samp, axis=-1)
                        plt.plot(grid, meansamp, label='Mean') 
                        plt.plot(grid, TP_1D.exactSolution, color='orange', label='True Signal')

                    fig_agg.draw()

                    # Remove output window
                    window['-LOADTXT-'].update(visible=False)
                    window['-OUTPUT-'].update(visible=False)
                    

            # Show true signal/confidence interval or not

            if ((event == 'TRUE_SIGNAL') or (event == 'PLOT-CONF') or (event == 'RSS') or (event == ('-UPDATE-1D-', None))) and updated_1D == True:
                if not show_ci and not show_true:  # plot mean
                    try:
                        plt.figure(6)
                        if show_RSS == True:
                            plt.subplot(212).clear()
                            plt.annotate("RSS: " +etext, xy=(0.05, 0.9), xycoords='axes fraction',bbox=dict(boxstyle="square", fc="w"))
                        else:
                            plt.subplot(212).clear()
                        samp = xs_1D.samples
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
                        samp = xs_1D.samples
                        plt.figure(6)
                        if show_RSS == True:
                            plt.subplot(212).clear()
                            plt.annotate("RSS: " +etext, xy=(0.05, 0.9), xycoords='axes fraction',bbox=dict(boxstyle="square", fc="w"))
                        else:
                            plt.subplot(212).clear()
                        xs_1D.plot_ci(conf)
                        #plt.ylim(-0.25, 1.25)
                        plt.xlim(0, 128)
                        fig_agg.draw()
                    except:
                        pass
                if show_true and show_ci:
                    try:
                        plt.figure(6)
                        if show_RSS == True:
                            plt.subplot(212).clear()
                            plt.annotate("RSS: " +etext, xy=(0.05, 0.9), xycoords='axes fraction',bbox=dict(boxstyle="square", fc="w"))
                        else:
                            plt.subplot(212).clear()
                        xs_1D.plot_ci(conf, exact=TP_1D.exactSolution)
                        #plt.ylim(-0.25, 1.25)
                        plt.xlim(0, 128)
                        fig_agg.draw()
                    except:
                        pass
                if show_true and not show_ci:
                    try:
                        plt.figure(6)
                        if show_RSS == True:
                            plt.subplot(212).clear()
                            plt.annotate("RSS: " +etext, xy=(0.05, 0.9), xycoords='axes fraction',bbox=dict(boxstyle="square", fc="w"))
                        else:
                            plt.subplot(212).clear()
                        samp = xs_1D.samples
                        meansamp = np.mean(samp, axis=-1)
                        plt.plot(grid, meansamp, label='Mean')
                        plt.plot(grid, TP_1D.exactSolution, color='orange', label='True Signal')
                        # plt.xlabel('x')
                        #plt.ylim(-0.25, 1.25)
                        plt.xlim(0, 128)
                        plt.legend()
                        fig_agg.draw()
                    except:
                        pass
    
        #2D
        if active_tab == 'Tab2':
            # Clicked exit button
            if event == '-EXIT_2D-':
                exit()
            
            window['-OUTPUT-'].restore_stdout()
            window['-OUTPUT_2D-'].reroute_stdout_to_here()
           
            orig_col = window['-RIGHT_SIZE_2D-'].BackgroundColor

            if event:
                window['-FIGUP_2D-'].update(visible = False)
            
            if isinstance(event, str): 
                if event in '-RIGHTA_2D-':
                    try:
                        if float(values['-RIGHTA_2D-']) >= window.Element('ALPHA').Range[0] and float(values['-RIGHTA_2D-'])<= window.Element('ALPHA').Range[1]:
                            window.Element('ALPHA').update(value = values['-RIGHTA_2D-'])
                            window.Element('-RIGHTA_2D-').update(background_color = orig_col)
                            test[0] = True
                        else:
                            window.Element('ALPHA').update(value = 0.05)
                            window.Element('-RIGHTA_2D-').update(background_color = 'red')
                            test[0] = False
                    except:
                        window.Element('ALPHA').update(value = 0.05)
                        window.Element('-RIGHTA_2D-').update(background_color = 'red')
                        test[0] = False

                if event in 'ALPHA':
                    window.Element('-RIGHTA_2D-').update(values['ALPHA'])
                    test[0] = True
                    window.Element('-RIGHTA_2D-').update(background_color = orig_col)
                
                if event in '-RIGHT2_2D-':
                    try:
                        if int(values['-RIGHT2_2D-']) in range(window['-SLIDER-SAMPLE_2D-'].Range[0],window['-SLIDER-SAMPLE_2D-'].Range[1]):
                            window.Element('-SLIDER-SAMPLE_2D-').update(value = int(values['-RIGHT2_2D-']))
                            window.Element('-RIGHT2_2D-').update(background_color = orig_col)
                            test[2] = True
                        else:
                            window.Element('-SLIDER-SAMPLE_2D-').update(value = 100)
                            window.Element('-RIGHT2_2D-').update(background_color = 'red')
                            test[2] = False
                    except:
                        window.Element('-SLIDER-SAMPLE_2D-').update(value = 100)
                        window.Element('-RIGHT2_2D-').update(background_color = 'red')
                        test[2] = False
                if event in '-SLIDER-SAMPLE_2D-':
                    window.Element('-RIGHT2_2D-').update(int(values['-SLIDER-SAMPLE_2D-']))
                    test[2] = True
                    window.Element('-RIGHT2_2D-').update(background_color = orig_col)
                
                if event in '-RIGHTn_2D-':
                    try:
                        if float(values['-RIGHTn_2D-']) >= window.Element('-SLIDER-NOISE_2D-').Range[0] and float(values['-RIGHTn_2D-'])<= window.Element('-SLIDER-NOISE_2D-').Range[1]:
                            window.Element('-SLIDER-NOISE_2D-').update(value = values['-RIGHTn_2D-'])
                            window.Element('-RIGHTn_2D-').update(background_color = orig_col)
                            test[3] = True
                        else:
                            window.Element('-SLIDER-NOISE_2D-').update(value = 0.05)
                            window.Element('-RIGHTn_2D-').update(background_color = 'red')
                            test[3] = False
                    except: 
                        window.Element('-SLIDER-NOISE_2D-').update(value = 0.05)
                        window.Element('-RIGHTn_2D-').update(background_color = 'red')
                        test[3] = False
                if event in '-SLIDER-NOISE_2D-':
                    window.Element('-RIGHTn_2D-').update(values['-SLIDER-NOISE_2D-'])
                    test[3] = True
                    window.Element('-RIGHTn_2D-').update(background_color = orig_col)
                
                if event in '-RIGHT_SIZE_2D-':
                    try:
                        if int(values['-RIGHT_SIZE_2D-']) in range(window['-SLIDER-SIZE_2D-'].Range[0],window['-SLIDER-SIZE_2D-'].Range[1]):
                            window.Element('-SLIDER-SIZE_2D-').update(value = int(values['-RIGHT_SIZE_2D-']))
                            window.Element('-RIGHT_SIZE_2D-').update(background_color = orig_col)
                            test[4] = True
                        elif int(values['-RIGHT_SIZE_2D-']) not in range(window['-SLIDER-SIZE_2D-'].Range[1], window['-SLIDER-SIZE_2D-'].Range[1]):
                            window.Element('-SLIDER-SIZE_2D-').update(value = 128)
                            window.Element('-RIGHT_SIZE_2D-').update(background_color = 'red')
                            test[4] = False
                    except:
                        window.Element('-SLIDER-SIZE_2D-').update(value = 128)
                        window.Element('-RIGHT_SIZE_2D-').update(background_color = 'red')
                        test[4] = False
                if event in '-SLIDER-SIZE_2D-':
                    window.Element('-RIGHT_SIZE_2D-').update(int(values['-SLIDER-SIZE_2D-']))
                    test[4] = True
                    window.Element('-RIGHT_SIZE_2D-').update(background_color = orig_col) 

            if event == '-FILE-':
                window['-TESTSIG_2D-'].update(value = '')
                window['file_error'].update(visible = False)
                window['-IB_2D-',5].update(visible = True)
            # if isinstance(event, str):  
            if event == '-TESTSIG_2D-':
                window['-FILE-'].update(value = '')
                print('')
                window['file_error'].update(visible = False)
                window['-IB_2D-',5].update(visible = False)
                iTog2D[5] = False
                window['-ITX_2D-',5].update(visible = bool(iTog2D[5]))
            if values['-TESTSIG_2D-'] == '' and values['-FILE-'] == '':
                window['-TESTSIG_2D-'].update(value = 'satellite')
                window['file_error'].update(visible = False)
            
            if event == '-GAUSSIAN_2D-':
                Dist2D = "GaussianCov"
                window['ORDER_2D'].update(visible=True)
                window['PRIOR_TEXT_2D'].update('Parameters for Gaussian Markov Random Field')
                window['ORDER_TEXT'].update(visible=True)
                window['ALPHA_TEXT'].update('Precision') 
                window['ALPHA_TEXT'].update(visible=True)  
                window['ALPHA'].update(value = 1)
                window['ALPHA'].update(visible=True)
                window['-GAUSSIAN_2D-'].update(button_color=(None,'green'))
                window['-CAUCHY_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
                window['-LAPLACE_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)

            elif event == '-LAPLACE_2D-':
                test[1] = True
                window['ORDER_TEXT'].update(visible=False)
                window['ORDER_2D'].update(visible=False)
                window['ALPHA_TEXT'].update('Scale')
                window['ALPHA_TEXT'].update(visible = True)
                window['ALPHA_TEXT'].update('Scale')  
                Dist2D = "Laplace_diff"
                window['PRIOR_TEXT_2D'].update('Parameters for Laplace Distribution')
                window['-LAPLACE_2D-'].update(button_color=(None,'green'))
                window['-GAUSSIAN_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
                window['-CAUCHY_2D-'].update(button_color = sg.TRANSPARENT_BUTTON)
            elif event == '-CAUCHY_2D-':
                Dist2D = "Cauchy_diff"
                test[1] = True
                window['ORDER_TEXT'].update(visible=False)
                window['ORDER_2D'].update(visible=False)
                window['ALPHA_TEXT'].update('Scale')
                window['ALPHA_TEXT'].update(visible = True)
                window['ALPHA_TEXT'].update('Scale')  
                window['PRIOR_TEXT_2D'].update('Parameters for Cauchy Distribution')
                window['-CAUCHY_2D-'].update(button_color=(None, 'green'))
                window['-GAUSSIAN_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
                window['-LAPLACE_2D-'].update(button_color=sg.TRANSPARENT_BUTTON)
            
            if sum(test) != 5:
                window['up2d'].update(disabled=True)
                window['up2d'].update(button_color='gray')
            elif sum(test) == 5:
                window['up2d'].update(disabled=False)
                window['up2d'].update(button_color=sg.theme_button_color())

            ## Shows image dimensions
            if values['-FILE-'] != '':
                filename = values["-FILE-"]
                if os.path.exists(filename) and os.path.splitext(filename)[1] in file_types2:
                    image = Image.open(values["-FILE-"]).convert('RGB')
                    window['-ITX_2D-',5].update(value = f"Original Image Dimensions: %s" % (image.size,))
                else:
                    window['-IB_2D-',5].update(visible = False)
                    iTog2D[5] = False
                    window['-ITX_2D-',5].update(visible = bool(iTog2D[5]))

            if event == '-FILE-':
                filename = values["-FILE-"]
                if (os.path.exists(filename) and os.path.splitext(filename)[1] in file_types2) or filename == '':
                    window['up2d'].update(disabled = False)
                    window['up2d'].update(button_color = sg.theme_button_color())
                    window['file_error'].update(visible = False)
                else:
                    window['up2d'].update(disabled = True)
                    window['up2d'].update(button_color = 'gray')
                    window['file_error'].update(visible = True)

            if event == 'show2D':
                updated = False
                axs[0,0].clear()
                axs[0,1].clear()
                axs[1,0].clear()
                axs[1,1].clear()
                axs[0,0].axis('off')
                axs[0,1].axis('off')
                axs[1,0].axis('off')
                axs[1,1].axis('off')
                fig2.clear()
                fig_agg2.draw()
                fig3.clear()
                fig_agg3.draw()
                fig4.clear()
                fig_agg4.draw()
                fig5.clear()
                fig_agg5.draw()
                
                if values['-FILE-'] == '':
                    sig = values['-TESTSIG_2D-']
                    sz = int(values['-SLIDER-SIZE_2D-'])
                    n_std = float(values['-SLIDER-NOISE_2D-'])
                    TP_2D = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = sig, noise_std=n_std)
                    plt.figure(1)
                    axs[0,0].imshow(np.reshape(TP_2D.exactSolution,(-1,sz)), cmap='gray')
                    axs[0,0].set_title('True image')

                    axs[0,1].imshow(np.reshape(TP_2D.data, (-1, sz)), cmap = 'gray')
                    axs[0,1].set_title('Blurred image')
                    fig_agg1.draw()

                    fig2.clear()
                    plt.figure(2)
                    TP_2D.exactSolution.plot()
                    plt.axis("off")
                    fig_agg2.draw()

                    fig3.clear()
                    plt.figure(3)
                    TP_2D.data.plot()
                    plt.axis("off")
                    fig_agg3.draw()

                    window['up2d'].update(disabled = False)
                    window['up2d'].update(button_color = sg.theme_button_color())
                elif values['-FILE-'] != '':
                    filename = values["-FILE-"]
                    if os.path.exists(filename) and os.path.splitext(filename)[1] in file_types2:
                    
                        sz = int(values['-SLIDER-SIZE_2D-'])
                        n_std = float(values['-SLIDER-NOISE_2D-'])
                        
                        image = Image.open(values["-FILE-"]).convert('RGB')
                        image = image.resize((sz,sz))
                        image = cuqi.data.rgb2gray(image)
                        TP_2D = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = image, noise_std = n_std)
                        plt.figure(1)
                        axs[0,0].imshow(image, cmap = 'gray')
                        axs[0,0].set_title('True image')

                        axs[0,1].imshow(np.reshape(TP_2D.data, (-1, sz)), cmap = 'gray')
                        axs[0,1].set_title('Blurred image')
                        fig_agg1.draw()

                        fig2.clear()
                        plt.figure(2)
                        plt.imshow(image, cmap = 'gray')
                        plt.axis("off")
                        fig_agg2.draw()

                        fig3.clear()
                        plt.figure(3)
                        TP_2D.data.plot()
                        plt.axis("off")
                        fig_agg3.draw()
                    else:
                        window['file_error'].update(visible = True)
                        window['up2d'].update(disabled = True)
                        window['up2d'].update(button_color = 'gray')

        # Clicked update button
            #if event in ('Update', None):
            if event in ('up2d', None):
                updated = True
                #window['-FIGUP-'].update(visible = True)
                #window['-FIGUP-'].update('Loading...')

                # Get values from input
                sz = int(values['-SLIDER-SIZE_2D-'])
                par1 = float(values['ALPHA'])
                par2 = values['BOUNDS_2D']
                order = int(values['ORDER_2D'])
                sampsize = int(values['-SLIDER-SAMPLE_2D-'])
                n_std = float(values['-SLIDER-NOISE_2D-'])
                alpha = float(values['ALPHA'])

                # Define and compute posterior to Deconvolution problem
                if values['-TESTSIG_2D-'] == '':
                    filename = values["-FILE-"]
                    if os.path.exists(filename) and os.path.splitext(filename)[1] in file_types2:
                        window['file_error'].update(visible = False)
                        image = Image.open(values["-FILE-"]).convert('RGB')
                        im = image.resize((sz,sz))
                        sig = cuqi.data.rgb2gray(im)
                        TP_2D = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = sig, noise_std = n_std)
                    else:
                        TP_2D = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = 'satellite', noise_std = n_std)
                        window['file_error'].update(visible = True)
                        window['-TESTSIG_2D-'].update(value = 'satellite')
                        window['-FILE-'].update(value = '')

                else:
                    sig = values['-TESTSIG_2D-']
                    TP_2D = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = sig, noise_std = n_std)
                
                if Dist2D == "GaussianCov": 
                    TP_2D.prior = cuqi.distribution.GMRF(np.zeros(TP_2D.model.domain_dim), prec = alpha, order = order, bc_type = par2, physical_dim=2)
                    window['-LOADTXT2D-'].update(visible = True)
                    window['-OUTPUT_2D-'].update(visible = True)
                    
                
                
                if Dist2D == "Laplace_diff":
                    TP_2D.prior = getattr(cuqi.distribution, Dist2D)(location = np.zeros(TP_2D.model.domain_dim), scale = par1, bc_type = par2, physical_dim = 2)
                    window['-LOADTXT2D-'].update(visible = True)
                    window['-OUTPUT_2D-'].update(visible = True)
                    
                    
                if Dist2D == "Cauchy_diff":
                    TP_2D.prior = getattr(cuqi.distribution, Dist2D)(location = np.zeros(TP_2D.model.domain_dim), scale = par1, bc_type = par2, physical_dim = 2)
                    window['-LOADTXT2D-'].update(visible = True)
                    window['-OUTPUT_2D-'].update(visible = True)
                    
                    
                try:
                    xs = TP_2D.sample_posterior(sampsize) # Sample posterior
                except:
                    window['-FIGUP_2D-'].update(visible = True)
                    window['-FIGUP_2D-'].update(text_color = 'red')
                    window['-FIGUP_2D-'].update('Sampler not implemented')
                else:
                    window['-FIGUP_2D-'].update('Figure updated!')
                    window['-FIGUP_2D-'].update(text_color = 'white')
                    window['-FIGUP_2D-'].update(visible = True)

                    # Remove output window
                    window['-LOADTXT2D-'].update(visible = False)
                    window['-OUTPUT_2D-'].update(visible=False)
                    

                #fig1.clear()
                error_2D = sum((xs.mean() - TP_2D.exactSolution)**2)
                etext_2D  = "{:.2e}".format(error_2D)
                std = np.reshape(np.std(xs.samples,axis=-1),(-1,sz))
                RED = np.zeros((sz,sz))
                std_stand = std/np.max(std)

                axs[0,0].clear()
                axs[0,1].clear()
                axs[1,0].clear()
                axs[1,1].clear()
                axs[0,0].axis('off')
                axs[0,1].axis('off')
                axs[1,0].axis('off')
                axs[1,1].axis('off')

                plt.figure(1)
                axs[0,0].imshow(np.reshape(TP_2D.exactSolution,(-1,sz)), cmap='gray')
                axs[0,0].set_title('True image')

                axs[0,1].imshow(np.reshape(TP_2D.data, (-1, sz)), cmap = 'gray')
                axs[0,1].set_title('Blurred image')

                axs[1,0].imshow(np.reshape(xs.mean(), (-1, sz)), cmap = 'gray')
                axs[1,0].set_title('Reconstructed image')

                axs[1,1].imshow(np.reshape(np.std(xs.samples,axis=-1), (-1, sz)))
                axs[1,1].set_title('Uncertainty')
                
                fig_agg1.draw()

                fig2.clear()
                plt.figure(2)
                TP_2D.exactSolution.plot()
                plt.axis("off")
                fig_agg2.draw()

                fig3.clear()
                plt.figure(3)
                TP_2D.data.plot()
                plt.axis("off")
                fig_agg3.draw()

                fig4.clear()
                plt.figure(4)
                #xs.plot_mean()
                plt.imshow(np.reshape(xs.mean(), (-1, sz)), cmap = 'gray')
                plt.title("Sample mean \nRSS: " + etext_2D)
                plt.axis("off")
                fig_agg4.draw()

                fig5.clear()
                plt.figure(5)
                uncPlt = plt.imshow(np.reshape(np.std(xs.samples,axis=-1), (-1, sz)))
                plt.title('Sample standard deviation')
                cBarUnc = plt.colorbar(uncPlt,fraction=0.046, pad=0.04)
                cBarUnc.ax.set_xlabel('std')
                plt.axis("off")
                fig_agg5.draw()
                
            if (event == 'Uncer' or event == 'up2d') and updated:
                if values['Uncer'] == True:
                    try:
                        plt.figure(1)
                        axs[1,0].axis("off")
                        axs[1,0].imshow(RED,cmap='autumn', alpha = std_stand)
                        axs[1,0].set_title('Reconstructed image')
                        fig_agg1.draw()

                        plt.figure(4)
                        #plt.axis("off")

                        plt.imshow(RED,cmap='autumn', alpha = std_stand)
                        cBarRed = plt.colorbar(ScalarMappable(norm=Normalize(vmin=0, vmax=np.max(std)),cmap=LinearSegmentedColormap.from_list("",["white","red"])),fraction=0.046, pad=0.04)
                        cBarRed.ax.set_xlabel('std')
                        fig_agg4.draw()
                    except: pass
                else:
                    try:
                        plt.figure(1)
                        axs[1,0].clear()
                        axs[1,0].axis("off")
                        axs[1,0].imshow(np.reshape(xs.mean(), (-1, sz)), cmap = 'gray')
                        axs[1,0].set_title('Reconstructed image')
                        fig_agg1.draw()

                        fig4.clear()
                        plt.figure(4)
                        #xs.plot_mean()
                        plt.axis("off")
                        plt.title("Sample mean \n RSS: " + etext_2D)
                        plt.imshow(np.reshape(xs.mean(), (-1, sz)), cmap = 'gray')
                        #plt.xlabel(etext_2D)
                        fig_agg4.draw()
                    except: pass

            # Clicking info button: showing and removing information
            for i in range(iNum2D):
                    if event == ('-IB_2D-',i):
                        for j in range(iNum2D):
                            if j == i:
                                iTog2D[j] = not iTog2D[j]
                                window[('-ITX_2D-',j)].update(visible=bool(iTog2D[j]))
                                continue
                            iTog2D[j] = False
                            window[('-ITX_2D-',j)].update(visible=bool(iTog2D[j])) 
    
    window.close()

if __name__ == '__main__':
    sg.change_look_and_feel('Dark Blue 12') #Theme
    main() #Runs main method


# %%
