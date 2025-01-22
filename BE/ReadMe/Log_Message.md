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
