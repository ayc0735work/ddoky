# 로그 메시지 시스템 가이드

## 1. 시스템 구조

### 1.1 개요
로그 메시지 시스템은 중앙 집중식 로그 관리를 통해 애플리케이션의 모든 로그를 체계적으로 관리합니다.

### 1.2 주요 컴포넌트
1. **BaseLogManager** (BE/log/base_log_manager.py)
   - 로그 메시지의 중앙 관리자
   - 싱글톤 패턴으로 구현
   - 로그 레벨, 시간, 출처 정보 관리
   - 터미널 출력 기능 지원

2. **LogWidget** (BE/log/widget/log_widget.py)
   - 로그 메시지 표시 UI
   - 로그 초기화, 스크롤 기능 제공

## 2. 구현 방법

### 2.1 기본 설정

#### 2.1.1 필요한 import
```python
from BE.log.manager.base_log_manager import BaseLogManager
```

#### 2.1.2 클래스에서 초기화
```python
class YourClass:
    def __init__(self):
        self.base_log_manager = BaseLogManager.instance()
```

### 2.2 로그 메시지 작성 가이드

#### 2.2.1 기본 로그 형식
```
[날짜 시간] [레벨] [파일 이름] [메서드이름] 메시지
```
예시:
```
[2024-01-01 12:34:56] [INFO] [base_log_manager] [process_key_input] 키 입력이 완료되었습니다
```

#### 2.2.2 시간 추적이 필요한 로그 형식
```
[날짜 시간] [경과시간] [레벨] [파일 이름] [메서드이름] 메시지
```
예시:
```
[2024-01-01 12:34:56] [1.2345초] [INFO] [base_log_manager] [execute_logic] 로직 실행을 시작합니다
```

#### 2.2.3 로그 레벨 사용 지침
- **INFO**: 일반적인 정보성 메시지
  - 예: 로직 실행 시작/완료, 설정 변경, 상태 업데이트
- **DEBUG**: 디버깅에 필요한 상세 정보
  - 예: 변수값 변경, 함수 호출 추적, 상세 처리 과정
- **WARNING**: 잠재적 문제 상황
  - 예: 예상치 못한 입력값, 성능 저하 가능성
- **ERROR**: 오류 발생 상황
  - 예: 예외 발생, 필수 데이터 누락, 처리 실패, 에러 로그는 터미널에도 함께 출력하는 것을 권고

#### 2.2.4 터미널 출력 옵션
터미널 출력과 관련하여 두 가지 옵션을 제공합니다:

1. **일반 터미널 출력 (print_to_terminal)**
   - 로그를 터미널과 로그 영역 모두에 출력
   - 중요한 시스템 이벤트나 오류 상황에서 사용

2. **터미널 전용 출력 (print_only_terminal)**
   - 로그를 터미널에만 출력하고 로그 영역에는 표시하지 않음
   - 디버깅이나 임시 출력이 필요한 경우 사용
   - 로그 버퍼에 저장되지 않음

### 2.3 사용 예시
```python
# 일반 로그 (메서드 이름 포함)
self.base_log_manager.log(
    message="설정이 변경되었습니다",
    level="INFO",
    file_name="base_log_manager",
    method_name="add_handler"
)

# 시간 추적이 필요한 로그
self.base_log_manager.log(
    message="로직 실행을 시작합니다",
    level="INFO",
    file_name="base_log_manager",
    method_name="remove_handler",
    include_time=True
)

# 터미널 출력이 필요한 로그
self.base_log_manager.log(
    message="중요한 오류가 발생했습니다",
    level="ERROR",
    file_name="base_log_manager",
    method_name="start_timer",
    print_to_terminal=True
)

# 터미널에만 출력하는 로그
self.base_log_manager.log(
    message="디버그 정보: 변수 값 = 42",
    level="DEBUG",
    file_name="base_log_manager",
    method_name="reset_timer",
    print_only_terminal=True
)
```

### 2.4 파일 이름 규칙
- 현재 파일의 이름을 확장자 빼고 파일 이름만 작성
   예시) BE\function\manage_logic\logic_manager.py 파일이라면 file_name은 logic_manager

### 2.5 주의사항
1. 모든 로그는 명확하고 간결하게 작성
2. 시간 추적이 필요한 경우에만 `include_time=True` 사용
3. 터미널 출력은 중요한 이벤트에만 `print_to_terminal=True` 사용
4. 터미널 전용 출력(`print_only_terminal=True`)은 디버깅 목적으로만 사용
5. 메서드 이름은 실제 호출된 메서드나 함수의 이름을 사용
6. 파일 이름은 확장자 빼고 파일 이름만 작성
7. 개인정보나 민감한 데이터는 로그에 포함하지 않음
8. HTML 스타일 태그는 UI 표시용으로만 사용
8. 에러 로그는 터미널에도 함께 출력하는 것을 권고

## 3. 로그 관리

### 3.1 버퍼 관리
- 최대 10000개의 로그 메시지 저장
- 버퍼 초과 시 가장 오래된 로그 자동 제거

### 3.2 시간 관리
- 각 모달별 독립적인 타이머 관리
- 시작, 정지, 리셋 기능 제공
- 경과 시간 밀리초 단위로 표시
