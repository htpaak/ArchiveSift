# 이미지 및 비디오 뷰어 애플리케이션 (PyQt5 기반)
import sys  # 시스템 관련 기능 제공 (프로그램 종료, 경로 관리 등)
import os  # 운영체제 관련 기능 제공 (파일 경로, 디렉토리 처리 등)
import platform
import shutil  # 파일 복사 및 이동 기능 제공 (고급 파일 작업)
import re  # 정규표현식 처리 기능 제공 (패턴 검색 및 문자열 처리)
import json  # JSON 파일 처리를 위한 모듈
from collections import OrderedDict  # LRU 캐시 구현을 위한 정렬된 딕셔너리
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout, QSizePolicy, QSlider, QLayout, QSpacerItem, QStyle, QStyleOptionSlider, QMenu, QAction, QScrollArea, QListWidgetItem, QListWidget, QAbstractItemView, QInputDialog, QMessageBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QLineEdit, QStackedWidget  # PyQt5 UI 위젯 (사용자 인터페이스 구성 요소)
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QFont, QMovie, QCursor, QIcon, QColor, QPalette, QFontMetrics, QTransform, QKeySequence  # 그래픽 요소 처리 (이미지, 폰트, 커서 등)
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
# 사용자 정의 UI 위젯
from ui.components.slider import ClickableSlider
from ui.components.scrollable_menu import ScrollableMenu
# 대화상자
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.preferences_dialog import PreferencesDialog
from events.handlers.keyboard_handler import KeyInputEdit
# 북마크 관리
from features.bookmark import BookmarkManager  # 북마크 관리 클래스


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
        
        # 북마크 관리자 초기화
        self.bookmark_manager = BookmarkManager(self)

        # UI 잠금 상태 변수 분리
        self.is_bottom_ui_locked = True  # 하단 UI 고정 상태 (True: 항상 표시, False: 마우스 위치에 따라 표시/숨김)
        self.is_title_ui_locked = True  # 상단 타이틀바 고정 상태

        # 이전 호환성을 위한 변수 유지
        self.is_ui_locked = True

        self.installEventFilter(self)
        
        # 키 설정 초기화
        self.key_settings = {
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
        
        # 키 설정 로드
        self.load_key_settings()
        
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

        # 전체 레이아웃 설정
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 여백 완전히 제거
        main_layout.setSpacing(0)  # 레이아웃 간 간격 완전히 제거
        
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
        title_lock_btn = QPushButton("🔒")  # 잠금 아이콘으로 초기화
        title_lock_btn.setStyleSheet("color: white; background: none; border: none; padding: 10px;")
        title_lock_btn.clicked.connect(self.toggle_title_ui_lock)  # 제목표시줄 UI 잠금 토글 기능 연결
        self.title_lock_btn = title_lock_btn  # 버튼 객체 저장
        
        # 창 컨트롤 버튼들 (최소화, 최대화, 닫기 - 윈도우 기본 버튼 대체)
        min_btn = QPushButton("_")  # 최소화 버튼
        min_btn.setStyleSheet("color: white; background: none; border: none; padding: 10px;")
        min_btn.clicked.connect(self.showMinimized)  # 최소화 기능 연결
        
        max_btn = QPushButton("□")  # 최대화 버튼
        max_btn.setStyleSheet("color: white; background: none; border: none; padding: 10px;")
        max_btn.clicked.connect(self.toggle_maximize_state)  # 최대화/복원 기능 연결
        self.max_btn = max_btn  # 버튼 객체 저장 (최대화 상태에 따라 아이콘 변경 위함)

        # 여기에 전체화면 버튼 추가
        fullscreen_btn = QPushButton("🗖")  # 전체화면 버튼 (적절한 아이콘 사용)
        fullscreen_btn.setStyleSheet("color: white; background: none; border: none; padding: 10px;")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)  # 전체화면 토글 기능 연결
        self.fullscreen_btn = fullscreen_btn  # 버튼 객체 저장
        
        close_btn = QPushButton("×")  # 닫기 버튼
        close_btn.setStyleSheet("color: white; background: none; border: none; padding: 10px;")
        close_btn.clicked.connect(self.close)  # 닫기 기능 연결
        
        # 창 컨트롤 버튼들 레이아웃에 추가
        title_layout.addWidget(title_lock_btn)
        title_layout.addWidget(min_btn)
        title_layout.addWidget(max_btn)
        title_layout.addWidget(fullscreen_btn)
        title_layout.addWidget(close_btn)

        # 제목 표시줄을 메인 레이아웃에 추가 (1% 비율 - 전체 UI 중 작은 부분)
        main_layout.addWidget(self.title_bar, 1)
        
        # 상단 툴바 컨테이너 생성 코드를 제거합니다.
        # 이미지 표시 컨테이너 위젯
        self.image_container = QWidget()
        self.image_container.setStyleSheet("background-color: white;")  # 흰색 배경
        
        # 책갈피 메뉴 초기화
        self.bookmark_manager.update_bookmark_menu()
        
        # 컨테이너 레이아웃 설정
        container_layout = QVBoxLayout(self.image_container)
        container_layout.setContentsMargins(0, 0, 0, 0)  # 여백 없음
        container_layout.setSpacing(0)  # 간격 없음
        
        # 이미지 표시 레이블
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)  # 중앙 정렬 (이미지 중앙 배치)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 확장 가능한 크기 정책
        self.image_label.setStyleSheet("background-color: black;")  # 검은색 배경 (이미지 대비 위함)
        container_layout.addWidget(self.image_label)
        
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

        # 왼쪽 공백 추가 (창 너비에 비례하게 resizeEvent에서 동적 조정)
        # 왼쪽 spacer 제거
        # self.left_spacer = QSpacerItem(10, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
        # new_slider_layout.addItem(self.left_spacer)
        
        # 폴더 열기 버튼 (첫 번째 위치)
        self.open_button = QPushButton('Open Folder', self)
        self.open_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 고정 크기 사용
        self.open_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                padding: 8px;  /* 패딩을 10px에서 8px로 줄임 */
                border-radius: 3px;
                font-size: 12px;  /* 폰트 크기 지정 */
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        self.open_button.clicked.connect(self.open_folder)  # 폴더 열기 기능 연결 (이미지 폴더 선택)
        new_slider_layout.addWidget(self.open_button)

        # Set Base Folder 버튼 (두 번째 위치)
        self.set_base_folder_button = QPushButton('Set Folder', self)
        self.set_base_folder_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 고정 크기 사용
        self.set_base_folder_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                padding: 8px;  /* 패딩을 10px에서 8px로 줄임 */
                border-radius: 3px;
                font-size: 12px;  /* 폰트 크기 지정 */
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        self.set_base_folder_button.clicked.connect(self.set_base_folder)  # 기준 폴더 설정 기능 연결 (복사 대상 폴더)
        new_slider_layout.addWidget(self.set_base_folder_button)

        # 재생 버튼 (세 번째 위치)
        self.play_button = QPushButton("▶", self)  # 재생 아이콘 버튼
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                padding: 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        self.play_button.clicked.connect(self.toggle_animation_playback)  # 재생 버튼 클릭 이벤트 연결 (재생/일시정지 전환)
        new_slider_layout.addWidget(self.play_button)

        # 회전 버튼 추가 (반시계 방향)
        self.rotate_ccw_button = QPushButton("↺", self)
        self.rotate_ccw_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """)
        self.rotate_ccw_button.clicked.connect(lambda: self.rotate_image(False))
        new_slider_layout.addWidget(self.rotate_ccw_button)

        # 회전 버튼 추가 (시계 방향)
        self.rotate_cw_button = QPushButton("↻", self)
        self.rotate_cw_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);
                color: white;
                border: none;
                padding: 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """)
        self.rotate_cw_button.clicked.connect(lambda: self.rotate_image(True))
        new_slider_layout.addWidget(self.rotate_cw_button)


        # MPV 상태 확인을 위한 타이머 설정 (주기적으로 재생 상태 업데이트)
        self.play_button_timer = QTimer(self)
        self.play_button_timer.timeout.connect(self.update_play_button)  # 타이머가 작동할 때마다 update_play_button 메소드 호출
        self.play_button_timer.start(200)  # 200ms마다 상태 확인 (초당 5번 업데이트로 최적화)
        self.timers.append(self.play_button_timer)  # 타이머 추적에 추가

        # 기존 슬라이더 (재생 바) 추가
        self.playback_slider = ClickableSlider(Qt.Horizontal, self)  # ClickableSlider로 변경 (클릭 시 해당 위치로 이동)
        self.playback_slider.setRange(0, 100)  # 슬라이더 범위 설정 (0-100%)
        self.playback_slider.setValue(0)  # 초기 값을 0으로 설정 (시작 위치)
        self.playback_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # 가로 방향으로 확장 가능하도록 설정
        self.playback_slider.setFixedHeight(50)  # 슬라이더 높이를 50px로 고정
        
        # 슬라이더에 추가 스타일 설정
        # additional_style = "QSlider { background: transparent; padding: 0px; margin: 0px; }"
        # self.playback_slider.setStyleSheet(additional_style)

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
        self.mute_button = QPushButton("🔈", self)  # 음소거 해제 아이콘으로 초기화
        self.mute_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 고정 크기 사용
        self.mute_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                padding: 8px;  /* 패딩을 10px에서 8px로 줄임 */
                border-radius: 3px;
                font-size: 12px;  /* 폰트 크기 지정 */
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        self.mute_button.clicked.connect(self.toggle_mute)  # 음소거 토글 기능 연결
        new_slider_layout.addWidget(self.mute_button)

        # 볼륨 슬라이더 추가 (음량 조절)
        self.volume_slider = ClickableSlider(Qt.Horizontal, self)
        self.volume_slider.setRange(0, 100)  # 볼륨 범위 0-100%
        self.volume_slider.setValue(100)  # 기본 볼륨 100%으로 설정 (최대 음량)
        self.volume_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 고정 크기 사용
        self.volume_slider.setFixedHeight(50)  # 슬라이더 높이를 50px로 고정
        
        # 볼륨 슬라이더에 추가 스타일 설정
        # self.volume_slider.setStyleSheet(additional_style)
        self.volume_slider.valueChanged.connect(self.adjust_volume)  # 슬라이더 값 변경 시 음량 조절 함수 연결
        self.volume_slider.clicked.connect(self.adjust_volume)  # 클릭 이벤트 연결 (클릭 위치로 음량 즉시 변경)
        new_slider_layout.addWidget(self.volume_slider)  # 음량 조절 슬라이더를 레이아웃에 추가
        
        # 메뉴 버튼 추가 
        self.menu_button = QPushButton('☰', self)  # 메뉴 아이콘 (햄버거 스타일)
        self.menu_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 고정 크기 사용
        self.menu_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);
                color: white;
                border: none;
                padding: 8px;  /* 패딩을 10px에서 8px로 줄임 */
                border-radius: 3px;
                font-size: 12px;  /* 폰트 크기를 14px에서 12px로 줄임 */
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """)
        self.menu_button.clicked.connect(self.show_menu_above)  # 메뉴 표시 함수 연결
        new_slider_layout.addWidget(self.menu_button)
        
        # 북마크 버튼 추가 (가장 오른쪽에 위치)
        self.slider_bookmark_btn = QPushButton('★', self)
        self.slider_bookmark_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 고정 크기 사용
        self.slider_bookmark_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(241, 196, 15, 0.9);  /* 노란색 배경 */
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(241, 196, 15, 1.0);  /* 호버 시 더 진한 노란색 */
            }
        """)
        # 북마크 토글 기능 대신 위로 펼쳐지는 메뉴 표시 기능으로 변경
        self.slider_bookmark_btn.clicked.connect(self.show_bookmark_menu_above)
        new_slider_layout.addWidget(self.slider_bookmark_btn)
        
        # 북마크 버튼을 북마크 매니저에 등록
        self.bookmark_manager.set_bookmark_button(self.slider_bookmark_btn)

        # 여기에 UI 고정 버튼 추가 (완전히 새로운 코드로 교체)
        self.ui_lock_btn = QPushButton('🔒', self)  # 잠금 아이콘으로 초기화
        self.ui_lock_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 고정 크기 사용
        # 고정 상태의 빨간색 스타일을 직접 지정 (초기값)
        self.ui_lock_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(231, 76, 60, 0.9);  /* 빨간색 배경 */
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(231, 76, 60, 1.0);  /* 호버 시 더 진한 빨간색 */
            }
        """)
        self.ui_lock_btn.clicked.connect(self.toggle_ui_lock)  # 토글 함수 연결
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
        # 볼륨 슬라이더는 별도 처리가 필요하므로 여기 포함하지 않음

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

        # 메인 레이아웃에 위젯 추가
        main_layout.addWidget(self.image_container, 90)  # 90% (이미지가 화면의 대부분 차지)

        # 하단 버튼 영역을 메인 레이아웃에 추가
        main_layout.addLayout(bottom_layout, 9)  # 9% (하단 컨트롤 영역)

        self.setFocusPolicy(Qt.StrongFocus)  # 강한 포커스를 설정 (위젯이 포커스를 받을 수 있도록 설정 - 키보드 이벤트 처리용)

        self.cap = None  # 비디오 캡처 객체 초기화 (OpenCV 비디오 캡처)
        self.timer = QTimer(self)  # 타이머 객체 생성 (비디오 프레임 업데이트용)
        self.timer.timeout.connect(self.update_video_frame)  # 타이머가 작동할 때마다 update_video_frame 메소드 호출

        # 마우스 트래킹 활성화 (마우스 움직임 감지를 위한 설정)
        self.setMouseTracking(True)
        self.image_container.setMouseTracking(True)
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

        # 메뉴 관련 변수 초기화
        self.dropdown_menu = None  # 드롭다운 메뉴 객체

        # 초기 및 resizeEvent에서 동적으로 호출되는 커스텀 UI 설정 메서드
        self.setup_custom_ui()  # 초기 호출 (창 크기에 맞게 UI 요소 조정)
        
        # 스타일시트 기본 적용 (슬라이더 외관 디자인 정의)
        self.playback_slider.setStyleSheet(self.slider_style)  # 재생 슬라이더 스타일 적용
        self.volume_slider.setStyleSheet(self.slider_style)  # 음량 조절 슬라이더 스타일 적용
        
        # 연결 추가 (이벤트와 함수 연결)
        self.volume_slider.valueChanged.connect(self.adjust_volume)  # 슬라이더 값 변경 시 음량 조절 메서드 연결 (볼륨 실시간 조절)

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
        QTimer.singleShot(0, self.update_ui_lock_button_state)

        # 미디어 핸들러 초기화
        self.image_handler = ImageHandler(self, self.image_label)
        self.psd_handler = PSDHandler(self, self.image_label)
        self.video_handler = VideoHandler(self, self.image_label)

    def delete_current_image(self):
        """현재 이미지를 삭제합니다 (크로스 플랫폼)."""
        if not self.current_image_path or not self.image_files:
            self.show_message("삭제할 이미지가 없습니다")
            return
            
        try:
            import os
            from pathlib import Path
            
            # Path 객체 사용 (크로스 플랫폼 호환성 향상)
            file_path = Path(self.current_image_path).resolve()
            
            # 파일이 존재하는지 확인
            if not file_path.is_file():
                self.show_message(f"파일이 존재하지 않습니다: {file_path.name}")
                # 이미지 파일 리스트에서 제거
                if self.current_image_path in self.image_files:
                    self.image_files.remove(self.current_image_path)
                return
                
            # 삭제 전 확인 메시지
            from PyQt5.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('이미지 삭제')
            msg_box.setText(f"정말로 이미지를 삭제하시겠습니까?\n{file_path.name}")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)

            reply = msg_box.exec_()
            
            if reply == QMessageBox.Yes:
                # send2trash 모듈 사용해서 휴지통으로 이동
                try:
                    # 먼저 send2trash 모듈이 있는지 확인
                    try:
                        from send2trash import send2trash
                    except ImportError:
                        # 자동으로 설치 시도
                        self.show_message("send2trash 모듈 설치 중...")
                        import subprocess
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "send2trash"])
                        from send2trash import send2trash
                    
                    # 휴지통으로 파일 이동
                    send2trash(str(file_path))
                    
                    # 북마크에서 제거 (BookmarkManager를 통해 처리)
                    if self.current_image_path in self.bookmark_manager.bookmarks:
                        self.bookmark_manager.remove_bookmark()
                    
                    # 이미지 파일 리스트에서 제거
                    self.image_files.remove(self.current_image_path)
                    
                    # 현재 인덱스 조정
                    if not self.image_files:  # 남은 파일이 없는 경우
                        self.current_index = 0
                        self.image_label.clear()
                        self.current_image_path = ""
                        self.show_message("모든 이미지가 삭제되었습니다")
                    else:
                        # 인덱스 범위 조정
                        if self.current_index >= len(self.image_files):
                            self.current_index = len(self.image_files) - 1
                        # 다음 이미지 표시
                        self.show_image(self.image_files[self.current_index])
                        self.show_message("이미지가 휴지통으로 이동되었습니다")
                except Exception as e:
                    # 오류 시 상세 로그 출력
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"휴지통 이동 중 오류: {e}\n{error_details}")
                    self.show_message(f"휴지통 이동 실패: {str(e)}")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"삭제 중 예외 발생: {e}\n{error_details}")
            self.show_message(f"삭제 중 오류 발생: {str(e)}")

    def ensure_maximized(self):
        """창이 최대화 상태인지 확인하고 그렇지 않으면 다시 최대화합니다."""
        if not self.isMaximized():
            self.showMaximized()  # 최대화 상태가 아니면 최대화 적용

    def resizeEvent(self, event):
        """창 크기 변경 이벤트 처리 (창 크기 변경 시 UI 요소 조정)"""
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
        self.update_bookmark_button_state()

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
                elif file_ext == '.gif' and hasattr(self, 'current_movie'):
                    # 애니메이션 크기 조정 처리
                    print("GIF 애니메이션 리사이징")  # 디버깅용 메시지
                    self.scale_gif()
                    # UI 처리 완료 후 애니메이션이 제대로 보이도록 강제 프레임 업데이트
                    QApplication.processEvents()
                elif file_ext == '.webp':
                    if hasattr(self, 'current_movie') and self.current_movie:
                        # WEBP 애니메이션 처리
                        print("WEBP 애니메이션 리사이징")  # 디버깅용 메시지
                        self.scale_webp()
                        # UI 처리 완료 후 애니메이션이 제대로 보이도록 강제 프레임 업데이트
                        QApplication.processEvents()
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
            self.update_bookmark_button_state()
                    
        except Exception as e:
            print(f"지연된 리사이징 처리 중 오류 발생: {e}")

    def mouseDoubleClickEvent(self, event):
        """더블 클릭 시 전체화면 또는 최대화 상태 전환"""
        if self.isFullScreen():
            # 전체화면 모드에서는 전체화면 토글 함수 호출
            self.toggle_fullscreen()
        else:
            # 일반 모드에서는 최대화/일반 창 전환
            self.toggle_maximize_state()

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
        """하위 폴더 버튼 클릭 처리 - 현재 이미지를 선택된 폴더로 복사"""
        button = self.sender()  # 클릭된 버튼 객체 참조
        folder_path = button.toolTip()  # 버튼 툴팁에서 폴더 경로 가져오기
        print(f"Selected folder: {folder_path}")  # 선택된 폴더 경로 출력

        # 커서를 일반 모양으로 복원
        QApplication.restoreOverrideCursor()  # 모래시계에서 일반 커서로 복원

        # 현재 이미지를 선택된 폴더로 복사
        self.copy_image_to_folder(folder_path)
        
        # 버튼 클릭 후 약간의 지연을 두고 창에 포커스를 돌려줌
        QTimer.singleShot(50, self.setFocus)

    def open_folder(self):
        """이미지 폴더 열기 대화상자 표시 및 처리"""
        folder_path = QFileDialog.getExistingDirectory(self, "Open Image Folder")  # 폴더 선택 대화상자

        if folder_path:  # 폴더가 선택된 경우
            self.image_files = self.get_image_files(folder_path)  # 지원되는 미디어 파일 목록 가져오기

            if self.image_files:  # 유효한 파일이 있는 경우
                self.image_files.sort()  # 파일 목록 정렬
                self.current_index = 0  # 현재 이미지 인덱스 초기화
                self.show_image(self.image_files[0])  # 첫 번째 이미지 표시
                self.update_image_info()  # 이미지 정보 업데이트 (인덱스 표시 업데이트)
            else:
                print("No valid image files found in the folder.")  # 유효한 파일이 없는 경우 메시지 출력

    def get_image_files(self, folder_path):
        """지원하는 모든 미디어 파일 목록 가져오기"""
        # 지원하는 파일 확장자 목록 (이미지, 비디오, 오디오 파일)
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.psd', '.gif', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif', '.mp4', '.avi', '.wav', '.ts', '.m2ts', '.mov', '.qt', '.mkv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', '.vob', '.wmv', '.mp3', '.flac', '.aac', '.m4a', '.ogg']
        # 폴더 내에서 지원하는 확장자를 가진 모든 파일 경로 목록 반환
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if any(f.lower().endswith(ext) for ext in valid_extensions)]

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

    def show_image(self, image_path):
        """이미지/미디어 파일 표시 및 관련 UI 업데이트"""
        self.stop_video()  # 기존 비디오 재생 중지

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

        # 이전 이미지/애니메이션 정지 및 정리
        self.image_label.clear()  # 레이블 내용 지우기 (애니메이션 정지)
        
        # 기존 진행 중인 로딩 스레드 취소 (현재 로딩 중인 이미지는 제외)
        for path, loader in list(self.loader_threads.items()):
            if path != image_path and loader.isRunning():
                try:
                    loader.terminate()
                    loader.wait(100)  # 최대 100ms 대기
                except:
                    pass
                del self.loader_threads[path]
                print(f"이미지 로딩 취소: {os.path.basename(path)}")
        
        # 기존 QMovie 정리
        try:
            if hasattr(self, 'current_movie') and self.current_movie is not None:
                try:
                    self.current_movie.stop()
                except RuntimeError:
                    # 이미 삭제된 객체인 경우 무시
                    pass
                try:
                    self.current_movie.deleteLater()  # Qt 객체 명시적 삭제 요청
                except RuntimeError:
                    # 이미 삭제된 객체인 경우 무시
                    pass
                self.current_movie = None
        except Exception as e:
            print(f"QMovie 객체 정리 중 오류: {e}")
            self.current_movie = None

        # 파일 이름을 제목표시줄에 표시
        file_name = os.path.basename(image_path) if image_path else "Image Viewer"
        title_text = f"Image Viewer - {file_name}" if image_path else "Image Viewer"
        # 제목표시줄 라벨 찾아서 텍스트 업데이트
        for child in self.title_bar.children():
            if isinstance(child, QLabel):
                child.setText(title_text)
                break
        
        # 책갈피 버튼 상태 업데이트
        self.update_bookmark_button_state()
        
        # 북마크 메뉴 업데이트 추가 - 이미지 변경 시 메뉴 상태도 함께 업데이트
        self.bookmark_manager.update_bookmark_menu()
        
        # 파일 확장자 확인 (소문자로 변환)
        file_ext = os.path.splitext(image_path)[1].lower()
        
        # 애니메이션이 재생 중일 경우 정지
        if hasattr(self, 'current_movie') and self.current_movie:
            self.current_movie.stop()  # 애니메이션 정지
        # 슬라이더 신호 연결 해제
        self.disconnect_all_slider_signals()

        # 슬라이더 초기화
        self.playback_slider.setRange(0, 0)  # 슬라이더 범위를 0으로 설정
        self.playback_slider.setValue(0)  # 슬라이더 초기값을 0으로 설정

        # 재생 버튼을 재생 상태로 초기화 (파일이 변경될 때마다 항상 재생 상태로 시작)
        self.play_button.setText("❚❚")  # 일시정지 아이콘으로 변경 (재생 중 상태)
        
        # FormatDetector를 사용하여 파일 형식 감지
        file_format = FormatDetector.detect_format(image_path)
        
        if file_format == 'gif_image' or file_format == 'gif_animation':
            # GIF 파일 처리 (정적/애니메이션 구분)
            self.current_media_type = file_format  # 미디어 타입 업데이트
            self.show_gif(image_path)  # GIF를 표시하는 메서드 호출
        elif file_format == 'webp_image' or file_format == 'webp_animation':
            # WEBP 파일 처리 (정적/애니메이션 구분)
            self.current_media_type = file_format  # 미디어 타입 업데이트
            self.show_webp(image_path)  # WEBP 파일 처리
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

        # 시간 레이블 초기화
        self.time_label.setText("00:00 / 00:00")  # 시간 레이블 초기화
        self.time_label.show()  # 시간 레이블 표시

        # 제목표시줄과 이미지 정보 레이블을 앞으로 가져옴
        if hasattr(self, 'title_bar'):
            self.title_bar.raise_()
        if hasattr(self, 'image_info_label'):
            self.image_info_label.raise_()
        
        # 추가: 전체화면 모드에서 지연된 리사이징 적용
        if self.isFullScreen():
            QTimer.singleShot(300, self.delayed_resize)
            print("전체화면 모드에서 이미지 로드 후 지연된 리사이징 예약")

    def show_gif(self, image_path):
        # gif 애니메이션을 처리하기 위해 QImageReader를 사용
        reader = QImageReader(image_path)

        # 이미지를 로드하고 애니메이션으로 처리
        if reader.supportsAnimation():  # 애니메이션을 지원하면
            # 애니메이션 GIF로 미디어 타입 설정 (FormatDetector가 이미 분석 완료했다면 유지)
            if self.current_media_type != 'gif_animation':
                self.current_media_type = 'gif_animation'
            
            # 기존 타이머 정지 및 관리
            if hasattr(self, 'gif_timer'):
                self.gif_timer.stop()
                if self.gif_timer in self.timers:
                    self.timers.remove(self.gif_timer)
                del self.gif_timer

            # 기존 QMovie 정리
            if hasattr(self, 'current_movie') and self.current_movie:
                self.current_movie.stop()
                self.current_movie.deleteLater()  # Qt 객체 명시적 삭제 요청
                del self.current_movie

            self.current_movie = QMovie(image_path)
            self.current_movie.setCacheMode(QMovie.CacheAll)
            self.current_movie.jumpToFrame(0)
            
            # 현재 회전 각도가 0이 아니면 회전 적용
            if hasattr(self, 'current_rotation') and self.current_rotation != 0:
                # 회전을 위한 변환 행렬 설정
                transform = QTransform().rotate(self.current_rotation)
                
                # 프레임 변경 시 회전을 적용하는 함수 연결
                def frame_changed(frame_number):
                    if not hasattr(self, 'image_label') or not self.image_label:
                        return
                        
                    # 현재 프레임 가져오기
                    current_pixmap = self.current_movie.currentPixmap()
                    if current_pixmap and not current_pixmap.isNull():
                        # 프레임 회전
                        rotated_pixmap = current_pixmap.transformed(transform, Qt.SmoothTransformation)
                        
                        # 화면에 맞게 크기 조절
                        label_size = self.image_label.size()
                        scaled_pixmap = rotated_pixmap.scaled(
                            label_size,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        
                        # 이미지 라벨에 표시
                        self.image_label.setPixmap(scaled_pixmap)
                
                # 프레임 변경 이벤트에 회전 함수 연결
                self.current_movie.frameChanged.connect(frame_changed)
                self.current_movie.start()
                print(f"GIF에 회전 적용됨: {self.current_rotation}°")
            else:
                # 회전이 없는 경우 일반적인 처리
                self.scale_gif()
                self.image_label.setMovie(self.current_movie)
                self.current_movie.start()

            # 슬라이더 범위를 gif의 프레임 수에 맞게 설정
            frame_count = self.current_movie.frameCount()
            if frame_count > 1:  # 프레임이 2개 이상일 때만 애니메이션으로 처리
                self.playback_slider.setRange(0, frame_count - 1)
                self.playback_slider.setValue(0)

                # 슬라이더 시그널 연결 전에 기존 연결 해제
                self.disconnect_all_slider_signals()
                
                # 슬라이더의 시그널 연결
                self.playback_slider.valueChanged.connect(self.seek_animation)  # 슬라이더와 연결
                self.playback_slider.sliderPressed.connect(self.slider_pressed)  # 드래그 시작 시 호출
                self.playback_slider.sliderReleased.connect(self.slider_released)  # 드래그 종료 시 호출
                self.playback_slider.clicked.connect(self.slider_clicked)  # 클릭 시 호출

                # gif의 프레임이 변경될 때마다 슬라이더 값을 업데이트
                def update_slider():
                    if hasattr(self, 'current_movie') and self.current_movie:
                        current_frame = self.current_movie.currentFrameNumber()
                        if self.current_movie.state() == QMovie.Running:
                            self.playback_slider.setValue(current_frame)
                            # 현재 프레임 / 총 프레임 표시 업데이트
                            self.time_label.setText(f"{current_frame + 1} / {self.current_movie.frameCount()}")

                # GIF 애니메이션 프레임 레이트에 맞춰 타이머 간격 설정
                try:
                    # 총 프레임 수와 애니메이션 속도 가져오기
                    frame_count = self.current_movie.frameCount()
                    animation_speed = self.current_movie.speed()  # 기본 속도는 100%
                    
                    # 프레임 지연 시간 계산 (근사값)
                    # GIF는 각 프레임마다 지연 시간이 다를 수 있지만, 평균으로 계산
                    reader = QImageReader(image_path)
                    if reader.supportsAnimation() and frame_count > 0:
                        # 첫 프레임 지연 시간 (밀리초)
                        delay = reader.nextImageDelay()
                        if delay <= 0:  # 유효하지 않은 경우 기본값 사용
                            delay = 100  # 기본값 100ms (약 10fps)
                    else:
                        delay = 100  # 정보를 얻을 수 없는 경우 기본값
                    
                    # 애니메이션 속도를 고려하여 지연 시간 조정
                    # 속도가 100%보다 빠르면 지연 시간이 줄어듦
                    timer_interval = int(delay * (100 / animation_speed))
                    
                    # 타이머 간격 범위 제한 (최소 10ms, 최대 200ms)
                    timer_interval = max(10, min(timer_interval, 200))
                except Exception as e:
                    print(f"GIF 프레임 레이트 계산 오류: {e}")
                    timer_interval = 50  # 오류 발생 시 기본값 (50ms)

                # 타이머를 사용하여 슬라이더 업데이트
                self.gif_timer = QTimer(self)
                self.gif_timer.timeout.connect(update_slider)
                self.gif_timer.start(timer_interval)  # 계산된 타이머 간격 사용
                self.timers.append(self.gif_timer)  # 타이머 추적에 추가

                # 애니메이션 재생 시작
                self.current_movie.start()  # 애니메이션 시작
                self.current_movie.setPaused(False)  # 일시정지 상태 해제
                # 재생 버튼 상태 업데이트
                self.play_button.setText("❚❚")  # 일시정지 아이콘 표시 (재생 중)
            else:
                # 프레임이 1개 이하일 경우 일반 이미지로 처리
                image = QImage(image_path)  # 이미지 로드
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)  # QImage를 QPixmap으로 변환
                    # 화면 크기에 맞게 이미지 조정 (비율 유지, 고품질 보간)
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.width(),
                        self.image_label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)  # 이미지 표시

                # 슬라이더 초기화 (단일 프레임 이미지인 경우)
                self.playback_slider.setRange(0, 0)  # 범위 초기화
                self.playback_slider.setValue(0)  # 값 초기화
                self.time_label.setText("00:00 / 00:00")  # 시간 표시 초기화
                self.time_label.show()  # 시간 레이블 표시
        else:
            # 일반 GIF 이미지 처리
            image = QImage(image_path)  # 이미지 로드
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)  # QImage를 QPixmap으로 변환
                # 화면 크기에 맞게 이미지 조정 (비율 유지, 고품질 보간)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.width(),
                    self.image_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)  # 이미지 표시

            # 슬라이더 초기화 (정적 이미지인 경우)
            self.playback_slider.setRange(0, 0)  # 범위 초기화
            self.playback_slider.setValue(0)  # 값 초기화
            self.time_label.setText("00:00 / 00:00")  # 시간 표시 초기화
            self.time_label.show()  # 시간 레이블 표시

    def show_webp(self, image_path):
        # WEBP 애니메이션을 처리하기 위해 QImageReader를 사용
        reader = QImageReader(image_path)

        # FormatDetector로 이미 타입이 결정되었는지 확인
        # (show_image 메서드에서 FormatDetector 사용 시)
        if self.current_media_type != 'webp_image' and self.current_media_type != 'webp_animation':
            # 아직 타입이 설정되지 않은 경우 직접 결정
            if reader.supportsAnimation():
                # 프레임 수를 확인하여 1개 이상이면 애니메이션으로 간주
                frame_count = reader.imageCount()
                if frame_count > 1:
                    self.current_media_type = 'webp_animation'
                else:
                    self.current_media_type = 'webp_image'
            else:
                self.current_media_type = 'webp_image'

        # 애니메이션 WEBP 처리
        if self.current_media_type == 'webp_animation':
            # 기존 타이머 정지 및 관리
            if hasattr(self, 'gif_timer'):
                self.gif_timer.stop()
                if self.gif_timer in self.timers:
                    self.timers.remove(self.gif_timer)
                del self.gif_timer

            # 기존 QMovie 정리
            if hasattr(self, 'current_movie') and self.current_movie:
                self.current_movie.stop()
                self.current_movie.deleteLater()  # Qt 객체 명시적 삭제 요청
                del self.current_movie

            self.current_movie = QMovie(image_path)
            self.current_movie.setCacheMode(QMovie.CacheAll)
            self.current_movie.jumpToFrame(0)
            
            # 현재 회전 각도가 0이 아니면 회전 적용
            if hasattr(self, 'current_rotation') and self.current_rotation != 0:
                # 회전을 위한 변환 행렬 설정
                transform = QTransform().rotate(self.current_rotation)
                
                # 프레임 변경 시 회전을 적용하는 함수 연결
                def frame_changed(frame_number):
                    if not hasattr(self, 'image_label') or not self.image_label:
                        return
                        
                    # 현재 프레임 가져오기
                    current_pixmap = self.current_movie.currentPixmap()
                    if current_pixmap and not current_pixmap.isNull():
                        # 프레임 회전
                        rotated_pixmap = current_pixmap.transformed(transform, Qt.SmoothTransformation)
                        
                        # 화면에 맞게 크기 조절
                        label_size = self.image_label.size()
                        scaled_pixmap = rotated_pixmap.scaled(
                            label_size,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        
                        # 이미지 라벨에 표시
                        self.image_label.setPixmap(scaled_pixmap)
                
                # 프레임 변경 이벤트에 회전 함수 연결
                self.current_movie.frameChanged.connect(frame_changed)
                self.current_movie.start()
                print(f"WEBP에 회전 적용됨: {self.current_rotation}°")
            else:
                # 회전이 없는 경우 일반적인 처리
                self.scale_webp()
                self.image_label.setMovie(self.current_movie)
                self.current_movie.start()

            # 슬라이더 범위를 WEBP의 프레임 수에 맞게 설정
            frame_count = self.current_movie.frameCount()
            if frame_count > 1:  # 프레임이 2개 이상일 때만 애니메이션으로 처리
                self.playback_slider.setRange(0, frame_count - 1)
                self.playback_slider.setValue(0)
                
                # 슬라이더 시그널 연결 전에 기존 연결 해제
                self.disconnect_all_slider_signals()
                
                # 슬라이더의 시그널 연결
                self.playback_slider.valueChanged.connect(self.seek_animation)  # 슬라이더와 연결
                self.playback_slider.sliderPressed.connect(self.slider_pressed)  # 드래그 시작 시 호출
                self.playback_slider.sliderReleased.connect(self.slider_released)  # 드래그 종료 시 호출
                self.playback_slider.clicked.connect(self.slider_clicked)  # 클릭 시 호출

                # WebP 프레임 변경 시 슬라이더 업데이트 함수
                def update_slider():
                    if hasattr(self, 'current_movie') and self.current_movie:
                        current_frame = self.current_movie.currentFrameNumber()  # 현재 프레임 번호
                        if self.current_movie.state() == QMovie.Running:  # 애니메이션이 재생 중인 경우
                            self.playback_slider.setValue(current_frame)  # 슬라이더 위치 업데이트
                            # 프레임 정보 업데이트 (현재/총 프레임)
                            self.time_label.setText(f"{current_frame + 1} / {self.current_movie.frameCount()}")

                # 타이머를 사용하여 슬라이더 주기적 업데이트
                self.gif_timer = QTimer(self)
                self.gif_timer.timeout.connect(update_slider)  # 타이머 이벤트에 함수 연결
                
                # WEBP 애니메이션 프레임 레이트에 맞춰 타이머 간격 설정
                try:
                    # 총 프레임 수와 애니메이션 속도 가져오기
                    frame_count = self.current_movie.frameCount()
                    animation_speed = self.current_movie.speed()  # 기본 속도는 100%
                    
                    # 프레임 지연 시간 계산 (근사값)
                    reader = QImageReader(image_path)
                    if reader.supportsAnimation() and frame_count > 0:
                        # 첫 프레임 지연 시간 (밀리초)
                        delay = reader.nextImageDelay()
                        if delay <= 0:  # 유효하지 않은 경우 기본값 사용
                            delay = 100  # 기본값 100ms (약 10fps)
                    else:
                        delay = 100  # 정보를 얻을 수 없는 경우 기본값
                    
                    # 애니메이션 속도를 고려하여 지연 시간 조정
                    timer_interval = int(delay * (100 / animation_speed))
                    
                    # 타이머 간격 범위 제한 (최소 10ms, 최대 200ms)
                    timer_interval = max(10, min(timer_interval, 200))
                except Exception as e:
                    print(f"WEBP 프레임 레이트 계산 오류: {e}")
                    timer_interval = 50  # 오류 발생 시 기본값 (50ms)
                
                self.gif_timer.start(timer_interval)  # 계산된 타이머 간격 사용
                self.timers.append(self.gif_timer)  # 타이머 추적에 추가

                # 애니메이션 재생 시작
                self.current_movie.start()  # 애니메이션 시작
                self.current_movie.setPaused(False)  # 일시정지 상태 해제
                # 재생 버튼 상태 업데이트
                self.play_button.setText("❚❚")  # 일시정지 아이콘 표시 (재생 중)
            else:
                # 프레임이 1개 이하일 경우 일반 이미지로 처리
                self.current_media_type = 'image'  # 일반 이미지로 미디어 타입 변경
                image = QImage(image_path)  # 이미지 로드
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)  # QImage를 QPixmap으로 변환
                    
                    # 회전 각도가 0이 아니면 회전 적용
                    if hasattr(self, 'current_rotation') and self.current_rotation != 0:
                        # 회전 변환 적용
                        transform = QTransform().rotate(self.current_rotation)
                        pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                        print(f"단일 프레임 WEBP에 회전 적용됨: {self.current_rotation}°")
                    
                    # 화면 크기에 맞게 이미지 조정 (비율 유지, 고품질 보간)
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.width(),
                        self.image_label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)  # 이미지 표시

                # 슬라이더 초기화 (단일 프레임 이미지인 경우)
                self.playback_slider.setRange(0, 0)  # 범위 초기화
                self.playback_slider.setValue(0)  # 값 초기화
                self.time_label.setText("00:00 / 00:00")  # 시간 표시 초기화
                self.time_label.show()  # 시간 레이블 표시
        else:
            # 애니메이션을 지원하지 않는 일반 WebP 이미지 처리
            self.current_media_type = 'image'  # 일반 이미지로 미디어 타입 설정
            image = QImage(image_path)  # 이미지 로드
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)  # QImage를 QPixmap으로 변환
                
                # 회전 각도가 0이 아니면 회전 적용
                if hasattr(self, 'current_rotation') and self.current_rotation != 0:
                    # 회전 변환 적용
                    transform = QTransform().rotate(self.current_rotation)
                    pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                    print(f"일반 WEBP 이미지에 회전 적용됨: {self.current_rotation}°")
                
                # 화면 크기에 맞게 이미지 조정 (비율 유지, 고품질 보간)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.width(),
                    self.image_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)  # 이미지 표시

            # 슬라이더 초기화 (정적 이미지인 경우)
            self.playback_slider.setRange(0, 0)  # 범위 초기화
            self.playback_slider.setValue(0)  # 값 초기화
            self.time_label.setText("00:00 / 00:00")  # 시간 표시 초기화
            self.time_label.show()  # 시간 레이블 표시

    def scale_webp(self):
        """WEBP 애니메이션 크기 조정"""
        # current_movie 속성이 있는지 확인
        if not hasattr(self, 'current_movie') or self.current_movie is None:
            return
            
        try:
            # 현재 프레임 번호 저장
            current_frame = self.current_movie.currentFrameNumber()
            
            # 원본 크기와 표시 영역 크기 정보
            original_size = QSize(self.current_movie.currentImage().width(), self.current_movie.currentImage().height())
            label_size = self.image_label.size()
            
            # 높이가 0인 경우 예외 처리 (0으로 나누기 방지)
            if original_size.height() == 0:
                original_size.setHeight(1)
                
            # 화면 비율에 맞게 새 크기 계산
            if label_size.width() / label_size.height() > original_size.width() / original_size.height():
                # 세로 맞춤 (세로 기준으로 가로 계산)
                new_height = label_size.height()
                new_width = int(new_height * (original_size.width() / original_size.height()))
            else:
                # 가로 맞춤 (가로 기준으로 세로 계산)
                new_width = label_size.width()
                new_height = int(new_width * (original_size.height() / original_size.width()))
            
            # 애니메이션 크기 조정 및 원래 프레임으로 복원
            self.current_movie.setScaledSize(QSize(new_width, new_height))
            self.current_movie.jumpToFrame(current_frame)
        except Exception as e:
            print(f"WEBP 크기 조정 중 오류 발생: {e}")

    def scale_gif(self):
        """GIF 애니메이션 크기 조정"""
        # current_movie 속성이 있는지 확인
        if not hasattr(self, 'current_movie') or self.current_movie is None:
            return
            
        try:
            # 현재 프레임 번호 저장
            current_frame = self.current_movie.currentFrameNumber()
            
            # 원본 크기와 표시 영역 크기 정보
            original_size = QSize(self.current_movie.currentImage().width(), self.current_movie.currentImage().height())
            label_size = self.image_label.size()
            
            # 높이가 0인 경우 예외 처리 (0으로 나누기 방지)
            if original_size.height() == 0:
                original_size.setHeight(1)
                
            # 화면 비율에 맞게 새 크기 계산
            if label_size.width() / label_size.height() > original_size.width() / original_size.height():
                # 세로 맞춤 (세로 기준으로 가로 계산)
                new_height = label_size.height()
                new_width = int(new_height * (original_size.width() / original_size.height()))
            else:
                # 가로 맞춤 (가로 기준으로 세로 계산)
                new_width = label_size.width()
                new_height = int(new_width * (original_size.height() / original_size.width()))
            
            # 애니메이션 크기 조정 및 원래 프레임으로 복원
            self.current_movie.setScaledSize(QSize(new_width, new_height))
            self.current_movie.jumpToFrame(current_frame)
        except Exception as e:
            print(f"GIF 크기 조정 중 오류 발생: {e}")

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
            self.play_button.setText("❚❚")  # 재생 중이므로 일시정지 아이콘 표시
            
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
        """슬라이더를 클릭했을 때 호출됩니다."""
        # 애니메이션 처리
        if hasattr(self, 'current_movie') and self.current_movie:
            try:
                # 유효한 프레임 번호인지 확인
                max_frame = self.current_movie.frameCount() - 1
                frame = min(max(0, value), max_frame)  # 범위 내로 제한
                self.current_movie.jumpToFrame(frame)
                return
            except Exception as e:
                pass  # 예외 발생 시 무시
        
        # 비디오 처리
        if self.current_media_type == 'video':
            try:
                # 클릭한 위치의 값을 초 단위로 변환
                seconds = value / 1000.0  # 밀리초를 초 단위로 변환
                # VideoHandler의 seek 함수를 사용하여 정확한 위치로 이동
                self.video_handler.seek(seconds)
            except Exception as e:
                print(f"비디오 Seek 오류: {e}")  # 오류 내용 출력
                pass  # 예외 발생 시 무시
                
        # 슬라이더 클릭 후 약간의 지연을 두고 창에 포커스를 돌려줌
        QTimer.singleShot(50, self.setFocus)

    def slider_pressed(self):
        """슬라이더를 드래그하기 시작할 때 호출됩니다."""
        self.is_slider_dragging = True

    def slider_released(self):
        """슬라이더 드래그가 끝날 때 호출됩니다."""
        self.is_slider_dragging = False
        
        # 애니메이션 처리
        if hasattr(self, 'current_movie') and self.current_movie:
            try:
                value = self.playback_slider.value()
                # 유효한 프레임 번호인지 확인
                max_frame = self.current_movie.frameCount() - 1
                frame = min(max(0, value), max_frame)  # 범위 내로 제한
                self.current_movie.jumpToFrame(frame)
            except Exception as e:
                print(f"애니메이션 Seek 오류: {e}")  # 오류 내용 출력
                pass  # 예외 발생 시 무시
                
        # 비디오 처리
        elif self.current_media_type == 'video':
            try:
                seconds = self.playback_slider.value() / 1000.0  # 밀리초를 초 단위로 변환
                self.video_handler.seek(seconds)  # VideoHandler의 seek 함수 사용
            except Exception as e:
                print(f"비디오 Seek 오류: {e}")  # 오류 내용 출력
                pass  # 예외 발생 시 무시
                
        # 슬라이더 조작 후 약간의 지연을 두고 창에 포커스를 돌려줌
        QTimer.singleShot(50, self.setFocus)

    def seek_video(self, value):
        """슬라이더 값에 따라 비디오 재생 위치를 변경합니다."""
        if self.is_slider_dragging:
            # 슬라이더 값을 초 단위로 변환 (value는 밀리초 단위)
            seconds = value / 1000.0  # 밀리초를 초 단위로 변환
            # VideoHandler의 seek 함수를 사용하여 정확한 위치로 이동
            self.video_handler.seek(seconds)

    def seek_animation(self, value):
        """슬라이더 값에 따라 애니메이션 재생 위치를 변경합니다."""
        if hasattr(self, 'current_movie'):
            # 슬라이더 값을 프레임 번호로 변환
            frame = value
            # 애니메이션이 재생 중일 경우 해당 프레임으로 점프
            self.current_movie.jumpToFrame(frame)

    def update_video_playback(self):
        """VideoHandler를 사용하여 비디오의 재생 위치에 따라 슬라이더 값을 업데이트합니다."""
        if not self.is_slider_dragging:
            try:
                position = self.video_handler.get_position()  # 현재 재생 위치
                duration = self.video_handler.get_duration()  # 총 길이
                
                # 재생 위치 값이 None인 경우 처리
                if position is None:
                    return  # 슬라이더 업데이트를 건너뜁니다.

                # 슬라이더 범위 설정
                if duration is not None and duration > 0:
                    # 슬라이더 범위를 밀리초 단위로 설정 (1000으로 곱해서 더 세밀하게)
                    self.playback_slider.setRange(0, int(duration * 1000))
                    
                    # 현재 위치가 duration을 초과하면 0으로 리셋
                    if position >= duration:
                        self.playback_slider.setValue(0)
                        self.video_handler.seek(0)
                    else:
                        # 슬라이더 값을 밀리초 단위로 설정 (1000으로 곱해서 더 세밀하게)
                        self.playback_slider.setValue(int(position * 1000))
                    
                    self.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

                self.previous_position = position  # 현재 위치를 이전 위치로 저장

            except Exception as e:
                print(f"비디오 업데이트 에러: {e}")
                self.video_timer.stop()  # 타이머 중지

    def format_time(self, seconds):
        """초를 'MM:SS' 형식으로 변환합니다."""
        # core.utils 모듈의 format_time 함수를 사용합니다
        return format_time(seconds)

    def update_play_button(self):
        """재생 상태에 따라 버튼 텍스트 업데이트"""
        # 미디어 타입에 따른 버튼 텍스트 업데이트
        if hasattr(self, 'current_movie') and self.current_movie:
            # 애니메이션(GIF, WEBP) 재생 상태 확인
            if self.current_movie.state() == QMovie.Running:
                self.play_button.setText("❚❚")  # 일시정지 아이콘
            else:
                self.play_button.setText("▶")  # 재생 아이콘
        elif self.current_media_type == 'video':
            # 비디오 재생 상태 확인
            try:
                is_playing = self.video_handler.is_video_playing()
                self.play_button.setText("❚❚" if is_playing else "▶")
                self.update_video_playback()  # 슬라이더 업데이트 호출
            except Exception as e:
                print(f"재생 버튼 업데이트 오류: {e}")
                self.play_button.setEnabled(False)  # 버튼 비활성화

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
        if self.image_files:
            image_info = f"{self.current_index + 1} / {len(self.image_files)}"
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
        
        # 이미지 컨테이너 레이아웃 강제 업데이트
        if hasattr(self, 'image_container'):
            self.image_container.updateGeometry()

    # 다음 이미지를 보여주는 메서드입니다.
    def show_next_image(self):
        if self.image_files:
            if self.current_index == len(self.image_files) - 1:  # 마지막 이미지인 경우
                # 메시지 표시
                self.show_message("마지막 이미지입니다.")
                return
            self.current_index += 1  # 다음 이미지로 이동
            self.show_image(self.image_files[self.current_index])

    # 이전 이미지를 보여주는 메서드입니다.
    def show_previous_image(self):
        if self.image_files:
            if self.current_index == 0:  # 첫 번째 이미지인 경우
                # 메시지 표시
                self.show_message("첫 번째 이미지입니다.")
                return
            self.current_index -= 1  # 이전 이미지로 이동
            self.show_image(self.image_files[self.current_index])

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
        
        QTimer.singleShot(2000, self.message_label.close)

    # 현재 이미지를 다른 폴더로 복사하는 메서드입니다.
    def copy_image_to_folder(self, folder_path):
        # 현재 이미지 경로가 존재하고, 폴더 경로도 제공되었으면 복사를 시작합니다.
        if self.current_image_path and folder_path:
            try:
                # 이미지 복사할 대상 경로를 생성합니다.
                target_path = self.get_unique_file_path(folder_path, self.current_image_path)  # 고유한 파일 경로 생성

                # 이미지 파일을 복사합니다.
                shutil.copy2(self.current_image_path, target_path)  # 파일 복사 (메타데이터도 함께 복사)
                print(f"Copied: {self.current_image_path} -> {target_path}")  # 복사된 경로 출력

                # 전체 경로가 너무 길 경우 축약
                path_display = target_path
                if len(path_display) > 60:  # 경로가 60자 이상인 경우
                    # 드라이브와 마지막 2개 폴더만 표시
                    drive, tail = os.path.splitdrive(path_display)
                    parts = tail.split(os.sep)
                    if len(parts) > 2:
                        # 드라이브 + '...' + 마지막 2개 폴더
                        path_display = f"{drive}{os.sep}...{os.sep}{os.sep.join(parts[-2:])}"
                
                # 새로운 메시지 형식으로 표시
                self.show_message(f"{path_display} 으로 이미지 복사")

                # 이미지 복사 후 자동으로 다음 이미지로 이동합니다.
                self.show_next_image()  # 복사 후 다음 이미지 표시
            except Exception as e:
                pass  # 에러 발생 시 출력

    # 고유한 파일 경로를 생성하는 메서드입니다.
    def get_unique_file_path(self, folder_path, image_path):
        # 파일 이름이 중복되지 않도록 새로운 파일 이름을 생성합니다.
        base_name = os.path.basename(image_path)  # 이미지 파일의 기본 이름을 추출
        name, ext = os.path.splitext(base_name)  # 파일 이름과 확장자를 분리

        # 파일 이름에 '(숫자)' 형식이 있으면 이를 제거합니다.
        name = re.sub(r'\s?\(\d+\)', '', name)  # '(숫자)' 패턴을 제거하여 중복을 방지

        # 폴더 경로와 새 파일 경로를 결합하여 대상 경로 생성
        target_path = os.path.join(folder_path, f"{name}{ext}")

        # 파일 이름이 이미 존재하면 숫자를 추가하여 새로운 이름을 만듭니다.
        counter = 1
        while os.path.exists(target_path):  # 경로가 존재하면
            target_path = os.path.join(folder_path, f"{name} ({counter}){ext}")  # 파일 이름 뒤에 숫자를 추가하여 경로 생성
            counter += 1  # 숫자 증가

        return target_path  # 고유한 파일 경로 반환

    def keyPressEvent(self, event):
            # ESC 키로 전체화면 모드 종료
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
            return  # ESC 키 처리 완료
        
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
        # ESC 키로 전체화면 모드 종료
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
            return
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
        current_time = time.time() * 1000  # 현재 시간(밀리초)
        
        # 기본 쿨다운 값 설정 (일반적인 경우 500ms)
        cooldown_ms = 500
        
        # 쿨다운 체크 - 상수 시간 연산 O(1)
        if current_time - self.last_wheel_time < cooldown_ms:
            event.accept()  # 이벤트 처리됨으로 표시하고 무시
            return
        
        # 방향 체크 후 이미지 전환
        if event.angleDelta().y() > 0:
            self.show_previous_image()
        elif event.angleDelta().y() < 0:
            self.show_next_image()
        
        self.last_wheel_time = current_time  # 마지막 처리 시간 업데이트

    def eventFilter(self, obj, event):
        """모든 마우스 이벤트를 필터링"""
        if event.type() == QEvent.MouseMove:
            global_pos = event.globalPos()
            local_pos = self.mapFromGlobal(global_pos)
            
            # 변수를 조건문 외부에서 정의 (이 부분이 중요합니다)
            title_bar_area_height = 50  # 마우스가 상단 50px 이내일 때 타이틀바 표시
            bottom_area_height = 250  # 마우스가 하단 250px 이내일 때 컨트롤 표시

                
            # UI 상태 변경 여부를 추적하기 위한 변수
            ui_state_changed = False
            title_bar_changed = False
            slider_changed = False
            buttons_changed = False

            # UI가 고정된 상태인지 확인
            title_ui_locked = hasattr(self, 'is_title_ui_locked') and self.is_title_ui_locked
            bottom_ui_locked = hasattr(self, 'is_bottom_ui_locked') and self.is_bottom_ui_locked

            # 상단 영역에 있을 때 타이틀바 표시 (타이틀바 UI가 잠겨있지 않은 경우만)
            if not title_ui_locked:
                if local_pos.y() <= title_bar_area_height:
                    if hasattr(self, 'title_bar') and self.title_bar.isHidden():
                        self.title_bar.show()
                        title_bar_changed = True
                else:
                    # 상단 영역을 벗어나면 타이틀바 숨김
                    if hasattr(self, 'title_bar') and not self.title_bar.isHidden():
                        self.title_bar.hide()
                        title_bar_changed = True

            # 하단 영역에 있을 때 슬라이더와 버튼 표시 (하단 UI가 잠겨있지 않은 경우만)
            if not bottom_ui_locked:
                if local_pos.y() >= self.height() - bottom_area_height:
                    if hasattr(self, 'slider_widget') and self.slider_widget.isHidden():
                        self.slider_widget.show()
                        slider_changed = True
                    
                    # 폴더 버튼 표시 설정
                    for row in self.buttons:
                        for button in row:
                            if button.isHidden():
                                button.show()
                                buttons_changed = True
                else:
                    # 하단 영역을 벗어나면 슬라이더와 버튼 숨김
                    if hasattr(self, 'slider_widget') and not self.slider_widget.isHidden():
                        self.slider_widget.hide()
                        slider_changed = True
                    
                    # 폴더 버튼 숨김 설정
                    for row in self.buttons:
                        for button in row:
                            if not button.isHidden():
                                button.hide()
                                buttons_changed = True
                
                # 모든 변경사항 처리 후 한 번만 UI 상태 변경 확인
                ui_state_changed = title_bar_changed or slider_changed or buttons_changed
                
                # UI 상태가 변경되었으면 이미지 크기 조정 (하단 UI 변경 시 지연 시간 증가)
                if ui_state_changed:
                    # 기존 타이머가 실행 중이면 중지
                    if self.ui_update_timer.isActive():
                        self.ui_update_timer.stop()
                    
                    # 하단 UI 변경이면 지연 시간 더 길게 설정
                    if slider_changed or buttons_changed:
                        delay = 150  # 하단 UI 변경 시 150ms 지연
                    else:
                        delay = 50   # 상단 UI만 변경 시 50ms 지연
                    
                    # 디버깅용 메시지
                    print(f"UI 업데이트 타이머 시작: {delay}ms 지연, 상단변경: {title_bar_changed}, 하단변경: {slider_changed or buttons_changed}")
                    
                    # 지연 시간 설정 후 타이머 시작
                    self.ui_update_timer.start(delay)
            
            # 창이 최대화 상태가 아닐 때만 크기 조절 가능
            if not self.isMaximized():
                # 리사이징 중이면 크기 조절 처리
                if self.resizing:
                    diff = event.globalPos() - self.resize_start_pos
                    new_geometry = self.resize_start_geometry.adjusted(0, 0, 0, 0)
                    
                    if self.resize_direction in ['left', 'top_left', 'bottom_left']:
                        new_geometry.setLeft(self.resize_start_geometry.left() + diff.x())
                    if self.resize_direction in ['right', 'top_right', 'bottom_right']:
                        new_geometry.setRight(self.resize_start_geometry.right() + diff.x())
                    if self.resize_direction in ['top', 'top_left', 'top_right']:
                        new_geometry.setTop(self.resize_start_geometry.top() + diff.y())
                    if self.resize_direction in ['bottom', 'bottom_left', 'bottom_right']:
                        new_geometry.setBottom(self.resize_start_geometry.bottom() + diff.y())
                    
                    # 최소 크기 제한
                    if new_geometry.width() >= 400 and new_geometry.height() >= 300:
                        self.setGeometry(new_geometry)
                    return True

                # 제목 표시줄 드래그 중이면 창 이동
                elif hasattr(self, 'drag_start_pos') and event.buttons() == Qt.LeftButton:
                    if self.isMaximized():
                        # 최대화 상태에서 드래그하면 일반 크기로 복원
                        cursor_x = event.globalPos().x()
                        window_width = self.width()
                        ratio = cursor_x / window_width
                        self.showNormal()
                        # 마우스 위치 비율에 따라 창 위치 조정
                        new_x = int(event.globalPos().x() - (self.width() * ratio))
                        self.move(new_x, 0)
                        self.drag_start_pos = event.globalPos()
                    else:
                        # 창 이동
                        self.move(event.globalPos() - self.drag_start_pos)
                    return True
                
                # 리사이징 중이 아닐 때 커서 모양 변경
                edge_size = 4
                
                # 제목표시줄의 버튼 영역인지 확인
                is_in_titlebar = local_pos.y() <= 30
                
                # 버튼 영역 판단 수정 - 버튼 위젯 객체를 직접 확인
                is_in_titlebar_buttons = False
                if is_in_titlebar:
                    # 제목 표시줄의 모든 자식 버튼 검사
                    for child in self.title_bar.children():
                        if isinstance(child, QPushButton):
                            # 버튼의 전역 위치와 크기로 사각형 생성
                            button_pos = child.mapToGlobal(QPoint(0, 0))
                            button_rect = QRect(button_pos, child.size())
                            # 마우스 포인터가 버튼 위에 있는지 확인
                            if button_rect.contains(event.globalPos()):
                                is_in_titlebar_buttons = True
                                QApplication.setOverrideCursor(Qt.ArrowCursor)  # 버튼 위에서는 항상 화살표 커서
                                break
                
                # 마우스 커서 위치에 따른 크기 조절 방향 결정
                if not is_in_titlebar_buttons:  # 버튼 영역이 아닐 때만 리사이징 방향 결정
                    if local_pos.x() <= edge_size and local_pos.y() <= edge_size:
                        QApplication.setOverrideCursor(Qt.SizeFDiagCursor)
                        self.resize_direction = 'top_left'
                    elif local_pos.x() >= self.width() - edge_size and local_pos.y() <= edge_size:
                        QApplication.setOverrideCursor(Qt.SizeBDiagCursor)
                        self.resize_direction = 'top_right'
                    elif local_pos.x() <= edge_size and local_pos.y() >= self.height() - edge_size:
                        QApplication.setOverrideCursor(Qt.SizeBDiagCursor)
                        self.resize_direction = 'bottom_left'
                    elif local_pos.x() >= self.width() - edge_size and local_pos.y() >= self.height() - edge_size:
                        QApplication.setOverrideCursor(Qt.SizeFDiagCursor)
                        self.resize_direction = 'bottom_right'
                    elif local_pos.x() <= edge_size:
                        QApplication.setOverrideCursor(Qt.SizeHorCursor)
                        self.resize_direction = 'left'
                    elif local_pos.x() >= self.width() - edge_size:
                        QApplication.setOverrideCursor(Qt.SizeHorCursor)
                        self.resize_direction = 'right'
                    elif local_pos.y() <= edge_size:
                        QApplication.setOverrideCursor(Qt.SizeVerCursor)
                        self.resize_direction = 'top'
                    elif local_pos.y() >= self.height() - edge_size:
                        QApplication.setOverrideCursor(Qt.SizeVerCursor)
                        self.resize_direction = 'bottom'
                    else:
                        if is_in_titlebar and not is_in_titlebar_buttons:
                            QApplication.setOverrideCursor(Qt.ArrowCursor)
                            self.resize_direction = None
                        elif self.image_label.geometry().contains(local_pos) or \
                            any(button.geometry().contains(local_pos) for row in self.buttons for button in row):
                            QApplication.setOverrideCursor(Qt.ArrowCursor)
                            self.resize_direction = None
                        else:
                            QApplication.restoreOverrideCursor()
                            self.resize_direction = None
                else:
                    # 제목표시줄 버튼 영역에서는 기본 커서 사용
                    QApplication.setOverrideCursor(Qt.ArrowCursor)
                    self.resize_direction = None

        elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            local_pos = self.mapFromGlobal(event.globalPos())
            is_in_titlebar = local_pos.y() <= 30
            
            # 버튼 영역 판단 수정 - 버튼 위젯 객체를 직접 확인
            is_in_titlebar_buttons = False
            if is_in_titlebar:
                # 제목 표시줄의 모든 자식 버튼 검사
                for child in self.title_bar.children():
                    if isinstance(child, QPushButton):
                        button_pos = child.mapToGlobal(QPoint(0, 0))
                        button_rect = QRect(button_pos, child.size())
                        if button_rect.contains(event.globalPos()):
                            is_in_titlebar_buttons = True
                            return False  # 버튼 클릭은 이벤트 필터에서 처리하지 않고 버튼에게 전달
            
            if self.resize_direction and not self.isMaximized() and not is_in_titlebar_buttons:
                # 리사이징 시작
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                return True
            elif is_in_titlebar and not is_in_titlebar_buttons:
                # 제목 표시줄 드래그 시작
                self.drag_start_pos = event.globalPos() - self.pos()
                # 제목 표시줄 드래그 시 창에 포커스 설정
                self.setFocus()
                return True
            return False

        elif event.type() == QEvent.MouseButtonRelease:
            # 리사이징 또는 드래그 종료
            was_resizing = self.resizing
            if self.resizing:
                self.resizing = False
                QApplication.restoreOverrideCursor()
            if hasattr(self, 'drag_start_pos'):
                delattr(self, 'drag_start_pos')
            
            # 버튼이나 슬라이더 조작 후에 창 전체에 포커스 설정
            QTimer.singleShot(10, self.setFocus)
            
            return was_resizing

        # 애플리케이션 활성화/비활성화 상태 처리
        elif event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:  # 창이 최소화되었을 때
                self.pause_all_timers()
            elif event.oldState() & Qt.WindowMinimized:  # 창이 최소화 상태에서 복구되었을 때
                self.resume_all_timers()
                
        # 창 활성화/비활성화 처리
        elif event.type() == QEvent.WindowActivate:  # 창이 활성화될 때
            self.resume_all_timers()
        elif event.type() == QEvent.WindowDeactivate:  # 창이 비활성화될 때
            self.pause_all_timers()

        return super().eventFilter(obj, event)

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
        """창이 닫힐 때 호출되는 이벤트, 리소스 정리를 수행합니다."""
        # 비디오 정지 및 플레이어 종료
        self.stop_video()
        
        # 로더 스레드 종료
        for path, loader in list(self.loader_threads.items()):
            if loader.isRunning():
                try:
                    loader.terminate()
                    loader.wait(300)  # 최대 300ms까지만 대기 (무한 대기 방지)
                except Exception as e:
                    print(f"스레드 종료 오류: {e}")
        self.loader_threads.clear()
        
        # VideoHandler 정리
        if hasattr(self, 'video_handler') and self.video_handler:
            try:
                self.video_handler.unload()  # VideoHandler의 unload 메서드 호출
            except Exception as e:
                print(f"비디오 핸들러 정리 오류: {e}")
        
        # 미디어 핸들러 정리
        if hasattr(self, 'image_handler'):
            self.image_handler.unload()
            
        if hasattr(self, 'psd_handler'):
            self.psd_handler.unload()
        
        # 캐시 정리
        if hasattr(self, 'image_cache'):
            self.image_cache.clear()
        if hasattr(self, 'psd_cache'):
            self.psd_cache.clear()
        if hasattr(self, 'gif_cache'):
            self.gif_cache.clear()
            
        # QMovie 정리
        if hasattr(self, 'current_movie') and self.current_movie:
            try:
                self.current_movie.stop()
                self.current_movie.deleteLater()
                self.current_movie = None
            except Exception as e:
                print(f"QMovie 정리 오류: {e}")
        
        # 타이머 정리
        for timer in list(self.timers):
            try:
                if timer.isActive():
                    timer.stop()
            except Exception as e:
                print(f"타이머 정리 오류: {e}")
        self.timers.clear()  # 타이머 목록 비우기
                
        # 책갈피 저장
        self.save_bookmarks()
        
        # 이벤트 처리 계속 (창 닫기)
        event.accept()

    def toggle_mute(self):
        """음소거 상태를 토글합니다."""
        try:
            # VideoHandler의 toggle_mute 메서드 사용
            is_muted = self.video_handler.toggle_mute()
            
            # 버튼 아이콘 변경 (음소거 상태에 따라)
            if is_muted:  # 토글 후 상태
                self.mute_button.setText("🔇")  # 음소거 상태 아이콘 (소리 없음)
            else:
                self.mute_button.setText("🔈")  # 음소거 해제 상태 아이콘 (소리 있음)
        except Exception as e:
            print(f"음소거 토글 오류: {e}")
            pass

    def adjust_volume(self, volume):
        """음량을 조절합니다."""
        try:
            # 현재 슬라이더 값을 가져와서 볼륨을 설정
            volume_value = self.volume_slider.value()  # 슬라이더의 현재 값
            # VideoHandler의 set_volume 메서드 사용
            self.video_handler.set_volume(volume_value)
        except Exception as e:
            print(f"볼륨 조절 오류: {e}")
            pass

    def toggle_animation_playback(self):
        """애니메이션(GIF, WEBP) 또는 비디오 재생/일시정지 토글"""
        
        # 현재 열려있는 파일 확인
        if not self.current_image_path:
            return
            
        # 미디어 타입에 따라 처리
        if hasattr(self, 'current_movie') and self.current_movie:
            # GIF나 WEBP 애니메이션 처리
            is_paused = self.current_movie.state() != QMovie.Running
            self.current_movie.setPaused(not is_paused)  # 상태 토글
            self.play_button.setText("▶" if not is_paused else "❚❚")  # 토글된 상태에 따라 아이콘 설정
                
        # 비디오 처리
        elif self.current_media_type == 'video':
            try:
                # VideoHandler를 사용하여 재생 상태 확인 및 토글
                is_playing = self.video_handler.is_video_playing()
                if is_playing:
                    self.video_handler.pause()  # 재생 중이면 일시정지
                else:
                    self.video_handler.play()  # 일시정지 중이면 재생
                # 버튼 상태 업데이트
                self.update_play_button()
            except Exception as e:
                print(f"비디오 재생/일시정지 토글 오류: {e}")
                pass  # 예외 발생 시 무시

    def toggle_bookmark(self):
        """현재 이미지의 북마크 상태를 토글합니다 (북마크 추가 또는 제거)"""
        # 북마크 매니저를 통해 토글 처리
        self.bookmark_manager.toggle_bookmark()

    def update_bookmark_menu(self):
        """북마크 메뉴를 업데이트합니다."""
        # 메서드 내용 전체 삭제
        # 함수 정의부터 다음 메서드가 시작되기 전까지 모두 삭제

    def load_bookmarked_image(self, path):
        """북마크된 이미지를 불러옵니다."""
        # 북마크 매니저를 통해 북마크된 이미지를 불러옵니다.
        self.bookmark_manager.load_bookmarked_image(path)

    def clear_bookmarks(self):
        """모든 북마크를 지웁니다."""
        # 북마크 매니저를 통해 모든 북마크를 지웁니다.
        self.bookmark_manager.clear_bookmarks()

    def update_bookmark_button_state(self):
        """북마크 버튼 상태 업데이트"""
        # 북마크 매니저의 메서드를 호출하여 북마크 버튼 상태를 업데이트
        self.bookmark_manager.update_bookmark_button_state()

        # 아래 직접 스타일을 설정하는 코드는 제거
        # if hasattr(self, 'current_image_path') and self.current_image_path and self.current_image_path in self.bookmark_manager.bookmarks:
        #     # 북마크된 상태
        #     self.slider_bookmark_btn.setStyleSheet("""
        #         QPushButton {
        #             background-color: rgba(241, 196, 15, 0.9);  /* 노란색 배경 */
        #             color: white;
        #             border: none;
        #             padding: 8px;
        #             border-radius: 3px;
        #             font-size: 12px;
        #         }
        #         QPushButton:hover {
        #             background-color: rgba(241, 196, 15, 1.0);  /* 호버 시 더 진한 노란색 */
        #         }
        #     """)
        # else:
        #     # 북마크되지 않은 상태 또는 이미지가 로드되지 않은 상태
        #     self.slider_bookmark_btn.setStyleSheet("""
        #         QPushButton {
        #             background-color: rgba(52, 73, 94, 0.6);  /* 일반 버튼과 동일한 색상 */
        #             color: white;
        #             border: none;
        #             padding: 8px;
        #             border-radius: 3px;
        #             font-size: 12px;
        #         }
        #         QPushButton:hover {
        #             background-color: rgba(52, 73, 94, 1.0);
        #         }
        #     """)

    def add_bookmark(self):
        """현재 이미지를 북마크에 추가합니다."""
        # 메서드 내용 전체 삭제

    def remove_bookmark(self):
      """현재 이미지를 북마크에서 제거합니다."""
       # 메서드 내용 전체 삭제

    def save_bookmarks(self):
       """북마크 정보를 JSON 파일로 저장합니다."""
       # 메서드 내용 전체 삭제
    
    def load_bookmarks(self):
       """JSON 파일에서 북마크 정보를 불러옵니다."""
       # 메서드 내용 전체 삭제

    def show_bookmark_menu_above(self):
        """북마크 메뉴를 버튼 위에 표시"""
        # BookmarkManager를 통해 북마크 메뉴를 버튼 위에 표시
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
        """하단 UI 요소 표시 상태를 고정/해제합니다."""
        self.is_bottom_ui_locked = not self.is_bottom_ui_locked
        # 이전 호환성을 위한 변수 업데이트
        self.is_ui_locked = self.is_bottom_ui_locked and self.is_title_ui_locked
        
        # UI 고정 버튼 상태 업데이트
        self.update_ui_lock_button_state()
        
        # UI 요소 표시/숨김 처리
        if self.is_bottom_ui_locked:
            # 하단 UI 요소 항상 표시
            if hasattr(self, 'slider_widget'):
                self.slider_widget.show()
            
            for row in self.buttons:
                for button in row:
                    button.show()
        
        # UI 변경 후 지연된 리사이징 적용
        QTimer.singleShot(150, self.delayed_resize)
        
        # 고정 상태 상태 메시지 표시
        if self.is_bottom_ui_locked:
            self.show_message("하단 UI가 고정되었습니다")
        else:
            self.show_message("하단 UI 고정이 해제되었습니다")

    def toggle_title_ui_lock(self):
        """상단 제목표시줄 표시 상태를 고정/해제합니다."""
        self.is_title_ui_locked = not self.is_title_ui_locked
        # 이전 호환성을 위한 변수 업데이트
        self.is_ui_locked = self.is_bottom_ui_locked and self.is_title_ui_locked
        
        # 제목표시줄 UI 고정 버튼 상태 업데이트
        self.update_title_lock_button_state()
        
        # UI 요소 표시/숨김 처리
        if self.is_title_ui_locked:
            # 상단 UI 항상 표시
            if hasattr(self, 'title_bar'):
                self.title_bar.show()
        
        # UI 변경 후 지연된 리사이징 적용
        QTimer.singleShot(150, self.delayed_resize)
        
        # 고정 상태 상태 메시지 표시
        if self.is_title_ui_locked:
            self.show_message("상단 UI가 고정되었습니다")
        else:
            self.show_message("상단 UI 고정이 해제되었습니다")

    def update_title_lock_button_state(self):
        """상단 제목표시줄 잠금 버튼의 상태를 현재 is_title_ui_locked 값에 맞게 업데이트"""
        if self.is_title_ui_locked:
            self.title_lock_btn.setText('🔒')  # 잠금 아이콘
        else:
            self.title_lock_btn.setText('🔓')  # 잠금 해제 아이콘

    def update_ui_lock_button_state(self):
        """UI 고정 버튼의 상태를 현재 is_bottom_ui_locked 값에 맞게 업데이트"""
        if self.is_bottom_ui_locked:
            self.ui_lock_btn.setText('🔒')  # 잠금 아이콘
            self.ui_lock_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(231, 76, 60, 0.9);  /* 빨간색 배경 */
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(231, 76, 60, 1.0);  /* 호버 시 더 진한 빨간색 */
                }
            """)
        else:
            self.ui_lock_btn.setText('🔓')  # 잠금 해제 아이콘
            self.ui_lock_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(52, 73, 94, 0.6);  /* 파란색 배경 */
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(52, 73, 94, 1.0);  /* 호버 시 더 진한 파란색 */
                }
            """)

    # 초기 및 resizeEvent에서 동적으로 호출되는 커스텀 UI 설정 메서드
    def setup_custom_ui(self):
        # 버튼 높이 측정 (open_button 기준)
        button_height = 50  # 실측으로 확인한 버튼 높이
        
        # 슬라이더 스타일 적용 (UI 일관성)
        self.playback_slider.setStyleSheet(self.slider_style)  # 재생 슬라이더 스타일 적용
        self.volume_slider.setStyleSheet(self.slider_style)  # 음량 조절 슬라이더 스타일 적용
        
        # 슬라이더를 버튼과 동일한 높이로 직접 설정
        self.playback_slider.setFixedHeight(button_height)  # 재생 슬라이더 높이 설정
        self.volume_slider.setFixedHeight(button_height)    # 볼륨 슬라이더 높이 설정
        
        # 슬라이더의 부모 위젯인 slider_widget에 배경 스타일을 적용
        self.slider_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        # 슬라이더 컨테이너에 대한 스타일 설정
        playback_container = self.playback_slider.parentWidget()
        volume_container = self.volume_slider.parentWidget()
        if playback_container:
            playback_container.setStyleSheet("""
                QWidget {
                    background-color: rgba(52, 73, 94, 0.6);
                    border-radius: 3px;
                }
                QWidget:hover {
                    background-color: rgba(52, 73, 94, 1.0);
                }
            """)
            
        if volume_container:
            volume_container.setStyleSheet("""
                QWidget {
                    background-color: rgba(52, 73, 94, 0.6);
                    border-radius: 3px;
                }
                QWidget:hover {
                    background-color: rgba(52, 73, 94, 1.0);
                }
            """)
        
        # 연결 추가 (이벤트와 함수 연결)
        self.volume_slider.valueChanged.connect(self.adjust_volume)  # 슬라이더 값 변경 시 음량 조절 메서드 연결 (볼륨 실시간 조절)

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
        for timer in self.timers:
            if timer.isActive():
                timer.stop()

    def resume_all_timers(self):
        for timer in self.timers:
            if not timer.isActive():
                timer.start()

    def rotate_image(self, clockwise=True):
        """이미지를 90도 회전합니다."""
        if not self.current_image_path:
            return
            
        # 회전 각도 계산 (시계/반시계 방향)
        rotation_delta = 90 if clockwise else -90
        self.current_rotation = (self.current_rotation + rotation_delta) % 360
        
        # 현재 미디어 타입에 따라 다르게 처리
        if self.current_media_type == 'image':
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
                # WEBP 일반 이미지 
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
                print(f"WEBP 일반 이미지 회전 즉시 적용: {self.current_rotation}°")
        elif self.current_media_type in ['gif_animation', 'webp_animation']:
            # 애니메이션 회전을 위한 더 안전한 방법 구현
            try:
                if hasattr(self, 'current_movie') and self.current_movie:
                    # 현재 재생 상태 및 프레임 기억
                    was_playing = self.current_movie.state() == QMovie.Running
                    current_frame = self.current_movie.currentFrameNumber()
                    
                    # 재로드 방식으로 처리
                    if self.current_media_type == 'gif_animation':
                        self.show_gif(self.current_image_path)
                    else:  # webp 또는 webp_animation
                        self.show_webp(self.current_image_path)
                        
                    # 프레임 복원 시도
                    if self.current_movie and current_frame < self.current_movie.frameCount():
                        self.current_movie.jumpToFrame(current_frame)
                        
                    # 정지 상태였다면 유지
                    if not was_playing and self.current_movie:
                        self.current_movie.setPaused(True)
                        
            except Exception as e:
                self.show_message(f"애니메이션 회전 중 오류 발생: {str(e)}")
                # 오류 발생 시 원본 이미지 다시 로드
                if self.current_media_type == 'gif_animation':
                    self.show_gif(self.current_image_path)
                else:
                    self.show_webp(self.current_image_path)
                return
        
        elif self.current_media_type == 'video':
            # 비디오 회전 처리
            try:
                # 기존 코드 교체: self.player 대신 video_handler 사용
                if hasattr(self, 'video_handler') and self.video_handler:
                    # 비디오 핸들러의 rotate 메서드 호출
                    self.video_handler.rotate(self.current_rotation)
            except Exception as e:
                self.show_message(f"비디오 회전 중 오류 발생: {str(e)}")
                return
        
        # 회전 상태 메시지 표시
        if self.current_media_type == 'video':
            self.show_message(f"비디오 회전: {self.current_rotation}°")
        elif self.current_media_type in ['gif_animation', 'webp_animation']:
            self.show_message(f"애니메이션 회전: {self.current_rotation}°")
        else:
            self.show_message(f"이미지 회전: {self.current_rotation}°")

    def update_button_sizes(self):
        # 창 너비 가져오기
        total_width = self.width()
        
        # 1. 폴더 버튼 행 처리
        if hasattr(self, 'buttons'):
            # 각 행 위젯의 최대 너비를 현재 창 너비로 업데이트
            for row in self.buttons:
                row_widget = row[0].parent()  # 버튼의 부모 위젯(row_widget) 가져오기
                row_widget.setMaximumWidth(total_width)
                
                # 버튼 너비 계산
                button_width = total_width / 20
                
                # 각 버튼의 너비 설정
                for i, button in enumerate(row):
                    if i == 19:  # 마지막 버튼
                        remaining_width = total_width - (int(button_width) * 19)
                        button.setFixedWidth(remaining_width)
                    else:
                        button.setFixedWidth(int(button_width))
                
                # 레이아웃 업데이트
                row_widget.updateGeometry()
        
        # 2. 슬라이더바 컨트롤 처리 (통합 로직)
        if hasattr(self, 'slider_controls'):
            # 기본 버튼 크기 계산 (모든 컨트롤에 동일하게 적용)
            button_width = max(60, min(150, int(total_width * 0.08)))
            button_height = max(30, min(50, int(button_width * 0.6)))
            
            # 모든 슬라이더 컨트롤에 동일한 로직 적용
            for control in self.slider_controls:
                # 시간 레이블은 너비만 다르게 설정 (내용이 더 길기 때문)
                if control == self.time_label:
                    control_width = int(button_width * 1.5)  # 시간 레이블은 1.5배 넓게
                else:
                    control_width = button_width
                
                # 크기 설정
                control.setFixedSize(control_width, button_height)
                
                # 폰트 크기 계산 (모든 컨트롤에 동일한 로직 적용)
                font_size = max(9, min(14, int(button_width * 0.25)))
                
                # 북마크 버튼은 특별하게 처리: update_bookmark_button_state 함수에서 색상 처리
                if control == self.slider_bookmark_btn:
                    # 크기만 설정하고 스타일은 건드리지 않음 (북마크 상태에 따라 다르게 표시해야 하므로)
                    continue
                    
                # 컨트롤 유형에 따라 적절한 스타일시트 적용
                if isinstance(control, QLabel):  # 레이블인 경우
                    control.setStyleSheet(f"""
                        QLabel {{
                            background-color: rgba(52, 73, 94, 0.6);
                            color: white;
                            border: none;
                            padding: 8px;
                            border-radius: 3px;
                            font-size: {font_size}px;
                            qproperty-alignment: AlignCenter;
                        }}
                        QLabel:hover {{
                            background-color: rgba(52, 73, 94, 1.0);
                        }}
                    """)
                else:  # 일반 버튼
                    control.setStyleSheet(f"""
                        QPushButton {{
                            background-color: rgba(52, 73, 94, 0.6);
                            color: white;
                            border: none;
                            padding: 8px;
                            border-radius: 3px;
                            font-size: {font_size}px;
                        }}
                        QPushButton:hover {{
                            background-color: rgba(52, 73, 94, 1.0);
                        }}
                    """)
            
            # 북마크 버튼 상태 업데이트 (별도로 호출)
            self.update_bookmark_button_state()

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