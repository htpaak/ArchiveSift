# 이미지 및 비디오 뷰어 애플리케이션 (PyQt5 기반)
import sys  # 시스템 관련 기능 제공 (프로그램 종료, 경로 관리 등)
import os  # 운영체제 관련 기능 제공 (파일 경로, 디렉토리 처리 등)
import platform
import shutil  # 파일 복사 및 이동 기능 제공 (고급 파일 작업)
import re  # 정규표현식 처리 기능 제공 (패턴 검색 및 문자열 처리)
import json  # JSON 파일 처리를 위한 모듈
from collections import OrderedDict  # LRU 캐시 구현을 위한 정렬된 딕셔너리
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout, QSizePolicy, QSlider, QLayout, QSpacerItem, QStyle, QStyleOptionSlider, QMenu, QAction, QScrollArea, QListWidgetItem, QListWidget, QAbstractItemView, QInputDialog, QMessageBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QLineEdit  # PyQt5 UI 위젯 (사용자 인터페이스 구성 요소)
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QFont, QMovie, QCursor, QIcon, QColor, QPalette, QFontMetrics, QTransform, QKeySequence  # 그래픽 요소 처리 (이미지, 폰트, 커서 등)
from PyQt5.QtCore import Qt, QSize, QTimer, QEvent, QPoint, pyqtSignal, QRect, QMetaObject, QObject, QUrl, QThread, QBuffer  # Qt 코어 기능 (이벤트, 신호, 타이머 등)
import cv2  # OpenCV 라이브러리 - 비디오 처리용 (프레임 추출, 이미지 변환 등)
from PIL import Image, ImageCms  # Pillow 라이브러리 - 이미지 처리용 (다양한 이미지 포맷 지원)
from io import BytesIO  # 바이트 데이터 처리용 (메모리 내 파일 스트림)
import time  # 시간 관련 기능 (시간 측정, 지연 등)

def get_app_directory():
    """애플리케이션 실행 파일이 있는 디렉토리를 반환합니다."""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 경우 (exe 파일)
        return os.path.dirname(sys.executable)
    else:
        # 일반 Python 스크립트로 실행된 경우
        return os.path.dirname(os.path.abspath(__file__))

def get_user_data_directory():
    """사용자 데이터를 저장할 디렉토리를 반환합니다."""
    app_dir = get_app_directory()
    data_dir = os.path.join(app_dir, 'UserData')
    
    # 디렉토리가 없으면 생성
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    return data_dir

# LRU 캐시 클래스 구현 (OrderedDict를 사용하여 최근 사용 항목 추적)
class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.memory_usage = 0  # 메모리 사용량 추적 (MB)
        self.max_memory = 300  # 최대 메모리 사용량 (MB) 500MB→300MB로 조정
        
    def get(self, key):
        if key not in self.cache:
            return None
        # 사용된 항목을 맨 뒤로 이동 (최근 사용)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value, size_mb=0):
        # 이미 있는 항목이면 먼저 메모리 사용량에서 제외
        if key in self.cache:
            old_item = self.cache[key]
            if hasattr(old_item, 'cached_size'):
                self.memory_usage -= old_item.cached_size
            self.cache.move_to_end(key)
        
        # 메모리 사용량 업데이트
        self.memory_usage += size_mb
        
        # 새 항목에 크기 정보 저장
        if hasattr(value, 'cached_size') == False:
            value.cached_size = size_mb
            
        # 새로운 항목 추가
        self.cache[key] = value
        
        # 메모리 제한 또는 용량 제한 초과 시 오래된 항목 제거
        while (len(self.cache) > self.capacity or 
               self.memory_usage > self.max_memory) and len(self.cache) > 0:
            _, oldest_item = self.cache.popitem(last=False)
            if hasattr(oldest_item, 'cached_size'):
                self.memory_usage -= oldest_item.cached_size
    
    def __len__(self):
        return len(self.cache)
    
    def clear(self):
        self.cache.clear()
        self.memory_usage = 0

# MPV DLL 경로를 환경 변수 PATH에 추가 (mpv 모듈 import 전에 필수)
mpv_path = os.path.join(get_app_directory(), 'mpv')
if not os.path.exists(mpv_path):
    os.makedirs(mpv_path, exist_ok=True)
    print(f"MPV 폴더가 생성되었습니다: {mpv_path}")

os.environ["PATH"] = mpv_path + os.pathsep + os.environ["PATH"]

# MPV 모듈 import (경로 설정 후에 가능)
import mpv  # 비디오 재생 라이브러리 (고성능 미디어 플레이어)

# 이미지 로딩용 작업자 스레드 클래스
class ImageLoaderThread(QThread):
    # 작업 완료 시 발생하는 신호 (경로, 픽스맵, 크기)
    loaded = pyqtSignal(str, object, float)
    error = pyqtSignal(str, str)  # 오류 발생 시 신호 (경로, 오류 메시지)
    
    def __init__(self, image_path, file_type='image'):
        super().__init__()
        self.image_path = image_path
        self.file_type = file_type  # 'image', 'psd', 'gif' 등
        
    def run(self):
        try:
            if self.file_type == 'psd':
                # PSD 파일 로딩 로직
                from PIL import Image, ImageCms
                from io import BytesIO
                
                # PSD 파일을 PIL Image로 열기
                print(f"PSD 파일 로딩 시작: {self.image_path}")
                
                # 이미지 크기 사전 확인 (매우 큰 이미지인 경우 축소 사본 사용)
                try:
                    with Image.open(self.image_path) as preview_img:
                        original_width, original_height = preview_img.size
                        original_size_mb = (original_width * original_height * 4) / (1024 * 1024)
                        
                        # 너무 큰 파일은 축소하여 로드 (100MB 이상 이미지)
                        if original_size_mb > 100:
                            # 크기를 조정하여 다시 로드 (1/2 크기로 로드)
                            max_size = (original_width // 2, original_height // 2)
                            image = Image.open(self.image_path)
                            image.thumbnail(max_size, Image.LANCZOS)
                            print(f"대형 PSD 파일 크기 조정: {original_size_mb:.2f}MB → 약 {original_size_mb/4:.2f}MB")
                        else:
                            image = Image.open(self.image_path)
                except Exception as e:
                    # 미리보기 로드 실패 시 일반적인 방법으로 로드
                    print(f"이미지 크기 확인 실패: {e}")
                    image = Image.open(self.image_path)
                
                # RGB 모드로 변환
                if image.mode != 'RGB':
                    print(f"이미지 모드 변환: {image.mode} → RGB")
                    image = image.convert('RGB')
                
                # ICC 프로파일 처리
                if 'icc_profile' in image.info:
                    try:
                        print("ICC 프로파일 변환 중...")
                        srgb_profile = ImageCms.createProfile('sRGB')
                        icc_profile = BytesIO(image.info['icc_profile'])
                        image = ImageCms.profileToProfile(
                            image,
                            ImageCms.ImageCmsProfile(icc_profile),
                            ImageCms.ImageCmsProfile(srgb_profile),
                            outputMode='RGB'
                        )
                    except Exception as icc_e:
                        print(f"ICC 프로파일 변환 실패: {icc_e}")
                        image = image.convert('RGB')
                
                # 변환된 이미지를 QPixmap으로 변환
                buffer = BytesIO()
                print("이미지를 PNG로 변환하는 중...")
                
                # 메모리 사용량 최적화 - 압축률 조정 (0이 최소 압축, 9가 최대 압축)
                compression_level = 6  # 기본값 6: 속도와 크기의 균형
                image.save(buffer, format='PNG', compress_level=compression_level, icc_profile=None)
                pixmap = QPixmap()
                
                buffer_value = buffer.getvalue()
                print(f"Buffer 크기: {len(buffer_value) / 1024:.2f} KB")
                
                if not pixmap.loadFromData(buffer_value):
                    raise ValueError("QPixmap에 이미지 데이터를 로드할 수 없습니다")
                    
                buffer.close()
                print("PSD 변환 완료")
                
            else:  # 일반 이미지
                print(f"일반 이미지 로딩 시작: {self.image_path}")
                
                # 파일 크기 확인
                file_size_mb = os.path.getsize(self.image_path) / (1024 * 1024)
                
                # 이미지 크기에 따라 로딩 방식 변경
                if file_size_mb > 30:  # 30MB보다 큰 이미지
                    reader = QImageReader(self.image_path)
                    # 품질 우선순위를 속도로 설정
                    reader.setQuality(25)  # 25% 품질 (더 빠른 로딩)
                    image = reader.read()
                    pixmap = QPixmap.fromImage(image)
                else:
                    # 일반적인 방식으로 이미지 로드
                    pixmap = QPixmap(self.image_path)
            
            if not pixmap.isNull():
                # 메모리 사용량 계산
                img_size_mb = (pixmap.width() * pixmap.height() * 4) / (1024 * 1024)
                # 로딩 완료 신호 발생
                self.loaded.emit(self.image_path, pixmap, img_size_mb)
            else:
                self.error.emit(self.image_path, "이미지 데이터가 유효하지 않습니다")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"이미지 로딩 오류: {e}\n{error_details}")
            self.error.emit(self.image_path, str(e))

