# Pika 遥操作系统架构 - 端到端流程详解

## 📋 系统概览

这是一个**从Pika Sense到Piper机械臂+夹爪**的完整遥操作系统，通过ROS话题实现数据流和控制流。

---

## 🔄 完整数据流和控制流

### **阶段1：硬件数据采集（终端2）**

**启动脚本：** `start_single_sensor.bash`

**关键节点：** `serial_gripper_imu` (C++节点)

**代码位置：**
- 启动脚本：`~/pika_ros/scripts/start_single_sensor.bash`
- Launch文件：`~/pika_ros/src/sensor_tools/launch/open_single_sensor.launch`
- 核心代码：`~/pika_ros/src/sensor_tools/src/serial_gripper_imu.cpp`

**工作流程：**
1. 通过串口 `/dev/ttyUSB50` 连接 **Pika Sense** 设备
2. 持续读取编码器数据（AS5047编码器，获取夹爪角度）
3. 读取IMU数据（姿态信息）
4. 发布到ROS话题：
   - `/gripper/data` - 夹爪状态（角度、距离、电压等）
   - `/gripper/joint_state` - 夹爪关节状态
   - `/imu/data` - IMU数据
   - `/joint_states_gripper` - 合并的关节状态（包含夹爪）

**关键代码逻辑：**
```cpp
// serial_gripper_imu.cpp 第410-467行
void jointStateCtrlHandler(const sensor_msgs::JointState::ConstPtr& msg){
    // 1. 检查时间戳（必须有效，不能为0）
    if(msg->header.stamp.toSec() - jointStateCtrlTime < ctrlFreq)
        return;
    
    // 2. 如果夹爪未使能，自动使能
    if(!enable){
        sendCommand(ENABLE);
    }
    
    // 3. 从消息的最后一个位置值获取距离（joint_6）
    float distance = msg->position.back();  // 单位：米 (0-0.098m)
    
    // 4. 转换为角度
    float angle = getAngle((distance/2+getDistance(0)));
    
    // 5. 发送位置控制命令到串口
    sendCommand(POSITION_CTRL_MIT, angle);
}
```

---

### **阶段2：遥操作转换（终端3）**

**启动命令：** `roslaunch pika_remote_piper teleop_rand_single_piper.launch`

**关键节点：** `teleop_piper` (Python节点)

**代码位置：**
- Launch文件：`~/pika_ros/src/PikaAnyArm/piper/pika_remote_piper/launch/teleop_rand_single_piper.launch`
- 核心代码：`~/pika_ros/src/PikaAnyArm/piper/pika_remote_piper/scripts/teleop_piper_publish.py`

**工作流程：**
1. 订阅话题：
   - `/pika_pose` - Pika Sense的位姿信息（从定位系统）
   - `/piper_FK/urdf_end_pose_orient` - Piper机械臂当前末端位姿
   - `/joint_states_gripper` - 包含夹爪的完整关节状态

2. **关键转换逻辑：**
```python
# teleop_piper_publish.py 第94-114行
def localization_pose_callback(self, msg):
    # 1. 获取Sense的位姿（6DOF）
    # 2. 计算相对变换
    pose_xyzrpy = matrix_to_xyzrpy(
        np.dot(self.arm_end_pose_matrix, 
               np.dot(np.linalg.inv(self.localization_pose_matrix), matrix))
    )
    # 3. 发布到 /piper_IK/ctrl_end_pose（末端位姿控制）
    self.arm_end_pose_ctrl_publisher.publish(pose_msg)
```

3. **夹爪控制：**
   - 从 `/joint_states_gripper` 读取夹爪位置（joint_6）
   - 发布到 `/joint_states` 话题
   - **关键：** 消息的 `header.stamp` 必须使用 `rospy.Time.now()`，不能为0！

```python
# teleop_piper_publish.py 第238-245行
joint_states_msgs = JointState()
joint_states_msgs.header = Header()
joint_states_msgs.header.stamp = rospy.Time.now()  # ⚠️ 必须使用当前时间！
joint_states_msgs.name = [f'joint{i+1}' for i in range(7)]
joint_states_msgs.position = interpolated_positions  # joint_6是夹爪位置
self.arm_joint_state_publisher.publish(joint_states_msgs)
```

---

### **阶段3：机械臂控制（终端3，Piper节点）**

**关键节点：** `piper_ctrl_single_node` (Python节点)

