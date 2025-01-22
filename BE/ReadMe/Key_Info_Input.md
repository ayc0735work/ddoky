# 키 입력 처리 흐름 문서

## 1. 개요
이 문서는 키 입력이 감지되는 순간부터 아이템 목록에 저장되기까지의 전체 과정을 설명합니다.

## 2. 파일 구조
```
BE/function/_common_components/modal/entered_key_info_modal/
├── entered_key_info_dialog.py     # 키 입력 모달 다이얼로그
├── entered_key_info_widget.py     # 키 입력 UI 위젯
└── keyboard_hook_handler.py       # 키보드 훅 처리기
```

## 3. 키 입력 처리 흐름

### 3.1 키 입력 시작
1. `LogicMakerToolWidget`의 "키 입력 추가" 버튼 클릭
2. `_request_key_to_input()` 메서드 호출
3. `EnteredKeyInfoDialog` 인스턴스 생성 및 모달로 표시

### 3.2 키보드 훅 설정
1. `EnteredKeyInfoWidget`의 입력 필드 클릭
2. `key_input_area_focused` 시그널 발생
3. `EnteredKeyInfoDialog._start_keyboard_hook()` 호출
4. `KeyboardHook` 인스턴스 생성 및 시작

### 3.3 키 입력 감지 및 처리
1. Windows API의 저수준 키보드 훅이 키 이벤트 감지
2. `KBDLLHOOKSTRUCT` 구조체로 키 이벤트 정보 수신:
   - vkCode: 가상 키 코드
   - scanCode: 하드웨어 스캔 코드
   - flags: 키 이벤트 플래그
   - time: 이벤트 발생 시간
   - dwExtraInfo: 추가 정보

### 3.4 키 정보 변환
`keyboard_hook_handler.py`에서 다음 함수들을 통해 키 정보 변환:

1. `get_key_name(vk_code, kb_flags)`:
   - 가상 키 코드를 사용자가 읽을 수 있는 이름으로 변환
   - 특수 키, 기능 키, 숫자패드 키 등 처리
   - 반환 예: 'A', 'Enter', '방향키 왼쪽 ←'

2. `get_qt_modifiers()`:
   - 현재 눌린 수정자 키(Ctrl, Alt, Shift) 상태 확인
   - Qt.KeyboardModifier 플래그로 변환

3. `get_modifier_text(modifiers)`:
   - 수정자 키 상태를 텍스트로 변환
   - 반환 예: 'Ctrl + Alt'

4. `get_scan_code(key)`:
   - 키 코드에 해당하는 하드웨어 스캔 코드 매핑
   - 특수 키(숫자패드 엔터 등) 처리

### 3.5 키 정보 구조화
다음 형식의 딕셔너리로 키 정보 구조화:
```python
{
    'key_code': str,        # 키의 표시 이름
    'scan_code': int,       # 하드웨어 키보드의 물리적 위치 값
    'virtual_key': int,     # Windows API 가상 키 코드
    'modifiers': int,       # Qt 기반 수정자 키 상태
    'location': str,        # 키보드 위치
    'modifier_text': str,   # 수정자 키 텍스트
    'is_system_key': bool,  # ALT 키 눌림 여부
    'simple_display_text': str  # UI 표시용 텍스트
}
```

### 3.6 UI 업데이트
1. `EnteredKeyInfoDialog._on_key_pressed()` 호출
2. 중복 키 입력 검사
3. `EnteredKeyInfoWidget.update_key_info()` 호출:
   - 메인 키 표시 업데이트
   - 상세 정보 표시 업데이트 (키 코드, 스캔 코드 등)
4. NumLock 상태 체크 및 경고 표시

### 3.7 키 정보 저장 및 전달
1. "입력된 키 정보 저장" 버튼 클릭
2. `EnteredKeyInfoDialog._on_confirm()` 호출
3. `LogicMakerToolWidget._add_confirmed_input_key()` 호출
4. 두 가지 키 상태 정보 생성 및 전달:
   ```python
   # 누르기 이벤트
   key_state_info_press = {
       'display_text': f"{key_code} --- 누르기",
       'action': "누르기",
       'type': "key_input",
       ...  # 원본 키 정보
   }
   
   # 떼기 이벤트
   key_state_info_release = {
       'display_text': f"{key_code} --- 떼기",
       'action': "떼기",
       'type': "key_input",
       ...  # 원본 키 정보
   }
   ```

