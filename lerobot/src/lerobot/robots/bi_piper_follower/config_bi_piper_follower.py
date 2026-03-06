#!/usr/bin/env python

from dataclasses import dataclass, field

from lerobot.cameras import CameraConfig

from ..config import RobotConfig


@RobotConfig.register_subclass("bi_piper_follower")
@dataclass
class BiPiperFollowerConfig(RobotConfig):
    # CAN ports or interface names for left and right Piper arms
    left_arm_port: str
    right_arm_port: str

    # Top-level disable_torque_on_disconnect (applies to both arms if not overridden)
    disable_torque_on_disconnect: bool = True

    # Optional behavior flags for each arm
    left_arm_disable_torque_on_disconnect: bool | None = None
    left_arm_max_relative_target: int | None = None
    left_arm_use_degrees: bool = False

    right_arm_disable_torque_on_disconnect: bool | None = None
    right_arm_max_relative_target: int | None = None
    right_arm_use_degrees: bool = False

    # Shared cameras between both arms (e.g. handeye, fixed, extra)
    cameras: dict[str, CameraConfig] = field(default_factory=dict)

