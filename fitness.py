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

    capture_thread = CaptureThread(capture_queue, enable_capture)
    capture_thread.start()

    detect_thread = DetectThread(capture_queue, result_queue, enable_capture, enable_predict)
    detect_thread.start()

    visualize_thread = VisualizeThread(result_queue, enable_predict, visualize_queue, output_path="output.mp4")
    # visualize_thread.run()
    # vi = VisualizeThread()

