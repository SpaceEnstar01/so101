## Pika Sense 深度相机禁用记录（~/pika_ros）

### 1. 修改时间与目的

- **时间**：2026-02-26
- **环境**：`~/pika_ros` 工作空间
- **目的**：
  - 当前实验主要依赖 Pika Sense 编码器 + Pika Gripper 执行动作，不需要 RealSense 深度/彩色图像。
  - 运行 `start_single_sensor.bash` 时，RealSense 节点加载失败，报错：
    - `librealsense2.so.2.50: cannot open shared object file`
  - 为避免无关报错，**临时禁用 RealSense 相机节点**，以后需要时可以恢复。

---

### 2. 修改的文件

#### 文件路径 1（源码工程）

```text
/home/paris/pika_ros/src/sensor_tools/launch/open_single_sensor.launch
```

#### 文件路径 2（install 后实际运行的工程）

```text
/home/paris/pika_ros/install/share/sensor_tools/launch/open_single_sensor.launch
```

#### 修改前关键片段（两处文件内容相同）

```xml
    <include file="$(find pika_locator)/launch/pika_single_locator.launch"/>

    <include file="$(find realsense2_camera)/launch/rs_camera.launch">
        <arg name="color_fps" value="$(arg camera_fps)"/>
        <arg name="color_width" value="$(arg camera_width)"/>
        <arg name="color_height" value="$(arg camera_height)"/>

        <arg name="depth_fps" value="$(arg camera_fps)"/>
        <arg name="depth_width" value="$(arg camera_width)"/>
        <arg name="depth_height" value="$(arg camera_height)"/>
    </include>
    
</launch>
```

#### 修改后关键片段（两处文件均已加注释 + 标记）

```xml
    <include file="$(find pika_locator)/launch/pika_single_locator.launch"/>

    <!-- PIKA_DEPTH_DISABLED_START: disable RealSense for Pika Sense
         Reason: depth/color from RealSense not needed now; RealSense library missing.
         To re-enable: remove this comment block and restore the <include> below. -->
    <!--
    <include file="$(find realsense2_camera)/launch/rs_camera.launch">
        <arg name="color_fps" value="$(arg camera_fps)"/>
        <arg name="color_width" value="$(arg camera_width)"/>
        <arg name="color_height" value="$(arg camera_height)"/>

        <arg name="depth_fps" value="$(arg camera_fps)"/>
        <arg name="depth_width" value="$(arg camera_width)"/>
        <arg name="depth_height" value="$(arg camera_height)"/>
    </include>
    -->
    <!-- PIKA_DEPTH_DISABLED_END -->
    
</launch>
```

**说明：**
- 只注释掉了 **RealSense 相机的 `<include>` 块**。
- `serial_gripper_imu`（串口 + IMU + 编码器）和 `camera_fisheye`（鱼眼相机）节点保持不变。
- 现在运行：

```bash
conda deactivate
source ~/pika_ros/install/setup.bash
cd ~/pika_ros/scripts && bash start_single_sensor.bash
```

时，**不会再尝试启动 RealSense 节点**，也就不会再报 `librealsense2.so.2.50` 相关错误。

---

### 3. 如何恢复 RealSense 深度相机

未来如果需要重新启用 RealSense（深度或彩色），步骤：

1. 确保系统已经正确安装匹配版本的 RealSense SDK：

```bash
ldconfig -p | grep librealsense2
```

2. 编辑文件：

```text
/home/paris/pika_ros/src/sensor_tools/launch/open_single_sensor.launch
```

3. 找到带有标记的部分：

```xml
<!-- PIKA_DEPTH_DISABLED_START: ... -->
...
<!-- PIKA_DEPTH_DISABLED_END -->
```

4. 删除整个注释块（`PIKA_DEPTH_DISABLED_START` 到 `PIKA_DEPTH_DISABLED_END` 之间的所有内容），恢复为原始的 `<include realsense2_camera/rs_camera.launch>` 配置。

5. 重新运行：

```bash
conda deactivate
source ~/pika_ros/install/setup.bash
cd ~/pika_ros/scripts && bash start_single_sensor.bash
```

确认 RealSense 节点可以正常启动且不再报库缺失错误。


---

## Pika Sense + Pika Gripper 深度相机禁用记录（~/pika_ros）

### 1. 修改时间与目的

- **时间**：2026-02-26
- **环境**：`~/pika_ros` 工作空间
- **目的**：
  - 在使用 `start_sensor_gripper.bash` 联合启动 Sense + Gripper 时，不需要 RealSense 深度/彩色图像。
  - 同样为避免 RealSense 驱动报错，临时禁用两路 RealSense（Sense 一路 + Gripper 一路），保留所有串口和鱼眼相机功能。

