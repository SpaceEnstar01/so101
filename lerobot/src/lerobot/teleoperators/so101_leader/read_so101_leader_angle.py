# test_so101_leader.py
import sys
import time  # ← 补上
sys.path.insert(0, '/home/paris/X/so101/lerobot/src')

from src.lerobot.teleoperators.so101_leader.so101_leader import SO101Leader
from src.lerobot.teleoperators.so101_leader.config_so101_leader import SO101LeaderConfig

cfg = SO101LeaderConfig(port="/dev/ttyACM0", id="R00")

leader = SO101Leader(cfg)
leader.connect(calibrate=False)  # ← 跳过校准

try:
    while True:
        #print(leader.get_action())  # get 6 joints degree
        print(leader.get_action()["shoulder_lift.pos"]) # 'shoulder_pan.pos':  , 'shoulder_lift.pos':  , 'elbow_flex.pos':  , 'wrist_flex.pos':  , 'wrist_roll.pos':  , 'gripper.pos':  
        time.sleep(1)
except KeyboardInterrupt:
    leader.disconnect()