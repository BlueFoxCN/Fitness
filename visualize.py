import pickle
import cv2
import numpy as np
from enum import Enum
from queue import Queue

from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

from cfgs.config import cfg


import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.messagebox import askquestion
# from fitness import Extractor
from PIL import Image
from PIL import ImageTk
import os
import time
import uuid
import pdb
from GUI.widgets import *

class Mode(Enum):
    OVERLAP = 1
    SIDE_BY_SIDE = 2
    BOTH = 3

class VisualizeThread():
    def __init_gui(self):

        self.window = tk.Tk()
        self.window.wm_title('VideoText')
        self.window.config(background = '#FFFFFF')

        self.canvas = ICanvas(self.window, width = cfg.output_width*2, height = cfg.output_height)
        self.canvas.grid(row = 0, column = 0)

        self.fm_control = tk.Frame(self.window, width=cfg.output_width*2, height=100, background = '#FFFFFF')
        self.fm_control.grid(row = 1, column=0, padx=10, pady=2)
        self.btn_prev_frame = tk.Button(self.fm_control, text='Start', command = self._start)
        self.btn_prev_frame.grid(row = 0, column=0, padx=10, pady=2)
        self.lb_current_frame = tk.Label(self.fm_control, background = '#FFFFFF')
        self.lb_current_frame.grid(row = 0, column=1, padx=10, pady=2)
        self.lb_current_frame['text'] = '----'
        self.btn_next_frame = tk.Button(self.fm_control, text='New', command = None)
        self.btn_next_frame.grid(row = 0, column=2, padx=10, pady=2)


        self.fm_status = tk.Frame(self.window, width = 100, height = 100, background = '#FFFFFF')
        self.fm_status.grid(row = 0, column=1, padx=10, pady=2)
  
        self.btn_prev_frame1 = tk.Button(self.fm_status, text='Start', command = self._start)
        self.btn_prev_frame1.grid(row = 0, column=0, padx=10, pady=2)
        

        self.btn_next_frame3 = tk.Button(self.fm_status, text='New', command = None)
        self.btn_next_frame3.grid(row = 1, column=0, padx=10, pady=20)
        
    def __init__(self, result_queue, enable_predict, visualize_queue, action, output_path=None):

        self.result_queue = result_queue
        self.visualize_queue = visualize_queue
        self.enable_predict = enable_predict
        self.action = action

        self.img_queue = []


        self.output_path = output_path

        self.mode = Mode.BOTH
        # self.mode = Mode.SIDE_BY_SIDE
        # self.mode = Mode.OVERLAP

        self.init_frame_num = 10
        self.frame_idx = 0
        self.__init_gui()
        self.window.mainloop()


    def run(self):
        self.init_peaks = []
        self.enable_predict.set()

        if self.output_path != None and cfg.capture_frame_num != -1:
            if self.mode == Mode.SIDE_BY_SIDE or self.mode == Mode.BOTH:
                videoWrite = cv2.VideoWriter(self.output_path, cv2.VideoWriter_fourcc(*'mp4v'), 20, (2 * cfg.output_width, cfg.output_height))
            else:   # The OVERLAP mode
                videoWrite = cv2.VideoWriter(self.output_path, cv2.VideoWriter_fourcc(*'mp4v'), 20, (cfg.output_width, cfg.output_height))

        frame_idx = 0

        while True:
            ret = self.result_queue.get()
            if len(ret) == 0:
                break

            print(frame_idx)
            print(time.time())
            frame_idx += 1

            '''
            self.img_queue.append(ret)
            # wait until the queue has some images
            if len(self.img_queue) < cfg.min_qsize:
                continue

            # the queue has at least 10 elements
            peaks = [e[0] for e in self.img_queue]
            '''

            peak, img = ret

            trans_std_img, trans_std_mask = self.action.next_frame()

            img_resize = cv2.resize(img, (cfg.output_width, cfg.output_height))

            if self.mode == Mode.SIDE_BY_SIDE:
                result_img = np.zeros((cfg.output_height, 2 * cfg.output_width, 3), dtype=np.uint8)
                result_img[:, :cfg.output_width] = img_resize
                result_img[:, cfg.output_width:] = trans_std_img
            elif self.mode == Mode.OVERLAP:   # The OVERLAP mode
                blend = cv2.addWeighted(img_resize, 0.5, trans_std_img, 0.5, 0)
                blend_fg = cv2.bitwise_and(blend, blend, mask=trans_std_mask)
                mask_inv = cv2.bitwise_not(trans_std_mask)
                img_bg = cv2.bitwise_and(img_resize, img_resize, mask=mask_inv)
                result_img = blend_fg + img_bg
            else:       # The BOTH mode
                blend = cv2.addWeighted(img_resize, 0.5, trans_std_img, 0.5, 0)
                blend_fg = cv2.bitwise_and(blend, blend, mask=trans_std_mask)
                mask_inv = cv2.bitwise_not(trans_std_mask)
                img_bg = cv2.bitwise_and(img_resize, img_resize, mask=mask_inv)
                overlap_result_img = blend_fg + img_bg

                result_img = np.zeros((cfg.output_height, 2 * cfg.output_width, 3), dtype=np.uint8)
                result_img[:, :cfg.output_width] = overlap_result_img
                result_img[:, cfg.output_width:] = trans_std_img


            if self.output_path != None and cfg.capture_frame_num != -1:
                videoWrite.write(result_img)
            # cv2.imshow('frame', result_img)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # self.visualize_queue.put(result_img)
            result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
            # print(result_img.shape)
            self.canvas.add(result_img)
            self.window.update_idletasks()  #快速重画屏幕  
            self.window.update()

        if self.output_path != None and cfg.capture_frame_num != -1:
            videoWrite.release()
        cv2.destroyAllWindows()
        print("done")

    def _start(self):
        self.run()

'''
if __name__ == "__main__":
    result_queue = Queue(maxsize=cfg.max_queue_len)
    enable_predict = Event()

    visualize_thread = VisualizeThread(result_queue, enable_predict, output_path="output_2.mp4")
    visualize_thread.start()
'''
