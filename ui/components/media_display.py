"""
미디어 표시 모듈

이 모듈은 미디어 표시를 위한 확장된 QLabel 클래스를 제공합니다.
이미지, 애니메이션, 비디오 등 다양한 미디어 형식 표시를 지원합니다.
"""

from PyQt5.QtWidgets import QLabel, QSizePolicy, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QMouseEvent, QWheelEvent


class MediaDisplay(QLabel):
    """
    미디어 표시를 위한 확장된 QLabel 클래스
    
    이미지, GIF, WEBP 애니메이션, 비디오 등 다양한 미디어 콘텐츠를 
    표시하기 위한 확장된 QLabel 위젯입니다.
    
    신호(Signals):
        mouseDoubleClicked: 더블 클릭 이벤트 발생 시 신호
        mouseWheelScrolled: 마우스 휠 스크롤 시 신호 (delta 값)
        mouseMoved: 마우스 이동 시 신호 (위치 좌표)
        mousePressed: 마우스 버튼 눌림 시 신호 (버튼, 위치)
        mouseReleased: 마우스 버튼 뗌 시 신호 (버튼, 위치)
    """
    
    # 사용자 정의 시그널 정의
    mouseDoubleClicked = pyqtSignal(object)  # 더블 클릭 이벤트 객체 전달
    mouseWheelScrolled = pyqtSignal(int)  # 휠 스크롤 방향과 강도
    mouseMoved = pyqtSignal(int, int)  # x, y 좌표
    mousePressed = pyqtSignal(int, int, int)  # 버튼, x, y 좌표
    mouseReleased = pyqtSignal(int, int, int)  # 버튼, x, y 좌표
    
    def __init__(self, parent=None):
        """
        MediaDisplay 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        
        # 기본 설정
        self.setAlignment(Qt.AlignCenter)  # 중앙 정렬 (미디어 중앙 배치)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 확장 가능한 크기 정책
        self.setStyleSheet("background-color: black;")  # 검은색 배경 (이미지 대비 위함)
        
        # 마우스 트래킹 활성화 (mouseMoveEvent 수신용)
        self.setMouseTracking(True)
        
        # 현재 표시 중인 미디어 유형
        self.current_media_type = None  # 'image', 'gif_animation', 'webp_animation', 'video', 'psd', 'unknown'
        
        # 크기 조절 모드 설정
        self.scaling_mode = Qt.KeepAspectRatio
        self.transformation_mode = Qt.SmoothTransformation
    
    def clear_media(self):
        """
        현재 표시 중인 모든 미디어를 지웁니다.
        """
        # 현재 재생 중인 Movie 객체 중지 (GIF/WEBP 애니메이션)
        if hasattr(self, 'movie') and self.movie() is not None:
            self.setMovie(None)
        
        # 레이블 콘텐츠 초기화
        self.clear()
        
        # 현재 미디어 타입 초기화
        self.current_media_type = None
        
        # 메모리 정리를 위한 추가 처리
        QApplication.processEvents()
    
    def display_pixmap(self, pixmap, media_type='image'):
        """
        QPixmap을 표시합니다. 필요시 크기 조절을 적용합니다.
        
        Args:
            pixmap (QPixmap): 표시할 픽스맵 객체
            media_type (str): 미디어 타입 ('image', 'psd' 등)
        
        Returns:
            bool: 성공적으로 표시되었는지 여부
        """
        if pixmap is None or pixmap.isNull():
            return False
        
        # 화면에 맞게 이미지 크기 조절
        scaled_pixmap = self.scale_pixmap_to_label(pixmap)
        
        # 레이블에 이미지 설정
        self.setPixmap(scaled_pixmap)
        
        # 현재 미디어 타입 설정
        self.current_media_type = media_type
        
        return True
    
    def scale_pixmap_to_label(self, pixmap):
        """
        QPixmap을 레이블 크기에 맞게 조절합니다.
        
        Args:
            pixmap (QPixmap): 원본 픽스맵 객체
        
        Returns:
            QPixmap: 크기 조절된 픽스맵 객체
        """
        if pixmap is None or pixmap.isNull():
            return pixmap
        
        # 레이블 크기 가져오기
        label_size = self.size()
        
        # 이미지 크기가 레이블보다 작은 경우 원본 크기 유지
        if (pixmap.width() <= label_size.width() and 
            pixmap.height() <= label_size.height()):
            return pixmap
        
        # 레이블 크기에 맞게 이미지 조절
        return pixmap.scaled(
            label_size,
            self.scaling_mode,
            self.transformation_mode
        )
    
    def resizeEvent(self, event):
        """
        위젯 크기 변경 이벤트 처리
        
        Args:
            event: 크기 변경 이벤트
        """
        super().resizeEvent(event)
        
        # 이미지 표시 중일 때 크기 조절
        if self.current_media_type == 'image' or self.current_media_type == 'psd':
            if self.pixmap() is not None and not self.pixmap().isNull():
                self.setPixmap(self.scale_pixmap_to_label(self.pixmap()))
    
    # 마우스 이벤트 처리 메서드들
    def mouseDoubleClickEvent(self, event):
        """
        마우스 더블 클릭 이벤트 처리
        
        Args:
            event (QMouseEvent): 마우스 이벤트
        """
        # 부모 클래스의 mouseDoubleClickEvent는 호출하지 않음
        # super().mouseDoubleClickEvent(event)
        
        # 이벤트가 처리되었음을 표시
        event.accept()
        
        # 시그널 발생
        self.mouseDoubleClicked.emit(event)
    
    def wheelEvent(self, event):
        """
        마우스 휠 이벤트 처리
        
        Args:
            event (QWheelEvent): 휠 이벤트
        """
        # 이벤트를 처리했음을 표시 (전파 방지)
        event.accept()
        
        # 휠 델타값 전달
        self.mouseWheelScrolled.emit(event.angleDelta().y())
        
        # 부모 클래스의 wheelEvent는 호출하지 않음 (이벤트 중복 방지)
    
    def mouseMoveEvent(self, event):
        """
        마우스 이동 이벤트 처리
        
        Args:
            event (QMouseEvent): 마우스 이벤트
        """
        super().mouseMoveEvent(event)
        self.mouseMoved.emit(event.x(), event.y())
    
    def mousePressEvent(self, event):
        """
        마우스 버튼 누름 이벤트 처리
        
        Args:
            event (QMouseEvent): 마우스 이벤트
        """
        super().mousePressEvent(event)
        self.mousePressed.emit(event.button(), event.x(), event.y())
    
    def mouseReleaseEvent(self, event):
        """
        마우스 버튼 뗌 이벤트 처리
        
        Args:
            event (QMouseEvent): 마우스 이벤트
        """
        super().mouseReleaseEvent(event)
        self.mouseReleased.emit(event.button(), event.x(), event.y())
    
    def get_preferred_size(self):
        """
        미디어에 적합한 권장 크기를 반환합니다.
        
        Returns:
            QSize: 권장 크기
        """
        if self.pixmap() and not self.pixmap().isNull():
            # 현재 픽스맵 크기를 기준으로 권장 크기 계산
            return QSize(self.pixmap().width(), self.pixmap().height())
        
        # 기본값: 현재 크기 유지
        return self.size() 