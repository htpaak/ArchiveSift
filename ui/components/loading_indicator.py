"""
로딩 인디케이터 모듈

이 모듈은 로딩 중임을 표시하는 인디케이터를 제공합니다.
이미지나 비디오가 로딩될 때 사용자에게 시각적인 피드백을 제공합니다.
"""

from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QMovie


class LoadingIndicator(QLabel):
    """
    로딩 인디케이터 클래스
    
    로딩 중임을 표시하는 애니메이션 라벨입니다.
    """
    
    def __init__(self, parent=None):
        """
        로딩 인디케이터 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        
        # 기본 설정
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
        """)
        
        # 애니메이션 로딩
        self.movie = QMovie("ui/resources/loading.gif")
        if not self.movie.isValid():
            # 기본 리소스가 없는 경우 내장 표시
            self.setText("Loading...")
            self.setStyleSheet("""
                background-color: rgba(0, 0, 0, 0.5);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                padding: 20px;
            """)
        else:
            # 애니메이션 설정
            self.movie.setScaledSize(QSize(64, 64))
            self.setMovie(self.movie)
        
        # 초기 상태: 숨김
        self.hide()
    
    def start_animation(self):
        """
        애니메이션 시작 및 표시
        """
        if self.movie.isValid():
            self.movie.start()
        self.show()
        self.raise_()  # 항상 맨 위에 표시
    
    def stop_animation(self):
        """
        애니메이션 정지 및 숨김
        """
        if self.movie.isValid():
            self.movie.stop()
        self.hide()
    
    def reset(self):
        """
        인디케이터 초기화
        """
        if self.movie.isValid():
            self.movie.stop()
            self.movie.start()
        self.raise_()
    
    def reposition(self, parent_width, parent_height):
        """
        부모 위젯 크기에 맞게 위치 조정
        
        Args:
            parent_width: 부모 위젯의 너비
            parent_height: 부모 위젯의 높이
        """
        # 중앙 위치 계산
        indicator_width = 100  # 기본 인디케이터 너비
        indicator_height = 100  # 기본 인디케이터 높이
        
        x = (parent_width - indicator_width) // 2
        y = (parent_height - indicator_height) // 2
        
        # 위치 및 크기 설정
        self.setGeometry(x, y, indicator_width, indicator_height) 