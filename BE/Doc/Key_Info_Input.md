# 키 입력 처리 흐름 문서

## 1. 개요
이 문서는 키 입력이 감지되는 순간부터 아이템 목록 상자에 표시되기까지의 전체 과정을 상세하게 설명합니다.

### 1.1 전체 흐름도
```
[사용자 키 입력] → [키보드 훅] → [키 정보 구조화] → [상태 정보 생성] → [시그널 전파] → [UI 표시]
     ↓                 ↓              ↓                  ↓                ↓              ↓
  버튼 클릭 → 모달 다이얼로그 → 데이터 포맷팅 → 누르기/떼기 변환 → 위젯 간 통신 → 목록 상자 표시
```

### 1.2 주요 컴포넌트 역할
- **키 입력 모달**: 사용자의 키 입력을 받고 표시
- **키보드 훅**: 저수준 키보드 이벤트 캡처
- **키 정보 핸들러**: 키 정보 가공 및 전달
- **로직 메이커**: 키 입력 정보 중계 및 관리, UI 표시 담당
- **로직 상세**: 최종 UI 표시 및 사용자 상호작용

## 2. 파일 구조 및 역할
```
BE/function/
├── _common_components/modal/entered_key_info_modal/
│   ├── entered_key_info_dialog.py     # 키 입력 모달 다이얼로그 (키 입력 UI 및 입력 처리)
│   ├── entered_key_info_widget.py     # 키 입력 UI 위젯 (키 입력 표시 및 상세 정보 표시)
│   └── keyboard_hook_handler.py       # 키보드 훅 처리기 (저수준 키보드 이벤트 캡처)
├── make_logic/logic_maker_tool/
│   ├── logic_maker_tool_widget.py     # 로직 메이커 도구 위젯 (키 입력 UI 처리 및 중계자)
│   └── handlers/
│       └── entered_key_info_handler.py # 키 입력 정보 핸들러 (키 정보 가공 및 전달)
└── make_logic/logic_detail/
    └── logic_detail_widget.py         # 로직 상세 위젯 (최종 UI 표시 담당)
```

### 2.1 파일 간 상호작용
```
[entered_key_info_dialog.py] ←→ [entered_key_info_widget.py]
           ↑                         ↑
           └─────── [keyboard_hook_handler.py]
                         ↑
[logic_maker_tool_widget.py] ←→ [entered_key_info_handler.py]
           ↓
[logic_detail_widget.py]
```

## 3. 키 입력 처리 상세 흐름

### 3.1 키 입력 시작 단계
1. 사용자가 `LogicMakerToolWidget`의 "키 입력 추가" 버튼 클릭
   - 버튼 위치: 로직 메이커 도구 위젯의 상단
   - 버튼 상태: 활성화 (다른 모달이 열려있지 않은 경우)

2. `LogicMakerToolWidget._request_key_to_input()` 메서드 호출
   - 키 입력 다이얼로그 생성 및 표시
   - 모달 형태로 화면에 표시
   - 기존 UI와의 상호작용 차단
   - 사용자 입력 대기

3. 모달 다이얼로그 초기화
   - 키 입력 영역 포커스 설정
   - 안내 메시지 표시
   - ESC 키 처리 방지 설정

### 3.2 키보드 입력 감지 단계
1. 사용자가 `EnteredKeyInfoWidget`의 입력 필드 클릭
   - 입력 필드 강조 표시
   - 키 입력 대기 상태 표시

2. `key_input_area_focused` 시그널 발생
   - 포커스 상태 변경 알림
   - 키보드 훅 시작 준비

3. `EnteredKeyInfoDialog._start_keyboard_hook()` 호출
   - 이전 훅 정리 (있는 경우)
   - 새로운 훅 초기화 준비

4. `KeyboardHook` 인스턴스 생성 및 시작
   - Windows API의 저수준 키보드 훅 설정
   - WH_KEYBOARD_LL 훅 타입 사용
   - 훅 체인에 등록

5. Windows API를 통해 키보드 이벤트 감지
   - 이벤트 종류:
     * 가상 키 코드(virtual key code): 키의 논리적 식별자
     * 스캔 코드(scan code): 물리적 키 위치 값
     * 확장 키 플래그(extended key flag): 특수 키 구분
     * 컨텍스트 코드(context code): 키 상태 정보
     * 이전 키 상태(previous key state): 이전 상태 값
     * 트랜지션 상태(transition state): 상태 변화 정보

6. 이벤트 필터링
   - 시스템 예약 키 처리
   - 중복 이벤트 제거
   - 유효하지 않은 키 코드 필터링