**代码位置：**
- 核心代码：`~/pika_ros/src/PikaAnyArm/piper/piper_ros/piper/scripts/piper_ctrl_single_node.py`

**工作流程：**
1. 订阅 `/joint_states` 话题（来自遥操作节点）
2. **关节控制：**
```python
# piper_ctrl_single_node.py 第321-350行
def joint_callback(self, joint_data):
    # 1. 转换前6个关节（机械臂关节）
    factor = 1000 * 180 / np.pi
    joint_0 = round(joint_data.position[0]*factor)
    # ... joint_1 到 joint_5
    
    # 2. 处理第7个关节（夹爪）
    if(len(joint_data.position) >= 7):
        joint_6 = round(joint_data.position[6]*1000*1000)  # 转换为微米
        joint_6 = joint_6 * self.gripper_val_mutiple
        joint_6 = clamp(joint_6, 0, 80000)  # 限制范围
    
    # 3. 通过CAN总线发送到Piper机械臂
    if(self.GetEnableFlag()):
        self.piper.JointCtrl(joint_0, joint_1, ..., joint_5)  # 机械臂关节
        self.piper.GripperCtrl(joint_6, 1000, 0x01, 0)  # 夹爪控制
```

**注意：** 这里的 `GripperCtrl` 是控制 **Piper机械臂的夹爪**，不是独立的Pika Gripper！

---

### **阶段4：Pika Gripper控制（如果使用独立夹爪）**

**关键节点：** `serial_gripper_imu` (已在阶段1启动)

**控制路径：**
1. 遥操作发布 `/joint_states`，其中 `position[6]` 是夹爪距离（米，0-0.098m）
2. `serial_gripper_imu` 节点订阅 `/joint_states`（通过remap：`/gripper/joint_state_ctrl` → `/joint_states`）
3. 节点处理：
   - 检查时间戳（必须有效）
   - 自动使能（如果未使能）
   - 转换距离→角度
   - 通过串口发送二进制命令到Pika Gripper硬件

**关键代码：**
```cpp
// serial_gripper_imu.cpp 第445-461行
float distance = msg->position.back();  // 从joint_states获取
distance = clamp(distance, 0.0, 0.098);  // 限制范围
float angle = getAngle((distance/2+getDistance(0)));  // 转换为角度
angle = clamp(angle, 0.0, 1.67);  // 角度范围0-1.67 rad

// 发送位置控制命令
std::vector<uint8_t> command = createBinaryCommand<float>(
    POSITION_CTRL_MIT, 
    std::vector<float>{angle}
);
boost::asio::write(*serial, boost::asio::buffer(command));
```

---

## 🔑 关键发现和问题

### **问题1：时间戳必须有效**
- **位置：** `serial_gripper_imu.cpp` 第412-414行
- **问题：** 如果消息时间戳为0或无效，命令会被忽略
- **解决：** 确保所有发布的消息使用 `rospy.Time.now()` 或 `$(date +%s)`

### **问题2：夹爪需要先使能**
- **位置：** `serial_gripper_imu.cpp` 第420-425行
- **问题：** 如果夹爪未使能，位置控制命令不会执行
- **解决：** 节点会自动使能，但也可以通过 `/gripper/ctrl` 手动使能

### **问题3：话题映射**
- **Sense节点：** 发布 `/gripper/data` 和 `/joint_states_gripper`
- **遥操作节点：** 订阅 `/joint_states_gripper`，发布 `/joint_states`
- **Gripper控制节点：** 订阅 `/joint_states`（通过remap）

---

## 📁 关键文件路径总结

### **启动脚本**
- `~/pika_ros/scripts/start_single_sensor.bash` - 启动Sense采集
- `~/pika_ros/src/PikaAnyArm/piper/pika_remote_piper/launch/teleop_rand_single_piper.launch` - 启动遥操作

### **核心代码**
- **Sense采集：** `~/pika_ros/src/sensor_tools/src/serial_gripper_imu.cpp`
- **遥操作：** `~/pika_ros/src/PikaAnyArm/piper/pika_remote_piper/scripts/teleop_piper_publish.py`
- **Piper控制：** `~/pika_ros/src/PikaAnyArm/piper/piper_ros/piper/scripts/piper_ctrl_single_node.py`

### **Launch文件**
- `~/pika_ros/src/sensor_tools/launch/open_single_sensor.launch`
- `~/pika_ros/src/PikaAnyArm/piper/pika_remote_piper/launch/teleop_rand_single_piper.launch`

