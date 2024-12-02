import numpy as np
import cv2

def analyze_gauge(self, image, gauge_type="hp"):
    # 이미지를 numpy 배열로 변환
    img_array = np.array(image)
    
    # 게은색 픽셀 마스크 설정 (RGB 값이 모두 0에 가까운 픽셀)
    black_threshold = 30  # 약간의 여유를 둠
    black_mask = np.all(img_array <= black_threshold, axis=2)
    
    # 전체 픽셀 수 계산
    total_pixels = black_mask.shape[1]  # 가로 픽셀 수
    
    # 검은색 픽셀 수 계산
    black_pixels = np.count_nonzero(black_mask)
    
    # 게이지 비율 계산 (검은색이 아닌 부분의 비율)
    ratio = 100 - ((black_pixels / total_pixels) * 100)
    
    return round(ratio, 1)

def get_gauge_values(self):
    hp_image = self.capture_hp_gauge()
    mp_image = self.capture_mp_gauge()
    
    hp_ratio = self.analyze_gauge(hp_image, "hp")
    mp_ratio = self.analyze_gauge(mp_image, "mp")
    
    return hp_ratio, mp_ratio 