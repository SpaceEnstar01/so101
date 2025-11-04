import time
import cv2
import numpy as np
from lerobot.cameras.realsense.camera_realsense import RealSenseCamera, RealSenseCameraConfig
from lerobot.cameras import ColorMode, Cv2Rotation

# -----------------------------
# 配置相机
# -----------------------------
config = RealSenseCameraConfig(
    serial_number_or_name="323622272756",  # 替换成你的 D405 SN
    width=848,
    height=480,
    fps=30,
    color_mode=ColorMode.BGR,
    rotation=Cv2Rotation.NO_ROTATION,
    use_depth=True
)

camera = RealSenseCamera(config)
camera.connect()

# -----------------------------
# 视频写入设置
# -----------------------------
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out_color = cv2.VideoWriter('d405_color.mp4', fourcc, config.fps, (config.width, config.height))
out_depth = cv2.VideoWriter('d405_depth.mp4', fourcc, config.fps, (config.width, config.height), isColor=False)

# -----------------------------
# 录制 10 秒
# -----------------------------
duration_s = 10
start_time = time.time()
frame_idx = 0
print("Recording for 10 seconds...")

while time.time() - start_time < duration_s:
    try:
        # 获取彩色 + 深度
        frame_color, frame_depth = camera.async_read()  # 返回 tuple

        # 处理深度帧: 转为单通道 uint8
        depth_vis = cv2.convertScaleAbs(frame_depth, alpha=0.03)
        if len(depth_vis.shape) == 3 and depth_vis.shape[2] == 3:
            depth_vis = cv2.cvtColor(depth_vis, cv2.COLOR_BGR2GRAY)

        # 写入视频
        out_color.write(frame_color)
        out_depth.write(depth_vis)

        frame_idx += 1

    except Exception as e:
        print(f"Frame {frame_idx} read error: {e}")

# -----------------------------
# 释放资源
# -----------------------------
out_color.release()
out_depth.release()
camera.disconnect()
print("Recording finished. Files saved: d405_color.mp4, d405_depth.mp4")