---

## 🎯 数据流图

```
Pika Sense硬件 (串口)
    ↓
serial_gripper_imu节点
    ↓ 发布
/gripper/data, /joint_states_gripper
    ↓
teleop_piper节点 (订阅/joint_states_gripper)
    ↓ 转换位姿 + 夹爪位置
    ↓ 发布
/joint_states (包含joint_6=夹爪距离)
    ↓
├─→ piper_ctrl_single_node (控制Piper机械臂+夹爪，通过CAN)
└─→ serial_gripper_imu (控制独立Pika Gripper，通过串口)
```

---

## 🔄 遥操作状态切换机制详解

### **状态切换逻辑**

遥操作节点有3个状态：**wait** → **start** → **close**

**代码位置：** `teleop_piper_publish.py` 第127-173行

**状态切换条件：**

1. **wait 状态：**
   - 初始状态或等待初始化
   - 需要等待两个话题都有消息：
     - `/pika_pose` - Pika Sense的定位位姿（来自定位系统）
     - `/piper_FK/urdf_end_pose_orient` - Piper机械臂当前末端位姿
   - 代码逻辑：
   ```python
   # 第97-98行：接收到/pika_pose消息后
   if self.refresh_localization_pose:
       self.refresh_localization_pose = False
   
   # 第123-124行：接收到/piper_FK/urdf_end_pose_orient消息后
   if self.refresh_arm_end_pose:
       self.refresh_arm_end_pose = False
   ```

2. **start 状态：**
   - 当两个刷新标志都变为 `False` 时自动切换
   - 代码逻辑：
   ```python
   # 第137-139行
   if not self.refresh_localization_pose and not self.refresh_arm_end_pose:
       print("start")
       self.status = True  # 开始遥操作
   ```

3. **close 状态：**
   - 通过调用 `/teleop_trigger` 服务触发
   - 代码逻辑：
   ```python
   # 第149-157行
   def teleop_trigger_callback(self, req):
       if self.status:
           self.status = False
           print("close")
   ```

### **为什么晃动Pika Sense会启动？**

晃动Pika Sense会触发：
1. **定位系统**检测到位姿变化，发布 `/pika_pose` 消息
2. **机械臂节点**可能也发布了 `/piper_FK/urdf_end_pose_orient` 消息
3. 两个条件满足后，自动从 **wait** 切换到 **start**

### **如何手动控制状态？**

**启动遥操作：**
```bash
rosservice call /teleop_trigger
```

**关闭遥操作：**
```bash
rosservice call /teleop_trigger  # 再次调用即可关闭
```

**检查当前状态：**
```bash
# 查看遥操作状态话题
rostopic echo /teleop_status -n 1

# 检查必要的话题是否有消息
rostopic hz /pika_pose
rostopic hz /piper_FK/urdf_end_pose_orient
```

### **改进建议（可选）**

如果需要更清晰的状态提示，可以修改代码添加更详细的日志：

```python
# 在 status_changing() 函数中添加
if not self.refresh_localization_pose and not self.refresh_arm_end_pose:
    print("✅ 遥操作已启动！状态：ACTIVE")
    self.status = True
else:
    missing = []
    if self.refresh_localization_pose:
        missing.append("/pika_pose")
    if self.refresh_arm_end_pose:
        missing.append("/piper_FK/urdf_end_pose_orient")
    print(f"⏳ 等待初始化... 缺少话题: {', '.join(missing)}")
```

---

## ⚠️ 常见问题

1. **夹爪不移动：**
   - 检查时间戳是否有效（不能为0）
   - 检查夹爪是否已使能
   - 检查话题是否正确连接

2. **遥操作不工作：**
   - 检查是否需要触发 `/teleop_trigger` 服务
   - 检查 `/joint_states` 是否有消息发布
   - 检查话题映射是否正确
   - **检查是否处于 "start" 状态**（不是 "wait" 状态）

3. **状态一直显示 "wait"：**
   - 检查 `/pika_pose` 话题是否有消息：`rostopic hz /pika_pose`
   - 检查 `/piper_FK/urdf_end_pose_orient` 话题是否有消息：`rostopic hz /piper_FK/urdf_end_pose_orient`
   - 确保定位系统和机械臂节点都在运行

4. **CAN通信失败：**
   - 检查CAN设备：`ip link show can0`
   - 检查权限：`ls -la /dev/can*`
   - 运行激活脚本：`bash can_activate.sh can0 1000000`
