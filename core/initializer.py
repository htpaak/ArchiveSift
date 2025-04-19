# app/core/initializer.py

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import platform
import sys

# main.py에서 사용되는 모듈들을 상대 경로로 가져옵니다.
# 경로 관련 기능
from core.utils.path_utils import get_app_directory, get_user_data_directory
# 유틸리티 함수
from core.utils.time_utils import format_time
from core.utils.sort_utils import atoi, natural_keys
# 캐시 관리 기능
from media.loaders.cache_manager import LRUCache
# 설정 관리
from core.config_manager import load_settings, save_settings
# 파일 형식 감지
from media.format_detector import FormatDetector
# 이미지 로딩 기능
from media.loaders.image_loader import ImageLoaderThread
from media.loaders.image_loader import ImageLoader, ImageLoaderThread
# 미디어 처리
from media.handlers.image_handler import ImageHandler
from media.handlers.psd_handler import PSDHandler
from media.handlers.video_handler import VideoHandler
from media.handlers.animation_handler import AnimationHandler
from media.handlers.audio_handler import AudioHandler
from media.handlers.image_handler import RAW_EXTENSIONS
# 사용자 정의 UI 위젯
from ui.components.slider import ClickableSlider
from ui.components.scrollable_menu import ScrollableMenu
from ui.components.control_buttons import (
    OpenFolderButton, SetBaseFolderButton, PlayButton, RotateButton,
    MuteButton, MenuButton, BookmarkButton, UILockButton,
    MinimizeButton, MaximizeButton, FullscreenButton, CloseButton, TitleLockButton
)
from ui.components.media_display import MediaDisplay
# 레이아웃
from ui.layouts.main_layout import MainLayout
from ui.layouts.controls_layout import ControlsLayout
# 대화상자
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.preferences_dialog import PreferencesDialog
from events.handlers.keyboard_handler import KeyboardHandler, KeyInputEdit
from events.handlers.mouse_handler import MouseHandler
from events.handlers.window_handler import WindowHandler
# 북마크 관리
from features.bookmark import BookmarkManager
# 회전 기능
from features.rotation.rotation_manager import RotationManager
from features.rotation.rotation_ui import RotationUI
# UI 잠금 기능
from features.ui_lock.ui_lock_manager import UILockManager
from features.ui_lock.ui_lock_ui import UILockUI
# UI 상태 관리
from core.ui.ui_state_manager import UIStateManager
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

from ui.components.dual_action_button import DualActionButton
from ui.components.custom_tooltip import TooltipManager # TooltipManager import
from ui.components.loading_indicator import LoadingIndicator # LoadingIndicator 추가
from ui.components.editable_index import EditableIndexLabel # EditableIndexLabel 추가

# MPV 래퍼
from mpv_wrapper import mpv

# 디버깅 모듈
from core.debug import QMovieDebugger, MemoryProfiler
# 메모리 관리 모듈
from core.memory import ResourceCleaner, TimerManager
# 이벤트 핸들러
from events.handlers.button_handler import ButtonEventHandler