---

### 2. 修改的文件

#### 文件路径 1（源码工程）

```text
/home/paris/pika_ros/src/sensor_tools/launch/open_sensor_gripper.launch
```

#### 文件路径 2（install 后实际运行的工程）

```text
/home/paris/pika_ros/install/share/sensor_tools/launch/open_sensor_gripper.launch
```

#### 修改前关键片段（两处文件内容相同）

```xml
    <node pkg="sensor_tools" name="gripper_camera_fisheye" type="usb_camera.py" output="screen" respawn="true">
        ...
    </node>
    <include file="$(find pika_locator)/launch/pika_single_locator.launch"/>
    <include file="$(find realsense2_camera)/launch/multi_camera.launch">
        <arg name="serial_no_camera1" value="$(arg sensor_depth_camera_no)"/>
        <arg name="serial_no_camera2" value="$(arg gripper_depth_camera_no)"/>
        <arg name="camera1" value="sensor/camera"/>
        <arg name="camera2" value="gripper/camera"/>

        <arg name="camera_fps" value="$(arg camera_fps)"/>
        <arg name="camera_width" value="$(arg camera_width)"/>
        <arg name="camera_height" value="$(arg camera_height)"/>
    </include>
</launch>
```

#### 修改后关键片段（两处文件均已加注释 + 标记）

```xml
    <node pkg="sensor_tools" name="gripper_camera_fisheye" type="usb_camera.py" output="screen" respawn="true">
        <param name="camera_port" value="$(arg gripper_fisheye_port)"/>
        <param name="camera_fps" value="$(arg camera_fps)"/>
        <param name="camera_width" value="$(arg camera_width)"/>
        <param name="camera_height" value="$(arg camera_height)"/>
        <param name="camera_frame_id" value="gripper/camera_fisheye_link"/>
        <remap from="/camera_rgb/color/image_raw" to="/gripper/camera_fisheye/color/image_raw"/>
        <remap from="/camera_rgb/color/camera_info" to="/gripper/camera_fisheye/color/camera_info"/>
    </node>
    <include file="$(find pika_locator)/launch/pika_single_locator.launch"/>

    <!-- PIKA_DEPTH_DISABLED_GRIPPER_START: disable RealSense depth cameras for Sense+Gripper (...) -->
    <!--
    <include file="$(find realsense2_camera)/launch/multi_camera.launch">
        <arg name="serial_no_camera1" value="$(arg sensor_depth_camera_no)"/>
        <arg name="serial_no_camera2" value="$(arg gripper_depth_camera_no)"/>
        <arg name="camera1" value="sensor/camera"/>
        <arg name="camera2" value="gripper/camera"/>

        <arg name="camera_fps" value="$(arg camera_fps)"/>
        <arg name="camera_width" value="$(arg camera_width)"/>
        <arg name="camera_height" value="$(arg camera_height)"/>
    </include>
    -->
    <!-- PIKA_DEPTH_DISABLED_GRIPPER_END -->
</launch>
```

**说明：**
- 只注释掉了 **双 RealSense 相机的 `<include multi_camera.launch>` 块**。
- 两个 `serial_gripper_imu`（Sense 串口 + Gripper 串口）以及两路鱼眼相机节点都保持不变。
- 现在运行：

```bash
conda deactivate
source ~/pika_ros/install/setup.bash
cd ~/pika_ros/scripts && bash start_sensor_gripper.bash
```

时，**不会再尝试启动 RealSense multi_camera 节点**。

---

### 3. 如何恢复 Sense+Gripper 的 RealSense 深度相机

1. 确保 RealSense SDK 安装正确（同上：`ldconfig -p | grep librealsense2`）。
2. 编辑两个文件：

```text
/home/paris/pika_ros/src/sensor_tools/launch/open_sensor_gripper.launch
/home/paris/pika_ros/install/share/sensor_tools/launch/open_sensor_gripper.launch
```

3. 查找带有 `PIKA_DEPTH_DISABLED_GRIPPER_START` / `PIKA_DEPTH_DISABLED_GRIPPER_END` 的注释块，删除整个注释块，恢复原始的 `<include realsense2_camera/launch/multi_camera.launch>`。
4. 重新运行：

```bash
conda deactivate
source ~/pika_ros/install/setup.bash
cd ~/pika_ros/scripts && bash start_sensor_gripper.bash
```

5. 确认双 RealSense 相机节点可以正常启动且不再报错。

