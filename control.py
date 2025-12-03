import ctypes
import enum
from typing import Tuple, List, Dict
import logging

class ControlMode(enum.IntEnum):
    GIMC_SUCCESS = 0
    GIMC_INVALID_HANDLE = 1         # 无效的句柄
    GIMC_INVALID_STRING_ADDRESS = 2 # 输入的字符串地址无效
    GIMC_INVALID_AXIS = 3           # 无效的轴号
    GIMC_LACK_PARAM = 4             # 缺少参数
    GIMC_ERROR_PARAM = 5            # 参数错误
    GIMC_ERROR_LINE = 6             # 行号错误
    GIMC_ERROR_FILE = 7             # 文件错误
    GIMC_NO_INIT = 8                # 没有初始化

class FifoSel(enum.IntEnum):
	SEL_IFIFO = 0
	SEL_QFIFO = 1
	SEL_PFIFO1 = 2
	SEL_PFIFO2 = 3
	SEL_CFIFO = 4

class ErrorCode(enum.IntEnum):
    IMC_ERR_PLIM = 1 << 0       #(0x0001)正向硬极限越界
    IMC_ERR_NLIM = 1 << 1       #(0x0002)负向硬极限越界
    IMC_ERR_PSOF = 1 << 2       #(0x0004)正向软极限越界
    IMC_ERR_NSOF = 1 << 3       #(0x0008)负向软极限越界
    IMC_ERR_STOP = 1 << 4       #(0x0010)急停输入
    IMC_ERR_ALM = 1 << 6        #(0x0040)伺服错误报警
    IMC_ERR_POSERRLIM = 1 << 7  #(0x0080)位置误差超限
    IMC_ERR_TGPOSOV = 1 << 9    #(0x0200)目标位置越界
    IMC_ERR_POSOV = 1 << 10     #(0x0400)指令位置越界
    IMC_ERR_INSERR = 1 << 12    #(0x1000)指令错误
    IMC_ERR_VELLIM = 1 << 13    #(0x2000)速度超限
    IMC_ERR_ACCLIM = 1 << 14    #(0x4000)加速度超限
    IMC_ERR_DELPOS = 1 << 15    #(0x8000)指令位置异常

