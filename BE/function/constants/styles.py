# Frame styles
FRAME_STYLE = "QFrame { background: transparent; border: none; }"
CONTAINER_STYLE = """
    QFrame {
        background-color: #f8f8f8;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
"""

# List widget style
LIST_STYLE = """
    QListWidget {
        border: 1px solid #ccc;
        background-color: white;
        border-radius: 4px;
    }
    QListWidget::item {
        height: 30px;
        padding: 5px;
    }
    QListWidget::item:selected {
        background-color: #0078D7;
        color: white;
    }
    QScrollBar:vertical {
        border: none;
        background: #f0f0f0;
        width: 10px;
    }
    QScrollBar::handle:vertical {
        background: #c1c1c1;
        min-height: 30px;
        border-radius: 5px;
    }
    QScrollBar::handle:vertical:hover {
        background: #a8a8a8;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
"""

# Button style
BUTTON_STYLE = """
    QPushButton {
        background-color: #f0f0f0;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: #e0e0e0;
    }
    QPushButton:pressed {
        background-color: #d0d0d0;
    }
"""

# Log text style
LOG_TEXT_STYLE = """
    QTextEdit {
        background-color: white;
        border: none;
        font-family: 'Consolas', monospace;
        font-size: 12px;
        line-height: 0.5;
    }
"""

# Font settings
TITLE_FONT_FAMILY = "Noto Sans CJK KR"
TITLE_FONT_SIZE = 20 # 각 영역 타이틀 폰트 사이즈
SECTION_FONT_SIZE = 14 # 각 영역의 하위 타이틀 폰트 사이즈
ETC_FUNCTION_COUNTDOWN_FONT_SIZE = 14  # 기타 기능 영역의 키 입력 카운트다운 라벨 폰트 사이즈
