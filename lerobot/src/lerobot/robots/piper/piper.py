# lerobot/robots/piper/piper.py
import numpy as np
from lerobot.robots.robot import ManipulatorRobot
from .config_piper import PiperConfig   # 后面再写

class PiperRobot(ManipulatorRobot):
    name = "piper"
    config_class = PiperConfig

    # 1. 生命周期 ----------------------------------------------------------
    def __init__(self, cfg):
        super().__init__(cfg)
        self.cfg = cfg
        self._connected = False

    def connect(self):
        print(f"[Piper] connect() called, port={self.cfg.port}")
        self._connected = True

    def disconnect(self):
        print("[Piper] disconnect() called")
        self._connected = False

    # 2. 数据钩子 ----------------------------------------------------------
    def read(self):
        # 占位：7 个 0（关节+夹爪）
        return {"joint": np.zeros(7, dtype=np.float32)}

    def write(self, action):
        # 占位：打印目标
        print(f"[Piper] write -> {action['joint']}")

    # 3. 可选钩子 ----------------------------------------------------------
    def calibrate(self):   pass
    def setup_motors(self): pass