### 3.3 키 정보 초기 구조화 단계
키보드 훅에서 감지된 정보를 다음 구조로 변환:
```python
{
    # 기본 키 정보
    'key_code': str,        # 키의 표시 이름 (예: 'Space')
    'scan_code': int,       # 하드웨어 키보드의 물리적 위치 값 (예: 57)
    'virtual_key': int,     # Windows API 가상 키 코드 (예: 32)
    
    # 수정자 키 정보
    'modifiers': int,       # Qt 기반 수정자 키 상태 (예: KeyboardModifier.NoModifier)
    'modifier_text': str,   # 수정자 키 텍스트 (예: '없음', 'Ctrl + Alt')
    
    # 위치 및 상태 정보
    'location': str,        # 키보드 위치 (예: '메인', '숫자패드')
    'is_system_key': bool,  # ALT 키 눌림 여부
    'is_numpad': bool,      # 숫자 패드 키 여부
    
    # 표시 정보
    'simple_display_text': str,  # UI 표시용 텍스트 (예: 'Space')
    'detail_display_text': str   # 상세 정보 표시용 텍스트
}
```

#### 3.3.1 필드별 상세 설명
1. **기본 키 정보**
   - `key_code`: 사용자가 읽을 수 있는 키 이름
   - `scan_code`: 하드웨어 수준의 키 식별 코드
   - `virtual_key`: 운영체제 수준의 키 식별 코드

2. **수정자 키 정보**
   - `modifiers`: Ctrl, Alt, Shift 등의 조합 상태
   - `modifier_text`: 수정자 키 조합의 텍스트 표현

3. **위치 및 상태 정보**
   - `location`: 키보드 상의 물리적 위치 구분
   - `is_system_key`: 시스템 키 여부 (ALT 조합)
   - `is_numpad`: 숫자 패드 영역 키 여부

4. **표시 정보**
   - `simple_display_text`: 간단한 UI 표시용
   - `detail_display_text`: 상세 정보 표시용

### 3.4 키 정보 확인 및 전달 단계
1. 사용자가 "입력된 키 정보 저장" 버튼 클릭
   - 버튼 상태: 키 입력이 있는 경우만 활성화
   - 클릭 시 시각적 피드백 제공

2. `EnteredKeyInfoDialog._on_confirm()` 호출
   - 현재 저장된 키 정보 유효성 검사
     * 필수 필드 존재 확인
     * 값 형식 검증
     * 범위 검증
   - 키 정보를 `EnteredKeyInfoHandler`로 전달
     * 깊은 복사로 전달
     * 원본 데이터 보존

3. `EnteredKeyInfoHandler.handle_confirmed_key_input()` 호출
   - 키 정보를 누르기/떼기 두 가지 상태로 변환
   - 각 상태별로 추가 정보 구성
   - 이벤트 순서 보장

4. 모달 다이얼로그 정리
   - 키보드 훅 해제
   - 리소스 정리
   - UI 상태 복원

### 3.5 키 상태 정보 생성 단계
하나의 키 입력에 대해 두 가지 상태 정보 생성:

#### 3.5.1 누르기 이벤트 정보
```python
key_state_info_press = {
    # 이벤트 타입 정보
    'type': 'key',                # 입력 타입 (키보드)
    'action': '누르기',           # 동작 유형
    
    # 표시 정보
    'display_text': 'Space --- 누르기',  # 목록 표시용 텍스트
    'detail_display_text': 'Space (키 위치: 메인) (스캔코드: 57, 가상키코드: 32, ...)',  # 상세 정보
    
    # 키 식별 정보
    'key_code': 'Space',          # 키 이름
    'scan_code': 57,              # 하드웨어 코드
    'virtual_key': 32,            # 가상 키 코드
    
    # 상태 및 위치 정보
    'modifiers': <KeyboardModifier.NoModifier: 0>,  # 수정자 키 상태
    'location': '메인',           # 키 위치
    'modifier_text': '없음',      # 수정자 키 텍스트
    'is_system_key': False        # 시스템 키 여부
}
```