class ArchiveSiftInitializer:
    def initialize(self, viewer):
        """
        ArchiveSift 뷰어의 초기화를 담당하는 메서드

        Args:
            viewer: ArchiveSift 인스턴스
        """
        viewer.logger = Logger("ArchiveSift")
        viewer.logger.info("Image viewer initialization start")

        # TooltipManager import는 클래스 정의 밖으로 이동했습니다.
        # 툴팁 매니저 초기화
        viewer.tooltip_manager = TooltipManager(viewer)

        viewer.setWindowTitle('Image Viewer')  # 창 제목 설정

        # 작업 표시줄 아이콘 설정 (절대 경로와 여러 대체 경로 시도)
        icon_paths = [
            './core/ArchiveSift.ico',
            'core/ArchiveSift.ico',
            os.path.join(get_app_directory(), 'core', 'ArchiveSift.ico'),
            'ArchiveSift.ico',
            './ArchiveSift.ico'
        ]

        # 찾은 첫 번째 유효한 아이콘 경로 사용
        icon_path = None
        for path in icon_paths:
            # 경로 정규화 추가
            normalized_path = os.path.normpath(path)
            if os.path.exists(normalized_path):
                icon_path = normalized_path
                print(f"Found window icon at: {icon_path}")
                break

        if icon_path:
            viewer.setWindowIcon(QIcon(icon_path))  # 앱 아이콘 설정
        else:
            # 기본 경로로 설정 (존재하지 않더라도)
            default_icon_path = os.path.normpath('core/ArchiveSift.ico') # 프로젝트 루트 기준
            viewer.setWindowIcon(QIcon(default_icon_path))
            print(f"Warning: Could not find icon file, using default path: {default_icon_path}")

        viewer.setGeometry(100, 100, 800, 600)  # 창 위치와 크기 설정

        # 키 설정 로드 - 키보드 단축키를 저장하는 사전
        viewer.load_key_settings()

        # 마우스 설정 로드 - 마우스 버튼 액션을 저장하는 사전
        viewer.load_mouse_settings()

        # 폴더 및 파일 관련 변수 초기화
        viewer.current_folder = ""  # 현재 폴더 경로
        viewer.image_files = []     # 이미지 파일 리스트

        # 앱 데이터 디렉토리 확인 및 생성
        app_data_dir = get_user_data_directory()
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir, exist_ok=True)

        # 상태 관리자 초기화
        viewer.state_manager = StateManager()

        # 기본 상태 설정
        viewer.state_manager.set_state("initialized", True)
        viewer.state_manager.set_state("app_version", get_version_string())
        viewer.state_manager.set_state("app_data_dir", app_data_dir)
        viewer.state_manager.set_state("boundary_navigation", True)

        # 상태 옵저버 등록 (current_index와 current_image_path 상태 변경 감지)
        viewer.state_manager.register_observer("current_index", viewer._on_current_index_changed)
        viewer.state_manager.register_observer("current_image_path", viewer._on_current_image_path_changed)

        # 경계 내비게이션 플래그 초기화
        viewer.is_boundary_navigation = False
        viewer.current_index = 0  # 현재 표시 중인 이미지 인덱스 (0으로 초기화)
        viewer.state_manager.set_state("current_index", viewer.current_index)  # 상태 관리자에도 설정
        viewer.current_image_path = ""  # 현재 표시 중인 이미지 경로
        viewer.state_manager.set_state("current_image_path", viewer.current_image_path)  # 상태 관리자에도 설정

        # 변수 초기화
        viewer.base_folder = ""  # 기준 폴더 경로
        viewer.folder_buttons = []  # 폴더 버튼 목록

        # 키보드 핸들러 초기화
        viewer.keyboard_handler = KeyboardHandler(viewer)

        # 북마크 관리자, 회전 관리자 및 UI 잠금 관리자 초기화
        viewer.bookmark_manager = BookmarkManager(viewer)

        # 디버깅 관련 인스턴스 생성
        viewer.qmovie_debugger = QMovieDebugger(viewer)
        viewer.memory_profiler = MemoryProfiler()

        # 메모리 관리 인스턴스 생성
        viewer.resource_cleaner = ResourceCleaner(viewer)
        viewer.timer_manager = TimerManager(viewer)
        viewer.singleshot_timers = viewer.timer_manager.singleshot_timers  # 호환성 유지

        # 회전 관리자 초기화
        viewer.rotation_manager = RotationManager(viewer) # viewer 전달
        viewer.rotation_ui = RotationUI(viewer, viewer.rotation_manager)
        viewer.ui_lock_manager = UILockManager()

        # 마우스 이벤트 핸들러 초기화
        viewer.mouse_handler = MouseHandler(viewer)

        # 버튼 이벤트 핸들러 초기화
        viewer.button_handler = ButtonEventHandler(viewer)

        # 윈도우 이벤트 핸들러 초기화
        viewer.window_handler = WindowHandler(viewer)

        # 파일 브라우저 생성
        viewer.file_browser = FileBrowser(parent=viewer)
        # 파일 내비게이터 생성
        viewer.file_navigator = FileNavigator(parent=viewer)
        # 파일 작업 관리자 생성
        viewer.file_operations = FileOperations(viewer=viewer)
        # Undo 관리자 생성
        viewer.undo_manager = UndoManager(viewer=viewer)
        # Undo 버튼 참조 저장을 위한 변수 (나중에 설정됨)
        viewer.undo_button = None

        # 북마크 관리자 초기화
        # viewer.bookmark_manager = BookmarkManager(viewer) # 위에서 이미 초기화 됨

        # 회전 관리자 초기화
        # viewer.rotation_manager = RotationManager(viewer) # 위에서 이미 초기화 됨

        viewer.installEventFilter(viewer)

        # 북마크 데이터 불러오기
        viewer.load_bookmarks()

        # UI 설정 후 마우스 추적 설정
        # image_label은 아래에서 초기화되므로, 초기화 후에 설정
        # if hasattr(viewer, 'image_label'):
        #     viewer.image_label.setMouseTracking(True)
        viewer.setMouseTracking(True)

        # 비동기 이미지 로딩 관련 변수 초기화
        viewer.loader_threads = {}  # 로더 스레드 추적용 딕셔너리 (경로: 스레드)
        viewer.image_loader = ImageLoader()  # 이미지 로더 매니저 초기화
        viewer.loading_label = QLabel("Loading...", viewer)  # 로딩 중 표시용 레이블
        viewer.loading_label.setAlignment(Qt.AlignCenter)  # 중앙 정렬
        viewer.loading_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(52, 73, 94, 0.9);
                font-size: 24px;
                padding: 20px;
                border-radius: 10px;
            }
        """)
        viewer.loading_label.hide()  # 처음에는 숨김
        viewer.is_loading = False  # 로딩 상태 추적
        viewer.loading_timer = None  # 로딩 타이머

        # OpenCV 비디오 캡처 객체 초기화
        viewer.cap = None

        # MPV DLL 경로 설정 (동적 라이브러리 로드 경로) - 이 부분은 mpv_wrapper에서 처리하도록 수정될 수 있음
        # MPV 관련 설정은 mpv_wrapper.py 또는 전역 설정에서 처리하는 것이 더 적절할 수 있음
        # system = platform.system()
        # ... (MPV DLL 경로 설정 코드 제거)

        # MPV 플레이어 초기화
        try:
            viewer.player = mpv.MPV(log_handler=print,
                                 ytdl=True,
                                 input_default_bindings=True,
                                 input_vo_keyboard=True,
                                 hwdec='no')  # 하드웨어 가속 비활성화
            viewer.player.loop = True
            viewer.player.keep_open = True
            viewer.player.terminal = False
            print("MPV player initialization successful")
        except Exception as e:
            print(f"MPV player initialization failed: {e}")
            viewer.player = None

        # 리소스 관리를 위한 객체 추적
        viewer.timers = []  # 모든 타이머 추적 - 먼저 초기화
        viewer.singleshot_timers = []  # 싱글샷 타이머 추적을 위한 리스트 추가

        # 화면 해상도의 75%로 초기 창 크기 설정
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.75)
        height = int(screen.height() * 0.75)
        viewer.resize(width, height)

        # 미디어 타입 추적 변수 초기화
        viewer.current_media_type = None
        viewer.is_slider_dragging = False

        # 창을 화면 중앙에 위치시키기
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        viewer.move(x, y)

        # 창 크기 조절 관련 변수 초기화
        viewer.resize_direction = None
        viewer.resizing = False
        viewer.resize_start_pos = None
        viewer.resize_start_geometry = None

        # 최소 창 크기 설정
        viewer.setMinimumSize(400, 300)

        # 버튼 스타일 정의 - 각 버튼 클래스에서 관리

        # 슬라이더 스타일 정의
        viewer.slider_style = """
            QSlider {
                background-color: rgba(52, 73, 94, 0.6); border: none; border-radius: 3px; padding: 0px; margin: 0px; height: 100%;
            }
            QSlider:hover { background-color: rgba(52, 73, 94, 1.0); }
            QSlider::groove:horizontal { border: none; height: 8px; background: rgba(30, 30, 30, 0.8); border-radius: 4px; margin: 0px; }
            QSlider::handle:horizontal { background: #ffffff; border: 2px solid #ffffff; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; }
            QSlider::add-page:horizontal { background: rgba(0, 0, 0, 0.5); border-radius: 4px; }
            QSlider::sub-page:horizontal { background: rgba(255, 255, 255, 0.8); border-radius: 4px; }
            """

        # 프레임리스 윈도우 설정
        viewer.setWindowFlags(Qt.FramelessWindowHint)

        # 배경색을 흰색으로 설정
        viewer.setStyleSheet("background-color: white;")

        # 메인 레이아웃 설정
        viewer.main_layout = MainLayout(viewer)
        layout = QVBoxLayout(viewer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 제목 표시줄
        viewer.title_bar = QWidget(viewer)
        viewer.title_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        viewer.title_bar.setObjectName("title_bar")
        viewer.title_bar.setStyleSheet("""
            QWidget#title_bar { background-color: #34495e; }
            QLabel { color: white; background-color: transparent; }
        """)

        # 타이틀바 컨트롤 저장을 위한 딕셔너리
        viewer.title_bar.controls = {}

        title_layout = QHBoxLayout(viewer.title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(2)
        title_layout.setAlignment(Qt.AlignVCenter)

        # 앱 아이콘 레이블 추가
        app_icon_label = QLabel()
        app_icon_pixmap = QIcon(icon_path if icon_path else './core/ArchiveSift.ico').pixmap(20, 20)
        app_icon_label.setPixmap(app_icon_pixmap)
        app_icon_label.setStyleSheet("background-color: transparent;")
        app_icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        title_layout.addWidget(app_icon_label)
        viewer.title_bar.controls['app_icon_label'] = app_icon_label

        # 제목 텍스트 레이블
        title_label = QLabel("ArchiveSift")
        title_label.setStyleSheet("""
            QLabel { color: white; background-color: transparent; padding: 2px 8px; font-size: 12px; font-weight: bold; }
        """)
        title_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        title_layout.addWidget(title_label)
        viewer.title_bar.controls['title_label'] = title_label
        title_layout.addStretch()

        # 상단 UI 잠금 버튼 추가
        title_lock_btn = TitleLockButton(viewer)
        title_lock_btn.connect_action(viewer.toggle_title_ui_lock)
        viewer.title_lock_btn = title_lock_btn
        viewer.title_bar.controls['title_lock_button'] = title_lock_btn

        # 피드백 버튼 추가
        feedback_button = QPushButton(viewer)
        feedback_button.setStyleSheet("""
            QPushButton { background-color: transparent; color: white; border: none; }
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.2); }
            QPushButton:pressed { background-color: rgba(0, 0, 0, 0.3); }
        """)
        feedback_button.setText("💬")
        feedback_button.setToolTip("피드백")
        feedback_button.clicked.connect(viewer.open_feedback)
        title_layout.addWidget(feedback_button)
        viewer.title_bar.controls['feedback_button'] = feedback_button

        # 창 컨트롤 버튼들
        min_btn = MinimizeButton(viewer)
        min_btn.connect_action(viewer.showMinimized)
        viewer.title_bar.controls['minimize_button'] = min_btn

        max_btn = MaximizeButton(viewer)
        max_btn.connect_action(viewer.toggle_maximize_state)
        viewer.max_btn = max_btn
        viewer.title_bar.controls['maximize_button'] = max_btn

        fullscreen_btn = FullscreenButton(viewer)
        fullscreen_btn.connect_action(viewer.toggle_fullscreen)
        viewer.fullscreen_btn = fullscreen_btn
        viewer.title_bar.controls['fullscreen_button'] = fullscreen_btn

        close_btn = CloseButton(viewer)
        close_btn.connect_action(viewer.close)
        viewer.title_bar.controls['close_button'] = close_btn

        # 창 컨트롤 버튼들 레이아웃에 추가
        title_layout.addWidget(title_lock_btn)
        title_layout.addWidget(min_btn)
        title_layout.addWidget(max_btn)
        title_layout.addWidget(fullscreen_btn)
        title_layout.addWidget(close_btn)

        # 각 주요 요소의 기본 비율 정의 (하단은 내부 요소 합으로 계산됨)
        viewer.title_stretch = 2
        viewer.slider_stretch = 3
        
        # 버튼 줄 수 및 줄당 비율 정의
        viewer.button_row_stretch = 2
        layout_settings = load_settings("layout_settings.json")
        try:
            # 저장된 값이 정수형인지 확인 후 로드
            loaded_button_rows = int(layout_settings.get("button_rows", 5))
            if not 1 <= loaded_button_rows <= 5:
                 loaded_button_rows = 5 # 유효 범위 벗어나면 기본값
        except (ValueError, TypeError):
            loaded_button_rows = 5 # 유효하지 않으면 기본값
            
        viewer.current_button_rows = loaded_button_rows # 현재 적용된 줄 수 저장
        
        # 버튼 컨테이너 비율 계산 (로드된 값 사용)
        viewer.button_stretch = viewer.current_button_rows * viewer.button_row_stretch
        
        # 하단 전체 및 메인 레이아웃 비율 계산
        viewer.total_bottom_stretch = viewer.slider_stretch + viewer.button_stretch
        viewer.main_stretch = 100 - (viewer.title_stretch + viewer.total_bottom_stretch)
        
        # 제목 표시줄을 메인 레이아웃에 추가 (저장된 비율 사용)
        layout.addWidget(viewer.title_bar, viewer.title_stretch)

        # 메인 레이아웃을 레이아웃에 추가 (계산된 비율 사용)
        layout.addWidget(viewer.main_layout, viewer.main_stretch)

        # 북마크 메뉴 초기화
        viewer.bookmark_manager.update_bookmark_menu()

        # 이미지 표시 레이블
        viewer.image_label = MediaDisplay()
        viewer.image_label.setMouseTracking(True)

        # 이미지 정보 표시 레이블
        viewer.image_info_label = EditableIndexLabel(viewer)
        viewer.image_info_label.setAlignment(Qt.AlignCenter)
        viewer.image_info_label.hide()
        viewer.image_info_label.indexChanged.connect(viewer.go_to_index)

        # 하단 컨트롤 레이아웃
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)

        # 통합 하단 UI 컨테이너 생성
        viewer.bottom_ui_container = QWidget()
        viewer.bottom_ui_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        viewer.bottom_ui_container.setContentsMargins(0, 0, 0, 0)

        # 최소 높이를 동적 비율 기반으로 설정
        initial_window_height = viewer.height() # 현재 viewer의 높이 사용
        min_height = int(initial_window_height * (viewer.total_bottom_stretch / 100.0))
        viewer.bottom_ui_container.setMinimumHeight(min_height)

        bottom_ui_layout = QVBoxLayout(viewer.bottom_ui_container)
        bottom_ui_layout.setContentsMargins(0, 0, 0, 0)
        bottom_ui_layout.setSpacing(0)
        bottom_ui_layout.setAlignment(Qt.AlignTop | Qt.AlignVCenter)

        # 슬라이더 위젯과 레이아웃
        viewer.slider_widget = QWidget()
        viewer.slider_widget.setStyleSheet("background-color: rgba(52, 73, 94, 0.9); border: none; padding: 0px; margin: 0px;")
        viewer.slider_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        new_slider_layout = QHBoxLayout(viewer.slider_widget)
        new_slider_layout.setContentsMargins(0, 0, 0, 0)
        new_slider_layout.setSpacing(2)
        new_slider_layout.setAlignment(Qt.AlignTop | Qt.AlignVCenter | Qt.AlignHCenter | Qt.AlignJustify)

        # 컨트롤 버튼 생성 및 추가
        viewer.open_button = OpenFolderButton(viewer)
        viewer.open_button.connect_action(viewer.open_folder)
        viewer.open_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_slider_layout.addWidget(viewer.open_button)

        viewer.set_base_folder_button = SetBaseFolderButton(viewer)
        viewer.set_base_folder_button.connect_action(viewer.set_base_folder)
        viewer.set_base_folder_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_slider_layout.addWidget(viewer.set_base_folder_button)

        viewer.play_button = PlayButton(viewer)
        viewer.play_button.connect_action(viewer.toggle_animation_playback)
        viewer.play_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_slider_layout.addWidget(viewer.play_button)

        viewer.rotate_ccw_button = RotateButton(clockwise=False, parent=viewer)
        viewer.rotate_ccw_button.connect_action(lambda: viewer.rotate_image(False))
        viewer.rotate_ccw_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_slider_layout.addWidget(viewer.rotate_ccw_button)

        viewer.rotate_cw_button = RotateButton(clockwise=True, parent=viewer)
        viewer.rotate_cw_button.connect_action(lambda: viewer.rotate_image(True))
        viewer.rotate_cw_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_slider_layout.addWidget(viewer.rotate_cw_button)

        viewer.playback_slider = ClickableSlider(Qt.Horizontal, viewer)
        viewer.playback_slider.setRange(0, 100)
        viewer.playback_slider.setValue(0)
        viewer.playback_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        viewer.playback_slider.clicked.connect(viewer.slider_clicked)
        new_slider_layout.addWidget(viewer.playback_slider, 10)

        viewer.time_label = QLabel("00:00 / 00:00", viewer)
        viewer.time_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        viewer.time_label.setStyleSheet("""
            QLabel { background-color: rgba(52, 73, 94, 0.6); color: white; border: none; border-radius: 3px; qproperty-alignment: AlignCenter; padding: 0px; }
            QLabel:hover { background-color: rgba(52, 73, 94, 1.0); }
        """)
        viewer.time_label.setAlignment(Qt.AlignCenter)
        new_slider_layout.addWidget(viewer.time_label)

        viewer.mute_button = MuteButton(viewer)
        viewer.mute_button.connect_action(viewer.toggle_mute)
        viewer.mute_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_slider_layout.addWidget(viewer.mute_button)

        viewer.volume_slider = ClickableSlider(Qt.Horizontal, viewer)
        viewer.volume_slider.setRange(0, 100)
        viewer.volume_slider.setValue(100)
        viewer.volume_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        viewer.volume_slider.setFixedWidth(80)
        viewer.volume_slider.connect_to_volume_control(viewer.adjust_volume)
        new_slider_layout.addWidget(viewer.volume_slider)

        viewer.menu_button = MenuButton(viewer)
        viewer.menu_button.connect_action(viewer.show_menu_above)
        viewer.menu_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_slider_layout.addWidget(viewer.menu_button)

        viewer.slider_bookmark_btn = BookmarkButton(viewer)
        viewer.slider_bookmark_btn.connect_action(viewer.show_bookmark_menu_above)
        viewer.slider_bookmark_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_slider_layout.addWidget(viewer.slider_bookmark_btn)
        viewer.bookmark_manager.set_bookmark_button(viewer.slider_bookmark_btn)

        viewer.ui_lock_btn = UILockButton(viewer)
        viewer.ui_lock_btn.connect_action(viewer.toggle_ui_lock)
        viewer.ui_lock_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        new_slider_layout.addWidget(viewer.ui_lock_btn)

        # 슬라이더바 컨트롤 리스트 생성
        viewer.slider_controls = [
            viewer.open_button, viewer.set_base_folder_button, viewer.play_button,
            viewer.rotate_ccw_button, viewer.rotate_cw_button, viewer.time_label,
            viewer.mute_button, viewer.menu_button, viewer.slider_bookmark_btn,
            viewer.ui_lock_btn
        ]

        # 새로운 슬라이더 위젯을 하단 레이아웃에 추가
        bottom_ui_layout.addWidget(viewer.slider_widget, viewer.slider_stretch)

        # 버튼 컨테이너 위젯 생성
        button_container = QWidget()
        viewer.button_container = button_container
        button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        button_container_layout = QVBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.setSpacing(0)

        # --- 제거 시작: 기존 인라인 버튼 생성 로직 ---
        # # 폴더 버튼 생성
        # viewer.buttons = []
        # total_width = viewer.width() # viewer 사용
        # # for row_idx in range(total_button_rows - 1): # 마지막 줄 제외하고 폴더 버튼 행 생성
        # for row_idx in range(viewer.current_button_rows - 1): # 마지막 줄 제외하고 폴더 버튼 행 생성
        #     row_widget = QWidget()
        #     row_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        #     button_layout = QHBoxLayout(row_widget)
        #     button_layout.setContentsMargins(0, 0, 0, 0)
        #     button_layout.setSpacing(0)
        #     button_row = []
        # 
        #     # 사용 가능한 너비 계산 (초기 창 크기 기준)
        #     available_width = total_width - button_layout.contentsMargins().left() - button_layout.contentsMargins().right()
        #     button_width = max(1, available_width // 20) # 0으로 나누는 것을 방지
        # 
        #     for i in range(20):
        #         empty_button = DualActionButton('', viewer)
        #         empty_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        #         empty_button.clicked.connect(viewer.on_button_click)
        # 
        #         if i == 19:
        #             remaining_width = total_width - (button_width * 19)
        #             empty_button.setFixedWidth(remaining_width)
        #         else:
        #             empty_button.setFixedWidth(button_width)
        # 
        #         button_row.append(empty_button)
        #         button_layout.addWidget(empty_button)
        # 
        #     viewer.buttons.append(button_row)
        #     # button_container_layout.addWidget(row_widget, 2) # 비율 적용 방식 변경
        #     button_container_layout.addWidget(row_widget)
        # 
        # # 마지막 행 (Undo 버튼 포함)
        # last_row_widget = QWidget()
        # last_row_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        # last_button_layout = QHBoxLayout(last_row_widget)
        # last_button_layout.setContentsMargins(0, 0, 0, 0)
        # last_button_layout.setSpacing(0)
        # last_button_row = []
        # 
        # # 사용 가능한 너비 계산 (초기 창 크기 기준)
        # available_width = total_width - last_button_layout.contentsMargins().left() - last_button_layout.contentsMargins().right()
        # button_width = max(1, available_width // 20) # 0으로 나누는 것을 방지
        # 
        # for i in range(20):
        #     if i == 19:
        #         empty_button = QPushButton('Undo', viewer)
        #         empty_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        #         empty_button.setStyleSheet("""\n        #             QPushButton { background-color: rgba(241, 196, 15, 0.9); color: white; border: none; border-radius: 3px; font-weight: bold; }\n        #             QPushButton:hover { background-color: rgba(241, 196, 15, 1.0); }\n        #         """)
        #         empty_button.clicked.connect(viewer.undo_last_action)
        #         viewer.undo_button = empty_button # viewer 사용
        #         viewer.undo_button.setEnabled(False)
        #         # viewer.undo_manager.undo_status_changed.connect(viewer.update_undo_button_state) # viewer 사용
        #         # connect는 viewer 객체가 완전히 생성된 후에 호출되어야 함
        #         # UndoManager 시그널 연결 (재생성 시 필요)
        #         # try: 
        #         #     viewer.undo_manager.undo_status_changed.disconnect(viewer.update_undo_button_state)
        #         # except TypeError:
        #         #     pass 
        #         # viewer.undo_manager.undo_status_changed.connect(lambda enabled: viewer.update_undo_button_state(enabled))
        #         viewer.undo_manager.undo_status_changed.connect(viewer.update_undo_button_state) # 시그널 직접 연결
        # 
        #         remaining_width = total_width - (int(button_width) * 19)
        #         empty_button.setFixedWidth(remaining_width)
        #     else:
        #         empty_button = DualActionButton('', viewer)
        #         empty_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        #         empty_button.clicked.connect(viewer.on_button_click)
        #         empty_button.setFixedWidth(int(button_width))
        # 
        #     last_button_row.append(empty_button)
        #     last_button_layout.addWidget(empty_button)
        # 
        # viewer.buttons.append(last_button_row)
        # # button_container_layout.addWidget(last_row_widget, 2)
        # button_container_layout.addWidget(last_row_widget)
        # --- 제거 끝 ---
        
        # --- 추가 시작: 헬퍼 메서드 호출로 버튼 생성 ---
        viewer._create_button_rows(viewer.current_button_rows)
        # --- 추가 끝 ---

        # 버튼 컨테이너를 bottom_ui_layout에 추가
        bottom_ui_layout.addWidget(viewer.button_container, viewer.button_stretch)
        
        # bottom_ui_container를 메인 레이아웃에 동적 비율로 추가 (저장된 비율 사용)
        # total_bottom_stretch = viewer.slider_stretch + viewer.button_stretch # 이미 계산됨
        layout.addWidget(viewer.bottom_ui_container, viewer.total_bottom_stretch)

        # 메인 레이아웃에 이미지 컨테이너 추가
        viewer.main_layout.set_media_display(viewer.image_label)

        # ControlsLayout 인스턴스 생성
        viewer.controls_layout = ControlsLayout(viewer)

        # MPV 상태 확인을 위한 타이머 설정
        viewer.play_button_timer = QTimer(viewer)
        viewer.play_button_timer.timeout.connect(viewer.controls_layout.update_play_button)
        viewer.play_button_timer.start(200)
        viewer.timers.append(viewer.play_button_timer)

        # 슬라이더 시그널 연결
        viewer.playback_slider.sliderPressed.connect(viewer.slider_pressed)
        viewer.playback_slider.sliderReleased.connect(viewer.slider_released)
        viewer.playback_slider.valueChanged.connect(viewer.seek_video)
        viewer.playback_slider.clicked.connect(viewer.slider_clicked)

        viewer.setFocusPolicy(Qt.StrongFocus)

        # 마우스 트래킹 활성화
        viewer.setMouseTracking(True)
        viewer.image_label.setMouseTracking(True)

        # 전역 이벤트 필터 설치
        QApplication.instance().installEventFilter(viewer)

        # MPV 경로 설정 - 이미 위에서 처리함
        # ...

        # MPV 플레이어 객체 생성 - 이미 위에서 처리함
        # viewer.player = mpv.MPV(...)

        # 슬라이더와 음량 조절 동기화
        viewer.volume_slider.connect_to_volume_control(viewer.adjust_volume)

        # 슬라이더 스타일 적용
        viewer.playback_slider.setStyleSheet(viewer.slider_style)
        viewer.volume_slider.setStyleSheet(viewer.slider_style)

        viewer.previous_position = None

        # 창 로드 후 이미지 정보 업데이트 타이머
        QTimer.singleShot(0, viewer.update_image_info) # 0ms 지연으로 즉시 실행과 유사하게
        QTimer.singleShot(100, viewer.update_image_info)

        # 이미지 캐시 초기화
        viewer.image_cache = LRUCache(10)
        viewer.gif_cache = LRUCache(3)
        viewer.psd_cache = LRUCache(3)

        viewer.last_wheel_time = 0
        # viewer.wheel_cooldown_ms = 1000 # mouse_settings에서 로드하도록 변경

        # 메뉴 관련 변수 초기화
        viewer.dropdown_menu = None

        # 커스텀 UI 설정 메서드 호출
        viewer.setup_custom_ui()

        # UI 상태 관리자 생성
        viewer.ui_state_manager = UIStateManager(viewer)
        viewer.ui_state_manager.ui_visibility_changed.connect(viewer.on_ui_visibility_changed)

        # UILockUI 초기화 (버튼들이 생성된 후)
        viewer.ui_lock_ui = UILockUI(viewer, viewer.ui_lock_manager)

        # 회전 관리자 생성 - 이미 위에서 초기화 됨
        # viewer.rotation_manager = RotationManager(viewer)
        viewer.rotation_manager.rotation_changed.connect(viewer.on_rotation_changed)
        # 회전 UI 관리자 생성 - 이미 위에서 초기화 됨
        # viewer.rotation_ui = RotationUI(viewer, viewer.rotation_manager)

        # 회전 관련 변수 추가
        viewer.current_rotation = 0
        viewer.rotated_frames = {}

        # 전체화면 오버레이 레이블 생성
        viewer.fullscreen_overlay = QLabel(viewer)
        viewer.fullscreen_overlay.setAlignment(Qt.AlignCenter)
        viewer.fullscreen_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.7); color: white; border-radius: 10px;")
        viewer.fullscreen_overlay.hide()

        # 리사이징 타이머 추가
        viewer.resize_timer = QTimer()
        viewer.resize_timer.setSingleShot(True)
        viewer.resize_timer.timeout.connect(viewer.delayed_resize)

        # UI 상태 변경을 위한 타이머 추가
        viewer.ui_update_timer = QTimer()
        viewer.ui_update_timer.setSingleShot(True)
        viewer.ui_update_timer.timeout.connect(viewer.delayed_resize)

        # UI 잠금 버튼 상태 업데이트 타이머
        viewer.create_single_shot_timer(0, viewer.update_ui_lock_button_state)

        # 미디어 핸들러 초기화
        viewer.image_handler = ImageHandler(viewer, viewer.image_label)
        viewer.psd_handler = PSDHandler(viewer, viewer.image_label)
        viewer.video_handler = VideoHandler(viewer, viewer.image_label)
        viewer.audio_handler = AudioHandler(viewer, viewer.image_label)

        # MediaDisplay 이벤트 연결
        viewer.image_label.mouseDoubleClicked.connect(viewer.mouseDoubleClickEvent)
        viewer.image_label.mouseWheelScrolled.connect(viewer.handle_wheel_event)

        # 전체 창에 휠 이벤트 필터 설치
        viewer.installEventFilter(viewer)