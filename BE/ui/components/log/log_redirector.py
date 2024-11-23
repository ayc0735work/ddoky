import sys

class LogRedirector:
    """표준 출력을 로그 위젯으로 리다이렉트하는 클래스"""
    
    def __init__(self, text_widget):
        """
        Args:
            text_widget (QTextEdit): 로그를 표시할 텍스트 위젯
        """
        self.text_widget = text_widget
        self.original_stdout = sys.stdout

    def write(self, text):
        """
        텍스트를 터미널과 로그 위젯에 출력
        
        Args:
            text (str): 출력할 텍스트
        """
        self.original_stdout.write(text)  # 터미널에도 출력
        if text.strip():  # 빈 줄이 아닌 경우에만 출력
            self.text_widget.append(text.rstrip())  # 오른쪽 공백과 줄바꿈 제거

    def flush(self):
        """버퍼 플러시"""
        self.original_stdout.flush()
