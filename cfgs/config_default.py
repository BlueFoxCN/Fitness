from easydict import EasyDict as edict

cfg = edict()


# general config
cfg.max_queue_len = 10000

# for capture
cfg.cam_idx = 1
cfg.capture_frame_num = -1
cfg.fps = 10 # choose from 30, 15, 10, 7.5, 6, 5

# for detect
cfg.model_path = "model_files/mobilenetv2_pose_estimation"

# for visualize
cfg.std_data_path = "deep_squat.pkl"

cfg.output_height = 640
cfg.output_width = 480
cfg.min_qsize = 10


