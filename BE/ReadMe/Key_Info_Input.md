# 키 입력 처리 흐름 문서

## 1. 개요
이 문서는 키 입력이 감지되는 순간부터 아이템 목록에 저장되기까지의 전체 과정을 설명합니다.

## 2. 파일 구조
```
BE/function/
├── _common_components/modal/entered_key_info_modal/
│   ├── entered_key_info_dialog.py     # 키 입력 모달 다이얼로그
│   ├── entered_key_info_widget.py     # 키 입력 UI 위젯
│   └── keyboard_hook_handler.py       # 키보드 훅 처리기
├── make_logic/logic_maker_tool/
│   ├── logic_maker_tool_widget.py     # 로직 메이커 도구 위젯
│   └── handlers/
│       └── entered_key_info_handler.py # 키 입력 정보 핸들러
└── make_logic/logic_detail/
    └── logic_detail_widget.py         # 로직 상세 위젯
```

## 3. 키 입력 처리 흐름

### 3.1 키 입력 시작
1. `LogicMakerToolWidget`의 "키 입력 추가" 버튼 클릭
2. `_request_key_to_input()` 메서드 호출
3. `EnteredKeyInfoHandler.request_key_input()` 메서드 호출
4. `EnteredKeyInfoDialog` 인스턴스 생성 및 모달로 표시

### 3.2 키보드 훅 설정 및 키 입력 감지
1. `EnteredKeyInfoWidget`의 입력 필드 클릭
2. `key_input_area_focused` 시그널 발생
3. `EnteredKeyInfoDialog._start_keyboard_hook()` 호출
4. `KeyboardHook` 인스턴스 생성 및 시작
5. Windows API의 저수준 키보드 훅이 키 이벤트 감지

### 3.3 키 정보 구조화 및 UI 업데이트
키 입력 시 다음 정보를 포함하는 딕셔너리 생성:
```python
{
    'key_code': str,        # 키의 표시 이름 (예: 'Space')
    'scan_code': int,       # 하드웨어 키보드의 물리적 위치 값 (예: 57)
    'virtual_key': int,     # Windows API 가상 키 코드 (예: 32)
    'modifiers': int,       # Qt 기반 수정자 키 상태 (예: KeyboardModifier.NoModifier)
    'location': str,        # 키보드 위치 (예: '메인')
    'modifier_text': str,   # 수정자 키 텍스트 (예: '없음')
    'is_system_key': bool,  # ALT 키 눌림 여부
    'simple_display_text': str  # UI 표시용 텍스트
}
```

### 3.4 키 정보 저장 및 전달 프로세스
1. 사용자가 "입력된 키 정보 저장" 버튼 클릭
2. `EnteredKeyInfoDialog._on_confirm()` 호출
3. `EnteredKeyInfoHandler.handle_confirmed_key_input()` 호출
4. 키 정보를 기반으로 두 가지 이벤트 생성:

#### 3.4.1 누르기 이벤트
```python
key_state_info_press = {
    'type': 'key',
    'action': '누르기',
    'display_text': 'Space --- 누르기',
    'detail_display_text': 'Space (키 위치: 메인) (스캔코드: 57, 가상키코드: 32, ...)',
    # ... 원본 키 정보 포함
}
```

#### 3.4.2 떼기 이벤트
```python
key_state_info_release = {
    'type': 'key',
    'action': '떼기',
    'display_text': 'Space --- 떼기',
    'detail_display_text': 'Space (키 위치: 메인) (스캔코드: 57, 가상키코드: 32, ...)',
    # ... 원본 키 정보 포함
}
```

### 3.5 시그널 전파 및 아이템 추가
1. `EnteredKeyInfoHandler`에서 `confirmed_and_added_key_info` 시그널 발생
2. `LogicMakerToolWidget._on_key_state_info_added()` 처리:
   - items 리스트에 키 상태 정보 추가
   - item_added 시그널 발생 (다른 위젯들에게 전달)
   - 로그 메시지 출력

3. `item_added` 시그널을 통해 다른 위젯들이 키 상태 정보를 받아 처리

### 3.6 로그 흐름
1. 키 입력 모달 확인 버튼 클릭 로그
2. 키 입력 추가 로그 (키입력핸들러)
3. 키 상태 정보 추가 시작 로그 (로직상세)
4. 데이터 처리 시작 로그 (로직상세)
5. 키 상태 정보 추가 완료 로그 (로직상세)
6. 키 상태 정보 추가 완료 로그 (로직메이커)
7. 키 상태 정보 업데이트 로그 (키입력핸들러)
8. 위 과정이 누르기/떼기 이벤트 각각에 대해 반복

## 4. 특별 처리 사항

### 4.1 중복 처리 방지
- 동일한 키 이벤트의 중복 처리 방지
- 시그널 연결의 중복 방지
- 아이템 추가의 중복 방지

### 4.2 예외 처리
- 잘못된 키 정보 형식 처리
- 시그널 전달 실패 처리
- 아이템 추가 실패 처리

### 4.3 로깅
- 각 단계별 상세 로그 기록
- 디버그 레벨 로그를 통한 상세 정보 추적
- 에러 발생 시 상세 정보 기록

## 5. 성능 최적화
- 불필요한 시그널 전파 방지
- 효율적인 데이터 구조 사용
- 메모리 사용량 최적화
