# 이미지 및 비디오 뷰어 애플리케이션 (PyQt5 기반)
import sys  # 시스템 관련 기능 제공 (프로그램 종료, 경로 관리 등)
import os  # 운영체제 관련 기능 제공 (파일 경로, 디렉토리 처리 등)
import platform
import shutil  # 파일 복사 및 이동 기능 제공 (고급 파일 작업)
import re  # 정규표현식 처리 기능 제공 (패턴 검색 및 문자열 처리)
import json  # JSON 파일 처리를 위한 모듈
from collections import OrderedDict  # LRU 캐시 구현을 위한 정렬된 딕셔너리
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QFileDialog, QStyle, QListWidget, QListWidgetItem, QSlider, QMenu, QAction, 
    QSizePolicy, QMessageBox, QFrame, QMainWindow, QDialog, QTabWidget, QCheckBox,
    QRadioButton, QLineEdit, QTextEdit, QProgressBar, QComboBox, QShortcut,
    QScrollArea, QSpacerItem, QLayout, QStyleOptionSlider, QAbstractItemView,
    QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget, QGroupBox
)
from PyQt5.QtGui import (
    QPixmap, QImage, QImageReader, QFont, QMovie, QCursor, QIcon, QColor, 
    QPalette, QFontMetrics, QTransform, QKeySequence, QWheelEvent, QDesktopServices
)
from PyQt5.QtCore import (
    Qt, QSize, QTimer, QEvent, QPoint, pyqtSignal, QRect, QMetaObject, 
    QObject, QUrl, QThread, QBuffer
)

# main.py 파일의 임포트 부분에서
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QFont, QMovie, QCursor, QIcon, QColor, QPalette, QFontMetrics, QTransform, QKeySequence, QWheelEvent, QDesktopServices  # 그래픽 요소 처리
from PyQt5.QtCore import Qt, QSize, QTimer, QEvent, QPoint, pyqtSignal, QRect, QMetaObject, QObject, QUrl, QThread, QBuffer  # Qt 코어 기능
# QDesktopServices 관련 중복 임포트 제거 (PyQt5.QtCore에는 QDesktopServices가 없음)
import cv2  # OpenCV 라이브러리 - 비디오 처리용 (프레임 추출, 이미지 변환 등)
from PIL import Image, ImageCms  # Pillow 라이브러리 - 이미지 처리용 (다양한 이미지 포맷 지원)
from io import BytesIO  # 바이트 데이터 처리용 (메모리 내 파일 스트림)
import time  # 시간 관련 기능 (시간 측정, 지연 등)
# ===== 우리가 만든 모듈 =====
# 경로 관련 기능
from core.utils.path_utils import get_app_directory, get_user_data_directory
# 유틸리티 함수
from core.utils.time_utils import format_time
from core.utils.sort_utils import atoi, natural_keys  # 유틸리티 함수들
# 캐시 관리 기능
from media.loaders.cache_manager import LRUCache
# 설정 관리
from core.config_manager import load_settings, save_settings  # 설정 관리 함수들
# 파일 형식 감지
from media.format_detector import FormatDetector  # 파일 형식 감지 클래스
# 이미지 로딩 기능
from media.loaders.image_loader import ImageLoaderThread
from media.loaders.image_loader import ImageLoader, ImageLoaderThread
# 미디어 처리
from media.handlers.image_handler import ImageHandler  # 이미지 처리 클래스
from media.handlers.psd_handler import PSDHandler  # PSD 처리 클래스
from media.handlers.video_handler import VideoHandler  # 비디오 처리 클래스
from media.handlers.animation_handler import AnimationHandler  # 애니메이션 처리 클래스 추가
from media.handlers.image_handler import RAW_EXTENSIONS
# 사용자 정의 UI 위젯
from ui.components.slider import ClickableSlider
from ui.components.scrollable_menu import ScrollableMenu
from ui.components.control_buttons import (
    OpenFolderButton, SetBaseFolderButton, PlayButton, RotateButton, 
    MuteButton, MenuButton, BookmarkButton, UILockButton,
    MinimizeButton, MaximizeButton, FullscreenButton, CloseButton, TitleLockButton
)  # 수정된 import
from ui.components.media_display import MediaDisplay  # 추가된 import
# 레이아웃
from ui.layouts.main_layout import MainLayout  # 추가된 import - 메인 레이아웃
from ui.layouts.controls_layout import ControlsLayout  # 추가된 import - 컨트롤 레이아웃
# 대화상자
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.preferences_dialog import PreferencesDialog
from events.handlers.keyboard_handler import KeyboardHandler, KeyInputEdit
from events.handlers.mouse_handler import MouseHandler
from events.handlers.window_handler import WindowHandler
# 북마크 관리
from features.bookmark import BookmarkManager  # 북마크 관리 클래스
# 회전 기능
from features.rotation.rotation_manager import RotationManager
from features.rotation.rotation_ui import RotationUI
# UI 잠금 기능
from features.ui_lock.ui_lock_manager import UILockManager
from features.ui_lock.ui_lock_ui import UILockUI
# UI 상태 관리
from core.ui.ui_state_manager import UIStateManager  # UI 상태 관리 클래스 추가
# 버전 정보
from core.version import get_version_string, get_full_version_string, get_version_info
# 로깅 시스템
from core.logger import Logger
# 상태 관리 시스템
from core.state_manager import StateManager

# 파일 브라우저 추가
from file import FileBrowser, FileNavigator
from file.operations import FileOperations
from file.navigator import FileNavigator
from file.undo_manager import UndoManager

from ui.components.dual_action_button import DualActionButton  # 듀얼 액션 버튼 클래스 import
# from ui.components.tooltip_manager import TooltipManager
# from ui.components.loading_indicator import LoadingIndicator

# Add MPV DLL path to PATH environment variable (required before importing mpv module)
# 현재 실행 중인 디렉토리를 PATH에 추가 (PyInstaller로 패키징된 경우를 위한 코드)
if getattr(sys, 'frozen', False):
    # PyInstaller로 패키징된 경우
    application_path = os.path.dirname(sys.executable)
    
    # 임시 디렉토리 경로 (PyInstaller의 _MEI로 시작하는 폴더)
    # sys._MEIPASS는 PyInstaller가 생성하는 임시 디렉토리
    temp_dir = getattr(sys, '_MEIPASS', application_path)
    
    # 다양한 가능성 있는 mpv DLL 경로들
    possible_paths = [
        os.path.join(temp_dir, 'mpv'),
        os.path.join(temp_dir, '_internal', 'mpv'),
        os.path.join(temp_dir, 'core', 'mpv'),
        temp_dir,
        application_path
    ]
    
    for p in possible_paths:
        if os.path.exists(p):
            if p not in os.environ['PATH']:
                os.environ['PATH'] = p + os.pathsep + os.environ['PATH']
                print(f"Added {p} to PATH")

    # DLL 파일이 실행 파일과 같은 디렉토리에 있는지 확인
    dll_files = ['libmpv-2.dll', 'mpv-2.dll', 'mpv-1.dll']
    dll_found = False
    
    for dll in dll_files:
        for p in possible_paths:
            dll_path = os.path.join(p, dll)
            if os.path.exists(dll_path):
                print(f"Found DLL: {dll_path}")
                dll_found = True
                break
        if dll_found:
            break
            
    if not dll_found:
        print("WARNING: No MPV DLL found in any potential location")
else:
    # 일반 Python 스크립트로 실행된 경우
    mpv_path = os.path.join(get_app_directory(), 'core', 'mpv')
    if not os.path.exists(mpv_path):
        mpv_path = os.path.join(get_app_directory(), 'mpv')
    
    # 경로를 PATH에 추가
    if mpv_path not in os.environ['PATH']:
        os.environ['PATH'] = mpv_path + os.pathsep + os.environ['PATH']
        print(f"Added {mpv_path} to PATH (dev mode)")

print(f"Current PATH: {os.environ['PATH']}")

# 로거 인스턴스 생성 (전역 로거)
from core.logger import Logger
logger = Logger("main")
logger.info(f"Application start - Version: {get_version_string()}")

# MPV 모듈 import (경로 설정 후에 가능)
try:
    # 래퍼 모듈을 통해 mpv 가져오기 (DLL 경로 문제 해결)
    from mpv_wrapper import mpv
    logger.info("MPV module imported successfully")
except Exception as e:
    logger.error(f"Error importing MPV: {str(e)}")
    print(f"Error importing MPV: {str(e)}")
    
    # 더미 MPV 클래스 정의 (비디오 기능 없이도 실행될 수 있도록)
    class DummyMPV:
        def __init__(self, *args, **kwargs):
            print("WARNING: Using dummy MPV implementation")
            self.dummy = True
        
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    # mpv 모듈 객체 생성
    class DummyMPVModule:
        def __init__(self):
            self.MPV = DummyMPV
    
    mpv = DummyMPVModule()

# 디버깅 모듈
from core.debug import QMovieDebugger, MemoryProfiler
# 메모리 관리 모듈
from core.memory import ResourceCleaner, TimerManager

