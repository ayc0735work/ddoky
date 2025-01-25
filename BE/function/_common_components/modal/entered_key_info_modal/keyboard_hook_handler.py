import win32con
import ctypes
from ctypes import wintypes
from PySide6.QtCore import Qt, QObject, Signal
import win32api

# Windows hook structures
LRESULT = ctypes.c_long
ULONG_PTR = wintypes.WPARAM

class KBDLLHOOKSTRUCT(ctypes.Structure):
    """Windows API의 키보드 후킹을 위한 구조체
    
    이 구조체는 Windows의 저수준 키보드 후킹에서 사용되며,
    키보드 이벤트가 발생할 때마다 이벤트의 상세 정보를 전달받습니다.
    
    Fields:
        vkCode (DWORD): 가상 키 코드 (예: 'A' 키는 0x41)
        scanCode (DWORD): 키보드의 물리적 키 위치에 대한 하드웨어 코드
        flags (DWORD): 키 이벤트의 추가 정보 (확장 키 여부 등)
        time (DWORD): 이벤트 발생 시간 (시스템 시작 이후 경과 시간, 밀리초)
        dwExtraInfo (ULONG_PTR): 추가 정보를 위한 포인터
    """
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
    """가상 키 코드를 사용자가 읽을 수 있는 키 이름으로 변환합니다.
    
    Args:
        vk_code (int): 변환할 가상 키 코드
        kb_flags (int): 키보드 플래그 (확장 키 여부 등의 추가 정보)
    
    Returns:
        str: 키의 표시 이름 (예: 'A', 'Enter', '방향키 왼쪽 ←' 등)
    """
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
    """현재 활성화된 수정자 키(Ctrl, Alt, Shift 등)의 상태를 Qt 플래그로 반환합니다.
    
    Returns:
        int: Qt.KeyboardModifier 플래그의 조합
             예: Qt.ControlModifier | Qt.ShiftModifier
    """
    modifiers = Qt.NoModifier
    
    # Shift
    if user32.GetAsyncKeyState(win32con.VK_LSHIFT) & 0x8000:
        modifiers |= Qt.KeypadModifier | Qt.ShiftModifier  # KeypadModifier를 왼쪽 구분자로 사용
    if user32.GetAsyncKeyState(win32con.VK_RSHIFT) & 0x8000:
        modifiers |= Qt.KeyboardModifier.MetaModifier | Qt.ShiftModifier  # MetaModifier를 오른쪽 구분자로 사용
        
    # Control
    if user32.GetAsyncKeyState(win32con.VK_LCONTROL) & 0x8000:
        modifiers |= Qt.KeypadModifier | Qt.ControlModifier
    if user32.GetAsyncKeyState(win32con.VK_RCONTROL) & 0x8000 or user32.GetAsyncKeyState(25) & 0x8000:  # 일반 오른쪽 Ctrl 또는 한영 전환 키
        modifiers |= Qt.KeyboardModifier.MetaModifier | Qt.ControlModifier
        
    # Alt
    if user32.GetAsyncKeyState(win32con.VK_LMENU) & 0x8000:
        modifiers |= Qt.KeypadModifier | Qt.AltModifier
    if user32.GetAsyncKeyState(win32con.VK_RMENU) & 0x8000:
        modifiers |= Qt.KeyboardModifier.MetaModifier | Qt.GroupSwitchModifier  # AltGr로 처리
        
    # 한자 키
    if user32.GetAsyncKeyState(21) & 0x8000:  # 한자 키
        modifiers |= Qt.KeypadModifier | Qt.AltModifier
        
    return modifiers

def get_modifier_from_text(modifier_text):
    """수정자 키 텍스트를 Qt 수정자 키 값으로 변환합니다.
    
    Args:
        modifier_text (str): 수정자 키 텍스트 (예: "왼쪽 Shift + 오른쪽 Ctrl")
    
    Returns:
        int: Qt.KeyboardModifier 플래그의 조합
    """
    if not modifier_text or modifier_text == "없음":
        return Qt.NoModifier
        
    modifiers = Qt.NoModifier
    mod_parts = modifier_text.split(" + ")
    
    for mod in mod_parts:
        if mod == "왼쪽 Shift":
            modifiers |= Qt.KeypadModifier | Qt.ShiftModifier
        elif mod == "오른쪽 Shift":
            modifiers |= Qt.KeyboardModifier.MetaModifier | Qt.ShiftModifier
        elif mod == "왼쪽 Ctrl":
            modifiers |= Qt.KeypadModifier | Qt.ControlModifier
        elif mod == "오른쪽 Ctrl":
            modifiers |= Qt.KeyboardModifier.MetaModifier | Qt.ControlModifier
        elif mod == "왼쪽 Alt":
            modifiers |= Qt.KeypadModifier | Qt.AltModifier
        elif mod == "오른쪽 Alt":
            modifiers |= Qt.KeyboardModifier.MetaModifier | Qt.AltModifier
        elif mod == "AltGr":
            modifiers |= Qt.KeyboardModifier.MetaModifier | Qt.GroupSwitchModifier
        elif mod == "Shift":
            modifiers |= Qt.ShiftModifier
        elif mod == "Ctrl":
            modifiers |= Qt.ControlModifier
        elif mod == "Alt":
            modifiers |= Qt.AltModifier
            
    return modifiers

