# 이미지 및 비디오 뷰어 애플리케이션 (PyQt5 기반)
import sys  # 시스템 관련 기능 제공 (프로그램 종료, 경로 관리 등)
import os  # 운영체제 관련 기능 제공 (파일 경로, 디렉토리 처리 등)
import platform
import shutil  # 파일 복사 및 이동 기능 제공 (고급 파일 작업)
import re  # 정규표현식 처리 기능 제공 (패턴 검색 및 문자열 처리)
import json  # JSON 파일 처리를 위한 모듈
from collections import OrderedDict  # LRU 캐시 구현을 위한 정렬된 딕셔너리
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout, QSizePolicy, QSlider, QLayout, QSpacerItem, QStyle, QStyleOptionSlider, QMenu, QAction, QScrollArea, QListWidgetItem, QListWidget, QAbstractItemView, QInputDialog, QMessageBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QLineEdit, QStackedWidget  # PyQt5 UI 위젯 (사용자 인터페이스 구성 요소)
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QFont, QMovie, QCursor, QIcon, QColor, QPalette, QFontMetrics, QTransform, QKeySequence, QWheelEvent  # 그래픽 요소 처리 (이미지, 폰트, 커서 등)
from PyQt5.QtCore import Qt, QSize, QTimer, QEvent, QPoint, pyqtSignal, QRect, QMetaObject, QObject, QUrl, QThread, QBuffer  # Qt 코어 기능 (이벤트, 신호, 타이머 등)
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
# 미디어 처리
from media.handlers.image_handler import ImageHandler  # 이미지 처리 클래스
from media.handlers.psd_handler import PSDHandler  # PSD 처리 클래스
from media.handlers.video_handler import VideoHandler  # 비디오 처리 클래스
from media.handlers.animation_handler import AnimationHandler  # 애니메이션 처리 클래스 추가
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
from events.handlers.keyboard_handler import KeyInputEdit
from events.handlers.mouse_handler import MouseHandler
# 북마크 관리
from features.bookmark import BookmarkManager  # 북마크 관리 클래스
# 회전 기능
from features.rotation.rotation_manager import RotationManager
from features.rotation.rotation_ui import RotationUI
# UI 잠금 기능
from features.ui_lock.ui_lock_manager import UILockManager
from features.ui_lock.ui_lock_ui import UILockUI

# 파일 브라우저 추가
from file import FileBrowser, FileNavigator
from file.operations import FileOperations

# MPV DLL 경로를 환경 변수 PATH에 추가 (mpv 모듈 import 전에 필수)
mpv_path = os.path.join(get_app_directory(), 'mpv')
print(f"MPV 경로: {mpv_path}")
dll_path = os.path.join(mpv_path, 'libmpv-2.dll')
print(f"DLL 파일 존재 여부: {os.path.exists(dll_path)}")
print(f"DLL 파일 크기: {os.path.getsize(dll_path) if os.path.exists(dll_path) else '파일 없음'}")

if not os.path.exists(mpv_path):
    os.makedirs(mpv_path, exist_ok=True)
    print(f"MPV 폴더가 생성되었습니다: {mpv_path}")

os.environ["PATH"] = mpv_path + os.pathsep + os.environ["PATH"]

# Windows에서는 os.add_dll_directory()가 PATH보다 더 확실한 방법입니다
if os.path.exists(mpv_path):
    os.add_dll_directory(mpv_path)

# MPV 모듈 import (경로 설정 후에 가능)
import mpv  # 비디오 재생 라이브러리 (고성능 미디어 플레이어)

