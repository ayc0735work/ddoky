import win32con
import ctypes
from ctypes import wintypes
from PySide6.QtCore import Qt, QObject, Signal

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

user32 = ctypes.WinDLL('user32', use_last_error=True)

def get_key_name(vk_code):
    """가상 키 코드를 키 이름으로 변환"""
    # 특수 키 이름
    special_keys = {
        # 기능 키 (F1-F12: 0x70-0x7B)
        0x70: 'F1', 0x71: 'F2', 0x72: 'F3', 0x73: 'F4',
        0x74: 'F5', 0x75: 'F6', 0x76: 'F7', 0x77: 'F8',
        0x78: 'F9', 0x79: 'F10', 0x7A: 'F11', 0x7B: 'F12',
        
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
        win32con.VK_LEFT: '방향키 왼쪽 ←',
        win32con.VK_RIGHT: '방향키 오른쪽 →',
        win32con.VK_UP: '방향키 위쪽 ↑',
        win32con.VK_DOWN: '방향키 아래쪽 ↓',
        
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

def get_qt_modifiers():
    """현재 수정자 키 상태 얻기"""
    modifiers = Qt.NoModifier
    if user32.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000:
        modifiers |= Qt.ShiftModifier
    if user32.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000:
        modifiers |= Qt.ControlModifier
    if user32.GetAsyncKeyState(win32con.VK_MENU) & 0x8000:
        modifiers |= Qt.AltModifier
    return modifiers

def get_key_location(scan_code):
    """키의 위치 정보 반환"""
    # 예시적인 위치 판단 (실제 구현 시 더 자세한 매핑 필요)
    if scan_code in [42, 29, 56]:  # 왼쪽 Shift, Ctrl, Alt
        return "왼쪽"
    elif scan_code in [54, 285, 312]:  # 오른쪽 Shift, Ctrl, Alt
        return "오른쪽"
    elif 71 <= scan_code <= 83:  # 숫자패드 영역
        return "숫자패드"
    return "메인"

def get_key_display_text(key_info):
    """키 표시 텍스트 생성"""
    key = key_info['key_code']  # 'key'에서 'key_code'로 변경
    location = get_key_location(key_info['scan_code'])  # scan_code를 직접 전달
    
    if key:
        return f"{key} ({location})"
    return f"알 수 없는 키 ({location})"

def get_modifier_text(modifiers):
    """수정자 키 텍스트 생성"""
    mod_texts = []
    
    # modifiers가 정수인 경우 Qt.KeyboardModifier로 변환
    if isinstance(modifiers, int):
        modifiers = Qt.KeyboardModifier(modifiers)
    
    if modifiers & Qt.ShiftModifier:
        mod_texts.append("Shift")
    if modifiers & Qt.ControlModifier:
        mod_texts.append("Ctrl")
    if modifiers & Qt.AltModifier:
        mod_texts.append("Alt")
        
    return " + ".join(mod_texts) if mod_texts else "없음"

def format_key_info(key_info):
    """키 정보를 일관된 형식의 문자열로 변환"""
    return (
        f"키: {key_info['key_code']}, "
        f"스캔 코드 (하드웨어 고유값): {key_info['scan_code']}, "
        f"확장 가상 키 (운영체제 레벨의 고유 값): {key_info['virtual_key']}, "
        f"키보드 위치: {get_key_location(key_info['scan_code'])}, "
        f"수정자 키: {get_modifier_text(key_info['modifiers'])}"
    )

class KeyboardHook(QObject):
    """키보드 훅을 관리하는 클래스"""
    
    key_pressed = Signal(dict)  # 키가 눌렸을 때 발생하는 시그널
    
    def __init__(self):
        super().__init__()
        self.hook = None
        self.hook_id = None
        
    def start(self):
        """키보드 훅 시작"""
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
                
                # 키 정보 생성
                key_info = {
                    'key_code': get_key_name(vk_code),
                    'scan_code': scan_code,
                    'virtual_key': vk_code,
                    'modifiers': get_qt_modifiers()
                }
                
                # 시그널 발생
                self.key_pressed.emit(key_info)
                
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
        import atexit
        atexit.register(self.stop)
        
    def stop(self):
        """키보드 훅 중지"""
        if self.hook_id:
            user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None
