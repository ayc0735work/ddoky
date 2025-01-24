# 키 입력 처리 흐름 문서

## 1. 개요
이 문서는 키 입력이 감지되는 순간부터 아이템 목록 상자에 표시되기까지의 전체 과정을 상세하게 설명합니다.

### 1.1 전체 흐름도
```
[사용자 키 입력] → [키보드 훅] → [키 정보 구조화] → [상태 정보 생성] → [Repository 저장] → [UI 표시]
     ↓                 ↓              ↓                  ↓                ↓              ↓
  버튼 클릭 → 모달 다이얼로그 → 데이터 포맷팅 → 누르기/떼기 변환 → 중앙 저장소 저장 → 목록 상자 표시
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
           self._Logic_Maker_Tool_key_info_controller.key_state_info_process(get_entered_key_info)
   ```

5. **키 상태 정보 생성 및 처리**
   - 파일: `logic_maker_tool_key_info_controller.py`
   - 메서드: `key_state_info_process()`
   - 동작: 
     * 하나의 키 입력을 누르기/떼기 두 상태로 변환
     * 각 상태별 표시 텍스트 생성
     * 각 상태 정보를 시그널로 전달
   ```python
   # 키 누르기 상태 정보 생성
   press_key_info = {
       'type': 'key',
       'key': key_info.get('key_code'),
       'modifiers': key_info.get('modifiers', []),
       'display_text': f"{key_info.get('simple_display_text')} --- 누르기",
       'action': '누르기',
       'scan_code': key_info.get('scan_code'),
       'virtual_key': key_info.get('virtual_key')
   }
   
   # 키 떼기 상태 정보 생성
   release_key_info = {
       'type': 'key',
       'key': key_info.get('key_code'),
       'modifiers': key_info.get('modifiers', []),
       'display_text': f"{key_info.get('simple_display_text')} --- 떼기",
       'action': '떼기',
       'scan_code': key_info.get('scan_code'),
       'virtual_key': key_info.get('virtual_key')
   }
   
   # 시그널 발생
   self.item_added.emit(press_key_info)
   self.item_added.emit(release_key_info)
   ```

6. **Repository를 통한 아이템 저장**
   - 파일: `logic_maker_tool_widget.py`
   - 메서드: `add_item()`
   - 동작: 
     * 아이템 정보 검증
     * 순서(order) 값 설정
     * Repository를 통한 아이템 저장
   ```python
   def add_item(self, item_info):
       if isinstance(item_info, dict):
           if 'order' not in item_info:
               item_info['order'] = self.get_next_order()
           self.repository.add_item(item_info)
   ```

7. **UI 업데이트**
   - 파일: `logic_detail_widget.py`
   - 메서드: Repository의 `item_added` 시그널 핸들러
   - 동작:
     * Repository로부터 아이템 추가 시그널 수신
     * QListWidgetItem 생성 및 설정
     * 리스트 위젯에 아이템 추가
     * 로그 기록

### 1.3 시그널 흐름
```
[키보드 훅 이벤트]
         ↓
[EnteredKeyInfoDialog]
         ↓
[LogicMakerToolWidget]
         ↓
[LogicMakerToolKeyInfoController]
         |
         | key_state_info_process()
         ↓
    item_added 시그널
         ↓
[LogicMakerToolWidget.add_item()]
         |
         | Repository 저장
         ↓
[LogicItemManageRepository.add_item()]
         |
         | Repository item_added 시그널
         ↓
[LogicDetailWidget UI 업데이트]
```

## 2. 파일 구조 및 역할
```
BE/function/
├── _common_components/modal/entered_key_info_modal/
│   ├── entered_key_info_dialog.py     # 키 입력 모달 다이얼로그
│   ├── entered_key_info_widget.py     # 키 입력 UI 위젯
│   └── keyboard_hook_handler.py       # 키보드 훅 처리기
├── make_logic/
│   ├── logic_maker_tool/
│   │   ├── logic_maker_tool_widget.py            # UI 표시 및 사용자 입력 처리
│   │   └── logic_maker_tool_key_info_controller.py  # 키 입력 데이터 처리
│   ├── repository/
│   │   └── logic_item_repository.py    # 아이템 중앙 저장소
│   └── logic_detail/
│       └── logic_detail_widget.py      # 최종 UI 표시
```

## 3. 주요 클래스 설명

### 3.1 LogicItemManageRepository
```python
class LogicItemManageRepository:
    # 시그널
    item_added = Signal(dict)    # 아이템 추가 시그널
    item_deleted = Signal(dict)  # 아이템 삭제 시그널
    
    def __init__(self):
        self.items = []         # 아이템 저장 리스트
    
    def add_item(self, item_info):
        # 아이템 추가 및 시그널 발생
        self.items.append(item_info)
        self.item_added.emit(item_info)
```

### 3.2 LogicMakerToolKeyInfoController
```python
class LogicMakerToolKeyInfoController(QObject):
    # 시그널
    item_added = Signal(dict)  # UI 업데이트용
    
    def key_state_info_process(self, key_info):
        # 키 정보를 누르기/떼기 상태로 변환
        # item_added 시그널 발생
```

### 3.3 LogicMakerToolWidget
```python
class LogicMakerToolWidget(QFrame):
    def __init__(self, repository: LogicItemManageRepository):
        self.repository = repository
        self._Logic_Maker_Tool_key_info_controller = LogicMakerToolKeyInfoController()
        # 컨트롤러의 시그널을 add_item 메서드에 연결
        self._Logic_Maker_Tool_key_info_controller.item_added.connect(self.add_item)
```

## 4. 데이터 구조

### 4.1 키 상태 정보
```python
{
    'type': 'key',                # 입력 타입
    'key': str,                   # 키 코드
    'modifiers': KeyboardModifier, # 수정자 키 상태
    'display_text': str,          # UI 표시용 텍스트
    'action': str,                # '누르기' 또는 '떼기'
    'scan_code': int,             # 스캔 코드
    'virtual_key': int,           # 가상 키 코드
    'order': int                  # 순서
}
```

## 5. 책임 분리

### 5.1 Repository (LogicItemManageRepository)
- 아이템 데이터 중앙 관리
- 아이템 추가/삭제/수정 기능
- 상태 변경 시그널 발생

### 5.2 컨트롤러 (LogicMakerToolKeyInfoController)
- 키 입력 데이터 처리
- 상태 정보 생성
- UI 업데이트 시그널 발생

### 5.3 위젯 (LogicMakerToolWidget)
- UI 컴포넌트 표시
- 사용자 입력 처리
- Repository를 통한 아이템 관리

### 5.4 UI 위젯 (LogicDetailWidget)
- Repository 시그널 구독
- UI 업데이트 처리
- 아이템 목록 표시