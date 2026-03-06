from dataclasses import dataclass, field
from ..config import RobotConfig
from lerobot.cameras import CameraConfig
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig  # 新增导入

@RobotConfig.register_subclass("piper")
@dataclass
class PiperConfig(RobotConfig):
    port: str = "can0"
    disable_torque_on_disconnect: bool = True
    max_relative_target: int | None = None

    # ====== 原始 cameras 字段保留 ======
    cameras: dict[str, CameraConfig] = field(default_factory=dict)
    use_degrees: bool = False

    # ====== XX代码：新增 Intel D405 摄像头配置 ======
    def __post_init__(self):
        # 如果用户没有显式传入 cameras，则添加默认 D405
        if not self.cameras:
            self.cameras = {
                "d405": RealSenseCameraConfig(
                    serial_number_or_name="323622272756",
                    width=848,
                    height=480,
                    fps=30,
                    use_depth=True,
                )
            }

