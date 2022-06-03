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

file_types = [("JPEG (*.jpg)", "*.jpg"),("PNG (*.png)", "*.png"),
              ("All files (*.*)", "*.*")]

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

    # look into enable_events = True
    # Define the GUI layout
    big_font = 'Courier 20 bold'
    medium_font = 'Courier 16'
    small_font = 'Helvetica 12'

    options_column = [
        [sg.Text('CUQIpy Interactive Demo', size=(40, 3), justification='center', font=big_font)],
        [sg.Text('Choose test signal', font =medium_font)],
        [sg.Combo(['astronaut','cat','camera','satellite', 'grains'],key = '-TESTSIG_2D-' , default_value='satellite', enable_events=True),
        sg.Text("Or choose a file ", key = 'CF', visible = True), sg.Input(key='-FILE-', visible = True, size = (20,10), enable_events = True), sg.FileBrowse(file_types=file_types, visible = True, enable_events = True, target = '-FILE-')], #key = 'Browse'
        #sg.Text("Choose a file: ", key = 'CF'), sg.Input(key="-FILE-"), sg.FileBrowse(file_types=file_types, key = 'Browse')],
        [sg.Text('Image size:', font = small_font), 
        sg.Slider(range=(8, 1024), default_value=128, resolution=8, size=(20, 10), orientation='h', key='-SLIDER-SIZE_2D-', enable_events = True, disable_number_display=True),
        sg.T('128', key='-RIGHT_SIZE_2D-', visible = True)],
        [sg.Text('Noise std:'), sg.Slider(range=(0.01, 1), default_value=0.05, resolution=0.01, size=(20, 10), orientation='h', key='-SLIDER-NOISE_2D-', enable_events = True, disable_number_display=True), 
        sg.T('0.05', key='-RIGHTn_2D-', visible = True),sg.Image("info.png",(18,18),tooltip="Change standard deviation of the normally distributed noise. \nValues range from 0.01 to 1.")],
        [sg.Text('Choose prior distribution', font =medium_font)], 
        [sg.Button('Gaussian', image_data = resize_base64_image("gauss2d.png", (150,300)), key = '-GAUSSIAN_2D-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font), 
        sg.Button('Laplace', image_data = resize_base64_image("laplace2d.png", (150,300)), key = '-LAPLACE_2D-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font), 
        sg.Button('Cauchy', image_data = resize_base64_image("cauchy2d.png", (150,300)), key = '-CAUCHY_2D-', button_color=('black', None), border_width = 10, mouseover_colors=('black', 'black'), auto_size_button=True, font = medium_font)], 
        #[sg.Combo(['GaussianCov','Laplace_diff'],key = '-DIST_2D-', default_value='GaussianCov')],
        [sg.Text('Set prior parameters', font =medium_font, key = 'PRIOR_TEXT_2D', visible = True)],
        [place(sg.Text('Precision Matrix Type', key = 'ORDER_TEXT')),place(sg.Combo([0,1,2],default_value = 0, key = 'ORDER'))], 
        [place(sg.Text('Alpha',key = 'ALPHA_TEXT')),place(sg.Slider((0,10),default_value=0.05, resolution=0.01, key = 'ALPHA',  size=(20, 10),orientation='h'))],
        [place(sg.Text('Par1', font = small_font, key = '-PAR1_2D-', visible = False)), 
        place(sg.Slider(range=(0.01, 1.0), default_value=0.1, resolution = 0.01, orientation='h', enable_events = True, disable_number_display=True, key='-SLIDER1_2D-', visible = False, size = (20,10))), 
        place(sg.T('0.1', key='-RIGHT1_2D-', visible = False))],
        [place(sg.Text('Par2', font = small_font, key = '-PAR2_2D-', visible=False)), 
        place(sg.Combo(['zero', 'periodic'], default_value = 'zero', key = '-BCTYPE_2D-', visible=False, size = (10,1)))],
        [sg.Text('Sample size', font = small_font), 
        sg.Slider(range=(100, 5000), default_value=100, resolution=100, size=(20, 10), orientation='h', key='-SLIDER-SAMPLE_2D-', enable_events = True, disable_number_display=True),
        sg.T('1000', key='-RIGHT2_2D-'),sg.Image("info.png",(18,18),tooltip="Change sample size. Choosing large values \nmay cause long computation time.")],
        [sg.Text('Confidence interval', font = small_font), sg.InputText(key = '-TEXT-CONF_2D-', size =(10,10), default_text=90),
        sg.Image("info.png",(18,18),tooltip="Choose size of confidance interval of the reconstructed solution. \nThe confidence interval is computed as percentiles of the posterior samples. \nValues range from 0% to 100%. ")],
        [sg.Checkbox('Show uncertainty', default=False, key='Uncer', enable_events = True)],
        [sg.Button('Update', size=(10, 1), font=medium_font),
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


   # Dist = values['-DIST_2D-'] # setting Gaussian as default
    while True:

        # Read current events and values from GUI
        event, values = window.read()

        # Clicked exit button
        if event in ('Exit', None):
            exit()
        
        window.Element('-RIGHT1_2D-').update(values['-SLIDER1_2D-']) # updates slider values
        window.Element('-RIGHT2_2D-').update(int(values['-SLIDER-SAMPLE_2D-'])) 
        window.Element('-RIGHTn_2D-').update(values['-SLIDER-NOISE_2D-'])
        window.Element('-RIGHT_SIZE_2D-').update(int(values['-SLIDER-SIZE_2D-']))

        if event == '-FILE-':
            window['-TESTSIG_2D-'].update(value = ' ')
        if event in '-TESTSIG_2D-':
            window['-FILE-'].update(value = ' ')

        Dist = "GaussianCov"
        if event == '-GAUSSIAN_2D-':
            Dist = "GaussianCov"
            window['PRIOR_TEXT_2D'].update('Set parameters for gaussian distribution')
            window['ORDER_TEXT'].update(visible=True)
            window['ALPHA_TEXT'].update(visible=True)  
            window['ORDER'].update(visible=True)
            window['ALPHA'].update(visible=True)
            #window['-GAUSSIAN-'].update(button_color='white on green') # updates buttons
            window['-GAUSSIAN_2D-'].update(button_color=(None,'green'))
            window['-CAUCHY_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-LAPLACE_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-PAR1_2D-'].update(visible = True)
            window['-SLIDER1_2D-'].update(visible=True)
            window['-RIGHT1_2D-'].update(visible=True)
            window['-PAR1_2D-'].update('Prior std')
            window['-PAR2_2D-'].update(visible = False) # removes buttons if other prior was chosen first
            window['-BCTYPE_2D-'].update(visible = False)
        elif event == '-LAPLACE_2D-':
            window['ORDER'].update(visible=False)
            window['ALPHA'].update(visible=False)
            window['ORDER_TEXT'].update(visible=False)
            window['ALPHA_TEXT'].update(visible=False)  
            Dist = "Laplace_diff"
            window['PRIOR_TEXT_2D'].update('Set parameters for laplace distribution')
            #window['-LAPLACE-'].update(button_color='white on green')
            window['-LAPLACE_2D-'].update(button_color=(None,'green'))
            window['-GAUSSIAN_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-CAUCHY_2D-'].update(button_color = sg.TRANSPARENT_BUTTON)
            window['-PAR1_2D-'].update(visible = True)
            window['-SLIDER1_2D-'].update(visible=True)
            window['-RIGHT1_2D-'].update(visible=True)
            window['-PAR1_2D-'].update('Scale')
            window['-PAR2_2D-'].update(visible = True) # add new parameter
            window['-PAR2_2D-'].update('Boundary')
            window['-BCTYPE_2D-'].update(visible = True)
            window['-FIGUP_2D-'].update(visible = True)
            window['-FIGUP_2D-'].update('Might take a while')
        elif event == '-CAUCHY_2D-':
            Dist = "Cauchy_diff"
            window['ORDER'].update(visible=False)
            window['ALPHA'].update(visible=False)
            window['ORDER_TEXT'].update(visible=False)
            window['ALPHA_TEXT'].update(visible=False)  
            window['PRIOR_TEXT_2D'].update('Set parameters for cauchy distribution')
            window['-CAUCHY_2D-'].update(button_color=(None, 'green')) #'white on green')
            window['-GAUSSIAN_2D-'].update(button_color= sg.TRANSPARENT_BUTTON)
            window['-LAPLACE_2D-'].update(button_color=sg.TRANSPARENT_BUTTON)
            window['-PAR1_2D-'].update(visible = True)
            window['-SLIDER1_2D-'].update(visible=True)
            window['-RIGHT1_2D-'].update(visible=True)
            window['-PAR1_2D-'].update('Scale')
            window['-PAR2_2D-'].update(visible = True)
            window['-PAR2_2D-'].update('Boundary')
            window['-BCTYPE_2D-'].update(visible = True)
            
    # Clicked update button
        if event in ('Update', None):
            #window['-FIGUP-'].update(visible = True)
            #window['-FIGUP-'].update('Loading...')

            # Get values from input
            sz = int(values['-SLIDER-SIZE_2D-'])
            par1 = float(values['-SLIDER1_2D-'])
            par2 = values['-BCTYPE_2D-']
            sampsize = int(values['-SLIDER-SAMPLE_2D-'])
            conf = int(values['-TEXT-CONF_2D-'])
            n_std = float(values['-SLIDER-NOISE_2D-'])
            order = int(values['ORDER'])
            alpha = float(values['ALPHA'])

            # Define and compute posterior to Deconvolution problem
            if values['-TESTSIG_2D-'] == "Own Picture":
                filename = values["-FILE-"]
                if os.path.exists(filename):
                    image = Image.open(values["-FILE-"]).convert('RGB')
                # if values[0] == True:
                    image = image.resize((sz,sz))
                    TP = cuqi.testproblem.Deconvolution2D(phantom = cuqi.data.rgb2gray(image), noise_std = n_std)
            else:
                sig = values['-TESTSIG_2D-']
                TP = cuqi.testproblem.Deconvolution2D(dim = sz, phantom = sig, noise_std = n_std)
            
            if Dist == "GaussianCov": 
               # TP.prior = getattr(cuqi.distribution, Dist)(np.zeros(128), par1) 
                #TP.prior = cuqi.distribution.GaussianCov(np.zeros(TP.model.domain_dim), 1)
                TP.prior = cuqi.distribution.GMRF(np.zeros(TP.model.domain_dim), alpha, order = order, physical_dim=2)
                window['-OUTPUT_2D-'].update(visible = True)
            
            #elif Dist == "Laplace_diff":
            #    TP.prior = cuqi.distribution.Laplace_diff(np.zeros(TP.model.domain_dim), 1)

            
            
            if Dist == "Laplace_diff":
                 TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(TP.model.domain_dim), scale = par1, bc_type = par2, physical_dim = 2)
                 window['-OUTPUT_2D-'].update(visible = True)
                
            # if Dist == "Cauchy_diff":
            #     TP.prior = getattr(cuqi.distribution, Dist)(location = np.zeros(128), scale = par1, bc_type = par2)
                
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
    
                # Update plot
                # grid = np.linspace(0,128, 128)

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

            axs[1,1].imshow(np.reshape(np.std(xs.samples,axis=-1), (-1, sz)), cmap = 'gray')
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
            xs.plot_std()
            plt.axis("off")
            fig_agg5.draw()

                
                # Print update in console
            print(" Figure updated!")

             

        if values['Uncer']:
            try:
                plt.figure(1)
                axs[1,0].axis("off")
                axs[1,0].imshow(RED,cmap='autumn', alpha = std_stand)
                fig_agg1.draw()

                plt.figure(4)
                plt.axis("off")
                plt.imshow(RED,cmap='autumn', alpha = std_stand)
                fig_agg4.draw()
            except: pass
        else:
            try:
                plt.figure(1)
                axs[1,0].clear()
                axs[1,0].axis("off")
                axs[1,0].imshow(np.reshape(xs.mean(), (-1, sz)), cmap = 'gray')
                fig_agg1.draw()

                fig4.clear()
                plt.figure(4)
                xs.plot_mean()
                plt.axis("off")
                fig_agg4.draw()
            except: pass
        
        # Show true signal
        # # show_true = values['TRUE_SIGNAL_2D']
        # # if show_true:
        # #     try:
        # #         p1 = plt.plot(grid, TP.exactSolution, color = 'darkorange')
        # #         fig_agg.draw()
        # #     except:
        # #         pass
        # # else:
        # #     try:
        # #         p = p1.pop(0)
        # #         p.remove()
        # #         fig_agg.draw()
        # #     except:
        # #         pass


if __name__ == '__main__':
    sg.change_look_and_feel('Dark Blue 12') #Theme
    main() #Runs main method