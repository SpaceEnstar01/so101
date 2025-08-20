"""
Minimal deployment: load a trained policy and run closed-loop control.
No dataset recording, no reset phase, ESC to quit.
"""

import logging
import time
from dataclasses import dataclass

from lerobot.configs import parser
from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.policies.factory import make_policy
from lerobot.robots import make_robot_from_config
from lerobot.utils.control_utils import init_keyboard_listener, predict_action
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.utils import get_safe_torch_device, init_logging, log_say
from lerobot.utils.visualization_utils import _init_rerun, log_rerun_data


@dataclass
class DeployConfig:
    robot: ...
    policy: PreTrainedConfig
    display_data: bool = False
    play_sounds: bool = True
    fps: int = 30
    task: str = "deploy"


@parser.wrap()
def main(cfg: DeployConfig) -> None:
    init_logging()

    # ---------- 1. 机器人 ----------
    robot = make_robot_from_config(cfg.robot)
    robot.connect()

    # ---------- 2. Dummy dataset_meta ----------
    features = hw_to_dataset_features(robot.observation_features, "observation", video=False)
    features.update(hw_to_dataset_features(robot.action_features, "action", video=False))
    dummy_ds = LeRobotDataset.create(
        repo_id="dummy/deploy",
        fps=cfg.fps,
        robot_type=robot.name,
        features=features,
        use_videos=False,
    )

    # ---------- 3. 策略 ----------
    policy = make_policy(cfg.policy, ds_meta=dummy_ds.meta)
    policy.reset()

    # ---------- 4. 主循环 ----------
    listener, events = init_keyboard_listener()
    if cfg.display_data:
        _init_rerun("deploy")

    log_say("Deployment started. Press ESC to quit.", cfg.play_sounds)
    device = get_safe_torch_device(cfg.policy.device)

    try:
        while not events["stop_recording"]:
            start = time.perf_counter()

            obs = robot.get_observation()
            frame = build_dataset_frame(features, obs, prefix="observation")

            action_tensor = predict_action(
                frame,
                policy,
                device,
                use_amp=policy.config.use_amp,
                task=cfg.task,
                robot_type=robot.robot_type,
            )
            action = {k: action_tensor[i].item() for i, k in enumerate(robot.action_features)}
            robot.send_action(action)

            if cfg.display_data:
                log_rerun_data(obs, action)

            busy_wait(1 / cfg.fps - (time.perf_counter() - start))

    except KeyboardInterrupt:
        pass
    finally:
        log_say("Stopping deployment", cfg.play_sounds, blocking=True)
        robot.disconnect()
        if listener is not None:
            listener.stop()


if __name__ == "__main__":
    main()
