from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QLineEdit)
from PySide6.QtCore import Qt, Signal
import win32con
import ctypes
from ctypes import wintypes
import atexit

user32 = ctypes.WinDLL('user32', use_last_error=True)

# Windows hook structures
LRESULT = ctypes.c_long
ULONG_PTR = wintypes.WPARAM

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ('vkCode', wintypes.DWORD),
        ('scanCode', wintypes.DWORD),
        ('flags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ULONG_PTR)
    ]

# Hook type for keyboard events
WH_KEYBOARD_LL = 13
# Event types
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

# Hook callback prototype
HOOKPROC = ctypes.CFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, ctypes.POINTER(KBDLLHOOKSTRUCT))

class KeyInputDialog(QDialog):
    """키 입력을 받는 다이얼로그"""
    
    key_selected = Signal(dict)  # 선택된 키 정보를 전달하는 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("키 입력")
        self.setFixedSize(400, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.last_key_info = None
        self.hook = None
        self.hook_id = None
        self._setup_ui()
        self._setup_keyboard_hook()
        
    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 안내 메시지
        guide_label = QLabel("입력하려는 키를 누르세요")
        guide_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(guide_label)
        
        # 입력된 키 표시
        self.key_display = QLineEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setAlignment(Qt.AlignCenter)
        self.key_display.setPlaceholderText("키를 입력하세요")
        layout.addWidget(self.key_display)
        
        # 키 정보 프레임
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QVBoxLayout()
        
        # 키 정보 레이블들
        self.key_code_label = QLabel("키 코드: ")
        self.scan_code_label = QLabel("스캔 코드 (하드웨어 고유값): ")
        self.virtual_key_label = QLabel("확장 가상 키 (운영체제 레벨의 고유 값): ")
        self.location_label = QLabel("키보드 위치: ")
        self.modifiers_label = QLabel("수정자 키: ")
        
        info_layout.addWidget(self.key_code_label)
        info_layout.addWidget(self.scan_code_label)
        info_layout.addWidget(self.virtual_key_label)
        info_layout.addWidget(self.location_label)
        info_layout.addWidget(self.modifiers_label)
        
        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        save_button = QPushButton("저장")
        cancel_button = QPushButton("취소")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def _setup_keyboard_hook(self):
        """키보드 훅 설정"""
        def hook_callback(nCode, wParam, lParam):
            if nCode >= 0 and (wParam == WM_KEYDOWN or wParam == WM_SYSKEYDOWN):
                kb = lParam.contents
                # 확장 키 플래그 (0x1)
                is_extended = (kb.flags & 0x1) == 0x1
                
                # 가상 키와 스캔 코드
                vk_code = kb.vkCode
                scan_code = kb.scanCode
                
                # 확장 키 처리
                if is_extended:
                    if vk_code == win32con.VK_RETURN:
                        vk_code = 0x10E  # 숫자패드 Enter
                    elif vk_code == win32con.VK_CONTROL:
                        vk_code = win32con.VK_RCONTROL
                    elif vk_code == win32con.VK_MENU:
                        vk_code = win32con.VK_RMENU
                elif not is_extended:
                    if vk_code == win32con.VK_SHIFT:
                        vk_code = win32con.VK_LSHIFT if scan_code == 42 else win32con.VK_RSHIFT
                    elif vk_code == win32con.VK_CONTROL:
                        vk_code = win32con.VK_LCONTROL
                    elif vk_code == win32con.VK_MENU:
                        vk_code = win32con.VK_LMENU
                
                # ESC 키 처리
                if vk_code == win32con.VK_ESCAPE:
                    self.reject()
                    return user32.CallNextHookEx(None, nCode, wParam, ctypes.cast(lParam, ctypes.c_void_p))
                
                # 키 정보 업데이트
                self.last_key_info = {
                    'key': self._get_key_name(vk_code),
                    'scan_code': scan_code,
                    'virtual_key': vk_code,
                    'text': chr(vk_code) if 32 <= vk_code <= 126 else '',
                    'modifiers': self._get_qt_modifiers()
                }
                self._update_key_info()
                
            return user32.CallNextHookEx(None, nCode, wParam, ctypes.cast(lParam, ctypes.c_void_p))
        
        self.hook = HOOKPROC(hook_callback)
        self.hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self.hook,
            None,
            0
        )
        if not self.hook_id:
            raise ctypes.WinError(ctypes.get_last_error())
        
        # 정리 함수 등록
        atexit.register(self._cleanup_hook)
    
    def _cleanup_hook(self):
        """키보드 훅 정리"""
        if self.hook_id:
            user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None
    
    def _get_key_name(self, vk_code):
        """가상 키 코드를 키 이름으로 변환"""
        # 특수 키 이름
        special_keys = {
            # 기능 키
            win32con.VK_F1: 'F1',
            win32con.VK_F2: 'F2',
            win32con.VK_F3: 'F3',
            win32con.VK_F4: 'F4',
            win32con.VK_F5: 'F5',
            win32con.VK_F6: 'F6',
            win32con.VK_F7: 'F7',
            win32con.VK_F8: 'F8',
            win32con.VK_F9: 'F9',
            win32con.VK_F10: 'F10',
            win32con.VK_F11: 'F11',
            win32con.VK_F12: 'F12',
            
            # 제어 키
            win32con.VK_RETURN: '엔터',
            0x10E: '숫자패드 엔터',
            win32con.VK_ESCAPE: 'ESC',
            win32con.VK_TAB: 'Tab',
            win32con.VK_SPACE: 'Space',
            win32con.VK_BACK: 'Backspace',
            win32con.VK_DELETE: 'Delete',
            win32con.VK_INSERT: 'Insert',
            win32con.VK_HOME: 'Home',
            win32con.VK_END: 'End',
            win32con.VK_PRIOR: 'Page Up',
            win32con.VK_NEXT: 'Page Down',
            
            # 화살표 키
            win32con.VK_LEFT: '←',
            win32con.VK_RIGHT: '→',
            win32con.VK_UP: '↑',
            win32con.VK_DOWN: '↓',
            
            # 수정자 키
            win32con.VK_LSHIFT: '왼쪽 쉬프트',
            win32con.VK_RSHIFT: '오른쪽 쉬프트',
            win32con.VK_LCONTROL: '왼쪽 컨트롤',
            win32con.VK_RCONTROL: '오른쪽 컨트롤',
            win32con.VK_LMENU: '왼쪽 알트',
            win32con.VK_RMENU: '오른쪽 알트',
            
            # 숫자패드
            win32con.VK_NUMPAD0: '숫자패드 0',
            win32con.VK_NUMPAD1: '숫자패드 1',
            win32con.VK_NUMPAD2: '숫자패드 2',
            win32con.VK_NUMPAD3: '숫자패드 3',
            win32con.VK_NUMPAD4: '숫자패드 4',
            win32con.VK_NUMPAD5: '숫자패드 5',
            win32con.VK_NUMPAD6: '숫자패드 6',
            win32con.VK_NUMPAD7: '숫자패드 7',
            win32con.VK_NUMPAD8: '숫자패드 8',
            win32con.VK_NUMPAD9: '숫자패드 9',
            win32con.VK_MULTIPLY: '숫자패드 *',
            win32con.VK_ADD: '숫자패드 +',
            win32con.VK_SUBTRACT: '숫자패드 -',
            win32con.VK_DECIMAL: '숫자패드 .',
            win32con.VK_DIVIDE: '숫자패드 /',
        }
        
        if vk_code in special_keys:
            return special_keys[vk_code]
        # 일반 문자키 (A-Z)
        elif 0x41 <= vk_code <= 0x5A:
            return chr(vk_code)
        # 숫자키 (0-9)
        elif 0x30 <= vk_code <= 0x39:
            return chr(vk_code)
        # 기타 키
        else:
            return f'키 코드 {vk_code}'
    
    def _get_qt_modifiers(self):
        """현재 수정자 키 상태 얻기"""
        modifiers = Qt.NoModifier
        if user32.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000:
            modifiers |= Qt.ShiftModifier
        if user32.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000:
            modifiers |= Qt.ControlModifier
        if user32.GetAsyncKeyState(win32con.VK_MENU) & 0x8000:
            modifiers |= Qt.AltModifier
        return modifiers
    
    def _update_key_info(self):
        """키 정보 표시 업데이트"""
        if not self.last_key_info:
            return
            
        # 키 표시 텍스트 설정
        key_text = self._get_key_display_text()
        self.key_display.setText(key_text)
        
        # 키 정보 레이블 업데이트
        self.key_code_label.setText(f"키 코드: {self.last_key_info['key']}")
        self.scan_code_label.setText(f"스캔 코드 (하드웨어 고유값): {self.last_key_info['scan_code']}")
        self.virtual_key_label.setText(f"확장 가상 키 (운영체제 레벨의 고유 값): {self.last_key_info['virtual_key']}")
        
        # 위치 정보 (스캔 코드 (하드웨어 고유값) 기반으로 판단)
        location = self._get_key_location()
        self.location_label.setText(f"위치: {location}")
        
        # 수정자 키 정보
        modifiers = self._get_modifier_text()
        self.modifiers_label.setText(f"수정자 키: {modifiers}")
        
    def _get_key_display_text(self):
        """키 표시 텍스트 생성"""
        key = self.last_key_info['key']
        text = self.last_key_info['text']
        location = self._get_key_location()
        
        if text:
            return f"{text} ({location})"
        return f"{key} ({location})"
        
    def _get_key_location(self):
        """키의 위치 정보 반환"""
        scan_code = self.last_key_info['scan_code']
        
        # 예시적인 위치 판단 (실제 구현 시 더 자세한 매핑 필요)
        if scan_code in [42, 29, 56]:  # 왼쪽 Shift, Ctrl, Alt
            return "왼쪽"
        elif scan_code in [54, 285, 312]:  # 오른쪽 Shift, Ctrl, Alt
            return "오른쪽"
        elif 71 <= scan_code <= 83:  # 숫자패드 영역
            return "숫자패드"
        return "메인"
        
    def _get_modifier_text(self):
        """수정자 키 텍스트 생성"""
        modifiers = self.last_key_info['modifiers']
        mod_texts = []
        
        if modifiers & Qt.ShiftModifier:
            mod_texts.append("Shift")
        if modifiers & Qt.ControlModifier:
            mod_texts.append("Ctrl")
        if modifiers & Qt.AltModifier:
            mod_texts.append("Alt")
            
        return " + ".join(mod_texts) if mod_texts else "없음"
        
    def accept(self):
        """저장 버튼 클릭 시 처리"""
        if self.last_key_info:
            self.key_selected.emit(self.last_key_info)
        super().accept()
        
    def closeEvent(self, event):
        """다이얼로그가 닫힐 때 정리"""
        self._cleanup_hook()
        super().closeEvent(event)
