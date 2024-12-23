import win32con
import ctypes
from ctypes import wintypes
from PySide6.QtCore import Qt, QObject, Signal
import win32api

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
WM_KEYUP = 0x0101
WM_SYSKEYUP = 0x0105

# Hook callback prototype
HOOKPROC = ctypes.CFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, ctypes.POINTER(KBDLLHOOKSTRUCT))

user32 = ctypes.WinDLL('user32', use_last_error=True)

def get_key_name(vk_code, kb_flags):
    """가상 키 코드를 키 이름으로 변환"""
    # 특수 키 이름
    special_keys = {
        # 기능 키 (F1-F12: 0x70-0x7B)
        0x70: 'F1', 0x71: 'F2', 0x72: 'F3', 0x73: 'F4',
        0x74: 'F5', 0x75: 'F6', 0x76: 'F7', 0x77: 'F8',
        0x78: 'F9', 0x79: 'F10', 0x7A: 'F11', 0x7B: 'F12',
        
        # 제어 키
        win32con.VK_RETURN: '엔터',
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
        
        # 특수 키
        44: ',',  # 쉼표 키 (VK_OEM_COMMA)
        188: ',',  # 쉼표 키 (대체 코드)
        192: '백쿼트(`)',  # 백쿼트 키 (VK_OEM_3)
        190: '마침표(.)',  # 마침표 키 (VK_OEM_PERIOD)
        25: '오른쪽 컨트롤(한영 전환)',  # 한/영 전환 키
        220: '백슬래시(\\)',  # 백슬래시 키 (VK_OEM_5)
        21: '한자',  # 한자 키
        144: 'NumLock',  # NumLock 키
        187: '등호(=)',  # 등호 키 (VK_OEM_PLUS)
        189: '하이픈(-)',  # 하이픈 키 (VK_OEM_MINUS)
        221: '오른쪽 대괄호(])',  # 오른쪽 대괄호 키 (VK_OEM_6)
        219: '왼쪽 대괄호([)',  # 왼쪽 대괄호 키 (VK_OEM_4)
        186: '세미콜론(;)',  # 세미콜론 키 (VK_OEM_1)
        222: '작은따옴표(\')',  # 작은따옴표 키 (VK_OEM_7)
        191: '슬래시(/)',  # 슬래시 키 (VK_OEM_2)
        91: '윈도우',  # 윈도우 키
        20: 'CapsLock',  # Caps Lock 키
    }

    # 숫자패드 엔터 키의 특수 처리
    if vk_code == win32con.VK_RETURN and (kb_flags & 0x1):  # 확장 키 플래그 확인
        return '숫자패드 엔터'
    
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

def get_scan_code(key):
    # 시스템 키 매핑
    key_code_map = {
        '왼쪽 쉬프트': win32con.VK_LSHIFT,
        '오른쪽 쉬프트': win32con.VK_RSHIFT,
        '왼쪽 컨트롤': win32con.VK_LCONTROL,
        '오른쪽 컨트롤': win32con.VK_RCONTROL,
        '왼쪽 알트': win32con.VK_LMENU,
        '오른쪽 알트': win32con.VK_RMENU,
        'Home': win32con.VK_HOME,
        '엔터': win32con.VK_RETURN,
        'Tab': win32con.VK_TAB,
        'ESC': win32con.VK_ESCAPE,
        'Space': win32con.VK_SPACE,
        'Backspace': win32con.VK_BACK,
        'Delete': win32con.VK_DELETE,
        'Insert': win32con.VK_INSERT,
        'End': win32con.VK_END,
        'Page Up': win32con.VK_PRIOR,
        'Page Down': win32con.VK_NEXT,
        '방향키 왼쪽 ←': win32con.VK_LEFT,
        '방향키 오른쪽 →': win32con.VK_RIGHT,
        '방향키 위쪽 ↑': win32con.VK_UP,
        '방향키 아래쪽 ↓': win32con.VK_DOWN,
        '숫자패드 0': win32con.VK_NUMPAD0,
        '숫자패드 1': win32con.VK_NUMPAD1,
        '숫자패드 2': win32con.VK_NUMPAD2,
        '숫자패드 3': win32con.VK_NUMPAD3,
        '숫자패드 4': win32con.VK_NUMPAD4,
        '숫자패드 5': win32con.VK_NUMPAD5,
        '숫자패드 6': win32con.VK_NUMPAD6,
        '숫자패드 7': win32con.VK_NUMPAD7,
        '숫자패드 8': win32con.VK_NUMPAD8,
        '숫자패드 9': win32con.VK_NUMPAD9,
        '숫자패드 *': win32con.VK_MULTIPLY,
        '숫자패드 +': win32con.VK_ADD,
        '숫자패드 -': win32con.VK_SUBTRACT,
        '숫자패드 .': win32con.VK_DECIMAL,
        '숫자패드 /': win32con.VK_DIVIDE,
    }

    # 가상 키 코드 얻기
    if key in key_code_map:
        virtual_key = key_code_map[key]
    else:
        # 일반 문자키의 경우
        virtual_key = ord(key.upper())

    # 숫자패드 엔터 키의 특수 처리
    if key == '엔터':
        scan_code = 28  # 0x1C (28) 
    else:
        scan_code = win32api.MapVirtualKey(virtual_key, 0)

    return scan_code, virtual_key

