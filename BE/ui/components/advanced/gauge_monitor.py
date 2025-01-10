import cv2
import numpy as np
import json
import os
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap, QImage, Qt
from .window_controller import WindowController
from ...data.settings_manager import SettingsManager
import win32gui
from datetime import datetime

class GaugeMonitor(QObject):
    """게이지 모니터링을 위한 클래스"""
    
    gauge_analyzed = Signal(str, float)  # type, ratio
    image_captured = Signal(str, QPixmap)  # type, image
    
    def __init__(self, advanced_widget=None):
        """초기화"""
        super().__init__()
        self.window_controller = WindowController()
        self.monitoring = False
        self.settings_manager = SettingsManager()
        self.advanced_widget = advanced_widget
        
        # 기본 게이지 비율 설정
        self.hp_ratio = {
            'x': 0.7481770833333333,  # 창 너비의 약 75% 위치
            'y': 0.8426323319027181,  # 창 높이의 약 84% 위치
            'width': 0.1,             # 창 너비의 10%
            'height': 0.020982355746304245  # 창 높이의 약 2%
        }
        
        self.mp_ratio = {
            'x': 0.7481770833333333,  # 창 너비의 약 75% 위치
            'y': 0.8702908917501192,  # 창 높이의 약 87% 위치
            'width': 0.1,             # 창 너비의 10%
            'height': 0.0195517405817835   # 창 높이의 약 2%
        }
        
        try:
            # 디버그 이미지 저장 경로 설정
            current_dir = os.path.dirname(os.path.abspath(__file__))  # BE/ui/components/advanced
            be_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))  # BE
            
            # 디버그 이미지 저장 경로 설정 (BE/BE/captures/Real_time_Capture)
            self.debug_dir = os.path.join(be_dir, 'BE', 'captures', 'Real_time_Capture')
            
            # 디렉토리 구조 생성
            os.makedirs(self.debug_dir, exist_ok=True)
            
            # 디버그 출력 추가
            print(f"GaugeMonitor: 현재 디렉토리 = {current_dir}")
            print(f"GaugeMonitor: BE 디렉토리 = {be_dir}")
            print(f"GaugeMonitor: 디버그 이미지 저장 경로 = {self.debug_dir}")
            print(f"GaugeMonitor: 디렉토리 존재 여부 = {os.path.exists(self.debug_dir)}")
            print(f"GaugeMonitor: 디렉토리 쓰기 권한 = {os.access(self.debug_dir, os.W_OK)}")
            print(f"GaugeMonitor: 디렉토리 절대 경로 = {os.path.abspath(self.debug_dir)}")
        except Exception as e:
            print(f"GaugeMonitor: 디렉토리 설정 중 오류 발생 - {str(e)}")
            import traceback
            traceback.print_exc()
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
                    # 비율 업데이트
                    self.hp_ratio = self.hp_capture_area['ratios']
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
                    # 비율 업데이트
                    self.mp_ratio = self.mp_capture_area['ratios']
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
    
    def _process_image(self, image, type_):
        """이미지 처리 및 분석"""
        try:
            if image is None:
                print(f"{type_} 이미지가 None입니다.")
                return
            
            # 이미지를 RGB로 변환
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 이미지 저장
            save_dir = "BE/captures/Real_time_Capture"
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f"capture_{type_}.png")
            cv2.imwrite(save_path, image)  # 원본 BGR 이미지 저장
            
            # QPixmap 생성
            height, width = rgb_image.shape[:2]
            bytes_per_line = 3 * width
            rgb_image = np.ascontiguousarray(rgb_image)
            q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # 이미지 크기 조정
            max_size = 200
            if width > max_size or height > max_size:
                pixmap = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 게이지 비율 계산 (RGB 이미지 사용)
            ratio = self._analyze_gauge(rgb_image, type_)
            
            # UI 업데이트
            if type_ == 'hp':
                if self.advanced_widget:
                    self.advanced_widget._update_capture_image('hp', pixmap)
                    self.advanced_widget._update_gauge_info('hp', ratio)
            else:  # mp
                if self.advanced_widget:
                    self.advanced_widget._update_capture_image('mp', pixmap)
                    self.advanced_widget._update_gauge_info('mp', ratio)
            
        except Exception as e:
            print(f"이미지 처리 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _analyze_gauge(self, image, gauge_type):
        """게이지 이미지를 분석하여 현재 비율을 반환합니다."""
        try:
            if image is None:
                print(f"{gauge_type} 게이지 분석 실패: 이미지가 없음")
                return 0.0
                
            # 이미지 크기 확인
            height, width = image.shape[:2]
            if width == 0 or height == 0:
                print(f"{gauge_type} 게이지 분석 실패: 유효하지 않은 이미지 크기 ({width}x{height})")
                return 0.0

            print(f"\n{gauge_type} 게이지 분석 시작:")
            print(f"이미지 크기: {width}x{height}")

            # 이미지 중앙 행의 RGB 값 출력 (디버그용)
            middle_row = height // 2
            middle_pixels = image[middle_row]
            print(f"중앙 행 ({middle_row}) RGB 값 샘플:")
            for i in range(0, min(width, 5)):  # 처음 5개 픽셀만 출력
                r, g, b = middle_pixels[i]
                print(f"픽셀 {i}: R={r}, G={g}, B={b}")

            # RGB 이미지를 분석
            mask = np.zeros((height, width), dtype=np.uint8)
            
            if gauge_type == 'hp':
                # HP 게이지 색상 범위 (붉은 계열)
                # RGB HEX: 5f1300, 8b1f00, b72f00, e74300, ff4f00
                hp_colors = [
                    (0x5f, 0x13, 0x00),  # 5f1300 (RGB)
                    (0x8b, 0x1f, 0x00),  # 8b1f00
                    (0xb7, 0x2f, 0x00),  # b72f00
                    (0xe7, 0x43, 0x00),  # e74300
                    (0xff, 0x4f, 0x00),  # ff4f00
                ]
                
                for r, g, b in hp_colors:
                    # RGB 이미지의 각 채널과 비교 (허용 오차 범위 축소)
                    color_mask = (
                        (image[..., 0] >= max(0, r - 20)) & (image[..., 0] <= min(255, r + 20)) &  # Red
                        (image[..., 1] >= max(0, g - 20)) & (image[..., 1] <= min(255, g + 20)) &  # Green
                        (image[..., 2] >= max(0, b - 20)) & (image[..., 2] <= min(255, b + 20))    # Blue
                    )
                    mask = mask | color_mask
                    
                    # 디버그: 각 색상에 대한 매칭 픽셀 수 출력
                    matching_pixels = np.sum(color_mask)
                    print(f"HP 색상 (R={r:02x}, G={g:02x}, B={b:02x}) 매칭 픽셀: {matching_pixels}")
            else:
                # MP 게이지 색상 범위 (파란 계열)
                # RGB HEX: 17235f, 33437f, 53679b, 7b93bb, abbfd7
                mp_colors = [
                    (0x17, 0x23, 0x5f),  # 17235f (RGB)
                    (0x33, 0x43, 0x7f),  # 33437f
                    (0x53, 0x67, 0x9b),  # 53679b
                    (0x7b, 0x93, 0xbb),  # 7b93bb
                    (0xab, 0xbf, 0xd7),  # abbfd7
                ]
                
                for r, g, b in mp_colors:
                    # RGB 이미지의 각 채널과 비교 (허용 오차 범위 축소)
                    color_mask = (
                        (image[..., 0] >= max(0, r - 20)) & (image[..., 0] <= min(255, r + 20)) &  # Red
                        (image[..., 1] >= max(0, g - 20)) & (image[..., 1] <= min(255, g + 20)) &  # Green
                        (image[..., 2] >= max(0, b - 20)) & (image[..., 2] <= min(255, b + 20))    # Blue
                    )
                    mask = mask | color_mask
                    
                    # 디버그: 각 색상에 대한 매칭 픽셀 수 출력
                    matching_pixels = np.sum(color_mask)
                    print(f"MP 색상 (R={r:02x}, G={g:02x}, B={b:02x}) 매칭 픽셀: {matching_pixels}")

            # 각 열에서 색상이 있는 픽셀 수 계산
            col_sums = np.sum(mask, axis=0)
            
            # 임계값 설정 (높이의 5%로 낮춤)
            threshold = height * 0.05
            
            print(f"\n열별 색상 픽셀 수:")
            for i in range(0, width, 10):  # 10픽셀 간격으로 출력
                print(f"열 {i}: {col_sums[i]} (threshold: {threshold:.2f})")
            
            # 연속된 게이지 세그먼트 찾기
            gauge_segments = []
            start_col = -1
            for i in range(width):
                if col_sums[i] > threshold:
                    if start_col == -1:
                        start_col = i
                elif start_col != -1:
                    # 최소 5픽셀 이상의 연속된 영역만 고려
                    if i - start_col >= 5:
                        gauge_segments.append((start_col, i-1))
                    start_col = -1
            
            # 마지막 세그먼트 처리
            if start_col != -1 and width - start_col >= 5:
                gauge_segments.append((start_col, width-1))
            
            # 게이지 세그먼트 분석
            if not gauge_segments:
                ratio = 0.0
                first_gauge_col = -1
                last_gauge_col = -1
            else:
                # 가장 긴 세그먼트 찾기
                longest_segment = max(gauge_segments, key=lambda x: x[1] - x[0])
                
                # 게이지 시작과 끝 지점 설정
                first_gauge_col = min(seg[0] for seg in gauge_segments)
                last_gauge_col = max(seg[1] for seg in gauge_segments)
                
                # 전체 게이지 영역
                total_width = last_gauge_col - first_gauge_col + 1
                
                # 실제 채워진 픽셀 수 계산
                filled_pixels = 0
                total_pixels = 0
                
                for i in range(first_gauge_col, last_gauge_col + 1):
                    # 각 열의 최대 가능한 픽셀 수
                    total_pixels += height
                    # 실제 채워진 픽셀 수
                    if col_sums[i] > threshold:
                        filled_pixels += col_sums[i]
                
                # 비율 계산 (실제 채워진 픽셀 / 전체 가능한 픽셀)
                ratio = (filled_pixels / total_pixels) * 100 if total_pixels > 0 else 0.0
                
                # 100%를 넘지 않도록 제한
                ratio = min(ratio, 100.0)

            print(f"\n분석 결과:")
            print(f"- 감지된 게이지 세그먼트: {gauge_segments}")
            print(f"- 첫 번째 게이지 열: {first_gauge_col}")
            print(f"- 마지막 게이지 열: {last_gauge_col}")
            if len(gauge_segments) > 0:
                print(f"- 전체 픽셀 수: {total_pixels}")
                print(f"- 채워진 픽셀 수: {filled_pixels}")
            print(f"- 계산된 비율: {ratio:.1f}%")
            
            # 디버그용 이미지 저장
            debug_image = image.copy()
            
            # 분석된 영역 표시
            if last_gauge_col != -1:
                cv2.line(debug_image, (last_gauge_col, 0), (last_gauge_col, height), (0, 0, 255), 1)
            
            # threshold 선 표시
            for i in range(width):
                if col_sums[i] > threshold:
                    cv2.line(debug_image, (i, height-2), (i, height-1), (0, 255, 0), 1)
            
            debug_path = os.path.join(self.debug_dir, f'analyzed_{gauge_type}.png')
            cv2.imwrite(debug_path, debug_image)

            return ratio

        except Exception as e:
            print(f"게이지 분석 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0.0
    
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
            
            # 창이 최소화되었거나 유효하지 않은 상태인지 확인
            if (client_area['width'] <= 0 or client_area['height'] <= 0 or
                client_area['x'] < -10000 or client_area['y'] < -10000):
                print("GaugeMonitor: 창이 최소화되었거나 화면을 벗어남")
                if self.advanced_widget:
                    self.advanced_widget._update_gauge_info('hp', 0.0)
                    self.advanced_widget._update_gauge_info('mp', 0.0)
                return
            
            # HP 게이지 캡처
            print(f"GaugeMonitor: HP 캡처 시도 - 비율 = {self.hp_ratio}")
            
            # 실제 클라이언트 영역 내에서의 상대 좌표 계산
            hp_x = int(client_area['width'] * self.hp_ratio['x'])
            hp_y = int(client_area['height'] * self.hp_ratio['y'])
            hp_width = int(client_area['width'] * self.hp_ratio['width'])
            hp_height = int(client_area['height'] * self.hp_ratio['height'])
            
            # 캡처 영역이 유효한지 확인
            if hp_width <= 0 or hp_height <= 0:
                print("GaugeMonitor: 유효하지 않은 HP 캡처 영역")
                if self.advanced_widget:
                    self.advanced_widget._update_gauge_info('hp', 0.0)
                return
            
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
                if self.advanced_widget:
                    self.advanced_widget._update_gauge_info('hp', 0.0)
                return
                
            hp_ratio = self._analyze_gauge(hp_image, 'hp')
            print(f"GaugeMonitor: HP 게이지 분석 결과 = {hp_ratio}%")
            
            # UI 업데이트
            if self.advanced_widget:
                # QPixmap 생성
                height, width = hp_image.shape[:2]
                bytes_per_line = 3 * width
                rgb_image = cv2.cvtColor(hp_image, cv2.COLOR_BGR2RGB)
                rgb_image = np.ascontiguousarray(rgb_image)
                q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)
                
                # 이미지 크기 조정
                max_size = 200
                if width > max_size or height > max_size:
                    pixmap = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                self.advanced_widget._update_capture_image('hp', pixmap)
                self.advanced_widget._update_gauge_info('hp', hp_ratio)
            
            # MP 게이지 캡처
            print(f"GaugeMonitor: MP 캡처 시도 - 비율 = {self.mp_ratio}")
            
            # 실제 클라이언트 영역 내에서의 상대 좌표 계산
            mp_x = int(client_area['width'] * self.mp_ratio['x'])
            mp_y = int(client_area['height'] * self.mp_ratio['y'])
            mp_width = int(client_area['width'] * self.mp_ratio['width'])
            mp_height = int(client_area['height'] * self.mp_ratio['height'])
            
            # 캡처 영역이 유효한지 확인
            if mp_width <= 0 or mp_height <= 0:
                print("GaugeMonitor: 유효하지 않은 MP 캡처 영역")
                if self.advanced_widget:
                    self.advanced_widget._update_gauge_info('mp', 0.0)
                return
            
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
                if self.advanced_widget:
                    self.advanced_widget._update_gauge_info('mp', 0.0)
                return
                
            mp_ratio = self._analyze_gauge(mp_image, 'mp')
            print(f"GaugeMonitor: MP 게이지 분석 결과 = {mp_ratio}%")
            
            # UI 업데이트
            if self.advanced_widget:
                # QPixmap 생성
                height, width = mp_image.shape[:2]
                bytes_per_line = 3 * width
                rgb_image = cv2.cvtColor(mp_image, cv2.COLOR_BGR2RGB)
                rgb_image = np.ascontiguousarray(rgb_image)
                q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)
                
                # 이미지 크기 조정
                max_size = 200
                if width > max_size or height > max_size:
                    pixmap = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                self.advanced_widget._update_capture_image('mp', pixmap)
                self.advanced_widget._update_gauge_info('mp', mp_ratio)
            
        except Exception as e:
            print(f"게이지 캡처 및 분석 중 오류: {str(e)}")
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