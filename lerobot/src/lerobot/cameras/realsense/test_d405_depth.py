# test_d405_depth_matplotlib.py
from lerobot.cameras.realsense.camera_realsense import RealSenseCamera
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig
import matplotlib.pyplot as plt
import cv2
import numpy as np

# 1️⃣ 配置 D405 相机
config = RealSenseCameraConfig(
    serial_number_or_name="Intel RealSense D405",
    fps=30,
    width=640,
    height=480,
    use_depth=True
)

# 2️⃣ 初始化并连接相机
camera = RealSenseCamera(config)
camera.connect()

try:
    # 3️⃣ 获取彩色帧
    color_frame = camera.read()  # shape: (H, W, 3)

    # 4️⃣ 获取深度帧
    depth_frame = camera.read_depth()  # shape: (H, W), uint16

    # 5️⃣ 可视化深度帧 (matplotlib + colormap)
    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.title("Color Frame")
    # 转换 BGR->RGB
    plt.imshow(cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB))
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.title("Depth Frame")
    # 显示深度值，使用 plasma colormap
    plt.imshow(depth_frame, cmap='plasma')
    plt.colorbar(label='Depth (mm)')
    plt.axis('off')

    plt.tight_layout()
    plt.show()

    # 6️⃣ 可选：保存彩色和深度图像到文件
    cv2.imwrite("color_frame.png", color_frame)
    cv2.imwrite("depth_frame.png", cv2.convertScaleAbs(depth_frame, alpha=0.03))

    print("Color and depth images saved as 'color_frame.png' and 'depth_frame.png'")

finally:
    # 7️⃣ 断开相机连接
    camera.disconnect()