# 클릭 가능한 슬라이더 클래스 정의 (기본 QSlider 확장)
class ClickableSlider(QSlider):
    clicked = pyqtSignal(int)  # 슬라이더 클릭 위치 값을 전달하는 사용자 정의 시그널
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # 부모 클래스 초기화 (QSlider 기본 기능 상속)
        self.is_dragging = False  # 드래그 상태 추적 변수 (마우스 누름+이동 상태 확인용)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:  # 좌클릭 이벤트만 처리 (다른 마우스 버튼은 무시)
            # 클릭한 위치가 핸들 영역인지 확인
            handle_rect = self.handleRect()
            
            if handle_rect.contains(event.pos()):
                # 핸들을 직접 클릭한 경우 기본 드래그 기능 활성화
                self.is_dragging = True
                return super().mousePressEvent(event)
            
            # 핸들이 아닌 슬라이더 영역 클릭 시 해당 위치로 핸들 이동
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            
            # 슬라이더의 그루브(홈) 영역 계산
            groove_rect = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderGroove, self
            )
            # 슬라이더의 핸들 영역 계산
            handle_rect = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
            )
            
            # 슬라이더의 유효 길이 계산
            slider_length = groove_rect.width()
            slider_start = groove_rect.x()
            
            # 핸들 중앙 위치 계산을 위한 핸들 너비의 절반
            handle_half_width = handle_rect.width() / 2
            
            # 클릭 위치 계산 (슬라이더 시작점 기준)
            pos = event.pos().x() - slider_start
            
            # 슬라이더 길이에서 핸들 너비 고려 (실제 이동 가능 영역 조정)
            effective_length = slider_length - handle_rect.width()
            effective_pos = max(0, min(pos, effective_length))
            
            # 클릭 위치에 대응하는 슬라이더 값 계산
            value_range = self.maximum() - self.minimum()
            
            if value_range > 0:
                # 클릭 위치 비율을 슬라이더 값으로 변환
                value = self.minimum() + (effective_pos * value_range) / effective_length
                # 슬라이더가 반전되어 있는 경우 값 조정
                if self.invertedAppearance():
                    value = self.maximum() - value + self.minimum()
                
                # 계산된 값으로 슬라이더 설정 및 시그널 발생
                self.setValue(int(value))
                self.clicked.emit(int(value))
                
                # 그루브 영역 클릭 시에도 드래그 상태로 설정
                self.is_dragging = True
        
        # 부모 클래스의 이벤트 처리기 호출
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        # 마우스 왼쪽 버튼을 누른 상태에서 드래그 중인 경우
        if self.is_dragging and event.buttons() & Qt.LeftButton:
            # 드래그 위치에 따라 슬라이더 값 계산 및 설정
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            
            # 슬라이더 그루브 영역 계산
            groove_rect = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderGroove, self
            )
            handle_rect = self.style().subControlRect(
                QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
            )
            
            # 슬라이더의 유효 길이 계산
            slider_length = groove_rect.width()
            slider_start = groove_rect.x()
            
            # 드래그 위치 계산 (슬라이더 시작점 기준)
            pos = event.pos().x() - slider_start
            
            # 슬라이더 길이에서 핸들 너비 고려
            effective_length = slider_length - handle_rect.width()
            effective_pos = max(0, min(pos, effective_length))
            
            # 드래그 위치에 대응하는 슬라이더 값 계산
            value_range = self.maximum() - self.minimum()
            
            if value_range > 0:
                # 드래그 위치 비율을 슬라이더 값으로 변환
                value = self.minimum() + (effective_pos * value_range) / effective_length
                # 슬라이더가 반전되어 있는 경우 값 조정
                if self.invertedAppearance():
                    value = self.maximum() - value + self.minimum()
                
                # 계산된 값으로 슬라이더 설정 및 시그널 발생
                self.setValue(int(value))
                self.clicked.emit(int(value))
                return
        
        # 드래그 상태가 아니거나 다른 마우스 버튼을 사용하는 경우 기본 동작 수행
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False  # 드래그 상태 해제 (마우스 버튼 뗌)
        super().mouseReleaseEvent(event)  # 부모 클래스의 이벤트 처리기 호출

    def handleRect(self):
        """슬라이더 핸들의 사각형 영역을 계산하여 반환 (클릭 위치 판단에 사용)"""
        option = QStyleOptionSlider()
        self.initStyleOption(option)  # 슬라이더 스타일 옵션 초기화
        
        # 현재 스타일에서 핸들 영역 계산
        handle_rect = self.style().subControlRect(
            QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self
        )
        
        return handle_rect  # 핸들 영역 반환

# 스크롤 가능한 메뉴 구현
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

