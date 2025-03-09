# 이미지 및 비디오 뷰어 애플리케이션 (PyQt5 기반)
import sys  # 시스템 관련 기능 제공 (프로그램 종료, 경로 관리 등)
import os  # 운영체제 관련 기능 제공 (파일 경로, 디렉토리 처리 등)
import shutil  # 파일 복사 및 이동 기능 제공 (고급 파일 작업)
import re  # 정규표현식 처리 기능 제공 (패턴 검색 및 문자열 처리)
import json  # JSON 파일 처리를 위한 모듈
from collections import OrderedDict  # LRU 캐시 구현을 위한 정렬된 딕셔너리
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout, QSizePolicy, QSlider, QLayout, QSpacerItem, QStyle, QStyleOptionSlider, QMenu, QAction, QScrollArea, QListWidgetItem, QListWidget, QAbstractItemView  # PyQt5 UI 위젯 (사용자 인터페이스 구성 요소)
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QFont, QMovie, QCursor, QIcon, QColor, QPalette, QFontMetrics  # 그래픽 요소 처리 (이미지, 폰트, 커서 등)
from PyQt5.QtCore import Qt, QSize, QTimer, QEvent, QPoint, pyqtSignal, QRect, QMetaObject, QObject, QUrl, QThread  # Qt 코어 기능 (이벤트, 신호, 타이머 등)
import cv2  # OpenCV 라이브러리 - 비디오 처리용 (프레임 추출, 이미지 변환 등)
from PIL import Image, ImageCms  # Pillow 라이브러리 - 이미지 처리용 (다양한 이미지 포맷 지원)
from io import BytesIO  # 바이트 데이터 처리용 (메모리 내 파일 스트림)
import time  # 시간 관련 기능 (시간 측정, 지연 등)

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
mpv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mpv')
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
        self.loading_timer = None  # 로딩 타임아웃 타이머
        
        # OpenCV 비디오 캡처 객체 초기화
        self.cap = None
        
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
        
        close_btn = QPushButton("×")  # 닫기 버튼
        close_btn.setStyleSheet("color: white; background: none; border: none; padding: 10px;")
        close_btn.clicked.connect(self.close)  # 닫기 기능 연결
        
        # 창 컨트롤 버튼들 레이아웃에 추가
        title_layout.addWidget(min_btn)
        title_layout.addWidget(max_btn)
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

        # MPV 상태 확인을 위한 타이머 설정 (주기적으로 재생 상태 업데이트)
        self.play_button_timer = QTimer(self)
        self.play_button_timer.timeout.connect(self.update_play_button)  # 타이머가 작동할 때마다 update_play_button 메소드 호출
        self.play_button_timer.start(100)  # 100ms마다 상태 확인 (초당 10번 업데이트)
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
        # 북마크 토글 기능 대신 위로 펼쳐지는 메뉴 표시 기능으로 변경
        self.slider_bookmark_btn.clicked.connect(self.show_bookmark_menu_above)
        new_slider_layout.addWidget(self.slider_bookmark_btn)

        # 새로운 슬라이더 위젯을 하단 레이아웃에 추가
        bottom_layout.addWidget(self.slider_widget, 0, Qt.AlignLeft | Qt.AlignTop)  # 좌측 정렬로 변경하여 최대한 넓게 표시
        
        # 중복된 슬라이더 위젯 할당 제거 (이미 위에서 self.slider_widget을 만들었음)
        # self.slider_widget = slider_widget

        # 슬라이더바와 폴더 버튼 사이에 20px의 빈 공간 추가 (색상 지정) - 제거
        # vertical_spacer = QWidget()
        # vertical_spacer.setFixedHeight(20)  # 높이를 20px로 고정
        # vertical_spacer.setStyleSheet("background-color: rgba(52, 73, 94, 0.9);")  # 색상 지정
        # bottom_layout.addWidget(vertical_spacer)

        # 폴더 버튼에 스타일 적용 (하위 폴더 선택용 버튼 그리드)
        self.buttons = []
        for _ in range(5):  # 4줄에서 5줄로 변경 (더 많은 폴더 버튼 표시)
            button_layout = QHBoxLayout()
            button_row = []
            for _ in range(20):  # 12개에서 20개로 변경 (버튼 수 증가)
                empty_button = QPushButton('')
                empty_button.setStyleSheet(button_style)
                empty_button.clicked.connect(self.on_button_click)  # 버튼 클릭 이벤트 연결 (이미지 복사 기능)
                button_row.append(empty_button)
                button_layout.addWidget(empty_button)
            self.buttons.append(button_row)
            bottom_layout.addLayout(button_layout)

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

        # MPV DLL 경로 설정 (동적 라이브러리 로드 경로)
        if getattr(sys, 'frozen', False):
            # PyInstaller로 패키징된 경우 (실행 파일 경로 기준)
            mpv_path = os.path.join(os.path.dirname(sys.executable), 'mpv')
            os.environ["MPV_DYLIB_PATH"] = os.path.join(mpv_path, "libmpv-2.dll")
        else:
            # 일반 스크립트로 실행되는 경우 (스크립트 경로 기준)
            mpv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mpv')
            os.environ["MPV_DYLIB_PATH"] = os.path.join(mpv_path, "libmpv-2.dll")

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

    def ensure_maximized(self):
        """창이 최대화 상태인지 확인하고 그렇지 않으면 다시 최대화합니다."""
        if not self.isMaximized():
            self.showMaximized()  # 최대화 상태가 아니면 최대화 적용

    def resizeEvent(self, event):
        """창 크기 변경 이벤트 처리 (창 크기 변경 시 UI 요소 조정)"""
        # 창 너비 구하기
        window_width = self.width()
        
        # 슬라이더 위젯의 너비를 창 너비와 동일하게 설정
        if hasattr(self, 'slider_widget'):
            self.slider_widget.setFixedWidth(window_width)
        
        if hasattr(self, 'title_bar'):
            self.title_bar.setGeometry(0, 0, self.width(), 30)  # 제목표시줄 위치와 크기 조정
            self.title_bar.raise_()  # 제목표시줄을 항상 맨 위로 유지
            
            # 제목표시줄의 버튼들 업데이트 (크기 변경에 맞춰 조정)
            for child in self.title_bar.children():
                if isinstance(child, QPushButton):
                    child.updateGeometry()  # 버튼 위치/크기 업데이트
                    child.update()  # 버튼의 시각적 상태도 업데이트
        
        # 현재 표시 중인 미디어 크기 조절 (화면 크기에 맞게 조정)
        if hasattr(self, 'current_image_path') and self.current_image_path:
            file_ext = os.path.splitext(self.current_image_path)[1].lower()  # 파일 확장자 확인 (소문자로 변환)
            
            if file_ext == '.psd':  # PSD 파일 처리 (Photoshop 이미지)
                try:
                    # 캐시된 이미지가 있으면 사용 (성능 최적화)
                    if self.current_image_path in self.psd_cache:
                        pixmap = self.psd_cache[self.current_image_path]
                    else:
                        # 캐시된 이미지가 없으면 변환 (PSD -> PNG)
                        from PIL import Image, ImageCms
                        from io import BytesIO
                        
                        # PSD 파일을 PIL Image로 열기
                        image = Image.open(self.current_image_path)
                        
                        # RGB 모드로 변환 (색상 모드 보정)
                        if image.mode != 'RGB':
                            image = image.convert('RGB')
                        
                        # ICC 프로파일 처리 (색상 프로파일 관리)
                        if 'icc_profile' in image.info:
                            try:
                                srgb_profile = ImageCms.createProfile('sRGB')  # sRGB 프로파일 생성
                                srgb_profile = ImageCms.createProfile('sRGB')
                                icc_profile = BytesIO(image.info['icc_profile'])
                                image = ImageCms.profileToProfile(
                                    image,
                                    ImageCms.ImageCmsProfile(icc_profile),
                                    ImageCms.ImageCmsProfile(srgb_profile),
                                    outputMode='RGB'
                                )
                            except Exception:
                                image = image.convert('RGB')
                        
                        # 변환된 이미지를 캐시에 저장
                        buffer = BytesIO()
                        image.save(buffer, format='PNG', icc_profile=None)
                        pixmap = QPixmap()
                        pixmap.loadFromData(buffer.getvalue())
                        buffer.close()
                        
                        # 캐시 크기 관리
                        if len(self.psd_cache) >= self.max_psd_cache_size:
                            # 가장 오래된 항목 제거 (캐시 크기 관리)
                            self.psd_cache.pop(next(iter(self.psd_cache)))
                        self.psd_cache[self.current_image_path] = pixmap  # 현재 이미지를 캐시에 저장
                    
                    # 이미지가 정상적으로 로드된 경우 화면에 표시
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.image_label.setPixmap(scaled_pixmap)  # 크기 조정된 이미지 표시

                except Exception as e:
                    pass  # 예외 발생 시 무시
            
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif']:  # JPG, JPEG, PNG 파일 처리
                pixmap = QPixmap(self.current_image_path)  # 이미지 로드
                if not pixmap.isNull():  # 이미지가 정상적으로 로드되었는지 확인
                    scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)  # 비율 유지하며 크기 조정
                    self.image_label.setPixmap(scaled_pixmap)  # 화면에 표시
            
            elif file_ext == '.webp':  # WebP 이미지/애니메이션 처리
                if hasattr(self, 'current_movie') and self.current_movie:  # 애니메이션 WebP인 경우
                    # 현재 프레임 정보 저장
                    current_frame = self.current_movie.currentFrameNumber()
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
                else:  # 정적 WebP 이미지인 경우
                    # 일반 이미지처럼 처리
                    pixmap = QPixmap(self.current_image_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.image_label.setPixmap(scaled_pixmap)
            
            elif file_ext in ['.gif', '.webp']:  # GIF/WebP 애니메이션 공통 처리
                if hasattr(self, 'current_movie'):  # 애니메이션 객체가 있는 경우
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
            
            elif file_ext in ['.mp4', '.avi', '.wmv', '.ts', '.m2ts', '.mov', '.qt', '.mkv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', '.vob', '.wav', '.flac', '.mp3', '.aac', '.m4a', '.ogg']:  # 모든 비디오/오디오 미디어 파일
                # MPV 플레이어를 사용하는 경우 윈도우 ID 업데이트
                if hasattr(self, 'player'):
                    # MPV 플레이어의 출력 윈도우 ID 설정 (이미지 라벨에 맞춤)
                    self.player.wid = int(self.image_label.winId())
        
        # 버튼 크기 계산 및 조정
        if hasattr(self, 'buttons') and hasattr(self, 'base_folder') and self.base_folder:
            button_width = self.width() // 20  # 창 너비를 20등분
            
            # 하위 폴더 목록 다시 가져오기
            def natural_keys(text):
                import re
                def atoi(text):
                    return int(text) if text.isdigit() else text
                return [atoi(c) for c in re.split('([0-9]+)', text)]

            subfolders = [f.path for f in os.scandir(self.base_folder) if f.is_dir()]
            subfolders.sort(key=lambda x: natural_keys(os.path.basename(x).lower()))

            # 각 버튼의 텍스트 업데이트
            for i, row in enumerate(self.buttons):
                for j, button in enumerate(row):
                    button.setFixedWidth(button_width)
                    index = i * 20 + j
                    if index < len(subfolders):
                        folder_name = os.path.basename(subfolders[index])
                        # 버튼의 실제 사용 가능한 너비 계산 (패딩 고려)
                        available_width = button_width - 16  # 좌우 패딩 8px씩 제외
                        
                        # QFontMetrics를 사용하여 텍스트 너비 계산
                        font_metrics = button.fontMetrics()
                        text_width = font_metrics.horizontalAdvance(folder_name)
                        
                        # 텍스트가 버튼 너비를 초과하면 자동으로 줄임
                        if text_width > available_width:
                            # 적절한 길이를 찾을 때까지 텍스트 줄임
                            for k in range(len(folder_name), 0, -1):
                                truncated = folder_name[:k] + ".."
                                if font_metrics.horizontalAdvance(truncated) <= available_width:
                                    button.setText(truncated)
                                    button.setToolTip(subfolders[index])  # 전체 경로는 툴큐로
                                    break
                        else:
                            button.setText(folder_name)  # 원래 폴더명으로 복원
        
        # 이미지 정보 레이블 업데이트
        if hasattr(self, 'image_info_label') and self.image_files:
            self.update_image_info()
            
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

        # 볼륨 슬라이더 크기 조정
        if hasattr(self, 'volume_slider'):
            window_width = self.width()
            # 볼륨 슬라이더 너비를 창 크기에 따라 가변적으로 조정
            vol_width = max(40, min(150, int(window_width * 0.08)))  # 최소 40px, 최대 150px, 기본 8%
            self.volume_slider.setFixedWidth(vol_width)
        
        # 재생 슬라이더 크기 조정
        if hasattr(self, 'playback_slider'):
            window_width = self.width()
            # 작은 창에서도 작동하도록 최소 너비를 더 작게 조정
            min_width = max(100, int(window_width * 0.45))  # 최소 100px, 기본 창 너비의 45%
            max_width = int(window_width * 0.85)  # 최대 창 너비의 85%
            self.playback_slider.setMinimumWidth(min_width)
            self.playback_slider.setMaximumWidth(max_width)
            
        # 슬라이더바 내 버튼들 크기 조정
        window_width = self.width()
        
        # 슬라이더 위젯 자체의 패딩 조정
        if hasattr(self, 'slider_widget'):
            # 패딩을 창 크기에 비례하게 설정
            padding = max(5, min(15, int(window_width * 0.01)))  # 창 너비의 1%, 최소 5px, 최대 15px
            self.slider_widget.setStyleSheet(f"background-color: rgba(52, 73, 94, 0.9); padding: {padding}px;")
            
            # 내부 레이아웃의 여백과 간격도 조정
            layout = self.slider_widget.layout()
            if layout:
                layout.setContentsMargins(padding, padding, padding, padding)
                spacing = max(4, min(12, int(window_width * 0.008)))  # 창 너비의 0.8%, 최소 4px, 최대 12px
                layout.setSpacing(spacing)
                
                # 좌우 여백(Spacer) 크기 조정
                spacer_width = max(5, min(20, int(window_width * 0.01)))  # 창 너비의 1%, 최소 5px, 최대 20px
                
                # 레이아웃의 첫 번째와 마지막 아이템이 spacer인지 확인
                if layout.count() > 0:
                    first_item = layout.itemAt(0)
                    if isinstance(first_item, QSpacerItem):
                        # 새로운 스페이서로 대체
                        layout.removeItem(first_item)
                        new_left_spacer = QSpacerItem(spacer_width, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
                        layout.insertItem(0, new_left_spacer)
                    
                    last_item = layout.itemAt(layout.count() - 1)
                    if isinstance(last_item, QSpacerItem):
                        # 새로운 스페이서로 대체
                        layout.removeItem(last_item)
                        new_right_spacer = QSpacerItem(spacer_width, 10, QSizePolicy.Fixed, QSizePolicy.Minimum)
                        layout.insertItem(layout.count(), new_right_spacer)
        
        # 1. 버튼 크기 계산 (창 너비의 일정 비율)
        button_width = max(50, min(150, int(window_width * 0.06)))  # 창 너비의 6%, 최소 50px, 최대 150px
        button_height = max(25, min(45, int(button_width * 0.5)))   # 버튼 너비의 50%, 최소 25px, 최대 45px
        
        # 2. 버튼별 가중치 설정 (각 버튼마다 상대적 크기 조정)
        button_config = {
            'slider_bookmark_btn': 0.7,      # 북마크 버튼 (★) - 아이콘 버튼
            'open_button': 1.0,              # 열기 버튼
            'set_base_folder_button': 1.0,   # 폴더 설정 버튼
            'play_button': 0.7,              # 재생 버튼 (▶) - 아이콘 버튼
            'mute_button': 0.7,              # 음소거 버튼 (🔈) - 아이콘 버튼
            'menu_button': 0.7,              # 메뉴 버튼 (☰) - 아이콘 버튼
        }
        
        # 버튼들 크기 조정 적용
        for button_name, weight in button_config.items():
            if hasattr(self, button_name):
                button = getattr(self, button_name)
                # 가중치를 적용한 버튼 크기 계산
                adjusted_width = int(button_width * weight)
                button.setFixedSize(adjusted_width, button_height)
                
                # 폰트 크기도 창 크기에 맞게 조정 (버튼 크기의 비율로 설정)
                font_size = max(9, min(16, int(adjusted_width * 0.40)))  # 버튼 너비의 40%, 최소 9px, 최대 16px (버튼과 동일한 비율)
                
                # 버튼 스타일시트 업데이트 (폰트 크기 포함)
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba(52, 73, 94, 0.6);
                        color: white;
                        border: none;
                        padding: 5px;
                        border-radius: 3px;
                        font-size: {font_size}px;
                    }}
                    QPushButton:hover {{
                        background-color: rgba(52, 73, 94, 1.0);
                    }}
                """)
                
                # 북마크 버튼이 활성화 되어 있으면 스타일 유지
                if button_name == 'slider_bookmark_btn' and self.current_image_path in self.bookmarks:
                    button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: rgba(241, 196, 15, 0.9);
                            color: white;
                            border: none;
                            padding: 5px;
                            border-radius: 3px;
                            font-size: {font_size}px;
                        }}
                        QPushButton:hover {{
                            background-color: rgba(241, 196, 15, 1.0);
                        }}
                    """)
        
        # 이미지 컨테이너 레이아웃 강제 업데이트
        if hasattr(self, 'image_container'):
            self.image_container.updateGeometry()
        
        # 모든 버튼의 레이아웃 업데이트
        for row in self.buttons:
            for button in row:
                button.updateGeometry()
        
        # 슬라이더 위젯 레이아웃 업데이트
        if hasattr(self, 'playback_slider'):
            self.playback_slider.updateGeometry()
        if hasattr(self, 'volume_slider'):
            self.volume_slider.updateGeometry()
        
        # 전체 레이아웃 강제 업데이트
        self.updateGeometry()
        self.layout().update()
        
        # 부모 클래스의 resizeEvent 호출
        super().resizeEvent(event)

    def mouseDoubleClickEvent(self, event):
        """더블 클릭 시 최대화/일반 창 상태 전환"""
        if self.isMaximized():
            self.showNormal()  # 최대화 상태면 일반 크기로 복원
        else:
            self.showMaximized()  # 일반 상태면 최대화

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
                    button.setVisible(False)  # 모든 버튼 숨기기

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

            # 필요한 버튼 수를 계산하고 최적화
            max_buttons_per_row = 20
            max_rows = 5
            total_buttons_needed = min(len(subfolders), max_buttons_per_row * max_rows)
            
            # 폴더 버튼 업데이트
            button_index = 0
            for i, row in enumerate(self.buttons):
                for j, button in enumerate(row):
                    index = i * max_buttons_per_row + j  # 버튼 인덱스 계산
                    if index < total_buttons_needed:  # 유효한 폴더가 있는 경우만 버튼 표시
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
                            button.setText(folder_name)  # 원본 폴더명 표시
                            button.setToolTip(subfolders[index])  # 툴팁으로 전체 경로 표시
                        
                        button.setVisible(True)  # 버튼 표시
                        button_index += 1
                    else:
                        button.setVisible(False)  # 불필요한 버튼 숨기기

    def on_button_click(self):
        """하위 폴더 버튼 클릭 처리 - 현재 이미지를 선택된 폴더로 복사"""
        button = self.sender()  # 클릭된 버튼 객체 참조
        folder_path = button.toolTip()  # 버튼 툴팁에서 폴더 경로 가져오기
        print(f"Selected folder: {folder_path}")  # 선택된 폴더 경로 출력

        # 커서를 일반 모양으로 복원
        QApplication.restoreOverrideCursor()  # 모래시계에서 일반 커서로 복원

        # 현재 이미지를 선택된 폴더로 복사
        self.copy_image_to_folder(folder_path)

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
        if hasattr(self, 'current_movie') and self.current_movie:
            self.current_movie.stop()
            self.current_movie.deleteLater()  # Qt 객체 명시적 삭제 요청
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
            self.show_psd(image_path)  # PSD를 표시하는 메서드 호출
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
                # 이미지 바로 표시
                self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
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
        elif file_ext == '.webp':  # WEBP 파일 처리
            self.current_media_type = 'webp'  # 미디어 타입 업데이트
            self.show_webp(image_path)  # WEBP 애니메이션 처리
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
        # LRUCache에서 캐시된 이미지 확인
        pixmap = self.psd_cache.get(image_path)
        
        if pixmap is not None:
            # 캐시에서 찾은 경우 바로 사용
            print(f"PSD 캐시 히트: {os.path.basename(image_path)}")
            # 이미지 바로 표시
            scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            # 로딩 중 표시
            self.show_loading_indicator()
            
            # 기존 스레드 정리
            self.cleanup_loader_threads()
            
            # 비동기 로딩 시작
            loader = ImageLoaderThread(image_path, 'psd')
            loader.loaded.connect(self.on_image_loaded)
            loader.error.connect(self.on_image_error)
            
            # 스레드 추적
            self.loader_threads[image_path] = loader
            loader.start()

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
            self.scale_gif()
            self.image_label.setMovie(self.current_movie)

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

                # 타이머를 사용하여 슬라이더 업데이트
                self.gif_timer = QTimer(self)
                self.gif_timer.timeout.connect(update_slider)
                self.gif_timer.start(50)  # 50ms마다 슬라이더 업데이트
                self.timers.append(self.gif_timer)  # 타이머 추적에 추가

                # 항상 재생 상태로 시작하도록 명시적으로 설정
                self.current_movie.start()
                self.current_movie.setPaused(False)  # 일시정지 상태 해제
                # 재생 버튼 상태 업데이트
                self.play_button.setText("❚❚")  # 재생 중이므로 일시정지 아이콘 표시
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
            self.scale_webp()
            self.image_label.setMovie(self.current_movie)

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
                self.gif_timer.start(50)  # 50ms마다 업데이트 (약 20fps)
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
            # 애니메이션을 지원하지 않는 일반 WebP 이미지 처리
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

    def scale_webp(self):
        """WebP 애니메이션 크기를 화면에 맞게 조정하는 메서드"""
        # 첫 번째 프레임으로 이동하여 이미지 데이터 가져오기
        self.current_movie.jumpToFrame(0)  # 첫 번째 프레임으로 이동
        image = self.current_movie.currentImage()  # 현재 프레임 이미지 가져오기

        # 원본 이미지 크기 정보
        original_width = image.width()  # 원본 너비
        original_height = image.height()  # 원본 높이

        # 높이가 0인 경우 예외 처리 (0으로 나누기 방지)
        if original_height == 0:
            original_height = 1  # 높이를 1로 설정
            
        # 원본 화면 비율 계산 (가로/세로)
        aspect_ratio = original_width / original_height

        # 이미지가 표시될 라벨의 크기를 얻습니다.
        label_width = self.image_label.width()  # 라벨의 너비
        label_height = self.image_label.height()  # 라벨의 높이

        # 원본 비율을 유지하며, 라벨의 크기에 맞는 새로운 크기를 계산합니다.
        if label_width / label_height > aspect_ratio:
            # 라벨이 세로로 더 좁은 경우, 세로에 맞춰 크기 조정
            new_height = label_height  # 라벨의 높이를 기준으로 새 높이 설정
            new_width = int(new_height * aspect_ratio)  # 비율을 유지하며 가로 크기 계산
        else:
            # 라벨이 가로로 더 좁은 경우, 가로에 맞춰 크기 조정
            new_width = label_width  # 라벨의 너비를 기준으로 새 너비 설정
            new_height = int(new_width / aspect_ratio)  # 비율을 유지하며 세로 크기 계산

        # 새로 계산된 크기로 WEBP를 설정합니다.
        self.current_movie.setScaledSize(QSize(new_width, new_height))  # 크기를 새로 계산된 크기로 설정

    def scale_gif(self):
        # 첫 번째 프레임으로 이동하여 이미지 데이터를 얻어옵니다.
        self.current_movie.jumpToFrame(0)  # 첫 번째 프레임으로 이동
        image = self.current_movie.currentImage()  # 현재 프레임의 이미지를 얻음

        # 원본 이미지의 너비와 높이를 얻습니다.
        original_width = image.width()  # 원본 이미지의 너비
        original_height = image.height()  # 원본 이미지의 높이

        # gif의 원본 비율을 계산합니다 (가로 / 세로 비율).
        if original_height == 0:
            original_height = 1  # 높이가 0인 경우(예외처리), 높이를 1로 설정하여 0으로 나누는 오류를 방지
        aspect_ratio = original_width / original_height  # 가로 세로 비율 계산

        # 이미지가 표시될 라벨의 크기를 얻습니다.
        label_width = self.image_label.width()  # 라벨의 너비
        label_height = self.image_label.height()  # 라벨의 높이

        # 원본 비율을 유지하며, 라벨의 크기에 맞는 새로운 크기를 계산합니다.
        if label_width / label_height > aspect_ratio:
            # 라벨이 세로로 더 좁은 경우, 세로에 맞춰 크기 조정
            new_height = label_height  # 라벨의 높이를 기준으로 새 높이 설정
            new_width = int(new_height * aspect_ratio)  # 비율을 유지하며 가로 크기 계산
        else:
            # 라벨이 가로로 더 좁은 경우, 가로에 맞춰 크기 조정
            new_width = label_width  # 라벨의 너비를 기준으로 새 너비 설정
            new_height = int(new_width / aspect_ratio)  # 비율을 유지하며 세로 크기 계산

        # 새로 계산된 크기로 gif를 설정합니다.
        self.current_movie.setScaledSize(QSize(new_width, new_height))  # 크기를 새로 계산된 크기로 설정

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
            
            # MPV의 재생 상태를 주기적으로 업데이트하기 위한 타이머 설정
            self.video_timer = QTimer(self)
            self.video_timer.timeout.connect(self.update_video_playback)  # 슬라이더 업데이트 호출
            self.video_timer.start(16)  # 16ms마다 업데이트 (약 60fps)
            self.timers.append(self.video_timer)  # 타이머 추적에 추가
            
            # 비디오 종료 시 타이머 중지
            self.player.observe_property('playback-restart', self.on_video_end)  # 비디오 종료 시 호출될 메서드 등록
            
            # duration 속성 관찰 (추가 정보 용도)
            def check_video_loaded(name, value):
                if value is not None and value > 0:
                    print(f"비디오 로드 완료: {video_path}, 길이: {value}초")
            
            self.player.observe_property('duration', check_video_loaded)
            
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
                max_frame = self.current_movie.frameCount() - 1
                frame = min(max(0, value), max_frame)  # 범위 내로 제한
                self.current_movie.jumpToFrame(frame)
            except Exception as e:
                pass  # 예외 발생 시 무시
                
        # 비디오 처리
        elif self.current_media_type == 'video' and hasattr(self, 'player') and self.player:
            try:
                if self.player.playback_time is not None:  # 재생 중인지 확인
                    seconds = self.playback_slider.value() / 1000.0  # 밀리초를 초 단위로 변환
                    self.player.command('seek', seconds, 'absolute')  # MPV의 seek 함수 사용
            except Exception as e:
                pass  # 예외 발생 시 무시

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

            # QImage를 QPixmap으로 변환하여 라벨에 표시합니다.
            pixmap = QPixmap.fromImage(qimg)  # QImage를 QPixmap으로 변환
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

        # 시간 레이블 크기 조정
        if hasattr(self, 'time_label'):
            # 레이블 너비 계산 (창 너비의 일정 비율)
            label_width = max(80, min(180, int(window_width * 0.1)))  # 최소 80px, 최대 180px, 기본 창 너비의 10%로 증가
            
            # 시간 레이블 높이를 버튼 높이와 유사하게 계산 (창 크기에 따라 조정)
            button_width = max(60, min(150, int(window_width * 0.08)))  # 버튼 너비 계산 (resizeEvent와 동일)
            button_height = max(30, min(50, int(button_width * 0.6)))   # 버튼 높이 계산 (높이 비율 0.5→0.6으로 증가)
            
            # 레이블 크기 설정
            self.time_label.setFixedSize(label_width, button_height)
            
            # 폰트 크기도 창 크기에 맞게 조정 (더 큰 폰트 크기 적용)
            font_size = max(9, min(16, int(label_width * 0.40)))  # 레이블 너비의 40%, 최소 9px, 최대 16px로 변경 (버튼과 동일)
            
            # 레이블 스타일시트 업데이트
            self.time_label.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(52, 73, 94, 0.6);
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                    font-size: {font_size}px;
                    qproperty-alignment: AlignCenter;
                }}
                QLabel:hover {{
                    background-color: rgba(52, 73, 94, 1.0);
                }}
            """)
        
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

    # 키보드 이벤트를 처리하는 메서드입니다.
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:  # 왼쪽 화살표키를 눌렀을 때
            self.show_previous_image()  # 이전 이미지로 이동
        elif event.key() == Qt.Key_Right:  # 오른쪽 화살표키를 눌렀을 때
            self.show_next_image()  # 다음 이미지로 이동

    # 마우스 휠 이벤트를 처리하는 메서드입니다.
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
                is_in_titlebar_buttons = is_in_titlebar and local_pos.x() >= self.width() - 90
                
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
            is_in_titlebar_buttons = is_in_titlebar and local_pos.x() >= self.width() - 90
            
            if self.resize_direction and not self.isMaximized() and not is_in_titlebar_buttons:
                # 리사이징 시작
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                return True
            elif is_in_titlebar and not is_in_titlebar_buttons:
                # 제목 표시줄 드래그 시작
                self.drag_start_pos = event.globalPos() - self.pos()
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
            return was_resizing

        return super().eventFilter(obj, event)

    # toggle_maximize 메소드 추가 (이름을 toggle_maximize_state로 변경)
    def toggle_maximize_state(self):
        """최대화 상태와 일반 상태를 토글합니다."""
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setText("□")  # 일반 상태일 때는 □ 표시
        else:
            self.showMaximized()
            self.max_btn.setText("❐")  # 최대화 상태일 때는 ❐ 표시

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
        if self.current_media_type in ['gif', 'webp'] and hasattr(self, 'current_movie') and self.current_movie:
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
                        # 드라이브 + '...' + 마지막 2개 폴더 + 파일명
                        path_parts = parts[:-1]  # 파일명 제외한 부분
                        path_display = f"{drive}{os.sep}...{os.sep}{os.sep.join(path_parts[-2:])}{os.sep}{filename}"
                
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
        if self.current_image_path:
            if self.current_image_path in self.bookmarks:
                # 슬라이더바 북마크 버튼 업데이트 (노란색 별표)
                if hasattr(self, 'slider_bookmark_btn'):
                    self.slider_bookmark_btn.setStyleSheet("""
                        QPushButton {
                            background-color: rgba(52, 73, 94, 0.6);
                            color: #FFD700;  /* 노란색(Gold) 별표 */
                            border: none;
                            padding: 10px;
                            border-radius: 3px;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background-color: rgba(52, 73, 94, 1.0);
                        }
                    """)
            else:
                # 슬라이더바 북마크 버튼 업데이트 (흰색 별표)
                if hasattr(self, 'slider_bookmark_btn'):
                    self.slider_bookmark_btn.setStyleSheet("""
                        QPushButton {
                            background-color: rgba(52, 73, 94, 0.6);
                            color: white;
                            border: none;
                            padding: 10px;
                            border-radius: 3px;
                            font-size: 14px;
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
            app_data_dir = os.path.join(os.path.expanduser("~"), "ImageViewer_Data")
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
            app_data_dir = os.path.join(os.path.expanduser("~"), "ImageViewer_Data")
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
            
            # 빈 메뉴 생성 (예시 항목 추가)
            self.dropdown_menu.addAction(QAction("메뉴 항목 1", self))
            self.dropdown_menu.addAction(QAction("메뉴 항목 2", self))
            self.dropdown_menu.addAction(QAction("메뉴 항목 3", self))
            self.dropdown_menu.addSeparator()
            self.dropdown_menu.addAction(QAction("설정", self))
            
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
        # 완료되었거나 오류가 발생한 스레드 제거
        current_threads = list(self.loader_threads.items())
        for path, loader in current_threads:
            if not loader.isRunning():
                del self.loader_threads[path]
                
        # 활성 스레드가 너무 많으면 가장 오래된 것부터 종료
        max_concurrent_threads = 3  # 최대 동시 실행 스레드 수
        
        if len(self.loader_threads) > max_concurrent_threads:
            # 현재 이미지의 로더는 제외하고 오래된 순으로 정리
            threads_to_remove = [
                path for path in self.loader_threads 
                if path != self.current_image_path
            ]
            
            # 초과된 만큼 오래된 스레드부터 제거
            for path in threads_to_remove[:len(self.loader_threads) - max_concurrent_threads]:
                if path in self.loader_threads:
                    loader = self.loader_threads[path]
                    if loader.isRunning():
                        loader.terminate()
                        try:
                            loader.wait(100)  # 최대 100ms까지만 대기
                        except:
                            pass
                    del self.loader_threads[path]
                    print(f"스레드 정리: {os.path.basename(path)}")

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
                self.image_cache.put(path, image, size_mb)
        else:
            print(f"크기가 너무 큰 이미지는 캐시되지 않습니다: {os.path.basename(path)} ({size_mb:.2f}MB)")
        
        # 현재 경로가 로드된 이미지 경로와 일치하는 경우에만 표시
        if self.current_image_path == path:
            # 이미지 크기에 따라 스케일링 방식 결정
            # 작은 이미지는 고품질 변환, 큰 이미지는 빠른 변환 사용
            transform_method = Qt.SmoothTransformation if size_mb < 20 else Qt.FastTransformation
            
            # 화면 크기 얻기
            label_size = self.image_label.size()
            
            # 이미지 크기가 화면보다 훨씬 크면 2단계 스케일링 적용
            if size_mb > 30 and (image.width() > label_size.width() * 2 or image.height() > label_size.height() * 2):
                # 1단계: 빠른 방식으로 대략적인 크기로 축소
                # float 값을 int로 변환 (타입 오류 수정)
                intermediate_pixmap = image.scaled(
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
                scaled_pixmap = image.scaled(
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

# 메인 함수
def main():
    app = QApplication(sys.argv)  # Qt 애플리케이션 객체 생성
    viewer = ImageViewer()  # ImageViewer 클래스의 객체 생성
    viewer.show()  # 뷰어 창 표시
    sys.exit(app.exec_())  # 이벤트 루프 실행

# 프로그램 실행 시 main() 함수 실행
if __name__ == "__main__":
    main()  # 메인 함수 실행