class IMCControl:
    def __init__(self, lib_path: str):
        self.handle = ctypes.c_void_p()
        self.lib = ctypes.CDLL(lib_path)  # Load the shared library

    ##########
    # 设备函数

    # def find_net_card(self):
    #     """
    #     用于查找电脑的以太网卡，以便于选择与控制卡连接的网卡
        
    #     :param self: class
    #     """
    #     info: ctypes.Array[ctypes.c_char] = ctypes.create_string_buffer(16*256)
    #     num: ctypes.c_int = ctypes.c_int()

    #     result: bool = self.lib.IMC_FindNetCard(ctypes.byref(info), ctypes.byref(num)) == 0
    #     cards: List[str] = [info.raw[i * 256: (i + 1) * 256].decode('utf-8').strip() for i in range(num.value)]
    #     return result, cards

    def find_net_card(self):
        """
        用于查找电脑的以太网卡，以便于选择与控制卡连接的网卡
        返回: (成功状态, 网卡列表)
        """
        try:
            # 检查lib是否加载
            if not hasattr(self.lib, 'IMC_FindNetCard'):
                return False, []
            
            # 分配缓冲区
            info = ctypes.create_string_buffer(256 * 16)  # 16个256字节的字符串
            num = ctypes.c_int()
            
            # 调用库函数
            result = self.lib.IMC_FindNetCard(ctypes.byref(info), ctypes.byref(num))
            
            if result == 0:
                # 解析网卡信息
                cards = []
                for i in range(num.value):
                    card_info = info.raw[i*256:(i+1)*256].decode('utf-8').strip('\x00')
                    if card_info:
                        cards.append(card_info)
                return True, cards
            else:
                return False, []
        except Exception as e:
            print(f"查找网卡异常: {e}")
            return False, []
    
    def open(self, net_card_index: int, imcid: int) -> bool:
        """
        用于打开控制卡设备，与设备建立通信连接

        1. 所有的对设备进行操作的函数在使用前，必须调用一个打开设备函数获得设备句柄，使用此句柄才能与设备进行通信。
        
        :param self: class
        :param net_card_index: 网卡索引，由搜索网卡函数返回的结果决定
        :type net_card_index: int
        :param imcid: IMC 控制卡的 id，由控制卡上的拨码开关设置决定
        :type imcid: int
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value != 0:
            logging.error(f'控制卡句柄已打开：{self.handle.value}')
            return False

        handle: ctypes.c_void_p = self.lib.IMC_Open(ctypes.c_int(net_card_index), ctypes.c_int(imcid))
        self.handle = handle

        return bool(handle.value != 0)
    
    def open_x(self, net_card_index: int, imcid: int, timeout: int = 40, open_mode: int = 1) -> bool:
        """
        用于打开控制卡设备，与设备建立通信连接

        1. 所有的对设备进行操作的函数在使用前，必须调用一个打开设备函数获得设备句柄，使用此句柄才能与设备进行通信
        2. Timeout 参数最小值为 1，用于设置通信函数等待的超时时间。如果电脑的运算速度慢，建议设置超时时间长些
        3. openMode 参数，一般情况下使用混杂模式，通信时间会快一些。但混杂模式，对某些无线网卡不支持，只能使用非混杂模式
        
        :param self: class
        :param net_card_index: 网卡索引，由搜索网卡函数返回的结果决定
        :type net_card_index: int
        :param imcid: IMC 控制卡的 id，由控制卡上的拨码开关设置决定
        :type imcid: int
        :param timeout: 通信超时时间，单位毫秒
        :type timeout: int
        :param open_mode: 打开模式；1：混杂模式， 0：非混杂模式
        :type open_mode: int
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value != 0:
            logging.error(f'控制卡句柄已打开：{self.handle.value}')
            return False
        
        if timeout < 1:
            logging.error(f'timeout参数最小值为1，当前值为{timeout}')
            return False
        
        if open_mode not in (0, 1):
            logging.error(f'无效的打开模式：{open_mode}')
            return False
        
        handle: ctypes.c_int = self.lib.IMC_OpenX(ctypes.c_int(net_card_index), ctypes.c_int(imcid), ctypes.c_int(timeout), ctypes.c_int(open_mode))
        self.handle = handle

        return bool(handle.value != 0)
    
    def open_by_password(self, net_card_index: int, imcid: int, password: str) -> bool:
        """
        用于打开控制卡设备，与设备建立通信连接

        1. 此函数与 open 类似，只是增加了密码检测功能
        2. 户可以使用自己设置的密码通过此函数打开设备，即客户编写的程序只适用于自己设置过密码的控制卡，可以使程序与控制卡一一对应
        3. 密码是一个至少 4 个、少于 100 个字符的 ASCII 字符串。出厂的控制卡没有设置密码，要使用密码，请使用 IMCSoft 调试平台中工具菜单下的固件更新功能来设置密码
        
        :param self: class
        :param net_card_index: 网卡索引，由搜索网卡函数返回的结果决定
        :type net_card_index: int
        :param imcid: IMC 控制卡的 id，由控制卡上的拨码开关设置决定
        :type imcid: int
        :param password: 密码字符串
        :type password: str
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value != 0:
            logging.error(f'控制卡句柄已打开：{self.handle.value}')
            return False
        
        if 4 <= len(password) < 100:
            logging.error(f'密码长度应在4到16之间，当前长度为{len(password)}')
            return False
        
        pwd: ctypes.Array[ctypes.c_char] = ctypes.create_string_buffer(password.encode('utf-8'))
        
        handle: ctypes.c_int = self.lib.IMC_OpenX(ctypes.c_int(net_card_index), ctypes.c_int(imcid), ctypes.byref(pwd))
        self.handle = handle

        return bool(handle.value != 0)
    
    def close(self) -> bool:
        """
        此函数用于关闭打开的设备

        1. 当设备关闭后，就无法再与设备进行通信，除非再次打开
        
        :param self: class
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        result: ctypes.c_int = self.lib.IMC_Close(self.handle)
        return bool(result.value != 0)
    
    ##########
    # 配置控制卡函数

    def init_cfg(self) -> bool:
        """
        配置控制卡内的基本寄存器

        1. 此函数配置的寄存器在 IMC_cfg.ini 文件中指明。可修改此文件中的配置来适合你的设备使用
        2. 除非自己手动配置控制卡，否则必须调用此函数之后，轴才能运动
        3. 如果不使用此函数配置控制卡，可以使用本章的其他函数单独配置
        
        :param self: class
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False

        result: ctypes.c_int = self.lib.IMC_InitCfg(self.handle)
        return bool(result.value != 0)
    
    def clear_imc(self) -> bool:
        """
        清空控制卡中所有 FIFO 中的未执行的指令
        
        :param self: class
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False

        result: ctypes.c_int = self.lib.IMC_ClearIMC(self.handle)
        return bool(result.value != 0)
    
    def clear_axis(self, axis_num: int) -> bool:
        """
        清空轴的所有状态

        当急停输入有效时，无法清除急停信息
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False

        result: ctypes.c_int = self.lib.IMC_ClearAxis(self.handle, ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_pul_width(self, axis_num: int, time_ns: int = 2000) -> Tuple[bool, int]:
        """
        设置指定轴的有效电平的脉冲宽度
        
        :param self: class
        :param axis_num: 需要设置脉冲宽度的轴号
        :type axis_num: int
        :param time_ns: 脉冲宽度，单位为纳秒
        :type time_ns: int
        :return: [是否成功, 实际设置的脉冲宽度]
        :rtype: Tuple[bool, int]
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False, int(0)
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False, int(0)
        
        if time_ns < 16:
            logging.error(f'脉冲宽度超限：{axis_num}')
            return False, int(0)
        
        result: ctypes.c_int = self.lib.IMC_SetPulWidth(self.handle, ctypes.c_uint(time_ns), ctypes.c_int(axis_num))
        return bool(result.value != 0), result.value
    
    def set_pul_polar(self, axis_num: int, pul: bool, dir: bool) -> bool:
        """
        设置指定轴的脉冲和方向的有效电平
        
        :param self: class
        :param axis_num: 需要设置有效电平的轴号
        :type axis_num: int
        :param pul: 脉冲信号的有效电平。True：高电平有效； False：低电平有效
        :type pul: bool
        :param dir: 方向信号的有效电平。True：高电平有效； False：低电平有效
        :type dir: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetPulPolar(self.handle, ctypes.c_int(pul), ctypes.c_int(dir), ctypes.c_int(axis_num))
        return bool(result.value != 0)
        
    def set_encoder_enable(self, axis_num: int, enable: bool = True) -> bool:
        """
        使能/禁用控制卡接收编码器反馈

        控制卡中默认禁用编码器反馈，而是使用内部虚拟反馈
        
        :param self: class
        :param axis_num: 需要使能/禁止控制卡接收编码器反馈的轴号
        :type axis_num: int
        :param enable: 使能标志。True：使能； False：不使能
        :type enable: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetEncpEna(self.handle, ctypes.c_int(enable), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_encoder_mode(self, axis_num: int, mode: int = 0, dir: int = 1) -> bool:
        """
        设置控制卡接收编码器反馈的计数模式和计数方向

        1. 只有使能编码器反馈才需要设置计数模式和方向
        2. 编码器的计数方向与计数模式的选择有关。当计数模式为正交信号模式时，dir 为1，则 A 相超前 B 相为正方向；为0，B 相超前 A 相为正方向。当计数模式为脉冲+方向模式时，dir 为1，B-方向为高电平时往正方向计数；为0，B-方向为低电平时往正方向计数
        3. 控制卡中的计数模式默认为正交信号，计数方向默认为 A 相超前 B 相为正方向
        
        :param self: class
        :param axis_num: 需要设置的轴号
        :type axis_num: int
        :param mode: 编码器的计数模式。0：正交信号模式； 1：脉冲+方向模式
        :type mode: int
        :param dir: 编码器的计数方向
        :type dir: int
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if mode not in (0, 1):
            logging.error(f'编码器模式错误：{mode}')
            return False
        
        if dir not in (0, 1):
            logging.error(f'编码器方向错误：{dir}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetEncpMode(self.handle, ctypes.c_int(mode), ctypes.c_int(dir), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_encoder_rate(self, axis_num: int, rate: float) -> bool:
        """
        设置编码器反馈倍率

        1. 对于一般的伺服电机系统，编码器的计数单位与 iMC 的位置单位（脉冲）是一致的，即每个计数单位等于 iMC 的一个基本位置单位，即 1：1 的关系。但在某些场合，例如安装了编码器或光栅尺作为位置反馈的步进系统中，编码器的计数单位与 iMC 的基本位置单位不一定相同，可能存在 1：f 的关系，即编码器的一个计数单位相当于 f 个位置单位（脉冲），其中 f 可能是一个小数，f 称为编码器的倍率
        2. 假设编码器的线数是 1024 线，在 4 倍频计数模式下该编码器每旋转一圈，控制卡可得到 4096 的计数值。若控制卡每输出 12800 个脉冲可驱动电机运动一圈（编码器也旋转一圈），则 f = 12800 / 4096 = 3.125。如果 f 乘以 65536 的结果存在小数，则会存在误差
        
        :param self: class
        :param axis_num: 需要设置倍率的轴号
        :type axis_num: int
        :param rate: 倍率
        :type rate: float
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetEncpRate(self.handle, ctypes.c_double(rate), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_vel_acc_limit(self, axis_num: int, vellim: float,acclim: float) -> bool:
        """
        设置轴的速度和加速度极限

        1. 所有运动模式中，只要速度或加速度超过设定值，控制卡内部都会报错，并停止该轴的运动
        2. 控制卡中速度和加速度限制值都默认为 0。因此需要先设置此速度和加速度限制
        
        :param self: class
        :param axis_num: 需要设置速度和加速度极限的轴号
        :type axis_num: int
        :param vellim: 速度极限，范围是 0 – 32767.9999，单位为脉冲每毫秒
        :type vellim: float
        :param acclim: 加速度极限，范围是 0 – 32767.9999，单位为脉冲每平方毫秒
        :type acclim: float
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if not (0 <= vellim <= 32767.9999):
            logging.error(f'速度限制超限：{vellim}')
            return False
        
        if not (0 <= acclim <= 32767.9999):
            logging.error(f'加速度限制超限：{acclim}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetVelAccLimit(self.handle, ctypes.c_double(vellim), ctypes.c_double(acclim), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_smooth(self, axis_num: int, smooth: int = 64) -> bool:
        """
        设置每个轴的平滑度

        1. 当轴在运动过程中时，不能修改平滑度，否则有可能会出错
        2. 设置的平滑度值越大则越平滑，但运动轨迹的误差就越大
        3. 控制卡中每个轴的平滑度默认值为 64
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param smooth: 平滑度，范围 0 - 32767
        :type smooth: int
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if smooth not in range(0, 32768):
            logging.error(f'平滑度超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetSmooth(self.handle, ctypes.c_short(smooth), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_enable(self, axis_num: int, enable: bool = False) -> bool:
        """
        使能/禁止指定轴的驱动器

        1. 需要进行运动的轴都必须设置使能，否则控制卡将不会对该轴发出脉冲
        2. 控制卡中默认值为 False，即默认不使能驱动器
        3. 必须先设置轴的速度和加速度极限之后才能使能驱动器，否则控制卡会置位速度和加速度超限的错误
        
        :param self: class
        :param axis_num: 需要使能/禁止驱动器的轴号
        :type axis_num: int
        :param enable: 使能标志。True：使能； False：不使能
        :type enable: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetEna(self.handle, ctypes.c_int(enable), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_hw_limit(self, axis_num: int, 
                     positive_limit_enable: bool = True, negative_limit_enable: bool = True, 
                     positive_limit_polar: bool = False, negative_limit_polar: bool = False) -> bool:
        """
        使能/禁用硬件输入端口限位功能和设置其有效极性

        控制卡中默认使能限位功能，其极性是低电平有效
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param positive_limit_enable: 是否使能硬件正限位功能。True：使能； False：不使能
        :type positive_limit_enable: bool
        :param negative_limit_enable: 是否使能硬件负限位功能。True：使能； False：不使能
        :type negative_limit_enable: bool
        :param positive_limit_polar: 正限位极性；True：高电平有效； False：低电平有效
        :type positive_limit_polar: bool
        :param negative_limit_polar: 负限位极性；True：高电平有效； False：低电平有效
        :type negative_limit_polar: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_Setlimit(self.handle, 
                                                     ctypes.c_int(positive_limit_enable), ctypes.c_int(positive_limit_polar),
                                                     ctypes.c_int(negative_limit_enable), ctypes.c_int(negative_limit_polar),
                                                     ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_alarm(self, axis_num: int, enable: bool = False, polar: bool = False) -> bool:
        """
        使能/禁用伺服报警输入和设置其有效极性

        1. 控制卡中默认不使能伺服报警功能
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param enable: 是否使能伺服报警输入功能。True：使能； False：不使能
        :type enable: bool
        :param polar: 极性；True：高电平有效； False：低电平有效
        :type polar: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetAlm(self.handle, 
                                                   ctypes.c_int(enable), ctypes.c_int(polar),
                                                   ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_in_place_input(self, axis_num: int, enable: bool = False, polar: bool = False) -> bool:
        """
        使能/禁用伺服到位输入和设置其有效极性

        1. 控制卡中默认不使能伺服到位功能
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param enable: 是否使能伺服到位输入功能。True：使能； False：不使能
        :type enable: bool
        :param polar: 极性；True：高电平有效； False：低电平有效
        :type polar: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetINP(self.handle, 
                                                   ctypes.c_int(enable), ctypes.c_int(polar),
                                                   ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_emergency_stop_polar(self, axis_num: int, polar: bool = False) -> bool:
        """
        设置急停输入端的有效极性

        1. 控制卡中默认值为 0，即低电平有效
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param polar: 极性；True：高电平有效； False：低电平有效
        :type polar: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetEmstopPolar(self.handle,  ctypes.c_int(polar), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_uni_input_polar(self, input_num: int, polar: bool = False) -> bool:
        """
        设置通用输入端的有效极性

        1. 控制卡中默认值为False，即低电平有效
        2. 输入端口号与控制卡硬件的对应关系如表 8.10-1
        
        :param self: class
        :param input_num: 输入端口，范围 1 - 32
        :type input_num: int
        :param polar: 极性；True：高电平有效； False：低电平有效
        :type polar: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if input_num not in range(1, 32 + 1):
            logging.error(f'输入端口编号超限：{input_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetInPolar(self.handle,  ctypes.c_int(polar), ctypes.c_int(input_num))
        return bool(result.value != 0)
    
    def set_stop_flit(self, axis_num: int, stop: bool = True) -> bool:
        """
        设置错误发生时，运动轴是否停止运行

        1. 控制卡中默认发生错误时运动轴停止运行
        2. 停止运行执行的是正常停止该轴的运动，即减速停止轴运动，不禁止驱动器使能
        3. 要恢复停止运行后的轴功能，只需检查并确认排除错误后，再使用“8.11 错误清除”函数清除控制卡中的错误标志
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param stop: 是否停止运行；True：停止； False：不停止
        :type stop: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetStopfilt(self.handle,  ctypes.c_int(stop), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_exit_flit(self, axis_num: int, exit: bool = True) -> bool:
        """
        设置错误发生时，运动轴是否退出运行

        1. 控制卡中默认发生错误时运动轴退出运行
        2. 退出运行是禁止驱动器使能，并停止脉冲输出。因禁止驱动器使能，因此电机可能存在自由滑行，所以该轴的机械原点可能不再正确，恢复运行后应重新搜寻机械零点
        3. 要恢复退出运行后的轴功能，需先排除退出运行的错误原因，然后使用“8.11 错误清除”函数清除控制卡中的错误标志。最后使用“8.3.2.10 使能/禁止驱动器”函数使能驱动器
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param exit: 是否退出运行；True：退出； False：不退出
        :type exit: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetExitfilt(self.handle,  ctypes.c_int(exit), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_recoup_range(self, axis_num: int, range: int) -> bool:
        """
        设置静态补偿的范围

        1. 在某些应用场合，要求运动停止后位置误差保持在设定的范围之内，以保证定位精度。在误差超出此函数设置的范围时，控制卡进行误差补偿，使误差始终处于设定的范围内
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param range: 误差补偿值；取值范围 0 - 32767
        :type range: int
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if range not in range(0, 32768):
            logging.error(f'静态补偿范围超限：{range}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetRecoupRange(self.handle,  ctypes.c_int(range), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def get_config(self, axis_num: int) -> Tuple[bool, Dict]:
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        steptime = ctypes.c_int()
        pulpolar = ctypes.c_int()
        dirpolar = ctypes.c_int()
        encpena = ctypes.c_int()
        encpmode = ctypes.c_int()
        encpdir = ctypes.c_int()
        encpfactor = ctypes.c_double()
        vellim = ctypes.c_int()
        acclim = ctypes.c_int()
        drvena = ctypes.c_int()
        plimena = ctypes.c_int()
        plimpolar = ctypes.c_int()
        nlimena = ctypes.c_int()
        nlimpolar = ctypes.c_int()
        almena = ctypes.c_int()
        almpolar = ctypes.c_int()
        INPena = ctypes.c_int()
        INPpolar = ctypes.c_int()

        result: ctypes.c_int = self.lib.IMC_GetConfig(self.handle,
                                                      ctypes.byref(steptime), ctypes.byref(pulpolar), ctypes.byref(dirpolar),
                                                      ctypes.byref(encpena), ctypes.byref(encpmode), ctypes.byref(encpdir), ctypes.byref(encpfactor),
                                                      ctypes.byref(vellim), ctypes.byref(acclim),
                                                      ctypes.byref(drvena),
                                                      ctypes.byref(plimena), ctypes.byref(plimpolar),
                                                      ctypes.byref(nlimena), ctypes.byref(nlimpolar),
                                                      ctypes.byref(almena), ctypes.byref(almpolar),
                                                      ctypes.byref(INPena), ctypes.byref(INPpolar),
                                                      ctypes.c_int(axis_num))
        
        if result.value != 0:
            return False, {}
        else:
            return True, {
                'steptime': steptime.value,
                'pulpolar': bool(pulpolar.value),
                'dirpolar': bool(dirpolar.value),
                'encpena': bool(encpena.value),
                'encpmode': encpmode.value,
                'encpdir': encpdir.value,
                'encpfactor': encpfactor.value,
                'vellim': vellim.value,
                'acclim': acclim.value,
                'drvena': bool(drvena.value),
                'plimena': bool(plimena.value),
                'plimpolar': bool(plimpolar.value),
                'nlimena': bool(nlimena.value),
                'nlimpolar': bool(nlimpolar.value),
                'almena': bool(almena.value),
                'almpolar': bool(almpolar.value),
                'INPena': bool(INPena.value),
                'INPpolar': bool(INPpolar.value),
            }
        
    ##########
    # 点到点运动函数

    def set_accel(self, axis_num: int, accel: float, decel: float, primary: bool = True) -> bool:
        """
        设置当前指定轴的加速度和减速度

        1. 控制卡上电后默认的加速度和减速度都为 0，因此在单个轴进行除插补运动之外的所有运动时，都需要先设置加速度和减速度
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param accel: 加速度，范围是 0-32767.9999，单位为脉冲每平方毫秒
        :type accel: float
        :param decel: 减速度，范围是 0-32767.9999，单位为脉冲每平方毫秒
        :type decel: float
        :param primary: 是否为主坐标系
        :type primary: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if not (0 <= accel <= 32767.9999):
            logging.error(f'加速度范围超限：{accel}')
            return False
        
        if not (0 <= decel <= 32767.9999):
            logging.error(f'减速度范围超限：{decel}')
            return False
        
        result = ctypes.c_int()
        if primary:
            result = self.lib.IMC_SetAccel(self.handle, ctypes.c_double(accel), ctypes.c_double(decel), ctypes.c_int(axis_num))
        else:
            result = self.lib.IMC_SetAccel_P(self.handle, ctypes.c_double(accel), ctypes.c_double(decel), ctypes.c_int(axis_num))

        return bool(result.value != 0)
    
    def move_abs(self, axis_num: int, position: int, start_vel: float, target_vel: float, wait: bool, primary: bool = True) -> bool:
        """
        使轴从当前位置移动到指定的目标位置

        1. 当 wait 参数为非零时，需要使用多线程来调用此函数，否则程序有可能会出现假死现象
        2. 当目标位置比当前位置值大，则是正方向运动，比当前位置值小，则是往负方向运动。
        3. 轴的目标速度必须为正值
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param position: 目标位置，单位为脉冲
        :type position: int
        :param start_vel: 起始速度，范围是 0-32767.9999，单位为脉冲每毫秒
        :type start_vel: float
        :param target_vel: 目标速度，范围是 0-32767.9999，单位为脉冲每毫秒
        :type target_vel: float
        :param wait: 是否等待运动完成后，函数才返回。True：等待运动完成；False：不等待
        :type wait: bool
        :param primary: 是否为主坐标系
        :type primary: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if not (0 <= start_vel <= 32767.9999):
            logging.error(f'速度范围超限：{start_vel}')
            return False
        
        if not (0 <= target_vel <= 32767.9999):
            logging.error(f'速度范围超限：{target_vel}')
            return False
        
        result = ctypes.c_int()
        if primary:
            result = self.lib.IMC_MoveAbs(self.handle, ctypes.c_long(position), 
                                          ctypes.c_double(start_vel), ctypes.c_double(target_vel), 
                                          ctypes.c_int(wait), ctypes.c_int(axis_num))
        else:
            result = self.lib.IMC_MoveAbs_P(self.handle, ctypes.c_long(position), 
                                            ctypes.c_double(start_vel), ctypes.c_double(target_vel), 
                                            ctypes.c_int(wait), ctypes.c_int(axis_num))

        return bool(result.value != 0)
    
    def move_distance(self, axis_num: int, distance: int, start_vel: float, target_vel: float, wait: bool, primary: bool = True) -> bool:
        """
        使轴从当前位置移动到指定的距离

        1. 当 wait 参数为非零时，需要使用多线程来调用此函数，否则程序有可能会出现假死现象
        2. 当移动距离是正数时，移动方向为正方向，移动距离是负数时，移动方向为负方向
        3. 目标速度必须为正值
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param distance: 移动距离，单位为脉冲
        :type distance: int
        :param start_vel: 起始速度，范围是 0-32767.9999，单位为脉冲每毫秒
        :type start_vel: float
        :param target_vel: 目标速度，范围是 0-32767.9999，单位为脉冲每毫秒
        :type target_vel: float
        :param wait: 是否等待运动完成后，函数才返回。True：等待运动完成；False：不等待
        :type wait: bool
        :param primary: 是否为主坐标系
        :type primary: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if not (0 <= start_vel <= 32767.9999):
            logging.error(f'速度范围超限：{start_vel}')
            return False
        
        if not (0 <= target_vel <= 32767.9999):
            logging.error(f'速度范围超限：{target_vel}')
            return False
        
        result = ctypes.c_int()
        if primary:
            result = self.lib.IMC_MoveDist(self.handle, ctypes.c_long(distance), 
                                           ctypes.c_double(start_vel), ctypes.c_double(target_vel), 
                                           ctypes.c_int(wait), ctypes.c_int(axis_num))
        else:
            result = self.lib.IMC_MoveDist_P(self.handle, ctypes.c_long(distance), 
                                             ctypes.c_double(start_vel), ctypes.c_double(target_vel), 
                                             ctypes.c_int(wait), ctypes.c_int(axis_num))

        return bool(result.value != 0)
    
    def set_p2p_vel(self, axis_num: int, target_vel: float, primary: bool = True) -> bool:
        """
        立即改变当前正在执行的点到点运动的运动速度

        1. 如果重新调用了点到点运动函数，则速度将会被运动函数中指定的速度替换
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param target_vel: 目标速度，范围是 0-32767.9999，单位为脉冲每毫秒
        :type target_vel: float
        :param primary: 是否为主坐标系
        :type primary: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if not (0 <= target_vel <= 32767.9999):
            logging.error(f'速度范围超限：{target_vel}')
            return False
        
        result = ctypes.c_int()
        if primary:
            result = self.lib.IMC_P2Pvel(self.handle, ctypes.c_double(target_vel), ctypes.c_int(axis_num))
        else:
            result = self.lib.IMC_P2Pvel_P(self.handle, ctypes.c_double(target_vel), ctypes.c_int(axis_num))

        return bool(result.value != 0)
    
    def set_p2p_mode(self, axis_num: int, mode: int = 0, primary: bool = True) -> bool:
        """
        设置点到点运动的模式

        1. 点到点运动有 2 种运动模式，分别是普通模式和跟踪模式。跟踪模式是任何时候只要设定的目标位置改变，立即执行点到点运动模式到达新的目标位置。而普通模式，只有在执行点到点运动的过程中，改变目标位置才会移动到新的目标位置，其他时候改变目标位置都不会移动
        2. 控制卡内默认点到点运动为普通模式
        3. 当设置为跟踪模式后，此轴将不能参与其他运动模式中运动
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param mode: 点到点运动模式。0：正常模式； 1：跟踪模式
        :type mode: int
        :param primary: 是否为主坐标系
        :type primary: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if mode not in (0, 1):
            logging.error(f'点到点运动模式错误：{mode}')
            return False
        
        result = ctypes.c_int()
        if primary:
            result = self.lib.IMC_SetP2Pmode(self.handle, ctypes.c_int(mode), ctypes.c_int(axis_num))
        else:
            result = self.lib.IMC_SetP2Pmode_P(self.handle, ctypes.c_int(mode), ctypes.c_int(axis_num))

        return bool(result.value != 0)
    
    def set_p2p_new_pos(self, axis_num: int, position: int, primary: bool = True) -> bool:
        """
        改变点到点运动的目标位置

        1. 当点到点运动模式是普通模式时，如果轴正在做点到点运动，此时改变目标位置，则立即以新目标为终点。如果轴处于静止状态，则不会有任何效果
        2. 当点到点运动模式是跟踪模式时，任何时候改变目标位置，都会开始移动，并到达新的目标位置处
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param position: 目标位置，单位为脉冲
        :type position: int
        :param primary: 是否为主坐标系
        :type primary: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result = ctypes.c_int()
        if primary:
            result = self.lib.IMC_SetP2PnewPos(self.handle, ctypes.c_long(position), ctypes.c_int(axis_num))
        else:
            result = self.lib.IMC_SetP2PnewPos_P(self.handle, ctypes.c_long(position), ctypes.c_int(axis_num))

        return bool(result.value != 0)
    
    def p2p_stop(self, axis_num: int, primary: bool = True) -> bool:
        """
        停止点到点运动
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param primary: 是否为主坐标系
        :type primary: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result = ctypes.c_int()
        if primary:
            result = self.lib.IMC_P2Pstop(self.handle, ctypes.c_int(axis_num))
        else:
            result = self.lib.IMC_P2Pstop_P(self.handle, ctypes.c_int(axis_num))

        return bool(result.value != 0)
    
    def set_move_vel(self, axis_num: int, start_vel: float, target_vel: float, primary: bool = True) -> bool:
        """
        使轴立即按指定的速度一直运动，直到速度被改变为止

        1. 当再次使用此函数设置 tgvel 为 0 时，将减速停止匀速运动
        2. 可以使用此函数实现软件点动功能，即按钮按下时，给定一个速度，放开时，将速度设为 0
        3. 当轴的运动速度为正数时，运动方向为正方向，为负数时，运动方向为负方向
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param start_vel: 起始速度，范围是 -32767.9999 到 32767.9999，单位为脉冲每毫秒
        :type start_vel: float
        :param target_vel: 目标速度，范围是 -32767.9999 到 32767.9999，单位为脉冲每毫秒
        :type target_vel: float
        :param primary: 是否为主坐标系
        :type primary: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if not (-32767.9999 <= start_vel <= 32767.9999):
            logging.error(f'速度范围超限：{start_vel}')
            return False
        
        if not (-32767.9999 <= target_vel <= 32767.9999):
            logging.error(f'速度范围超限：{target_vel}')
            return False
        
        result = ctypes.c_int()
        if primary:
            result = self.lib.IMC_MoveVel(self.handle, ctypes.c_double(start_vel), ctypes.c_double(target_vel), ctypes.c_int(axis_num))
        else:
            result = self.lib.IMC_MoveVel_P(self.handle, ctypes.c_double(start_vel), ctypes.c_double(target_vel), ctypes.c_int(axis_num))

        return bool(result.value != 0)
    
    ##########
    # 环形轴函数

    ##########
    # 插补运动函数

    ##########
    # 齿轮函数

    ##########
    # IO控制

    def set_output(self, output_num: int, value: bool = False, fifo: FifoSel = FifoSel.SEL_IFIFO) -> bool:
        """
        对输出端口进行控制

        1. 以太网类型不同轴数的控制卡，其输出端口数不同，最多 48 个，最少 40 个，其根据控制卡的实际输出端口数来进行控制
        
        :param self: class
        :param output_num: 输出端口号；范围是 1 – 48
        :type output_num: int
        :param value: 控制输出端口的状态； False：断开输出端口； True：连通输出端口
        :type value: bool
        :param fifo: 指定将此指令发送到哪个 FIFO 中执行
        :type fifo: FifoSel
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if output_num not in range(1, 48 + 1):
            logging.error(f'输出端口编号超限：{output_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetOut(self.handle, ctypes.c_int(output_num), ctypes.c_int(value), ctypes.c_int(fifo.value))
        return bool(result.value != 0)
    
    ##########
    # 搜索零点函数

    def set_home_vel(self, axis_num: int, high_vel: float, low_vel: float) -> bool:
        """
        设置当前搜零过程中使用的高速度和低速度

        1. 控制卡中默认高速和低速都为 0，因此在首次使用搜零函数前，需要设置搜零速度
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param high_vel: 高速搜索速度，范围是 0-32767.9999，单位为脉冲每毫秒
        :type high_vel: float
        :param low_vel: 低速搜索速度，范围是 0-32767.9999，单位为脉冲每毫秒
        :type low_vel: float
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if not (0 <= high_vel <= 32767.9999):
            logging.error(f'高速搜索速度范围超限：{high_vel}')
            return False
        
        if not (0 <= low_vel <= 32767.9999):
            logging.error(f'低速搜索速度范围超限：{low_vel}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetHomeVel(self.handle, ctypes.c_double(high_vel), ctypes.c_double(low_vel), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def set_home_index_polar(self, axis_num: int, polar: float) -> bool:
        """
        设置编码器索引信号的有效极性

        1. 控制卡中默认编码器索引信号为上升沿有效
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param polar: 索引信号的极性；True：上升沿有效； False：下降沿有效
        :type polar: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetHomeIndexPolar(self.handle, ctypes.c_int(polar), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def home_switch(self, axis_num: int, check_num: int, dir: int, rise_edge: bool, pos: int, stpos: int, move_vel: float, wait: bool) -> bool:
        """
        使用零点开关搜索零点
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param check_num: 零点开关搜索次数，0~3
        :type check_num: int
        :param dir: 搜零方向。零：正方向搜零；非零：负方向搜零；
        :type dir: int
        :param rise_edge: 指定检测原点开关的边沿；False：下降沿； True：上升沿
        :type rise_edge: bool
        :param pos: 设置零点时刻零点开关的位置值
        :type pos: int
        :param stpos: 搜零结束时，电机停止的位置
        :type stpos: int
        :param move_vel: 设置零点后移动到停止位置时的速度，范围是 0-32767.9999
        :type move_vel: float
        :param wait: 是否搜零运动完成，函数才返回。True：等待运动完成；False：不等待
        :type wait: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        if check_num not in (1, 2, 3):
            logging.error(f'搜零检测方式错误：{check_num}')
            return False
        
        if dir not in (0, 1):
            logging.error(f'搜零方向错误：{dir}')
            return False
        
        if not (0 <= move_vel <= 32767.9999):
            logging.error(f'速度范围超限：{move_vel}')
            return False
        
        result: ctypes.c_int = ctypes.c_int()
        if check_num == 1:
            result = self.lib.IMC_HomeSwitch1(self.handle, 
                                             ctypes.c_int(dir), ctypes.c_int(rise_edge), 
                                             ctypes.c_long(pos), ctypes.c_long(stpos), 
                                             ctypes.c_double(move_vel), ctypes.c_int(wait), 
                                             ctypes.c_int(axis_num))
        elif check_num == 2:
            result = self.lib.IMC_HomeSwitch2(self.handle, 
                                             ctypes.c_int(dir), ctypes.c_int(rise_edge), 
                                             ctypes.c_long(pos), ctypes.c_long(stpos), 
                                             ctypes.c_double(move_vel), ctypes.c_int(wait), 
                                             ctypes.c_int(axis_num))
        elif check_num == 3:
            result = self.lib.IMC_HomeSwitch3(self.handle, 
                                             ctypes.c_int(dir), ctypes.c_int(rise_edge), 
                                             ctypes.c_long(pos), ctypes.c_long(stpos), 
                                             ctypes.c_double(move_vel), ctypes.c_int(wait), 
                                             ctypes.c_int(axis_num))
            
        return bool(result.value != 0)
    
    def set_pos(self, axis_num: int, position: int) -> bool:
        """
        把该轴的当前位置设定为指定值

        1. 可以使用此函数将轴的当前位置清零。可用于没有安装零点开关的轴设置零点位置
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :param position: 设置的指定值，单位为脉冲
        :type position: int
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_SetPos(self.handle, ctypes.c_long(position), ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    def home_stop(self, axis_num: int) -> bool:
        """
        立即停止搜零运动
        
        :param self: class
        :param axis_num: 轴号
        :type axis_num: int
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_HomeStop(self.handle, ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    ##########
    # 获得状态函数

    def get_axis_num(self) -> int:
        """
        获取控制卡上的轴数量
        
        :param self: class
        :return: 轴数量
        :rtype: int
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return 0
        
        axis_num: ctypes.c_int = self.lib.IMC_GetAxisNum(self.handle, ctypes.byref(axis_num))
        return axis_num.value
    
    def get_encounter_position(self) -> Tuple[bool, List[int]]:
        """
        获得所有轴的机械位置

        1. 返回的位置数据是从轴 0 开始按顺序存放的
        2. 如果没有启用编码器反馈，则函数获得的是控制卡内部的虚拟反馈值
        3. 正常情况下，电机处于停止状态时，机械位置应与指令位置相同
        
        :param self: class
        :return: [是否成功, 位置列表]
        :rtype: Tuple[bool, List[int]]
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False, 0
        
        axis_num: int = self.get_axis_num()
        position: ctypes.Array[ctypes.c_long] = (ctypes.c_long * axis_num)()
        result: ctypes.c_int = self.lib.IMC_GetEncp(self.handle, ctypes.byref(position), ctypes.c_int(axis_num))
        if result.value != 0:
            return False, []
        else:
            return True, position.value
        
    def get_command_position(self) -> Tuple[bool, List[int]]:
        """
        获得所有轴的指令位置

        1. 返回的位置数据是从轴 0 开始按顺序存放的
        
        :param self: class
        :return: [是否成功, [机械位置]]
        :rtype: Tuple[bool, List[int]]
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False, 0
        
        axis_num: int = self.get_axis_num()
        position: ctypes.Array[ctypes.c_long] = (ctypes.c_long * axis_num)()
        result: ctypes.c_int = self.lib.IMC_GetCurpos(self.handle, ctypes.byref(position), ctypes.c_int(axis_num))
        if result.value != 0:
            return False, []
        else:
            return True, position.value
        
    def get_axis_moving_status(self) -> Tuple[bool, bool]:
        """
        获得所有轴的运动状态

        1. 返回的位置数据是从轴 0 开始按顺序存放的
        2. 所有运动都可以通过此函数判断轴是否运动完成
        
        :param self: class
        :return: [是否成功, [运动状态]]
        :rtype: Tuple[bool, bool]
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False, False
                
        axis_num: int = self.get_axis_num()
        moving: ctypes.Array[ctypes.c_short] = (ctypes.c_short * axis_num)()
        result: ctypes.c_int = self.lib.IMC_GetMoving(self.handle, ctypes.byref(moving), ctypes.c_int(axis_num))
        if result.value != 0:
            return False, False
        else:
            return True, [bool(moving.value[i]) for i in range(axis_num)]
        
    def get_axis_all_input_status(self) -> Tuple[bool, List[Dict[str, bool]]]:
        """
        获得所有轴的输入端口状态

        1. 返回的位置数据是从轴 0 开始按顺序存放的
        
        :param self: class
        :return: [是否成功, {输入端口状态}]
        :rtype: Tuple[bool, List[Dict[str, bool]]]
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False, False
                
        axis_num: int = self.get_axis_num()
        input_status: ctypes.Array[ctypes.c_short] = (ctypes.c_ushort * axis_num * 6)()
        result: ctypes.c_int = self.lib.IMC_GetAin(self.handle, ctypes.byref(input_status), ctypes.c_int(axis_num))
        if result.value != 0:
            return False, []
        else:
            status_List: List[Dict[str, bool]] = []
            for i in range(axis_num):
                status_List.append({
                    'PLim': bool(input_status[i][0]),   # 正限位
                    'NLim': bool(input_status[i][1]),   # 负限位
                    'ORG': bool(input_status[i][2]),    # 原点
                    'PRO': bool(input_status[i][3]),    # 探针
                    'ALM': bool(input_status[i][4]),    # 报警
                    'INP': bool(input_status[i][5]),    # 到位
                })
            return True, status_List
        
    def get_uni_input_status(self) -> Tuple[bool, List[bool]]:
        """
        获得所有通用输入端口的实时状态

        1. 当 gin 的值为False时，表示输入开关连通；为True，表示输入开关断开
        
        :param self: class
        :return: [是否成功, 输入端口状态列表]
        :rtype: Tuple[bool, List[bool]]
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False, False
                
        input_num: int = 32
        input_status: ctypes.Array[ctypes.c_short] = (ctypes.c_ushort * input_num)()
        result: ctypes.c_int = self.lib.IMC_GetGin(self.handle, ctypes.byref(input_status), ctypes.c_int(input_num))
        if result.value != 0:
            return False, []
        else:
            return True, [bool(input_status.value[i]) for i in range(input_num)]
        
    def get_uni_output_status(self) -> Tuple[bool, List[bool]]:
        """
        获得所有输出端口的状态

        1. 当 gout 的值为False时，表示输出开关断开；为True时，表示输出开关连通
        
        :param self: class
        :return: [是否成功, 输出端口状态列表]
        :rtype: Tuple[bool, List[bool]]
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False, False
                
        output_num: int = 48
        output_status: ctypes.Array[ctypes.c_short] = (ctypes.c_ushort * output_num)()
        result: ctypes.c_int = self.lib.IMC_GetGout(self.handle, ctypes.byref(output_status))
        if result.value != 0:
            return False, []
        else:
            return True, [bool(output_status.value[i]) for i in range(output_num)]
        

    def get_axis_error_status(self) -> Tuple[bool, List[ErrorCode]]:
        """
        获得所有轴的错误状态
        
        :param self: class
        :return: [是否成功, [错误代码]]
        :rtype: Tuple[bool, List[ErrorCode]]
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False, 0
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False, 0
        
        axis_num: int = self.get_axis_num()
        error_code: ctypes.Array[ctypes.c_ushort] = (ctypes.c_ushort * axis_num)()
        result: ctypes.c_int = self.lib.IMC_GetErrorReg(self.handle, ctypes.byref(error_code), ctypes.c_int(axis_num))
        if result.value != 0:
            return False, 0
        else:
            return True, [ErrorCode(error_code.value[i]) for i in range(axis_num)]
        
    def get_error_str(self, error_code: ErrorCode) -> str:
        """
        根据错误代码获取错误描述字符串
        
        :param self: class
        :param error_code: 错误代码
        :type error_code: ErrorCode
        :return: 错误描述字符串
        :rtype: str
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return ''
        
        error_str: ctypes.c_char_p = self.lib.IMC_GetErrorStr(ctypes.c_ushort(error_code.value))
        return error_str.value.decode('utf-8').strip()
    
    ##########
    # 错误清除

    def clear_axis_error(self, axis_num: int) -> bool:
        """
        立即清除指定轴的错误

        1. 当由 8.10.8 获取轴运动错误状态 得到的值为非零时，可以使用此函数清除错误。注意，由硬件限位和急停输入引起的错误不能通过此函数清除
        
        :param self: class
        :param axis_num: 需要清除错误的轴号
        :type axis_num: int
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        if axis_num not in range(0, 16):
            logging.error(f'轴编号超限：{axis_num}')
            return False
        
        result: ctypes.c_int = self.lib.IMC_ClrError(self.handle, ctypes.c_int(axis_num))
        return bool(result.value != 0)
    
    ##########
    # 其他功能函数

    def emergency_stop(self, stop: bool = True) -> bool:
        """
        急停或解除急停

        1. 当 stop 参数为 True 时，表示急停；为 False 时，表示解除急停
        2. 除了停止输入端口可以停止轴运动外，还可以使用软件停止。此功能和停止输入端口的功能相同
        3. 当使用此函数停止之后，控制卡会禁止所有轴的驱动器
        4. 当使用此函数解除停止之后，需要再使用“8.11 错误清除”函数清除控制卡中所有轴的错误标志，使用“8.3.2.10 使能/禁止驱动器”函数使能所有轴的驱动器
        
        :param self: class
        :param stop: 急停或解除急停
        :type stop: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        result: ctypes.c_int = self.lib.IMC_Emstop(self.handle, ctypes.c_int(stop))
        return bool(result.value != 0)
    
    def pause(self, pause: bool = True) -> bool:
        """
        对所有轴立即暂停或解除暂停状态

        1. 当 pause 参数为 True 时，表示暂停；为 False 时，表示恢复
        2. 使用暂停功能时，运动的轴是减速停止的
        
        :param self: class
        :param pause: 暂停或恢复
        :type pause: bool
        :return: 是否成功
        :rtype: bool
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return False
        
        result: ctypes.c_int = self.lib.IMC_Pause(self.handle, ctypes.c_int(pause))
        return bool(result.value != 0)
    
    def exit_wait(self) -> None:
        """
        退出所有等待状态的运动函数

        1. 当某个运动函数在等待运动完成时，可以使用此函数退出等待状态，使得运动函数立即返回
        2. 使用此函数后，运动轴将继续保持运动状态，不会停止
        
        :param self: class
        :return: None
        :rtype: None
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return
        
        self.lib.IMC_ExitWait(self.handle)

    def get_func_error_str(self) -> str:
        """
        获取最后一次函数调用的错误描述字符串
        
        :param self: class
        :return: 错误描述字符串
        :rtype: str
        """
        if self.handle.value == 0:
            logging.error(f'控制卡句柄未打开')
            return ''
        
        error_str: ctypes.c_char_p = self.lib.IMC_GetFunErrStr(self.handle)
        return error_str.value.decode('utf-8').strip()
    
if __name__ == '__main__':
    ctrl = IMCControl('./lib/libIMCnet.so.1.0.0')
    for net in ctrl.find_net_card()[1]:
        print(f'发现网卡：{net}')




