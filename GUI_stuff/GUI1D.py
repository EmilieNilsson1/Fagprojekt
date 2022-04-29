
import PySimpleGUI as sg
import base64
import io
from PIL import Image

def place(elem): 
    return sg.Column([[elem]], pad=(0,0))

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
        [sg.Button('Update', size=(10, 1), font='Helvetica 14'),
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