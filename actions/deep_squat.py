import numpy as np
from enum import Enum
import time
import matplotlib
import cv2

from cfgs.config import cfg
from .action import Action
from .frame import *

class DeepSquatTip(Enum):
    tip_1 = 1
    tip_2 = 2
    tip_3 = 3

# the part oder:
# 0:nose         1:neck           2:right_shoulder   3:right_elbow
# 4:right_wrist  5:left_shoulder  6:left_elbow       7:left_wrist
# 8:right_hip    9:right_knee     10:right_ankle    11:left_hip
# 12:left_knee   13:left_ankle    14:right_eye       15:left_eye
# 16:right_ear   17:left_ear

class DeepSquat(Action):
    def __init__(self, data_path):
        self.frame_interval = 2
        self.shown_part = [0, 1, 2, 3, 4, 8, 9, 10, 14, 16]
        self.temp = 0
        Action.__init__(self, data_path, self.frame_interval)

    def _draw_result(self, img, peaks):
        canvas = np.copy(img) # B,G,R order
        cmap = matplotlib.cm.get_cmap('hsv')
        for i, peak in enumerate(peaks):
            if len(peak) == 0 or i not in self.shown_part:
                continue
            rgba = np.array(cmap(1 - i/18. - 1./36))
            rgba[0:3] *= 255
            cv2.circle(img, peaks[i][0:2], 4, cfg.part_colors[i], thickness=-1)
            img_with_result = cv2.addWeighted(img, 0.5, canvas, 0.5, 0)
        return img_with_result

    def _correct_tip(self):
        tips = []
        text_list = []
        bottom_frames = [(idx, e) for idx, e in enumerate(self.info_buffer) if e.is_status('bottom')]

        if len(bottom_frames) == 0:
            return tips, text_list

        last_bottom_frame_idx = bottom_frames[-1][0]
        last_bottom_frame = self.info_buffer[last_bottom_frame_idx]

        # 1. 下蹲时是否到位
        def check_1(frame):
            # check if the right hip is two much higher than the right knee
            if frame.r_hip.y != None and frame.r_knee.y != None and \
                frame.r_knee.y - frame.r_hip.y > 10:
                return True
            else:
                return False

        if DeepSquatTip.tip_1 not in last_bottom_frame.tips:
            if check_1(last_bottom_frame):
                tips.append("tips/tip_1.wav")
                text_list.append("下蹲不到位")
                self.info_buffer[last_bottom_frame_idx].tips.append(DeepSquatTip.tip_1)
                return tips, text_list

        # 2. 膝盖是否太靠前了
        def check_2(frame):
            # check if the right knee is two much in front of the right ankle
            print(frame.r_knee.x - frame.r_ankle.x)
            if frame.r_knee.y != None and frame.r_knee.y != None and \
                frame.r_knee.x - frame.r_ankle.x > 10:
                return True
            else:
                return False

        if DeepSquatTip.tip_2 not in last_bottom_frame.tips:
            if check_2(last_bottom_frame):
                tips.append("tips/tip_2.wav")
                text_list.append("膝盖太靠前了")
                self.info_buffer[last_bottom_frame_idx].tips.append(DeepSquatTip.tip_2)
                return tips, text_list

        # 3. 腰背是否没有挺直
        def check_3(frame):
            # check if the right shoulder is two much in front of the right hip
            if frame.r_shoulder.y != None and frame.r_hip.y != None and \
                frame.r_shoulder.x - frame.r_hip.x > 40:
                return True
            else:
                return False

        if DeepSquatTip.tip_3 not in last_bottom_frame.tips:
            if check_3(last_bottom_frame):
                tips.append("tips/tip_3.wav")
                text_list.append("腰背没有挺直")
                self.info_buffer[last_bottom_frame_idx].tips.append(DeepSquatTip.tip_3)
                return tips, text_list


        # 4. 表扬动作到位
        if True:
            if len(last_bottom_frame.tips) == 0:
                tips.append("tips/good_tip_1.wav")
                text_list.append("动作很到位")
            self.temp = (self.temp + 1) % 30
        return tips, text_list



    def push_new_frame(self, peaks, img):
        std_img, std_mask = self.next_frame()

        if len(self.info_buffer) >= cfg.max_buffer_len:
            del(self.info_buffer[0])
        self.info_buffer.append(Frame(peaks, img))

        # use the right hip to determine the action cycle
        # get the y-coord of right_hip in past frames
        r_hip_y = [e.r_hip.y for e in self.info_buffer]

        # if r_hip_y is the greatest in the neighbourhood with length 50, then it is a bottom frame
        # if r_hip_y is the smallest in the neighbourhood with length 50, then it is a top frame

        key_frame = ""
        if len(r_hip_y) >= 50:
            if r_hip_y[-25] == np.min(r_hip_y[-50:]) and np.where(r_hip_y[-50:-25] == r_hip_y[-25])[0].shape[0] == 0:
                key_frame = "top"
                self.info_buffer[-25].set_status("top")
            if r_hip_y[-25] == np.max(r_hip_y[-50:]) and np.where(r_hip_y[-50:-25] == r_hip_y[-25])[0].shape[0] == 0:
                key_frame = "bottom"
                self.info_buffer[-25].set_status("bottom")

        # judge whether the action is correct and generate the tips
        tips, text_list = self._correct_tip()

        # generate the shown image
        img = self._draw_result(img, peaks)
        img_resize = cv2.resize(img, (cfg.output_width, cfg.output_height))

        blend = cv2.addWeighted(img_resize, 0.5, std_img, 0.5, 0)
        blend_fg = cv2.bitwise_and(blend, blend, mask=std_mask)
        mask_inv = cv2.bitwise_not(std_mask)
        img_bg = cv2.bitwise_and(img_resize, img_resize, mask=mask_inv)
        overlap_result_img = blend_fg + img_bg

        result_img = np.zeros((cfg.output_height, 2 * cfg.output_width, 3), dtype=np.uint8)
        result_img[:, :cfg.output_width] = overlap_result_img
        # result_img[:, :cfg.output_width] = img_resize
        result_img[:, cfg.output_width:] = std_img

        return tips, key_frame, result_img
