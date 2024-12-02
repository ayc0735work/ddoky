import cv2
import numpy as np
import json
import os
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap, QImage
from BE.logic.window_controller import WindowController
from ...data.settings_manager import SettingsManager

class GaugeMonitor(QObject):
    """게이지 모니터링을 위한 클래스"""
    
    gauge_analyzed = Signal(str, float)  # type, ratio
    image_captured = Signal(str, QPixmap)  # type, image
    
    def __init__(self):
        super().__init__()
        self.window_controller = WindowController()
        self.monitoring = False
        self.settings_manager = SettingsManager()
        self._load_capture_areas()
    
    def _load_capture_areas(self):
        """캡처 영역 정보 로드"""
        try:
            settings = self.settings_manager.load_settings()
            if settings:
                gauge_settings = settings.get('gauge_monitor', {})
                
                # HP 캡처 영역 로드
                hp_gauge = gauge_settings.get('hp_gauge', {})
                self.hp_capture_area = hp_gauge.get('coordinates', {})
                print(f"HP 캡처 영역 로드: {self.hp_capture_area}")  # 디버그 출력
                
                # MP 캡처 영역 로드
                mp_gauge = gauge_settings.get('mp_gauge', {})
                self.mp_capture_area = mp_gauge.get('coordinates', {})
                print(f"MP 캡처 영역 로드: {self.mp_capture_area}")  # 디버그 출력
            else:
                print("설정을 불러올 수 없습니다.")
                self.hp_capture_area = {}
                self.mp_capture_area = {}
                
        except Exception as e:
            print(f"캡처 영역 정보 로드 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            # 기본값 설정
            self.hp_capture_area = {}
            self.mp_capture_area = {}
    
    def analyze_gauge(self, image, type_):
        """게이지 이미지 분석"""
        try:
            # 이미지 전처리
            image = cv2.GaussianBlur(image, (5, 5), 0)  # 노이즈 제거
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            if type_ == 'hp':
                # 빨간색 게이지 검출 (HSV 색공간 사용)
                # 주황-빨강 계열 색상 범위
                lower_red1 = np.array([0, 120, 100])
                upper_red1 = np.array([20, 255, 255])
                # 진한 빨강 색상 범위
                lower_red2 = np.array([160, 120, 100])
                upper_red2 = np.array([180, 255, 255])
                
                # 빨간색 마스크 생성
                mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                mask = cv2.bitwise_or(mask1, mask2)
                
            else:  # mp
                # 파란색 게이지 검출 (HSV 색공간 사용)
                # 파란색 범위 조정
                lower_blue = np.array([90, 120, 100])
                upper_blue = np.array([130, 255, 255])
                mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # 노이즈 제거
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # 게이지 영역만 분석 (위아래 여백 제거)
            height = mask.shape[0]
            margin = int(height * 0.2)  # 위아래 20% 여백
            roi = mask[margin:-margin, :]  # 중앙 60% 영역만 사용
            
            # 게이지 비율 계산
            gauge_pixels = np.sum(roi > 0)
            total_pixels = roi.shape[1] * roi.shape[0]  # ROI 영역의 전체 픽셀 수
            
            if total_pixels == 0:
                print(f"{type_} 게이지: 분석할 픽셀이 없습니다")
                return 0
                
            ratio = min((gauge_pixels / total_pixels) * 100, 100)  # 100%를 넘지 않도록 제한
            
            # 디버깅을 위한 이미지 저장
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            
            # 원본, 마스크, ROI 이미지 저장
            cv2.imwrite(os.path.join(debug_dir, f'gauge_{type_}_original.png'), image)
            cv2.imwrite(os.path.join(debug_dir, f'gauge_{type_}_mask.png'), mask)
            cv2.imwrite(os.path.join(debug_dir, f'gauge_{type_}_roi.png'), roi)
            
            print(f"{type_} 게이지: 픽셀 수 = {gauge_pixels}, 전체 픽셀 = {total_pixels}, 비율 = {ratio}%")
            
            return ratio
            
        except Exception as e:
            print(f"{type_} 게이지 분석 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0
    
    def capture_and_analyze(self):
        """게이지 캡처 및 분석"""
        if not self.window_controller.is_target_window_active():
            print("대상 윈도우가 활성화되지 않음")
            return
            
        try:
            settings = self.settings_manager.load_settings()
            if not settings:
                print("설정을 불러올 수 없습니다.")
                return

            # HP 게이지 캡처 및 분석
            if self.hp_capture_area and all(k in self.hp_capture_area for k in ['x', 'y', 'width', 'height']):
                hp_image = self.window_controller.capture_screen(
                    self.hp_capture_area['x'],
                    self.hp_capture_area['y'],
                    self.hp_capture_area['width'],
                    self.hp_capture_area['height']
                )
                if hp_image is not None:
                    hp_ratio = self.analyze_gauge(hp_image, 'hp')
                    print(f"HP 게이지 분석 결과: {hp_ratio}%")  # 디버그 출력
                    self.gauge_analyzed.emit('hp', hp_ratio)
                    
                    # HP 게이지 수치 저장
                    if 'gauge_monitor' not in settings:
                        settings['gauge_monitor'] = {}
                    if 'hp_gauge' not in settings['gauge_monitor']:
                        settings['gauge_monitor']['hp_gauge'] = {}
                    settings['gauge_monitor']['hp_gauge']['value'] = hp_ratio
                    
                    try:
                        # OpenCV 이미지를 QImage로 변환
                        hp_image_rgb = cv2.cvtColor(hp_image, cv2.COLOR_BGR2RGB)
                        h, w, ch = hp_image_rgb.shape
                        bytes_per_line = ch * w
                        # numpy 배열을 연속적인 메모리로 만듦
                        hp_image_rgb = np.ascontiguousarray(hp_image_rgb)
                        qimage = QImage(hp_image_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimage)
                        self.image_captured.emit('hp', pixmap)
                    except Exception as e:
                        print(f"HP 이미지 변환 중 오류 발생: {str(e)}")
                else:
                    print("HP 이미지 캡처 실패")
            else:
                print("HP 게이지 캡처 영역이 설정되지 않았습니다.")
                self.gauge_analyzed.emit('hp', 0.0)

            # MP 게이지 캡처 및 분석
            if self.mp_capture_area and all(k in self.mp_capture_area for k in ['x', 'y', 'width', 'height']):
                mp_image = self.window_controller.capture_screen(
                    self.mp_capture_area['x'],
                    self.mp_capture_area['y'],
                    self.mp_capture_area['width'],
                    self.mp_capture_area['height']
                )
                if mp_image is not None:
                    mp_ratio = self.analyze_gauge(mp_image, 'mp')
                    print(f"MP 게이지 분석 결과: {mp_ratio}%")  # 디버그 출력
                    self.gauge_analyzed.emit('mp', mp_ratio)
                    
                    # MP 게이지 수치 저장
                    if 'gauge_monitor' not in settings:
                        settings['gauge_monitor'] = {}
                    if 'mp_gauge' not in settings['gauge_monitor']:
                        settings['gauge_monitor']['mp_gauge'] = {}
                    settings['gauge_monitor']['mp_gauge']['value'] = mp_ratio
                    
                    try:
                        # OpenCV 이미지를 QImage로 변환
                        mp_image_rgb = cv2.cvtColor(mp_image, cv2.COLOR_BGR2RGB)
                        h, w, ch = mp_image_rgb.shape
                        bytes_per_line = ch * w
                        # numpy 배열을 연속적인 메모리로 만듦
                        mp_image_rgb = np.ascontiguousarray(mp_image_rgb)
                        qimage = QImage(mp_image_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimage)
                        self.image_captured.emit('mp', pixmap)
                    except Exception as e:
                        print(f"MP 이미지 변환 중 오류 발생: {str(e)}")
                else:
                    print("MP 이미지 캡처 실패")
            else:
                print("MP 게이지 캡처 영역이 설정되지 않았습니다.")
                self.gauge_analyzed.emit('mp', 0.0)

            # 변경된 설정 저장
            self.settings_manager.save_settings(settings)

        except Exception as e:
            print(f"게이지 캡처 및 분석 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            self.gauge_analyzed.emit('hp', 0.0)
            self.gauge_analyzed.emit('mp', 0.0)
    
    def set_target_process(self, process_info):
        """대상 프로세스 설정"""
        if process_info:
            self.window_controller.set_target_window(process_info['hwnd'])
            print(f"대상 프로세스 설정됨: {process_info['name']} (hwnd: {process_info['hwnd']})")