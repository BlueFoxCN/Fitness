import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import askquestion
# from demo_neo import Extractor
from PIL import Image
from PIL import ImageTk
import os
import threading
import time
import numpy as np
import uuid
import cv2
import pdb
from GUI.widgets import *



class Extractor_GUI():
    def __init__(self):
        self.__init_gui()
        # self.__init_model()
    def __init_gui(self):
       
        self.window = tk.Tk()
        self.window.wm_title('VideoText')
        self.window.config(background = '#FFFFFF')

        self.canvas = ICanvas(self.window, width = 800, height = 800)
        self.canvas.grid(row = 0, column = 0)

        self.fm_control = tk.Frame(self.window, width=800, height=100, background = '#FFFFFF')
        self.fm_control.grid(row = 1, column=0, padx=10, pady=2)
        self.btn_prev_frame = tk.Button(self.fm_control, text='Start', command = self.__action_read_frame)
        self.btn_prev_frame.grid(row = 0, column=0, padx=10, pady=2)
        self.lb_current_frame = tk.Label(self.fm_control, background = '#FFFFFF')
        self.lb_current_frame.grid(row = 0, column=1, padx=10, pady=2)
        self.lb_current_frame['text'] = '----'
        self.btn_next_frame = tk.Button(self.fm_control, text='Next Frame', command = None)
        self.btn_next_frame.grid(row = 0, column=2, padx=10, pady=2)


        self.fm_status = tk.Frame(self.window, width = 100, height = 100, background = '#FFFFFF')
        self.fm_status.grid(row = 0, column=1, padx=10, pady=2)
  
        self.btn_prev_frame1 = tk.Button(self.fm_status, text='Start1', command = self.__action_read_frame)
        self.btn_prev_frame1.grid(row = 0, column=0, padx=10, pady=2)
        

        self.btn_next_frame3 = tk.Button(self.fm_status, text='Start2', command = None)
        self.btn_next_frame3.grid(row = 1, column=0, padx=10, pady=20)



    def __init_model(self):
        def init():
           
            self.cnt_status = STATE_INITIALIZING
            self.ext = Extractor()
            self.cnt_status = STATE_READY
            self.__update_btn_new()
           
        threading.Thread(target = init).start()

    def __action_read_frame(self):
        self.from_video()

    def from_video(self):

        cap = cv2.VideoCapture(0)
        idx = 0
        while True:
            ret,frame = cap.read()
            # print(frame)
            img = cv2.transpose(frame)
            img = cv2.flip(img,1)
            print(img.shape)

            self.canvas.add(img)
            self.window.update_idletasks()#快速重画屏幕  
            self.window.update()


    def __update_status_bar(self):
        self.lb_status['text'] = self.cnt_status
        if self.cnt_status == STATE_READY or self.cnt_status == STATE_FILE_ERROR:
            self.btn_new['state'] = 'normal'
        else:
            self.btn_new['state'] = 'disabled'
        self.lb_status.after(500, self.__update_status_bar)

    def do(self):
        pass

    
    def wait_for_result(self):
        print("over")
        # if self.cnt_status == STATE_READY or self.cnt_status == STATE_FILE_ERROR:
        #     self.collections_frame = self.ext.gui_frames
        #     if len(self.collections_frame)  <= 0:
        #         self.btn_next_frame['state'] = 'disabled' 
        #         self.btn_prev_frame['state'] = 'disabled'
        #         print("********this vodeo is passed*********please next******************")
        #         return
        #     self.collections_text = self.ext.gui_preds
        #     self.cnt_current_frame = 0
        #     self.cnt_total_frame = len(self.collections_frame)
        #     self.__update_control_bar()
        #     self.__update_canvas_frame()
        # else:
        #     self.window.after(1000, self.wait_for_result)


    def launch(self):
        self.window.mainloop()


if __name__ == '__main__':
    ext = Extractor_GUI()
    ext.launch()
    # ext.from_video()
