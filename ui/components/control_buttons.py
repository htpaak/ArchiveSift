from PyQt5.QtWidgets import QPushButton, QSizePolicy
from PyQt5.QtCore import Qt

class ControlButton(QPushButton):
    """기본 컨트롤 버튼 클래스"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setup_style()
        
    def setup_style(self):
        """기본 버튼 스타일 설정"""
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);
                color: white;
                border: none;
                padding: 2px 4px;
                margin: 0px;
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """)


class OpenFolderButton(ControlButton):
    """폴더 열기 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__('Open Folder', parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);
                color: white;
                border: none;
                padding: 2px 4px;
                margin: 0px;
                font-size: 18px;
                font-weight: bold;
                text-align: center;
                qproperty-alignment: AlignCenter;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """)
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)


class SetBaseFolderButton(ControlButton):
    """기준 폴더 설정 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__('Set Folder', parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);
                color: white;
                border: none;
                padding: 2px 4px;
                margin: 0px;
                font-size: 18px;
                font-weight: bold;
                text-align: center;
                qproperty-alignment: AlignCenter;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """)
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)


class PlayButton(ControlButton):
    """재생/일시정지 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("▶", parent)
        self.is_playing = False
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)
        
    def set_play_state(self, is_playing):
        """재생 상태에 따라 버튼 텍스트 변경"""
        self.is_playing = is_playing
        if is_playing:
            self.setText("❚❚ ")  # 일시정지 아이콘 뒤에 공백 추가
        else:
            self.setText("  ▶  ")  # 재생 아이콘에 앞뒤 공백 2개씩 추가


class RotateButton(ControlButton):
    """회전 버튼 클래스"""
    
    def __init__(self, clockwise=True, parent=None):
        """
        회전 버튼 초기화
        
        Args:
            clockwise (bool): True면 시계 방향, False면 반시계 방향
            parent: 부모 위젯
        """
        icon = "↻" if clockwise else "↺"  # 시계/반시계 방향 아이콘
        super().__init__(icon, parent)
        self.clockwise = clockwise
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        # 람다 함수를 사용하여 시계/반시계 방향 정보 전달
        self.clicked.connect(lambda: callback(self.clockwise))


class MuteButton(ControlButton):
    """음소거 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("🔈", parent)
        self.is_muted = False
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)
        
    def set_mute_state(self, is_muted):
        """음소거 상태에 따라 버튼 텍스트 변경"""
        self.is_muted = is_muted
        if is_muted:
            self.setText("🔇")  # 음소거 아이콘
        else:
            self.setText("🔈")  # 소리 켜짐 아이콘


class MenuButton(ControlButton):
    """메뉴 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("☰", parent)
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)


class BookmarkButton(ControlButton):
    """북마크 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("★", parent)
        self.is_bookmarked = False
        self.setup_bookmark_style()
        
    def setup_bookmark_style(self):
        """북마크 버튼 전용 스타일 설정"""
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(241, 196, 15, 0.9); /* 북마크된 상태와 동일한 색상으로 변경 */
                color: white;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: rgba(241, 196, 15, 1.0); /* 북마크된 상태와 동일한 호버 색상으로 변경 */
            }
        """)
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)
        
    def set_bookmark_state(self, is_bookmarked):
        """북마크 상태에 따라 버튼 스타일 변경"""
        self.is_bookmarked = is_bookmarked
        if is_bookmarked:
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(241, 196, 15, 0.9);
                    color: rgba(231, 76, 60, 0.9); /* UI 잠금 버튼 배경색과 동일하게 변경 */
                    border: none;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(241, 196, 15, 1.0);
                    color: rgba(231, 76, 60, 1.0); /* 호버 시에도 동일한 색상 유지 (불투명) */
                }
            """)
        else:
            self.setup_bookmark_style()  # 기본 스타일로 되돌림


class UILockButton(ControlButton):
    """UI 잠금 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("🔒", parent)
        self.is_locked = False
        self.setup_lock_style()
        
    def setup_lock_style(self):
        """잠금 해제 상태 스타일 설정"""
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);
                color: white;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """)
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)
        
    def set_lock_state(self, is_locked):
        """잠금 상태에 따라 버튼 텍스트와 스타일 변경"""
        self.is_locked = is_locked
        if is_locked:
            self.setText("🔒")  # 잠금 아이콘
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(231, 76, 60, 0.9); 
                    color: white;
                    border: none;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(231, 76, 60, 1.0); 
                }
            """)
        else:
            self.setText("🔓")  # 잠금 해제 아이콘
            self.setup_lock_style()  # 기본 스타일로 되돌림


# 타이틀바 버튼 스타일을 위한 기본 클래스
class TitleBarButton(QPushButton):
    """타이틀바 버튼 기본 클래스"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(20, 20)  # 타이틀바 버튼 크기를 30x30에서 20x20으로 축소
        self.setup_style()
        
    def setup_style(self):
        """기본 버튼 스타일 설정"""
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(41, 128, 185, 0.7);
            }
        """)


class MinimizeButton(TitleBarButton):
    """최소화 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("_", parent)
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)


class MaximizeButton(TitleBarButton):
    """최대화 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("□", parent)
        self.is_maximized = False
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)
        
    def set_maximize_state(self, is_maximized):
        """최대화 상태에 따라 버튼 텍스트 변경"""
        self.is_maximized = is_maximized
        if is_maximized:
            self.setText("❐")  # 윈도우 복원 아이콘
        else:
            self.setText("□")  # 최대화 아이콘


class FullscreenButton(TitleBarButton):
    """전체화면 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("🗖", parent)
        self.is_fullscreen = False
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)
        
    def set_fullscreen_state(self, is_fullscreen):
        """전체화면 상태에 따라 버튼 텍스트 변경"""
        self.is_fullscreen = is_fullscreen
        # 필요시 아이콘 변경 로직 추가


class CloseButton(TitleBarButton):
    """닫기 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("×", parent)
        self.setup_close_style()
        
    def setup_close_style(self):
        """닫기 버튼 전용 스타일 설정"""
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(231, 76, 60, 0.7);  /* 빨간색 배경 (마우스 오버 시) */
            }
        """)
        
    def connect_action(self, callback):
        """버튼 클릭 이벤트에 콜백 함수 연결"""
        self.clicked.connect(callback)


class TitleLockButton(TitleBarButton):
    """타이틀 바의 UI 잠금 버튼 클래스"""
    
    def __init__(self, parent=None):
        super().__init__("🔒", parent)
        self.is_locked = False
        self.setup_unlock_style()
        
    def setup_unlock_style(self):
        """잠금 해제 상태 스타일 설정"""
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(41, 128, 185, 0.7);
            }
        """)
        
    def connect_action(self, callback):
        """버튼 클릭 시 실행할 함수 연결"""
        self.clicked.connect(callback)
        
    def set_lock_state(self, locked):
        """잠금 상태 설정 및 표시 업데이트"""
        self.is_locked = locked
        if locked:
            self.setText("🔒")  # 잠금 아이콘
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(231, 76, 60, 0.9); 
                    color: white;
                    border: none;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(231, 76, 60, 1.0); 
                }
            """)
        else:
            self.setText("🔓")  # 열림 아이콘
            self.setup_unlock_style()  # 기본 스타일로 되돌림 