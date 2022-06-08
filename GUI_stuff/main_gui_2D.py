#%%
#!/usr/bin/env python
# Basic packages
from argparse import FileType
from email.policy import default
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import matplotlib.cm
import matplotlib.colors as mpc
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

file_types = [("JPEG (*.jpg)", "*.jpg"),("PNG (*.png)", "*.png"),
              ("All files (*.*)", "*.*")]
file_types2 = ['.png','.PNG','.JPG', '.jpg', '.jpeg']
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

def main():
    test = True
    # Define the GUI layout
    big_font = 'Courier 20 bold'
    medium_font = 'Courier 16'
    small_font = 'Helvetica 12'

    # initialising toggles for info buttons:
    # number of info buttons
    iNum2D = 6
    iTog2D = np.full((iNum2D,) , False )

    options_column = [
        [sg.Text('CUQIpy Interactive Demo', size=(40, 3), justification='center', font=big_font)],
        [sg.Text('Choose test signal', font =medium_font)],
        [sg.Combo(['astronaut','cat','camera','satellite', 'grains', 'smooth', 'threephases','binary'],key = '-TESTSIG_2D-' , default_value='satellite', enable_events=True, readonly = True),
        sg.Text("Or choose a file ", key = 'CF', visible = True), sg.Input(key='-FILE-', visible = True, size = (20,10), enable_events = True), 
        sg.FileBrowse(file_types=file_types, visible = True, enable_events = True, target = '-FILE-'), 
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',4)),
        sg.Text('error in image path', visible = False, enable_events = True, key = 'file_error', text_color = 'white', background_color = 'red', font = small_font)], #key = 'Browse'
        [sg.pin(sg.Text('Files must be PNG or JPEG.', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[4]), key= ('-ITX_2D-',4)))],
        [sg.Text('Image size:', font = small_font), 
        sg.Slider(range=(8, 1024), default_value=128, resolution=8, size=(20, 10), orientation='h', key='-SLIDER-SIZE_2D-', enable_events = True, disable_number_display=True),
        sg.Input('128', key='-RIGHT_SIZE_2D-', visible = True, enable_events = True, size = (5,1)),
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), visible = False, key = ('-IB_2D-',5))],
        [sg.pin(sg.Text('Image Dimension: ( , )', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[5]), key= ('-ITX_2D-',5)))],
        [sg.Text('Noise std:'), sg.Slider(range=(0.01, 1), default_value=0.05, resolution=0.01, size=(20, 10), orientation='h', key='-SLIDER-NOISE_2D-', enable_events = True, disable_number_display=True), 
        sg.Input('0.05', key='-RIGHTn_2D-', visible = True, enable_events = True, size = (5,1)),
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',0))],
        [sg.pin(sg.Text('Change standard deviation of the normally distributed noise. \nValues range from 0.01 to 1.', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[0]), key= ('-ITX_2D-',0)))],
        [sg.Button('Show initial signal', key = 'show2D')],
        [sg.Text('_'*120)],
        [sg.Text('Choose prior distribution', font =medium_font)], 
        [sg.Button('Gaussian', image_data = resize_base64_image("gauss2d.png", (150,300)), key = '-GAUSSIAN_2D-', button_color=('black', 'Green'), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font), 
        sg.Button('Laplace', image_data = resize_base64_image("laplace2d.png", (150,300)), key = '-LAPLACE_2D-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font), 
        sg.Button('Cauchy', image_data = resize_base64_image("cauchy2d.png", (150,300)), key = '-CAUCHY_2D-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font),
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',3))], 
        [sg.pin(sg.Text('something about the priors - diff things', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[3]), key= ('-ITX_2D-',3)))],
        [sg.Text('Set parameters for gaussian distribution', font =medium_font, key = 'PRIOR_TEXT_2D', visible = True)],
        [place(sg.Text('Precision Matrix Type', key = 'ORDER_TEXT', font = small_font)),place(sg.Combo([0,1,2],default_value = 0, key = 'ORDER', size = (5,1)))], 
        [place(sg.Text('Alpha',key = 'ALPHA_TEXT', font = small_font)),place(sg.Slider((0,10),default_value=0.05, resolution=0.01, key = 'ALPHA',  size=(20, 10),orientation='h', disable_number_display=True,  enable_events = True)), 
        place(sg.InputText('0.1', key='-RIGHTA_2D-', visible = True, enable_events = True, size = (5,0.8), background_color = None))],
        [place(sg.Text('Prior std', font = small_font, key = '-PAR1_2D-', visible = True)), 
        place(sg.Slider(range=(0.01, 1.0), default_value=0.1, resolution = 0.01, orientation='h', enable_events = True, disable_number_display=True, key='-SLIDER1_2D-', visible = True, size = (20,10))), 
        place(sg.InputText('0.1', key='-RIGHT1_2D-', visible = True, enable_events = True, size = (5,1)))],
        [sg.Text('_'*120)],
        [sg.Text('Plot options', font = medium_font)],
        [sg.Text('Sample size', font = small_font), 
        sg.Slider(range=(10, 1000), default_value=10, resolution=10, size=(20, 10), orientation='h', key='-SLIDER-SAMPLE_2D-', enable_events = True, disable_number_display=True),
        sg.Input('10', key='-RIGHT2_2D-', enable_events = True, size = (5,0.8)),
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',1))],
        [sg.pin(sg.Text('Change sample size. Choosing large values \nmay cause long computation time.', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[1]), key= ('-ITX_2D-',1)))],
        [sg.Checkbox('Add uncertainty overlay', default=False, key='Uncer', enable_events = True, font = small_font),
        sg.Button(image_data=resize_base64_image("info.png", (30,30)), border_width=0 , button_color=sg.theme_background_color(), key = ('-IB_2D-',2))],
        [sg.pin(sg.Text('The uncertainty image is added as a red overlay on the reconstruction.\nThe values are scaled so the largest std value is red and smaller\nvalues are become more transparent. Gaussian prior will often result in\na completely red overlay.', text_color='black' , background_color = 'light yellow', visible= bool(iTog2D[2]), key= ('-ITX_2D-',2)))],
        [sg.Button('Run', size=(10, 1), font=medium_font, enable_events=True, key = 'up2d'),
        sg.Button('Exit', size=(10, 1), font=medium_font),
        sg.Text('Figure updated', visible = False, key = '-FIGUP_2D-', text_color = 'red', font= medium_font, enable_events = True)],
        [sg.Multiline(size=(20,1.5), no_scrollbar = True, auto_refresh = True, autoscroll = True, reroute_stdout = True, visible = False, key='-OUTPUT_2D-')]
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

    plot_column = [
        [sg.TabGroup([[sg.Tab('All plots', plot2D_tab1_layout, key='2DTab1'),
                         sg.Tab('True image', plot2D_tab2_layout, key = '2DTab2'),
                         sg.Tab('Blurred image', plot2D_tab3_layout, key = '2DTab3'),
                         sg.Tab('Reconstructed image', plot2D_tab4_layout, key = '2DTab4'),
                         sg.Tab('Uncertainty', plot2D_tab5_layout, key = '2DTab5')]],
                       key='-TABS2D-', title_color='black',
                       selected_title_color='white', tab_location='topleft', font = 'Helvetica 16')]
    ]

    # layout:
    layout = [
        [sg.Column(options_column),
        sg.VSeperator(),
        sg.Column(plot_column),]
    ]

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
    fig1, axs = plt.subplots(nrows = 2, ncols = 2,figsize = (6,6))
    fig_agg1 = draw_figure(canvas1, fig1)
    axs[0,0].axis('off')
    axs[0,1].axis('off')
    axs[1,0].axis('off')
    axs[1,1].axis('off')

    fig2 = plt.figure(2,figsize = (6,6))
    fig_agg2 = draw_figure(canvas2, fig2)

    fig3 = plt.figure(3,figsize = (6,6))
    fig_agg3 = draw_figure(canvas3, fig3)

    fig4 = plt.figure(4,figsize = (6,6))
    fig_agg4 = draw_figure(canvas4, fig4)

    fig5 = plt.figure(5,figsize = (6,6))
    fig_agg5 = draw_figure(canvas5, fig5)

    test = [True, True, True, True, True]
    Dist = "GaussianCov"
   # Dist = values['-DIST_2D-'] # setting Gaussian as default
    while True:

        # Read current events and values from GUI
        event, values = window.read()

        # Clicked exit button
        if event in ('Exit', None):
            exit()
         
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
            
           
            if event in '-RIGHT1_2D-':
                try:
                    if float(values['-RIGHT1_2D-']) >= window.Element('-SLIDER1_2D-').Range[0] and float(values['-RIGHT1_2D-'])<= window.Element('-SLIDER1_2D-').Range[1]:
                        window.Element('-SLIDER1_2D-').update(value = values['-RIGHT1_2D-'])
                        window.Element('-RIGHT1_2D-').update(background_color = orig_col)
                        test[1] = True
                    else:
                        window.Element('-SLIDER1_2D-').update(value = 0.05)
                        window.Element('-RIGHT1_2D-').update(background_color = 'red')
                        test[1] = False
                except: 
                    window.Element('-SLIDER1_2D-').update(value = 0.05)
                    window.Element('-RIGHT1_2D-').update(background_color = 'red')
                    test[1] = False
            if window.Element('-RIGHT1_2D-').visible == False:
                test[1] = True
                
            if event in '-SLIDER1_2D-':
                window.Element('-RIGHT1_2D-').update(values['-SLIDER1_2D-'])
                test[1] = True
                window.Element('-RIGHT1_2D-').update(background_color = orig_col)
            
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
        
       

        
        if event == '-GAUSSIAN_2D-' or event == '-LAPLACE_2D-' or event == '-CAUCHY_2D-':
            window.Element('ALPHA').update(value = 0.05)
            window.Element('-RIGHTA_2D-').update(value = 0.05)
            window.Element('-RIGHTA_2D-').update(background_color = orig_col)
            test[0] = True
            window.Element('-SLIDER1_2D-').update(value = 0.05)
            window.Element('-RIGHT1_2D-').update(value = 0.05)
            window.Element('-RIGHT1_2D-').update(background_color = orig_col)
            test[1] = True
        if event == '-GAUSSIAN_2D-':
            Dist = "GaussianCov"
            window['ORDER'].update(value = '0',values = ['0', '1', '2'])
            window['ORDER_TEXT'].update('Precision Matrix Type')
            window['PRIOR_TEXT_2D'].update('Set parameters for gaussian distribution')
            window['ORDER_TEXT'].update(visible=True)
            window['ALPHA_TEXT'].update('Alpha') 
            window['ALPHA_TEXT'].update(visible=True)  
            window['ORDER'].update(visible=True)
            window['ALPHA'].update(value = 0.05)
            window['ALPHA'].update(visible=True)
            window['ALPHA'].update(range = (0,10))
            window['-GAUSSIAN_2D-'].update(button_color=(None,'green'))
            window['-CAUCHY_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-LAPLACE_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-PAR1_2D-'].update(visible = True)
            window['-SLIDER1_2D-'].update(visible=True)
            window['-RIGHT1_2D-'].update(visible=True)
            window['-PAR1_2D-'].update('Prior std')
        elif event == '-LAPLACE_2D-':
            test[1] = True
            window['ORDER_TEXT'].update('Boundary')
            window['ALPHA_TEXT'].update('Scale')
            window['ALPHA_TEXT'].update(visible = True)
            window['ORDER'].update(value = 'zero', values = ['zero', 'periodic'])
            window['ALPHA_TEXT'].update('Scale')  
            window['ALPHA'].update(visible = True)
            window['ALPHA'].update(range = (0,1))
            Dist = "Laplace_diff"
            window['PRIOR_TEXT_2D'].update('Set parameters for laplace distribution')
            window['-LAPLACE_2D-'].update(button_color=(None,'green'))
            window['-GAUSSIAN_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-CAUCHY_2D-'].update(button_color = sg.TRANSPARENT_BUTTON)
            window['-PAR1_2D-'].update(visible = False)
            window['-SLIDER1_2D-'].update(visible=False)
            window['-RIGHT1_2D-'].update(visible=False)

        elif event == '-CAUCHY_2D-':
            Dist = "Cauchy_diff"
            test[1] = True
            window['ORDER_TEXT'].update('Boundary')
            window['ALPHA_TEXT'].update('Scale')
            window['ALPHA_TEXT'].update(visible = True)
            window['ORDER'].update(value = 'zero', values = ['zero', 'periodic'])
            window['ALPHA_TEXT'].update('Scale')  
            window['ALPHA'].update(visible = True)
            window['ALPHA'].update(range = (0,1))
            window['PRIOR_TEXT_2D'].update('Set parameters for cauchy distribution')
            window['-CAUCHY_2D-'].update(button_color=(None, 'green'))
            window['-GAUSSIAN_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-LAPLACE_2D-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-SLIDER1_2D-'].update(visible=False)
            window['-RIGHT1_2D-'].update(visible=False)
            window['-PAR1_2D-'].update(visible = False)

        
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
                TP = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = sig, noise_std=n_std)
                plt.figure(1)
                axs[0,0].imshow(np.reshape(TP.exactSolution,(-1,sz)), cmap='gray')
                axs[0,0].set_title('True image')

                axs[0,1].imshow(np.reshape(TP.data, (-1, sz)), cmap = 'gray')
                axs[0,1].set_title('Blurred image')
                fig_agg1.draw()

                fig2.clear()
                plt.figure(2)
                TP.exactSolution.plot()
                plt.axis("off")
                fig_agg2.draw()

                fig3.clear()
                plt.figure(3)
                TP.data.plot()
                plt.axis("off")
                fig_agg3.draw()

                window['up2d'].update(disabled = False)
                window['up2d'].update(button_color = sg.theme_button_color())
            elif values['-FILE-'] != '':
                filename = values["-FILE-"]
                if os.path.exists(filename) and os.path.splitext(filename)[1] in file_types2:
                
                    sz = int(values['-SLIDER-SIZE_2D-'])
                    
                    image = Image.open(values["-FILE-"]).convert('RGB')
                    window['-ImDim-'].update(value = image.size)
                    image = image.resize((sz,sz))
                    image = cuqi.data.rgb2gray(image)
                    TP = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = image, noise_std = n_std)
                    plt.figure(1)
                    axs[0,0].imshow(image, cmap = 'gray')
                    axs[0,0].set_title('True image')

                    axs[0,1].imshow(np.reshape(TP.data, (-1, sz)), cmap = 'gray')
                    axs[0,1].set_title('Blurred image')
                    fig_agg1.draw()

                    fig2.clear()
                    plt.figure(2)
                    plt.imshow(image, cmap = 'gray')
                    plt.axis("off")
                    fig_agg2.draw()

                    fig3.clear()
                    plt.figure(3)
                    TP.data.plot()
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
            par1 = float(values['-SLIDER1_2D-'])
            par2 = values['ORDER']
            sampsize = int(values['-SLIDER-SAMPLE_2D-'])
            n_std = float(values['-SLIDER-NOISE_2D-'])
            try:
                order = int(values['ORDER'])
            except: pass
            alpha = float(values['ALPHA'])

            # Define and compute posterior to Deconvolution problem
            if values['-TESTSIG_2D-'] == '':
                filename = values["-FILE-"]
                if os.path.exists(filename) and os.path.splitext(filename)[1] in file_types2:
                    window['file_error'].update(visible = False)
                    image = Image.open(values["-FILE-"]).convert('RGB')
                    im = image.resize((sz,sz))
                    sig = cuqi.data.rgb2gray(im)
                    TP = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = sig, noise_std = n_std)
                else:
                    TP = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = 'satellite', noise_std = n_std)
                    window['file_error'].update(visible = True)
                    window['-TESTSIG_2D-'].update(value = 'satellite')
                    window['-FILE-'].update(value = '')

            else:
                sig = values['-TESTSIG_2D-']
                TP = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = sig, noise_std = n_std)
            
            if Dist == "GaussianCov": 
                TP.prior = cuqi.distribution.GMRF(np.zeros(TP.model.domain_dim), alpha, order = order, physical_dim=2)
                window['-OUTPUT_2D-'].update(visible = True)
            
            
            if Dist == "Laplace_diff":
                 TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(TP.model.domain_dim), scale = par1, bc_type = par2, physical_dim = 2)
                 window['-OUTPUT_2D-'].update(visible = True)
                
            if Dist == "Cauchy_diff":
                TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(TP.model.domain_dim), scale = par1, bc_type = par2)
                window['-OUTPUT_2D-'].update(visible = True)
                
            try:
                xs = TP.sample_posterior(sampsize) # Sample posterior
            except:
                window['-FIGUP_2D-'].update(visible = True)
                window['-FIGUP_2D-'].update(text_color = 'red')
                window['-FIGUP_2D-'].update('Sampler not implemented')
            else:
                window['-FIGUP_2D-'].update('Figure updated!')
                window['-FIGUP_2D-'].update(text_color = 'white')
                window['-FIGUP_2D-'].update(visible = True)

                # Remove output window
                window['-OUTPUT_2D-'].update(visible=False)

            #fig1.clear()
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
            axs[0,0].imshow(np.reshape(TP.exactSolution,(-1,sz)), cmap='gray')
            axs[0,0].set_title('True image')

            axs[0,1].imshow(np.reshape(TP.data, (-1, sz)), cmap = 'gray')
            axs[0,1].set_title('Blurred image')

            axs[1,0].imshow(np.reshape(xs.mean(), (-1, sz)), cmap = 'gray')
            axs[1,0].set_title('Reconstructed image')

            axs[1,1].imshow(np.reshape(np.std(xs.samples,axis=-1), (-1, sz)))
            axs[1,1].set_title('Uncertainty')
            
            fig_agg1.draw()

            fig2.clear()
            plt.figure(2)
            TP.exactSolution.plot()
            plt.axis("off")
            fig_agg2.draw()

            fig3.clear()
            plt.figure(3)
            TP.data.plot()
            plt.axis("off")
            fig_agg3.draw()

            fig4.clear()
            plt.figure(4)
            xs.plot_mean()
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
                    plt.axis("off")
                    plt.imshow(RED,cmap='autumn', alpha = std_stand)
                    cBarRed = plt.colorbar(matplotlib.cm.ScalarMappable(norm=mpc.Normalize(vmin=0, vmax=np.max(std)),cmap=mpc.LinearSegmentedColormap.from_list("",["white","red"])),fraction=0.046, pad=0.04)
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
                    xs.plot_mean()
                    plt.axis("off")
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
            


if __name__ == '__main__':
    sg.change_look_and_feel('Dark Blue 12') #Theme
    main() #Runs main method