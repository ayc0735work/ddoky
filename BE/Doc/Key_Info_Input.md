# 키 입력 처리 흐름 문서

## 1. 개요
이 문서는 키 입력이 감지되는 순간부터 아이템 목록 상자에 표시되기까지의 전체 과정을 상세하게 설명합니다.

### 1.1 전체 흐름도
```
[사용자 키 입력] → [키보드 훅] → [키 정보 구조화] → [상태 정보 생성] → [시그널 전파] → [UI 표시]
     ↓                 ↓              ↓                  ↓                ↓              ↓
  버튼 클릭 → 모달 다이얼로그 → 데이터 포맷팅 → 누르기/떼기 변환 → 위젯 간 통신 → 목록 상자 표시
```

### 1.2 상세 처리 순서
1. **다이얼로그 생성 및 표시**
   - 파일: `logic_maker_tool_widget.py`
   - 메서드: `_open_key_input_dialog()`
   - 동작:
     * 모달 다이얼로그 생성
     * 키 입력 영역 포커스 설정
     * ESC 키 처리 방지 설정 (모달 닫힘 방지)
   ```python
   dialog = EnteredKeyInfoDialog(self)  # 다이얼로그 생성
   ```

2. **키 입력 감지 및 저장**
   - 파일: `entered_key_info_dialog.py`
   - 메서드: `get_entered_key_info()`
   - 동작:
     * Windows API의 저수준 키보드 훅 설정 (WH_KEYBOARD_LL)
     * 키 이벤트 필터링 (시스템 예약 키, 중복 이벤트 제거)
     * NumLock, CapsLock 등 특수 상태 처리
   ```python
   return self.last_key_info  # 키보드 훅으로 캡처된 키 정보 반환
   ```

3. **확인 버튼 클릭 처리**
   - 파일: `entered_key_info_dialog.py`
   - 메서드: `_on_confirm()`
   - 동작:
     * 키 정보 유효성 검사
     * 필수 필드 존재 확인
     * 키보드 훅 정리 및 해제
   ```python
   confirmed_key_info = self.get_entered_key_info()
   if confirmed_key_info:
       self.accept()  # 다이얼로그 성공적 종료
   ```

4. **다이얼로그 결과 처리**
   - 파일: `logic_maker_tool_widget.py`
   - 메서드: `_open_key_input_dialog()`
   - 동작:
     * 다이얼로그 결과 코드 확인
     * 키 정보 컨트롤러로 전달
     * 예외 상황 처리 (취소, 키 정보 없음 등)
   ```python
   if dialog.exec() == QDialog.Accepted:
       get_entered_key_info = dialog.get_entered_key_info()
       if get_entered_key_info:
           self.key_controller.handle_confirmed_key_input(get_entered_key_info)
   ```

5. **키 상태 정보 생성**
   - 파일: `logic_maker_tool_key_info_controller.py`
   - 메서드: `handle_confirmed_key_input()`
   - 동작: 
     * 하나의 키 입력을 누르기/떼기 두 상태로 변환
     * 각 상태별 표시 텍스트 생성
     * 이벤트 순서 보장 (누르기 → 떼기)
     * 수정자 키 상태 보존
   ```python
   # 누르기 이벤트 생성
   key_state_info_press = get_entered_key_info.copy()
   key_state_info_press['type'] = "key"
   key_state_info_press['action'] = "누르기"
   key_state_info_press['display_text'] = f"{get_entered_key_info['key_code']} --- 누르기"
   
   # 떼기 이벤트 생성
   key_state_info_release = get_entered_key_info.copy()
   key_state_info_release['type'] = "key"
   key_state_info_release['action'] = "떼기"
   key_state_info_release['display_text'] = f"{get_entered_key_info['key_code']} --- 떼기"
   ```

6. **컨트롤러의 아이템 처리**
   - 파일: `logic_maker_tool_key_info_controller.py`
   - 메서드: `_on_key_state_info_added()`
   - 동작: 
     * 내부 아이템 리스트에 추가
     * UI 업데이트 시그널 발생
     * 로그 기록 (디버깅 및 추적용)
     * 메모리 관리 (깊은 복사 사용)
   ```python
   self.items.append(key_state_info)  # 내부 리스트에 추가
   self.item_added.emit(key_state_info)  # UI 업데이트 시그널
   ```

### 1.3 주요 컴포넌트 역할
- **키 입력 모달**: 사용자의 키 입력을 받고 표시
- **키보드 훅**: 저수준 키보드 이벤트 캡처
- **키 입력 컨트롤러**: 키 입력 데이터 처리 및 상태 관리
- **로직 메이커 위젯**: UI 표시 및 사용자 상호작용
- **로직 상세 위젯**: 최종 UI 표시

