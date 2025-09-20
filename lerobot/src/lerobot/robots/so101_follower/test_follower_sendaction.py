#!/usr/bin/env python
# follower_sendaction.py
# 最小化测试 SO101 Follower 单关节动作

import time
import os 
import sys 


# 将 lerobot 根目录加入模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用绝对导入
from lerobot.robots.so101_follower.so101_follower import SO101Follower, SO101FollowerConfig


def main():
    # 1️⃣ 创建硬编码配置
    cfg = SO101FollowerConfig(
        port="/dev/ttyACM0",  # 根据实际端口修改
        use_degrees=True,
        cameras={},            # 暂时不使用摄像头
        max_relative_target=None,
        id="R00",  # 硬编码机器人ID
    )

    # 2️⃣ 初始化机器人
    robot = SO101Follower(cfg)

    # 3️⃣ 连接机器人
    print("Connecting to SO101 Follower...")
    robot.connect()
    print("Connected!")

    try:
        # 4️⃣ 构造动作字典（只动 shoulder_pan）
        #action = {"shoulder_pan.pos": 20.0}  # 目标角度，单位度
        action = {
                    "shoulder_pan.pos": -10.0,
                    "shoulder_lift.pos": -10.0,
                    "elbow_flex.pos": -70.0,
                    "wrist_flex.pos": 0.0,
                    "wrist_roll.pos": 0.0,
                    "gripper.pos": 0.0,  # 假设 0~100

                    }


        # 5️⃣ 发送动作
        print(f"Sending action: {action}")
        sent_action = robot.send_action(action)
        print(f"Action actually sent: {sent_action}")

        # 6️⃣ 保持一会儿观察动作
        time.sleep(2)

    finally:
        # 7️⃣ 断开连接
        robot.disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    main()