# 메인 이미지 뷰어 클래스 정의
class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()  # 부모 클래스 생성자 호출
        # 앱 데이터 디렉토리 확인 및 생성
        app_data_dir = get_user_data_directory()
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)
        
        # 변수 초기화
        self.image_files = []  # 이미지 파일 목록
        self.current_index = 0  # 현재 표시 중인 이미지 인덱스 (0으로 초기화)
        self.current_image_path = ""  # 현재 이미지 경로
        self.base_folder = ""  # 기준 폴더 경로
        self.folder_buttons = []  # 폴더 버튼 목록
        
        # 키 설정 로드
        self.load_key_settings()
        
        # 북마크 관리자, 회전 관리자 및 UI 잠금 관리자 초기화
        self.bookmark_manager = BookmarkManager(self)
        self.rotation_manager = RotationManager()
        self.rotation_ui = RotationUI(self, self.rotation_manager)
        self.ui_lock_manager = UILockManager()
        self.ui_lock_ui = UILockUI(self, self.ui_lock_manager)
        
        # 마우스 이벤트 핸들러 초기화
        self.mouse_handler = MouseHandler(self)
        
        # 파일 브라우저 초기화
        self.file_browser = FileBrowser(self)
        
        # 파일 내비게이터 초기화
        self.file_navigator = FileNavigator(self)
        
        # 파일 작업 관리자 초기화
        self.file_operations = FileOperations(self)
        
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
        self.loading_label = QLabel("로딩 중...", self)  # 로딩 중 표시용 레이블
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
        mpv_path = os.path.join(get_app_directory(), 'mpv')

        if system == 'Windows':
            mpv_dll_path = os.path.join(mpv_path, "libmpv-2.dll")
            if not os.path.exists(mpv_dll_path):
                print(f"경고: {mpv_dll_path} 파일이 없습니다.")
            os.environ["MPV_DYLIB_PATH"] = mpv_dll_path
        elif system == 'Darwin':  # macOS
            mpv_dll_path = os.path.join(mpv_path, "libmpv.dylib")
            if not os.path.exists(mpv_dll_path):
                print(f"경고: {mpv_dll_path} 파일이 없습니다.")
            os.environ["MPV_DYLIB_PATH"] = mpv_dll_path
        else:  # Linux
            mpv_dll_path = os.path.join(mpv_path, "libmpv.so")
            if not os.path.exists(mpv_dll_path):
                print(f"경고: {mpv_dll_path} 파일이 없습니다.")
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

            print("MPV 플레이어 초기화 성공")
        except Exception as e:
            print(f"MPV 플레이어 초기화 실패: {e}")
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
                padding: 10px;  /* 내부 여백 */
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
                min-height: 50px;
                max-height: 50px;
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
        
        # 제목 표시줄 생성 (커스텀 - 기본 윈도우 타이틀바 대체)
        self.title_bar = QWidget(self)
        self.title_bar.setStyleSheet("background-color: rgba(52, 73, 94, 1.0);")  # 남색 배경
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)  # 좌우 여백만 설정
        
        # 제목 텍스트 레이블
        title_label = QLabel("Image Viewer")
        title_label.setStyleSheet("color: white; font-size: 16px;")  # 흰색 텍스트, 16px 크기
        title_layout.addWidget(title_label)
        title_layout.addStretch()  # 가운데 빈 공간 추가 (창 컨트롤 버튼을 오른쪽으로 밀기 위함)

        # 상단 UI 잠금 버튼 추가
        title_lock_btn = TitleLockButton(self)  # 타이틀 잠금 버튼 클래스 사용
        title_lock_btn.connect_action(self.toggle_title_ui_lock)  # toggle_title_ui_lock은 이제 controls_layout으로 호출을 위임합니다
        self.title_lock_btn = title_lock_btn  # 버튼 객체 저장
        
        # 창 컨트롤 버튼들 (최소화, 최대화, 닫기 - 윈도우 기본 버튼 대체)
        min_btn = MinimizeButton(self)  # 최소화 버튼
        min_btn.connect_action(self.showMinimized)  # 최소화 기능 연결
        
        max_btn = MaximizeButton(self)  # 최대화 버튼
        max_btn.connect_action(self.toggle_maximize_state)  # 최대화/복원 기능 연결
        self.max_btn = max_btn  # 버튼 객체 저장 (최대화 상태에 따라 아이콘 변경 위함)

        # 여기에 전체화면 버튼 추가
        fullscreen_btn = FullscreenButton(self)  # 전체화면 버튼
        fullscreen_btn.connect_action(self.toggle_fullscreen)  # 전체화면 토글 기능 연결
        self.fullscreen_btn = fullscreen_btn  # 버튼 객체 저장
        
        close_btn = CloseButton(self)  # 닫기 버튼
        close_btn.connect_action(self.close)  # 닫기 기능 연결
        
        # 창 컨트롤 버튼들 레이아웃에 추가
        title_layout.addWidget(title_lock_btn)
        title_layout.addWidget(min_btn)
        title_layout.addWidget(max_btn)
        title_layout.addWidget(fullscreen_btn)
        title_layout.addWidget(close_btn)

        # 제목 표시줄을 메인 레이아웃에 추가 (1% 비율 - 전체 UI 중 작은 부분)
        layout.addWidget(self.title_bar, 1)
        
        # 메인 레이아웃을 레이아웃에 추가 (90% 비율)
        layout.addWidget(self.main_layout, 90)
        
        # 북마크 메뉴 초기화
        self.bookmark_manager.update_bookmark_menu()
        
        # 이미지 표시 레이블 (QLabel → MediaDisplay로 변경)
        self.image_label = MediaDisplay()
        
        # 이미지 정보 표시 레이블 (파일 이름, 크기 등 표시)
        self.image_info_label = QLabel(self)
        self.image_info_label.setAlignment(Qt.AlignCenter)  # 중앙 정렬
        self.image_info_label.hide()  # 처음에는 숨김 (이미지 로드 후 표시)
        
        # 하단 컨트롤 레이아웃
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)  # 여백 없음
        bottom_layout.setSpacing(0)  # 레이아웃 사이 간격 제거

        # 슬라이더 위젯과 레이아웃
        self.slider_widget = QWidget()
        self.slider_widget.setStyleSheet("""
            background-color: rgba(52, 73, 94, 0.9);
            padding: 0px;
            margin: 0px;
            border: none;
        """)  # 패딩과 마진 완전히 제거
        self.slider_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 가로로 최대한 확장, 세로는 고정
        new_slider_layout = QHBoxLayout(self.slider_widget)
        new_slider_layout.setContentsMargins(0, 0, 0, 0)  # 여백을 완전히 제거
        new_slider_layout.setSpacing(0)  # 위젯 간 간격도 0으로 설정

        # 폴더 열기 버튼 (첫 번째 위치)
        self.open_button = OpenFolderButton(self)
        self.open_button.connect_action(self.open_folder)  # 폴더 열기 기능 연결 (이미지 폴더 선택)
        new_slider_layout.addWidget(self.open_button)

        # Set Base Folder 버튼 (두 번째 위치)
        self.set_base_folder_button = SetBaseFolderButton(self)
        self.set_base_folder_button.connect_action(self.set_base_folder)  # 기준 폴더 설정 기능 연결 (복사 대상 폴더)
        new_slider_layout.addWidget(self.set_base_folder_button)

        # 재생 버튼 (세 번째 위치)
        self.play_button = PlayButton(self)  # 재생 아이콘 버튼
        self.play_button.connect_action(self.toggle_animation_playback)  # 재생 버튼 클릭 이벤트 연결 (재생/일시정지 전환)
        new_slider_layout.addWidget(self.play_button)

        # 회전 버튼 추가 (반시계 방향)
        self.rotate_ccw_button = RotateButton(clockwise=False, parent=self)
        self.rotate_ccw_button.connect_action(self.rotate_image)
        new_slider_layout.addWidget(self.rotate_ccw_button)

        # 회전 버튼 추가 (시계 방향)
        self.rotate_cw_button = RotateButton(clockwise=True, parent=self)
        self.rotate_cw_button.connect_action(self.rotate_image)
        new_slider_layout.addWidget(self.rotate_cw_button)

        # 기존 슬라이더 (재생 바) 추가
        self.playback_slider = ClickableSlider(Qt.Horizontal, self)  # ClickableSlider로 변경 (클릭 시 해당 위치로 이동)
        self.playback_slider.setRange(0, 100)  # 슬라이더 범위 설정 (0-100%)
        self.playback_slider.setValue(0)  # 초기 값을 0으로 설정 (시작 위치)
        self.playback_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 가로 방향으로 확장 가능하도록 설정
        self.playback_slider.setFixedHeight(50)  # 슬라이더 높이를 50px로 고정
        
        self.playback_slider.clicked.connect(self.slider_clicked)  # 클릭 이벤트 연결 (클릭 위치로 미디어 이동)
        new_slider_layout.addWidget(self.playback_slider, 10)  # 재생 바 슬라이더를 레이아웃에 추가, stretch factor 10 적용

        # 재생 시간 레이블 추가 (현재 시간/총 시간 표시)
        self.time_label = QLabel("00:00 / 00:00", self)  # 초기 시간 표시
        self.time_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)  # 필요한 최소 크기만 사용
        self.time_label.setStyleSheet("""
            QLabel {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                padding: 8px;  /* 패딩을 10px에서 8px로 줄임 */
                border-radius: 3px;
                font-size: 14px;  /* 폰트 크기를 더 크게 설정 */
                qproperty-alignment: AlignCenter;  /* 텍스트 중앙 정렬 */
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
        new_slider_layout.addWidget(self.mute_button)

        # 볼륨 슬라이더 추가 (음량 조절)
        self.volume_slider = ClickableSlider(Qt.Horizontal, self)
        self.volume_slider.setRange(0, 100)  # 볼륨 범위 0-100%
        self.volume_slider.setValue(100)  # 기본 볼륨 100%으로 설정 (최대 음량)
        self.volume_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 고정 크기 사용
        self.volume_slider.setFixedHeight(50)  # 슬라이더 높이를 50px로 고정
        
        self.volume_slider.valueChanged.connect(self.adjust_volume)  # 슬라이더 값 변경 시 음량 조절 함수 연결
        self.volume_slider.clicked.connect(self.adjust_volume)  # 클릭 이벤트 연결 (클릭 위치로 음량 즉시 변경)
        new_slider_layout.addWidget(self.volume_slider)  # 음량 조절 슬라이더를 레이아웃에 추가
        
        # 메뉴 버튼 추가 
        self.menu_button = MenuButton(self)
        self.menu_button.connect_action(self.show_menu_above)  # 메뉴 표시 함수 연결
        new_slider_layout.addWidget(self.menu_button)
        
        # 북마크 버튼 추가 (가장 오른쪽에 위치)
        self.slider_bookmark_btn = BookmarkButton(self)
        self.slider_bookmark_btn.connect_action(self.show_bookmark_menu_above)  # 메뉴 표시 함수 연결로 변경
        new_slider_layout.addWidget(self.slider_bookmark_btn)
        
        # 북마크 매니저 설정
        self.bookmark_manager.set_bookmark_button(self.slider_bookmark_btn)

        # 여기에 UI 고정 버튼 추가 (완전히 새로운 코드로 교체)
        self.ui_lock_btn = UILockButton(self)  # UILockButton 클래스 사용
        self.ui_lock_btn.connect_action(self.toggle_ui_lock)  # toggle_ui_lock은 이제 controls_layout으로 호출을 위임합니다
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
        bottom_layout.addWidget(self.slider_widget, 0)  # 정렬 플래그 제거

        # 버튼 컨테이너 위젯 생성
        button_container = QWidget()
        button_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button_container_layout = QVBoxLayout(button_container)
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.setSpacing(0)

        # 폴더 버튼에 스타일 적용
        self.buttons = []
        for _ in range(5):  # 5줄
            row_widget = QWidget()  # 각 행을 위한 위젯
            row_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)  # Expanding 대신 MinimumExpanding 사용
            row_widget.setMaximumWidth(self.width())  # 최대 너비 제한 추가
            button_layout = QHBoxLayout(row_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setSpacing(0)
            button_row = []
            
            total_width = self.width()
            available_width = total_width - button_layout.contentsMargins().left() - button_layout.contentsMargins().right()
            button_width = available_width / 20  # 실제 사용 가능한 너비로 계산
            
            for i in range(20):
                empty_button = QPushButton('')
                empty_button.setStyleSheet(button_style)
                empty_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
                empty_button.clicked.connect(self.on_button_click)
                
                if i == 19:
                    remaining_width = total_width - (int(button_width) * 19)
                    empty_button.setFixedWidth(remaining_width)
                else:
                    empty_button.setFixedWidth(int(button_width))
                
                button_row.append(empty_button)
                button_layout.addWidget(empty_button)
            
            self.buttons.append(button_row)
            button_container_layout.addWidget(row_widget)

        # 버튼 컨테이너를 bottom_layout에 추가
        bottom_layout.addWidget(button_container)

        # 하단 버튼 영역을 메인 레이아웃에 추가 (9% 비율)
        layout.addLayout(bottom_layout, 9)

        # 메인 레이아웃에 이미지 컨테이너 추가
        self.main_layout.set_media_display(self.image_label)
        
        # 메인 레이아웃에 컨트롤 레이아웃 추가
        self.main_layout.set_controls_layout(self.slider_widget)
        
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

        self.cap = None  # 비디오 캡처 객체 초기화 (OpenCV 비디오 캡처)
        self.timer = QTimer(self)  # 타이머 객체 생성 (비디오 프레임 업데이트용)
        self.timer.timeout.connect(self.update_video_frame)  # 타이머가 작동할 때마다 update_video_frame 메소드 호출

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
        self.volume_slider.valueChanged.connect(self.adjust_volume)  # 슬라이더 값 변경 시 음량 조절 메서드 연결 (볼륨 실시간 조절)

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
        self.volume_slider.valueChanged.connect(self.adjust_volume)  # 슬라이더 값 변경 시 음량 조절 메서드 연결 (볼륨 실시간 조절)

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
            padding: 10px;
            font-size: 16px;
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
        
        # 추가 이벤트 핸들러 함수 추가
    def handle_wheel_event(self, delta):
        """
        MediaDisplay에서 전달된 휠 이벤트를 처리합니다.
        
        Args:
            delta (int): 휠 스크롤 값 (양수: 위로, 음수: 아래로)
        """
        # 현재 미디어 타입 확인
        current_media_type = getattr(self, 'current_media_type', 'unknown')
        
        # 애니메이션이나 비디오 재생 중인 경우 필요한 정리 작업 수행
        if current_media_type in ['gif_animation', 'webp_animation', 'video']:
            # 비디오 재생 중인 경우
            if current_media_type == 'video':
                # 비디오 중지
                self.stop_video()
            
            # 애니메이션 재생 중인 경우 (GIF/WEBP)
            elif current_media_type in ['gif_animation', 'webp_animation']:
                # 리소스 정리를 위해 먼저 cleanup_current_media 호출
                self.cleanup_current_media()
                # 스크롤 방향에 따라 이미지 변경 위치 선택
                if delta > 0:
                    # 휠을 위로 돌린 경우 - 이전 이미지
                    self.show_previous_image()
                else:
                    # 휠을 아래로 돌린 경우 - 다음 이미지
                    self.show_next_image()
                return
        
        # 일반 이미지인 경우 또는 다른 타입
        if delta > 0:
            # 휠을 위로 돌린 경우 - 이전 이미지
            self.show_previous_image()
        else:
            # 휠을 아래로 돌린 경우 - 다음 이미지
            self.show_next_image()

    def delete_current_image(self):
        """
        현재 이미지를 삭제합니다 (휴지통으로 이동).
        
        FileOperations 클래스를 사용하여 안전하게 파일을 휴지통으로 이동합니다.
        파일이 성공적으로 삭제되면 내비게이터에서 파일을 제거하고 다음 이미지로 이동합니다.
        """
        current_file = self.file_navigator.get_current_file()
        if not current_file:
            self.show_message("삭제할 이미지가 없습니다")
            return
        
        try:
            # 삭제 전에 미리 다음 파일 정보 가져오기 (필요한 경우)
            next_file = None
            if len(self.image_files) > 1:
                _, next_file = self.file_navigator.peek_next_file()
                
            # FileOperations를 통해 파일 삭제 시도
            # 확인 대화상자는 FileOperations에서 표시
            success, _ = self.file_operations.delete_file(current_file, confirm=True)
            
            if success:
                # 내비게이터에서 파일 제거
                success, next_file_after_deletion = self.file_navigator.delete_current_file()
                
                if success:
                    # 현재 인덱스와 파일 목록 업데이트
                    self.current_index = self.file_navigator.get_current_index()
                    self.image_files = self.file_navigator.get_files()
                    
                    # 이미지가 남아있는지 확인
                    if self.image_files:
                        # 새로운 다음 파일 있으면 표시
                        if next_file_after_deletion:
                            print(f"삭제 후 다음 이미지로 이동: {next_file_after_deletion}")
                            self.show_image(next_file_after_deletion)
                        else:
                            # 다음 파일이 없으면 현재 인덱스의 파일 표시
                            current_file = self.file_navigator.get_current_file()
                            if current_file:
                                print(f"현재 인덱스의 파일 표시: {current_file}")
                                self.show_image(current_file)
                            else:
                                # 파일이 없으면 메시지만 표시
                                self.image_label.clear()
                                self.current_image_path = ""
                    else:
                        # 더 이상 표시할 이미지가 없음
                        self.image_label.clear()
                        self.current_image_path = ""
                        self.show_message("모든 이미지가 삭제되었습니다")
                else:
                    self.show_message("파일 목록 업데이트 실패")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"이미지 삭제 중 오류 발생: {e}\n{error_details}")
            self.show_message(f"이미지 삭제 실패: {str(e)}")

    def ensure_maximized(self):
        """창이 최대화 상태인지 확인하고, 최대화 상태가 아니면 최대화합니다."""
        if not self.isMaximized():
            self.showMaximized()

    def resizeEvent(self, event):
        """창 크기가 변경될 때 호출되는 이벤트"""
        # 필수적인 UI 요소 즉시 조정
        window_width = self.width()
        
        # 슬라이더 위젯의 너비를 창 너비와 동일하게 설정
        if hasattr(self, 'slider_widget'):
            self.slider_widget.setFixedWidth(window_width)
        
        if hasattr(self, 'title_bar'):
            self.title_bar.setGeometry(0, 0, self.width(), 30)  # 제목표시줄 위치와 크기 조정
            self.title_bar.raise_()  # 제목표시줄을 항상 맨 위로 유지
            # 제목표시줄 버튼 업데이트
            for child in self.title_bar.children():
                if isinstance(child, QPushButton):
                    child.updateGeometry()
                    child.update()
        
        # 전체화면 오버레이 위치 조정
        if hasattr(self, 'fullscreen_overlay') and not self.fullscreen_overlay.isHidden():
            self.fullscreen_overlay.move(
                (self.width() - self.fullscreen_overlay.width()) // 2,
                (self.height() - self.fullscreen_overlay.height()) // 2
            )
        
        # 버튼 크기 계산 및 조정
        self.update_button_sizes()
        
        # 슬라이더 위젯 레이아웃 업데이트
        if hasattr(self, 'playback_slider'):
            self.playback_slider.updateGeometry()
        if hasattr(self, 'volume_slider'):
            self.volume_slider.updateGeometry()
        
        # 메시지 레이블 업데이트
        if hasattr(self, 'message_label') and self.message_label.isVisible():
            window_width = self.width()
            font_size = max(12, min(32, int(window_width * 0.02)))
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
            self.message_label.adjustSize()
            toolbar_height = 90  # 제목바(30) + 툴바(40) + 추가 여백(20)
            self.message_label.move(margin, toolbar_height + margin)

        # resizeEvent 함수 내에 다음 코드 추가 (message_label 업데이트 코드 아래에)
        # 이미지 정보 레이블 즉시 업데이트 
        if hasattr(self, 'image_info_label') and self.image_info_label.isVisible():
            window_width = self.width()
            font_size = max(12, min(32, int(window_width * 0.02)))
            padding = max(8, min(12, int(window_width * 0.008))) 
            margin = max(10, min(30, int(window_width * 0.02)))
            
            self.image_info_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background-color: rgba(52, 73, 94, 0.9);
                    font-size: {font_size}px;
                    padding: {padding}px {padding + 4}px;
                    border-radius: 3px;
                    font-weight: normal;
                }}
            """)
            self.image_info_label.adjustSize()
            
            # 우측 상단에 위치
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
        
        # 슬라이더 위젯 자체의 패딩 조정
        if hasattr(self, 'slider_widget'):
            padding = max(5, min(15, int(window_width * 0.01)))
            self.slider_widget.setStyleSheet(f"background-color: rgba(52, 73, 94, 0.9); padding: {padding}px;")
        
        # 전체 레이아웃 강제 업데이트
        self.updateGeometry()
        if self.layout():
            self.layout().update()
        
        # 나머지 무거운 작업은 타이머를 통해 지연 처리
        if self.resize_timer.isActive():
            self.resize_timer.stop()
        self.resize_timer.start(150)  # 리사이징이 끝나고 150ms 후에 업데이트
        
        # 부모 클래스의 resizeEvent 호출
        super().resizeEvent(event)

        # 잠금 버튼과 북마크 버튼 상태 업데이트
        self.update_ui_lock_button_state()
        self.update_title_lock_button_state()
        self.controls_layout.update_bookmark_button_state()

    def delayed_resize(self):
        """리사이징 완료 후 지연된 UI 업데이트 처리"""
        try:
            print("delayed_resize 실행")  # 디버깅용 메시지 추가
            
            # 현재 표시 중인 미디어 크기 조절
            if hasattr(self, 'current_image_path') and self.current_image_path:
                file_ext = os.path.splitext(self.current_image_path)[1].lower()
                
                # 이미지 타입에 따른 리사이징 처리
                if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif']:
                    # ImageHandler를 사용하여 이미지 크기 조정
                    self.image_handler.resize()
                elif file_ext == '.psd':
                    # PSDHandler를 사용하여 PSD 파일 크기 조정
                    self.psd_handler.resize()
                elif (file_ext == '.gif' or file_ext == '.webp') and self.current_media_type in ['gif_animation', 'webp_animation']:
                    # 애니메이션 핸들러를 통해 애니메이션 크기 조정
                    if hasattr(self, 'animation_handler'):
                        print(f"{file_ext.upper()} 애니메이션 핸들러를 통한 리사이징")
                        self.animation_handler.scale_animation()
                    else:
                        # 기존 방식으로 처리 (호환성 유지)
                        if file_ext == '.gif':
                            print("GIF 애니메이션 직접 리사이징")
                            self.scale_gif()
                        elif file_ext == '.webp':
                            print("WEBP 애니메이션 직접 리사이징")
                            self.scale_webp()
                        # UI 처리 완료 후 애니메이션이 제대로 보이도록 강제 프레임 업데이트
                        QApplication.processEvents()
                elif file_ext == '.webp' and self.current_media_type == 'webp_image':
                    # 정적 WEBP 이미지 처리
                    if hasattr(self, 'animation_handler'):
                        print("정적 WEBP 이미지 핸들러를 통한 리사이징")
                        self.animation_handler.rotate_static_image(self.current_image_path)
                    else:
                        # 일반 WEBP 이미지 처리 (애니메이션이 아닌 경우)
                        pixmap = QPixmap(self.current_image_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            self.image_label.setPixmap(scaled_pixmap)
                elif file_ext in ['.mp4', '.avi', '.wmv', '.ts', '.m2ts', '.mov', '.qt', '.mkv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', '.vob', '.wav', '.flac', '.mp3', '.aac', '.m4a', '.ogg']:
                    # MPV 플레이어 윈도우 ID 업데이트
                    if hasattr(self, 'player'):
                        self.player.wid = int(self.image_label.winId())
            
            # 이미지 정보 레이블 업데이트
            if hasattr(self, 'image_info_label') and self.image_files:
                self.update_image_info()

            # 잠금 버튼과 북마크 버튼 상태 업데이트 (리사이징 후 스타일 복원)
            self.update_ui_lock_button_state()
            self.update_title_lock_button_state()
            self.controls_layout.update_bookmark_button_state()
                    
        except Exception as e:
            print(f"지연된 리사이징 처리 중 오류 발생: {e}")

    def mouseDoubleClickEvent(self, event=None):
        """더블 클릭 시 전체화면 또는 최대화 상태 전환"""
        if event:
            self.mouse_handler.handle_double_click(event)
        else:
            # 이벤트 객체가 없는 경우 (MediaDisplay에서 호출된 경우) 처리
            print("더블 클릭 이벤트가 이벤트 객체 없이 호출되었습니다.")
            self.mouse_handler.handle_double_click(None)

    def set_base_folder(self):
        """기준 폴더 설정 (하위 폴더 버튼 자동 생성용)"""
        folder_path = QFileDialog.getExistingDirectory(self, "Set Base Folder")  # 폴더 선택 대화상자
        if folder_path:  # 폴더가 선택된 경우
            self.base_folder = folder_path  # 기준 폴더 경로 저장
            print(f"Base folder set to: {self.base_folder}")  # 콘솔에 설정된 경로 출력

            # 모든 버튼 초기화 (텍스트 및 툴팁 제거)
            for row in self.buttons:
                for button in row:
                    button.setText('')
                    button.setToolTip('')

            # core.utils 모듈의 natural_keys 함수를 사용합니다

            # 하위 폴더 목록 가져오기
            subfolders = [f.path for f in os.scandir(self.base_folder) if f.is_dir()]  # 디렉토리만 선택
            subfolders.sort(key=lambda x: natural_keys(os.path.basename(x).lower()))  # 자연스러운 순서로 정렬

            # 버튼 너비 계산
            button_width = self.width() // 20  # 창 너비의 1/20로 설정

            # 폴더 버튼 업데이트
            for i, row in enumerate(self.buttons):
                for j, button in enumerate(row):
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
                        if text_width > available_width:
                            # 적절한 길이를 찾을 때까지 텍스트 줄임
                            for k in range(len(folder_name), 0, -1):
                                truncated = folder_name[:k] + ".."  # 텍스트 뒷부분 생략 표시
                                if font_metrics.horizontalAdvance(truncated) <= available_width:
                                    button.setText(truncated)  # 축약된 텍스트 설정
                                    button.setToolTip(subfolders[index])  # 툴팁으로 전체 경로 표시
                                    break
                        else:
                            button.setText(folder_name)  # 원본 폴더명으로 복원
                            button.setToolTip(subfolders[index])  # 툴팁으로 전체 경로 표시

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
            self.image_files, self.current_index = self.file_browser.process_folder(folder_path)
            
            # 파일 내비게이터에도 파일 목록 설정
            self.file_navigator.set_files(self.image_files, self.current_index)
            
            if self.image_files:
                self.show_image(self.image_files[0])  # 첫 번째 이미지 표시
                self.update_image_info()  # 이미지 정보 업데이트 (인덱스 표시 업데이트)

    def get_image_files(self, folder_path):
        """지원하는 모든 미디어 파일 목록 가져오기"""
        return self.file_browser.get_media_files(folder_path)

    def stop_video(self):
        """비디오 재생 중지 및 관련 리소스 정리"""
        self.video_handler.unload()
        # 슬라이더 값 초기화
        if hasattr(self, 'playback_slider'):
            self.playback_slider.setValue(0)
        # 시간 표시 초기화
        if hasattr(self, 'time_label'):
            self.time_label.setText("00:00 / 00:00")

    def disconnect_all_slider_signals(self):
        """슬라이더의 모든 신호 연결 해제 (이벤트 충돌 방지)"""
        
        try:
            # valueChanged 시그널 연결 해제
            self.playback_slider.valueChanged.disconnect()
        except (TypeError, RuntimeError):
            pass  # 연결된 슬롯이 없으면 무시
            
        try:
            # sliderPressed 시그널 연결 해제
            self.playback_slider.sliderPressed.disconnect()
        except (TypeError, RuntimeError):
            pass  # 연결된 슬롯이 없으면 무시
            
        try:
            # sliderReleased 시그널 연결 해제
            self.playback_slider.sliderReleased.disconnect()
        except (TypeError, RuntimeError):
            pass  # 연결된 슬롯이 없으면 무시
            
        try:
            # clicked 시그널 연결 해제
            self.playback_slider.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass  # 연결된 슬롯이 없으면 무시

    def cancel_pending_loaders(self, current_path=None):
        """현재 로딩 중인 이미지를 제외한 모든 로더 스레드를 취소합니다."""
        # 기존 진행 중인 로딩 스레드 취소 (현재 로딩 중인 이미지는 제외)
        for path, loader in list(self.loader_threads.items()):
            if (current_path is None or path != current_path) and loader.isRunning():
                try:
                    loader.terminate()
                    loader.wait(100)  # 최대 100ms 대기
                except:
                    pass
                del self.loader_threads[path]
                print(f"이미지 로딩 취소: {os.path.basename(path)}")

    def update_ui_for_media(self, image_path):
        """미디어 표시에 필요한 UI 요소들을 업데이트합니다."""
        # 파일 이름을 제목표시줄에 표시
        file_name = os.path.basename(image_path) if image_path else "Image Viewer"
        title_text = f"Image Viewer - {file_name}" if image_path else "Image Viewer"
        # 제목표시줄 라벨 찾아서 텍스트 업데이트
        for child in self.title_bar.children():
            if isinstance(child, QLabel):
                child.setText(title_text)
                break
        
        # 책갈피 버튼 상태 업데이트
        self.controls_layout.update_bookmark_button_state()
        
        # 북마크 메뉴 업데이트 추가 - 이미지 변경 시 메뉴 상태도 함께 업데이트
        self.controls_layout.update_bookmark_menu()
        
        # 비디오 미디어의 경우 음소거 버튼 상태 재설정
        if self.current_media_type == 'video' and hasattr(self, 'mute_button'):
            try:
                is_muted = self.video_handler.is_muted()
                if is_muted is not None:  # None이 아닌 경우에만 상태 업데이트
                    self.mute_button.set_mute_state(is_muted)
            except Exception as e:
                print(f"음소거 버튼 상태 업데이트 오류: {e}")
        
        # 제목표시줄과 이미지 정보 레이블을 앞으로 가져옴
        if hasattr(self, 'title_bar'):
            self.title_bar.raise_()
        if hasattr(self, 'image_info_label'):
            self.image_info_label.raise_()

    def show_image(self, image_path):
        """이미지/미디어 파일 표시 및 관련 UI 업데이트"""
        print(f"\n========= 이미지 로드 시작: {os.path.basename(image_path)} =========")
        
        # 기존 미디어 리소스 정리
        self.cleanup_current_media()

        # 이미지 크기 확인
        image_size_mb = 0
        try:
            if os.path.exists(image_path):
                image_size_mb = os.path.getsize(image_path) / (1024 * 1024)  # 메가바이트 단위로 변환
        except Exception as e:
            print(f"이미지 크기 확인 오류: {e}")

        # 전체화면 모드에서 고품질 이미지 로딩 (비동기로 처리)
        if self.isFullScreen() and image_size_mb > 5:  # 큰 이미지인 경우
            # 최대한 고품질로 표시 (필요한 작업 추가)
            QApplication.processEvents()  # UI 응답성 유지

        # 현재 이미지 경로 저장
        self.current_image_path = image_path
        
        # 기존 진행 중인 로딩 스레드 취소
        self.cancel_pending_loaders(image_path)

        # UI 요소 업데이트
        self.update_ui_for_media(image_path)
        
        # 파일 확장자 확인 (소문자로 변환)
        file_ext = os.path.splitext(image_path)[1].lower()
        
        # FormatDetector를 사용하여 파일 형식 감지
        file_format = FormatDetector.detect_format(image_path)
        print(f"FormatDetector 감지 결과: {file_format}")

        # 파일 형식 감지 결과에 따라 적절한 핸들러 호출
        if file_format == 'gif_image' or file_format == 'gif_animation':
            # AnimationHandler로 GIF 처리
            if hasattr(self, 'animation_handler'):
                detected_type = self.animation_handler.load_gif(image_path)
                self.current_media_type = detected_type
            else:
                # AnimationHandler가 없는 경우 기존 방식으로 처리
                self.show_gif(image_path) 
        elif file_format == 'webp_image' or file_format == 'webp_animation':
            # AnimationHandler로 WEBP 처리
            if hasattr(self, 'animation_handler'):
                detected_type = self.animation_handler.load_webp(image_path)
                self.current_media_type = detected_type
                print(f"WEBP 미디어 타입 감지: {detected_type}")
            else:
                # AnimationHandler가 없는 경우 기존 방식으로 처리
                self.show_webp(image_path)
        elif file_format == 'psd':
            # PSD 파일 처리
            self.current_media_type = 'image'  # 미디어 타입 업데이트
            
            # PSDHandler를 사용하여 PSD 파일 로드
            self.psd_handler.load(image_path)
            
            # 이미지 정보 업데이트
            self.update_image_info()
        elif file_format == 'video':
            # 비디오 파일 처리
            self.current_media_type = 'video'  # 미디어 타입 업데이트
            self.play_video(image_path)  # 비디오 재생
        elif file_format == 'image' or file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif']:
            # 일반 이미지 파일 처리
            self.current_media_type = 'image'  # 미디어 타입 업데이트
            
            # ImageHandler를 사용하여 이미지 로드
            self.image_handler.load(image_path)
            
            # 이미지 정보 업데이트
            self.update_image_info()
        else:
            self.current_media_type = 'unknown'  # 미디어 타입 업데이트
        
        # 추가: 전체화면 모드에서 지연된 리사이징 적용
        if self.isFullScreen():
            QTimer.singleShot(300, self.delayed_resize)
            print("전체화면 모드에서 이미지 로드 후 지연된 리사이징 예약")

    def show_gif(self, image_path):
        """GIF 애니메이션을 표시합니다."""
        if not hasattr(self, 'animation_handler'):
            self.animation_handler = AnimationHandler(self.image_label, self)
        
        # AnimationHandler를 통해 GIF 로드
        self.animation_handler.load_gif(image_path)
        
        # 미디어 타입 설정
        self.current_media_type = 'gif_animation'
        self.current_image_path = image_path

    def show_webp(self, image_path):
        """WEBP 애니메이션을 표시합니다."""
        if not hasattr(self, 'animation_handler'):
            self.animation_handler = AnimationHandler(self.image_label, self)
        
        # AnimationHandler를 통해 WEBP 로드
        self.animation_handler.load_webp(image_path)
        
        # 미디어 타입 설정
        self.current_media_type = 'webp_animation'
        self.current_image_path = image_path

    def scale_webp(self):
        """WEBP 애니메이션 크기 조정"""
        if self.current_media_type == 'webp_animation' and hasattr(self, 'animation_handler'):
            success = self.animation_handler.scale_animation()
            if success:
                print("WEBP 애니메이션 크기 조정 완료")
            else:
                print("WEBP 애니메이션 크기 조정 실패")

    def scale_gif(self):
        """GIF 애니메이션 크기 조정"""
        if self.current_media_type == 'gif_animation' and hasattr(self, 'animation_handler'):
            success = self.animation_handler.scale_animation()
            if success:
                print("GIF 애니메이션 크기 조정 완료")
            else:
                print("GIF 애니메이션 크기 조정 실패")

    def play_video(self, video_path):
        """MPV를 사용하여 비디오 재생"""
        # 비디오 핸들러를 사용하여 비디오 로드
        result = self.video_handler.load(video_path)
        if result:
            # 비디오 정보 업데이트
            self.current_image_path = video_path
            self.current_media_type = 'video'
            
            # 슬라이더 초기화 및 설정
            self.playback_slider.setRange(0, 0)  # 슬라이더 범위를 0으로 설정
            self.playback_slider.setValue(0)  # 슬라이더 초기값을 0으로 설정
            
            # 슬라이더 시그널 연결 전에 기존 연결 해제
            self.disconnect_all_slider_signals()
            
            # 슬라이더 이벤트 연결
            self.playback_slider.sliderPressed.connect(self.slider_pressed)
            self.playback_slider.sliderReleased.connect(self.slider_released)
            self.playback_slider.valueChanged.connect(self.seek_video)
            self.playback_slider.clicked.connect(self.slider_clicked)
            
            # 재생 버튼 상태 업데이트
            self.play_button.set_play_state(True)  # 일시정지 아이콘으로 설정
            
            # 비디오 재생 시작
            self.video_handler.play()
            
        return result

    def on_video_end(self, name, value):
        """비디오가 종료될 때 호출되는 메서드입니다."""
        # 메인 스레드에서 안전하게 타이머를 중지하기 위해 QTimer.singleShot 사용
        QTimer.singleShot(0, self.stop_video_timer)

    def stop_video_timer(self):
        """타이머를 중지하는 메서드입니다."""
        if hasattr(self, 'video_timer') and self.video_timer.isActive():
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
        """재생 상태에 따라 버튼 텍스트 업데이트"""
        # 이 메서드는 controls_layout으로 이동했으므로 여기서는 controls_layout의 메서드를 호출
        self.controls_layout.update_play_button()

    def update_video_frame(self):
        # 비디오에서 프레임을 읽어옵니다.
        ret, frame = self.cap.read()  # 프레임을 하나 읽어와 ret과 frame에 저장

        if ret:  # 비디오에서 정상적으로 프레임을 읽었으면
            # OpenCV에서 읽은 BGR 형식을 RGB 형식으로 변환합니다.
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # OpenCV는 BGR 형식이므로 RGB로 변환

            # numpy 배열을 QImage로 변환하여 PyQt에서 사용할 수 있도록 만듭니다.
            height, width, channel = frame.shape  # 이미지의 높이, 너비, 채널 수를 가져옵니다.
            bytes_per_line = 3 * width  # 한 줄에 필요한 바이트 수 (RGB는 3바이트)
            qimg = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)  # numpy 데이터를 QImage로 변환

            # QImage를 QPixmap으로 변환
            pixmap = QPixmap.fromImage(qimg)  # QImage를 QPixmap으로 변환
            
            # 회전 각도가 0이 아니면 회전 적용
            if hasattr(self, 'current_rotation') and self.current_rotation != 0:
                transform = QTransform().rotate(self.current_rotation)
                pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
            
            # 라벨에 표시
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))  
            # 라벨에 표시된 크기를 라벨 크기에 맞춰 비율을 유지하면서 스무스하게 변환하여 표시
        else:
            # 비디오의 끝에 도달하면 첫 번째 프레임으로 돌아갑니다.
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 비디오의 첫 번째 프레임으로 돌아가기

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
            # 기본 이미지 인덱스 정보
            image_info = f"{self.current_index + 1} / {len(self.image_files)}"
            
            # 파일 크기 정보는 표시하지 않음
            
            self.image_info_label.setText(image_info)
            
            self.image_info_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background-color: rgba(52, 73, 94, 0.9);
                    font-size: {font_size}px;
                    padding: {padding}px {padding + 4}px;
                    border-radius: 3px;
                    font-weight: normal;
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
        print("\n=== 다음 이미지 로드 시작 ===")
        print(f"현재 인덱스(이동 전): {self.current_index}")
        print(f"현재 이미지: {self.current_image_path}")
        print(f"파일 내비게이터 파일 수: {len(self.file_navigator.get_files())}")
        print(f"메인 이미지 목록 수: {len(self.image_files)}")
        
        if self.file_navigator.get_files() != self.image_files:
            print("경고: 파일 내비게이터와 메인 이미지 목록이 불일치합니다.")
            # 필요한 경우 동기화
            self.image_files = self.file_navigator.get_files()
            print(f"이미지 목록 동기화됨: {len(self.image_files)} 파일")
        
        success, next_image = self.file_navigator.next_file()
        
        print(f"다음 이미지 로드 성공 여부: {success}")
        print(f"다음 이미지 경로: {next_image}")
        
        if success and next_image:
            self.current_index = self.file_navigator.get_current_index()  # 인덱스 동기화
            print(f"새 인덱스: {self.current_index}")
            self.show_image(next_image)
        else:
            print("다음 이미지 로드 실패")
        
        print("=== 다음 이미지 로드 종료 ===\n")

    # 이전 이미지를 보여주는 메서드입니다.
    def show_previous_image(self):
        success, prev_image = self.file_navigator.previous_file()
        if success and prev_image:
            self.current_index = self.file_navigator.get_current_index()  # 인덱스 동기화
            self.show_image(prev_image)

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
        # ESC 키로 전체화면 모드 종료
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
            return  # ESC 키 처리 완료
        
        # Ctrl+D: 디버깅 모드 토글
        if event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
            self.toggle_debug_mode()
            return
            
        # Ctrl+G: QMovie 참조 그래프 생성
        if event.key() == Qt.Key_G and event.modifiers() == Qt.ControlModifier:
            self.generate_qmovie_reference_graph()
            return
            
        # 현재 미디어 타입 확인
        current_media_type = getattr(self, 'current_media_type', 'unknown')
            
        # 이전/다음 이미지 키 처리 시 애니메이션/비디오 정리
        if (event.key() == self.key_settings["prev_image"] or 
            event.key() == self.key_settings["next_image"]):
            
            # 애니메이션이나 비디오 재생 중인 경우 필요한 정리 작업 수행
            if current_media_type in ['gif_animation', 'webp_animation', 'video']:
                # 비디오 재생 중인 경우
                if current_media_type == 'video':
                    # 비디오 중지
                    self.stop_video()
                
                # 애니메이션 재생 중인 경우 (GIF/WEBP)
                elif current_media_type in ['gif_animation', 'webp_animation']:
                    # 리소스 정리를 위해 먼저 cleanup_current_media 호출
                    self.cleanup_current_media()
        
        # 이제 해당 키 이벤트 처리
        if event.key() == self.key_settings["prev_image"]:  # 이전 이미지 키
            self.show_previous_image()  # 이전 이미지로 이동
        elif event.key() == self.key_settings["next_image"]:  # 다음 이미지 키
            self.show_next_image()  # 다음 이미지로 이동
        elif event.key() == self.key_settings["rotate_clockwise"]:  # 시계 방향 회전 키
            self.rotate_image(True)  # 시계 방향 회전
        elif event.key() == self.key_settings["rotate_counterclockwise"]:  # 반시계 방향 회전 키
            self.rotate_image(False)  # 반시계 방향 회전
        elif event.key() == self.key_settings["play_pause"]:  # 재생/일시정지 키
            self.toggle_animation_playback()  # 재생/일시정지 토글
        elif event.key() == self.key_settings["volume_up"]:  # 볼륨 증가 키
            # 볼륨 슬라이더 값을 가져와서 5씩 증가 (0-100 범위)
            current_volume = self.volume_slider.value()
            new_volume = min(current_volume + 5, 100)  # 최대 100을 넘지 않도록
            self.volume_slider.setValue(new_volume)
            self.adjust_volume(new_volume)
        elif event.key() == self.key_settings["volume_down"]:  # 볼륨 감소 키
            # 볼륨 슬라이더 값을 가져와서 5씩 감소 (0-100 범위)
            current_volume = self.volume_slider.value()
            new_volume = max(current_volume - 5, 0)  # 최소 0 미만으로 내려가지 않도록
            self.volume_slider.setValue(new_volume)
            self.adjust_volume(new_volume)
        elif event.key() == self.key_settings["toggle_mute"]:  # 음소거 토글 키
            self.toggle_mute()  # 음소거 토글 함수 호출
        elif event.key() == self.key_settings["delete_image"]:  # 이미지 삭제 키
            self.delete_current_image()  # 현재 이미지 삭제 함수 호출
        # 전체화면 토글
        elif event.key() == self.key_settings.get("toggle_fullscreen", Qt.ControlModifier | Qt.Key_Return) or \
          (event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Return):  # Ctrl+Enter도 추가
            self.toggle_fullscreen()
            return
            
        # 최대화 상태 토글 (Enter 키) - 전체화면 모드가 아닐 때만 적용
        elif event.key() == self.key_settings.get("toggle_maximize_state", Qt.Key_Return) and \
          event.modifiers() != Qt.ControlModifier and not self.isFullScreen():  # 전체화면이 아닐 때만 처리
            self.toggle_maximize_state()
            return

    def wheelEvent(self, event):
        """휠 이벤트 처리"""
        self.mouse_handler.wheel_event(event)

    def eventFilter(self, obj, event):
        """모든 마우스 이벤트를 필터링"""
        # MouseHandler로 이벤트 필터링 위임
        return self.mouse_handler.event_filter(obj, event)

    def toggle_fullscreen(self):
        """전체화면 모드를 전환합니다."""
        if self.isFullScreen():
            # 전체화면 모드에서 일반 모드로 전환
            self.showNormal()
            
            # UI 고정 상태에 따라 UI 요소 표시 여부 결정 - 각각 독립적으로 확인
            if hasattr(self, 'is_title_ui_locked') and self.is_title_ui_locked:
                # 상단 UI가 고정된 상태라면 타이틀바 표시
                if hasattr(self, 'title_bar'):
                    self.title_bar.show()
            else:
                # 상단 UI가 고정되지 않은 상태라면 타이틀바 숨김
                if hasattr(self, 'title_bar'):
                    self.title_bar.hide()
            
            if hasattr(self, 'is_bottom_ui_locked') and self.is_bottom_ui_locked:
                # 하단 UI가 고정된 상태라면 UI 요소들을 표시
                if hasattr(self, 'slider_widget'):
                    self.slider_widget.show()
                
                for row in self.buttons:
                    for button in row:
                        button.show()
            else:
                # 하단 UI가 고정되지 않은 상태라면 UI 요소들을 숨김
                if hasattr(self, 'slider_widget'):
                    self.slider_widget.hide()
                
                for row in self.buttons:
                    for button in row:
                        button.hide()
            
            # 전체화면 오버레이 숨기기
            if hasattr(self, 'fullscreen_overlay') and self.fullscreen_overlay.isVisible():
                self.fullscreen_overlay.hide()
                
            # 풀스크린 버튼 텍스트 업데이트
            if hasattr(self, 'fullscreen_btn'):
                self.fullscreen_btn.setText("🗖")  # 전체화면 아이콘
            
            # 전체화면 모드 상태 업데이트
            self.is_in_fullscreen = False
            
            # 전체화면에서 일반 모드로 전환 후 모든 미디어 타입에 대해 리사이징 적용
            QTimer.singleShot(100, self.delayed_resize)

            # 잠금 버튼 상태 갱신 - 각각 개별적으로 갱신
            QTimer.singleShot(150, self.update_title_lock_button_state)
            QTimer.singleShot(150, self.update_ui_lock_button_state)
                
        else:
            # 현재 비디오 상태 저장 (있는 경우)
            was_playing = False
            position = 0
            if self.current_media_type == 'video' and hasattr(self, 'player') and self.player:
                try:
                    was_playing = not self.player.pause
                    position = self.player.playback_time or 0
                except:
                    pass
            
            # 일반 모드에서 전체화면 모드로 전환
            self.showFullScreen()

            # 상단 UI 및 하단 UI 잠금 상태에 따라 개별적으로 처리
            if not hasattr(self, 'is_title_ui_locked') or not self.is_title_ui_locked:
                if hasattr(self, 'title_bar'):
                    self.title_bar.hide()
            
            if not hasattr(self, 'is_bottom_ui_locked') or not self.is_bottom_ui_locked:
                if hasattr(self, 'slider_widget'):
                    self.slider_widget.hide()
                
                for row in self.buttons:
                    for button in row:
                        button.hide()
            
            # 풀스크린 버튼 텍스트 업데이트
            if hasattr(self, 'fullscreen_btn'):
                self.fullscreen_btn.setText("🗗")  # 창 모드 아이콘
            
            # 전체화면 모드 상태 업데이트
            self.is_in_fullscreen = True
            
            # 전체화면 모드로 전환 후 모든 미디어 타입에 대해 리사이징 적용
            QTimer.singleShot(100, self.delayed_resize)

            # 잠금 버튼 상태 갱신 - 각각 개별적으로 갱신
            QTimer.singleShot(150, self.update_title_lock_button_state)
            QTimer.singleShot(150, self.update_ui_lock_button_state)
                
            # 비디오 복구 (필요한 경우)
            if self.current_media_type == 'video' and position > 0:
                QTimer.singleShot(500, lambda: self.restore_video_state(was_playing, position))

    def restore_video_state(self, was_playing, position):
        """비디오 재생 상태를 복구합니다"""
        if self.current_media_type == 'video':
            try:
                # 위치 복구
                self.video_handler.seek(position)
                
                # 재생 상태 복구
                if was_playing:
                    self.video_handler.play()
                    self.update_play_button()
                
                # 슬라이더 위치 업데이트 강제
                QTimer.singleShot(50, self.update_video_playback)
            except Exception as e:
                print(f"비디오 상태 복구 실패: {e}")

    # toggle_maximize 메소드 추가 (이름을 toggle_maximize_state로 변경)
    def toggle_maximize_state(self):
        """최대화 상태와 일반 상태를 토글합니다."""
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText("□")  # 일반 상태일 때는 □ 표시
            print("창 상태: 일반")  # 디버깅용 로그
        else:
            self.showMaximized()
            self.max_btn.setText("❐")  # 최대화 상태일 때는 ❐ 표시
            print("창 상태: 최대화")  # 디버깅용 로그
        
        # 창 포커스 설정 (이벤트 처리 개선)
        QTimer.singleShot(50, self.setFocus)

    def closeEvent(self, event):
        """
        애플리케이션 종료 시 필요한 정리 작업을 수행합니다.
        """
        print("프로그램 종료 처리 시작...")
        
        # 디버깅을 위한 초기 상태 확인
        if hasattr(self, 'debug_mode') and self.debug_mode:
            self.debug_qmovie_before_cleanup()
        
        # 현재 미디어 리소스 정리
        self.cleanup_current_media()
        
        # PSD 핸들러 언로드
        if hasattr(self, 'psd_handler') and self.psd_handler:
            self.psd_handler.unload()
            
        # 이미지 캐시 정리
        if hasattr(self, 'image_cache') and self.image_cache:
            print("이미지 캐시 정리 시작...")
            self.image_cache.clear()
            print("이미지 캐시 정리 완료")
            
        # PSD 캐시 정리
        if hasattr(self, 'psd_cache') and self.psd_cache:
            print("PSD 캐시 정리 시작...")
            self.psd_cache.clear()
            print("PSD 캐시 정리 완료")
            
        # GIF 캐시 정리
        if hasattr(self, 'gif_cache') and self.gif_cache:
            print("GIF 캐시 정리 시작...")
            # 단순화된 QMovie 정리 과정
            try:
                from PyQt5.QtGui import QMovie
                from PyQt5.QtWidgets import QApplication
                
                # 캐시에서 QMovie 객체 간단히 확인 및 정리
                for key, item in list(self.gif_cache.cache.items()):
                    if isinstance(item, QMovie):
                        # 기본적인 정리 단계만 수행
                        item.stop()
                        item.deleteLater()
                
                # 한 번의 이벤트 처리만 수행
                QApplication.processEvents()
                
                # 캐시 비우기
                self.gif_cache.clear()
                self.gif_cache = None  # 참조 해제
            except Exception as e:
                print(f"GIF 캐시 정리 중 오류: {e}")
            print("GIF 캐시 정리 완료")
            
        # 활성 타이머 정리
        for timer in list(self.timers):
            try:
                if timer.isActive():
                    timer.stop()
                timer.deleteLater()
            except Exception as e:
                print(f"타이머 정리 오류: {e}")
        self.timers.clear()  # 타이머 목록 비우기
        
        # 싱글샷 타이머 정리 추가
        for timer in list(self.singleshot_timers):
            try:
                if timer.isActive():
                    timer.stop()
                timer.deleteLater()
            except Exception as e:
                print(f"싱글샷 타이머 정리 오류: {e}")
        self.singleshot_timers.clear()
                
        # 책갈피 저장
        self.save_bookmarks()
        
        # 디버깅을 위한 정리 후 상태 확인
        if hasattr(self, 'debug_mode') and self.debug_mode:
            self.debug_qmovie_after_cleanup()
            
        # 마지막 정리 작업 후 이벤트 처리를 강제로 수행하여 모든 정리 작업이 완료되도록 함
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # 이벤트 처리 계속 (창 닫기)
        event.accept()

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
            key_settings_action = QAction("환경 설정", self)
            key_settings_action.triggered.connect(self.show_preferences_dialog)
            self.dropdown_menu.addAction(key_settings_action)
            
            # 구분선 추가
            self.dropdown_menu.addSeparator()
            
            # 정보 메뉴 항목
            about_action = QAction("프로그램 정보", self)
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
        # 이전 코드는 유지하지 않음 - controls_layout에서 모든 기능 처리

    def show_loading_indicator(self):
        """로딩 인디케이터를 화면 중앙에 표시합니다."""
        # 이미 로딩 중이면 무시
        if self.is_loading:
            return
            
        # 로딩 상태 설정
        self.is_loading = True
        
        # 로딩 레이블 스타일 설정 (테두리 없는 파란색 배경)
        self.loading_label.setText("로딩 중...")
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
        """로딩 인디케이터를 숨깁니다."""
        # 로딩 중이 아니면 무시
        if not self.is_loading:
            return
            
        # 로딩 상태 해제
        self.is_loading = False
        
        # 타이머 정리
        if self.loading_timer is not None and self.loading_timer.isActive():
            self.loading_timer.stop()
            if self.loading_timer in self.timers:
                self.timers.remove(self.loading_timer)
            self.loading_timer = None
        
        # 로딩 레이블 숨기기 (단순하게 숨기기만 함)
        self.loading_label.hide()
        
        # 강제 업데이트를 통해 화면 갱신
        self.image_label.update()
        QApplication.processEvents()
        
        print("로딩 인디케이터 숨김")

    def cleanup_loader_threads(self):
        """로더 스레드를 정리하고 메모리를 확보합니다."""
        try:
            # 완료되었거나 오류가 발생한 스레드 제거
            current_threads = list(self.loader_threads.items())
            for path, loader in current_threads:
                # 로더가 아직 실행 중이 아닌 경우 (완료된 경우)
                try:
                    if not loader.isRunning():
                        # 스레드 객체 제거
                        del self.loader_threads[path]
                except Exception as e:
                    print(f"스레드 정리 중 오류: {path}, {e}")
                    # 오류가 발생한 스레드는 목록에서 제거 시도
                    try:
                        del self.loader_threads[path]
                    except:
                        pass
        except Exception as e:
            print(f"스레드 정리 중 일반 오류: {e}")

    def on_image_loaded(self, path, image, size_mb):
        """이미지 로딩이 완료되면 호출되는 콜백 메서드"""
        # 로딩 표시 숨기기
        self.hide_loading_indicator()
        
        # 이미지 크기 제한 (메모리 관리)
        large_image_threshold = 50  # MB 단위
        
        # 너무 큰 이미지는 캐시하지 않음
        if size_mb < large_image_threshold:
            # 캐시에 이미지 저장 (파일 확장자에 따라 적절한 캐시 선택)
            file_ext = os.path.splitext(path)[1].lower()
            
            if file_ext == '.psd':
                self.psd_cache.put(path, image, size_mb)
            elif file_ext in ['.gif', '.webp']:
                self.gif_cache.put(path, image, size_mb)
            else:
                # 원본 이미지를 캐시 (회전하지 않은 상태)
                self.image_cache.put(path, image, size_mb)
        else:
            print(f"크기가 너무 큰 이미지는 캐시되지 않습니다: {os.path.basename(path)} ({size_mb:.2f}MB)")
        
        # 현재 경로가 로드된 이미지 경로와 일치하는 경우에만 표시
        if self.current_image_path == path:
            # 회전 각도가 0이 아니면 이미지 회전 적용 (원본 이미지에 직접 적용)
            display_image = image  # 기본적으로 원본 이미지 사용
            if hasattr(self, 'current_rotation') and self.current_rotation != 0:
                transform = QTransform().rotate(self.current_rotation)
                display_image = image.transformed(transform, Qt.SmoothTransformation)
                print(f"이미지에 회전 적용됨: {self.current_rotation}°")
            
            # 이미지 크기에 따라 스케일링 방식 결정
            # 작은 이미지는 고품질 변환, 큰 이미지는 빠른 변환 사용
            transform_method = Qt.SmoothTransformation if size_mb < 20 else Qt.FastTransformation
            
            # 화면 크기 얻기
            label_size = self.image_label.size()
            
            # 이미지 크기가 화면보다 훨씬 크면 2단계 스케일링 적용
            if size_mb > 30 and (display_image.width() > label_size.width() * 2 or display_image.height() > label_size.height() * 2):
                # 1단계: 빠른 방식으로 대략적인 크기로 축소
                # float 값을 int로 변환 (타입 오류 수정)
                intermediate_pixmap = display_image.scaled(
                    int(label_size.width() * 1.2),  # float를 int로 변환
                    int(label_size.height() * 1.2),  # float를 int로 변환
                    Qt.KeepAspectRatio,
                    Qt.FastTransformation  # 빠른 변환 사용
                )
                
                # 2단계: 고품질 방식으로 최종 크기로 조정
                scaled_pixmap = intermediate_pixmap.scaled(
                    label_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation  # 고품질 변환 사용
                )
            else:
                # 일반 크기 이미지는 바로 스케일링
                scaled_pixmap = display_image.scaled(
                    label_size,
                    Qt.KeepAspectRatio,
                    transform_method  # 이미지 크기에 따라 결정된 변환 방식 사용
                )
            
            # 스케일링된 이미지 표시
            self.image_label.setPixmap(scaled_pixmap)
            print(f"이미지 로드 완료: {os.path.basename(path)}, 크기: {size_mb:.2f}MB")
        
        # 스레드 정리
        if path in self.loader_threads:
            del self.loader_threads[path]
        
        # 추가: 전체화면 모드에서 지연된 리사이징 적용
        if self.isFullScreen():
            QTimer.singleShot(200, self.delayed_resize)
            print("전체화면 모드에서 지연된 리사이징 적용")

    def on_image_error(self, path, error):
        """이미지 로딩 중 오류가 발생하면 호출되는 콜백 메서드"""
        # 로딩 표시 숨기기
        self.hide_loading_indicator()
        
        # 오류 메시지 표시
        error_msg = f"이미지 로드 실패: {os.path.basename(path)}\n{error}"
        self.show_message(error_msg)
        print(error_msg)  # 콘솔에도 출력
        
        # 스레드 정리
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
        """회전 변경 신호를 처리합니다."""
        # 호환성을 위해 current_rotation 업데이트
        self.current_rotation = angle
        
        # 필요한 경우 여기에 추가 작업 구현
        print(f"회전 각도 변경됨: {angle}°")

    def rotate_image(self, clockwise=True):
        """이미지를 90도 회전합니다."""
        if not self.current_image_path:
            return
            
        # RotationManager를 사용하여 회전 각도 변경
        if clockwise:
            self.rotation_manager.rotate_clockwise()
        else:
            self.rotation_manager.rotate_counterclockwise()
            
        # 이전 코드와의 호환성을 위해 current_rotation 업데이트
        self.current_rotation = self.rotation_manager.rotation_angle
        
        # AnimationHandler에 회전 각도 전달
        if hasattr(self, 'animation_handler'):
            self.animation_handler.current_rotation = self.current_rotation
        
        # 현재 미디어 타입에 따라 다르게 처리
        if self.current_media_type == 'image' or self.current_media_type == 'webp_image':
            # 일반 이미지 회전 - 현재 회전 각도에 따라 새로 이미지를 로드하여 처리
            file_ext = os.path.splitext(self.current_image_path)[1].lower()
            if file_ext == '.psd':
                # PSD 파일은 PSDHandler를 통해 다시 로드
                self.psd_handler.load(self.current_image_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif']:
                # 일반 이미지는 ImageHandler를 통해 다시 로드
                self.image_handler.load(self.current_image_path)
                print(f"일반 이미지 회전 적용: {self.current_rotation}°")
            elif file_ext == '.webp':
                # WEBP 일반 이미지 (AnimationHandler를 통해 처리)
                if hasattr(self, 'animation_handler'):
                    self.animation_handler.rotate_static_image(self.current_image_path)
                    print(f"WEBP 이미지 회전 AnimationHandler로 적용: {self.current_rotation}°")
                else:
                    # 예전 방식 (직접 처리)
                    image = QImage(self.current_image_path)
                    if not image.isNull():
                        pixmap = QPixmap.fromImage(image)
                        transform = QTransform().rotate(self.current_rotation)
                        rotated_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                        
                        # 회전된 이미지를 화면에 맞게 크기 조절
                        label_size = self.image_label.size()
                        scaled_pixmap = rotated_pixmap.scaled(
                            label_size,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.image_label.setPixmap(scaled_pixmap)
                    print(f"WEBP 일반 이미지 회전 직접 적용: {self.current_rotation}°")
        elif self.current_media_type in ['gif_animation', 'webp_animation']:
            # AnimationHandler 사용
            if hasattr(self, 'animation_handler'):
                # 현재 재생 상태 및 프레임 기억 (AnimationHandler 통해 접근)
                was_playing = self.animation_handler.is_playing()
                current_frame = 0
                
                if self.animation_handler.current_movie:
                    current_frame = self.animation_handler.current_movie.currentFrameNumber()
                
                # 이미지 레이블 초기화 (중요: 깜빡임 방지)
                self.image_label.clear()
                
                # 애니메이션 핸들러 정리
                self.animation_handler.cleanup()
                
                # 이벤트 처리로 UI 갱신 시간 확보
                QApplication.processEvents()
                
                # AnimationHandler를 통해 다시 로드
                if self.current_media_type == 'gif_animation':
                    self.animation_handler.load_gif(self.current_image_path)
                elif self.current_media_type == 'webp_animation':
                    self.animation_handler.load_webp(self.current_image_path)
                    
                # 프레임 및 재생 상태 복원 (AnimationHandler로 복원)
                if self.animation_handler.current_movie:
                    if current_frame < self.animation_handler.current_movie.frameCount():
                        self.animation_handler.seek_to_frame(current_frame)
                    
                    # 재생 상태 복원
                    if not was_playing:
                        self.animation_handler.current_movie.setPaused(True)
                        self.play_button.setText("▶")  # 재생 아이콘
            else:
                # AnimationHandler 없는 경우 생성하고 로드
                self.animation_handler = AnimationHandler(self.image_label, self)
                
                # AnimationHandler를 통해 다시 로드
                if self.current_media_type == 'gif_animation':
                    self.animation_handler.load_gif(self.current_image_path)
                elif self.current_media_type == 'webp_animation':
                    self.animation_handler.load_webp(self.current_image_path)
        elif self.current_media_type == 'video':
            # 비디오 회전 처리
            try:
                # 기존 코드 교체: self.player 대신 video_handler 사용
                if hasattr(self, 'video_handler') and self.video_handler:
                    # 비디오 핸들러의 rotate 메서드 호출
                    self.video_handler.rotate(self.current_rotation)
            except Exception as e:
                self.show_message(f"비디오 회전 중 오류 발생: {str(e)}")
                
        # 회전 상태 메시지 표시
        if self.current_media_type == 'video':
            self.show_message(f"비디오 회전: {self.current_rotation}°")
        elif self.current_media_type in ['gif_animation', 'webp_animation']:
            self.show_message(f"애니메이션 회전: {self.current_rotation}°")
        else:
            self.show_message(f"이미지 회전: {self.current_rotation}°")

    def update_button_sizes(self):
        """버튼 크기를 창 크기에 맞게 업데이트하는 메서드 - 이제 ControlsLayout에 위임"""
        if hasattr(self, 'controls_layout'):
            self.controls_layout.update_button_sizes()
        else:
            # 컨트롤 레이아웃이 아직 초기화되지 않은 경우 (예: 초기 로딩 과정)
            print("ControlsLayout이 초기화되지 않았습니다. 버튼 크기 업데이트를 건너뜁니다.")

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
            
            # core.config 모듈의 load_settings 함수를 사용해 설정을 로드합니다
            loaded_settings = load_settings("key_settings.json")
            
            # 기존 설정 파일에서 값을 불러와 기본 설정에 적용합니다
            for key, value in loaded_settings.items():
                if key in default_settings:
                    try:
                        # JSON에서 불러온 값은 문자열이나 숫자일 수 있으므로 정수로 변환합니다
                        default_settings[key] = int(value)
                    except (ValueError, TypeError) as e:
                        # 변환할 수 없는 경우 오류 메시지 출력하고 기본값 유지
                        print(f"키 설정 '{key}'의 값을 변환할 수 없습니다: {e}")
            
            # 최종 설정을 self.key_settings에 할당합니다
            self.key_settings = default_settings
            print("키 설정 로드 완료")
            
        except Exception as e:
            # 로드 중 예외가 발생하면 기본 설정을 사용합니다
            print(f"키 설정 로드 오류: {e}")
            self.key_settings = default_settings

    def save_key_settings(self):
        """키 설정을 저장합니다."""
        try:
            # core.config 모듈의 save_settings 함수를 사용해 설정을 저장합니다
            if save_settings(self.key_settings, "key_settings.json"):
                print("키 설정이 저장되었습니다")
            else:
                print("키 설정 저장에 실패했습니다")
        except Exception as e:
            print(f"키 설정 저장 오류: {e}")
    
    def show_preferences_dialog(self):
        # 키 설정 다이얼로그 표시
        dialog = PreferencesDialog(self, self.key_settings)
        if dialog.exec_() == QDialog.Accepted:
            # 변경된 키 설정 적용
            self.key_settings = dialog.get_key_settings()
            # 키 설정 저장
            self.save_key_settings()
            # 메시지 표시
            self.show_message("키 설정이 변경되었습니다.")

    def show_about_dialog(self):
        # 정보 다이얼로그 표시
        dialog = AboutDialog(self)
        dialog.exec_()

    def cleanup_current_media(self):
        """현재 미디어 정리 (이미지, 비디오, 애니메이션 등)"""
        # 디버깅을 위한 초기 상태 확인
        if hasattr(self, 'debug_mode') and self.debug_mode:
            self.debug_qmovie_before_cleanup()
            
        print("미디어 리소스 정리 시작...")
        
        # 비디오 재생 중지
        self.stop_video()  

        # 애니메이션 핸들러 존재 여부 확인
        animation_handler_exists = hasattr(self, 'animation_handler')

        # 애니메이션 핸들러 리소스 정리 (current_movie 포함)
        if animation_handler_exists:
            print("애니메이션 핸들러 정리 시작...")
            self.animation_handler.cleanup()
            
            # 이벤트 처리 루프 실행으로 UI 갱신 및 정리 작업 완료 유도
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()
        
        # 이미지 라벨 초기화 - MediaDisplay의 clear_media 메서드 사용
        if hasattr(self, 'image_label'):
            print("MediaDisplay 초기화...")
            # MediaDisplay의 clear_media 메서드 호출
            self.image_label.clear_media()
            # 이벤트 프로세싱
            QApplication.processEvents()
        
        # 슬라이더 신호 연결 해제 및 초기화
        self.disconnect_all_slider_signals()
        if hasattr(self, 'playback_slider'):
            self.playback_slider.setRange(0, 0)
            self.playback_slider.setValue(0)

        # 재생 버튼 상태 초기화
        if hasattr(self, 'play_button'):
            self.play_button.set_play_state(True)  # 일시정지 아이콘으로 설정
        
        # 시간 레이블 초기화
        if hasattr(self, 'time_label'):
            self.time_label.setText("00:00 / 00:00")
            self.time_label.show()
            
        # 가비지 컬렉션 명시적 호출
        try:
            import gc
            gc.collect()
            print("가비지 컬렉션 실행 완료")
        except Exception as e:
            print(f"가비지 컬렉션 호출 중 오류: {e}")
            
        print("미디어 리소스 정리 완료")

        # 디버깅을 위한 정리 후 상태 확인
        if hasattr(self, 'debug_mode') and self.debug_mode:
            self.debug_qmovie_after_cleanup()

    def create_single_shot_timer(self, timeout, callback):
        """
        싱글샷 타이머를 생성하고 추적합니다.
        
        Args:
            timeout (int): 타이머 실행 지연 시간 (밀리초)
            callback (callable): 타이머 만료 시 실행할 콜백 함수
            
        Returns:
            QTimer: 생성된 타이머 객체
        """
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._handle_single_shot_timeout(timer, callback))
        timer.start(timeout)
        
        # 타이머 추적 리스트에 추가
        self.singleshot_timers.append(timer)
        return timer
    
    def _handle_single_shot_timeout(self, timer, callback):
        """
        싱글샷 타이머의 타임아웃을 처리합니다.
        
        Args:
            timer (QTimer): 만료된 타이머
            callback (callable): 실행할 콜백 함수
        """
        try:
            # 콜백 실행
            callback()
        finally:
            # 타이머 정리
            if timer in self.singleshot_timers:
                self.singleshot_timers.remove(timer)
            timer.deleteLater()

    def toggle_debug_mode(self):
        """디버깅 모드를 켜고 끕니다."""
        import gc
        import objgraph
        
        if not hasattr(self, 'debug_mode'):
            self.debug_mode = False
            
        self.debug_mode = not self.debug_mode
        print(f"디버깅 모드: {'켜짐' if self.debug_mode else '꺼짐'}")
        
        # 디버깅 모드가 켜진 경우 현재 QMovie 객체 상태 출력
        if self.debug_mode:
            self.debug_qmovie_status()
            
    def debug_qmovie_status(self):
        """현재 QMovie 객체 상태를 출력합니다."""
        import gc
        import objgraph
        from PyQt5.QtGui import QMovie
        import types
        
        print("\n===== QMovie 객체 상태 =====")
        # QMovie 객체 수 확인
        try:
            movie_count = objgraph.count('QMovie')
            print(f"QMovie 객체 수: {movie_count}")
        except Exception as e:
            print(f"objgraph로 QMovie 객체 수 확인 중 오류: {e}")
        
        # 모든 객체에서 QMovie 인스턴스 찾기
        qmovie_objects = []
        for obj in gc.get_objects():
            if isinstance(obj, QMovie):
                qmovie_objects.append(obj)
                
        print(f"gc에서 찾은 QMovie 객체 수: {len(qmovie_objects)}")
        
        # 각 QMovie 객체에 대한 참조 출력
        for i, movie in enumerate(qmovie_objects):
            print(f"\nQMovie 객체 #{i+1}:")
            try:
                print(f"- 파일명: {movie.fileName() if movie.fileName() else '알 수 없음'}")
                print(f"- 상태: {'실행 중' if movie.state() == QMovie.Running else '중지됨'}")
            except Exception as e:
                print(f"QMovie 속성 접근 중 오류: {e}")
            
            # 이 객체를 참조하는 객체들 찾기
            try:
                referrers = gc.get_referrers(movie)
                print(f"- 참조하는 객체 수: {len(referrers)}")
                
                # 참조하는 객체 유형 분석
                ref_types = {}
                for ref in referrers:
                    ref_type = type(ref).__name__
                    if ref_type in ref_types:
                        ref_types[ref_type] += 1
                    else:
                        ref_types[ref_type] = 1
                        
                print("- 참조 유형:")
                for ref_type, count in ref_types.items():
                    print(f"  - {ref_type}: {count}개")
                
                # 중요 참조 자세히 출력 (모듈, 함수, 클래스 외의 참조)
                print("- 중요 참조 상세:")
                for ref in referrers:
                    # 함수, 모듈, 클래스, dict, list 등은 건너뛰기
                    if (isinstance(ref, (types.ModuleType, types.FunctionType, type)) or 
                            type(ref).__name__ in ['dict', 'list', 'tuple', 'set', 'frame']):
                        continue
                        
                    # LRUCache 객체인지 확인
                    if type(ref).__name__ == 'LRUCache' or 'Cache' in type(ref).__name__:
                        print(f"  - 캐시 객체 발견: {type(ref).__name__}")
                        if hasattr(ref, 'cache'):
                            print(f"    - 캐시 항목 수: {len(ref.cache)}")
                            # 캐시 내의 QMovie 객체 찾기
                            for k, v in ref.cache.items():
                                if v is movie:
                                    print(f"    - 캐시 키: {k}")
                                    
                    elif hasattr(ref, 'image_label') and hasattr(ref, 'current_movie'):
                        print(f"  - AnimationHandler 의심 객체: {type(ref).__name__}")
                        print(f"    - current_movie: {ref.current_movie is movie}")
                        print(f"    - image_label.movie(): {ref.image_label.movie() is movie if hasattr(ref.image_label, 'movie') else 'N/A'}")
                    else:
                        print(f"  - 기타 객체: {type(ref).__name__}")
                        # 객체의 주요 속성 출력
                        for attr_name in dir(ref):
                            if attr_name.startswith('__'):
                                continue
                            try:
                                attr = getattr(ref, attr_name)
                                if attr is movie:
                                    print(f"    - 속성: {attr_name} ({type(ref).__name__}.{attr_name} == QMovie)")
                            except:
                                pass
            except Exception as e:
                print(f"참조 분석 중 오류: {e}")
        
        print("\n===== 메모리 상위 객체 =====")
        try:
            objgraph.show_most_common_types(limit=10)
        except Exception as e:
            print(f"메모리 상위 객체 분석 중 오류: {e}")
        
    def debug_qmovie_before_cleanup(self):
        """정리 전 QMovie 상태를 출력합니다."""
        print("\n===== 정리 전 QMovie 상태 =====")
        self.debug_qmovie_status()
        
    def debug_qmovie_after_cleanup(self):
        """정리 후 QMovie 상태를 출력합니다."""
        import gc
        # 가비지 컬렉션 강제 실행
        gc.collect()
        print("\n===== 정리 후 QMovie 상태 =====")
        self.debug_qmovie_status()
        
    def generate_qmovie_reference_graph(self):
        """QMovie 객체의 참조 그래프를 생성합니다."""
        import gc
        import objgraph
        from PyQt5.QtGui import QMovie
        
        # 가비지 컬렉션 강제 실행
        gc.collect()
        
        # QMovie 객체 찾기
        qmovie_objects = []
        for obj in gc.get_objects():
            if isinstance(obj, QMovie):
                qmovie_objects.append(obj)
                
        if not qmovie_objects:
            print("QMovie 객체를 찾을 수 없습니다.")
            return
            
        print(f"{len(qmovie_objects)}개의 QMovie 객체 발견, 참조 그래프 생성 중...")
        
        try:
            # 첫 번째 QMovie 객체에 대한 참조 그래프 생성
            objgraph.show_backrefs(
                qmovie_objects[0], 
                max_depth=5, 
                filename='qmovie_refs.png',
                filter=lambda x: not isinstance(x, dict)
            )
            print("참조 그래프가 'qmovie_refs.png' 파일로 저장되었습니다.")
        except Exception as e:
            print(f"참조 그래프 생성 중 오류: {e}")

class ScrollableMenu(QMenu):
    """스크롤을 지원하는 메뉴 클래스"""
    def __init__(self, parent=None):
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
                font-size: 9pt;  /* 글자 크기 축소 */
            }
            QMenu::item:selected {
                background-color: #34495e;
                color: #ecf0f1;
            }
            QMenu::separator {
                height: 1px;
                background: #34495e;
                margin: 3px 0;  /* 구분선 간격 축소 */
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
        # 마우스 휠 이벤트 처리
        super().wheelEvent(event)
        # 이벤트가 처리되었음을 표시
        event.accept()
        
    def showEvent(self, event):
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
        """여러 액션을 추가하고 필요시 스크롤을 활성화합니다"""
        for action in actions:
            self.addAction(action)
        
        # 액션이 많으면 스크롤 속성을 다시 설정
        if len(actions) > 7:
            self.setProperty("_q_scrollable", True)
            self.setStyle(self.style())

# 메인 함수
def main():
    app = QApplication(sys.argv)  # Qt 애플리케이션 객체 생성
    viewer = ImageViewer()  # ImageViewer 클래스의 객체 생성
    viewer.show()  # 뷰어 창 표시
    sys.exit(app.exec_())  # 이벤트 루프 실행

# 프로그램 실행 시 main() 함수 실행
if __name__ == "__main__":
    main()  # 메인 함수 실행