def get_modifier_text(modifiers):
    """수정자 키 상태를 텍스트로 변환합니다.(수정자 키가 없으면 '없음'을 반환함)
    Args:
        modifiers (int): Qt.KeyboardModifier 플래그의 조합
    Returns:
        str: 수정자 키 설명 (예: '왼쪽 Ctrl + 오른쪽 Alt + 왼쪽 Shift')
    """
    mod_texts = []
    
    # modifiers가 정수인 경우 Qt.KeyboardModifier로 변환
    if isinstance(modifiers, int):
        modifiers = Qt.KeyboardModifier(modifiers)
    
    # Shift 키 처리
    if modifiers & Qt.ShiftModifier:
        if modifiers & Qt.KeypadModifier:
            mod_texts.append("왼쪽 Shift")
        elif modifiers & Qt.KeyboardModifier.MetaModifier:
            mod_texts.append("오른쪽 Shift")
        else:
            mod_texts.append("Shift")
            
    # Control 키 처리
    if modifiers & Qt.ControlModifier:
        if modifiers & Qt.KeypadModifier:
            mod_texts.append("왼쪽 Ctrl")
        elif modifiers & Qt.KeyboardModifier.MetaModifier:
            mod_texts.append("오른쪽 Ctrl")
        else:
            mod_texts.append("Ctrl")
            
    # Alt 키 처리
    if modifiers & Qt.AltModifier:
        if modifiers & Qt.KeypadModifier:
            mod_texts.append("왼쪽 Alt")
        elif modifiers & Qt.KeyboardModifier.MetaModifier:
            mod_texts.append("오른쪽 Alt")
        else:
            mod_texts.append("Alt")
            
    # AltGr 키 처리
    if modifiers & Qt.GroupSwitchModifier and modifiers & Qt.KeyboardModifier.MetaModifier:
        mod_texts.append("AltGr")
        
    return " + ".join(mod_texts) if mod_texts else "없음"

def get_scan_code(key):
    """키 코드에 해당하는 스캔 코드를 반환합니다.
    
    Args:
        key (int): 가상 키 코드
    
    Returns:
        int: 해당 키의 스캔 코드
    """
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

    # 가상 키와 스캔 코드
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

def get_key_location(scan_code):
    """스캔 코드를 기반으로 키의 물리적 위치 정보를 반환합니다.
    
    Args:
        scan_code (int): 키보드 스캔 코드
    
    Returns:
        str: 키의 위치 설명 (예: '왼쪽', '오른쪽', '숫자패드')
    """
    # 예시적인 위치 판단 (실제 구현 시 더 자세한 매핑 필요)
    if scan_code in [42, 29, 56]:  # 왼쪽 Shift, Ctrl, Alt
        return "왼쪽"
    elif scan_code in [54, 285, 312]:  # 오른쪽 Shift, Ctrl, Alt
        return "오른쪽"
    elif 71 <= scan_code <= 83:  # 숫자패드 영역
        return "숫자패드"
    return "메인"

