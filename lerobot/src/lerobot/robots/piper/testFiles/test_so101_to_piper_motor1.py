import time
import numpy as np
import sys
import math

sys.path.insert(0, '/home/paris/X/so101/lerobot/src')

# 导入 Leader
from src.lerobot.teleoperators.so101_leader.so101_leader import SO101Leader
from src.lerobot.teleoperators.so101_leader.config_so101_leader import SO101LeaderConfig

# 导入 Piper
from piper_sdk import C_PiperInterface_V2


class Piper:
    def __init__(self, cfg):
        self.port = cfg["port"]
        self.piper = C_PiperInterface_V2(self.port)
        self.connected = False

    def connect(self):
        self.piper.ConnectPort()
        # 循环使能
        start = time.time()
        while not all([
            self.piper.GetArmLowSpdInfoMsgs().motor_1.foc_status.driver_enable_status,
            self.piper.GetArmLowSpdInfoMsgs().motor_2.foc_status.driver_enable_status,
        ]):
            self.piper.EnableArm(7)
            if time.time() - start > 5:
                raise RuntimeError("Piper使能超时")
            time.sleep(0.1)
        self.connected = True
        print("[Piper] 已成功连接并使能")

    def disconnect(self):
        self.piper.DisableArm(7)
        self.connected = False
        print("[Piper] 已断开连接")

    def send_action(self, action):
        """
        这里只控制关节1
        action: dict 来自 SO101Leader.get_action()
        """
        # SO101 -> Piper 映射
        #val = action["shoulder_pan.pos"]
        # 添加 motor_dir
        motor_dir = [-1, -1, -1, -1, -1, -1]  # 对应关节 1~6 的方向修正
        val = action["shoulder_pan.pos"] * math.pi / 180
        val *= motor_dir[0]  # 乘上方向系数，第一关节
        print(f"[DEBUG] shoulder_pan.pos raw value = {val}\n--------")


        # 限位 (根据你之前给的数据，大概范围)
        so101_min, so101_max = -1.57, 1.57
        piper_min, piper_max =-1.57, 1.57

        # 限幅
        val = max(so101_min, min(so101_max, val))

        # 归一化 + 映射到 Piper
        norm = (val - so101_min) / (so101_max - so101_min)
        projected_val = piper_min + norm * (piper_max - piper_min)

        # 转换成指令
        factor = 57295.7795
        cmd = int(projected_val * factor)
        # 调试打印
        print(f"[调试] val={val:.3f}, norm={norm:.3f}, projected_val={projected_val:.3f}, cmd={cmd}")


        # 只控制第1关节，其他置0
        cmds = [cmd, 0, 0, 0, 0, 0]

        self.piper.MotionCtrl_2(0x01, 0x01, 100, 0x00)
        self.piper.JointCtrl(*cmds)
        print(f"[Piper] 已发送关节1角度: {projected_val:.3f} rad (原值={val:.3f})")


if __name__ == "__main__":
    # 初始化 SO101Leader
    leader_cfg = SO101LeaderConfig(port="/dev/ttyACM0", id="R00")
    leader = SO101Leader(leader_cfg)
    leader.connect(calibrate=False)  # 跳过校准

    # 初始化 Piper
    piper_cfg = {"port": "can0"}
    piper = Piper(piper_cfg)
    piper.connect()

    try:
        while True:
            action = leader.get_action()
            piper.send_action(action)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n\n[系统] 停止程序")
    finally:
        leader.disconnect()
        piper.disconnect()
