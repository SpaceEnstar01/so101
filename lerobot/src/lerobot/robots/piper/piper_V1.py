import time
import math
from dataclasses import dataclass

from ..robot import Robot
from ..utils import ensure_safe_goal_position
from .config_piper import PiperConfig
from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError


# 导入 Piper SDK
from piper_sdk.interface.piper_interface_v2 import C_PiperInterface_V2

class PiperRobot(Robot):
    config_class = PiperConfig
    name = "piper"


    
    @property
    def action_features(self):
        # 返回一个 dict 列出所有可以控制的关节和 gripper
        return {
            "shoulder_pan.pos": 0,
            "shoulder_lift.pos": 0,
            "elbow_flex.pos": 0,
            "wrist_flex.pos": 0,
            "wrist_roll.pos": 0,
            "gripper.pos": 0,
        }

    @property
    def observation_features(self):
        return {
            "shoulder_pan.pos": float,
            "shoulder_lift.pos": float,
            "elbow_flex.pos": float,
            "wrist_flex.pos": float,
            "wrist_roll.pos": float,
            "gripper.pos": float,
            **{cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3)
            for cam in self.cameras},
        }


    def calibrate(self):
        # 如果不需要特殊标定，直接返回
        print("[Piper] calibrate called")
        return True

    def configure(self):
        # 如果不需要特殊配置，直接返回
        print("[Piper] configure called")
        return True


    def get_observation(self) -> dict[str, float]:
        """
        获取 Piper 6 个关节和夹爪的观测信息
        返回 dict:
            {
                "shoulder_pan.pos": float,
                "shoulder_lift.pos": float,
                "elbow_flex.pos": float,
                "wrist_flex.pos": float,
                "wrist_roll.pos": float,
                "gripper.pos": float,  # mm
            }
        """
        if not self.connected:
            raise RuntimeError("[Piper] 机械臂未连接")

        # 获取关节角度
        arm_joint_msgs = self.piper.GetArmJointMsgs()
        # 获取夹爪状态
        arm_gripper_msgs = self.piper.GetArmGripperMsgs()

        obs = {
            "shoulder_pan.pos": arm_joint_msgs.joint_state.joint_1 / 1000.0,
            "shoulder_lift.pos": arm_joint_msgs.joint_state.joint_2 / 1000.0,
            "elbow_flex.pos": arm_joint_msgs.joint_state.joint_3 / 1000.0,
            "wrist_flex.pos": arm_joint_msgs.joint_state.joint_5 / 1000.0,
            "wrist_roll.pos": arm_joint_msgs.joint_state.joint_6 / 1000.0,
            "gripper.pos": arm_gripper_msgs.gripper_state.grippers_angle / 1000.0,  # mm
        }
        # === cameras ===
        for cam_key, cam in self.cameras.items():
            obs[cam_key] = cam.async_read()

        # 打印便于调试
        #print("[Piper] 关节角度 & 夹爪状态:", obs)
        # print(f"夹爪力矩: {arm_gripper_msgs.gripper_state.grippers_effort / 1000.0} N/m")
        # print(f"夹爪状态码: {arm_gripper_msgs.gripper_state.status_code}")

        return obs


    def is_calibrated(self):
        # 直接返回 True
        return True

    def is_connected(self):
        return self.connected






        #-----------------------------------------------------
    def __init__(self, config: PiperConfig):
        super().__init__(config)
        self.config = config
        self.piper = C_PiperInterface_V2(self.config.port)
        self.connected = False
        # === cameras ===
        self.cameras = make_cameras_from_configs(config.cameras)

    def connect(self):
        self.piper.ConnectPort()
        start = time.time()
        # 循环使能电机
        while not all([
            self.piper.GetArmLowSpdInfoMsgs().motor_1.foc_status.driver_enable_status,
            self.piper.GetArmLowSpdInfoMsgs().motor_2.foc_status.driver_enable_status,
            self.piper.GetArmLowSpdInfoMsgs().motor_3.foc_status.driver_enable_status,
            self.piper.GetArmLowSpdInfoMsgs().motor_5.foc_status.driver_enable_status,
            self.piper.GetArmLowSpdInfoMsgs().motor_6.foc_status.driver_enable_status,
        ]):
            self.piper.EnableArm(7)
            self.piper.GripperCtrl(0, 1000, 0x01, 0)
            if time.time() - start > 5:
                raise RuntimeError("Piper使能超时")
            time.sleep(0.1)
        for cam in self.cameras.values():
            cam.connect()
        self.connected = True
        # === connect cameras ===
        for cam in self.cameras.values():
            cam.connect()
        print("[Piper] 已成功连接并使能")

    def disconnect(self):
        self.piper.DisableArm(7)
        self.connected = False
        # === disconnect cameras ===
        for cam in self.cameras.values():
            cam.disconnect()
        print("[Piper] 已断开连接")

    def send_action(self, action):
        """
        控制 Piper 关节和 Gripper
        action: dict 来自 SO101Leader.get_action()
        """
        # 关节映射
        mapping = [
            ("shoulder_pan.pos", 1),
            ("shoulder_lift.pos", 2),
            ("elbow_flex.pos", 3),
            (None, 4),
            ("wrist_flex.pos", 5),
            ("wrist_roll.pos", 6),
        ]
        motor_dir = [-1, 1, 1, 1, 1, -1]
        so101_limits = [
            [-1.57, 1.57], 
            [-1.57, 1], 
            [-1.67, 1.67],
            [0, 0], 
            [-1.57, 1.57], 
            [-1.57, 1.57]
        ]
        piper_limits = [
            [-1.57, 1.57], 
            [0, 2.6], 
            [-2.9, 0],
            [0, 0],
            [-1.2, 1.2], 
            [-2, 2]
        ]
        factor = 57295.7795
        cmds = [0]*6

        for i, (so101_key, motor_id) in enumerate(mapping):
            if so101_key is None:
                cmds[motor_id - 1] = 0
                continue
            raw_val = action[so101_key] * math.pi / 180
            raw_val *= motor_dir[i]
            so_min, so_max = so101_limits[i]
            val = max(so_min, min(so_max, raw_val))
            norm = (val - so_min) / (so_max - so_min)
            p_min, p_max = piper_limits[i]
            projected_val = p_min + norm * (p_max - p_min)
            cmd = int(projected_val * factor)
            cmds[motor_id - 1] = cmd
        self.piper.MotionCtrl_2(0x01, 0x01, 100, 0x00)
        self.piper.JointCtrl(*cmds)

        if "gripper.pos" in action:
            val = action["gripper.pos"] * math.pi / 180
            val = max(0, min(1.67, val))
            gripper_cmd = int(round((val / 1.67) * 100 * 1000))
            self.piper.GripperCtrl(abs(gripper_cmd), 1000, 0x01, 0)