#### 3.5.2 떼기 이벤트 정보
```python
key_state_info_release = {
    # 이벤트 타입 정보
    'type': 'key',                # 입력 타입 (키보드)
    'action': '떼기',             # 동작 유형
    
    # 표시 정보
    'display_text': 'Space --- 떼기',  # 목록 표시용 텍스트
    'detail_display_text': 'Space (키 위치: 메인) (스캔코드: 57, 가상키코드: 32, ...)',  # 상세 정보
    
    # 키 식별 정보
    'key_code': 'Space',          # 키 이름
    'scan_code': 57,              # 하드웨어 코드
    'virtual_key': 32,            # 가상 키 코드
    
    # 상태 및 위치 정보
    'modifiers': <KeyboardModifier.NoModifier: 0>,  # 수정자 키 상태
    'location': '메인',           # 키 위치
    'modifier_text': '없음',      # 수정자 키 텍스트
    'is_system_key': False        # 시스템 키 여부
}
```

### 3.6 시그널 전파 단계
1. `EnteredKeyInfoHandler`에서 각 상태 정보에 대해:
   ```python
   # 누르기 이벤트 전파
   self.confirmed_and_added_key_info.emit(key_state_info_press)
   
   # 떼기 이벤트 전파
   self.confirmed_and_added_key_info.emit(key_state_info_release)
   ```

2. `LogicMakerToolWidget._on_key_state_info_added()` 에서 처리:
   ```python
   def _on_key_state_info_added(self, key_state_info):
       # 1. 내부 아이템 리스트에 추가
       self.items.append(key_state_info)
       
       # 2. 다른 위젯들에게 전달
       self.item_added.emit(key_state_info)
       
       # 3. 로그 기록
       self.modal_log_manager.log(
           message=f"키 입력 정보가 추가되었습니다: {key_state_info.get('display_text')}",
           level="INFO",
           modal_name="로직메이커"
       )
   ```

3. 시그널 전파 흐름도:
```
[EnteredKeyInfoHandler]
         ↓
confirmed_and_added_key_info
         ↓
[LogicMakerToolWidget]
         ↓
    item_added
         ↓
[LogicDetailWidget]
```

### 3.7 UI 표시 단계
1. `LogicDetailWidget`에서 `item_added` 시그널 수신
   - 시그널 연결 확인
   - 데이터 유효성 검증

2. 아이템 목록 상자(QListWidget)에 새 아이템 추가:
   - 아이템 순서 계산
     * 현재 목록의 마지막 순서 확인
     * 새 아이템의 순서 결정
   
   - 표시 텍스트 설정
     * 기본 텍스트: `display_text` 사용
     * 툴팁: `detail_display_text` 사용
   
   - 아이템 위젯 생성 및 설정
     * 위젯 스타일 적용
     * 아이콘 설정 (있는 경우)
     * 상호작용 설정 (클릭, 드래그 등)
   
   - 아이템 추가 애니메이션 실행
     * 페이드 인 효과
     * 슬라이드 효과 (설정된 경우)

3. UI 업데이트 최적화
   - 일괄 업데이트 사용
   - 불필요한 재그리기 방지
   - 애니메이션 성능 조정

### 3.8 로그 기록 흐름
각 단계별 상세 로그:

1. 키 입력 모달 확인 버튼 클릭
   ```
   [INFO] [키입력모달] 키 입력 모달의 확인버튼이 클릭되었습니다.
   ```
   - 시점: 사용자가 확인 버튼 클릭 시
   - 목적: 사용자 액션 기록

2. 키 입력 정보 처리 시작
   ```
   [INFO] [입력된_키_정보_핸들러] 키 입력이 추가되었습니다 [ 
   키: Space, 
   스캔 코드 (하드웨어 고유값): 57, 
   확장 가상 키 (운영체제 레벨의 고유 값): 32, 
   키보드 위치: 메인, 
   수정자 키: 없음 ]
   ```
   - 시점: 키 정보 처리 시작 시
   - 목적: 입력된 키 정보 상세 기록

3. 누르기 이벤트 처리
   ```
   [DEBUG] [로직상세] add_item 시작 - 입력받은 데이터: {...}
   [DEBUG] [로직상세] 딕셔너리 형식의 데이터 처리 시작
   [INFO] [로직상세] 아이템이 성공적으로 추가되었습니다. 위치: 2
   [INFO] [로직상세] 키 입력이 추가되었습니다: Space --- 누르기
   [INFO] [로직메이커] 키 입력 정보가 추가되었습니다: Space --- 누르기
   ```
   - 시점: 누르기 이벤트 처리 과정
   - 목적: 처리 과정 추적 및 디버깅

4. 떼기 이벤트 처리
   ```
   [DEBUG] [입력된_키_정보_핸들러] 키 상태 정보가 업데이트 되었습니다.
   type: key, 
   action: 떼기,
   display_text: Space --- 떼기
   ```
   - 시점: 떼기 이벤트 처리 과정
   - 목적: 이벤트 처리 상태 확인

