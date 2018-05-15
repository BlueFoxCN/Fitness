import pickle
import cv2
import numpy as np
from enum import Enum

from queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

from detect import DetectThread
from capture import CaptureThread
from visualize import VisualizeThread

from cfgs.config import cfg

if __name__ == "__main__":

    capture_queue = Queue(maxsize=cfg.max_queue_len)
    result_queue = Queue(maxsize=cfg.max_queue_len)
    visualize_queue = Queue(maxsize=cfg.max_queue_len)
    enable_capture = Event()
    enable_predict = Event()

    # capture_thread = CaptureThread(capture_queue, enable_capture, video_file="20180513_1.mp4")
    capture_thread = CaptureThread(capture_queue, enable_capture)
    capture_thread.start()

    detect_thread = DetectThread(capture_queue, result_queue, enable_capture, enable_predict)
    detect_thread.start()

    visualize_thread = VisualizeThread(result_queue, enable_predict, visualize_queue, output_path="output_2.mp4")
    visualize_thread.start()

    '''
    while True:
        frame = visualize_queue.get()
        # frame = np.random.rand(500, 800, 3)
        print(frame.shape)
        cv2.imshow('frame', frame)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    '''