class KeyboardHook(QObject):
    """키보드 훅을 관리하는 클래스"""
    
    key_pressed = Signal(dict)  # 키가 눌렸을 때 발생하는 시그널
    key_released = Signal(dict)  # 키가 떼졌을 때 발생하는 시그널
    
    def __init__(self):
        super().__init__()
        self.hook = None
        self.hook_id = None
        
    def start(self):
        """키보드 훅 시작"""
        def hook_callback(nCode, wParam, lParam):
            if nCode >= 0:
                kb = lParam.contents
                # 확장 키 플래그 (0x1)
                is_extended = (kb.flags & 0x1) == 0x1
                # ALT 키 플래그 (0x20)
                is_alt_down = (kb.flags & 0x20) == 0x20
                
                # 가상 키와 스캔 코드
                vk_code = kb.vkCode
                scan_code = kb.scanCode
                
                # 확장 키 처리 (시스템 키 포함)
                if is_extended:
                    if vk_code == win32con.VK_RETURN:
                        vk_code = win32con.VK_RETURN
                        scan_code = 0x1C + 0xE0  # 252 (숫자패드 엔터의 확장 스캔 코드)
                    elif vk_code == win32con.VK_CONTROL:
                        vk_code = win32con.VK_RCONTROL
                        scan_code = scan_code | 0xE0  # 확장 키 플래그 추가
                    elif vk_code == win32con.VK_MENU:
                        vk_code = win32con.VK_RMENU
                        scan_code = scan_code | 0xE0  # 확장 키 플래그 추가
                elif not is_extended:
                    if vk_code == win32con.VK_SHIFT:
                        vk_code = win32con.VK_LSHIFT if scan_code == 42 else win32con.VK_RSHIFT
                    elif vk_code == win32con.VK_CONTROL:
                        vk_code = win32con.VK_LCONTROL
                    elif vk_code == win32con.VK_MENU:
                        vk_code = win32con.VK_LMENU
                
                # 특수 키 처리 (쉼표 등)
                if vk_code in [44, 188]:  # 쉼표 키 (VK_OEM_COMMA 또는 대체 코드)
                    vk_code = 44  # VK_OEM_COMMA로 통일
                    scan_code = 84  # 쉼표 키의 스캔 코드
                else:
                    # 시스템 키의 스캔 코드 처리
                    scan_code = win32api.MapVirtualKey(vk_code, 0) or scan_code
                
                # 키 정보 생성
                key_info = {
                    'key_code': get_key_name(vk_code, kb.flags),
                    'scan_code': scan_code,
                    'virtual_key': vk_code,
                    'modifiers': get_qt_modifiers(),
                    'is_system_key': is_alt_down
                }
                
                # 시스템 키(알트) 처리
                if wParam in [WM_SYSKEYDOWN, WM_SYSKEYUP]:
                    if vk_code == win32con.VK_MENU or vk_code in [win32con.VK_LMENU, win32con.VK_RMENU]:
                        # ALT 키 자체의 이벤트
                        if wParam == WM_SYSKEYDOWN:
                            self.key_pressed.emit(key_info)
                        else:
                            self.key_released.emit(key_info)
                        return user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)
                
                # 일반 키 이벤트 처리
                if wParam in [WM_KEYDOWN, WM_SYSKEYDOWN]:
                    self.key_pressed.emit(key_info)
                elif wParam in [WM_KEYUP, WM_SYSKEYUP]:
                    self.key_released.emit(key_info)
                
            return user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)
        
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
