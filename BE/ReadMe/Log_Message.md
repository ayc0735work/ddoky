# 로그 메시지 시스템 가이드

## 1. 시스템 구조

### 1.1 개요
로그 메시지 시스템은 중앙 집중식 로그 관리를 통해 애플리케이션의 모든 로그를 체계적으로 관리합니다.

### 1.2 주요 컴포넌트
1. **ModalLogManager** (BE/log/manager/modal_log_manager.py)
   - 로그 메시지의 중앙 관리자
   - 싱글톤 패턴으로 구현
   - 로그 레벨, 시간, 출처 정보 관리

2. **LogWidget** (BE/log/widget/log_widget.py)
   - 로그 메시지 표시 UI
   - 로그 초기화, 스크롤 기능 제공

## 2. 구현 방법

### 2.1 기본 설정

#### 2.1.1 필요한 import
```python
from BE.log.manager.modal_log_manager import ModalLogManager
```

#### 2.1.2 클래스에서 초기화
```python
class YourClass:
    def __init__(self):
        self.modal_log_manager = ModalLogManager.instance()
```

### 2.2 MainWindow에서의 설정 (최초 1회만 하면 됨)
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 모달 로그 매니저 초기화 및 연결
        self.modal_log_manager = ModalLogManager.instance()
        self.modal_log_manager.add_handler(self._append_log)
```

## 3. 로그 메시지 작성 가이드

## 기본 형식
모든 로그 메시지는 다음 형식을 따릅니다:
```
[날짜 시간] [레벨] [모달이름] 메시지
```
예시:
```
[2024-01-01 12:34:56] [INFO] [키입력모달] 키 입력이 완료되었습니다
```

## 시간 추적이 필요한 로그 형식
특정 작업의 경과 시간을 추적해야 하는 경우 다음 형식을 사용합니다:
```
[날짜 시간] [경과시간] [레벨] [모달이름] 메시지
```
예시:
```
[2024-01-01 12:34:56] [1.2345초] [INFO] [로직실행] 로직 실행을 시작합니다
```

## 로그 레벨 사용 지침
- INFO: 일반적인 정보성 메시지
  - 예: 로직 실행 시작/완료, 설정 변경, 상태 업데이트
- DEBUG: 디버깅에 필요한 상세 정보
  - 예: 변수값 변경, 함수 호출 추적, 상세 처리 과정
- WARNING: 잠재적 문제 상황
  - 예: 예상치 못한 입력값, 성능 저하 가능성
- ERROR: 오류 발생 상황
  - 예: 예외 발생, 필수 데이터 누락, 처리 실패

## 시간 추적이 필요한 메시지 유형
다음 상황에서는 경과 시간을 포함해야 합니다:

1. 로직 실행 관련
   - 로직 실행 시작/완료
   - 중첩 로직 실행
   - 반복 완료
   - 스텝 실행

2. 사용자 입력 관련
   - 키 입력/해제
   - 마우스 클릭/이동
   - 텍스트 입력

3. 대기 및 지연
   - 지연시간 처리
   - 클릭 대기
   - 이미지 검색 대기

4. 상태 변경
   - 강제 중지
   - 타이머 정리
   - 키 상태 정리
   - 프로세스 상태 변경

## 사용 예시
```python
# 타이머 시작
modal_log_manager.start_timer("로직실행")

# 시간 정보 포함 로그
modal_log_manager.log(
    message="로직 실행을 시작합니다",
    level="INFO",
    modal_name="로직실행",
    include_time=True
)

# 일반 로그
modal_log_manager.log(
    message="설정을 불러왔습니다",
    level="DEBUG",
    modal_name="로직실행"
)

# 경고 로그
modal_log_manager.log(
    message="지연시간이 예상보다 깁니다",
    level="WARNING",
    modal_name="로직실행"
)

# 에러 로그
modal_log_manager.log(
    message="프로세스 접근 권한이 없습니다",
    level="ERROR",
    modal_name="로직실행"
)

# 작업 완료 후 타이머 정지
modal_log_manager.stop_timer("로직실행")
```

## 주의사항
1. 모든 로그는 명확하고 간결해야 합니다
2. 시간 추적이 필요한 경우에만 include_time을 True로 설정합니다
3. 모달 이름은 일관성 있게 사용합니다
   - 키입력모달
   - 로직실행
   - 로직상세
   - 로직리스트
   - 기타기능
4. 중요한 상태 변경은 반드시 로깅합니다
5. 불필요한 로그는 피하고, 중요한 정보만 기록합니다
6. 개인정보나 민감한 데이터는 로그에 포함하지 않습니다

## 4. 모달 이름 규칙

### 4.1 기본 규칙
- 한글 사용
- "모달" 접미사 포함
- 띄어쓰기 없이 작성

### 4.2 예시
```python
modal_name="키입력모달"     # 좋음
modal_name="설정모달"       # 좋음
modal_name="dialog1"       # 나쁨
modal_name="key input"     # 나쁨
```

### 4.3 계층 구조 표현
```python
modal_name="설정모달/일반"     # 설정 모달의 일반 섹션
modal_name="설정모달/고급"     # 설정 모달의 고급 섹션
```

## 5. 로그 출력 형식

### 5.1 기본 형식
```
[시간] [레벨] [모달이름] 메시지
```

### 5.2 출력 예시
```
[2024-01-01 12:34:56] [INFO] [키입력모달] 키 입력이 완료되었습니다.
[2024-01-01 12:34:57] [WARNING] [설정모달] 변경사항이 저장되지 않았습니다.
[2024-01-01 12:34:58] [ERROR] [저장모달] 파일 저장 실패: 권한 없음
```

## 6. 효율성과 장점

### 6.1 중앙 집중식 관리
- 모든 로그를 한 곳에서 관리
- 일관된 형식 보장
- 로그 필터링 용이

### 6.2 메모리 효율성
- 버퍼 크기 제한 (기본 1000개)
- 오래된 로그 자동 제거
- 필요한 경우만 로그 저장

### 6.3 디버깅 용이성
- 시간 정보 자동 기록
- 출처 추적 가능
- 로그 레벨별 분류

### 6.4 확장성
- 새로운 로그 핸들러 추가 가능
- 로그 저장 기능 확장 가능
- 필터링 시스템 도입 가능

## 7. 사용 예시

### 7.1 기본적인 사용
```python
class MyModal(QDialog):
    def __init__(self):
        super().__init__()
        self.modal_log_manager = ModalLogManager.instance()
        
    def process_data(self):
        try:
            # 작업 수행
            self.modal_log_manager.log(
                message="데이터 처리가 완료되었습니다.",
                level="INFO",
                modal_name="처리모달"
            )
        except Exception as e:
            self.modal_log_manager.log(
                message=f"오류 발생: {str(e)}",
                level="ERROR",
                modal_name="처리모달"
            )
```

### 7.2 복잡한 로그 메시지
```python
def handle_process_result(self, result):
    status = "성공" if result.success else "실패"
    color = "green" if result.success else "red"
    
    self.modal_log_manager.log(
        message=(
            f"처리 결과:<br>"
            f"- 상태: <span style='color: {color}'>{status}</span><br>"
            f"- 처리 항목: {result.items_processed}개<br>"
            f"- 소요 시간: {result.duration}초"
        ),
        level="INFO",
        modal_name="결과모달"
    )
```
