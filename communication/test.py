import serial
import time
import random

PORT = '/dev/pts/16'  # 根据socat输出修改
BAUDRATE = 115200

def create_response_packet():
    """创建模拟数据包"""
    packet = bytearray(17)
    packet[0] = 0x40  # 包头
    
    # 命令类型 - 轮询
    packet[1] = 0x01
    
    # 坐标数据 (随机生成)
    packet[9] = random.randint(0, 255)  # 滑轨X
    packet[10] = random.randint(0, 255)  # 滑轨Y
    packet[11] = random.randint(0, 255)  # 滑轨Z
    packet[12] = random.randint(0, 255)  # 平台X
    packet[13] = random.randint(0, 255)  # 平台Y
    packet[14] = random.randint(0, 255)  # 平台Z
    
    packet[15] = 0x23  # 包尾
    packet[16] = 0x21  # 包尾
    return packet

def main():
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    print(f"模拟下位机已启动，监听 {PORT}")
    
    try:
        while True:
            # 接收数据
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                print(f"收到数据: {data.hex()}")
                
                # 解析命令
                if len(data) >= 17 and data[0] == 0x40:
                    command = data[1]
                    if command == 8:  # 电机调试
                        motor_action = data[6]
                        print(f"执行电机调试: 动作={motor_action}")
                    elif command == 9:  # 寸动
                        axis = data[6]
                        direction = data[7]
                        print(f"执行寸动: 轴={axis}, 方向={direction}")
            
            # 发送状态更新
            response = create_response_packet()
            ser.write(response)
            print(f"发送状态更新: {response.hex()}")
            time.sleep(0.1)  # 500ms更新一次
            
    except KeyboardInterrupt:
        ser.close()
        print("模拟下位机关闭")

if __name__ == "__main__":
    main()