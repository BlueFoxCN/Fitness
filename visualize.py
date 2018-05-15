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

class Mode(Enum):
    OVERLAP = 1
    SIDE_BY_SIDE = 2

class VisualizeThread(Thread):
    def __init__(self, result_queue, enable_predict, visualize_queue, output_path=None):
        Thread.__init__(self)
        self.result_queue = result_queue
        self.visualize_queue = visualize_queue
        self.enable_predict = enable_predict

        self.img_queue = []

        f = open(cfg.std_data_path, 'rb')
        std_data = pickle.load(f)
        self.std_masks = [e[0] for e in std_data]
        self.std_imgs = [e[1] for e in std_data]
        self.std_peaks = [e[2] for e in std_data]

        self.std_height, self.std_width, _ = self.std_imgs[0].shape

        # for each frame, each peak has the format (x_coord, y_coord)
        x_min = np.min([np.min([e[0] for e in one_frame_peaks]) for one_frame_peaks in self.std_peaks])
        x_max = np.max([np.max([e[0] for e in one_frame_peaks]) for one_frame_peaks in self.std_peaks])
        y_min = np.min([np.min([e[1] for e in one_frame_peaks]) for one_frame_peaks in self.std_peaks])
        y_max = np.max([np.max([e[1] for e in one_frame_peaks]) for one_frame_peaks in self.std_peaks])

        std_width = x_max - x_min
        std_height = y_max - y_min
        self.std_crop_width = int(std_width * 1.3)
        self.std_crop_height = int(std_height * 1.3)

        if self.std_crop_width / cfg.output_width > self.std_crop_height / cfg.output_height:
            self.std_crop_height = int(self.std_crop_width / cfg.output_width * cfg.output_height)
        else:
            self.std_crop_width = int(self.std_crop_height / cfg.output_height * cfg.output_width)

        std_x_center = (x_max + x_min) / 2
        std_y_center = (y_max + y_min) / 2

        self.std_crop_x_start = int(std_x_center - self.std_crop_width / 2)
        self.std_crop_x_end = int(std_x_center + self.std_crop_width / 2)
        self.std_crop_y_start = int(std_y_center - self.std_crop_height / 2)
        self.std_crop_y_end = int(std_y_center + self.std_crop_height / 2)

        self.std_frame_num = len(self.std_masks)

        self.trans_std_imgs = []
        self.trans_std_masks = []
        self.trans_std_peaks = []

        for std_idx in range(self.std_frame_num):
            self.transform_std_img(std_idx)

        self.output_path = output_path

        # 0 for overlap, 1 for side by side
        self.mode = Mode.SIDE_BY_SIDE

        self.init_frame_num = 10
        self.frame_idx = 0

    def transform_std_img(self, std_idx):
        if len(self.trans_std_imgs) > std_idx:
            return [self.trans_std_imgs[std_idx], self.trans_std_masks[std_idx], self.trans_std_peaks[std_idx]]

        pad_left = np.maximum(0, 0 - self.std_crop_x_start)
        pad_top = np.maximum(0, 0 - self.std_crop_y_start)
        pad_right = np.maximum(0, self.std_crop_x_end - self.std_width)
        pad_bot = np.maximum(0, self.std_crop_y_end - self.std_height)

        trans_std_img = np.pad(self.std_imgs[std_idx], ((pad_top, pad_bot), (pad_left, pad_right), (0, 0)), 'edge')
        trans_std_mask = np.pad(self.std_masks[std_idx], ((pad_top, pad_bot), (pad_left, pad_right)), 'constant', constant_values=0)

        trans_std_img = trans_std_img[self.std_crop_y_start + pad_top:self.std_crop_y_end + pad_top,
                                      self.std_crop_x_start + pad_left:self.std_crop_x_end + pad_left]
        trans_std_mask = trans_std_mask[self.std_crop_y_start + pad_top:self.std_crop_y_end + pad_top,
                                        self.std_crop_x_start + pad_left:self.std_crop_x_end + pad_left]

        trans_std_img = cv2.resize(trans_std_img, (cfg.output_width, cfg.output_height))
        trans_std_mask = cv2.resize(trans_std_mask, (cfg.output_width, cfg.output_height), cv2.INTER_NEAREST)

        scale = cfg.output_width / self.std_crop_width
        trans_std_peaks = [((e[0] - self.std_crop_x_start) * scale, (e[1] - self.std_crop_y_start) * scale) for e in self.std_peaks[std_idx]]

        self.trans_std_imgs.append(cv2.resize(trans_std_img, (cfg.output_width, cfg.output_height)))
        self.trans_std_masks.append(cv2.resize(trans_std_mask, (cfg.output_width, cfg.output_height), cv2.INTER_NEAREST))
        self.trans_std_peaks.append(trans_std_peaks)

        return [self.trans_std_imgs[std_idx], self.trans_std_masks[std_idx], self.trans_std_peaks[std_idx]]


    def run(self):
        self.init_peaks = []
        self.enable_predict.set()
        std_idx = -1

        if self.output_path != None and cfg.capture_frame_num != -1:
            if self.mode == Mode.SIDE_BY_SIDE:
                videoWrite = cv2.VideoWriter(self.output_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (2 * cfg.output_width, cfg.output_height))
            else:   # The OVERLAP mode
                videoWrite = cv2.VideoWriter(self.output_path, cv2.VideoWriter_fourcc(*'mp4v'), 30, (cfg.output_width, cfg.output_height))

        while True:
            ret = self.result_queue.get()
            if len(ret) == 0:
                break

            '''
            self.img_queue.append(ret)
            # wait until the queue has some images
            if len(self.img_queue) < cfg.min_qsize:
                continue

            # the queue has at least 10 elements
            peaks = [e[0] for e in self.img_queue]
            '''

            peak, img = ret

            std_idx = (std_idx + 1) % self.std_frame_num

            trans_std_peak = self.trans_std_peaks[std_idx]
            trans_std_img = self.trans_std_imgs[std_idx]
            trans_std_mask = self.trans_std_masks[std_idx]


            img_resize = cv2.resize(img, (cfg.output_width, cfg.output_height))

            if self.mode == Mode.SIDE_BY_SIDE:
                result_img = np.zeros((cfg.output_height, 2 * cfg.output_width, 3), dtype=np.uint8)
                result_img[:, :cfg.output_width] = img_resize
                result_img[:, cfg.output_width:] = trans_std_img
            else:   # The OVERLAP mode
                blend = cv2.addWeighted(img_resize, 0.5, trans_std_img, 0.5, 0)
                blend_fg = cv2.bitwise_and(blend, blend, mask=trans_std_mask)
                mask_inv = cv2.bitwise_not(trans_std_mask)
                img_bg = cv2.bitwise_and(img_resize, img_resize, mask=mask_inv)
                result_img = blend_fg + img_bg
            if self.output_path != None and cfg.capture_frame_num != -1:
                videoWrite.write(result_img)
            cv2.imshow('frame', result_img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # self.visualize_queue.put(result_img)

        if self.output_path != None and cfg.capture_frame_num != -1:
            videoWrite.release()
        cv2.destroyAllWindows()
        print("done")

if __name__ == "__main__":
    result_queue = Queue(maxsize=cfg.max_queue_len)
    enable_predict = Event()

    visualize_thread = VisualizeThread(result_queue, enable_predict, output_path="output_2.mp4")
    visualize_thread.start()