## 2. 파일 구조 및 역할
```
BE/function/
├── _common_components/modal/entered_key_info_modal/
│   ├── entered_key_info_dialog.py     # 키 입력 모달 다이얼로그
│   ├── entered_key_info_widget.py     # 키 입력 UI 위젯
│   └── keyboard_hook_handler.py       # 키보드 훅 처리기
├── make_logic/logic_maker_tool/
│   ├── logic_maker_tool_widget.py            # UI 표시 및 사용자 입력 처리
│   └── logic_maker_tool_key_info_controller.py  # 키 입력 데이터 처리 및 상태 관리
└── make_logic/logic_detail/
    └── logic_detail_widget.py         # 최종 UI 표시
```

### 2.1 파일 간 상호작용
```
[entered_key_info_dialog.py] ←→ [entered_key_info_widget.py]
           ↑                         ↑
           └─────── [keyboard_hook_handler.py]
                         ↑
[logic_maker_tool_widget.py] ←→ [logic_maker_tool_key_info_controller.py]
           ↓
[logic_detail_widget.py]
```

## 3. 데이터 흐름

### 3.1 키 입력 시작
1. 사용자가 `LogicMakerToolWidget`의 "키 입력 추가" 버튼 클릭
2. `_open_key_input_dialog()` 메서드에서 `EnteredKeyInfoDialog` 생성
3. 모달 다이얼로그 표시 및 사용자 입력 대기

### 3.2 키 입력 감지
1. 키보드 훅이 키 입력 이벤트 캡처
2. `EnteredKeyInfoDialog`에서 키 정보 구조화
3. 사용자가 확인 버튼 클릭 시 `get_entered_key_info()` 호출

### 3.3 컨트롤러 처리
1. `LogicMakerToolKeyInfoController`가 키 정보 수신
2. 누르기/떼기 상태 정보 생성
3. 내부 아이템 리스트에 추가
4. UI 업데이트를 위한 시그널 발생

### 3.4 시그널 흐름
```
[키보드 훅 이벤트]
         ↓
[EnteredKeyInfoDialog]
         ↓
[LogicMakerToolWidget]
         ↓
[LogicMakerToolKeyInfoController] --- confirmed_and_added_key_info --> [자체 처리]
         |                                                              ↓
         |                                                        [아이템 추가]
         |                                                              ↓
    item_added                                                    [로그 기록]
         ↓
[LogicMakerToolWidget] --- item_added --> [LogicDetailWidget]
```

## 4. 주요 클래스 설명

### 4.1 LogicMakerToolKeyInfoController
```python
class LogicMakerToolKeyInfoController(QObject):
    # 시그널
    item_added = Signal(dict)  # UI 업데이트용
    
    def __init__(self):
        self.items = []  # 키 입력 관련 아이템 관리
    
    def handle_confirmed_key_input(self, key_info):
        # 키 정보를 누르기/떼기 상태로 변환
        # 아이템 리스트에 추가
        # UI 업데이트 시그널 발생
```

### 4.2 LogicMakerToolWidget
```python
class LogicMakerToolWidget(QFrame):
    # 시그널
    item_added = Signal(dict)  # UI 업데이트용
    
    def __init__(self):
        self.key_controller = LogicMakerToolKeyInfoController()
        # 컨트롤러의 시그널을 위젯의 시그널로 연결
        self.key_controller.item_added.connect(self.item_added.emit)
```

## 5. 데이터 구조

### 5.1 키 상태 정보
```python
{
    'type': 'key',                # 입력 타입
    'action': '누르기' or '떼기',  # 동작 유형
    'key_code': str,              # 키 이름
    'scan_code': int,             # 하드웨어 코드
    'virtual_key': int,           # 가상 키 코드
    'modifiers': KeyboardModifier, # 수정자 키 상태
    'location': str,              # 키 위치
    'modifier_text': str,         # 수정자 키 텍스트
    'display_text': str,          # UI 표시용 텍스트
    'detail_display_text': str    # 상세 정보
}
```

## 6. 책임 분리

### 6.1 컨트롤러 (LogicMakerToolKeyInfoController)
- 키 입력 데이터 처리
- 상태 정보 생성 및 관리
- 아이템 리스트 관리
- UI 업데이트 시그널 발생

### 6.2 위젯 (LogicMakerToolWidget)
- UI 컴포넌트 표시
- 사용자 입력 처리
- 컨트롤러와의 시그널 연결
- UI 업데이트 시그널 전달