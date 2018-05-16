from .action import Action

class DeepSquat(Action):
    def __init__(self, data_path):
        self.frame_interval = 2
        Action.__init__(self, data_path, self.frame_interval)
