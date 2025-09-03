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

'''
'shoulder_pan.pos':  , -> motor_1
'shoulder_lift.pos': , -> motor_2
'elbow_flex.pos':  , -> motor_3
'wrist_flex.pos':  ,  -> motor_5
'wrist_roll.pos':  ,  -> motor_4
'gripper.pos':   -> gripper

'''



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
            self.piper.GetArmLowSpdInfoMsgs().motor_3.foc_status.driver_enable_status,
            self.piper.GetArmLowSpdInfoMsgs().motor_4.foc_status.driver_enable_status,
            self.piper.GetArmLowSpdInfoMsgs().motor_5.foc_status.driver_enable_status,
            self.piper.GetArmLowSpdInfoMsgs().motor_6.foc_status.driver_enable_status,
        ]):
            self.piper.EnableArm(7)
            self.piper.GripperCtrl(0,1000,0x01, 0)
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
        控制 Piper 关节 1,2,3,5,4 , 
        action: dict 来自 SO101Leader.get_action()
        """

        # SO101 -> Piper 对应表
        # 关节: (SO101 名称, Piper Motor ID)
        mapping = [
            ("shoulder_pan.pos", 1),   # J1 -> motor_1
            ("shoulder_lift.pos", 2),  # J2 -> motor_2
            ("elbow_flex.pos", 3),     # J3 -> motor_3
            ("wrist_roll.pos", 4),     # wrist_roll -> motor_4 -> 
            ("wrist_flex.pos", 5),     # J5 -> motor_5
            (None, 6),                 #
           
        ]

        # 方向修正，每个关节一个（顺序对应上面 mapping）
        motor_dir = [-1, 1, 1 ,-1 ,1, -1]

        # SO101 限位 (rad)
        so101_limits = [
            [-1.57, 1.57],    # shoulder_pan
            [-1.57,  1],        # shoulder_lift [-90 -- 60 degree] 60=1.04 radian
            [-1.67, 1.67],       # elbow_flex
            [-1.57, 1.57],    # wrist_roll
            [-1.57, 1.57],    # wrist_flex
            [0, 0],           # J4（占位，不受控）

        ]

        # Piper 限位 (rad)
        piper_limits = [
            [-1.57, 1.57],    # J1
            [0, 2.6],        # J2  0-150 degree .1.57+ 1.04 (60 degree) =2.6
            [-2.9, 0],       # J3
            [-1.8, 1.8],           # J4
            [-1.2, 1.2],    # J5
            [0, 0],    # J6（占位）
        ]

        factor = 57295.7795  # rad -> 指令系数

        cmds = [0, 0, 0, 0, 0, 0]  # 初始化 6 电机命令（motor_4 先不管）
        #motor_4 不受控，留在 cmds[3] = 0。

        # 遍历关节，逐个处理
        for i, (so101_key, motor_id) in enumerate(mapping):
            if so101_key is None:

                # 占位，不受控（保持 0 或未来扩展）
                cmds[motor_id - 1] = 0
                continue


            raw_val = action[so101_key] * math.pi / 180   # Leader 默认是度，转弧度
            raw_val *= motor_dir[i]                      # 方向修正

            # 限幅 (SO101)
            so_min, so_max = so101_limits[i]
            val = max(so_min, min(so_max, raw_val))

            # 归一化
            norm = (val - so_min) / (so_max - so_min)

            # 映射到 Piper 限位
            p_min, p_max = piper_limits[i]
            projected_val = p_min + norm * (p_max - p_min)

            # 转成指令
            cmd = int(projected_val * factor)
            cmds[motor_id - 1] = cmd   # motor_id 从1开始，Python list 从0开始

            # 调试输出
            print(f"[调试] J{motor_id}: raw={raw_val:.3f}, limited={val:.3f}, "
                  f"projected={projected_val:.3f}, cmd={cmd}")

        # 发送给 Piper
        self.piper.MotionCtrl_2(0x01, 0x01, 100, 0x00)
        self.piper.JointCtrl(*cmds)
        print(f"[Piper] 已发送命令: {cmds}")


            # ========== 2. Gripper 部分 ==========
        if "gripper.pos" in action:
            gripper_dir = 1
            val = action["gripper.pos"] * math.pi / 180
            val *= gripper_dir

            # 限位
            so101_min, so101_max = 0, 1.67   # rad
            val = max(so101_min, min(so101_max, val))

            # 映射到 mm
            piper_min, piper_max = 0, 100    # mm
            norm = (val - so101_min) / (so101_max - so101_min)
            projected_val_mm = piper_min + norm * (piper_max - piper_min)

            # 转换为 int (mm*1000)
            gripper_cmd = int(round(projected_val_mm * 1000))

            # 下发 Gripper 命令
            self.piper.GripperCtrl(abs(gripper_cmd), 1000, 0x01, 0)
             # 调试打印
            print(f"[Piper][Gripper] 目标开度={projected_val_mm:.3f} mm "
                f"(SO101Leader原值={val:.3f} rad)")




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
            time.sleep(0.005)
    except KeyboardInterrupt:
        print("\n\n[系统] 停止程序")
    finally:
        leader.disconnect()
        piper.disconnect()