# 메인 이미지 뷰어 클래스 정의
class ImageViewer(QWidget):
    def __init__(self):
        """이미지 뷰어 초기화"""
        super().__init__()
        
        # 변수 초기화
        self.image_files = []  # 이미지 파일 목록
        self.current_index = 0  # 현재 표시 중인 이미지 인덱스 (0으로 초기화)
        self.current_image_path = ""  # 현재 이미지 경로
        self.base_folder = ""  # 기준 폴더 경로
        self.folder_buttons = []  # 폴더 버튼 목록
        # 북마크 관련 변수 초기화
        self.bookmarks = []  # 책갈피된 파일 경로 리스트
        self.bookmark_menu = None  # 북마크 메뉴 객체
        
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

        # 책갈피 관련 변수 초기화
        self.bookmark_menu = None  # 책갈피 드롭다운 메뉴 객체

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
        self.update_bookmark_menu()
        
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
        self.image_cache = LRUCache(30)  # 일반 이미지용 캐시 (30개 항목)
        self.psd_cache = LRUCache(3)     # PSD 파일용 캐시 (5→3개 항목으로 축소)
        self.gif_cache = LRUCache(8)     # GIF/애니메이션용 캐시 (10→8개 항목으로 축소)

        self.last_wheel_time = 0  # 마지막 휠 이벤트 발생 시간 (휠 이벤트 쓰로틀링용)
        self.wheel_cooldown_ms = 1000  # 1000ms 쿨다운 (500ms에서 변경됨) - 휠 이벤트 속도 제한

        # 리소스 관리를 위한 객체 추적
        self.timers = []  # 모든 타이머 추적

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
                    
                    # 북마크에서 제거
                    if self.current_image_path in self.bookmarks:
                        self.bookmarks.remove(self.current_image_path)
                        self.save_bookmarks()
                        self.update_bookmark_menu()
                    
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
            self.message_label.move(margin, margin + 20)
        
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

    def delayed_resize(self):
        """리사이징 완료 후 지연된 UI 업데이트 처리"""
        try:
            # 현재 표시 중인 미디어 크기 조절
            if hasattr(self, 'current_image_path') and self.current_image_path:
                file_ext = os.path.splitext(self.current_image_path)[1].lower()
                
                # 이미지 타입에 따른 리사이징 처리
                if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif']:
                    pixmap = QPixmap(self.current_image_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.image_label.setPixmap(scaled_pixmap)
                elif file_ext == '.gif' and hasattr(self, 'current_movie'):
                    # 애니메이션 크기 조정 처리
                    self.scale_gif()
                elif file_ext == '.webp' and hasattr(self, 'current_movie'):
                    # WEBP 이미지/애니메이션 처리
                    self.scale_webp()
                elif file_ext == '.psd':
                    # PSD 파일 리사이징 처리
                    self.show_psd(self.current_image_path)
                elif file_ext in ['.mp4', '.avi', '.wmv', '.ts', '.m2ts', '.mov', '.qt', '.mkv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', '.vob', '.wav', '.flac', '.mp3', '.aac', '.m4a', '.ogg']:
                    # MPV 플레이어 윈도우 ID 업데이트
                    if hasattr(self, 'player'):
                        self.player.wid = int(self.image_label.winId())
                
            # 이미지 정보 레이블 업데이트
            if hasattr(self, 'image_info_label') and self.image_files:
                self.update_image_info()
                    
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

            # 자연스러운 정렬을 위한 함수 정의 (숫자가 포함된 텍스트 정렬용)
            def natural_keys(text):
                import re
                def atoi(text):
                    return int(text) if text.isdigit() else text  # 숫자는 정수로 변환
                return [atoi(c) for c in re.split('([0-9]+)', text)]  # 숫자와 텍스트 부분 분리

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
        
        # OpenCV 비디오 캡처 객체 정리
        if self.cap is not None:
            self.cap.release()  # 비디오 캡처 객체 해제
            self.cap = None  # 참조 제거
        
        # 비디오 프레임 업데이트 타이머 중지
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()  # 타이머 중지
            if self.timer in self.timers:
                self.timers.remove(self.timer)
        
        # MPV 플레이어 정지 (플레이어가 존재하고 실행 중인 경우)
        if hasattr(self, 'player') and self.player:
            try:
                # 플레이어가 재생 중인지 확인
                if self.player.playback_time is not None:  # 재생 시간이 있으면 재생 중
                    self.player.stop()  # 재생 중지
                    # mpv 속성 초기화
                    self.player.loop = False
                    self.player.mute = False
            except Exception as e:
                print(f"비디오 정지 에러: {e}")  # 에러 로깅
                
        # 비디오 타이머 정지
        if hasattr(self, 'video_timer') and self.video_timer.isActive():
            self.video_timer.stop()  # 비디오 타이머 중지
            if self.video_timer in self.timers:
                self.timers.remove(self.video_timer)
                
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
        self.update_bookmark_menu()
        
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

        if file_ext == '.gif':  # GIF 파일 처리
            self.current_media_type = 'gif'  # 미디어 타입 업데이트
            self.show_gif(image_path)  # GIF를 표시하는 메서드 호출
        elif file_ext == '.psd':  # PSD 파일 처리
            self.current_media_type = 'image'  # 미디어 타입 업데이트
            
            # 기존 진행 중인 PSD 로더 스레드 확인 및 종료
            for path, loader in list(self.loader_threads.items()):
                if path != image_path and loader.isRunning():
                    try:
                        # 이전 로더 강제 종료
                        loader.terminate()
                        loader.wait(100)  # 최대 100ms 대기
                        print(f"PSD 로더 종료: {os.path.basename(path)}")
                    except Exception as e:
                        print(f"PSD 로더 종료 중 오류: {e}")
            
            # PSD 파일 로딩 시작
            try:
                self.show_psd(image_path)  # PSD를 표시하는 메서드 호출
            except Exception as e:
                print(f"PSD 표시 중 오류: {e}")
                # 오류 발생 시 기본 이미지 또는 오류 메시지 표시
                self.image_label.setText("PSD 파일 로드 중 오류 발생")
                self.show_message(f"PSD 파일 로드 오류: {str(e)}")
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif']:  # JPG, JPEG, PNG 파일 처리
            self.current_media_type = 'image'  # 미디어 타입 업데이트
            
            # 파일 크기 확인 (대용량 이미지 확인)
            file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
            
            # 대용량 이미지인 경우 먼저 저해상도 미리보기 표시
            if file_size_mb > 20:  # 20MB 이상인 경우
                # 로딩 중 표시
                self.show_loading_indicator()
                
                # "대용량 이미지 로딩 중" 메시지 표시
                self.show_message(f"대용량 이미지 로딩 중 ({file_size_mb:.1f}MB)")
                
                # 미리보기 이미지 표시 (빠른 로딩)
                reader = QImageReader(image_path)
                reader.setScaledSize(QSize(800, 600))  # 작은 크기로 미리보기
                preview = reader.read()
                if not preview.isNull():
                    preview_pixmap = QPixmap.fromImage(preview)
                    # float를 int로 변환
                    label_size = self.image_label.size()
                    self.image_label.setPixmap(preview_pixmap.scaled(
                        label_size,
                        Qt.KeepAspectRatio,
                        Qt.FastTransformation  # 빠른 변환 적용
                    ))
                    QApplication.processEvents()  # UI 즉시 업데이트
            
            # 캐시에서 먼저 확인
            cached_pixmap = self.image_cache.get(image_path)
            
            if cached_pixmap is not None:
                # 캐시에서 찾은 경우 바로 사용
                pixmap = cached_pixmap
                print(f"이미지 캐시 히트: {os.path.basename(image_path)}")
                
                # 회전 각도가 0이 아니면 회전 적용
                if hasattr(self, 'current_rotation') and self.current_rotation != 0:
                    # 회전 변환 적용 (원본 이미지에 직접 적용)
                    transform = QTransform().rotate(self.current_rotation)
                    pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                    print(f"캐시된 이미지에 회전 적용됨: {self.current_rotation}°")
                
                # 이미지 바로 표시 (크기 조정 후)
                label_size = self.image_label.size()
                scaled_pixmap = pixmap.scaled(
                    label_size, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                # 로딩 중 표시
                self.show_loading_indicator()
                
                # 기존 스레드 정리
                self.cleanup_loader_threads()
                
                # 비동기 로딩 시작
                loader = ImageLoaderThread(image_path, 'image')
                loader.loaded.connect(self.on_image_loaded)
                loader.error.connect(self.on_image_error)
                
                # 스레드 추적
                self.loader_threads[image_path] = loader
                loader.start()
        elif file_ext == '.webp':  # WEBP 이미지/애니메이션 처리
            # WEBP 파일은 애니메이션일 수도 있고 일반 이미지일 수도 있음
            # show_webp 함수에서 알맞은 미디어 타입을 설정함 ('image' 또는 'webp_animation')
            self.show_webp(self.current_image_path)  # WEBP 파일 처리
        elif file_ext in ['.mp4', '.avi', '.wmv', '.ts', '.m2ts', '.mov', '.qt', '.mkv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', '.vob', '.wav', '.flac', '.mp3', '.aac', '.m4a', '.ogg']:  # MP4 파일 처리-
            self.current_media_type = 'video'  # 미디어 타입 업데이트
            self.play_video(image_path)  # MP4 비디오 재생
        else:
            self.current_media_type = 'unknown'  # 미디어 타입 업데이트

        self.update_image_info()  # 이미지 정보 업데이트 메소드 호출

        # 시간 레이블 초기화
        self.time_label.setText("00:00 / 00:00")  # 시간 레이블 초기화
        self.time_label.show()  # 시간 레이블 표시

        # 제목표시줄과 이미지 정보 레이블을 앞으로 가져옴
        if hasattr(self, 'title_bar'):
            self.title_bar.raise_()
        if hasattr(self, 'image_info_label'):
            self.image_info_label.raise_()

    def show_psd(self, image_path):
        """PSD 파일을 처리하는 메서드입니다."""
        # 이미 로딩 중인지 확인
        loading_in_progress = False
        for path, loader in list(self.loader_threads.items()):
            if path == image_path and loader.isRunning():
                loading_in_progress = True
                print(f"이미 로딩 중: {os.path.basename(image_path)}")
                break
        
        if loading_in_progress:
            # 이미 로딩 중이면 다시 시작하지 않음
            return
        
        # 로딩 표시 시작
        self.show_loading_indicator()
        
        # LRUCache에서 캐시된 이미지 확인
        pixmap = self.psd_cache.get(image_path)
        
        if pixmap is not None:
            # 캐시에서 찾은 경우 바로 사용
            print(f"PSD 캐시 히트: {os.path.basename(image_path)}")
            
            # 회전 각도가 0이 아니면 회전 적용
            if hasattr(self, 'current_rotation') and self.current_rotation != 0:
                # 회전 변환 적용
                transform = QTransform().rotate(self.current_rotation)
                pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                print(f"PSD에 회전 적용됨: {self.current_rotation}°")
            
            # 이미지 크기 조정 후 표시
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            
            # 로딩 인디케이터 숨기기
            self.hide_loading_indicator()
        else:
            # 진행 중인 모든 PSD 로더를 안전하게 처리
            for path, loader in list(self.loader_threads.items()):
                if loader.isRunning():
                    # 실행 중인 다른 PSD 로더의 연결을 해제하여 신호가 처리되지 않도록 함
                    try:
                        loader.loaded.disconnect()
                        loader.error.disconnect()
                    except Exception:
                        pass
                        
                    # 강제 종료는 하지 않고 자연스럽게 종료되도록 함
                    # terminate()는 불안정할 수 있으므로 사용하지 않음
            
            # 로더 스레드 목록 비우기 (새 시작 전에)
            self.loader_threads.clear()
            
            # 비동기 로딩 시작
            print(f"새 PSD 로더 시작: {os.path.basename(image_path)}")
            loader = ImageLoaderThread(image_path, 'psd')
            loader.loaded.connect(self.on_image_loaded)
            loader.error.connect(self.on_image_error)
            
            # 스레드 추적
            self.loader_threads[image_path] = loader
            loader.start()
            
            # 로딩 시작 메시지 (파일 경로 포함)
            print(f"PSD 파일 로딩 시작: {image_path}")
            
            # 로딩 메시지 표시
            self.show_message(f"PSD 파일 로딩 중... ({os.path.basename(image_path)})")

    def show_gif(self, image_path):
        # gif 애니메이션을 처리하기 위해 QImageReader를 사용
        reader = QImageReader(image_path)

        # 이미지를 로드하고 애니메이션으로 처리
        if reader.supportsAnimation():  # 애니메이션을 지원하면
            
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

        # 이미지를 로드하고 애니메이션으로 처리
        if reader.supportsAnimation():  # 애니메이션을 지원하면
            # 애니메이션 WEBP로 미디어 타입 설정
            self.current_media_type = 'webp_animation'
            
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
        
        # 로딩 표시 시작
        self.show_loading_indicator()
        
        # 비디오가 표시되고 500ms 후에 로딩 인디케이터 숨기기
        QTimer.singleShot(500, self.hide_loading_indicator)
        
        # 기존 비디오 중지
        self.stop_video()
        
        # 애니메이션이 재생 중일 경우 정지
        if hasattr(self, 'current_movie') and self.current_movie:
            self.current_movie.stop()
            self.current_movie.deleteLater()  # Qt 객체 명시적 삭제 요청
            
            if hasattr(self, 'gif_timer') and self.gif_timer.isActive():
                self.gif_timer.stop()
                if self.gif_timer in self.timers:
                    self.timers.remove(self.gif_timer)
        
        # MPV 플레이어가 초기화되지 않은 경우 재초기화 시도
        if not hasattr(self, 'player') or self.player is None:
            try:
                self.player = mpv.MPV(log_handler=print, 
                                    ytdl=True, 
                                    input_default_bindings=True, 
                                    input_vo_keyboard=True,
                                    hwdec='no')  # 하드웨어 가속 비활성화 (문제 해결을 위해)
                print("MPV 플레이어 동적 초기화 성공")
            except Exception as e:
                print(f"MPV 플레이어 초기화 실패: {e}")
                self.hide_loading_indicator()
                self.show_message("비디오 플레이어 초기화 실패")
                return
                
        # MPV로 비디오 재생
        try:
            # 화면에 비디오 출력을 위한 윈도우 핸들 설정
            wid = int(self.image_label.winId())
            self.player.wid = wid
            
            # MPV 옵션 설정
            self.player.loop = True  # 비디오 반복 재생
            self.player.volume = 100  # 볼륨 100%로 설정
            self.player.seekable = True  # seek 가능하도록 설정
            self.player.pause = False  # 항상 재생 상태로 시작
            
            # 회전 각도 설정
            self.player['video-rotate'] = str(self.current_rotation)
            
            # 비디오 파일 재생
            self.player.play(video_path)
            
            # 비디오 정보 업데이트
            self.current_image_path = video_path
            self.current_media_type = 'video'  # 미디어 타입 설정
            
            # 슬라이더 초기화
            self.playback_slider.setRange(0, 0)  # 슬라이더 범위를 0으로 설정
            self.playback_slider.setValue(0)  # 슬라이더 초기값을 0으로 설정
            
            # 재생 버튼 상태 업데이트
            self.play_button.setText("❚❚")  # 재생 중이므로 일시정지 아이콘 표시
            
            # 슬라이더 시그널 연결 전에 기존 연결 해제
            self.disconnect_all_slider_signals()
            
            # 슬라이더 이벤트 연결
            self.playback_slider.sliderPressed.connect(self.slider_pressed)
            self.playback_slider.sliderReleased.connect(self.slider_released)
            self.playback_slider.valueChanged.connect(self.seek_video)
            self.playback_slider.clicked.connect(self.slider_clicked)
            
            # 비디오 프레임 레이트에 맞춰 타이머 간격 설정
            try:
                # OpenCV로 비디오 프레임 레이트 확인
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                cap.release()
                
                # 프레임 레이트가 유효한 경우에만 사용
                if fps > 0:
                    # 밀리초 단위로 변환 (1000/fps)
                    timer_interval = int(1000 / fps)
                    # 최소 16ms (약 60fps), 최대 100ms (약 10fps)로 제한
                    timer_interval = max(16, min(timer_interval, 100))
                else:
                    timer_interval = 33  # 약 30fps (기본값)
            except Exception as e:
                print(f"프레임 레이트 확인 오류: {e}")
                timer_interval = 33  # 오류 발생 시 약 30fps로 기본 설정
            
            # MPV의 재생 상태를 주기적으로 업데이트하기 위한 타이머 설정
            self.video_timer = QTimer(self)
            self.video_timer.timeout.connect(self.update_video_playback)  # 슬라이더 업데이트 호출
            self.video_timer.start(timer_interval)  # 비디오 프레임 레이트에 맞춰 설정
            self.timers.append(self.video_timer)  # 타이머 추적에 추가
            
            # 비디오 종료 시 타이머 중지
            self.player.observe_property('playback-restart', self.on_video_end)  # 비디오 종료 시 호출될 메서드 등록
            
            # 이전 duration 관찰자가 있으면 제거
            if hasattr(self, 'duration_observer_callback'):
                try:
                    self.player.unobserve_property('duration', self.duration_observer_callback)
                except Exception as e:
                    print(f"관찰자 제거 오류: {e}")
                    pass  # 기존 관찰자가 없거나 오류 발생 시 무시
            
            # duration 속성 관찰 (추가 정보 용도)
            def check_video_loaded(name, value):
                if value is not None and value > 0:
                    print(f"비디오 로드 완료: {video_path}, 길이: {value}초")
            
            # 새 관찰자 등록 및 참조 저장
            self.duration_observer_callback = check_video_loaded
            self.player.observe_property('duration', self.duration_observer_callback)
            
        except Exception as e:
            print(f"비디오 재생 에러: {e}")  # 에러 로깅
            self.hide_loading_indicator()  # 에러 발생 시 로딩 인디케이터 숨김
            self.show_message(f"비디오 재생 오류: {str(e)}")

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
        if self.current_media_type in ['gif', 'webp'] and hasattr(self, 'current_movie') and self.current_movie:
            try:
                # 유효한 프레임 번호인지 확인
                max_frame = self.current_movie.frameCount() - 1
                frame = min(max(0, value), max_frame)  # 범위 내로 제한
                self.current_movie.jumpToFrame(frame)
                return
            except Exception as e:
                pass  # 예외 발생 시 무시
        
        # 비디오 처리
        if self.current_media_type == 'video' and hasattr(self, 'player') and self.player:
            try:
                if self.player.playback_time is not None:  # 재생 중인지 확인
                    # 클릭한 위치의 값을 초 단위로 변환
                    seconds = value / 1000.0  # 밀리초를 초 단위로 변환
                    # MPV의 seek 함수를 사용하여 정확한 위치로 이동
                    self.player.command('seek', seconds, 'absolute')
            except Exception as e:
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
        if self.current_media_type in ['gif', 'webp'] and hasattr(self, 'current_movie') and self.current_movie:
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
        elif self.current_media_type == 'video' and hasattr(self, 'player') and self.player:
            try:
                if self.player.playback_time is not None:  # 재생 중인지 확인
                    seconds = self.playback_slider.value() / 1000.0  # 밀리초를 초 단위로 변환
                    self.player.command('seek', seconds, 'absolute')  # MPV의 seek 함수 사용
            except Exception as e:
                pass  # 예외 발생 시 무시
                
        # 슬라이더 조작 후 약간의 지연을 두고 창에 포커스를 돌려줌
        QTimer.singleShot(50, self.setFocus)

    def seek_video(self, value):
        """슬라이더 값에 따라 비디오 재생 위치를 변경합니다."""
        if hasattr(self, 'player') and self.is_slider_dragging:
            # MPV가 비디오를 재생 중인지 확인
            if self.player.playback_time is None or self.player.playback_time < 0:
                return  # MPV가 비디오를 재생 중이지 않으면 seek 명령을 실행하지 않음

            # 슬라이더 값을 초 단위로 변환 (value는 밀리초 단위)
            seconds = value / 1000.0  # 밀리초를 초 단위로 변환
            # MPV의 seek 함수를 사용하여 정확한 위치로 이동
            self.player.command('seek', seconds, 'absolute')

    def seek_animation(self, value):
        """슬라이더 값에 따라 애니메이션 재생 위치를 변경합니다."""
        if hasattr(self, 'current_movie'):
            # 슬라이더 값을 프레임 번호로 변환
            frame = value
            # 애니메이션이 재생 중일 경우 해당 프레임으로 점프
            self.current_movie.jumpToFrame(frame)

    def update_video_playback(self):
        """MPV 비디오의 재생 위치에 따라 슬라이더 값을 업데이트합니다."""
        if hasattr(self, 'player') and not self.is_slider_dragging:
            try:
                position = self.player.playback_time  # 현재 재생 위치
                duration = self.player.duration  # 총 길이
                
                # playback_time 값이 None인 경우 처리
                if position is None:
                    return  # 슬라이더 업데이트를 건너뜁니다.

                # 슬라이더 범위 설정
                if duration is not None and duration > 0:
                    # 슬라이더 범위를 밀리초 단위로 설정 (1000으로 곱해서 더 세밀하게)
                    self.playback_slider.setRange(0, int(duration * 1000))
                    
                    # 현재 위치가 duration을 초과하면 0으로 리셋
                    if position >= duration:
                        self.playback_slider.setValue(0)
                        self.player.command('seek', 0, 'absolute')  # seek_to 대신 command 사용
                    else:
                        # 슬라이더 값을 밀리초 단위로 설정 (1000으로 곱해서 더 세밀하게)
                        self.playback_slider.setValue(int(position * 1000))
                    
                    self.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

                self.previous_position = position  # 현재 위치를 이전 위치로 저장

            except mpv.ShutdownError:
                self.video_timer.stop()  # 타이머 중지

    def format_time(self, seconds):
        """초를 'MM:SS' 형식으로 변환합니다."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02}:{seconds:02}"

    def update_play_button(self):
        """재생 상태에 따라 버튼 텍스트 업데이트"""
        # 미디어 타입에 따른 버튼 텍스트 업데이트
        if self.current_media_type in ['gif', 'webp'] and hasattr(self, 'current_movie') and self.current_movie:
            # 애니메이션(GIF, WEBP) 재생 상태 확인
            if self.current_movie.state() == QMovie.Running:
                self.play_button.setText("❚❚")  # 일시정지 아이콘
            else:
                self.play_button.setText("▶")  # 재생 아이콘
        elif self.current_media_type == 'video' and hasattr(self, 'player') and self.player:
            # 비디오 재생 상태 확인
            try:
                if self.player.playback_time is not None:  # 비디오가 로드되었는지 확인
                    self.play_button.setText("❚❚" if not self.player.pause else "▶")
                    self.update_video_playback()  # 슬라이더 업데이트 호출
            except mpv.ShutdownError:
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
        
        # 동작 중인 비디오나 애니메이션인 경우 쿨다운 시간 증가 (더 느리게 이미지 전환)
        if self.current_media_type in ['video', 'gif', 'webp']:
            cooldown_ms = 800  # 미디어 재생 중일 때는 더 긴 쿨다운
        
        # 큰 이미지를 로딩 중인 경우 쿨다운 시간 증가
        if self.loader_threads and len(self.loader_threads) > 0:
            cooldown_ms = 1000  # 로딩 중일 때는 가장 긴 쿨다운
        
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
        """전체화면 모드와 일반 모드를 전환합니다."""
        is_entering_fullscreen = not self.isFullScreen()  # 현재 상태의 반대
        
        # 현재 비디오 재생 상태 저장
        video_was_playing = False
        current_position = 0
        if hasattr(self, 'player') and self.current_media_type == 'video':
            try:
                video_was_playing = not self.player.pause  # 재생 중이었는지 확인
                current_position = self.player.playback_time or 0  # 현재 재생 위치 저장
            except Exception:
                pass
        
        if self.isFullScreen():
            # 전체화면 모드에서 일반 모드로 전환
            self.showNormal()
            
            # 타이틀바 및 컨트롤 위젯 표시
            if hasattr(self, 'title_bar'):
                self.title_bar.show()
            
            # 버튼 및 컨트롤 표시 - 속성 존재 확인 후 실행
            if hasattr(self, 'playback_controls_widget'):
                self.playback_controls_widget.show()
            if hasattr(self, 'button_widget'):
                self.button_widget.show()
                
            # 슬라이더 위젯 표시
            if hasattr(self, 'slider_widget'):
                self.slider_widget.show()
            
            # 폴더 버튼들 표시
            for row in self.buttons:
                for button in row:
                    button.show()
            
            # 전체화면 아이콘 변경
            self.fullscreen_btn.setText("🗖")  # 전체화면 아이콘으로 변경
                
            # 비디오 상태 복구
            if hasattr(self, 'player') and self.current_media_type == 'video':
                try:
                    # 비디오가 재생 중이었다면 약간의 지연 후 상태 복구
                    QTimer.singleShot(100, lambda: self.restore_video_state(video_was_playing, current_position))
                except Exception:
                    pass
        else:
            # 일반 모드에서 전체화면 모드로 전환
            self.showFullScreen()
            
            # 타이틀바 숨기기
            if hasattr(self, 'title_bar'):
                self.title_bar.hide()
            
            # 버튼 및 컨트롤 숨기기 - 속성 존재 확인 후 실행
            if hasattr(self, 'playback_controls_widget'):
                self.playback_controls_widget.hide()
            if hasattr(self, 'button_widget'):
                self.button_widget.hide()
            if hasattr(self, 'slider_widget'):
                self.slider_widget.hide()
                
            # 폴더 버튼들 숨기기
            for row in self.buttons:
                for button in row:
                    button.hide()
            
            # 전체화면 아이콘 변경
            self.fullscreen_btn.setText("⛶")  # 일반화면 아이콘으로 변경
            
            # 성능 최적화: 전체화면 모드에서 추가 최적화 
            if hasattr(self, 'player') and hasattr(self, 'current_media_type') and self.current_media_type == 'video':
                # 비디오 품질 전체화면 모드로 최적화
                self.player['video-sync'] = 'audio'  # 오디오 기반으로 동기화 (성능 향상)
        
        # 현재 이미지 크기 조정 강제 실행 (전체화면 전환 시 필요)
        QTimer.singleShot(10, self.update_image_info)
        QTimer.singleShot(10, lambda: self.show_image(self.current_image_path))
        
        # 오버레이 표시
        if is_entering_fullscreen:
            self.fullscreen_overlay.setText("전체화면 모드로 전환\nESC 키로 종료")
        else:
            self.fullscreen_overlay.setText("일반 모드로 전환")
        
        # 오버레이 위치 및 크기 조정
        self.fullscreen_overlay.adjustSize()
        self.fullscreen_overlay.move(
            (self.width() - self.fullscreen_overlay.width()) // 2,
            (self.height() - self.fullscreen_overlay.height()) // 2
        )
        
        # 오버레이 표시 및 자동 숨김 타이머 설정
        self.fullscreen_overlay.show()
        QTimer.singleShot(2000, self.fullscreen_overlay.hide)  # 2초 후 숨김
        
        # 전체화면 변경 시 메시지 표시
        self.show_message("전체화면 모드" if self.isFullScreen() else "일반 모드로 전환")

    def restore_video_state(self, was_playing, position):
        """비디오 재생 상태를 복구합니다"""
        if hasattr(self, 'player') and self.current_media_type == 'video':
            try:
                # 위치 복구
                self.player.command('seek', position, 'absolute')
                
                # 재생 상태 복구
                if was_playing:
                    self.player.pause = False
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
        
        # MPV 플레이어 정리
        if hasattr(self, 'player'):
            try:
                self.player.terminate()  # 플레이어 종료
                self.player = None  # 참조 제거
            except Exception as e:
                print(f"플레이어 종료 오류: {e}")
        
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
        if hasattr(self, 'player'):
            self.player.mute = not self.player.mute  # MPV의 음소거 상태를 토글
            # 버튼 아이콘 변경 (음소거 상태에 따라)
            if self.player.mute:
                self.mute_button.setText("🔇")  # 음소거 상태 아이콘 (소리 없음)
            else:
                self.mute_button.setText("🔈")  # 음소거 해제 상태 아이콘 (소리 있음)

    def adjust_volume(self, volume):
        """음량을 조절합니다."""
        if hasattr(self, 'player'):
            # 현재 슬라이더 값을 가져와서 볼륨을 설정
            volume_value = self.volume_slider.value()  # 슬라이더의 현재 값
            self.player.volume = volume_value  # MPV의 볼륨 설정

    def toggle_animation_playback(self):
        """애니메이션(GIF, WEBP) 또는 비디오 재생/일시정지 토글"""
        
        # 현재 열려있는 파일 확인
        if not self.current_image_path:
            return
            
        # 미디어 타입에 따라 처리
        if self.current_media_type in ['gif', 'webp', 'webp_animation'] and hasattr(self, 'current_movie') and self.current_movie:
            # GIF나 WEBP 애니메이션 처리
            is_paused = self.current_movie.state() != QMovie.Running
            self.current_movie.setPaused(not is_paused)  # 상태 토글
            self.play_button.setText("▶" if not is_paused else "❚❚")  # 토글된 상태에 따라 아이콘 설정
                
        # 비디오 처리
        elif self.current_media_type == 'video' and hasattr(self, 'player'):
            try:
                is_paused = self.player.pause
                self.player.pause = not is_paused  # 비디오 재생/일시정지 토글
                self.play_button.setText("▶" if self.player.pause else "❚❚")  # 버튼 상태 업데이트
            except Exception as e:
                pass  # 예외 발생 시 무시

    def toggle_bookmark(self):
        """현재 이미지를 책갈피에 추가하거나 제거합니다."""
        if not hasattr(self, 'current_image_path') or not self.current_image_path:
            self.show_message("북마크할 이미지가 없습니다")
            return
            
        # 이미 책갈피되어 있는지 확인
        if self.current_image_path in self.bookmarks:
            # 책갈피 제거
            self.bookmarks.remove(self.current_image_path)
            self.show_message("북마크에서 제거되었습니다")
        else:
            # 책갈피 추가
            self.bookmarks.append(self.current_image_path)
            self.show_message("북마크에 추가되었습니다")
            
        # 북마크 버튼 상태 업데이트
        self.update_bookmark_button_state()
            
        # 책갈피 메뉴 업데이트
        self.update_bookmark_menu()

    def update_bookmark_menu(self):
        """책갈피 메뉴를 업데이트합니다."""
        # 기존 메뉴가 없으면 생성
        if not self.bookmark_menu:
            self.bookmark_menu = ScrollableMenu(self)
        else:
            # 메뉴가 있으면 비우기
            self.bookmark_menu.clear()
        
        # 북마크 관리 액션 추가 - 항상 표시
        add_bookmark_action = QAction("북마크 추가", self)
        add_bookmark_action.triggered.connect(self.add_bookmark)  # 추가 기능 연결
        self.bookmark_menu.addAction(add_bookmark_action)
        
        # 현재 북마크 삭제 버튼 - 항상 표시
        remove_bookmark_action = QAction("현재 북마크 삭제", self)
        remove_bookmark_action.triggered.connect(self.remove_bookmark)  # 삭제 기능 연결
        
        # 현재 이미지가 북마크되어 있지 않을 경우 비활성화
        if not hasattr(self, 'current_image_path') or self.current_image_path not in self.bookmarks:
            remove_bookmark_action.setEnabled(False)
            
        self.bookmark_menu.addAction(remove_bookmark_action)
        
        # 모든 책갈피 지우기 액션 - 항상 표시 (북마크 삭제 바로 아래로 이동)
        clear_action = QAction("모든 북마크 지우기", self)
        clear_action.triggered.connect(self.clear_bookmarks)
        # 북마크가 없을 경우 비활성화
        if not self.bookmarks:
            clear_action.setEnabled(False)
            
        self.bookmark_menu.addAction(clear_action)
            
        # 구분선 추가
        self.bookmark_menu.addSeparator()
            
        # 북마크 목록 섹션
        if not self.bookmarks:
            empty_action = QAction("북마크 없음", self)
            empty_action.setEnabled(False)
            self.bookmark_menu.addAction(empty_action)
        else:
            # 북마크 수 표시
            bookmark_count_action = QAction(f"총 북마크: {len(self.bookmarks)}개", self)
            bookmark_count_action.setEnabled(False)
            self.bookmark_menu.addAction(bookmark_count_action)
            
            # 구분선 추가
            self.bookmark_menu.addSeparator()
            
            # 최대 100개까지 표시 (기존 30개에서 변경)
            max_bookmarks = min(100, len(self.bookmarks))
            
            # 책갈피 목록 추가
            for idx, path in enumerate(self.bookmarks[:max_bookmarks]):
                # 파일 이름만 추출
                filename = os.path.basename(path)
                
                # 경로 처리 - 너무 길면 축약
                path_display = path
                if len(path_display) > 60:  # 경로가 60자 이상인 경우
                    # 드라이브와 마지막 2개 폴더만 표시
                    drive, tail = os.path.splitdrive(path_display)
                    parts = tail.split(os.sep)
                    if len(parts) > 2:
                        # 드라이브 + '...' + 마지막 2개 폴더
                        path_display = f"{drive}{os.sep}...{os.sep}{os.sep.join(parts[-2:])}"
                
                # 표시 번호 추가 (간결하게 수정)
                display_text = f"{idx + 1}. {filename}"  # 경로 없이 파일명만 표시
                
                # 메뉴 항목에 파일명만 표시하고 툴팁에 전체 경로 표시
                bookmark_action = QAction(display_text, self)
                bookmark_action.setToolTip(path_display)  # 전체 경로는 툴팁으로 표시
                
                # 클릭 시 해당 이미지로 이동하는 함수 생성 (람다 함수의 캡처 문제 해결)
                def create_bookmark_handler(bookmark_path):
                    return lambda: self.load_bookmarked_image(bookmark_path)
                
                # 각 북마크 항목마다 고유한 핸들러 함수 생성
                bookmark_action.triggered.connect(create_bookmark_handler(path))
                self.bookmark_menu.addAction(bookmark_action)
            
            # 북마크가 100개 이상이면 메시지 표시
            if len(self.bookmarks) > 100:
                more_action = QAction(f"... 외 {len(self.bookmarks) - 100}개 더 있습니다.", self)
                more_action.setEnabled(False)
                self.bookmark_menu.addAction(more_action)

        # 메뉴에 직접 스크롤 활성화 속성 설정
        self.bookmark_menu.setProperty("_q_scrollable", True)
        
        # 북마크가 7개 이상이면 스크롤을 위한 추가 설정
        if len(self.bookmarks) > 7:
            # 메뉴 크기 제한 설정
            desktop = QApplication.desktop().availableGeometry()
            max_height = min(800, desktop.height() * 0.7)
            self.bookmark_menu.setMaximumHeight(int(max_height))
            
            # 스타일시트 재적용
            self.bookmark_menu.setStyle(self.bookmark_menu.style())

    def load_bookmarked_image(self, path):
        """책갈피된 이미지를 로드합니다."""
        if os.path.exists(path):
            # 이미지가 위치한 폴더 경로 추출
            folder_path = os.path.dirname(path)
            
            # 폴더 내의 이미지 목록 가져오기
            self.image_files = self.get_image_files(folder_path)
            
            if self.image_files:
                # 파일 목록 정렬
                self.image_files.sort()
                
                # 현재 이미지의 인덱스 찾기
                if path in self.image_files:
                    self.current_index = self.image_files.index(path)
                    
                    # 이미지 표시
                    self.show_image(path)
                    
                    # 이미지 정보 업데이트
                    self.update_image_info()
                    
                    self.show_message(f"북마크 폴더 열기: {os.path.basename(folder_path)}")
                else:
                    # 정렬된 목록에 이미지가 없는 경우 (드물게 발생 가능)
                    self.show_image(path)
                    self.show_message(f"북마크 이미지를 표시합니다: {os.path.basename(path)}")
            else:
                # 폴더에 이미지가 없는 경우 (드물게 발생 가능)
                self.show_image(path)
                self.show_message(f"북마크 이미지를 표시합니다: {os.path.basename(path)}")
            
            # 북마크 메뉴 업데이트
            self.update_bookmark_menu()
        else:
            self.show_message(f"파일을 찾을 수 없습니다: {os.path.basename(path)}")
            # 존재하지 않는 책갈피 제거
            if path in self.bookmarks:
                self.bookmarks.remove(path)
                self.update_bookmark_menu()

    def clear_bookmarks(self):
        """모든 책갈피를 지웁니다."""
        self.bookmarks = []
        # 페이지 관련 변수 제거
        # self.current_bookmark_page = 0  # 현재 북마크 페이지
        # 북마크 버튼 상태 업데이트
        self.update_bookmark_button_state()
        # 북마크 메뉴 업데이트
        self.update_bookmark_menu()
        # 메시지 표시
        self.show_message("모든 북마크가 삭제되었습니다")
        # 북마크 저장
        self.save_bookmarks()
        
    def update_bookmark_button_state(self):
        """북마크 버튼 상태 업데이트"""
        # 초기 상태 확인: 현재 이미지 경로가 있고 북마크에 포함되어 있는지 확인
        if hasattr(self, 'current_image_path') and self.current_image_path and self.current_image_path in self.bookmarks:
            # 북마크된 상태
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
        else:
            # 북마크되지 않은 상태 또는 이미지가 로드되지 않은 상태
            self.slider_bookmark_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(52, 73, 94, 0.6);  /* 일반 버튼과 동일한 색상 */
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(52, 73, 94, 1.0);
                }
            """)

    def add_bookmark(self):
        """현재 이미지를 북마크에 추가합니다."""
        if not hasattr(self, 'current_image_path') or not self.current_image_path:
            self.show_message("북마크할 이미지가 없습니다")
            return
            
        # 이미 북마크되어 있는지 확인
        if self.current_image_path in self.bookmarks:
            self.show_message("이미 북마크되어 있습니다")
            return
            
        # 북마크 추가
        self.bookmarks.append(self.current_image_path)
        
        # 북마크 버튼 상태 업데이트
        self.update_bookmark_button_state()
        
        # 북마크 메뉴 업데이트
        self.update_bookmark_menu()
        
        self.show_message("북마크에 추가되었습니다")
        
        # 북마크 저장
        self.save_bookmarks()
        
    def remove_bookmark(self):
        """현재 이미지를 북마크에서 제거합니다."""
        if not hasattr(self, 'current_image_path') or not self.current_image_path:
            self.show_message("북마크 제거할 이미지가 없습니다")
            return
            
        # 북마크에 있는지 확인
        if self.current_image_path not in self.bookmarks:
            self.show_message("북마크에 없는 이미지입니다")
            return
            
        # 북마크 제거
        self.bookmarks.remove(self.current_image_path)
        
        # 북마크 버튼 상태 업데이트
        self.update_bookmark_button_state()
        
        # 북마크 메뉴 업데이트
        self.update_bookmark_menu()
        
        self.show_message("북마크에서 제거되었습니다")
        
        # 북마크 저장
        self.save_bookmarks()

    def save_bookmarks(self):
        """북마크 정보를 JSON 파일로 저장합니다."""
        try:
            # 앱 데이터 폴더 확인 및 생성
            app_data_dir = get_user_data_directory()
            if not os.path.exists(app_data_dir):
                os.makedirs(app_data_dir)
                
            # 북마크 파일 저장 경로
            bookmarks_file = os.path.join(app_data_dir, "bookmarks.json")
            
            # 현재 북마크 목록을 JSON으로 저장
            with open(bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=4)
                
            # 디버깅용 메시지 (실제 사용 시 제거)
            print(f"북마크가 저장되었습니다: {bookmarks_file}")
        except Exception as e:
            print(f"북마크 저장 중 오류 발생: {e}")
    
    def load_bookmarks(self):
        """JSON 파일에서 북마크 정보를 불러옵니다."""
        try:
            # 앱 데이터 폴더 경로
            app_data_dir = get_user_data_directory()
            bookmarks_file = os.path.join(app_data_dir, "bookmarks.json")
            
            # 파일이 존재하면 불러오기
            if os.path.exists(bookmarks_file):
                with open(bookmarks_file, 'r', encoding='utf-8') as f:
                    loaded_bookmarks = json.load(f)
                    
                # 북마크 중 존재하는 파일만 리스트에 추가
                valid_bookmarks = []
                for bookmark in loaded_bookmarks:
                    if os.path.exists(bookmark):
                        valid_bookmarks.append(bookmark)
                
                # 유효한 북마크만 설정
                self.bookmarks = valid_bookmarks
                
                # 디버깅용 메시지 (실제 사용 시 제거)
                print(f"북마크 {len(self.bookmarks)}개가 로드되었습니다")
        except Exception as e:
            print(f"북마크 불러오기 중 오류 발생: {e}")
            # 오류 발생 시 빈 리스트로 초기화
            self.bookmarks = []

    def show_bookmark_menu_above(self):
        """북마크 메뉴를 버튼 위에 표시"""
        if self.bookmark_menu:
            # 메뉴를 표시하기 전에 업데이트하여 크기를 정확히 계산
            self.update_bookmark_menu()
            
            # 버튼 좌표를 전역 좌표로 변환
            pos = self.slider_bookmark_btn.mapToGlobal(QPoint(0, 0))
            
            # 메뉴 사이즈 계산
            menu_width = self.bookmark_menu.sizeHint().width()
            button_width = self.slider_bookmark_btn.width()
            
            # 최대 높이 설정
            desktop = QApplication.desktop().availableGeometry()
            max_height = min(800, desktop.height() * 0.8)  # 화면 높이의 80%까지 사용
            self.bookmark_menu.setMaximumHeight(int(max_height))
            
            # 메뉴 높이가 화면 높이보다 크면 화면의 80%로 제한
            menu_height = min(self.bookmark_menu.sizeHint().height(), max_height)
            
            # 화면 정보 가져오기
            desktop = QApplication.desktop().availableGeometry()
            
            # 기준을 버튼의 오른쪽 변으로 설정 (메뉴의 오른쪽 가장자리를 버튼의 오른쪽 가장자리에 맞춤)
            button_right_edge = pos.x() + button_width
            x_pos = button_right_edge - menu_width  # 메뉴의 오른쪽 끝이 버튼의 오른쪽 끝과 일치하도록 계산
            y_pos = pos.y() - menu_height  # 버튼 위에 메뉴가 나타나도록 설정
            
            # 메뉴가 화면 왼쪽 경계를 벗어나는지 확인
            if x_pos < desktop.left():
                x_pos = desktop.left()
            
            # 메뉴가 화면 위로 넘어가지 않도록 조정
            if y_pos < desktop.top():
                # 화면 위로 넘어가면 버튼 아래에 표시
                y_pos = pos.y() + self.slider_bookmark_btn.height()
            
            # 메뉴가 화면 아래로 넘어가지 않도록 조정
            if y_pos + menu_height > desktop.bottom():
                # 화면 아래로 넘어가면 버튼 위에 표시하되, 필요한 만큼만 위로 올림
                y_pos = desktop.bottom() - menu_height
            
            # 메뉴 팝업 (스크롤이 필요한 경우를 위해 높이 속성 명시적 설정)
            self.bookmark_menu.setProperty("_q_scrollable", True)
            self.bookmark_menu.popup(QPoint(x_pos, y_pos))
    
    def show_menu_above(self):
        """메뉴 버튼 위에 드롭업 메뉴를 표시합니다."""
        # 메뉴가 없으면 생성
        if not self.dropdown_menu:
            self.dropdown_menu = ScrollableMenu(self)
            
            # 키 설정 메뉴 항목
            key_settings_action = QAction("환경 설정", self)
            key_settings_action.triggered.connect(self.show_key_settings_dialog)
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
                # PSD 파일은 다시 로드
                self.show_psd(self.current_image_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif', '.webp']:
                # 일반 이미지는 캐시에서 다시 가져오거나 새로 로드
                if file_ext == '.webp':
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
                else:
                    # 다른 일반 이미지 처리
                    cached_pixmap = self.image_cache.get(self.current_image_path)
                    if cached_pixmap is not None:
                        # 캐시에서 원본을 가져와서 현재 회전 각도를 직접 적용
                        original_pixmap = cached_pixmap
                        transform = QTransform().rotate(self.current_rotation)
                        rotated_pixmap = original_pixmap.transformed(transform, Qt.SmoothTransformation)
                        
                        # 회전된 이미지를 화면에 맞게 크기 조절
                        label_size = self.image_label.size()
                        scaled_pixmap = rotated_pixmap.scaled(
                            label_size,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.image_label.setPixmap(scaled_pixmap)
                        print(f"캐시된 이미지 회전 적용: {self.current_rotation}°")
                    else:
                        # 캐시에 없으면 이미지를 다시 로드 (로더 스레드에서 회전 적용됨)
                        # 현재 경로를 다시 로드 - on_image_loaded에서 회전 적용
                        self.show_image(self.current_image_path)
                
        elif self.current_media_type in ['gif', 'webp', 'webp_animation']:
            # 애니메이션 회전을 위한 더 안전한 방법 구현
            try:
                if hasattr(self, 'current_movie') and self.current_movie:
                    # 현재 재생 상태 및 프레임 기억
                    was_playing = self.current_movie.state() == QMovie.Running
                    current_frame = self.current_movie.currentFrameNumber()
                    
                    # 재로드 방식으로 처리
                    if self.current_media_type == 'gif':
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
                if self.current_media_type == 'gif':
                    self.show_gif(self.current_image_path)
                else:
                    self.show_webp(self.current_image_path)
                return
        
        elif self.current_media_type == 'video':
            # 비디오 회전 처리
            try:
                if hasattr(self, 'player') and self.player:
                    # MPV의 video-rotate 속성 설정
                    # MPV에서는 회전 각도가 0, 90, 180, 270도만 지원됨
                    self.player['video-rotate'] = str(self.current_rotation)
                    print(f"비디오 회전 적용: {self.current_rotation}°")
            except Exception as e:
                self.show_message(f"비디오 회전 중 오류 발생: {str(e)}")
                return
        
        # 회전 상태 메시지 표시
        if self.current_media_type == 'video':
            self.show_message(f"비디오 회전: {self.current_rotation}°")
        elif self.current_media_type in ['gif', 'webp', 'webp_animation']:
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
            app_data_dir = get_user_data_directory()
            settings_path = os.path.join(app_data_dir, "key_settings.json")
            
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
            
            # 파일이 존재하면 로드
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    
                    # 문자열로 저장된 키 값을 정수로 변환
                    for key, value in loaded_settings.items():
                        if key in default_settings:
                            default_settings[key] = int(value)
            
            # 로드된 설정을 self.key_settings에 직접 할당
            self.key_settings = default_settings
            print(f"키 설정 로드 완료: {settings_path}")
            
        except Exception as e:
            print(f"키 설정 로드 오류: {e}")
            return default_settings

    def save_key_settings(self):
        """키 설정을 JSON 파일로 저장합니다."""
        try:
            # 앱 데이터 폴더 확인 및 생성
            app_data_dir = get_user_data_directory()
            if not os.path.exists(app_data_dir):
                os.makedirs(app_data_dir)
                
            # 키 설정 파일 저장 경로
            settings_file = os.path.join(app_data_dir, "key_settings.json")
            
            # 현재 키 설정을 JSON으로 저장
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.key_settings, f, ensure_ascii=False, indent=4)
                
            print(f"키 설정이 저장되었습니다: {settings_file}")
        except Exception as e:
            print(f"키 설정 저장 오류: {e}")
    
    def show_key_settings_dialog(self):
        # 키 설정 다이얼로그 표시
        dialog = KeySettingDialog(self, self.key_settings)
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

class AboutDialog(QDialog):
    """프로그램 정보를 표시하는 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("프로그램 정보")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # 레이아웃 설정
        layout = QVBoxLayout(self)
        
        # 프로그램 제목
        title_label = QLabel("이미지 뷰어")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2980b9;")
        layout.addWidget(title_label)
        
        # 버전 정보
        version_label = QLabel("버전: 1.1.0 (빌드 날짜: 2025-03-12)")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 스크롤 영역 추가
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 프로그램 설명
        description = QLabel(
            "이 프로그램은 다양한 이미지 형식과 비디오를 볼 수 있는 고성능 뷰어입니다."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignLeft)
        description.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(description)
        
        # 지원 형식
        formats_label = QLabel("<b>지원하는 형식:</b>")
        formats_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(formats_label)
        
        formats_detail = QLabel(
            "• 이미지: JPG, PNG, GIF, WEBP, BMP, TIFF, ICO, PSD 등\n"
            "• 비디오: MP4, AVI, MKV, MOV, WMV 등\n"
            "• 애니메이션: GIF, WEBP"
        )
        formats_detail.setStyleSheet("margin-left: 15px;")
        formats_detail.setWordWrap(True)
        scroll_layout.addWidget(formats_detail)
        
        # 주요 기능
        features_label = QLabel("<b>주요 기능:</b>")
        features_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(features_label)
        
        features_detail = QLabel(
            "• 다양한 이미지 및 비디오 형식 지원\n"
            "• 이미지 확대/축소 및 회전\n"
            "• 북마크 기능으로 자주 사용하는 파일 즐겨찾기\n"
            "• 사용자 정의 키보드 단축키 설정\n"
            "• 애니메이션 GIF 및 WEBP 재생 제어\n"
            "• 비디오 재생 및 제어\n"
            "• 파일 복사 및 관리 기능\n"
            "• 빠른 폴더 탐색 및 이동"
        )
        features_detail.setStyleSheet("margin-left: 15px;")
        features_detail.setWordWrap(True)
        scroll_layout.addWidget(features_detail)
        
        # 사용된 라이브러리
        libs_label = QLabel("<b>사용된 주요 라이브러리:</b>")
        libs_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(libs_label)
        
        libs_detail = QLabel(
            "• PyQt5 - GUI 프레임워크\n"
            "• OpenCV (cv2) - 비디오 및 이미지 처리\n"
            "• Pillow (PIL) - 이미지 처리 및 변환\n"
            "• JSON - 설정 저장 및 불러오기"
        )
        libs_detail.setStyleSheet("margin-left: 15px;")
        libs_detail.setWordWrap(True)
        scroll_layout.addWidget(libs_detail)
        
        # 개발자 정보
        developer_label = QLabel("<b>개발:</b>")
        developer_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(developer_label)
        
        developer_detail = QLabel("htpaak@gmail.com")
        developer_detail.setStyleSheet("margin-left: 15px;")
        developer_detail.setWordWrap(True)
        scroll_layout.addWidget(developer_detail)
        
        # 저작권 정보
        copyright_label = QLabel("<b>저작권:</b>")
        copyright_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(copyright_label)
        
        copyright_detail = QLabel("© 2025 저작권 소유자. 모든 권리 보유.")
        copyright_detail.setStyleSheet("margin-left: 15px;")
        copyright_detail.setWordWrap(True)
        scroll_layout.addWidget(copyright_detail)
        
        # 스페이서 추가
        scroll_layout.addStretch()
        
        # 스크롤 영역에 위젯 설정
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # 확인 버튼
        ok_button = QPushButton("확인")
        ok_button.setFixedWidth(100)
        ok_button.clicked.connect(self.accept)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)


class KeySettingDialog(QDialog):
    """키 설정을 변경할 수 있는 다이얼로그"""
    
    def __init__(self, parent=None, key_settings=None):
        super().__init__(parent)
        self.setWindowTitle("키 설정")
        self.setMinimumWidth(900)

        self.setMinimumHeight(600)
        
        # 기본 키 설정 정의
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
        
        # 전달받은 키 설정이 있으면 사용, 없으면 기본값 사용
        self.key_settings = key_settings.copy() if key_settings else default_settings.copy()

        # 누락된 키가 있으면 기본값에서 추가
        for key, value in default_settings.items():
            if key not in self.key_settings:
                self.key_settings[key] = value
        
        # 키 이름 매핑은 그대로 유지
        self.key_names = {
            "play_pause": "재생/일시정지",
            "next_image": "다음 이미지",
            "prev_image": "이전 이미지",
            "rotate_clockwise": "시계 방향 회전",
            "rotate_counterclockwise": "반시계 방향 회전",
            "volume_up": "볼륨 증가",
            "volume_down": "볼륨 감소",
            "toggle_mute": "음소거 토글",
            "delete_image": "이미지 삭제",
            "toggle_fullscreen": "전체화면 전환",
            "toggle_maximize_state": "최대화 전환"  # 추가
        }
        
        # 메인 레이아웃 - 수평 레이아웃으로 변경
        main_layout = QHBoxLayout(self)

        # 왼쪽 버튼 패널 생성
        left_panel = QVBoxLayout()

        # 버튼 스타일 설정
        button_style = """
            QPushButton {
                text-align: left;
                padding: 10px;
                border: none;
                background-color: rgba(52, 73, 94, 0.8);
                min-height: 40px;
                font-size: 10pt;
                color: rgb(255, 255, 255, 1.0);
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
            QPushButton:pressed {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """

        # 왼쪽 패널 버튼들 생성
        button_names = ["일반", "보기", "영상 처리", "확장자", "키보드", "마우스", "책갈피", "탐색기 메뉴", "기타"]
        self.left_buttons = []

        for name in button_names:
            button = QPushButton(name)
            button.setStyleSheet(button_style)
            button.setMinimumWidth(150)
            left_panel.addWidget(button)
            self.left_buttons.append(button)

        # 왼쪽 패널에 공간 추가
        left_panel.addStretch()

        # 왼쪽 패널을 메인 레이아웃에 추가
        left_panel_widget = QWidget()
        left_panel_widget.setLayout(left_panel)
        left_panel_widget.setMaximumWidth(200)
        main_layout.addWidget(left_panel_widget)

        # 오른쪽 패널 (기존 테이블과 버튼) 생성
        right_panel = QVBoxLayout()

        # 설명 레이블
        label = QLabel("단축키를 변경하려면 해당 행을 클릭한 후 원하는 키를 누르세요.")
        label.setWordWrap(True)
        right_panel.addWidget(label)
        
        # 테이블 생성 및 설정
        self.table = QTableWidget(len(self.key_settings), 2)
        self.table.setHorizontalHeaderLabels(["기능", "단축키"])
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        
        # 키 설정 테이블에 데이터 추가 부분을 찾으세요 (약 4180 라인 주변)
        for i, (key, value) in enumerate(self.key_settings.items()):
            # 기능 이름 설정
            name_item = QTableWidgetItem(self.key_names.get(key, key))
            self.table.setItem(i, 0, name_item)
            
            # 키 이름 설정 - 모디파이어 처리 추가
            key_text = ""
            # 키가 모디파이어를 포함하는지 확인
            if isinstance(value, int) and value & Qt.ControlModifier:
                key_text = "Ctrl+"
                # 모디파이어를 제거하고 실제 키 값만 추출
                actual_key = value & ~(int(Qt.ControlModifier) | int(Qt.AltModifier) | int(Qt.ShiftModifier))
                # Qt.Key_Return은 "Enter"로 표시
                if actual_key == Qt.Key_Return:
                    key_text += "Enter"
                else:
                    key_text += QKeySequence(actual_key).toString()
            else:
                # Qt.Key_Return은 "Enter"로 표시
                if value == Qt.Key_Return:
                    key_text = "Enter"
                else:
                    key_text = QKeySequence(value).toString()
            
            key_item = QTableWidgetItem(key_text)
            self.table.setItem(i, 1, key_item)
        
        # 테이블 행 높이 설정
        for i in range(self.table.rowCount()):
            self.table.setRowHeight(i, 30)
        
        right_panel.addWidget(self.table)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 기본값 버튼
        default_button = QPushButton("기본값으로 복원")
        default_button.clicked.connect(self.reset_to_default)
        button_layout.addWidget(default_button)
        
        # 스페이서 추가
        button_layout.addStretch()
        
        # 확인 및 취소 버튼
        ok_button = QPushButton("확인")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        right_panel.addLayout(button_layout)

        # 오른쪽 패널을 메인 레이아웃에 추가
        right_panel_widget = QWidget()
        right_panel_widget.setLayout(right_panel)
        main_layout.addWidget(right_panel_widget)
        
        # 테이블 셀 클릭 이벤트 연결
        self.table.cellClicked.connect(self.cell_clicked)

        # 키보드 버튼을 기본적으로 선택된 상태로 설정
        self.left_buttons[4].setStyleSheet(button_style + "QPushButton { background-color: rgba(52, 73, 94, 1.0); }")
        
        # 현재 편집 중인 셀
        self.current_edit_row = -1
        self.current_edit_col = -1
        
        # 키 입력 이벤트 필터 설치
        self.table.installEventFilter(self)
    
    def cell_clicked(self, row, col):
        if col == 1:  # 단축키 열을 클릭한 경우
            # 선택된 기능 이름 가져오기
            function_name = self.table.item(row, 0).text()
            
            # key_names 딕셔너리에서 실제 키 이름 찾기
            actual_key = None
            for k, v in self.key_names.items():
                if v == function_name:
                    actual_key = k
                    break
            
            if actual_key:
                # 키 입력 다이얼로그 표시
                dialog = QDialog(self)
                dialog.setWindowTitle("단축키 입력")
                dialog.setFixedSize(300, 150)
                
                layout = QVBoxLayout(dialog)
                label = QLabel("새 단축키를 입력하세요.\n모디파이어(Ctrl, Alt, Shift)와 조합도 가능합니다.")
                layout.addWidget(label)
                
                # 키 입력을 위한 라인 에디트
                key_edit = KeyInputEdit()
                layout.addWidget(key_edit)
                
                # 버튼
                button_layout = QHBoxLayout()
                ok_button = QPushButton("확인")
                cancel_button = QPushButton("취소")
                button_layout.addWidget(ok_button)
                button_layout.addWidget(cancel_button)
                layout.addLayout(button_layout)
                
                # 버튼 이벤트 연결
                ok_button.clicked.connect(dialog.accept)
                cancel_button.clicked.connect(dialog.reject)
                
                # 다이얼로그 실행
                if dialog.exec_() == QDialog.Accepted and key_edit.key_value:
                    # 테이블 업데이트
                    key_text = key_edit.text()
                    self.table.setItem(row, 1, QTableWidgetItem(key_text))
                    
                    # 키 설정 업데이트
                    self.key_settings[actual_key] = key_edit.key_value
    
    def eventFilter(self, obj, event):
        """이벤트 필터 - 키 입력 처리"""
        if (obj == self.table and event.type() == QEvent.KeyPress and 
            self.current_edit_row >= 0 and self.current_edit_col == 1):
            
            # ESC 키는 편집 취소
            if event.key() == Qt.Key_Escape:
                # 원래 값으로 복원
                original_key = self.table.item(self.current_edit_row, 1).data(Qt.UserRole)
                self.table.item(self.current_edit_row, 1).setText(QKeySequence(original_key).toString())
                self.current_edit_row = -1
                self.current_edit_col = -1
                return True
            
            # 다음 키들은 허용하지 않음
            if event.key() in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]:
                return True
                
            # 키 이름 가져오기
            key_name = ""
            if event.key() == Qt.Key_Return:
                key_name = "Enter"
            else:
                key_name = QKeySequence(event.key()).toString()
            
            # 빈 문자열이 아닌 경우에만 처리 (유효한 키인 경우)
            if key_name:
                # 키 설정 업데이트
                key_action = list(self.key_settings.keys())[self.current_edit_row]
                self.key_settings[key_action] = event.key()
                
                # 테이블 업데이트
                self.table.item(self.current_edit_row, 1).setText(key_name)
                self.table.item(self.current_edit_row, 1).setData(Qt.UserRole, event.key())
                
                # 편집 모드 종료
                self.current_edit_row = -1
                self.current_edit_col = -1
                return True
        
        return super().eventFilter(obj, event)
    
    def reset_to_default(self):
        # 기본 키 설정 정의
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
        
        # 테이블 업데이트 (이 부분이 누락된 것 같습니다)
        for i, (key, value) in enumerate(default_settings.items()):
            if i < self.table.rowCount():  # 테이블 행 범위 내인지 확인
                # 키 이름 설정image.png
                key_text = ""
                if isinstance(value, int) and value & Qt.ControlModifier:
                    key_text = "Ctrl+"
                    # 모디파이어를 제거하고 실제 키 값만 추출
                    actual_key = value & ~(Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier)
                    # Qt.Key_Return은 "Enter"로 표시
                    if actual_key == Qt.Key_Return:
                        key_text += "Enter"
                    else:
                        key_text += QKeySequence(actual_key).toString()
                else:
                    # Qt.Key_Return은 "Enter"로 표시
                    if value == Qt.Key_Return:
                        key_text = "Enter"
                    else:
                        key_text = QKeySequence(value).toString()
                
                key_item = QTableWidgetItem(key_text)
                self.table.setItem(i, 1, key_item)
                
        # 키 설정 업데이트
        self.key_settings = default_settings.copy()

    def get_key_settings(self):
        """현재 설정된 키 매핑을 반환합니다."""
        return self.key_settings
    


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

class KeyInputEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.key_value = None
        self.setReadOnly(True)
        self.setPlaceholderText("여기를 클릭하고 키를 누르세요")
        
    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        key = event.key()
        
        # ESC, Tab 등의 특수 키는 무시
        if key in (Qt.Key_Escape, Qt.Key_Tab):
            return
        
        # 모디파이어만 눌렀을 때는 처리하지 않음
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        
        # 키 조합 생성
        self.key_value = key
        if modifiers & Qt.ControlModifier:
            self.key_value |= Qt.ControlModifier
        if modifiers & Qt.AltModifier:
            self.key_value |= Qt.AltModifier
        if modifiers & Qt.ShiftModifier:
            self.key_value |= Qt.ShiftModifier
        
        # 텍스트 표시
        text = ""
        if modifiers & Qt.ControlModifier:
            text += "Ctrl+"
        if modifiers & Qt.AltModifier:
            text += "Alt+"
        if modifiers & Qt.ShiftModifier:
            text += "Shift+"
        
        text += QKeySequence(key).toString()
        self.setText(text)
        
        # 이벤트 수락
        event.accept()

# 메인 함수
def main():
    app = QApplication(sys.argv)  # Qt 애플리케이션 객체 생성
    viewer = ImageViewer()  # ImageViewer 클래스의 객체 생성
    viewer.show()  # 뷰어 창 표시
    sys.exit(app.exec_())  # 이벤트 루프 실행

# 프로그램 실행 시 main() 함수 실행
if __name__ == "__main__":
    main()  # 메인 함수 실행