def create_formatted_key_info(raw_key_info):
    """키보드 입력의 raw 정보를 UI 표시와 이벤트 처리에 적합한 형식으로 변환합니다.
    
    이 함수는 키보드 이벤트의 raw 데이터를 받아서 애플리케이션 전체에서 사용할
    표준화된 형식(formatted_key_info)으로 변환합니다.
    
    Args:
        raw_key_info (dict): 키보드 입력 원시 정보
            {
                'key_code': str,      # 키의 표시 이름 (예: 'A', '엔터', '방향키 왼쪽 ←') 
                'scan_code': int,     # 하드웨어 키보드의 물리적 위치 값
                'virtual_key': int,   # Windows API 가상 키 코드
                'modifiers': int,     # Qt 기반 수정자 키 상태 플래그 (예: NoModifier=0, ShiftModifier=0x02000000, ControlModifier=0x04000000, AltModifier=0x08000000)
                'is_system_key': bool # ALT 키 눌림 여부
            }

    Returns:
        formatted_key_info (dict): 표준화된 키 정보
            {
                'key_code': str,      # 키의 표시 이름 (예: 'A', '엔터', '방향키 왼쪽 ←')
                'scan_code': int,     # 하드웨어 키보드의 물리적 위치 값 
                'virtual_key': int,   # Windows API 가상 키 코드
                'location': str,      # 키보드 위치 (예: '왼쪽', '오른쪽', '숫자패드', '메인')
                'modifiers': int,     # Qt 기반 수정자 키 상태 플래그 (예: NoModifier=0, ShiftModifier=0x02000000, ControlModifier=0x04000000, AltModifier=0x08000000)
                'modifier_text': str, # 수정자 키 텍스트 (예: '왼쪽 Ctrl', '오른쪽 Alt', '왼쪽 Shift')
                'is_system_key': bool # ALT 키 눌림 여부
                'simple_display_text': str   # UI에 표시할 간단한 텍스트 (예: '왼쪽 Ctrl + A (키 위치: 메인)')
            }
    """
    
    location = get_key_location(raw_key_info['scan_code'])

    # get_modifier_text() 함수에서 수정자키가 없을 때 '없음'을 반환함
    modifier_text = get_modifier_text(raw_key_info['modifiers'])
    
    # 간단한 표시 텍스트 생성
    simple_display_text = f"{modifier_text} + {raw_key_info['key_code']} (키 위치: {location})" if modifier_text != '없음' else f"{raw_key_info['key_code']} (키 위치: {location})"
    if not raw_key_info['key_code']:
        simple_display_text = f"알 수 없는 키 (키 위치: {location})"

    # 애플리케이션 전체에서 사용할 표준화된 키 정보 생성
    formatted_key_info = {
        'key_code': raw_key_info['key_code'],
        'scan_code': raw_key_info['scan_code'],
        'virtual_key': raw_key_info['virtual_key'],
        'location': location,        
        'modifiers': raw_key_info['modifiers'],
        'modifier_text': modifier_text,
        'is_system_key': raw_key_info.get('is_system_key', False),
        'simple_display_text': simple_display_text,
    }
    
    return formatted_key_info

class KeyboardHook(QObject):
    """키보드 후킹을 담당하는 클래스
    
    이 클래스는 Windows API의 저수준 키보드 후킹을 통해
    키보드 입력을 감지하고 처리합니다.
    """
    
    key_pressed = Signal(dict)  # 키가 눌렸을 때 발생하는 시그널
    key_released = Signal(dict)  # 키가 떼졌을 때 발생하는 시그널
    
    def __init__(self):
        """KeyboardHook 초기화"""
        super().__init__()
        self._hook = None
        self._hook_id = None
        self._last_formatted_key_info = None  # 마지막 키 정보 저장
    
    @property
    def last_formatted_key_info(self):
        """마지막으로 입력된 키 정보를 반환합니다.
        
        Returns:
            dict or None: 마지막으로 입력된 키의 formatted_key_info
        """
        return self._last_formatted_key_info
    
    def start(self):
        """키보드 후킹을 시작합니다."""
        def hook_callback(nCode, wParam, lParam):
            """키보드 이벤트 콜백 함수
            
            Args:
                nCode (int): 후킹 코드
                wParam (int): 이벤트 타입
                lParam (KBDLLHOOKSTRUCT): 키보드 이벤트 데이터
            
            Returns:
                LRESULT: 후킹 체인 처리 결과
            """
            if nCode < 0:
                return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)
                
            kb = lParam.contents
            raw_key_info = {
                'key_code': get_key_name(kb.vkCode, kb.flags),
                'scan_code': kb.scanCode,
                'virtual_key': kb.vkCode,
                'modifiers': get_qt_modifiers(),
                'is_system_key': wParam in (WM_SYSKEYDOWN, WM_SYSKEYUP)
            }
            
            formatted_key_info = create_formatted_key_info(raw_key_info)
            
            # 키가 눌렸을 때의 이벤트 처리 (WM_KEYDOWN: 일반 키, WM_SYSKEYDOWN: ALT와 함께 눌린 시스템 키)
            if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                # 현재 입력된 키 정보를 마지막 키 정보로 저장
                self._last_formatted_key_info = formatted_key_info
                # key_pressed 시그널을 발생시켜 구조화된 키 정보를 전달
                self.key_pressed.emit(formatted_key_info)
            
            # 키가 떼졌을 때의 이벤트 처리 (WM_KEYUP: 일반 키, WM_SYSKEYUP: ALT와 함께 떼진 시스템 키)
            elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                # key_released 시그널을 발생시켜 구조화된 키 정보를 전달
                self.key_released.emit(formatted_key_info)
            
            return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)
        
        # 후킹 프로시저 생성
        self._hook = HOOKPROC(hook_callback)
        # 후킹 설치
        self._hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook,
            None,
            0
        )
        
        if not self._hook_id:
            raise RuntimeError('키보드 후킹 설치 실패')
    
    def stop(self):
        """키보드 후킹을 중지합니다."""
        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)
            self._hook_id = None
            self._hook = None
            self._last_formatted_key_info = None  # 키 정보 초기화
