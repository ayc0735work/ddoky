import cv2
import numpy as np
import json
import os
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap, QImage
from .window_controller import WindowController
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
        
        # 기본 게이지 비율 설정
        self.hp_ratio = {
            'x': 0.7481770833333333,  # 창 너비의 약 75% 위치
            'y': 0.8426323319027181,  # 창 높이의 약 84% 위치
            'width': 0.0984375,       # 창 너비의 약 10%
            'height': 0.020982355746304245  # 창 높이의 약 2%
        }
        
        self.mp_ratio = {
            'x': 0.7481770833333333,  # 창 너비의 약 75% 위치
            'y': 0.8702908917501192,  # 창 높이의 약 87% 위치
            'width': 0.09817708333333333,  # 창 너비의 약 10%
            'height': 0.0195517405817835   # 창 높이의 약 2%
        }
        
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
    
    def _get_client_rect(self, hwnd):
        """클라이언트 영역의 실제 화면 좌표를 계산"""
        try:
            # 윈도우 전체 영역
            window_rect = win32gui.GetWindowRect(hwnd)
            # 클라이언트 영역
            client_rect = win32gui.GetClientRect(hwnd)
            
            # 클라이언트 영역의 좌상단 스크린 좌표 얻기
            point = win32gui.ClientToScreen(hwnd, (0, 0))
            
            # 실제 클라이언트 영역의 화면 좌표와 크기
            return {
                'x': point[0],
                'y': point[1],
                'width': client_rect[2],
                'height': client_rect[3]
            }
        except Exception as e:
            print(f"클라이언트 영역 계산 중 오류: {str(e)}")
            return None
    
    def capture_and_analyze(self):
        """게이지 캡역을 캡처하고 분석합니다."""
        try:
            print("GaugeMonitor: 캡처 및 분석 시작")
            
            # 윈도우 정보 가져오기
            print("GaugeMonitor: 윈도우 정보 가져오기 시도")
            window_info = self.window_controller.get_window_info()
            if not window_info:
                print("GaugeMonitor: 윈도우 정보를 가져올 수 없음")
                return
                
            print(f"WindowController: 윈도우 정보 = {window_info}")
            
            client_area = window_info['client']
            print(f"GaugeMonitor: 현재 클라이언트 영역 = {client_area}")
            
            # HP 게이지 캡처
            print(f"GaugeMonitor: HP 캡처 시도 - 비율 = {self.hp_ratio}")
            
            hp_x = int(client_area['width'] * self.hp_ratio['x'])
            hp_y = int(client_area['height'] * self.hp_ratio['y'])
            hp_width = int(client_area['width'] * self.hp_ratio['width'])
            hp_height = int(client_area['height'] * self.hp_ratio['height'])
            
            print("GaugeMonitor: HP 좌표 계산 과정:")
            print(f"  - 원본 비율: x={self.hp_ratio['x']:.4f}, y={self.hp_ratio['y']:.4f}")
            print(f"  - 클라이언트 크기: width={client_area['width']}, height={client_area['height']}")
            print(f"  - 계산된 픽셀 좌표: x={hp_x}, y={hp_y}")
            print(f"  - 계산된 크기: width={hp_width}, height={hp_height}")
            
            print("GaugeMonitor: HP 캡처 영역:")
            print(f"  - 상대 좌표: x={hp_x}, y={hp_y}")
            print(f"  - 크기: {hp_width}x{hp_height}")
            
            hp_image = self.window_controller.capture_region(hp_x, hp_y, hp_width, hp_height, gauge_type='hp')
            if hp_image is None:
                print("GaugeMonitor: HP 이미지 캡처 실패")
                self.gauge_analyzed.emit('hp', 0.0)
                return
                
            hp_ratio = self.analyze_gauge(hp_image, 'hp')
            print(f"GaugeMonitor: HP 게이지 분석 결과 = {hp_ratio}%")
            self.gauge_analyzed.emit('hp', hp_ratio)
            
            # MP 게이지 캡처
            print(f"GaugeMonitor: MP 캡처 시도 - 비율 = {self.mp_ratio}")
            
            mp_x = int(client_area['width'] * self.mp_ratio['x'])
            mp_y = int(client_area['height'] * self.mp_ratio['y'])
            mp_width = int(client_area['width'] * self.mp_ratio['width'])
            mp_height = int(client_area['height'] * self.mp_ratio['height'])
            
            print("GaugeMonitor: MP 좌표 계산 과정:")
            print(f"  - 원본 비율: x={self.mp_ratio['x']:.4f}, y={self.mp_ratio['y']:.4f}")
            print(f"  - 클라이언트 크기: width={client_area['width']}, height={client_area['height']}")
            print(f"  - 계산된 픽셀 좌표: x={mp_x}, y={mp_y}")
            print(f"  - 계산된 크기: width={mp_width}, height={mp_height}")
            
            print("GaugeMonitor: MP 캡처 영역:")
            print(f"  - 상대 좌표: x={mp_x}, y={mp_y}")
            print(f"  - 크기: {mp_width}x{mp_height}")
            
            mp_image = self.window_controller.capture_region(mp_x, mp_y, mp_width, mp_height, gauge_type='mp')
            if mp_image is None:
                print("GaugeMonitor: MP 이미지 캡처 실패")
                self.gauge_analyzed.emit('mp', 0.0)
                return
                
            mp_ratio = self.analyze_gauge(mp_image, 'mp')
            print(f"GaugeMonitor: MP 게이지 분석 결과 = {mp_ratio}%")
            self.gauge_analyzed.emit('mp', mp_ratio)
            
        except Exception as e:
            print(f"GaugeMonitor: 캡처 및 분석 중 오류 발생 - {e}")
            import traceback
            traceback.print_exc()
    
    def set_target_process(self, process_info):
        """대상 프로세스를 설정합니다."""
        try:
            print(f"GaugeMonitor: 대상 프로세스 정 시도 - {process_info}")
            if not process_info or 'hwnd' not in process_info:
                print("GaugeMonitor: 유효하지 않은 프로세스 정보")
                return False
                
            # 윈도우 컨트롤러에 대상 윈도우 설정
            if self.window_controller.set_target_window(process_info['hwnd']):
                print(f"GaugeMonitor: 대상 프로세스 설정됨 - {process_info['name']} (hwnd: {process_info['hwnd']})")
                return True
            else:
                print("GaugeMonitor: 대상 프로세스 설정 실패")
                return False
                
        except Exception as e:
            print(f"GaugeMonitor: 대상 프로세스 설정 중 오류 발생 - {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_gauge_ratio(self, gauge_type, x, y, width, height):
        """게이지 영역의 비율을 설정합니다."""
        ratio = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }
        
        if gauge_type == 'hp':
            self.hp_ratio = ratio
        elif gauge_type == 'mp':
            self.mp_ratio = ratio
            
        print(f"게이지 비율 설정됨 - {gauge_type}: {ratio}")