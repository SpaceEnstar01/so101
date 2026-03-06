from dataclasses import dataclass, field
from ..config import RobotConfig
from lerobot.cameras import CameraConfig

@RobotConfig.register_subclass("piper")
@dataclass
class PiperConfig(RobotConfig):
    port: str = "can0"
    disable_torque_on_disconnect: bool = True
    max_relative_target: int | None = None
    cameras: dict[str, CameraConfig] = field(default_factory=dict)
    use_degrees: bool = False
