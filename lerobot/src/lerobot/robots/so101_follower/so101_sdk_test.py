import sys
import time
sys.path.insert(0, '/home/paris/X/so101/lerobot/src')

from lerobot.robots.so101_follower.so101_follower import SO101Follower
from lerobot.robots.so101_follower.config_so101_follower import SO101FollowerConfig

cfg = SO101FollowerConfig(port="/dev/ttyACM0", id="00")

follower = SO101Follower(cfg)
follower.connect(calibrate=False)  # ← 跳过校准

try:
    while True:
        obs = follower.get_observation()
        print(obs["shoulder_lift.pos"])  # 例如打印一个关节
        time.sleep(1)
except KeyboardInterrupt:
    follower.disconnect()


#so101/lerobot/src/lerobot/robots/so101_follower/so101_sdk_test.py