# 메인 이미지 뷰어 클래스 정의
class ArchiveSift(QWidget):
    def __init__(self):
        super().__init__()  # 부모 클래스 초기화

        # 앱 초기화 시작 로깅
        # get_logger 함수가 없으므로 원래 코드로 되돌립니다
        self.logger = Logger("ArchiveSift")
        self.logger.info("Image viewer initialization start")
        
        # TooltipManager import
        from ui.components.custom_tooltip import TooltipManager
        
        # 툴팁 매니저 초기화
        self.tooltip_manager = TooltipManager(self)
        
        self.setWindowTitle('Image Viewer')  # 창 제목 설정
        
        # 작업 표시줄 아이콘 설정 (절대 경로와 여러 대체 경로 시도)
        icon_paths = [
            './core/ArchiveSift.ico',
            'core/ArchiveSift.ico',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'ArchiveSift.ico'),
            'ArchiveSift.ico',
            './ArchiveSift.ico'
        ]
        
        # 찾은 첫 번째 유효한 아이콘 경로 사용
        icon_path = None
        for path in icon_paths:
            if os.path.exists(path):
                icon_path = path
                print(f"Found window icon at: {path}")
                break
        
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))  # 앱 아이콘 설정
        else:
            # 기본 경로로 설정 (존재하지 않더라도)
            self.setWindowIcon(QIcon('./core/ArchiveSift.ico'))
            print("Warning: Could not find icon file, using default path")
            
        self.setGeometry(100, 100, 800, 600)  # 창 위치와 크기 설정
        
        # 키 설정 로드 - 키보드 단축키를 저장하는 사전
        self.load_key_settings()
        
        # 마우스 설정 로드 - 마우스 버튼 액션을 저장하는 사전
        self.load_mouse_settings()

        # 폴더 및 파일 관련 변수 초기화
        self.current_folder = ""  # 현재 폴더 경로
        self.image_files = []     # 이미지 파일 리스트
        
        # 앱 데이터 디렉토리 확인 및 생성
        app_data_dir = get_user_data_directory()
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir, exist_ok=True)
        
        # 상태 관리자 초기화
        self.state_manager = StateManager()
        
        # 기본 상태 설정
        self.state_manager.set_state("initialized", True)
        self.state_manager.set_state("app_version", get_version_string())
        self.state_manager.set_state("app_data_dir", app_data_dir)
        self.state_manager.set_state("boundary_navigation", True)
        
        # 상태 옵저버 등록 (current_index와 current_image_path 상태 변경 감지)
        self.state_manager.register_observer("current_index", self._on_current_index_changed)
        self.state_manager.register_observer("current_image_path", self._on_current_image_path_changed)
        
        # 경계 내비게이션 플래그 초기화
        self.is_boundary_navigation = False
        self.current_index = 0  # 현재 표시 중인 이미지 인덱스 (0으로 초기화)
        self.state_manager.set_state("current_index", self.current_index)  # 상태 관리자에도 설정
        self.current_image_path = ""  # 현재 표시 중인 이미지 경로
        self.state_manager.set_state("current_image_path", self.current_image_path)  # 상태 관리자에도 설정
        
        # 변수 초기화
        self.base_folder = ""  # 기준 폴더 경로
        self.folder_buttons = []  # 폴더 버튼 목록
        
        # 키보드 핸들러 초기화
        self.keyboard_handler = KeyboardHandler(self)
        
        # 북마크 관리자, 회전 관리자 및 UI 잠금 관리자 초기화
        self.bookmark_manager = BookmarkManager(self)
        
        # 디버깅 관련 인스턴스 생성
        self.qmovie_debugger = QMovieDebugger(self)
        self.memory_profiler = MemoryProfiler()
        
        # 메모리 관리 인스턴스 생성
        self.resource_cleaner = ResourceCleaner(self)
        self.timer_manager = TimerManager(self)
        self.singleshot_timers = self.timer_manager.singleshot_timers  # 호환성 유지
        
        # 회전 관리자 초기화
        self.rotation_manager = RotationManager()
        self.rotation_ui = RotationUI(self, self.rotation_manager)
        self.ui_lock_manager = UILockManager()
        self.ui_lock_ui = UILockUI(self, self.ui_lock_manager)
        
        # 마우스 이벤트 핸들러 초기화
        self.mouse_handler = MouseHandler(self)
        
        # 버튼 이벤트 핸들러 초기화
        from events.handlers.button_handler import ButtonEventHandler
        self.button_handler = ButtonEventHandler(self)
        
        # 윈도우 이벤트 핸들러 초기화
        self.window_handler = WindowHandler(self)
        
        # 파일 브라우저 생성
        self.file_browser = FileBrowser(parent=self)
        # 파일 내비게이터 생성
        self.file_navigator = FileNavigator(parent=self)
        # 파일 작업 관리자 생성
        self.file_operations = FileOperations(viewer=self)
        # Undo 관리자 생성
        self.undo_manager = UndoManager(viewer=self)
        # Undo 버튼 참조 저장을 위한 변수 (나중에 설정됨)
        self.undo_button = None
        
        # 북마크 관리자 초기화
        self.bookmark_manager = BookmarkManager(self)
        
        # 회전 관리자 초기화
        self.rotation_manager = RotationManager(self)

        self.installEventFilter(self)
        
        # 북마크 데이터 불러오기
        self.load_bookmarks()

        # UI 설정 후 마우스 추적 설정
        if hasattr(self, 'image_label'):
            self.image_label.setMouseTracking(True)
        self.setMouseTracking(True)
        
        # 비동기 이미지 로딩 관련 변수 초기화
        self.loader_threads = {}  # 로더 스레드 추적용 딕셔너리 (경로: 스레드)
        self.image_loader = ImageLoader()  # 이미지 로더 매니저 초기화
        self.loading_label = QLabel("Loading...", self)  # 로딩 중 표시용 레이블
        self.loading_label.setAlignment(Qt.AlignCenter)  # 중앙 정렬
        self.loading_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(52, 73, 94, 0.9);
                font-size: 24px;
                padding: 20px;
                border-radius: 10px;
            }
        """)
        self.loading_label.hide()  # 처음에는 숨김
        self.is_loading = False  # 로딩 상태 추적
        self.loading_timer = None  # 로딩 타이머
        
        # OpenCV 비디오 캡처 객체 초기화
        self.cap = None

        # MPV DLL 경로 설정 (동적 라이브러리 로드 경로)
        system = platform.system()

        # PyInstaller로 패키징된 경우 처리
        if getattr(sys, 'frozen', False):
            # PyInstaller로 패키징된 경우 실행 파일과 같은 디렉토리에 DLL이 있어야 함
            application_path = os.path.dirname(sys.executable)
            
            if system == 'Windows':
                # 여러 가능한 DLL 파일명 검색
                possible_dlls = ['libmpv-2.dll', 'mpv-2.dll', 'mpv-1.dll']
                dll_found = False
                
                for dll_name in possible_dlls:
                    mpv_dll_path = os.path.join(application_path, dll_name)
                    if os.path.exists(mpv_dll_path):
                        os.environ["MPV_DYLIB_PATH"] = mpv_dll_path
                        print(f"Found DLL in packaged app: {mpv_dll_path}")
                        dll_found = True
                        break
                
                if not dll_found:
                    # PATH에 현재 디렉토리를 추가하여 DLL을 찾을 수 있도록 함
                    print("No DLL found, adding application directory to PATH")
                    os.environ["PATH"] = application_path + os.pathsep + os.environ["PATH"]
            
            elif system == 'Darwin':  # macOS
                mpv_dll_path = os.path.join(application_path, "libmpv.dylib")
                if os.path.exists(mpv_dll_path):
                    os.environ["MPV_DYLIB_PATH"] = mpv_dll_path
            else:  # Linux
                mpv_dll_path = os.path.join(application_path, "libmpv.so")
                if os.path.exists(mpv_dll_path):
                    os.environ["MPV_DYLIB_PATH"] = mpv_dll_path
        else:
            # 일반 Python 스크립트로 실행된 경우 (개발 환경)
            mpv_path = os.path.join(get_app_directory(), 'mpv')
            if not os.path.exists(mpv_path):
                mpv_path = os.path.join(get_app_directory(), 'core', 'mpv')

            if system == 'Windows':
                mpv_dll_path = os.path.join(mpv_path, "libmpv-2.dll")
                if not os.path.exists(mpv_dll_path):
                    print(f"Warning: File {mpv_dll_path} does not exist.")
                os.environ["MPV_DYLIB_PATH"] = mpv_dll_path
            elif system == 'Darwin':  # macOS
                mpv_dll_path = os.path.join(mpv_path, "libmpv.dylib")
                if not os.path.exists(mpv_dll_path):
                    print(f"Warning: File {mpv_dll_path} does not exist.")
                os.environ["MPV_DYLIB_PATH"] = mpv_dll_path
            else:  # Linux
                mpv_dll_path = os.path.join(mpv_path, "libmpv.so")
                if not os.path.exists(mpv_dll_path):
                    print(f"Warning: File {mpv_dll_path} does not exist.")
                os.environ["MPV_DYLIB_PATH"] = mpv_dll_path

        # MPV 플레이어 초기화
        try:
            self.player = mpv.MPV(log_handler=print, 
                                 ytdl=True, 
                                 input_default_bindings=True, 
                                 input_vo_keyboard=True,
                                 hwdec='no')  # 하드웨어 가속 비활성화 (문제 해결을 위해)
            
            # 기본 설정
            self.player.loop = True  # 반복 재생
            self.player.keep_open = True  # 재생 후 닫지 않음
            self.player.terminal = False  # 터미널 출력 비활성화

            print("MPV player initialization successful")
        except Exception as e:
            print(f"MPV player initialization failed: {e}")
            self.player = None  # 초기화 실패 시 None으로 설정
        
        # 리소스 관리를 위한 객체 추적
        self.timers = []  # 모든 타이머 추적 - 먼저 초기화
        self.singleshot_timers = []  # 싱글샷 타이머 추적을 위한 리스트 추가

        # 책갈피 관련 변수 - BookmarkManager에서 관리함
        # self.bookmark_menu = None  # 책갈피 드롭다운 메뉴 객체 - 더 이상 사용하지 않음

        # 화면 해상도의 75%로 초기 창 크기 설정 (화면에 맞게 조정)
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.75)
        height = int(screen.height() * 0.75)
        self.resize(width, height)

        # 미디어 타입 추적 변수 초기화
        self.current_media_type = None  # 'image', 'gif', 'webp', 'video' 중 하나의 값 가짐
        self.is_slider_dragging = False  # 슬라이더 드래그 상태 추적 (시크바 조작 중 확인용)

        # 창을 화면 중앙에 위치시키기
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.move(x, y)

        # 창 크기 조절 관련 변수 초기화
        self.resize_direction = None  # 크기 조절 방향 (좌/우/상/하/모서리)
        self.resizing = False  # 크기 조절 중인지 여부
        self.resize_start_pos = None  # 크기 조절 시작 위치
        self.resize_start_geometry = None  # 크기 조절 시작 시 창 geometry
        
        # 최소 창 크기 설정 (UI 요소가 겹치지 않도록)
        self.setMinimumSize(400, 300)

        # 버튼 스타일 정의 (모든 버튼에 일관된 스타일 적용)
        button_style = """
            QPushButton {
                background-color: rgba(52, 73, 94, 0.9);  /* 반투명 남색 배경 */
                color: white;  /* 흰색 텍스트 */
                border: none;  /* 테두리 없음 */
                border-radius: 3px;  /* 둥근 모서리 */
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 불투명 남색 */
            }
        """

        # 슬라이더 스타일 정의 (재생바와 볼륨 슬라이더에 적용)
        self.slider_style = """
            QSlider {
                background-color: rgba(52, 73, 94, 0.6);
                border: none;
                border-radius: 3px;
                padding: 0px;
                margin: 0px;
                height: 100%;
            }
            QSlider:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
            QSlider::groove:horizontal {
                border: none;
                height: 8px;
                background: rgba(30, 30, 30, 0.8);
                border-radius: 4px;
                margin: 0px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #ffffff;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::add-page:horizontal {
                background: rgba(0, 0, 0, 0.5);
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: rgba(255, 255, 255, 0.8);
                border-radius: 4px;
            }
            """

        # 프레임리스 윈도우 설정 (제목 표시줄 없는 창 - 커스텀 UI용)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 배경색을 흰색으로 설정 (기본 배경)
        self.setStyleSheet("background-color: white;")

        # 메인 레이아웃 설정
        self.main_layout = MainLayout(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 제목 표시줄 (커스텀 타이틀바)
        self.title_bar = QWidget(self)  # 제목 표시줄 위젯 생성
        # self.title_bar.setFixedHeight(30)  # 고정 높이 제거
        self.title_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 크기 정책을 Preferred로 설정
        self.title_bar.setObjectName("title_bar")  # CSS 선택자로 사용할 객체 이름 설정
        # 제목 표시줄 배경색을 어둡게, 글자색을 흰색으로 설정
        self.title_bar.setStyleSheet("""
            QWidget#title_bar {
                background-color: #34495e;  /* 남색 계열 배경 */
            }
            QLabel {
                color: white;
                background-color: transparent;
            }
        """)  # 남색 배경
        
        # 타이틀바 컨트롤 저장을 위한 딕셔너리
        self.title_bar.controls = {}
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)  # 좌우 여백만 설정
        
        # 앱 아이콘 레이블 추가
        app_icon_label = QLabel()
        app_icon_pixmap = QIcon('./core/ArchiveSift.ico').pixmap(20, 20)  # 아이콘 크기 20x20
        app_icon_label.setPixmap(app_icon_pixmap)
        app_icon_label.setStyleSheet("background-color: transparent;")
        app_icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)  # 너비는 고정, 높이는 가변
        title_layout.addWidget(app_icon_label)
        self.title_bar.controls['app_icon_label'] = app_icon_label  # 컨트롤에 추가하여 동적 크기 조절 적용
        
        # 제목 텍스트 레이블
        title_label = QLabel("ArchiveSift")
        # 스타일시트는 이미 title_bar에 적용된 것을 사용
        title_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)  # 너비는 고정, 높이는 가변
        title_layout.addWidget(title_label)
        self.title_bar.controls['title_label'] = title_label  # 컨트롤에 추가하여 동적 크기 조절 적용
        title_layout.addStretch()  # 가운데 빈 공간 추가 (창 컨트롤 버튼을 오른쪽으로 밀기 위함)

        # 상단 UI 잠금 버튼 추가
        title_lock_btn = TitleLockButton(self)  # 타이틀 잠금 버튼 클래스 사용
        title_lock_btn.connect_action(self.toggle_title_ui_lock)  # toggle_title_ui_lock은 이제 controls_layout으로 호출을 위임합니다
        self.title_lock_btn = title_lock_btn  # 버튼 객체 저장
        
        # 새로운 버튼 추가 (UI 잠금 버튼 왼쪽)
        new_button = QPushButton(self)
        new_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.3);
            }
        """)
        new_button.setText("💬")  # 대화 이모지로 변경
        new_button.setToolTip("피드백")  # 툴팁 설정
        new_button.clicked.connect(self.open_feedback)  # 클릭 이벤트 연결
        title_layout.addWidget(new_button)  # 레이아웃에 버튼 추가
        self.title_bar.controls['feedback_button'] = new_button  # 컨트롤 등록
        
        # 창 컨트롤 버튼들 (최소화, 최대화, 닫기 - 윈도우 기본 버튼 대체)
        min_btn = MinimizeButton(self)  # 최소화 버튼
        min_btn.connect_action(self.showMinimized)
        self.title_bar.controls['minimize_button'] = min_btn  # 컨트롤 등록
        
        max_btn = MaximizeButton(self)  # 최대화 버튼
        max_btn.connect_action(self.toggle_maximize_state)  # 최대화/복원 기능 연결
        self.max_btn = max_btn  # 버튼 객체 저장 (최대화 상태에 따라 아이콘 변경 위함)
        self.title_bar.controls['maximize_button'] = max_btn  # 컨트롤 등록

        # 여기에 전체화면 버튼 추가
        fullscreen_btn = FullscreenButton(self)  # 전체화면 버튼
        fullscreen_btn.connect_action(self.toggle_fullscreen)  # 전체화면 토글 기능 연결
        self.fullscreen_btn = fullscreen_btn  # 버튼 객체 저장
        self.title_bar.controls['fullscreen_button'] = fullscreen_btn  # 컨트롤 등록
        
        close_btn = CloseButton(self)  # 닫기 버튼
        close_btn.connect_action(self.close)  # 닫기 기능 연결
        self.title_bar.controls['close_button'] = close_btn  # 컨트롤 등록
        
        # 잠금 버튼 컨트롤 등록
        self.title_bar.controls['title_lock_button'] = title_lock_btn
        
        # 창 컨트롤 버튼들 레이아웃에 추가
        title_layout.addWidget(title_lock_btn)
        title_layout.addWidget(min_btn)
        title_layout.addWidget(max_btn)
        title_layout.addWidget(fullscreen_btn)
        title_layout.addWidget(close_btn)

        # 제목 표시줄을 메인 레이아웃에 추가 (1% 비율 - 전체 UI 중 작은 부분)
        layout.addWidget(self.title_bar, 2)
        
        # 메인 레이아웃을 레이아웃에 추가 (87% 비율)
        layout.addWidget(self.main_layout, 86)
        
        # 북마크 메뉴 초기화
        self.bookmark_manager.update_bookmark_menu()
        
        # 이미지 표시 레이블 (QLabel → MediaDisplay로 변경)
        self.image_label = MediaDisplay()
        
        # 이미지 정보 표시 레이블 (파일 이름, 크기 등 표시)
        # QLabel 대신 EditableIndexLabel 사용
        from ui.components import EditableIndexLabel
        self.image_info_label = EditableIndexLabel(self)
        self.image_info_label.setAlignment(Qt.AlignCenter)  # 중앙 정렬
        self.image_info_label.hide()  # 처음에는 숨김 (이미지 로드 후 표시)
        
        # 인덱스 변경 시그널 연결
        self.image_info_label.indexChanged.connect(self.go_to_index)
        
        # 하단 컨트롤 레이아웃
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)  # 여백 없음
        bottom_layout.setSpacing(0)  # 레이아웃 사이 간격 제거

        # 통합 하단 UI 컨테이너 생성
        self.bottom_ui_container = QWidget()
        # Fixed에서 Preferred로 변경하여 비율 설정(12%)이 적용되도록 함
        self.bottom_ui_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.bottom_ui_container.setContentsMargins(0, 0, 0, 0)
        
        # 최소 높이 설정 - 화면 높이의 12%를 최소값으로 사용
        screen_height = QApplication.desktop().availableGeometry().height()
        min_height = int(screen_height * 0.12)  # 12% 비율 적용
        self.bottom_ui_container.setMinimumHeight(min_height)
        
        bottom_ui_layout = QVBoxLayout(self.bottom_ui_container)
        bottom_ui_layout.setContentsMargins(0, 0, 0, 0)
        bottom_ui_layout.setSpacing(0)

        # 슬라이더 위젯과 레이아웃
        self.slider_widget = QWidget()
        self.slider_widget.setStyleSheet("""
            background-color: rgba(52, 73, 94, 0.9);
            border: none;
            padding: 0px;
            margin: 0px;
        """)  # 패딩과 마진 완전히 제거
        # 크기 정책을 Expanding으로 변경하여 전체 높이를 차지하도록 함
        self.slider_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 최소 높이 설정 제거 - 비율에 맞게 자동 조절되도록 함
        # button_height = 50  # 기본 버튼 높이
        # self.slider_widget.setMinimumHeight(int(button_height * 1.2))
        
        new_slider_layout = QHBoxLayout(self.slider_widget)
        new_slider_layout.setContentsMargins(0, 0, 0, 0)  # 여백을 완전히 제거
        new_slider_layout.setSpacing(0)  # 위젯 간 간격도 0으로 설정

        # 폴더 열기 버튼 (첫 번째 위치)
        self.open_button = OpenFolderButton(self)
        self.open_button.connect_action(self.open_folder)  # 폴더 열기 기능 연결 (이미지 폴더 선택)
        self.open_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        new_slider_layout.addWidget(self.open_button)

        # Set Base Folder 버튼 (두 번째 위치)
        self.set_base_folder_button = SetBaseFolderButton(self)
        self.set_base_folder_button.connect_action(self.set_base_folder)  # 기준 폴더 설정 기능 연결 (복사 대상 폴더)
        self.set_base_folder_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        new_slider_layout.addWidget(self.set_base_folder_button)

        # 재생 버튼 (세 번째 위치)
        self.play_button = PlayButton(self)  # 재생 아이콘 버튼
        self.play_button.connect_action(self.toggle_animation_playback)  # 재생 버튼 클릭 이벤트 연결 (재생/일시정지 전환)
        self.play_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        new_slider_layout.addWidget(self.play_button)

        # 회전 버튼 추가 (반시계 방향)
        self.rotate_ccw_button = RotateButton(clockwise=False, parent=self)
        self.rotate_ccw_button.connect_action(self.rotate_image)
        self.rotate_ccw_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        new_slider_layout.addWidget(self.rotate_ccw_button)

        # 회전 버튼 추가 (시계 방향)
        self.rotate_cw_button = RotateButton(clockwise=True, parent=self)
        self.rotate_cw_button.connect_action(self.rotate_image)
        self.rotate_cw_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        new_slider_layout.addWidget(self.rotate_cw_button)

        # 기존 슬라이더 (재생 바) 추가
        self.playback_slider = ClickableSlider(Qt.Horizontal, self)  # ClickableSlider로 변경 (클릭 시 해당 위치로 이동)
        self.playback_slider.setRange(0, 100)  # 슬라이더 범위 설정 (0-100%)
        self.playback_slider.setValue(0)  # 초기 값을 0으로 설정 (시작 위치)
        self.playback_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        # 고정 높이 설정 제거 (setFixedHeight 제거)
        
        self.playback_slider.clicked.connect(self.slider_clicked)  # 클릭 이벤트 연결 (클릭 위치로 미디어 이동)
        new_slider_layout.addWidget(self.playback_slider, 10)  # 재생 바 슬라이더를 레이아웃에 추가, stretch factor 10으로 증가 (기존 3에서 변경)

        # 재생 시간 레이블 추가 (현재 시간/총 시간 표시)
        self.time_label = QLabel("00:00 / 00:00", self)  # 초기 시간 표시
        self.time_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)  # Expanding으로 변경하여 전체 높이 사용
        self.time_label.setStyleSheet("""
            QLabel {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                border-radius: 3px;
                qproperty-alignment: AlignCenter;  /* 텍스트 중앙 정렬 */
                padding: 0px;
            }
            QLabel:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        self.time_label.setAlignment(Qt.AlignCenter)  # 텍스트 중앙 정렬 (레이블 내 텍스트 위치)
        new_slider_layout.addWidget(self.time_label)  # 레이블을 재생 바 오른쪽에 추가

        # 음소거 버튼 추가 (오디오 켜기/끄기)
        self.mute_button = MuteButton(self)
        self.mute_button.connect_action(self.toggle_mute)  # 음소거 토글 기능 연결
        self.mute_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        new_slider_layout.addWidget(self.mute_button)

        # 볼륨 슬라이더 추가 (음량 조절)
        self.volume_slider = ClickableSlider(Qt.Horizontal, self)
        self.volume_slider.setRange(0, 100)  # 볼륨 범위 0-100%
        self.volume_slider.setValue(100)  # 기본 볼륨 100%으로 설정 (최대 음량)
        self.volume_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        self.volume_slider.setFixedWidth(80)  # 볼륨 슬라이더 너비 고정
        # 고정 높이 설정 제거 (setFixedHeight 제거)
        
        # ClickableSlider의 메서드로 볼륨 컨트롤에 필요한 시그널 연결
        self.volume_slider.connect_to_volume_control(self.adjust_volume)
        new_slider_layout.addWidget(self.volume_slider)  # 음량 조절 슬라이더를 레이아웃에 추가
        
        # 메뉴 버튼 추가 
        self.menu_button = MenuButton(self)
        self.menu_button.connect_action(self.show_menu_above)  # 메뉴 표시 함수 연결
        self.menu_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        new_slider_layout.addWidget(self.menu_button)
        
        # 북마크 버튼 추가 (가장 오른쪽에 위치)
        self.slider_bookmark_btn = BookmarkButton(self)
        self.slider_bookmark_btn.connect_action(self.show_bookmark_menu_above)  # 메뉴 표시 함수 연결로 변경
        self.slider_bookmark_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        new_slider_layout.addWidget(self.slider_bookmark_btn)
        
        # 북마크 매니저 설정
        self.bookmark_manager.set_bookmark_button(self.slider_bookmark_btn)

        # 여기에 UI 고정 버튼 추가 (완전히 새로운 코드로 교체)
        self.ui_lock_btn = UILockButton(self)  # UILockButton 클래스 사용
        self.ui_lock_btn.connect_action(self.toggle_ui_lock)  # toggle_ui_lock은 이제 controls_layout으로 호출을 위임합니다
        self.ui_lock_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # 세로 방향 Expanding으로 변경
        new_slider_layout.addWidget(self.ui_lock_btn)

        # 슬라이더바 컨트롤 리스트 생성 (버튼과 레이블을 함께 관리)
        self.slider_controls = []

        # 이미 생성된 컨트롤들을 리스트에 추가
        self.slider_controls.append(self.open_button)
        self.slider_controls.append(self.set_base_folder_button)
        self.slider_controls.append(self.play_button)
        self.slider_controls.append(self.rotate_ccw_button)
        self.slider_controls.append(self.rotate_cw_button)
        self.slider_controls.append(self.time_label)  # 시간 레이블도 같은 리스트에 추가
        self.slider_controls.append(self.mute_button)
        self.slider_controls.append(self.menu_button)
        self.slider_controls.append(self.slider_bookmark_btn)
        self.slider_controls.append(self.ui_lock_btn)

        # 새로운 슬라이더 위젯을 하단 레이아웃에 추가
        bottom_ui_layout.addWidget(self.slider_widget, 1)  # 슬라이더 위젯 비율 1 (1/11 = 9.1%)

        # 버튼 컨테이너 위젯 생성
        button_container = QWidget()
        self.button_container = button_container  # 클래스 멤버로 먼저 저장
        button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        button_container_layout = QVBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.setSpacing(0)

        # 폴더 버튼에 스타일 적용
        self.buttons = []
        for row_idx in range(4):  # 4줄로 변경
            row_widget = QWidget()
            row_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
            
            button_layout = QHBoxLayout(row_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setSpacing(0)
            button_row = []
            
            total_width = self.width()
            available_width = total_width - button_layout.contentsMargins().left() - button_layout.contentsMargins().right()
            button_width = available_width / 20  # 실제 사용 가능한 너비로 계산
            
            for i in range(20):
                # Undo 버튼 제거 (5행 마지막에 배치 예정)
                empty_button = DualActionButton('', self)
                empty_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
                empty_button.clicked.connect(self.on_button_click)
                
                if i == 19:
                    remaining_width = total_width - (int(button_width) * 19)
                    empty_button.setFixedWidth(remaining_width)
                else:
                    empty_button.setFixedWidth(int(button_width))
                
                button_row.append(empty_button)
                button_layout.addWidget(empty_button)
            
            self.buttons.append(button_row)
            # 각 행에 stretch factor 1을 적용하여 컨테이너 높이의 1/4씩 할당
            button_container_layout.addWidget(row_widget, 1)
            
        # 마지막 행을 추가하여 남은 공간 채우기
        last_row_widget = QWidget()
        last_row_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        last_button_layout = QHBoxLayout(last_row_widget)
        last_button_layout.setContentsMargins(0, 0, 0, 0)
        last_button_layout.setSpacing(0)
        last_button_row = []
        
        for i in range(20):
            if i == 19:  # 마지막 버튼(100번째 = 5번째 행의 20번째 버튼)은 Undo 버튼으로 설정
                # 일반 QPushButton 사용
                empty_button = QPushButton('Undo', self)
                empty_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
                # 북마크 버튼과 동일한 노란색 스타일 적용
                empty_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(241, 196, 15, 0.9);
                        color: white;
                        border: none;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: rgba(241, 196, 15, 1.0);
                    }
                """)
                # Undo 기능에 연결
                empty_button.clicked.connect(self.undo_last_action)
                # Undo 버튼 참조 저장
                self.undo_button = empty_button
                # 초기 상태로 비활성화 (삭제된 파일이 없으므로)
                self.undo_button.setEnabled(False)
                # Undo 상태 변경 시그널 연결
                self.undo_manager.undo_status_changed.connect(self.update_undo_button_state)
                
                remaining_width = total_width - (int(button_width) * 19)
                empty_button.setFixedWidth(remaining_width)
            else:
                empty_button = DualActionButton('', self)
                empty_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
                empty_button.clicked.connect(self.on_button_click)
                
                empty_button.setFixedWidth(int(button_width))
            
            last_button_row.append(empty_button)
            last_button_layout.addWidget(empty_button)
        
        self.buttons.append(last_button_row)
        # 마지막 행에 stretch factor 2를 적용하여 남은 공간을 채움
        button_container_layout.addWidget(last_row_widget, 1)  # 2에서 1로 변경하여 모든 행이 동일한 크기로 표시

        # 버튼 컨테이너를 bottom_ui_layout에 추가
        bottom_ui_layout.addWidget(self.button_container, 11)  # 버튼 컨테이너 비율 11 (11/12 = 91.7%)

        # 하단 UI 컨테이너를 메인 레이아웃에 추가 (12% 비율)
        layout.addWidget(self.bottom_ui_container, 12)

        # 메인 레이아웃에 이미지 컨테이너 추가
        self.main_layout.set_media_display(self.image_label)
        
        # 메인 레이아웃에 컨트롤 레이아웃 추가
        # self.main_layout.set_controls_layout(self.slider_widget)
        
        # ControlsLayout 인스턴스 생성
        self.controls_layout = ControlsLayout(self)
        
        # MPV 상태 확인을 위한 타이머 설정 (주기적으로 재생 상태 업데이트)
        self.play_button_timer = QTimer(self)
        self.play_button_timer.timeout.connect(self.controls_layout.update_play_button)  # 타이머가 작동할 때마다 update_play_button 메소드 호출
        self.play_button_timer.start(200)  # 200ms마다 상태 확인 (초당 5번 업데이트로 최적화)
        self.timers.append(self.play_button_timer)  # 타이머 추적에 추가
        
        # 슬라이더 시그널 연결
        self.playback_slider.sliderPressed.connect(self.slider_pressed)
        self.playback_slider.sliderReleased.connect(self.slider_released)
        self.playback_slider.valueChanged.connect(self.seek_video)
        self.playback_slider.clicked.connect(self.slider_clicked)

        self.setFocusPolicy(Qt.StrongFocus)  # 강한 포커스를 설정 (위젯이 포커스를 받을 수 있도록 설정 - 키보드 이벤트 처리용)

        # 마우스 트래킹 활성화 (마우스 움직임 감지를 위한 설정)
        self.setMouseTracking(True)
        self.image_label.setMouseTracking(True)
        
        # 전역 이벤트 필터 설치 (모든 위젯의 이벤트 캡처)
        QApplication.instance().installEventFilter(self)

        # 크로스 플랫폼 지원을 위한 MPV 경로 설정
        mpv_path = os.path.join(get_app_directory(), 'mpv')
        if platform.system() == 'Windows':
            os.environ["MPV_DYLIB_PATH"] = os.path.join(mpv_path, "libmpv-2.dll")
        elif platform.system() == 'Darwin':  # macOS
            os.environ["MPV_DYLIB_PATH"] = os.path.join(mpv_path, "libmpv.dylib")
        else:  # Linux
            os.environ["MPV_DYLIB_PATH"] = os.path.join(mpv_path, "libmpv.so")

        self.player = mpv.MPV(ytdl=True, input_default_bindings=True, input_vo_keyboard=True, hr_seek="yes")  # MPV 플레이어 객체 생성 (고품질 비디오 재생)

        # 슬라이더와 음량 조절 동기화
        self.volume_slider.connect_to_volume_control(self.adjust_volume)

        # 슬라이더 스타일 적용 (UI 일관성)
        self.playback_slider.setStyleSheet(self.slider_style)  # 재생 슬라이더 스타일 적용
        self.volume_slider.setStyleSheet(self.slider_style)  # 음량 조절 슬라이더 스타일 적용

        self.previous_position = None  # 클래스 변수로 이전 위치 저장 (시크 동작 최적화용)

        # 창이 완전히 로드된 후 이미지 정보 업데이트를 위한 타이머 설정
        # 초기 레이아웃 설정을 위해 바로 호출
        self.update_image_info()
        # 창이 완전히 로드된 후 한번 더 업데이트 (지연 업데이트로 화면 크기에 맞게 조정)
        QTimer.singleShot(100, self.update_image_info)

        # 이미지 캐시 초기화
        self.image_cache = LRUCache(10)  # 일반 이미지용 캐시 (최대 10개 항목)
        self.gif_cache = LRUCache(3)      # GIF 파일용 캐시 (최대 3개 항목)
        self.psd_cache = LRUCache(3)     # PSD 파일용 캐시 (5→3개 항목으로 축소)

        self.last_wheel_time = 0  # 마지막 휠 이벤트 발생 시간 (휠 이벤트 쓰로틀링용)
        self.wheel_cooldown_ms = 1000  # 1000ms 쿨다운 (500ms에서 변경됨) - 휠 이벤트 속도 제한

        # 리소스 관리를 위한 객체 추적
        self.timers = []  # 모든 타이머 추적 - 먼저 초기화
        self.singleshot_timers = []  # 싱글샷 타이머 추적을 위한 리스트 추가

        # 메뉴 관련 변수 초기화
        self.dropdown_menu = None  # 드롭다운 메뉴 객체

        # 초기 및 resizeEvent에서 동적으로 호출되는 커스텀 UI 설정 메서드
        self.setup_custom_ui()  # 초기 호출 (창 크기에 맞게 UI 요소 조정)
        
        # 스타일시트 기본 적용 (슬라이더 외관 디자인 정의)
        self.playback_slider.setStyleSheet(self.slider_style)  # 재생 슬라이더 스타일 적용
        self.volume_slider.setStyleSheet(self.slider_style)  # 음량 조절 슬라이더 스타일 적용
        
        # 연결 추가 (이벤트와 함수 연결)
        self.volume_slider.connect_to_volume_control(self.adjust_volume)  # 슬라이더로 음량 조절

        # UI 상태 관리자 생성
        self.ui_state_manager = UIStateManager(self)
        # UI 상태 관리자 신호 연결
        self.ui_state_manager.ui_visibility_changed.connect(self.on_ui_visibility_changed)

        # UI 잠금 관리자 생성
        self.ui_lock_manager = UILockManager(self)
        # UI 잠금 UI 관리자 생성
        self.ui_lock_ui = UILockUI(self, self.ui_lock_manager)

        # 회전 관리자 생성
        self.rotation_manager = RotationManager(self)
        # 회전 관리자 시그널 연결
        self.rotation_manager.rotation_changed.connect(self.on_rotation_changed)
        # 회전 UI 관리자 생성
        self.rotation_ui = RotationUI(self, self.rotation_manager)

        # 회전 관련 변수 추가
        self.current_rotation = 0  # 현재 회전 각도 (0, 90, 180, 270)
        self.rotated_frames = {}  # 회전된 애니메이션 프레임 캐시

        # 전체화면 오버레이 레이블 생성
        self.fullscreen_overlay = QLabel(self)
        self.fullscreen_overlay.setAlignment(Qt.AlignCenter)
        self.fullscreen_overlay.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border-radius: 10px;
        """)
        self.fullscreen_overlay.hide()  # 초기에는 숨김 상태

        # 리사이징 타이머 추가 (다른 변수 초기화 부분 아래에 추가)
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)  # 한 번만 실행
        self.resize_timer.timeout.connect(self.delayed_resize)

        # UI 상태 변경을 위한 타이머 추가 (반드시 추가해야 함)
        self.ui_update_timer = QTimer()
        self.ui_update_timer.setSingleShot(True)
        self.ui_update_timer.timeout.connect(self.delayed_resize)

        # __init__ 메서드 끝에 타이머 추가
        self.create_single_shot_timer(0, self.update_ui_lock_button_state)

        # 미디어 핸들러 초기화
        self.image_handler = ImageHandler(self, self.image_label)
        self.psd_handler = PSDHandler(self, self.image_label)
        self.video_handler = VideoHandler(self, self.image_label)

        # MediaDisplay 이벤트 연결
        self.image_label.mouseDoubleClicked.connect(self.mouseDoubleClickEvent)
        self.image_label.mouseWheelScrolled.connect(self.handle_wheel_event)
        
        # 전체 창에 휠 이벤트 필터 설치
        self.installEventFilter(self)
        
        # 추가 이벤트 핸들러 함수 추가
    def handle_wheel_event(self, delta):
        """
        MediaDisplay에서 전달된 휠 이벤트를 처리합니다.
        
        Args:
            delta (int): 휠 스크롤 값 (양수: 위로, 음수: 아래로)
        """
        # 마우스 핸들러로 휠 이벤트 위임
        # 경계 이동 처리 및 리소스 정리는 show_image 내부에서 처리됩니다
        self.mouse_handler.handle_wheel_event(delta)

    def delete_current_image(self):
        """
        현재 이미지를 삭제합니다 (휴지통으로 이동).
        
        단일책임 원칙에 맞게 파일 삭제 로직을 FileOperations로 위임합니다.
        """
        # FileOperations로 삭제 기능 위임
        self.file_operations.delete_current_image(confirm=True)

    def ensure_maximized(self):
        """창이 최대화 상태인지 확인하고, 최대화 상태가 아니면 최대화합니다."""
        self.window_handler.ensure_maximized()

    def resizeEvent(self, event):
        """창 크기가 변경될 때 호출되는 이벤트"""
        # window_handler로 이벤트 처리 위임
        self.window_handler.resize_event(event)
        
        # 부모 클래스의 resizeEvent 호출
        super().resizeEvent(event)

    def delayed_resize(self):
        """리사이징 완료 후 지연된 UI 업데이트 처리"""
        self.window_handler.delayed_resize()

    def mouseDoubleClickEvent(self, event=None):
        """더블 클릭 시 전체화면 또는 최대화 상태 전환"""
        if event:
            self.mouse_handler.handle_double_click(event)
        else:
            # When event object is missing (called from MediaDisplay)
            self.mouse_handler.handle_double_click(None)

    def set_base_folder(self):
        """Set base folder (for auto-generating subfolder buttons)"""
        folder_path = QFileDialog.getExistingDirectory(self, "Set Base Folder")  # Folder selection dialog
        if folder_path:  # When folder is selected
            self.base_folder = folder_path  # Save base folder path
            print(f"Base folder set to: {self.base_folder}")  # Print set path to console

            # 모든 버튼 초기화 (텍스트 및 툴팁 제거) - 마지막 Undo 버튼 제외
            for i, row in enumerate(self.buttons):
                for j, button in enumerate(row):
                    # 마지막 버튼(Undo 버튼)은 건너뜀
                    if i == 3 and j == 19:
                        continue
                        
                    # DualActionButton 특화 메서드 호출
                    if hasattr(button, 'set_folder_info'):
                        button.set_folder_info('', '')
                    else:
                        # 이전 버전 호환성 유지
                        button.setText('')
                        button.setToolTip('')

            # 하위 폴더 목록 가져오기
            subfolders = [f.path for f in os.scandir(self.base_folder) if f.is_dir()]  # 디렉토리만 선택
            subfolders.sort(key=lambda x: natural_keys(os.path.basename(x).lower()))  # 자연스러운 순서로 정렬

            # 버튼 너비 계산
            button_width = self.width() // 20

            # 폴더 버튼 업데이트
            for i, row in enumerate(self.buttons):
                for j, button in enumerate(row):
                    # 마지막 버튼(Undo 버튼)은 건너뜀
                    if i == 3 and j == 19:
                        continue
                        
                    index = i * 20 + j  # 버튼 인덱스 계산 (5행 20열)
                    if index < len(subfolders):  # 유효한 폴더가 있는 경우
                        folder_name = os.path.basename(subfolders[index])  # 폴더명 추출
                        button.setFixedWidth(button_width)  # 버튼 너비 설정
                        
                        # 버튼 텍스트 영역 계산 (패딩 고려)
                        available_width = button_width - 16  # 좌우 패딩 8px씩 제외
                        
                        # 텍스트 너비 측정
                        font_metrics = button.fontMetrics()
                        text_width = font_metrics.horizontalAdvance(folder_name)
                        
                        # 텍스트가 버튼 너비를 초과하면 자동으로 축약
                        truncated_name = folder_name
                        if text_width > available_width:
                            # 적절한 길이를 찾을 때까지 텍스트 줄임
                            for k in range(len(folder_name), 0, -1):
                                truncated = folder_name[:k] + ".."  # 텍스트 뒷부분 생략 표시
                                if font_metrics.horizontalAdvance(truncated) <= available_width:
                                    truncated_name = truncated
                                    break
                        
                        # DualActionButton 특화 메서드 호출
                        if hasattr(button, 'set_folder_info'):
                            button.set_folder_info(subfolders[index], truncated_name)
                        else:
                            # 이전 버전 호환성 유지
                            button.setText(truncated_name)
                            button.setToolTip(subfolders[index])

    def on_button_click(self):
        """하위 폴더 버튼 클릭 처리 - controls_layout으로 위임"""
        # 이 메서드는 controls_layout으로 이동됨
        if hasattr(self, 'controls_layout'):
            self.controls_layout.on_button_click()
        else:
            print("Controls layout not initialized")

    def open_folder(self):
        """이미지 폴더 열기 대화상자 표시 및 처리"""
        folder_path = self.file_browser.open_folder_dialog()
        
        if folder_path:
            # 파일 브라우저로 폴더 내 이미지 파일 찾기
            self.image_files, self.current_index = self.file_browser.process_folder(folder_path)
            self.state_manager.set_state("current_index", self.current_index)  # 상태 관리자 업데이트
            
            # 파일 내비게이터에도 파일 목록 설정
            self.file_navigator.set_files(self.image_files, self.current_index)
            
            if self.image_files:
                self.show_image(self.image_files[0])  # 첫 번째 이미지 표시
                self.update_image_info()  # 이미지 정보 업데이트 (인덱스 표시 업데이트)

    def get_image_files(self, folder_path):
        """폴더에서 이미지 파일 목록을 가져옵니다."""
        try:
            # file_browser.py에서 사용하는 확장자 목록과 일치시키기
            # 1. 순수 일반 이미지 (표준 라이브러리로 처리 가능)
            normal_img_extensions = [
                '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico',
                '.jfif', '.jp2', '.jpe', '.jps', '.tga'
            ]
            
            # 2. 특수 라이브러리가 필요한 이미지
            heic_heif_extensions = ['.heic', '.heif']
            avif_extensions = ['.avif']
            
            # 3. RAW 이미지 형식
            raw_extensions = [
                '.cr2', '.nef', '.arw', '.orf', '.rw2', '.dng', '.pef', '.raf', '.srw',
                '.crw', '.raw', '.kdc', '.mrw', '.dcr', '.sr2', '.3fr', '.mef', '.erf',
                '.rwl', '.mdc', '.mos', '.x3f', '.bay', '.nrw'
            ]
            
            # 4. 애니메이션 이미지
            animation_extensions = ['.gif', '.webp']
            
            # 5. 비디오 형식
            video_extensions = [
                '.mp4', '.avi', '.wav', '.ts', '.m2ts', '.mov', '.qt', 
                '.mkv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', 
                '.vob', '.wmv'
            ]
            
            # 6. 오디오 형식
            audio_extensions = ['.mp3', '.flac', '.aac', '.m4a', '.ogg']
            
            # 7. 디자인 파일
            design_extensions = ['.psd']
            
            # 모든 지원 확장자 목록 병합
            valid_extensions = (
                normal_img_extensions + 
                heic_heif_extensions + 
                avif_extensions + 
                raw_extensions + 
                animation_extensions + 
                video_extensions + 
                audio_extensions + 
                design_extensions
            )
            
            # 폴더 내의 모든 파일 목록 가져오기
            files = os.listdir(folder_path)
            
            # 이미지 파일만 필터링하고 전체 경로로 변환
            image_files = [os.path.join(folder_path, f) for f in files 
                          if os.path.splitext(f)[1].lower() in valid_extensions]
            
            # 파일 이름으로 정렬
            image_files.sort()
            
            return image_files
            
        except Exception as e:
            return []

    def stop_video(self):
        """Stop video playback and clean up related resources"""
        if self.video_handler:
            self.video_handler.stop_video()

    def disconnect_all_slider_signals(self):
        """Disconnect all slider signals (to prevent event conflicts)"""
        
        # Delegate responsibility to ClickableSlider's disconnect_all_signals method
        if hasattr(self, 'playback_slider') and self.playback_slider:
            self.playback_slider.disconnect_all_signals()

    def cancel_pending_loaders(self, current_path=None):
        """Cancel all loader threads except for the currently loading image."""
        # Delegate loader cancellation responsibility to the ImageLoader class
        self.image_loader.cancel_pending_loaders(current_path)
        
        # Maintain compatibility with existing code (incremental migration)
        for path, loader in list(self.loader_threads.items()):
            if (current_path is None or path != current_path) and loader.isRunning():
                try:
                    loader.terminate()
                    loader.wait(100)  # Wait up to 100ms
                except:
                    pass
                del self.loader_threads[path]

    def update_ui_for_media(self, image_path):
        """미디어 표시에 필요한 UI 요소들을 업데이트합니다."""
        # 창 제목 업데이트
        self.update_window_title(image_path)
        
        # 북마크 관련 UI 업데이트 
        self.update_bookmark_ui()
        
        # 미디어 컨트롤 상태 업데이트
        self.update_media_controls()
        
        # UI 컴포넌트의 가시성 관리
        self.ensure_ui_visibility()
        
    def update_window_title(self, image_path):
        """창 제목과 제목표시줄 업데이트"""
        # 파일 이름을 제목표시줄에 표시
        file_name = os.path.basename(image_path) if image_path else "ArchiveSift"
        title_text = f"ArchiveSift - {file_name}" if image_path else "ArchiveSift"
        
        # 제목표시줄 라벨 찾아서 텍스트 업데이트 (두 번째 자식이 제목 레이블)
        title_label = None
        for child in self.title_bar.children():
            if isinstance(child, QLabel) and not child.pixmap():  # pixmap이 없는 QLabel(텍스트 레이블)
                title_label = child
                break
                
        if title_label:
            title_label.setText(title_text)
            # 라벨 텍스트 색상을 흰색으로 설정 (제목 표시줄은 남색 배경 유지)
            title_label.setStyleSheet("color: white; background-color: transparent;")

    def update_bookmark_ui(self):
        """북마크 관련 UI 요소들을 업데이트"""
        # 책갈피 버튼 상태 업데이트
        self.controls_layout.update_bookmark_button_state()
        
        # 북마크 메뉴 업데이트 추가 - 이미지 변경 시 메뉴 상태도 함께 업데이트
        self.controls_layout.update_bookmark_menu()
        
    def update_media_controls(self):
        """Update control states based on media type"""
        # For video media, reset the mute button state
        if self.current_media_type == 'video' and hasattr(self, 'mute_button'):
            try:
                is_muted = self.video_handler.is_muted()
                if is_muted is not None:  # Update state only if not None
                    self.mute_button.set_mute_state(is_muted)
            except Exception as e:
                pass
                
    def ensure_ui_visibility(self):
        """Manage visibility of UI components"""
        # Bring the title bar and image info label to the front
        if hasattr(self, 'title_bar'):
            self.title_bar.raise_()
        if hasattr(self, 'image_info_label'):
            self.image_info_label.raise_()

    def prepare_for_media_loading(self, image_path):
        """Preparations before media loading"""
        # Skip resource cleanup for boundary navigation
        if self.is_boundary_navigation:
            # Flag reset
            self.is_boundary_navigation = False
        else:
            # Perform resource cleanup in normal cases
            self.cleanup_current_media()

        # Check image size
        image_size_mb = 0
        try:
            if os.path.exists(image_path):
                image_size_mb = os.path.getsize(image_path) / (1024 * 1024)  # Convert to megabytes
        except Exception as e:
            pass

        # 전체화면 모드에서 고품질 이미지 로딩 (비동기로 처리)
        if self.isFullScreen() and image_size_mb > 5:  # 큰 이미지인 경우
            # 최대한 고품질로 표시 (필요한 작업 추가)
            QApplication.processEvents()  # UI 응답성 유지
            
        return image_size_mb  # 이미지 크기 정보 반환

    def update_current_media_state(self, image_path):
        """현재 미디어 상태 관련 변수 업데이트 및 UI 요소 갱신"""
        # 현재 이미지 경로 저장
        self.current_image_path = image_path
        
        # 기존 진행 중인 로딩 스레드 취소
        self.cancel_pending_loaders(image_path)

        # UI 요소 업데이트
        self.update_ui_for_media(image_path)

    def detect_media_format(self, image_path):
        """파일 형식을 감지하고 적절한 형식을 반환합니다."""
        return FormatDetector.detect_media_format(image_path)

    def load_animation_media(self, image_path, format_type):
        """GIF와 WEBP 애니메이션을 로드하고 표시합니다."""
        # AnimationHandler가 없는 경우 초기화
        if not hasattr(self, 'animation_handler'):
            from media.handlers.animation_handler import AnimationHandler
            self.animation_handler = AnimationHandler(self.image_label, self)
            # 애니메이션 핸들러 시그널 연결
            if hasattr(self, 'controls_layout'):
                self.controls_layout.connect_animation_handler(self.animation_handler)
                
        # Call the appropriate handler method based on media type
        if format_type == 'gif_image' or format_type == 'gif_animation':
            detected_type = self.animation_handler.load_gif(image_path)
            self.current_media_type = detected_type
        elif format_type == 'webp_image' or format_type == 'webp_animation':
            detected_type = self.animation_handler.load_webp(image_path)
            self.current_media_type = detected_type

    def load_static_image(self, image_path, format_type, file_ext):
        """Load and display regular images and PSD images."""
        self.image_handler.load_static_image(image_path, format_type, file_ext)

    def load_video_media(self, image_path):
        """Load and play the video file."""
        # Process video file
        self.current_media_type = 'video'  # Update media type
        self.play_video(image_path)  # Play video

    def finalize_media_loading(self, image_path):
        """Perform final processing tasks after media loading."""
        # Apply delayed resizing in fullscreen mode
        if self.isFullScreen():
            QTimer.singleShot(300, self.delayed_resize)

    def show_image(self, image_path):
        """Display image/media file and update related UI
           Resets the is_boundary_navigation flag that skips resource cleanup in the prepare_for_media_loading method.
        """
        # Reset flag to not skip resource cleanup when boundary is reached
        # Print boundary_navigation flag state
        
        # 항상 리소스를 정리하도록 플래그 재설정
        # is_boundary_navigation 상태와 상관없이 미디어 로딩 전에 리소스를 항상 정리
        self.is_boundary_navigation = False
        
        # 이미지 핸들러에게 이미지 표시 위임
        self.image_handler.show_image(image_path)

    def scale_webp(self):
        """WEBP 애니메이션 크기 조정"""
        if self.current_media_type == 'webp_animation' and hasattr(self, 'animation_handler'):
            self.animation_handler.scale_webp()

    def scale_gif(self):
        """GIF 애니메이션 크기 조정"""
        if self.current_media_type == 'gif_animation' and hasattr(self, 'animation_handler'):
            self.animation_handler.scale_gif()

    def play_video(self, video_path):
        """비디오 파일을 재생합니다."""
        # VideoHandler에 비디오 재생 위임
        self.video_handler.play_video(video_path)

    def on_video_end(self, name, value):
        """비디오 재생이 종료되면 호출되는 핸들러"""
        # VideoHandler에 이벤트 위임
        self.video_handler.on_video_end(name, value)

    def stop_video_timer(self):
        """타이머를 중지하는 메서드입니다."""
        if self.video_handler:
            self.video_handler.stop_video_timer()
        elif hasattr(self, 'video_timer') and self.video_timer.isActive():
            self.video_timer.stop()
            if self.video_timer in self.timers:
                self.timers.remove(self.video_timer)

    def slider_clicked(self, value):
        """슬라이더 클릭 이벤트 처리 - controls_layout으로 위임"""
        # 이 메서드는 controls_layout으로 이동됨
        if hasattr(self, 'controls_layout'):
            self.controls_layout.slider_clicked(value)
        else:
            print("Controls layout not initialized")

    def slider_pressed(self):
        """슬라이더 드래그 시작 이벤트 처리 - controls_layout으로 위임"""
        # 이 메서드는 controls_layout으로 이동됨
        if hasattr(self, 'controls_layout'):
            self.controls_layout.slider_pressed()
        else:
            print("Controls layout not initialized")

    def slider_released(self):
        """슬라이더 드래그 종료 이벤트 처리 - controls_layout으로 위임"""
        # 이 메서드는 controls_layout으로 이동됨
        if hasattr(self, 'controls_layout'):
            self.controls_layout.slider_released()
        else:
            print("Controls layout not initialized")

    def seek_video(self, value):
        """슬라이더 값에 따라 비디오 재생 위치를 변경하는 메서드 - controls_layout으로 위임"""
        # 이 메서드는 controls_layout으로 이동됨
        if hasattr(self, 'controls_layout'):
            self.controls_layout.seek_video(value)
        else:
            print("Controls layout not initialized")

    def seek_animation(self, value):
        """슬라이더 값에 따라 애니메이션 재생 위치를 변경하는 메서드 - controls_layout으로 위임"""
        # 이 메서드는 controls_layout으로 이동됨
        if hasattr(self, 'controls_layout'):
            self.controls_layout.seek_animation(value)
        else:
            print("Controls layout not initialized")

    def update_video_playback(self):
        """비디오 재생 위치에 따라 슬라이더 값을 업데이트하는 메서드 - controls_layout으로 위임"""
        # 이 메서드는 controls_layout으로 이동됨
        if hasattr(self, 'controls_layout'):
            self.controls_layout.update_video_playback()
        else:
            print("Controls layout not initialized")

    def format_time(self, seconds):
        """초를 'MM:SS' 형식으로 변환하는 메서드 - controls_layout으로 위임"""
        # 이 메서드는 controls_layout으로 이동됨
        if hasattr(self, 'controls_layout'):
            return self.controls_layout.format_time(seconds)
        else:
            # controls_layout이 초기화되지 않은 경우 직접 모듈 함수 호출
            from core.utils.time_utils import format_time as utils_format_time
            return utils_format_time(seconds)

    def update_play_button(self):
        """재생 버튼 상태를 업데이트합니다."""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        self.controls_layout.update_play_button()

    def update_image_info(self):
        """이미지 정보를 업데이트하고 레이블 크기를 조절합니다."""
        # 기존 레이블이 표시중이면 닫기
        if hasattr(self, 'image_info_label') and self.image_info_label.isVisible():
            self.image_info_label.hide()

        # 창 크기에 따라 폰트 크기 동적 조절
        window_width = self.width()
        font_size = max(12, min(32, int(window_width * 0.02)))
            
        # 패딩과 마진도 창 크기에 비례하여 조절
        padding = max(8, min(12, int(window_width * 0.008)))
        margin = max(10, min(30, int(window_width * 0.02)))

        # 이미지 파일이 있을 때만 정보 표시
        if self.image_files and hasattr(self, 'current_image_path'):
            # 인덱스 정보 업데이트
            total_files = len(self.image_files)
            self.image_info_label.update_index(self.current_index, total_files)
            
            self.image_info_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background-color: rgba(52, 73, 94, 0.9);
                    font-size: {font_size}px;
                    padding: {padding}px {padding + 4}px;
                    border-radius: 3px;
                    font-weight: normal;
                }}
                QLabel:hover {{
                    background-color: rgba(72, 93, 114, 0.9);
                }}
                QLineEdit {{
                    color: white;
                    background-color: rgba(52, 73, 94, 0.9);
                    font-size: {font_size}px;
                    padding: {padding}px {padding + 4}px;
                    border-radius: 3px;
                    border: 1px solid #7f8c8d;
                    font-weight: normal;
                    selection-background-color: #3498db;
                }}
            """)
            
            # 레이블 크기와 위치 조정
            self.image_info_label.adjustSize()
            
            # 우측 상단에 위치 (여백은 창 크기에 비례, 툴바 높이 고려)
            toolbar_height = 90  # 제목바(30) + 툴바(40) + 추가 여백(20)
            x = self.width() - self.image_info_label.width() - margin
            y = toolbar_height + margin
            
            self.image_info_label.move(x, y)
            self.image_info_label.show()
            self.image_info_label.raise_()
        
        # 이미지 레이아웃 강제 업데이트
        if hasattr(self, 'main_layout') and hasattr(self, 'image_label'):
            self.image_label.updateGeometry()
            self.main_layout.update()

    # 다음 이미지를 보여주는 메서드입니다.
    def show_next_image(self):
        """Move to the next image."""
        # Check current index and the number of image files to determine if it's the last image
        current_index = self.file_navigator.get_current_index()
        file_count = len(self.file_navigator.get_files())
        
        # Handle boundary navigation only when it is the last image
        is_last_image = (current_index >= file_count - 1)
        
        success, next_image = self.file_navigator.next_file()
        if success and next_image:
            self.current_index = self.file_navigator.get_current_index()  # Synchronize index
            self.state_manager.set_state("current_index", self.current_index)  # Update state manager
            self.show_image(next_image)
        else:
            # Set boundary navigation flag only when trying to go beyond the last image
            if is_last_image:
                self.is_boundary_navigation = True
            else:
                # Handle failure for other reasons in a general manner
                pass

    def show_previous_image(self):
        """Move to the previous image."""
        # Check current index and the number of image files to determine if it's the first image
        current_index = self.file_navigator.get_current_index()
        
        # Handle boundary navigation only when it is the first image (index 0)
        is_first_image = (current_index == 0)
        
        success, prev_image = self.file_navigator.previous_file()
        if success and prev_image:
            self.current_index = self.file_navigator.get_current_index()  # Synchronize index
            self.state_manager.set_state("current_index", self.current_index)  # Update state manager
            self.show_image(prev_image)
        else:
            # Set boundary navigation flag only when trying to go before the first image
            if is_first_image:
                self.is_boundary_navigation = True
            else:
                # Handle failure for other reasons in a general manner
                pass

    def handle_navigation(self, direction):
        """Handles image navigation logic.
        
        Args:
            direction (str): 'next' or 'previous'
        """
        # Debug messages removed: current index before navigation, current image, file navigator file count, and main image list count
        
        # Check image list synchronization
        if self.file_navigator.get_files() != self.image_files:
            # Synchronize if necessary
            self.image_files = self.file_navigator.get_files()
        
        # Default boundary navigation flag is False
        self.is_boundary_navigation = False
        
        # Check current index
        current_index = self.file_navigator.get_current_index()
        file_count = len(self.file_navigator.get_files())
        
        # Determine if it is the first or last image
        is_first_image = (current_index == 0)
        is_last_image = (current_index >= file_count - 1)
        
        # Call the appropriate method based on navigation direction
        if direction == 'next':
            success, image_path = self.file_navigator.next_file()
            direction_text = "next"
            
            # Set boundary navigation flag only when attempting to go beyond the last image
            if not success and is_last_image:
                self.is_boundary_navigation = True
        else:  # previous
            success, image_path = self.file_navigator.previous_file()
            direction_text = "previous"
            
            # Set boundary navigation flag only when attempting to go before the first image
            if not success and is_first_image:
                self.is_boundary_navigation = True
        
        # Debug messages removed: image load success/failure details
        if success and image_path:
            self.current_index = self.file_navigator.get_current_index()  # Synchronize index
            # Debug message removed: new index
            self.show_image(image_path)
        else:
            # Display message if navigation fails due to boundary or unknown reason
            if self.is_boundary_navigation:
                pass  # Debug message removed: image load failed - boundary reached
            else:
                pass  # Debug message removed: image load failed - unknown reason

    def show_message(self, message):
        if hasattr(self, 'message_label') and self.message_label.isVisible():
            self.message_label.close()

        self.message_label = QLabel(message, self)
        
        # 창 크기에 따라 폰트 크기 동적 조절
        window_width = self.width()
        font_size = max(12, min(32, int(window_width * 0.02)))
        
        # 패딩과 마진도 창 크기에 비례하여 조절
        padding = max(8, min(12, int(window_width * 0.008)))
        margin = max(10, min(30, int(window_width * 0.02)))
        
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                background-color: rgba(52, 73, 94, 0.9);
                font-size: {font_size}px;
                padding: {padding}px {padding + 4}px;
                border-radius: 3px;
                font-weight: normal;
            }}
        """)
        
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.show()
        self.message_label.adjustSize()
        
        # 좌측 상단에 위치 (image_info_label과 동일한 높이 사용)
        toolbar_height = 90  # 제목바(30) + 툴바(40) + 추가 여백(20)
        self.message_label.move(margin, toolbar_height + margin)
        self.message_label.raise_()  # 항상 위에 표시되도록 함
        
        self.create_single_shot_timer(2000, self.message_label.close)

    # 현재 이미지를 다른 폴더로 복사하는 메서드입니다.
    def copy_image_to_folder(self, folder_path):
        # 현재 이미지 경로가 존재하고, 폴더 경로도 제공되었으면 복사를 시작합니다.
        if self.current_image_path and folder_path:
            # FileOperations 클래스를 사용하여 파일 복사
            success, _ = self.file_operations.copy_file_to_folder(self.current_image_path, folder_path)
            
            # 복사 성공 시 다음 이미지로 이동
            if success:
                self.show_next_image()

    def keyPressEvent(self, event):
        """키보드 이벤트를 키보드 핸들러로 위임합니다."""
        # 키보드 핸들러로 이벤트 처리 위임
        self.keyboard_handler.handle_key_press(event)

    def eventFilter(self, obj, event):
        """이벤트 필터 - 여러 유형의 이벤트를 감시하고 필요에 따라 처리"""
        # 마우스 이벤트 처리
        if event.type() in [QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease]:
            return self.mouse_handler.event_filter(obj, event)
        # 휠 이벤트 처리 (UI 요소에 상관없이 전체 창에서 작동하도록)
        elif event.type() == QEvent.Wheel:
            # 현재 마우스 커서 아래에 있는 위젯이 QDialog이면 휠 이벤트를 무시함
            pos = QCursor.pos()
            widget_under_cursor = QApplication.widgetAt(pos)
            
            # QDialog 또는 QDialog의 자식 위젯인 경우 휠 이벤트 처리하지 않음
            parent_widget = widget_under_cursor
            while parent_widget is not None:
                if isinstance(parent_widget, QDialog):
                    return False  # 이벤트를 처리하지 않고 기본 핸들러로 전달
                parent_widget = parent_widget.parent()
                
            # QDialog가 아닌 경우 평소처럼 처리
            delta = event.angleDelta().y()
            self.handle_wheel_event(delta)
            # 이벤트 처리됨으로 표시
            event.accept()
            return True
        
        return False  # 다른 이벤트는 기본 처리로 전달

    def toggle_fullscreen(self):
        """전체화면 모드를 전환합니다."""
        # 전체화면 모드 전환은 WindowHandler에 위임
        self.window_handler.toggle_fullscreen()

    def restore_video_state(self, was_playing, position):
        """비디오 재생 상태를 복구합니다"""
        if self.current_media_type == 'video' and hasattr(self, 'video_handler'):
            self.video_handler.restore_video_state(was_playing, position)

    # toggle_maximize 메소드 추가 (이름을 toggle_maximize_state로 변경)
    def toggle_maximize_state(self):
        """최대화 상태와 일반 상태를 토글합니다."""
        self.window_handler.toggle_maximize_state()

    def closeEvent(self, event):
        """
        애플리케이션 종료 시 필요한 정리 작업을 수행합니다.
        """
        self.window_handler.close_event(event)

    def toggle_mute(self):
        """음소거 상태를 토글합니다."""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        self.controls_layout.toggle_mute()

    def adjust_volume(self, volume):
        """음량을 조절합니다."""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        self.controls_layout.adjust_volume(volume)

    def toggle_animation_playback(self):
        """애니메이션(GIF, WEBP) 또는 비디오 재생/일시정지 토글"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        self.controls_layout.toggle_animation_playback()

    def toggle_bookmark(self):
        """북마크 토글: 북마크 관리자에 위임"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        self.controls_layout.toggle_bookmark()
        
    def update_bookmark_menu(self):
        """북마크 메뉴 업데이트: 북마크 관리자에 위임"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        # controls_layout이 초기화되어 있을 때만 호출
        if hasattr(self, 'controls_layout'):
            self.controls_layout.update_bookmark_menu()
        else:
            # controls_layout이 아직 초기화되지 않았다면 직접 북마크 매니저에 위임
            self.bookmark_manager.update_bookmark_menu()
        
    def load_bookmarked_image(self, path):
        """북마크된 이미지 로드: 북마크 관리자에 위임"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        if hasattr(self, 'controls_layout'):
            self.controls_layout.load_bookmarked_image(path)
        else:
            # controls_layout이 아직 초기화되지 않았다면 직접 북마크 매니저에 위임
            self.bookmark_manager.load_bookmarked_image(path)
        
    def clear_bookmarks(self):
        """모든 북마크 삭제: 북마크 관리자에 위임"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        if hasattr(self, 'controls_layout'):
            self.controls_layout.clear_bookmarks()
        else:
            # controls_layout이 아직 초기화되지 않았다면 직접 북마크 매니저에 위임
            self.bookmark_manager.clear_bookmarks()
        
    def update_bookmark_button_state(self):
        """북마크 버튼 상태 업데이트: 북마크 관리자에 위임"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        if hasattr(self, 'controls_layout'):
            self.controls_layout.update_bookmark_button_state()
        else:
            # controls_layout이 아직 초기화되지 않았다면 직접 북마크 매니저에 위임
            self.bookmark_manager.update_bookmark_button_state()
    
    # 삭제할 메서드들 (이미 북마크 관리자로 기능이 이전됨)
    def add_bookmark(self):
        pass
        
    def remove_bookmark(self):
        pass
        
    def save_bookmarks(self):
        pass
        
    def load_bookmarks(self):
        pass
        
    def show_bookmark_menu_above(self):
        """북마크 메뉴 표시: 북마크 관리자에 위임"""
        self.bookmark_manager.show_menu_above_button()

    def show_menu_above(self):
        """메뉴 버튼 위에 드롭업 메뉴를 표시합니다."""
        # 메뉴가 없으면 생성
        if not self.dropdown_menu:
            self.dropdown_menu = ScrollableMenu(self)
            
            # 키 설정 메뉴 항목
            key_settings_action = QAction("Preferences", self)
            key_settings_action.triggered.connect(self.show_preferences_dialog)
            self.dropdown_menu.addAction(key_settings_action)
            
            # 구분선 추가
            self.dropdown_menu.addSeparator()
            
            # 정보 메뉴 항목
            about_action = QAction("About", self)
            about_action.triggered.connect(self.show_about_dialog)
            self.dropdown_menu.addAction(about_action)
            
            # 메뉴에 스크롤 속성 설정
            self.dropdown_menu.setProperty("_q_scrollable", True)
        
        # 버튼 좌표를 전역 좌표로 변환
        pos = self.menu_button.mapToGlobal(QPoint(0, 0))
        
        # 메뉴 사이즈 계산
        menu_width = self.dropdown_menu.sizeHint().width()
        button_width = self.menu_button.width()
        
        # 최대 높이 설정
        desktop = QApplication.desktop().availableGeometry()
        max_height = min(800, desktop.height() * 0.8)  # 화면 높이의 80%까지 사용
        self.dropdown_menu.setMaximumHeight(int(max_height))
        
        # 메뉴 높이가 화면 높이보다 크면 화면의 80%로 제한
        menu_height = min(self.dropdown_menu.sizeHint().height(), max_height)
        
        # 화면 정보 가져오기
        desktop = QApplication.desktop().availableGeometry()
        
        # 기준을 버튼의 오른쪽 변으로 설정 (메뉴의 오른쪽 가장자리를 버튼의 오른쪽 가장자리에 맞춤)
        button_right_edge = pos.x() + button_width
        x_pos = button_right_edge - menu_width  # 메뉴의 오른쪽 끝이 버튼의 오른쪽 끝과 일치하도록 계산
        y_pos = pos.y() - menu_height  # 버튼 위에 메뉴가 나타나도록 설정
        
        # 메뉴가 화면 왼쪽 경계를 벗어나는지 확인
        if x_pos < desktop.left():
            x_pos = desktop.left()  # 화면 왼쪽 경계에 맞춤
        
        # 메뉴가 화면 위로 넘어가지 않도록 조정
        if y_pos < desktop.top():
            # 화면 위로 넘어가면 버튼 아래에 표시
            y_pos = pos.y() + self.menu_button.height()
        
        # 메뉴가 화면 아래로 넘어가지 않도록 조정
        if y_pos + menu_height > desktop.bottom():
            # 화면 아래로 넘어가면 버튼 위에 표시하되, 필요한 만큼만 위로 올림
            y_pos = desktop.bottom() - menu_height
        
        # 메뉴 팝업 (스크롤이 필요한 경우를 위해 높이 속성 명시적 설정)
        self.dropdown_menu.setProperty("_q_scrollable", True)
        self.dropdown_menu.popup(QPoint(x_pos, y_pos))

    def toggle_ui_lock(self):
        """UI 잠금을 토글합니다."""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        self.controls_layout.toggle_ui_lock()

    def toggle_title_ui_lock(self):
        """타이틀바 잠금을 토글합니다."""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        self.controls_layout.toggle_title_ui_lock()

    def update_ui_lock_button_state(self):
        """UI 잠금 버튼 상태 업데이트"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        if hasattr(self, 'controls_layout'):
            self.controls_layout.update_ui_lock_button_state()
        # 이전 호환성을 위해 유지
        elif hasattr(self, 'ui_lock_ui'):
            self.ui_lock_ui.update_ui_lock_button_state()

    def update_title_lock_button_state(self):
        """타이틀 잠금 버튼 상태 업데이트"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        if hasattr(self, 'controls_layout'):
            self.controls_layout.update_title_lock_button_state()
        # 이전 호환성을 위해 유지
        elif hasattr(self, 'ui_lock_ui'):
            self.ui_lock_ui.update_title_lock_button_state()

    # 초기 및 resizeEvent에서 동적으로 호출되는 커스텀 UI 설정 메서드
    def setup_custom_ui(self):
        """사용자 정의 UI 설정"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        if hasattr(self, 'controls_layout'):
            self.controls_layout.setup_custom_ui()
            
            # 툴팁 등록 - UI 초기화 후 실행
            self.setup_tooltips()
        # 이전 코드는 유지하지 않음 - controls_layout에서 모든 기능 처리
        
    def setup_tooltips(self):
        """Register custom tooltips for buttons and control elements"""
        # Register title bar button tooltips
        if hasattr(self, 'title_bar') and hasattr(self.title_bar, 'controls'):
            for control_name, control in self.title_bar.controls.items():
                if control_name == 'close_button':
                    self.tooltip_manager.register(control, "Close Window")
                elif control_name == 'minimize_button':
                    self.tooltip_manager.register(control, "Minimize")
                elif control_name == 'maximize_button':
                    self.tooltip_manager.register(control, "Maximize/Restore")
                elif control_name == 'fullscreen_button':
                    self.tooltip_manager.register(control, "Toggle Fullscreen")
                elif control_name == 'title_lock_button':
                    self.tooltip_manager.register(control, "Toggle Title Bar Lock")
                elif control_name == 'feedback_button':
                    self.tooltip_manager.register(control, "Send Feedback")
                
        # Register bottom control button tooltips
        if hasattr(self, 'slider_controls'):
            for control in self.slider_controls:
                if control == self.open_button:
                    self.tooltip_manager.register(control, "Open Folder")
                elif control == self.set_base_folder_button:
                    self.tooltip_manager.register(control, "Set Base Folder")
                elif control == self.play_button:
                    self.tooltip_manager.register(control, "Play/Pause")
                elif control == self.rotate_ccw_button:
                    self.tooltip_manager.register(control, "Rotate Counter-Clockwise")
                elif control == self.rotate_cw_button:
                    self.tooltip_manager.register(control, "Rotate Clockwise")
                elif control == self.mute_button:
                    self.tooltip_manager.register(control, "Mute/Unmute")
                elif control == self.menu_button:
                    self.tooltip_manager.register(control, "Menu")
                elif control == self.slider_bookmark_btn:
                    self.tooltip_manager.register(control, "Add/Remove Bookmark")
                elif control == self.ui_lock_btn:
                    self.tooltip_manager.register(control, "Toggle UI Lock")
                elif control == self.time_label:
                    self.tooltip_manager.register(control, "Playback Time Info")
                    
        # Register slider tooltips
        if hasattr(self, 'playback_slider'):
            self.tooltip_manager.register(self.playback_slider, "Adjust Playback Position")
        if hasattr(self, 'volume_slider'):
            self.tooltip_manager.register(self.volume_slider, "Adjust Volume")

    def show_loading_indicator(self):
        """로딩 인디케이터를 화면 중앙에 표시합니다."""
        # 이미 로딩 중이면 무시
        if self.is_loading:
            return
            
        # 로딩 상태 설정
        self.is_loading = True
        
        # 로딩 레이블 스타일 설정 (테두리 없는 파란색 배경)
        self.loading_label.setText("Loading...")
        self.loading_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(52, 73, 94, 0.9);
                font-size: 24px;
                padding: 20px;
                border-radius: 10px;
            }
        """)
        
        # 로딩 레이블을 이미지 레이블 중앙에 위치시킴
        self.loading_label.resize(200, 80)  # 크기 설정
        
        # 이미지 레이블 중앙 좌표 계산
        x = self.image_label.x() + (self.image_label.width() - self.loading_label.width()) // 2
        y = self.image_label.y() + (self.image_label.height() - self.loading_label.height()) // 2
        
        # 로딩 레이블 위치 설정
        self.loading_label.move(x, y)
        self.loading_label.raise_()  # 맨 앞으로 가져오기
        self.loading_label.show()
        
        # 기존 타이머 정리
        if self.loading_timer is not None and self.loading_timer.isActive():
            self.loading_timer.stop()
            if self.loading_timer in self.timers:
                self.timers.remove(self.loading_timer)
        
        # 타임아웃 설정 (10초 후 자동으로 숨김)
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.hide_loading_indicator)
        self.loading_timer.setSingleShot(True)
        self.loading_timer.start(10000)  # 10초 타임아웃
        self.timers.append(self.loading_timer)
        
        # UI 즉시 업데이트
        QApplication.processEvents()

    def hide_loading_indicator(self):
        """Hides the loading indicator."""
        # If not currently loading, ignore
        if not self.is_loading:
            return
            
        # Reset loading state
        self.is_loading = False
        
        # Clean up timer
        if self.loading_timer is not None and self.loading_timer.isActive():
            self.loading_timer.stop()
            if self.loading_timer in self.timers:
                self.timers.remove(self.loading_timer)
            self.loading_timer = None
        
        # Hide loading label (simply hide)
        self.loading_label.hide()
        
        # Force update to refresh display
        self.image_label.update()
        QApplication.processEvents()

    def cleanup_loader_threads(self):
        """Cleans up loader threads and frees memory."""
        try:
            # Clean up using ImageLoader (added for gradual migration)
            self.image_loader.cleanup()
            
            # Remove threads that have completed or encountered an error
            current_threads = list(self.loader_threads.items())
            for path, loader in current_threads:
                # If the loader is not running (completed)
                try:
                    if not loader.isRunning():
                        # Remove thread object
                        del self.loader_threads[path]
                except Exception as e:
                    # Attempt to remove thread from the list after an error occurs
                    try:
                        del self.loader_threads[path]
                    except:
                        pass
        except Exception as e:
            pass

    def on_image_loaded(self, path, image, size_mb):
        """Callback method called when image loading is complete"""
        # Hide loading indicator
        self.hide_loading_indicator()
        
        # Process image caching
        self.handle_image_caching(path, image, size_mb)
        
        # Display only if the current path matches the loaded image path
        if self.current_image_path == path:
            # Prepare image for display (rotation, scaling)
            scaled_pixmap = self.prepare_image_for_display(image, size_mb)
            
            # Display image
            self.display_image(scaled_pixmap, path, size_mb)
        
        # Clean up loader thread
        self.cleanup_image_loader(path)
        
        # Additional: apply delayed resizing in fullscreen mode
        if self.isFullScreen():
            QTimer.singleShot(200, self.delayed_resize)
            
    def handle_image_caching(self, path, image, size_mb):
        """Method to handle image caching"""
        self.image_handler.handle_image_caching(path, image, size_mb)
    
    def prepare_image_for_display(self, image, size_mb):
        """Method to handle image transformation (rotation, scaling)"""
        return self.image_handler.prepare_image_for_display(image, size_mb)
    
    def display_image(self, scaled_pixmap, path, size_mb):
        """Method to display image on screen"""
        self.image_handler.display_image(scaled_pixmap, path, size_mb)
    
    def cleanup_image_loader(self, path):
        """Method to handle cleanup of loader threads"""
        # Cleanup threads
        if path in self.loader_threads:
            del self.loader_threads[path]

    def on_image_error(self, path, error):
        """Callback method called when an error occurs during image loading"""
        # Hide loading indicator
        self.hide_loading_indicator()
        
        # Display error message
        error_msg = f"Image load failed: {os.path.basename(path)}\n{error}"
        self.show_message(error_msg)
        
        # Cleanup threads
        if path in self.loader_threads:
            del self.loader_threads[path]

    def pause_all_timers(self):
        """모든 타이머를 일시 중지합니다."""
        for timer in self.timers:
            if timer.isActive():
                timer.stop()
        
        # 싱글샷 타이머도 중지
        for timer in self.singleshot_timers:
            if timer.isActive():
                timer.stop()

    def resume_all_timers(self):
        for timer in self.timers:
            if not timer.isActive():
                timer.start()

    def on_rotation_changed(self, angle):
        """Handles rotation change signal."""
        # Update current_rotation for compatibility
        self.current_rotation = angle
        
        # Call ImageHandler's on_rotation_changed method to immediately apply image rotation
        if hasattr(self, 'image_handler') and self.current_image_path:
            self.image_handler.on_rotation_changed(angle)

    def rotate_image(self, clockwise=True):
        """Rotate image 90 degrees."""
        if not self.current_image_path:
            return
            
        # Use RotationManager to process rotation and update UI
        self.rotation_manager.apply_rotation(clockwise)

    def update_button_sizes(self):
        """Method to update button sizes to fit the window - now delegated to ControlsLayout"""
        if hasattr(self, 'controls_layout'):
            self.controls_layout.update_button_sizes()
        else:
            # When ControlsLayout is not yet initialized (e.g., during initial loading process)
            pass

    def load_key_settings(self):
        """키 설정을 로드합니다."""
        try:
            # 기본 키 설정
            default_settings = {
                "next_image": Qt.Key_Right,
                "prev_image": Qt.Key_Left,
                "rotate_clockwise": Qt.Key_R,
                "rotate_counterclockwise": Qt.Key_L,
                "play_pause": Qt.Key_Space,
                "volume_up": Qt.Key_Up,
                "volume_down": Qt.Key_Down,
                "toggle_mute": Qt.Key_M,
                "delete_image": Qt.Key_Delete,
                "toggle_fullscreen": Qt.ControlModifier | Qt.Key_Return,  # Ctrl+Enter로 변경
                "toggle_maximize_state": Qt.Key_Return  # Enter 키 추가
            }
            
            # Use the load_settings function from the core.config module to load settings
            loaded_settings = load_settings("key_settings.json")
            
            # Apply values loaded from the existing settings file to the default settings
            for key, value in loaded_settings.items():
                if key in default_settings:
                    try:
                        # Since the values loaded from JSON can be strings or numbers, convert them to integers
                        default_settings[key] = int(value)
                    except (ValueError, TypeError) as e:
                        # If conversion fails, output an error message and retain the default value
                        pass
            
            # Assign the final settings to self.key_settings
            self.key_settings = default_settings
            
        except Exception as e:
            # If an exception occurs during loading, use the default settings
            self.key_settings = default_settings

    def save_key_settings(self):
        """Save key settings."""
        try:
            # Use the save_settings function from the core.config module to save settings
            if save_settings(self.key_settings, "key_settings.json"):
                pass
            else:
                pass
        except Exception as e:
            pass
    def show_preferences_dialog(self):
        """Displays the preferences dialog."""
        # Display key settings dialog
        dialog = PreferencesDialog(self, self.key_settings, self.mouse_settings)
        if dialog.exec_() == QDialog.Accepted:
            # Apply updated key settings
            self.key_settings = dialog.get_key_settings()
            # Save key settings
            self.save_key_settings()
            
            # Apply updated mouse settings
            self.mouse_settings = dialog.get_mouse_settings()
            # Save mouse settings
            self.save_mouse_settings()
            
            # Display message
            self.show_message("Settings have been updated.")

    def show_about_dialog(self):
        # Display about dialog
        dialog = AboutDialog(self)
        dialog.exec_()
        
    def _on_current_index_changed(self, new_value, old_value):
        """
        Observer callback called when current_index changes.
        
        Args:
            new_value: new index value
            old_value: previous index value
        """
        
    def _on_current_image_path_changed(self, new_value, old_value):
        """
        Observer callback called when current_image_path changes.
        
        Args:
            new_value: new image path
            old_value: previous image path
        """

    def cleanup_current_media(self):
        """현재 로드된 미디어 리소스를 정리합니다."""
        return self.resource_cleaner.cleanup_current_media()
    
    def cleanup_video_resources(self):
        """비디오 관련 리소스 정리"""
        if hasattr(self, 'video_handler'):
            return self.video_handler.cleanup_video_resources()
        return False
    
    def cleanup_animation_resources(self):
        """애니메이션 관련 리소스 정리"""
        return self.resource_cleaner.cleanup_animation_resources()
    
    def cleanup_ui_components(self):
        """UI 컴포넌트 초기화"""
        return self.resource_cleaner.cleanup_ui_components()
    
    # 타이머 관련 메서드를 위임
    def create_single_shot_timer(self, timeout, callback):
        """싱글샷 타이머를 생성하고 추적합니다."""
        return self.timer_manager.create_single_shot_timer(timeout, callback)
    
    def _handle_single_shot_timeout(self, timer, callback):
        """싱글샷 타이머의 타임아웃을 처리합니다."""
        return self.timer_manager._handle_single_shot_timeout(timer, callback)

    def toggle_debug_mode(self):
        """디버깅 모드를 켜고 끕니다."""
        return self.qmovie_debugger.toggle_debug_mode()
    
    def perform_garbage_collection(self):
        """가비지 컬렉션 명시적 수행"""
        return self.memory_profiler.perform_garbage_collection()
    
    def generate_qmovie_reference_graph(self):
        """QMovie 객체의 참조 그래프를 생성합니다."""
        return self.qmovie_debugger.generate_qmovie_reference_graph()
    
    # 다른 디버깅 관련 메서드를 제거하고 대체합니다
    
    def on_ui_visibility_changed(self, visibility_dict):
        """
        UI 요소 가시성 변경 이벤트 처리
        
        Args:
            visibility_dict: 각 UI 요소의 가시성 상태가 포함된 딕셔너리
        """
        # UI 요소 가시성 적용을 UI 상태 관리자에 위임
        self.ui_state_manager.apply_ui_visibility()
        
        # UI 변경 후 리사이징이 필요한 경우
        if hasattr(self, 'current_image_path') and self.current_image_path:
            file_ext = os.path.splitext(self.current_image_path)[1].lower()
 
            # RAW 파일의 경우 즉시 리사이징 적용 (문제 해결을 위해)
            if file_ext in RAW_EXTENSIONS:
                # 즉시 다중 리사이징 시도를 강제 실행
                QApplication.processEvents()
                
                # 전체 창 영역을 사용하도록 플래그 설정 (새로운 추가)
                self.image_handler.use_full_window = True
                self.image_handler.resize()
                
                # 이미지 처리 완료 후 플래그 재설정
                self.image_handler.use_full_window = False
                
                # 화면 새로고침
                QApplication.processEvents()
                self.image_label.repaint()
                self.image_label.update()
            else:
                # For non-RAW files: start delayed resizing after a set time
                if hasattr(self, 'resize_timer') and not self.resize_timer.isActive():
                    self.resize_timer.start(100)

    def mousePressEvent(self, event):
        """마우스 버튼이 눌렸을 때 이벤트 처리

        Args:
            event: 마우스 이벤트 객체
        """
        # 마우스 버튼에 따른 처리
        if event.button() == Qt.LeftButton:
            # 왼쪽 버튼은 직접 처리 (주로 UI 클릭/드래그 용도로 사용)
            # 기본 동작 유지 (Qt 이벤트 시스템에서 처리)
            super().mousePressEvent(event)
        else:
            # 중간 버튼과 오른쪽 버튼은 MouseHandler로 위임
            self.mouse_handler.handle_mouse_button(event.button())
            event.accept()  # 이벤트가 처리됨을 표시

    def show_context_menu(self):
        """Display the right-click context menu."""
        # 컨텍스트 메뉴 생성
        context_menu = QMenu(self)
        context_menu.setStyleSheet("""
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                padding: 5px;
                min-width: 200px;
            }
            QMenu::item {
                padding: 5px 20px;
                border: 1px solid transparent;
            }
            QMenu::item:selected {
                background-color: #34495e;
            }
            QMenu::separator {
                height: 1px;
                background: #34495e;
                margin: 5px 0;
            }
        """)
        
        # 이미지/미디어 관련 메뉴 항목
        # 재생/일시정지 (미디어 타입에 따라 다르게 표시)
        if hasattr(self, 'current_media_type') and self.current_media_type in ['animation', 'video']:
            is_playing = False
            if self.current_media_type == 'animation' and hasattr(self, 'animation_handler'):
                is_playing = self.animation_handler.is_playing()
            elif self.current_media_type == 'video' and hasattr(self, 'video_handler'):
                is_playing = self.video_handler.is_video_playing()
                
            play_pause_text = "Pause" if is_playing else "Play"
            play_pause_action = QAction(play_pause_text, self)
            play_pause_action.triggered.connect(self.toggle_animation_playback)
            context_menu.addAction(play_pause_action)
            
            # 구분선 추가
            context_menu.addSeparator()
        
        # 북마크 관련 메뉴
        if hasattr(self, 'bookmark_manager'):
            # 북마크 추가/제거
            is_bookmarked = False
            if hasattr(self, 'current_image_path'):
                is_bookmarked = self.bookmark_manager.is_bookmarked(self.current_image_path)
                
            bookmark_text = "Remove Bookmark" if is_bookmarked else "Add Bookmark"
            bookmark_action = QAction(bookmark_text, self)
            bookmark_action.triggered.connect(self.toggle_bookmark)
            context_menu.addAction(bookmark_action)
        
        # 이미지 회전
        rotate_menu = QMenu("Image Rotation", self)
        rotate_menu.setStyleSheet(context_menu.styleSheet())
        
        rotate_cw_action = QAction("Rotate Clockwise", self)
        rotate_cw_action.triggered.connect(lambda: self.rotate_image(True))
        rotate_menu.addAction(rotate_cw_action)
        
        rotate_ccw_action = QAction("Rotate Counterclockwise", self)
        rotate_ccw_action.triggered.connect(lambda: self.rotate_image(False))
        rotate_menu.addAction(rotate_ccw_action)
        
        context_menu.addMenu(rotate_menu)
        
        # 구분선 추가
        context_menu.addSeparator()
        
        # 파일 관련 메뉴
        if hasattr(self, 'current_image_path') and self.current_image_path:
            # 이미지 삭제
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(self.delete_current_image)
            context_menu.addAction(delete_action)
            
            # 파일 탐색기에서 열기
            open_in_explorer_action = QAction("Open in Explorer", self)
            open_in_explorer_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(self.current_image_path))))
            context_menu.addAction(open_in_explorer_action)
        
        # 화면 모드 관련 메뉴
        fullscreen_action = QAction("Toggle Fullscreen", self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        context_menu.addAction(fullscreen_action)
        
        # 구분선 추가
        context_menu.addSeparator()
        
        # 환경설정 메뉴 추가
        settings_action = QAction("Preferences", self)
        settings_action.triggered.connect(self.show_preferences_dialog)
        context_menu.addAction(settings_action)
        
        # 메뉴 표시
        cursor_pos = QCursor.pos()
        context_menu.popup(cursor_pos)

    def load_mouse_settings(self):
        """마우스 설정을 로드합니다."""
        try:
            # 기본 마우스 설정
            default_settings = {
                "middle_click": "toggle_play",         # 중간 버튼: 재생/일시정지
                "right_click": "context_menu",         # 오른쪽 버튼: 컨텍스트 메뉴
                "double_click": "toggle_fullscreen",   # 더블 클릭: 전체화면
                "wheel_up": "prev_image",              # 휠 위로: 이전 이미지
                "wheel_down": "next_image",            # 휠 아래로: 다음 이미지
                "ctrl_wheel_up": "volume_up",          # Ctrl + 휠 위로: 볼륨 증가
                "ctrl_wheel_down": "volume_down",      # Ctrl + 휠 아래로: 볼륨 감소
                "shift_wheel_up": "rotate_counterclockwise",  # Shift + 휠 위로: 반시계방향 회전
                "shift_wheel_down": "rotate_clockwise",  # Shift + 휠 아래로: 시계방향 회전
                "wheel_cooldown_ms": 500               # 휠 이벤트 쿨다운 (밀리초)
            }
            
            # 설정 파일 로드
            loaded_settings = load_settings("mouse_settings.json")
            
            # 기존 설정 파일에서 값을 불러와 기본 설정에 적용합니다
            for key, value in loaded_settings.items():
                if key in default_settings:
                    # wheel_cooldown은 숫자로 변환, 나머지는 문자열로 사용
                    if key == "wheel_cooldown_ms":
                        try:
                            default_settings[key] = int(value)
                        except (ValueError, TypeError) as e:
                            # 변환할 수 없는 경우 오류 메시지 출력하고 기본값 유지
                            pass
                    else:
                        default_settings[key] = value
            
            # 최종 설정을 self.mouse_settings에 할당합니다
            self.mouse_settings = default_settings
            
        except Exception as e:
            # 로드 중 예외가 발생하면 기본 설정을 사용합니다
            self.mouse_settings = default_settings

    def save_mouse_settings(self):
        """마우스 설정을 저장합니다."""
        try:
            # core.config 모듈의 save_settings 함수를 사용해 설정을 저장합니다
            if save_settings(self.mouse_settings, "mouse_settings.json"):
                pass
            else:
                pass
        except Exception as e:
            pass

    def open_feedback(self):
        """GitHub Discussions 페이지를 웹 브라우저에서 엽니다."""
        feedback_url = "https://github.com/htpaak/ArchiveSift/discussions"
        QDesktopServices.openUrl(QUrl(feedback_url))

    def go_to_index(self, index):
        """Go to the specified index in the image list."""
        if 0 <= index < len(self.image_files):
            # 인덱스 및 상태 업데이트
            self.current_index = index
            self.state_manager.set_state("current_index", self.current_index)
            
            # 현재 경로 업데이트
            current_path = self.image_files[self.current_index]
            self.current_image_path = current_path
            
            # file_navigator와 동기화
            if hasattr(self, 'file_navigator') and self.file_navigator:
                self.file_navigator.set_current_index(self.current_index)
            
            # 이미지 표시
            self.show_image(self.image_files[self.current_index])
            
            # UI 업데이트
            self.update_image_info()
            self.update_bookmark_ui()

    def copy_image_to_folder(self, folder_path):
        # 현재 이미지 경로가 존재하고, 폴더 경로도 제공되었으면 복사를 시작합니다.
        if self.current_image_path and folder_path:
            # FileOperations 클래스를 사용하여 파일 복사
            success, _ = self.file_operations.copy_file_to_folder(self.current_image_path, folder_path)
            
            # 복사 성공 시 다음 이미지로 이동
            if success:
                self.show_next_image()

    def move_image_to_folder(self, folder_path):
        """
        Moves the current image to the specified folder.
        현재 이미지를 지정된 폴더로 이동합니다.
        
        Args:
            folder_path: Target folder path
        """
        if self.current_image_path and folder_path:
            # Move the file using FileOperations
            self.file_operations.move_file_to_folder(self.current_image_path, folder_path)
            
            # 파일 이동 후 추가 로직은 FileOperations 클래스에서 처리됨

    def undo_last_deletion(self):
        """
        마지막으로 삭제된 파일을 복원합니다.
        (이전 버전 호환성을 위해 유지)
        """
        if not hasattr(self, 'undo_manager'):
            self.show_message("Undo feature is not available.")
            return
            
        success, restored_path = self.undo_manager.undo_last_deletion()
        
        if success and restored_path:
            # 복원된 파일이 표시되도록 UndoManager에서 처리함
            # 파일 목록 업데이트
            self.image_files = self.file_navigator.get_files()
            # 현재 인덱스 업데이트
            self.current_index = self.file_navigator.get_current_index()
            # 이미지 정보 업데이트 (인덱스 표시)
            self.update_image_info()
            # 복원된 파일 표시는 UndoManager에서 이미 처리됨
        elif not success and not restored_path:
            # 실패 메시지는 UndoManager에서 이미 표시함
            pass
            
    def undo_last_action(self):
        """
        마지막으로 수행한 작업(삭제, 이동, 복사)을 취소합니다.
        """
        if not hasattr(self, 'undo_manager'):
            self.show_message("Undo feature is not available.")
            return
            
        success, restored_path = self.undo_manager.undo_last_action()
        
        if success and restored_path:
            # 복원된 파일이 표시되도록 UndoManager에서 처리함
            # 파일 목록 업데이트
            self.image_files = self.file_navigator.get_files()
            # 현재 인덱스 업데이트
            self.current_index = self.file_navigator.get_current_index()
            # 이미지 정보 업데이트 (인덱스 표시)
            self.update_image_info()
            # 복원된 파일 표시는 UndoManager에서 이미 처리됨
        elif not success and not restored_path:
            # 실패 메시지는 UndoManager에서 이미 표시함
            pass

    def update_undo_button_state(self, enabled):
        """
        Undo 버튼의 상태를 업데이트합니다.
        
        Args:
            enabled (bool): 활성화 여부
        """
        if hasattr(self, 'undo_button') and self.undo_button:
            self.undo_button.setEnabled(enabled)
            
    def update_undo_state(self, enabled):
        """
        Undo 버튼의 상태를 업데이트하는 대체 메서드입니다.
        
        Args:
            enabled (bool): 활성화 여부
        """
        if hasattr(self, 'undo_button') and self.undo_button:
            self.undo_button.setEnabled(enabled)

# Main function
def main():
    app = QApplication(sys.argv)  # Qt application instance creation
    app.setApplicationName("ArchiveSift")  # Set application name
    
    # 작업 표시줄 아이콘 설정
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core', 'ArchiveSift.ico')
    if not os.path.exists(icon_path):
        icon_path = 'core/ArchiveSift.ico'
    
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)
    
    # Windows에서 작업 표시줄 아이콘 설정
    if platform.system() == 'Windows':
        try:
            import ctypes
            myappid = 'ArchiveSift.ImageViewer.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Windows taskbar icon setting error: {e}")
    
    viewer = ArchiveSift()  # Create instance of ArchiveSift class
    viewer.show()  # Display viewer window
    exit_code = app.exec_()  # Execute event loop
    sys.exit(exit_code)

# Execute main() function when program is run
if __name__ == "__main__":
    main()  # Call main function