#!/usr/bin/env python

import time
from functools import cached_property
from typing import Any

from lerobot.cameras.utils import make_cameras_from_configs

from ..robot import Robot
from ..piper.config_piper import PiperConfig
from ..piper.piper import PiperRobot
from .config_bi_piper_follower import BiPiperFollowerConfig


class BiPiperFollower(Robot):
    """
    Bimanual Piper follower robot composed of two single-arm PiperRobot instances.

    This mirrors the design of BiSO100Follower: a thin wrapper that instantiates
    two underlying single-arm robots, and exposes left_/right_ prefixed
    observation and action features.
    """

    config_class = BiPiperFollowerConfig
    name = "bi_piper_follower"

    def __init__(self, config: BiPiperFollowerConfig):
        super().__init__(config)
        self.config = config

        # Left arm Piper config
        # Use left_arm_disable_torque_on_disconnect if explicitly set, otherwise use top-level value
        left_disable_torque = (
            config.left_arm_disable_torque_on_disconnect
            if config.left_arm_disable_torque_on_disconnect is not None
            else config.disable_torque_on_disconnect
        )
        left_arm_config = PiperConfig(
            id=f"{config.id}_left" if config.id else None,
            calibration_dir=config.calibration_dir,
            port=config.left_arm_port,
            disable_torque_on_disconnect=left_disable_torque,
            max_relative_target=config.left_arm_max_relative_target,
            use_degrees=config.left_arm_use_degrees,
            cameras={},
        )

        # Right arm Piper config
        # Use right_arm_disable_torque_on_disconnect if explicitly set, otherwise use top-level value
        right_disable_torque = (
            config.right_arm_disable_torque_on_disconnect
            if config.right_arm_disable_torque_on_disconnect is not None
            else config.disable_torque_on_disconnect
        )
        right_arm_config = PiperConfig(
            id=f"{config.id}_right" if config.id else None,
            calibration_dir=config.calibration_dir,
            port=config.right_arm_port,
            disable_torque_on_disconnect=right_disable_torque,
            max_relative_target=config.right_arm_max_relative_target,
            use_degrees=config.right_arm_use_degrees,
            cameras={},
        )

        self.left_arm = PiperRobot(left_arm_config)
        self.right_arm = PiperRobot(right_arm_config)
        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def _motors_ft(self) -> dict[str, type]:
        # Prefix all joint/gripper features with left_ / right_
        left = {f"left_{name}": ftype for name, ftype in self.left_arm.action_features.items()}
        right = {f"right_{name}": ftype for name, ftype in self.right_arm.action_features.items()}
        return left | right

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        return (
            self.left_arm.is_connected()
            and self.right_arm.is_connected()
            and all(cam.is_connected for cam in self.cameras.values())
        )

    def connect(self, calibrate: bool = True) -> None:
        self.left_arm.connect()
        self.right_arm.connect()

        for cam in self.cameras.values():
            cam.connect()

        if calibrate:
            self.calibrate()

    @property
    def is_calibrated(self) -> bool:
        return self.left_arm.is_calibrated() and self.right_arm.is_calibrated()

    def calibrate(self) -> None:
        self.left_arm.calibrate()
        self.right_arm.calibrate()

    def configure(self) -> None:
        self.left_arm.configure()
        self.right_arm.configure()

    def setup_motors(self) -> None:
        # PiperRobot currently does not define a dedicated setup_motors;
        # keep this for API symmetry with other robots, guard with hasattr.
        if hasattr(self.left_arm, "setup_motors"):
            self.left_arm.setup_motors()  # type: ignore[call-arg]
        if hasattr(self.right_arm, "setup_motors"):
            self.right_arm.setup_motors()  # type: ignore[call-arg]

    def get_observation(self) -> dict[str, Any]:
        obs_dict: dict[str, Any] = {}

        # Left arm observations with prefix
        left_obs = self.left_arm.get_observation()
        obs_dict.update({f"left_{key}": value for key, value in left_obs.items()})

        # Right arm observations with prefix
        right_obs = self.right_arm.get_observation()
        obs_dict.update({f"right_{key}": value for key, value in right_obs.items()})

        # Shared cameras
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            # Logging kept similar to BiSO100Follower, but without importing logger here.
            # If detailed timing is needed, it can be added later.
            _ = dt_ms

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        # Strip prefixes for each arm
        left_action = {key.removeprefix("left_"): value for key, value in action.items() if key.startswith("left_")}
        right_action = {
            key.removeprefix("right_"): value for key, value in action.items() if key.startswith("right_")
        }

        sent_left = self.left_arm.send_action(left_action)
        sent_right = self.right_arm.send_action(right_action)

        # Add prefixes back for logging / dataset storage
        prefixed_left = {f"left_{key}": value for key, value in sent_left.items()}
        prefixed_right = {f"right_{key}": value for key, value in sent_right.items()}

        return {**prefixed_left, **prefixed_right}

    def disconnect(self) -> None:
        self.left_arm.disconnect()
        self.right_arm.disconnect()

        for cam in self.cameras.values():
            cam.disconnect()

