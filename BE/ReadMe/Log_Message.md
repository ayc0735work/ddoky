# 로그 메시지 시스템 가이드

## 1. 로그 메시지 시스템 개요

### 1.1 구조
로그 메시지 시스템은 크게 세 부분으로 구성됩니다:
1. 로그 메시지 발신자 (컨트롤러, 위젯 등)
2. 로그 메시지 중계자 (MainWindow)
3. 로그 메시지 수신자 (LogWidget)

### 1.2 동작 흐름
1. 각 컴포넌트에서 `log_message` 시그널을 발생시킴
2. MainWindow가 시그널을 받아서 LogWidget으로 전달
3. LogWidget이 메시지를 화면에 표시

## 2. 로그 메시지 구현 방법

### 2.1 컴포넌트에 로그 메시지 기능 추가하기

#### 2.1.1 시그널 정의 - 컨트롤러의 경우
```python
from PySide6.QtCore import Signal, QObject

class YourController(QObject): # 컨트롤러는 반드시 QObject를 상속해야 함
    log_message = Signal(str)  # 로그 메시지 시그널 정의
```

#### 2.1.2 시그널 정의 - 위젯의 경우
```python
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Signal

class YourWidget(QFrame):  # QWidget, QFrame 등은 이미 QObject를 상속하고 있음
    log_message = Signal(str)  # 로그 메시지 시그널 정의
```

#### 2.1.3 로그 메시지 발생시키기
```python
class YourController(QObject):
    def some_method(self):
        self.log_message.emit("로그 메시지 내용")
```

### 2.2 MainWindow에서 로그 메시지 연결하기

```python
def _setup_connections(self):
    # 컴포넌트의 log_message 시그널을 _append_log 메서드에 연결
    your_component.log_message.connect(self._append_log)
```

## 3. 로그 메시지 사용 가이드

### 3.1 기본 텍스트 로그
```python
self.log_message.emit("기본 로그 메시지입니다.")
```

### 3.2 HTML 형식 로그
```python
# 굵은 텍스트
self.log_message.emit("<b>중요한 메시지입니다</b>")

# 색상이 있는 텍스트
self.log_message.emit("<span style='color: red'>경고 메시지입니다</span>")

# 줄바꿈
self.log_message.emit("첫 번째 줄<br>두 번째 줄")
```

### 3.3 로그 메시지 작성 규칙
1. 메시지는 명확하고 간단하게 작성
2. 중요한 정보는 HTML 태그를 사용하여 강조
3. 오류 메시지는 빨간색으로 표시
4. 긴 메시지는 줄바꿈(`<br>`)을 사용하여 가독성 확보

### 3.4 로그 레벨 사용 가이드
로그 레벨은 메시지의 중요도와 성격을 나타냅니다:

1. **INFO** (일반 정보)
   - 일반적인 작업의 성공적인 완료
   - 사용자 동작에 대한 피드백
   - 시스템 상태 변경 알림
   ```python
   ModalLogManager.instance().log(
       message="설정이 저장되었습니다.",
       level="INFO",
       modal_name="설정모달"
   )
   ```

2. **WARNING** (경고)
   - 잠재적인 문제 상황
   - 사용자 주의가 필요한 상황
   - 권장되지 않는 동작 수행
   ```python
   ModalLogManager.instance().log(
       message="NumLock이 켜져 있어 키 동작이 달라질 수 있습니다.",
       level="WARNING",
       modal_name="키입력모달"
   )
   ```

3. **ERROR** (오류)
   - 작업 실패
   - 예외 발생
   - 시스템 오류
   ```python
   ModalLogManager.instance().log(
       message="파일 저장 중 오류가 발생했습니다.",
       level="ERROR",
       modal_name="저장모달"
   )
   ```

4. **DEBUG** (디버깅)
   - 개발자용 상세 정보
   - 문제 해결을 위한 정보
   - 시스템 내부 상태
   ```python
   ModalLogManager.instance().log(
       message="키 입력 처리 - scanCode: 65, virtualKey: 0x41",
       level="DEBUG",
       modal_name="키입력모달"
   )
   ```

### 3.5 모달 이름 지정 규칙
모달 이름은 로그의 출처를 명확히 하기 위해 사용됩니다:

1. **명명 규칙**
   - 간단하고 명확한 이름 사용
   - 모달의 목적을 반영
   - "모달" 접미사 포함
   ```python
   modal_name="키입력모달"    # 좋은 예
   modal_name="설정모달"      # 좋은 예
   modal_name="dialog1"      # 피해야 할 예
   ```

2. **일관성 유지**
   - 동일한 모달은 항상 같은 이름 사용
   - 한글 사용 권장
   - 띄어쓰기 없이 작성

3. **계층 구조 표현** (필요한 경우)
   ```python
   modal_name="설정모달/키설정"    # 설정 모달 내의 키 설정 섹션
   modal_name="설정모달/마우스설정" # 설정 모달 내의 마우스 설정 섹션
   ```

### 3.6 로그 출력 형식
```
[시간] [레벨] [모달이름] 메시지

예시:
[2024-01-01 12:34:56] [INFO] [키입력모달] 키 입력이 완료되었습니다.
[2024-01-01 12:34:57] [WARNING] [키입력모달] NumLock이 켜져 있습니다.
[2024-01-01 12:34:58] [ERROR] [키입력모달] 키 입력 처리 중 오류가 발생했습니다.
```

## 4. LogWidget 기능 사용하기

