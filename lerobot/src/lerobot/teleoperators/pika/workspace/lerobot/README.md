# LeRobot Integration

LeRobot 集成代码目录。

## 目录结构

- `pika_ros_bridge/` - rosbridge 桥接层核心代码
  - `rosbridge_client.py` - WebSocket 客户端封装
  - `pika_ros_teleoperator.py` - Teleoperator 实现类
  - `config_pika_ros.py` - 配置类
- `config/` - 配置文件
  - `joint_mapping.yaml` - 关节名称映射
  - `topic_config.yaml` - 话题配置

## 集成说明

此模块将在完成测试验证后实现，通过 rosbridge 连接 Pika ROS 和 lerobot。
