from lerobot.teleoperators.so101_leader import SO101Leader, SO101LeaderConfig
from lerobot.robots.piper.piper import Piper
from lerobot.utils.robot_utils import busy_wait

# 创建 Leader 配置
#teleop_cfg = SO101LeaderConfig(port="/dev/ACM0")
teleop_cfg = SO101LeaderConfig(port="/dev/ttyACM0")

teleop = SO101Leader(teleop_cfg)

# 创建 Piper
robot_cfg = {"port": "can0"}  # 你 Piper 类的 __init__ 可以接受 dict
robot = Piper(robot_cfg)

# 连接
teleop.connect()
robot.connect()

try:
    while True:
        action = teleop.get_action()
        robot.send_action(action)
        busy_wait(0.05)
except KeyboardInterrupt:
    print("退出")
finally:
    teleop.disconnect()
    robot.disconnect()