### 4.1 로그 초기화
- "초기화" 버튼 클릭
- 프로그래밍 방식: `log_widget.clear_log()`

### 4.2 스크롤 제어
- "맨 위로" 버튼: 로그의 처음으로 이동
- "맨 아래로" 버튼: 로그의 끝으로 이동
- 프로그래밍 방식:
  ```python
  log_widget.scroll_to_top()     # 맨 위로
  log_widget.scroll_to_bottom()  # 맨 아래로
  ```

## 5. 실제 사용 예시

### 5.1 컨트롤러에서 로그 메시지 발생
```python
# LogicDetailController 예시
class LogicDetailController:
    def _handle_item_moved(self):
        self.log_message.emit("로직 구성 순서가 변경되었습니다.")
```

### 5.2 위젯에서 로그 메시지 발생
```python
# LogicDetailWidget 예시
class LogicDetailWidget:
    def add_item(self, item):
        self.log_message.emit(f"새로운 아이템이 추가되었습니다: {item}")
```

### 5.3 오류 처리와 로그
```python
try:
    # 작업 수행
    pass
except Exception as e:
    self.log_message.emit(f"<span style='color: red'>오류 발생: {str(e)}</span>")
```

## 6. 주의사항

### 6.1 로그 메시지 작성 시 주의사항
1. 불필요한 로그 메시지 남발 금지
2. 민감한 정보(비밀번호 등) 포함 금지
3. HTML 태그 사용 시 올바른 닫힘 태그 확인
4. 메시지는 한글로 작성하여 가독성 확보

### 6.2 성능 관련 주의사항
1. 대량의 로그 메시지 발생 시 성능 저하 가능
2. 로그 메시지는 필요한 경우에만 발생
3. HTML 태그는 필요한 경우에만 사용

## 7. 로그 메시지 예시 모음

### 7.1 일반 정보 로그
```python
self.log_message.emit("설정이 저장되었습니다.")
```

### 7.2 경고 로그
```python
self.log_message.emit("<span style='color: orange'>경고: 저장되지 않은 변경사항이 있습니다.</span>")
```

### 7.3 오류 로그
```python
self.log_message.emit("<span style='color: red'>오류: 파일을 저장할 수 없습니다.</span>")
```

### 7.4 성공 로그
```python
self.log_message.emit("<span style='color: green'>성공: 작업이 완료되었습니다.</span>")
```

### 7.5 복합 로그
```python
self.log_message.emit(
    "작업 결과:<br>" +
    "- 성공: <span style='color: green'>3건</span><br>" +
    "- 실패: <span style='color: red'>1건</span>"
)
```

## 8. 모달 다이얼로그의 로그 메시지 처리

### 8.1 모달 다이얼로그의 특수성
모달 다이얼로그는 일반 위젯과 달리 특별한 처리가 필요합니다:
1. 동적 생성/소멸: 필요할 때만 생성되고 사용 후 제거됨
2. 임시성: 항상 존재하지 않고 일시적으로만 존재
3. 소유권: 다른 위젯에서 사용되지만 로그는 메인 윈도우에 표시

### 8.2 모달 다이얼로그 로그 처리 방법

#### 8.2.1 현재 방식 (개별 처리)
```python
# MainWindow에서
def show_modal_dialog(self):
    dialog = ModalDialog(self)
    dialog.log_message.connect(self._append_log)
    return dialog

# 사용하는 곳에서
dialog = self.parent().show_modal_dialog()
if dialog.exec() == QDialog.Accepted:
    # 처리
    pass
```

#### 8.2.2 제안되는 개선 방식 (중앙 집중식)
```python
# modal_log_handler.py
class ModalLogHandler:
    def __init__(self):
        self.modal_logs = []
        self.log_updated = Signal(str)
    
    def handle_modal_log(self, message):
        self.modal_logs.append(message)
        self.log_updated.emit(message)

# MainWindow에서
self.modal_log_handler = ModalLogHandler()
self.modal_log_handler.log_updated.connect(self._append_log)

# 모달에서
self.parent().modal_log_handler.handle_modal_log("메시지")
```

### 8.3 모달 로그 처리 시 주의사항
1. 메모리 관리
   - 모달이 닫힐 때 시그널 연결 해제 필요
   - 불필요한 로그 데이터 정리

2. 로그 동기화
   - 여러 모달이 동시에 열릴 경우 로그 순서 보장
   - 로그 중복 방지

3. 성능 고려
   - 로그 버퍼링 검토
   - 대량의 로그 발생 시 처리 방안

### 8.4 구현 예시

#### 8.4.1 기본 구현
```python
class BaseModalDialog(QDialog):
    log_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        if hasattr(parent, '_append_log'):
            self.log_message.connect(parent._append_log)
```

#### 8.4.2 중앙 집중식 구현
```python
class ModalLogManager:
    _instance = None
    
    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.handlers = []
    
    def add_handler(self, handler):
        self.handlers.append(handler)
    
    def log(self, message, level="INFO"):
        for handler in self.handlers:
            handler(message, level)
```

## 9. 향후 개선 방향

### 9.1 로그 처리 구조 개선
1. 모달 로그 전용 핸들러 구현
2. 로그 레벨 세분화
3. 로그 필터링 기능 추가

### 9.2 성능 최적화
1. 로그 버퍼링 메커니즘 도입
2. 비동기 로그 처리
3. 로그 압축 저장

### 9.3 사용성 개선
1. 로그 검색 기능
2. 로그 필터링 UI
3. 로그 내보내기 기능
