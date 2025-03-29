"""
스크롤 가능한 메뉴 모듈

이 모듈은 스크롤 가능한 메뉴 컨트롤을 제공합니다.
항목이 많은 메뉴에서 모든 항목을 스크롤하여 볼 수 있습니다.
"""

from PyQt5.QtWidgets import QMenu, QApplication  # 메뉴 관련 위젯
from PyQt5.QtCore import Qt  # Qt 기본 기능

class ScrollableMenu(QMenu):
    """
    스크롤 가능한 메뉴 클래스예요.
    
    일반 메뉴와 달리 항목이 많을 때 스크롤바가 나타나서
    모든 항목을 볼 수 있어요. 북마크 메뉴 등에 사용해요.
    """
    def __init__(self, parent=None):
        """
        스크롤 가능한 메뉴 초기화
        
        매개변수:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 스크롤 지원을 위한 설정
        self.setProperty("_q_scrollable", True)
        # 최대 높이 제한 - 항목을 더 많이 표시하기 위해 높이 증가
        self.setMaximumHeight(800)
        self.setStyleSheet("""
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                padding: 5px;
                min-width: 300px;
                max-height: 800px;
            }
            QMenu::item {
                padding: 3px 20px 3px 20px;  /* 패딩 줄여서 항목 높이 감소 */
                border: 1px solid transparent;
                color: #ecf0f1;
                max-width: 600px;
                font-size: 9pt;  
            }
            QMenu::item:selected {
                background-color: #34495e;
                color: #ecf0f1;
            }
            QMenu::separator {
                height: 1px;
                background: #34495e;
                margin: 3px 0; 
            }
            QMenu::item:disabled {
                color: #7f8c8d;
            }
            QScrollBar:vertical {
                background: #2c3e50;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #34495e;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
    
    def wheelEvent(self, event):
        """
        마우스 휠 이벤트 처리
        
        메뉴 내용을 스크롤할 수 있게 해줘요.
        
        매개변수:
            event: 휠 이벤트 정보
        """
        # 마우스 휠 이벤트 처리
        super().wheelEvent(event)
        # 이벤트가 처리되었음을 표시
        event.accept()
        
    def showEvent(self, event):
        """
        메뉴가 표시될 때 호출되는 이벤트
        
        메뉴가 화면에 나타날 때 스크롤 속성을 설정해요.
        
        매개변수:
            event: 표시 이벤트 정보
        """
        # 메뉴가 표시될 때 호출되는 이벤트
        super().showEvent(event)
        # 스크롤을 지원하도록 다시 설정
        self.setProperty("_q_scrollable", True)
        # 스타일시트 재적용
        self.setStyle(self.style())
        
        # 화면 크기에 맞게 최대 높이 조절
        desktop = QApplication.desktop().availableGeometry()
        self.setMaximumHeight(min(800, desktop.height() * 0.7))
    
    def addMultipleActions(self, actions):
        """
        여러 액션을 메뉴에 한번에 추가해요.
        
        많은 항목을 추가할 때 스크롤바가 자동으로 나타나요.
        
        매개변수:
            actions: 추가할 액션 목록
        """
        for action in actions:
            self.addAction(action)
        
        # 액션이 많으면 스크롤 속성을 다시 설정
        if len(actions) > 7:
            self.setProperty("_q_scrollable", True)
            self.setStyle(self.style()) 