5. 로그 레벨별 용도
   - DEBUG: 상세 처리 과정 추적
   - INFO: 주요 상태 변경 알림
   - ERROR: 예외 상황

## 4. 특별 처리 사항

### 4.1 중복 처리 방지
1. 동일한 키 이벤트의 중복 처리 방지
   ```python
   if (self.last_key_info and
       self.last_key_info['key_code'] == formatted_key_info['key_code'] and
       self.last_key_info['modifiers'] == formatted_key_info['modifiers']):
       return  # 중복 처리 방지
   ```
   - 목적: 동일 키 이벤트 중복 방지
   - 비교 기준: 키 코드와 수정자 키

2. 시그널 연결의 중복 방지
   - 초기화 시점에만 시그널 연결
   - 연결 상태 추적
   - 불필요한 재연결 방지

3. 데이터 중복 방지
   - 고유 식별자 사용
   - 타임스탬프 활용
   - 해시값 비교

### 4.2 예외 처리
1. 키 정보 형식 검증
   ```python
   if not isinstance(key_state_info, dict):
       self.modal_log_manager.log(
           message="잘못된 형식의 키 정보",
           level="ERROR"
       )
       return
   ```
   - 목적: 잘못된 데이터 형식 차단
   - 조치: 로그 기록 및 처리 중단

2. 필수 필드 검증
   ```python
   required_fields = ['type', 'action', 'key_code']
   if not all(field in key_state_info for field in required_fields):
       self.modal_log_manager.log(
           message="필수 필드 누락",
           level="ERROR"
       )
       return
   ```
   - 목적: 필수 정보 누락 방지
   - 조치: 로그 기록 및 처리 중단

3. 시그널 전달 실패 처리
   - 예외 발생 시 로그 기록
   - UI 상태 복구
   - 사용자에게 오류 알림
   - 재시도 메커니즘 구현

4. 메모리 부족 상황 처리
   - 리소스 정리
   - 임시 데이터 저장
   - 복구 프로세스 실행

### 4.3 로깅 전략
1. 단계별 로그 레벨
   - INFO: 주요 처리 단계
     * 사용자 액션
     * 상태 변경
     * 처리 완료
   
   - DEBUG: 상세 처리 정보
     * 함수 호출
     * 데이터 변환
     * 중간 상태
   
   - ERROR: 예외 상황
     * 유효성 검증 실패
     * 시그널 전달 실패
     * 리소스 부족

2. 컨텍스트 정보 포함
   - 처리 단계 식별자
     * 모듈명
     * 클래스명
     * 함수명
   
   - 입력값/출력값
     * 데이터 구조
     * 값 범위
     * 형식
   
   - 처리 결과
     * 성공/실패 여부
     * 에러 코드
     * 상세 메시지

3. 성능 모니터링
   - 처리 시간 기록
     * 단계별 소요 시간
     * 전체 처리 시간
   
   - 메모리 사용량 추적
     * 할당량
     * 해제량
     * 누수 여부
   
   - 병목 구간 식별
     * 지연 구간
     * 반복 구간
     * 최적화 대상

## 5. 성능 최적화

### 5.1 메모리 관리
1. 키 정보 객체 재사용
   - 객체 풀링 사용
   - 임시 객체 최소화
   - 가비지 컬렉션 최적화

2. 불필요한 복사 최소화
   - 참조 전달 활용
   - 얕은 복사 사용
   - 깊은 복사 최소화

3. 메모리 누수 방지
   - 리소스 해제 보장
   - 순환 참조 방지
   - 메모리 모니터링

### 5.2 시그널 최적화
1. 불필요한 시그널 전파 방지
   - 조건부 시그널 발생
   - 배치 처리 활용
   - 중복 전파 방지

2. 시그널 연결 최적화
   - 적절한 연결 시점
   - 불필요한 연결 해제
   - 연결 상태 관리

3. 대량 데이터 처리
   - 배치 처리 구현
   - 버퍼링 활용
   - 비동기 처리

### 5.3 UI 업데이트 최적화
1. 화면 갱신 최소화
   - 일괄 업데이트 사용
   - 더티 플래그 활용
   - 부분 갱신 구현

2. 애니메이션 성능 조정
   - 프레임 레이트 최적화
   - 하드웨어 가속 활용
   - 리소스 사용량 조절

3. 지연 로딩 활용
   - 필요시점 로딩
   - 백그라운드 로딩
   - 캐시 활용