import time
import math
from functools import cached_property

from ..robot import Robot
from ..utils import ensure_safe_goal_position
from .config_piperX import PiperXConfig
from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

# 导入 PiperX SDK
from pyAgxArm import create_agx_arm_config, AgxArmFactory

class PiperXRobot(Robot):
    config_class = PiperXConfig
    name = "piperX"

    @cached_property
    def action_features(self) -> dict[str, type]:
        """返回 action features"""
        return {
            "shoulder_pan.pos": float,
            "shoulder_lift.pos": float,
            "elbow_flex.pos": float,
            "wrist_flex.pos": float,
            "wrist_roll.pos": float,
            "gripper.pos": float,
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        """返回 observation features"""
        return {
            "shoulder_pan.pos": float,
            "shoulder_lift.pos": float,
            "elbow_flex.pos": float,
            "wrist_flex.pos": float,
            "wrist_roll.pos": float,
            "gripper.pos": float,
            **{
                cam: (self.config.cameras[cam].height,
                      self.config.cameras[cam].width,
                      3)
                for cam in self.cameras
            },
        }

    def calibrate(self):
        """校准方法"""
        print("[PiperX] calibrate called")
        return True

    def configure(self):
        """配置方法"""
        print("[PiperX] configure called")
        return True

    def get_observation(self) -> dict[str, float]:
        """
        获取 PiperX 6 个关节和夹爪的观测信息
        返回 dict:
            {
                "shoulder_pan.pos": float,
                "shoulder_lift.pos": float,
                "elbow_flex.pos": float,
                "wrist_flex.pos": float,
                "wrist_roll.pos": float,
                "gripper.pos": float,
            }
        """
        if not self.connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        
        # 获取关节角度（弧度）
        joint_states = self.robot.get_joint_states()
        if joint_states is None:
            raise RuntimeError("[PiperX] 无法获取关节状态")
        
        # 更新 J6 缓存（用于 send_action() 中保持 J6 当前值）
        self._cached_j6 = joint_states.msg[5]  # J6
        
        # 映射到 SO101 格式
        # 注意：Piper 中 wrist_roll 对应 joint_4, wrist_flex 对应 joint_5
        # 但 PiperX 的关节顺序需要确认，这里先按相同顺序处理
        obs = {
            "shoulder_pan.pos": joint_states.msg[0],   # J1
            "shoulder_lift.pos": joint_states.msg[1],  # J2
            "elbow_flex.pos": joint_states.msg[2],     # J3
            "wrist_flex.pos": joint_states.msg[3],    # J4  
            "wrist_roll.pos": joint_states.msg[4],     # J5
        }
        
        # 获取夹爪状态
        gripper_status = self.gripper.get_gripper_status()
        if gripper_status is not None:
            # piperX 返回的是米，需要转换为与 SO101 兼容的格式（度）
            width_m = gripper_status.msg.width  # 单位：米
            # 转换为度：width_m (0-0.1m) -> 归一化 -> 弧度 -> 度
            # 映射关系：0.0m -> 0度, 0.1m -> 30度 (30 * π/180 弧度)
            gripper_rad = (width_m / 0.1) * (30 * math.pi / 180)  # 归一化到 [0, 30度] 弧度
            gripper_deg = gripper_rad * 180 / math.pi  # 转换为度
            obs["gripper.pos"] = gripper_deg
        else:
            obs["gripper.pos"] = 0.0  # 如果无法获取，返回 0
        
        # 如果使用角度制，转换为角度
        if self.config.use_degrees:
            for key in ["shoulder_pan.pos", "shoulder_lift.pos", "elbow_flex.pos", 
                       "wrist_flex.pos", "wrist_roll.pos"]:
                obs[key] = math.degrees(obs[key])
        
        # 添加相机数据
        for cam_key, cam in self.cameras.items():
            obs[cam_key] = cam.async_read()
        
        return obs

    def is_calibrated(self):
        """是否已校准"""
        return True

    def is_connected(self):
        """是否已连接"""
        return self.connected

    def __init__(self, config: PiperXConfig):
        super().__init__(config)
        self.config = config
        # 创建 PiperX SDK 配置
        robot_cfg = create_agx_arm_config(
            robot="piper_x",
            comm="can",
            channel=config.port,
            interface=config.interface
        )
        # 创建机器人驱动实例
        self.robot = AgxArmFactory.create_arm(robot_cfg)
        self.connected = False
        self.cameras = make_cameras_from_configs(config.cameras)
        # 缓存 J6 当前值，避免每次 send_action() 都调用 get_joint_states()
        self._cached_j6 = 0.0
        # 夹爪执行器（将在 connect() 中初始化）
        self.gripper = None

    def connect(self):
        """连接机器人"""
        if self.connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")
        
        # 初始化夹爪执行器（必须在 connect() 之前调用）
        self.gripper = self.robot.init_effector(self.robot.EFFECTOR.AGX_GRIPPER)
        
        # 连接机器人（初始化 CAN 通信并启动接收线程）
        self.robot.connect()
        
        # 使能所有关节
        print("[PiperX] 正在启用机器人...")
        start = time.time()
        while not self.robot.enable():
            if time.time() - start > 5:
                raise RuntimeError("[PiperX] 使能超时")
            time.sleep(0.1)
        
        # 设置运动模式为 JS 模式（快速响应，无轨迹规划）
        # MOTION_MODE.JS: 快速响应模式，无轨迹规划，适合遥操作
        # 风险：可能导致冲击、振荡、失稳，请测试稳定性
        self.robot.set_motion_mode(self.robot.MOTION_MODE.JS)
        # 注意：JS 模式下速度设置失效，控制器会尽可能快地响应
        # self.robot.set_speed_percent(100)  # JS 模式下此设置无效
        
        self.connected = True
        
        # 连接相机
        for cam in self.cameras.values():
            cam.connect()
        
        print("[PiperX] 已成功连接并使能")

    def disconnect(self):
        """断开连接"""
        if not self.connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        
        # 禁用所有关节
        if self.config.disable_torque_on_disconnect:
            self.robot.disable()
        
        self.connected = False
        
        # 断开相机
        for cam in self.cameras.values():
            cam.disconnect()
        
        print("[PiperX] 已断开连接")

    def send_action(self, action):
        """
        控制 PiperX 关节和 Gripper
        action: dict 来自 SO101Leader.get_action()
        """
        if not self.connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")
        
        # 关节映射关系（与 Piper 相同）
        mapping = [
            ("shoulder_pan.pos", 1),   # J1 -> PiperX joint_1
            ("shoulder_lift.pos", 2),  # J2 -> PiperX joint_2
            ("elbow_flex.pos", 3),     # J3 -> PiperX joint_3
            ("wrist_flex.pos", 4),     # wrist_flex
            ("wrist_roll.pos", 5),     # J5 -> PiperX joint_5
            (None, 6),                 # J6 -> PiperX joint_6 (占位)
        ]
        
        # 方向校正（与 Piper 相同）
        #motor_dir = [-1, 1, 1, 1, -1, -1]  # right corrected direction
        motor_dir = [-1, 1, 1, 1, 1, -1] #fifth joint direction corrected 
        # SO101 限位范围（与 Piper 相同）
        so101_limits = [
            [-1.57, 1.57],    # shoulder_pan
            [-1.57, 1],        # shoulder_lift [-90° ~ 60°]
            [-1.67, 1.67],    # elbow_flex
            [-1.57, 1.57],    # wrist_roll
            [-1.57, 1.57],    # wrist_flex
            [0, 0],           # J6（占位）
        ]
        
        # PiperX 限位范围（弧度，使用与 Piper 相同的限位）
        piperX_limits = [
            [-1.57, 1.57],    # J1 [-90° ~ 90°]  与 Piper 相同
            [0, 2.7],         # J2 [0° ~ 154.7°] 与 Piper 相同
            [-2.8, 0],        # J3 [-160.4° ~ 0°] 与 Piper 相同
            [-1.57, 1.57],    # J4 [-90° ~ 90°]  与 Piper 相同
            [-1.57, 1.57],      # J5 [-68.8° ~ 68.8°]  1.57for piperX 
            [0, 0],           # J6（占位，与 Piper 相同）
        ]
        
        # 使用缓存的 J6 值（在 get_observation() 中更新），避免每次调用 get_joint_states()
        # 优化说明：之前每次 send_action() 都调用 get_joint_states() 获取 J6，导致延迟
        # 现在使用缓存值，因为 get_observation() 已经读取了关节状态并更新了缓存
        current_j6 = self._cached_j6
        
        # 初始化 6 关节目标数组
        target_joints = [0.0] * 6
        target_joints[5] = current_j6  # 保持 J6 当前值
        
        # 处理 J1-J5 映射
        for i, (so101_key, joint_idx) in enumerate(mapping):
            if so101_key is None:
                continue  # J6 已处理，跳过
            
            # 提取 action 值（SO101 Leader 输出的是角度制）
            raw_val = action[so101_key] * math.pi / 180  # 角度转弧度
            
            # 应用方向校正
            raw_val *= motor_dir[i]
            
            # SO101 限位裁剪
            so_min, so_max = so101_limits[i]
            val = max(so_min, min(so_max, raw_val))
            
            # 归一化到 [0, 1]
            norm = (val - so_min) / (so_max - so_min) if (so_max - so_min) > 0 else 0.0
            
            # 映射到 PiperX 限位
            p_min, p_max = piperX_limits[i]
            projected_val = p_min + norm * (p_max - p_min)
            
            # 赋值到对应关节（joint_idx 从 1 开始，数组从 0 开始）
            target_joints[joint_idx - 1] = projected_val
        
        # 发送控制命令
        # 使用 move_js(): 无轨迹规划，快速响应，适合遥操作
        # 注意：move_js() 可能导致冲击、振荡、失稳，请谨慎使用并测试稳定性
        self.robot.move_js(target_joints)  # 快速响应模式
        
        # 处理夹爪控制
        if "gripper.pos" in action:
            # SO101 Leader 输出：度
            gripper_deg = action["gripper.pos"]
            
            # 转换为弧度
            gripper_rad = gripper_deg * math.pi / 180
            
            # 限位到 [0, 30度] 弧度（30 * π/180 ≈ 0.5236 弧度）
            gripper_rad = max(0, min(30 * math.pi / 180, gripper_rad))
            
            # 映射到 piperX 范围 [0.0, 0.1] 米
            width_m = (gripper_rad / (30 * math.pi / 180)) * 0.1
            
            # 调用 piperX API 控制夹爪
            self.gripper.move_gripper(width=width_m, force=1.0)
        
        # 返回原始 SO101 风格 action（与 so101_follower 一致）
        sent_action = {key: action[key] for key in action}
        return sent_action
