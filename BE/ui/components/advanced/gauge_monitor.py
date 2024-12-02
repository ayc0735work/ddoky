import cv2
import numpy as np
import json
import os
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap, QImage
from BE.logic.window_controller import WindowController
from ...data.settings_manager import SettingsManager
import win32gui

class GaugeMonitor(QObject):
    """게이지 모니터링을 위한 클래스"""
    
    gauge_analyzed = Signal(str, float)  # type, ratio
    image_captured = Signal(str, QPixmap)  # type, image
    
    def __init__(self):
        super().__init__()
        self.window_controller = WindowController()
        self.monitoring = False
        self.settings_manager = SettingsManager()
        
        try:
            # 디버그 이미지 저장 경로 설정
            current_dir = os.path.dirname(os.path.abspath(__file__))  # BE/ui/components/advanced
            be_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))  # BE
            
            # 디버그 이미지 저장 경로 설정 (BE/captures/Real_time_Capture)
            self.debug_dir = os.path.join(be_dir, 'BE', 'captures', 'Real_time_Capture')
            
            # 디렉토리 구조 생성
            if not os.path.exists(os.path.join(be_dir, 'BE')):
                os.makedirs(os.path.join(be_dir, 'BE'), exist_ok=True)
            if not os.path.exists(os.path.join(be_dir, 'BE', 'captures')):
                os.makedirs(os.path.join(be_dir, 'BE', 'captures'), exist_ok=True)
            if not os.path.exists(self.debug_dir):
                os.makedirs(self.debug_dir, exist_ok=True)
            
            print(f"GaugeMonitor: 디버그 이미지 저장 경로 = {self.debug_dir}")
            print(f"GaugeMonitor: 디렉토리 존재 여부 = {os.path.exists(self.debug_dir)}")
            print(f"GaugeMonitor: 디렉토리 쓰기 권한 = {os.access(self.debug_dir, os.W_OK)}")
        except Exception as e:
            print(f"GaugeMonitor: 디렉토리 설정 중 오류 발생 - {str(e)}")
            self.debug_dir = None
        
        self._load_capture_areas()
    
    def _load_capture_areas(self):
        """캡처 영역 정보 로드"""
        try:
            settings = self.settings_manager.load_settings()
            if settings and 'gauge_monitor' in settings:
                gauge_settings = settings.get('gauge_monitor', {})
                
                # HP 캡처 영역 로드
                hp_gauge = gauge_settings.get('hp_gauge', {})
                if hp_gauge:
                    self.hp_capture_area = {
                        'coordinates': hp_gauge.get('coordinates', {}),
                        'ratios': hp_gauge.get('ratios', {})
                    }
                    print(f"HP 캡처 영역 로드: {self.hp_capture_area}")
                else:
                    print("HP 캡처 영역 정보가 없습니다.")
                    self.hp_capture_area = {}
                
                # MP 캡처 영역 로드
                mp_gauge = gauge_settings.get('mp_gauge', {})
                if mp_gauge:
                    self.mp_capture_area = {
                        'coordinates': mp_gauge.get('coordinates', {}),
                        'ratios': mp_gauge.get('ratios', {})
                    }
                    print(f"MP 캡처 영역 로드: {self.mp_capture_area}")
                else:
                    print("MP 캡처 영역 정보가 없습니다.")
                    self.mp_capture_area = {}
            else:
                print("게이지 모니터 설정을 찾을 수 없습니다.")
                self.hp_capture_area = {}
                self.mp_capture_area = {}
                
        except Exception as e:
            print(f"캡처 영역 정보 로드 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            self.hp_capture_area = {}
            self.mp_capture_area = {}
    
    def analyze_gauge(self, image, type_):
        """게이지 이미지 분"""
        try:
            if not self.debug_dir or not os.path.exists(self.debug_dir):
                print("GaugeMonitor: 디버그 디렉토리가 존재하지 않습니다")
                return 0
            
            # 디버그용 이미지 복사 및 크기 조정
            debug_image = image.copy()
            display_image = cv2.resize(debug_image, (100, 30))  # UI 표시를 위한 크기 조정
            
            # 이미지 전처리
            image = cv2.GaussianBlur(image, (3, 3), 0)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # 게이지 영역 분석 (위아래 25%만 사용하여 숫자 부분 제외)
            height = hsv.shape[0]
            top_margin = int(height * 0.25)
            bottom_margin = int(height * 0.75)
            
            # 상단과 하단 부분만 선택
            top_part = hsv[:top_margin, :]
            bottom_part = hsv[bottom_margin:, :]
            
            if type_ == 'hp':
                # HP 게이지 색상 범위 (빨간색/주황색)
                def is_red_pixel(pixel):
                    h, s, v = pixel
                    return ((0 <= h <= 15 or 170 <= h <= 180) and  # 색상
                            s >= 150 and                           # 채도
                            v >= 150)                             # 명도
                
                # 각 열에 대해 게이지 픽셀 비율 계산
                gauge_ratios = []
                for x in range(image.shape[1]):
                    top_pixels = top_part[:, x]
                    bottom_pixels = bottom_part[:, x]
                    all_pixels = np.vstack((top_pixels, bottom_pixels))
                    
                    red_pixels = sum(1 for pixel in all_pixels if is_red_pixel(pixel))
                    ratio = red_pixels / len(all_pixels)
                    gauge_ratios.append(ratio)
                
            else:  # mp
                # MP 게이지 색상 범위 (파란색)
                def is_blue_pixel(pixel):
                    h, s, v = pixel
                    return (100 <= h <= 130 and  # 색상
                           s >= 150 and          # 채도
                           v >= 150)             # 명도
                
                # 각 열에 대해 게이지 픽셀 비율 계산
                gauge_ratios = []
                for x in range(image.shape[1]):
                    top_pixels = top_part[:, x]
                    bottom_pixels = bottom_part[:, x]
                    all_pixels = np.vstack((top_pixels, bottom_pixels))
                    
                    blue_pixels = sum(1 for pixel in all_pixels if is_blue_pixel(pixel))
                    ratio = blue_pixels / len(all_pixels)
                    gauge_ratios.append(ratio)
            
            # 게이지 비율을 0-100 사이의 값으로 변환
            gauge_segments = [1 if ratio > 0.2 else 0 for ratio in gauge_ratios]  # 20% 이상이면 게이지로 인정
            
            # 연속된 게이지 영역 찾기
            max_gauge_length = 0
            current_length = 0
            for segment in gauge_segments:
                if segment == 1:
                    current_length += 1
                    max_gauge_length = max(max_gauge_length, current_length)
                else:
                    # 작은 틈(2픽셀 이하)은 무시
                    if current_length > 0 and sum(gauge_segments[current_length:current_length+3]) >= 1:
                        current_length += 1
                    else:
                        current_length = 0
            
            # 최종 게이지 비율 계산
            ratio = (max_gauge_length * 100) // len(gauge_segments)
            
            # 디버깅을 위한 시각화
            segments_str = ''
            for segment in gauge_segments:
                if segment == 1:
                    segments_str += '■'
                else:
                    segments_str += '□'
            
            print(f"{type_} 게이지 구간 분석: {segments_str}")
            print(f"{type_} 게이지: 게이지 길이 = {max_gauge_length}/{len(gauge_segments)}, 비율 = {ratio}%")
            
            # 분석 영역 표시
            cv2.line(display_image, (0, top_margin), (display_image.shape[1], top_margin), (0, 255, 0), 1)
            cv2.line(display_image, (0, bottom_margin), (display_image.shape[1], bottom_margin), (0, 255, 0), 1)
            
            # 디버그 이미지 저장
            debug_path = os.path.join(self.debug_dir, f'debug_{type_}.png')
            try:
                if display_image is not None and display_image.size > 0 and len(display_image.shape) == 3:
                    if not display_image.flags['C_CONTIGUOUS']:
                        display_image = np.ascontiguousarray(display_image)
                    
                    # 방법 1: PIL 사용
                    try:
                        from PIL import Image
                        # BGR에서 RGB로 변환
                        rgb_img = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
                        pil_img = Image.fromarray(rgb_img)
                        pil_img.save(debug_path)
                        success = os.path.exists(debug_path)
                        if success:
                            print(f"GaugeMonitor: 디버그 이미지 저장됨 = {debug_path}")
                            print(f"GaugeMonitor: 파일 크기 = {os.path.getsize(debug_path)} bytes")
                        else:
                            print(f"GaugeMonitor: PIL 저장 실패")
                    except Exception as e:
                        print(f"GaugeMonitor: PIL 저장 실패 - {str(e)}")
                        success = False
                    
                    # 방법 2: OpenCV 시도 (PIL이 실패한 경우)
                    if not success:
                        try:
                            success = cv2.imwrite(str(debug_path), display_image)
                            if success:
                                print(f"GaugeMonitor: OpenCV로 이미지 저장됨 = {debug_path}")
                            else:
                                print("GaugeMonitor: OpenCV 저장 실패")
                        except Exception as e:
                            print(f"GaugeMonitor: OpenCV 저장 실패 - {str(e)}")
                else:
                    print(f"GaugeMonitor: 유효하지 않은 이미지 데이터 - shape: {display_image.shape if display_image is not None else 'None'}")
            except Exception as e:
                print(f"GaugeMonitor: 이미지 저장 실패 - {str(e)}")
                import traceback
                traceback.print_exc()
            
            # UI 업데이트를 위한 이미지 변환 및 시그널 발생
            try:
                if display_image is not None and display_image.size > 0 and len(display_image.shape) == 3:
                    rgb_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    rgb_image = np.ascontiguousarray(rgb_image)
                    qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_image)
                    self.image_captured.emit(type_, pixmap)
                else:
                    print(f"GaugeMonitor: UI 업데이트를 위한 유효하지 않은 이미지 데이터")
            except Exception as e:
                print(f"GaugeMonitor: UI 업데이트 실패 - {str(e)}")
                import traceback
                traceback.print_exc()
            
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
            # 윈도우 정보 가져오기
            hwnd = self.window_controller.target_hwnd
            window_rect = win32gui.GetWindowRect(hwnd)
            client_rect = win32gui.GetClientRect(hwnd)
            
            # 프레임 크기 계산
            frame_x = ((window_rect[2] - window_rect[0]) - client_rect[2]) // 2
            frame_y = (window_rect[3] - window_rect[1]) - client_rect[3] - frame_x
            
            # 클라이언트 영역의 실제 좌표 계산
            client_x = window_rect[0] + frame_x
            client_y = window_rect[1] + frame_y
            
            # 클라이언트 영역의 현재 크기
            client_width = client_rect[2]
            client_height = client_rect[3]
            
            print(f"현재 클라이언트 영역: width={client_width}, height={client_height}")
            
            # HP 게이지 캡처 및 분석
            if self.hp_capture_area and 'ratios' in self.hp_capture_area:
                ratios = self.hp_capture_area['ratios']
                print(f"HP 캡처 시도 - 비율: {ratios}")
                
                # 비율을 현재 클라이언트 크기에 맞춰 픽셀 좌표로 변환
                x = int(ratios['x'] * client_width)
                y = int(ratios['y'] * client_height)
                width = int(ratios['width'] * client_width)
                height = int(ratios['height'] * client_height)
                
                # 절대 좌표 계산
                abs_x = client_x + x
                abs_y = client_y + y
                
                print(f"HP 캡처 시도 - 절대 좌표: x={abs_x}, y={abs_y}, width={width}, height={height}")
                
                hp_image = self.window_controller.capture_screen(
                    abs_x, abs_y, width, height
                )
                
                if hp_image is not None:
                    print(f"HP 이미지 캡처 성공 - 크기: {hp_image.shape}")
                    # 캡처된 이미지 저장 (디버깅용)
                    debug_hp_path = os.path.join(self.debug_dir, 'capture_hp.png')
                    cv2.imwrite(debug_hp_path, hp_image)
                    
                    hp_ratio = self.analyze_gauge(hp_image, 'hp')
                    print(f"HP 게이지 분석 결과: {hp_ratio}%")
                    self.gauge_analyzed.emit('hp', hp_ratio)
                else:
                    print("HP 이미지 캡처 실패")
                    self.gauge_analyzed.emit('hp', 0.0)
            else:
                print("HP 게이지 캡처 영역이 올바르게 설정되지 않았습니다.")
                self.gauge_analyzed.emit('hp', 0.0)
            
            # MP 게이지 캡처 및 분석
            if self.mp_capture_area and 'ratios' in self.mp_capture_area:
                ratios = self.mp_capture_area['ratios']
                print(f"MP 캡처 시도 - 비율: {ratios}")
                
                # 비율을 현재 클라이언트 크기에 맞춰 픽셀 좌표로 변환
                x = int(ratios['x'] * client_width)
                y = int(ratios['y'] * client_height)
                width = int(ratios['width'] * client_width)
                height = int(ratios['height'] * client_height)
                
                # 절대 좌표 계산
                abs_x = client_x + x
                abs_y = client_y + y
                
                print(f"MP 캡처 시도 - 절대 좌표: x={abs_x}, y={abs_y}, width={width}, height={height}")
                
                mp_image = self.window_controller.capture_screen(
                    abs_x, abs_y, width, height
                )
                
                if mp_image is not None:
                    print(f"MP 이미지 캡처 성공 - 크기: {mp_image.shape}")
                    # 캡처된 이미지 저장 (디버깅용)
                    debug_mp_path = os.path.join(self.debug_dir, 'capture_mp.png')
                    cv2.imwrite(debug_mp_path, mp_image)
                    
                    mp_ratio = self.analyze_gauge(mp_image, 'mp')
                    print(f"MP 게이지 분석 결과: {mp_ratio}%")
                    self.gauge_analyzed.emit('mp', mp_ratio)
                else:
                    print("MP 이미지 캡처 실패")
                    self.gauge_analyzed.emit('mp', 0.0)
            else:
                print("MP 게이지 캡처 영역이 올바르게 설정되지 않았습니다.")
                self.gauge_analyzed.emit('mp', 0.0)
                
        except Exception as e:
            print(f"캡처 및 분석 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def set_target_process(self, process_info):
        """대상 프로세스 설정"""
        if process_info:
            self.window_controller.set_target_window(process_info['hwnd'])
            print(f"대상 프로세스 설정됨: {process_info['name']} (hwnd: {process_info['hwnd']})")