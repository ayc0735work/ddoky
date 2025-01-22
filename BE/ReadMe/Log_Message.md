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

### 3.1 기본 로그 출력
```python
self.modal_log_manager.log(
    message="작업이 완료되었습니다.",
    level="INFO",
    modal_name="작업모달"
)
```

### 3.2 로그 레벨
1. **INFO**: 일반적인 정보
   ```python
   self.modal_log_manager.log(
       message="설정이 저장되었습니다.",
       level="INFO",
       modal_name="설정모달"
   )
   ```

2. **WARNING**: 주의가 필요한 상황
   ```python
   self.modal_log_manager.log(
       message="저장되지 않은 변경사항이 있습니다.",
       level="WARNING",
       modal_name="편집모달"
   )
   ```

3. **ERROR**: 오류 상황
   ```python
   self.modal_log_manager.log(
       message="파일 저장 중 오류가 발생했습니다.",
       level="ERROR",
       modal_name="저장모달"
   )
   ```

4. **DEBUG**: 개발/디버깅용 정보
   ```python
   self.modal_log_manager.log(
       message="함수 호출 - 매개변수: value=42",
       level="DEBUG",
       modal_name="처리모달"
   )
   ```

### 3.3 HTML 형식 사용
```python
self.modal_log_manager.log(
    message=(
        f"처리 결과:<br>"
        f"- 성공: <span style='color: green'>3건</span><br>"
        f"- 실패: <span style='color: red'>1건</span>"
    ),
    level="INFO",
    modal_name="결과모달"
)
```

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
