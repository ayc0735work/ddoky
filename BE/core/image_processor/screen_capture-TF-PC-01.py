import numpy as np
import cv2

def capture_hp_gauge(self):
    # 디버그: 캡처 전 정보 출력
    print("\nHP 게이지 캡처 시도:")
    print(f"- 캡처 영역: {self.hp_gauge_rect}")
    
    # 이미지 캡처
    image = self.capture_area(self.hp_gauge_rect)
    
    # 디버그: 캡처된 이미지 정보 출력
    if image is not None:
        print(f"- 캡처 성공: {image.size}, 모드: {image.mode}")
        # 캡처된 이미지 저장
        image.save('captured_hp.png')
    else:
        print("- 캡처 실패!")
    
    return image

def capture_mp_gauge(self):
    # 디버그: 캡처 전 정보 출력
    print("\nMP 게이지 캡처 시도:")
    print(f"- 캡처 영역: {self.mp_gauge_rect}")
    
    # 이미지 캡처
    image = self.capture_area(self.mp_gauge_rect)
    
    # 디버그: 캡처된 이미지 정보 출력
    if image is not None:
        print(f"- 캡처 성공: {image.size}, 모드: {image.mode}")
        # 캡처된 이미지 저장
        image.save('captured_mp.png')
    else:
        print("- 캡처 실패!")
    
    return image

def analyze_gauge(self, image, gauge_type="hp"):
    if image is None:
        print(f"{gauge_type.upper()} 게이지 분석 실패: 이미지가 None입니다")
        return 0.0
        
    # 이미지를 numpy 배열로 변환
    img_array = np.array(image)
    height, width = img_array.shape[:2]
    
    # 디버그: 이미지 정보 출력
    print(f"\n{gauge_type.upper()} 이미지 분석 시작:")
    print(f"- Shape: {img_array.shape}")
    print(f"- dtype: {img_array.dtype}")
    
    # 중앙 행 선택
    middle_row = height // 2
    row_data = img_array[middle_row]
    
    # 픽셀 밝기 계산 (RGB 평균)
    brightness = np.mean(row_data, axis=1)
    
    # 디버그: 밝기 값 출력
    print("\n중앙 행 첫 10개 픽셀 밝기:")
    for i in range(min(10, len(brightness))):
        print(f"Pixel {i}: RGB={row_data[i]}, Brightness={brightness[i]:.1f}")
    
    # 어두운 픽셀 카운트 (임계값: 50)
    dark_pixels = np.sum(brightness < 50)
    
    # 게이지 비율 계산
    ratio = 100 - (dark_pixels / width * 100)
    
    print(f"\n분석 결과:")
    print(f"- 전체 픽셀: {width}")
    print(f"- 어두운 픽셀: {dark_pixels}")
    print(f"- 밝기 범위: {brightness.min():.1f} ~ {brightness.max():.1f}")
    print(f"- 계산된 비율: {ratio:.1f}%")
    
    # 디버그 이미지 생성
    debug_img = img_array.copy()
    
    # 분석된 행 시각화
    for x in range(width):
        color = [0, 255, 0] if brightness[x] >= 50 else [255, 0, 0]
        for y in range(max(0, middle_row-2), min(height, middle_row+3)):
            debug_img[y, x] = color
    
    # 디버그 이미지 저장
    cv2.imwrite(f'debug_{gauge_type}_analyzed.png', cv2.cvtColor(debug_img, cv2.COLOR_RGB2BGR))
    
    return round(ratio, 1)

def get_gauge_values(self):
    hp_image = self.capture_hp_gauge()
    mp_image = self.capture_mp_gauge()
    
    hp_ratio = self.analyze_gauge(hp_image, "hp")
    mp_ratio = self.analyze_gauge(mp_image, "mp")
    
    return hp_ratio, mp_ratio 