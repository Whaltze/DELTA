import cv2
import numpy as np
import glob

# 设置棋盘格参数
pattern_size = (8, 6)  # 内角点数量
square_size = 25.0     # 每个方格的实际尺寸 (毫米)

# 准备对象点 (0,0,0), (1,0,0), (2,0,0) ..., (7,5,0)
objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
objp *= square_size

# 存储对象点和图像点的列表
objpoints = []  # 真实世界中的3D点
imgpoints = []  # 图像中的2D点

# 获取标定图像
images = glob.glob('calibration_images/*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 查找棋盘格角点
    ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)
    
    if ret:
        print(f"处理图像: {fname}")
        objpoints.append(objp)
        
        # 提高角点检测精度
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners_refined)
        
        # 绘制并显示角点
        cv2.drawChessboardCorners(img, pattern_size, corners_refined, ret)
        cv2.imshow('Corners', img)
        cv2.waitKey(500)
    else:
        print(f"未找到角点: {fname}")

cv2.destroyAllWindows()

# 进行相机标定
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)

# 打印标定结果
print("\n相机标定结果:")
print(f"重投影误差: {ret}")
print("相机内参矩阵:")
print(camera_matrix)
print("\n畸变系数:")
print(dist_coeffs)

# 保存标定结果
np.savez('camera_calibration.npz', 
         camera_matrix=camera_matrix, 
         dist_coeffs=dist_coeffs)

print("\n标定结果已保存到 camera_calibration.npz")