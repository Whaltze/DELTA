#!/usr/bin/env python3
import sys
import os

def test_imc_connection():
    try:
        # 确保导入正确的模块
        # 假设control.py与测试脚本在同一目录
        lib_path = './lib/libIMCnet.so.1.0.0'        
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from control import IMCControl
        
        # 创建实例，根据实际构造函数调整
        imc = IMCControl(lib_path)  # 可能需要无参数
        
        # 查找网卡
        print("查找网卡...")
        success, cards = imc.find_net_card()
        
        if not success:
            print("查找网卡失败")
            # 尝试查看错误信息
            if hasattr(imc, 'get_last_error'):
                error_msg = imc.get_last_error()
                print(f"错误详情: {error_msg}")
            return False
            
        print(f"找到网卡: {cards}")
        
        if not cards:
            print("没有找到任何网卡")
            return False
            
        # 尝试连接
        print(f"尝试连接第一个网卡: {cards[0]}")
        open_success = imc.open_x(0, 0)
        
        if open_success:
            print("连接成功!")
            imc.close()
            return True
        else:
            print("连接失败")
            if hasattr(imc, 'get_last_error'):
                error_msg = imc.get_last_error()
                print(f"连接错误详情: {error_msg}")
            return False
            
    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保control.py存在且可导入")
        return False
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os
    if os.geteuid() != 0:
        print("请以root权限运行此脚本")
        sys.exit(1)
        
    # 设置库路径
    os.environ['LD_LIBRARY_PATH'] = '/usr/lib:/usr/local/lib:' + os.environ.get('LD_LIBRARY_PATH', '')
    
    test_imc_connection()