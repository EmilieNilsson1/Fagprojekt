import PySimpleGUI as sg
import os

layout = [
          [sg.Text('This text is clickable', click_submits=True)],
          [sg.Text('os.system("start \"\" https://google.com/")', enable_events = True, click_submits=True, key='Text Key')],
          [sg.Text('This text is not clickable')],
          [sg.ReadButton('Button that does nothing')]
         ]

form = sg.FlexForm('Demo of clickable Text Elements').Layout(layout)

while True:
    button, values = form.Read()
    if button is None: break
    print(button, values)