### 3.8 아이템 목록 저장
최종적으로 `settings.json`에 다음 형식으로 저장:
```json
{
    "order": 1,
    "display_text": "키 입력: 엔터 --- 누르기",
    "action": "누르기",
    "type": "key_input",
    "key_code": "엔터",
    "scan_code": 28,
    "virtual_key": 13,
    "modifiers": 0
}
```

## 4. 특별 처리 사항

### 4.1 NumLock 처리
- NumLock 상태 실시간 체크
- 상태 변경 시 경고 메시지 표시
- 숫자패드 키 입력 시 특별 처리

### 4.2 보안 및 안정성
- ESC 키로 다이얼로그가 닫히는 것 방지
- 중복 키 입력 방지
- 키보드 훅의 안전한 시작과 종료

### 4.3 특수 키 처리
- 숫자패드 엔터 키 구분
- 확장 키 처리 (오른쪽 Alt, Ctrl 등)
- 시스템 키(Alt 조합) 처리

## 5. 시그널 흐름
1. `key_input_area_focused` → `_start_keyboard_hook()`
2. `key_input_area_unfocused` → `_stop_keyboard_hook()`
3. `key_pressed` → `_on_key_pressed()`
4. `key_input_changed` → UI 업데이트
5. `confirmed_and_added_key_info` → 아이템 목록 추가

## 6. 트리거 키 관리

### 6.1 트리거 키 중복 체크
1. 키 입력 시 `LogicDetailWidget._on_key_input_changed()` 메서드에서 중복 체크
2. 중복 체크 프로세스:
   - 모든 로직 데이터 로드 (`settings_manager.load_logics()`)
   - 현재 로직과 중첩 로직 제외
   - virtual_key와 modifiers 값 비교
   - 중복 발견 시 경고 메시지 표시 및 키 입력 초기화

### 6.2 키 정보 저장 및 로드
1. 저장 과정:
   - `settings.json`에 로직별로 키 정보 저장
   - 저장 시점: 로직 저장 또는 수정 시
   - 저장 형식: JSON 구조 (3.8 아이템 목록 저장 참조)

2. 로드 과정:
   - 프로그램 시작 시 `settings.json` 로드
   - 로직 편집 시 해당 로직의 키 정보 로드
   - 트리거 키 설정 시 기존 키 정보 복원

## 7. 키보드 훅 생명주기

### 7.1 키보드 훅 시작
- 입력 필드 포커스 획득 시
- 다이얼로그 표시 상태에서만 동작
- 단일 인스턴스만 유지

### 7.2 키보드 훅 종료
1. 정상 종료:
   - 입력 필드 포커스 상실 시
   - 다이얼로그 닫힐 때
   - 확인/취소 버튼 클릭 시

2. 비정상 상황 처리:
   - 예외 발생 시 자동 정리
   - 프로그램 강제 종료 시 정리

## 8. 예외 처리

### 8.1 키 입력 예외
- 잘못된 키 코드 처리
- 시스템 예약 키 처리
- 중복 키 입력 필터링

### 8.2 UI 관련 예외
- NumLock 상태 변경 처리
- 다이얼로그 강제 종료 처리
- 포커스 관련 예외 처리

### 8.3 데이터 예외
- 잘못된 키 정보 형식 처리
- 저장/로드 실패 처리
- 메모리 부족 상황 처리

## 9. 성능 고려사항

### 9.1 키보드 훅 최적화
- 불필요한 이벤트 필터링
- 메모리 사용량 최소화
- 훅 체인 지연 최소화

### 9.2 UI 응답성
- 비동기 처리 활용
- 긴 작업 분할 처리
- 화면 갱신 최적화
