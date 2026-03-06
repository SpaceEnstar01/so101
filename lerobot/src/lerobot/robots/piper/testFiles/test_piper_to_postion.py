import time
import sys
from piper_sdk import C_PiperInterface_V2

def main():
    print("[piperTest0] 开始验证 …")
    piper = C_PiperInterface_V2("can0")
    piper.ConnectPort()
    while not piper.EnablePiper():
        time.sleep(0.01)
    piper.GripperCtrl(0, 1000, 0x01, 0)

    factor = 57295.7795  # 1000*180/3.1415926
    position = [0, 0, 0, 0, 0, 0, 0]
    count = 0
    try:
        while True:
            count += 1
            if count % 300 == 0:
                position = [0.2, 0.2, -0.2, 0.3, -0.2, 0.5, 0.08]
            elif count % 600 == 0:
                position = [0, 0, 0, 0, 0, 0, 0]
                count = 0

            joints = [round(p * factor) for p in position[:6]]
            grip = round(position[6] * 1000 * 1000)

            piper.MotionCtrl_2(0x01, 0x01, 100, 0x00)
            piper.JointCtrl(*joints)
            piper.GripperCtrl(abs(grip), 1000, 0x01, 0)

            print(piper.GetArmStatus())
            time.sleep(0.005)
    except KeyboardInterrupt:
        print("\n[piperTest0] 手动停止")
    finally:
        piper.DisableArm(7)
        print("[piperTest0] 已断开")

if __name__ == "__main__":
    main()
 
