# GIF 크기를 조정하는 메서드입니다.
import sys
import os
import shutil
import re
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout, QSizePolicy, QSlider, QLayout
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QFont, QMovie, QCursor, QIcon
from PyQt5.QtCore import Qt, QSize, QTimer, QEvent, QPoint, pyqtSignal
import cv2
from PIL import Image, ImageCms
from io import BytesIO

# MPV DLL 경로를 PATH에 추가 (반드시 mpv 모듈을 import하기 전에 해야 함)
mpv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mpv')
os.environ["PATH"] = mpv_path + os.pathsep + os.environ["PATH"]

# 이제 mpv 모듈을 import
import mpv

# QSlider를 상속받는 새로운 클래스 추가
class ClickableSlider(QSlider):
    clicked = pyqtSignal(int)  # 클릭 이벤트 시그널 추가

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 클릭한 위치의 값을 계산
            pos = event.pos().x()
            value = int((pos / self.width()) * (self.maximum() - self.minimum()) + self.minimum())
            # 값을 범위 내로 제한
            value = max(self.minimum(), min(self.maximum(), value))
            self.setValue(value)  # 슬라이더 값을 직접 설정
            self.clicked.emit(value)  # 클릭 이벤트 발생
        super().mousePressEvent(event)

class ImageViewer(QWidget):  # 이미지 뷰어 클래스를 정의
    def __init__(self):
        super().__init__()  # QWidget의 초기화 메소드 호출

        # 화면 해상도의 75%로 초기 창 크기 설정
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.75)
        height = int(screen.height() * 0.75)
        self.resize(width, height)

        # 창을 화면 중앙에 위치
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.move(x, y)

        # 크기 조절을 위한 변수들 추가
        self.resize_direction = None
        self.resizing = False
        self.resize_start_pos = None
        self.resize_start_geometry = None
        
        # 최소 창 크기 설정
        self.setMinimumSize(400, 300)

        # Define button style here
        button_style = """
            QPushButton {
                background-color: rgba(52, 73, 94, 0.9);
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진해지는 색상 */
            }
        """

        # 슬라이더 스타일 설정 (슬라이더 배경 색상 변경)
        slider_style = """
            QSlider::groove:horizontal {
                border: none;
                height: 10px;
                background: rgba(52, 73, 94, 0.9);
                margin: 0px;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 2px solid white;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::add-page:horizontal {
                background: rgba(52, 73, 94, 0.3);
                border-radius: 5px;
            }
            QSlider::sub-page:horizontal {
                background: rgba(52, 73, 94, 0.9);
                border-radius: 5px;
            }
        """

        # 프레임리스 윈도우 설정
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 배경색을 흰색으로 설정
        self.setStyleSheet("background-color: white;")

        # 전체 레이아웃 설정
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 제목표시줄 생성
        self.title_bar = QWidget(self)
        self.title_bar.setStyleSheet("background-color: rgba(52, 73, 94, 1.0);")
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 제목 텍스트
        title_label = QLabel("Image Viewer")
        title_label.setStyleSheet("color: white; font-size: 16px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 윈도우 컨트롤 버튼
        min_btn = QPushButton("_")
        min_btn.setStyleSheet("color: white; background: none; border: none;")
        min_btn.setFixedSize(30, 30)
        min_btn.clicked.connect(self.showMinimized)
        
        max_btn = QPushButton("□")
        max_btn.setStyleSheet("color: white; background: none; border: none;")
        max_btn.setFixedSize(30, 30)
        max_btn.clicked.connect(self.toggle_maximize_state)
        self.max_btn = max_btn  # 버튼 객체를 클래스 변수로 저장
        
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("color: white; background: none; border: none;")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(min_btn)
        title_layout.addWidget(max_btn)
        title_layout.addWidget(close_btn)

        # 메인 레이아웃에 제목표시줄 추가
        main_layout.addWidget(self.title_bar, 1)  # 1%
        
        # 이미지를 표시할 컨테이너 위젯
        self.image_container = QWidget()
        self.image_container.setStyleSheet("background-color: white;")
        
        # 컨테이너에 대한 레이아웃
        container_layout = QVBoxLayout(self.image_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 이미지 레이블 설정
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("background-color: black;")  # QLabel 배경색을 검은색으로 설정
        container_layout.addWidget(self.image_label)
        
        # 이미지 정보 레이블 생성
        self.image_info_label = QLabel(self)
        self.image_info_label.setAlignment(Qt.AlignCenter)
        self.image_info_label.hide()
        
        # 하단 버튼 레이아웃 생성
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # 새로운 슬라이더를 위한 위젯 추가
        slider_widget = QWidget(self)  # 슬라이더를 감싸는 위젯 생성
        slider_widget.setStyleSheet("background-color: rgba(52, 73, 94, 0.9);")  # 위젯 색상 설정

        # 새로운 슬라이더를 위한 수평 레이아웃 추가
        new_slider_layout = QHBoxLayout(slider_widget)
        new_slider_layout.setContentsMargins(0, 0, 0, 0)

        # Open Image Folder 버튼 (첫 번째 위치)
        self.open_button = QPushButton('Open Image Folder', self)
        self.open_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        self.open_button.clicked.connect(self.open_folder)
        new_slider_layout.addWidget(self.open_button)

        # Set Base Folder 버튼 (두 번째 위치)
        self.set_base_folder_button = QPushButton('Set Base Folder', self)
        self.set_base_folder_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        self.set_base_folder_button.clicked.connect(self.set_base_folder)
        new_slider_layout.addWidget(self.set_base_folder_button)

        # 재생 버튼 (세 번째 위치)
        self.play_button = QPushButton("▶", self)  # 재생 아이콘 버튼
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        new_slider_layout.addWidget(self.play_button)

        # MPV 상태 확인을 위한 타이머 설정
        self.play_button_timer = QTimer(self)
        self.play_button_timer.timeout.connect(self.update_play_button)
        self.play_button_timer.start(100)  # 100ms마다 상태 확인

        # 기존 슬라이더 (재생 바) 추가
        self.playback_slider = ClickableSlider(Qt.Horizontal, self)  # ClickableSlider로 변경
        self.playback_slider.setRange(0, 100)  # 슬라이더 범위 설정
        self.playback_slider.setValue(0)  # 초기 값을 0으로 설정
        self.playback_slider.setStyleSheet(slider_style)  # 슬라이더 스타일 적용
        self.playback_slider.clicked.connect(self.slider_clicked)  # 클릭 이벤트 연결
        new_slider_layout.addWidget(self.playback_slider)  # 재생 바 슬라이더를 레이아웃에 추가

        # 재생 시간 레이블 추가
        self.time_label = QLabel("00:00 / 00:00", self)  # 초기 시간 표시
        self.time_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 14px;
                min-width: 100px;
                max-width: 100px;
                qproperty-alignment: AlignCenter;  /* 텍스트 중앙 정렬 */
            }
            QLabel:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        self.time_label.setFixedSize(100, 30)  # 너비 100px, 높이 30px로 고정
        self.time_label.setAlignment(Qt.AlignCenter)  # 텍스트 중앙 정렬
        new_slider_layout.addWidget(self.time_label)  # 레이블을 재생 바 오른쪽에 추가

        # 음소거 버튼 추가
        self.mute_button = QPushButton("🔈", self)  # 음소거 해제 아이콘으로 초기화
        self.mute_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.6);  /* 평상시 더 연하게 */
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);  /* 마우스 오버 시 진하게 */
            }
        """)
        self.mute_button.setFixedSize(30, 30)  # 버튼 크기 설정
        self.mute_button.clicked.connect(self.toggle_mute)  # 음소거 토글 메서드 연결
        new_slider_layout.addWidget(self.mute_button)  # 음소거 버튼을 레이아웃에 추가

        # 음량 조절용 슬라이더 추가
        self.volume_slider = ClickableSlider(Qt.Horizontal, self)  # ClickableSlider로 변경
        self.volume_slider.setRange(0, 100)  # 슬라이더 범위 설정
        self.volume_slider.setValue(100)  # 초기 값 설정 (100%로 시작)
        self.volume_slider.setStyleSheet(slider_style)  # 슬라이더 스타일 적용
        self.volume_slider.setFixedWidth(int(self.image_label.width() * 0.3))  # 슬라이더 너비를 이미지 너비의 30%로 설정
        self.volume_slider.clicked.connect(self.adjust_volume)  # 클릭 이벤트 연결
        self.volume_slider.valueChanged.connect(self.adjust_volume)  # 드래그 이벤트 연결
        new_slider_layout.addWidget(self.volume_slider)  # 음량 조절 슬라이더를 레이아웃에 추가

        # 새로운 슬라이더 위젯을 하단 레이아웃에 추가
        bottom_layout.addWidget(slider_widget)

        # 48개의 폴더 버튼에 스타일 적용
        self.buttons = []
        for _ in range(5):  # 4줄에서 5줄로 변경
            button_layout = QHBoxLayout()
            button_row = []
            for _ in range(20):  # 12개에서 20개로 변경
                empty_button = QPushButton('')
                empty_button.setStyleSheet(button_style)
                empty_button.clicked.connect(self.on_button_click)
                button_row.append(empty_button)
                button_layout.addWidget(empty_button)
            self.buttons.append(button_row)
            bottom_layout.addLayout(button_layout)

        # 메인 레이아웃에 위젯 추가
        main_layout.addWidget(self.image_container, 90)  # 89%

        # 하단 버튼 영역을 메인 레이아웃에 추가
        main_layout.addLayout(bottom_layout, 9)  # 10%

        self.image_files = []  # 이미지 파일 리스트 초기화
        self.current_index = 0  # 현재 이미지의 인덱스 초기화
        self.current_image_path = None  # 현재 이미지 경로 초기화
        self.base_folder = None  # 기준 폴더 변수 초기화

        self.setFocusPolicy(Qt.StrongFocus)  # 강한 포커스를 설정 (위젯이 포커스를 받을 수 있도록 설정)

        self.cap = None  # 비디오 캡처 객체 초기화
        self.timer = QTimer(self)  # 타이머 객체 생성
        self.timer.timeout.connect(self.update_video_frame)  # 타이머가 작동할 때마다 update_video_frame 메소드 호출

        # 마우스 트래킹 활성화
        self.setMouseTracking(True)
        self.image_container.setMouseTracking(True)
        self.image_label.setMouseTracking(True)
        
        # 전역 이벤트 필터 설치
        QApplication.instance().installEventFilter(self)

        # MPV DLL 경로 설정
        if getattr(sys, 'frozen', False):
            # PyInstaller로 패키징된 경우
            mpv_path = os.path.join(os.path.dirname(sys.executable), 'mpv')
            os.environ["MPV_DYLIB_PATH"] = os.path.join(mpv_path, "libmpv-2.dll")
        else:
            # 일반 스크립트로 실행되는 경우
            mpv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mpv')
            os.environ["MPV_DYLIB_PATH"] = os.path.join(mpv_path, "libmpv-2.dll")

        self.player = mpv.MPV(ytdl=True, input_default_bindings=True, input_vo_keyboard=True, hr_seek="yes")

        # 슬라이더와 음량 조절 동기화
        self.volume_slider.valueChanged.connect(self.adjust_volume)  # 슬라이더 값 변경 시 음량 조절 메서드 연결

        # 슬라이더 스타일 적용
        self.playback_slider.setStyleSheet(slider_style)  # 슬라이더 스타일 적용
        self.volume_slider.setStyleSheet(slider_style)  # 음량 조절 슬라이더 스타일 적용

        self.previous_position = None  # 클래스 변수로 이전 위치 저장

        # 창이 완전히 로드된 후 이미지 정보 업데이트를 위한 타이머 설정
        # 초기 레이아웃 설정을 위해 바로 호출
        self.update_image_info()
        # 창이 완전히 로드된 후 한번 더 업데이트
        QTimer.singleShot(100, self.update_image_info)

        self.psd_cache = {}  # PSD 캐시를 딕셔너리로 변경
        self.max_psd_cache_size = 5  # PSD 캐시 최대 크기

        self.is_slider_dragging = False  # 슬라이더 드래그 상태를 추적하는 변수 추가

    def ensure_maximized(self):
        """창이 최대화 상태인지 확인하고 그렇지 않으면 다시 최대화합니다."""
        if not self.isMaximized():
            self.showMaximized()

    def resizeEvent(self, event):
        """창 크기 변경 이벤트 처리"""
        if hasattr(self, 'title_bar'):
            self.title_bar.setGeometry(0, 0, self.width(), 30)
            self.title_bar.raise_()
            
            # 제목표시줄의 버튼들 업데이트
            for child in self.title_bar.children():
                if isinstance(child, QPushButton):
                    child.updateGeometry()
                    child.update()  # 버튼의 시각적 상태도 업데이트
        
        # 현재 표시 중인 미디어 크기 조절
        if hasattr(self, 'current_image_path') and self.current_image_path:
            file_ext = os.path.splitext(self.current_image_path)[1].lower()
            
            if file_ext == '.psd':  # PSD 파일
                try:
                    # 캐시된 이미지가 있으면 사용
                    if self.current_image_path in self.psd_cache:
                        pixmap = self.psd_cache[self.current_image_path]
                    else:
                        # 캐시된 이미지가 없으면 변환
                        from PIL import Image, ImageCms
                        from io import BytesIO
                        
                        # PSD 파일을 PIL Image로 열기
                        image = Image.open(self.current_image_path)
                        
                        # RGB 모드로 변환
                        if image.mode != 'RGB':
                            image = image.convert('RGB')
                        
                        # ICC 프로파일 처리
                        if 'icc_profile' in image.info:
                            try:
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
                            # 가장 오래된 항목 제거
                            self.psd_cache.pop(next(iter(self.psd_cache)))
                        self.psd_cache[self.current_image_path] = pixmap
                    
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.image_label.setPixmap(scaled_pixmap)

                except Exception as e:
                    print(f"PSD 파일 리사이즈 중 오류 발생: {e}")
            
            elif file_ext in ['.jpg', '.jpeg', '.png']:  # 일반 이미지
                pixmap = QPixmap(self.current_image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)
            
            elif file_ext == '.webp':  # WEBP 파일
                if hasattr(self, 'current_movie') and self.current_movie:
                    # 애니메이션인 경우
                    current_frame = self.current_movie.currentFrameNumber()
                    original_size = QSize(self.current_movie.currentImage().width(), self.current_movie.currentImage().height())
                    label_size = self.image_label.size()
                    
                    if original_size.height() == 0:
                        original_size.setHeight(1)
                    
                    if label_size.width() / label_size.height() > original_size.width() / original_size.height():
                        new_height = label_size.height()
                        new_width = int(new_height * (original_size.width() / original_size.height()))
                    else:
                        new_width = label_size.width()
                        new_height = int(new_width * (original_size.height() / original_size.width()))
                    
                    self.current_movie.setScaledSize(QSize(new_width, new_height))
                    self.current_movie.jumpToFrame(current_frame)
                else:
                    # 일반 이미지인 경우
                    pixmap = QPixmap(self.current_image_path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        self.image_label.setPixmap(scaled_pixmap)
            
            elif file_ext in ['.gif', '.webp']:  # 애니메이션
                if hasattr(self, 'current_movie'):
                    # 현재 프레임 번호 저장
                    current_frame = self.current_movie.currentFrameNumber()
                    
                    # 새로운 크기 계산
                    original_size = QSize(self.current_movie.currentImage().width(), self.current_movie.currentImage().height())
                    label_size = self.image_label.size()
                    
                    if original_size.height() == 0:
                        original_size.setHeight(1)
                    
                    if label_size.width() / label_size.height() > original_size.width() / original_size.height():
                        new_height = label_size.height()
                        new_width = int(new_height * (original_size.width() / original_size.height()))
                    else:
                        new_width = label_size.width()
                        new_height = int(new_width * (original_size.height() / original_size.width()))
                    
                    # 새로운 크기로 설정
                    self.current_movie.setScaledSize(QSize(new_width, new_height))
                    
                    # 현재 프레임으로 복귀
                    self.current_movie.jumpToFrame(current_frame)
            
            elif file_ext == '.mp4':  # 비디오
                if hasattr(self, 'player'):
                    # MPV 플레이어의 출력 크기 업데이트
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
                            button.setToolTip(subfolders[index])
        
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
            self.volume_slider.setFixedWidth(int(window_width * 0.15))  # 창 너비의 15%

        # 재생 슬라이더 크기 조정
        if hasattr(self, 'playback_slider'):
            window_width = self.width()
            min_width = int(window_width * 0.4)  # 최소 40%
            max_width = int(window_width * 0.6)  # 최대 60%
            self.playback_slider.setMinimumWidth(min_width)
            self.playback_slider.setMaximumWidth(max_width)
        
        # 레이아웃 강제 업데이트 추가
        if hasattr(self, 'image_container'):
            self.image_container.updateGeometry()
        
        # 모든 버튼의 레이아웃 업데이트
        for row in self.buttons:
            for button in row:
                button.updateGeometry()
        
        # 슬라이더 위젯의 레이아웃 업데이트
        if hasattr(self, 'playback_slider'):
            self.playback_slider.updateGeometry()
        if hasattr(self, 'volume_slider'):
            self.volume_slider.updateGeometry()
        
        # 전체 레이아웃 강제 업데이트
        self.updateGeometry()
        self.layout().update()
        
        super().resizeEvent(event)

    def mouseDoubleClickEvent(self, event):
        """더블 클릭 시 최대화 및 일반 창 상태를 전환합니다."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def set_base_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Set Base Folder")
        if folder_path:
            self.base_folder = folder_path
            print(f"Base folder set to: {self.base_folder}")

            # 버튼들 초기화
            for row in self.buttons:
                for button in row:
                    button.setText('')
                    button.setToolTip('')

            # 하위 폴더들을 가져와서 자연스러운 순서로 정렬
            def natural_keys(text):
                import re
                def atoi(text):
                    return int(text) if text.isdigit() else text
                return [atoi(c) for c in re.split('([0-9]+)', text)]

            subfolders = [f.path for f in os.scandir(self.base_folder) if f.is_dir()]
            subfolders.sort(key=lambda x: natural_keys(os.path.basename(x).lower()))

            # 버튼 너비 계산
            button_width = self.width() // 20

            # 빈 버튼에 하위 폴더 경로를 순서대로 설정
            for i, row in enumerate(self.buttons):
                for j, button in enumerate(row):
                    index = i * 20 + j
                    if index < len(subfolders):
                        folder_name = os.path.basename(subfolders[index])
                        button.setFixedWidth(button_width)
                        
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
                            button.setText(folder_name)
                            button.setToolTip(subfolders[index])

    def on_button_click(self):
        button = self.sender()  # 클릭된 버튼을 가져옴
        folder_path = button.toolTip()  # 버튼의 툴큐에서 폴더 경로 가져오기
        print(f"Selected folder: {folder_path}")  # 선택된 폴더 경로 출력

        # 커서를 일반 커서로 설정
        QApplication.restoreOverrideCursor()  # 모래시계에서 일반 커서로 복원

        self.copy_image_to_folder(folder_path)  # 해당 폴더로 이미지를 복사하는 메소드 호출

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Image Folder")  # 폴더 선택 대화상자 열기

        if folder_path:  # 폴더가 선택되었으면
            self.image_files = self.get_image_files(folder_path)  # 이미지 파일 목록 가져오기

            if self.image_files:  # 유효한 이미지 파일이 있으면
                self.image_files.sort()  # 이미지 파일을 정렬
                self.show_image(self.image_files[0])  # 첫 번째 이미지를 화면에 표시
                self.current_index = 0  # 현재 이미지 인덱스를 0으로 설정
            else:
                print("No valid image files found in the folder.")  # 유효한 이미지 파일이 없으면 출력

    def get_image_files(self, folder_path):
        # 유효한 이미지 확장자 목록
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.psd', '.gif', '.mp4']
        # 폴더 내의 유효한 이미지 파일 경로 목록을 반환
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if any(f.lower().endswith(ext) for ext in valid_extensions)]

    def stop_video(self):
        """비디오 재생 중지"""
        # OpenCV 객체 정리
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        if self.timer.isActive():
            self.timer.stop()
        
        # MPV 정지 - 플레이어가 존재하고 실행 중일 때만 중지
        if hasattr(self, 'player') and self.player:
            try:
                # 플레이어가 실행 중인지 확인
                if self.player.playback_time is not None:  # 재생 중인지 확인
                    self.player.stop()
            except Exception as e:
                print(f"MPV 플레이어 종료 중 오류 발생: {e}")

    def show_image(self, image_path):
        self.stop_video()  # 비디오 중지

        # 이전 이미지 애니메이션 정지
        self.image_label.clear()  # QLabel의 내용을 지워서 애니메이션 정지

        # 파일 이름과 확장자를 제목표시줄에 표시
        file_name = os.path.basename(image_path) if image_path else "Image Viewer"
        title_text = f"Image Viewer - {file_name}" if image_path else "Image Viewer"
        # title_label을 찾아서 텍스트 업데이트
        for child in self.title_bar.children():
            if isinstance(child, QLabel):
                child.setText(title_text)
                break
        
        # 파일 확장자 확인 (소문자로 변환)
        file_ext = os.path.splitext(image_path)[1].lower()

        # GIF가 재생 중일 경우 정지
        if hasattr(self, 'current_movie') and self.current_movie.state() == QMovie.Running:
            self.current_movie.stop()  # GIF 정지
            try:
                self.playback_slider.valueChanged.disconnect()  # 슬라이더 연결 해제
            except TypeError:
                pass  # 연결된 시그널이 없으면 무시

        # 슬라이더 초기화
        self.playback_slider.setRange(0, 0)  # 슬라이더 범위를 0으로 설정
        self.playback_slider.setValue(0)  # 슬라이더 초기값을 0으로 설정

        if file_ext == '.gif':  # GIF 파일 처리
            self.show_gif(image_path)  # GIF를 표시하는 메서드 호출
        elif file_ext == '.psd':  # PSD 파일
            try:
                # 캐시된 이미지가 있으면 사용
                if image_path in self.psd_cache:
                    pixmap = self.psd_cache[image_path]
                else:
                    # 캐시된 이미지가 없으면 변환
                    from PIL import Image, ImageCms
                    from io import BytesIO
                    
                    # PSD 파일을 PIL Image로 열기
                    image = Image.open(image_path)
                    
                    # RGB 모드로 변환
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # ICC 프로파일 처리
                    if 'icc_profile' in image.info:
                        try:
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
                        # 가장 오래된 항목 제거
                        self.psd_cache.pop(next(iter(self.psd_cache)))
                    self.psd_cache[image_path] = pixmap
                
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)

            except Exception as e:
                print(f"PSD 파일 리사이즈 중 오류 발생: {e}")
        elif file_ext in ['.jpg', '.jpeg', '.png']:  # JPG, JPEG, PNG 파일 처리
            pixmap = QPixmap(image_path)  # QPixmap으로 이미지 로드
            if not pixmap.isNull():  # 이미지가 정상적으로 로드되었는지 확인
                self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))  
        elif file_ext == '.webp':  # WEBP 파일 처리
            self.show_webp_animation(image_path)  # WEBP 애니메이션 처리
        elif file_ext == '.mp4':  # MP4 파일 처리
            self.play_video(image_path)  # MP4 비디오 재생

        self.current_image_path = image_path  # 현재 이미지 경로 업데이트
        self.update_image_info()  # 이미지 정보 업데이트 메소드 호출

        # 시간 레이블 초기화
        self.time_label.setText("00:00 / 00:00")  # 시간 레이블 초기화
        self.time_label.show()  # 시간 레이블 표시

        # 제목표시줄과 이미지 정보 레이블을 앞으로 가져옴
        if hasattr(self, 'title_bar'):
            self.title_bar.raise_()
        if hasattr(self, 'image_info_label'):
            self.image_info_label.raise_()

    def show_gif(self, image_path):
        # 이전 GIF 상태 정리
        if hasattr(self, 'gif_timer'):
            self.gif_timer.stop()  # 타이머 정지
            del self.gif_timer  # 타이머 객체 삭제

        # 이전 QMovie 객체가 있다면 삭제
        if hasattr(self, 'current_movie'):
            self.current_movie.stop()  # 현재 GIF 정지
            del self.current_movie  # 메모리 해제

        self.current_movie = QMovie(image_path)  # 새로운 QMovie 객체 생성

        # GIF의 유효성 검사
        if not self.current_movie.isValid():
            return

        # GIF의 첫 번째 프레임을 로드
        self.current_movie.jumpToFrame(0)
        if self.current_movie.currentImage().isNull():
            return

        # QLabel의 크기에 맞게 GIF 크기 조정
        original_size = QSize(self.current_movie.currentImage().width(), self.current_movie.currentImage().height())
        label_size = self.image_label.size()

        if original_size.height() == 0:
            original_size.setHeight(1)

        if label_size.width() / label_size.height() > original_size.width() / original_size.height():
            new_height = label_size.height()
            new_width = int(new_height * (original_size.width() / original_size.height()))
        else:
            new_width = label_size.width()
            new_height = int(new_width * (original_size.height() / original_size.width()))

        self.current_movie.setScaledSize(QSize(new_width, new_height))
        self.image_label.setMovie(self.current_movie)
        self.current_movie.start()

        # 슬라이더 범위를 GIF의 프레임 수에 맞게 설정
        frame_count = self.current_movie.frameCount()
        if frame_count > 0:
            self.playback_slider.setRange(0, frame_count - 1)
            self.playback_slider.setValue(0)

            # 슬라이더 값 변경 시 프레임 변경 연결
            self.playback_slider.valueChanged.connect(lambda value: self.current_movie.jumpToFrame(value))

            # GIF의 프레임이 변경될 때마다 슬라이더 값을 업데이트
            def update_slider():
                current_frame = self.current_movie.currentFrameNumber()
                if self.current_movie.state() == QMovie.Running:
                    self.playback_slider.setValue(current_frame)
                    # 현재 프레임 / 총 프레임 표시 업데이트
                    self.time_label.setText(f"{current_frame + 1} / {self.current_movie.frameCount()}")  # 현재 프레임은 0부터 시작하므로 +1

                # 타이머를 사용하여 슬라이더 업데이트
                if not hasattr(self, 'gif_timer'):  # 타이머가 이미 존재하지 않을 때만 생성
                    self.gif_timer = QTimer(self)
                    self.gif_timer.timeout.connect(update_slider)
                    self.gif_timer.start(50)  # 50ms마다 슬라이더 업데이트

            # 타이머를 사용하여 슬라이더 업데이트
            self.gif_timer = QTimer(self)
            self.gif_timer.timeout.connect(update_slider)
            self.gif_timer.start(50)

        # GIF 반복 설정
        self.current_movie.loopCount = 0  # 무한 반복

    def show_webp_animation(self, image_path):
        # WEBP 애니메이션을 처리하기 위해 QImageReader를 사용
        reader = QImageReader(image_path)

        # 이미지를 로드하고 애니메이션으로 처리
        if reader.supportsAnimation():  # 애니메이션을 지원하면
            if hasattr(self, 'gif_timer'):
                self.gif_timer.stop()
                del self.gif_timer

            if hasattr(self, 'current_movie'):
                self.current_movie.stop()
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

                # 슬라이더 값 변경 시 프레임 변경 연결
                try:
                    self.playback_slider.valueChanged.disconnect()
                except TypeError:
                    pass
                self.playback_slider.valueChanged.connect(lambda value: self.current_movie.jumpToFrame(value))

                # WEBP의 프레임이 변경될 때마다 슬라이더 값을 업데이트
                def update_slider():
                    current_frame = self.current_movie.currentFrameNumber()
                    if self.current_movie.state() == QMovie.Running:
                        self.playback_slider.setValue(current_frame)
                        # 현재 프레임 / 총 프레임 표시 업데이트
                        self.time_label.setText(f"{current_frame + 1} / {self.current_movie.frameCount()}")

                # 타이머를 사용하여 슬라이더 업데이트
                self.gif_timer = QTimer(self)
                self.gif_timer.timeout.connect(update_slider)
                self.gif_timer.start(50)  # 50ms마다 슬라이더 업데이트

                self.current_movie.start()
            else:
                # 프레임이 1개 이하일 경우 일반 이미지로 처리
                image = QImage(image_path)
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.width(),
                        self.image_label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)

                # 슬라이더 초기화
                self.playback_slider.setRange(0, 0)
                self.playback_slider.setValue(0)
                self.time_label.setText("00:00 / 00:00")
                self.time_label.show()
        else:
            # 일반 WEBP 이미지 처리
            image = QImage(image_path)
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.width(),
                    self.image_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)

            # 슬라이더 초기화
            self.playback_slider.setRange(0, 0)
            self.playback_slider.setValue(0)
            self.time_label.setText("00:00 / 00:00")
            self.time_label.show()

    def scale_webp(self):
        # 첫 번째 프레임으로 이동하여 이미지 데이터를 얻어옵니다.
        self.current_movie.jumpToFrame(0)  # 첫 번째 프레임으로 이동
        image = self.current_movie.currentImage()  # 현재 프레임의 이미지를 얻음

        # 원본 이미지의 너비와 높이를 얻습니다.
        original_width = image.width()  # 원본 이미지의 너비
        original_height = image.height()  # 원본 이미지의 높이

        # GIF의 원본 비율을 계산합니다 (가로 / 세로 비율).
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

        # 새로 계산된 크기로 WEBP를 설정합니다.
        self.current_movie.setScaledSize(QSize(new_width, new_height))  # 크기를 새로 계산된 크기로 설정

    def play_video(self, video_path):
        """MPV를 사용하여 비디오 재생"""
        # 기존 비디오 중지
        self.stop_video()
        
        # MPV로 비디오 재생
        try:
            # 화면에 비디오 출력을 위한 윈도우 핸들 설정
            wid = int(self.image_label.winId())
            self.player.wid = wid
            
            # MPV 옵션 설정
            self.player.loop = True  # 비디오 반복 재생
            self.player.volume = 100  # 볼륨 100%로 설정
            self.player.seekable = True  # seek 가능하도록 설정
            
            # 비디오 파일 재생
            self.player.play(video_path)
            
            # 비디오 정보 업데이트
            self.current_image_path = video_path
            
            # 슬라이더 초기화
            self.playback_slider.setRange(0, 0)  # 슬라이더 범위를 0으로 설정
            self.playback_slider.setValue(0)  # 슬라이더 초기값을 0으로 설정
            
            # 슬라이더 이벤트 연결
            self.playback_slider.sliderPressed.connect(self.slider_pressed)
            self.playback_slider.sliderReleased.connect(self.slider_released)
            self.playback_slider.valueChanged.connect(self.seek_video)
            
            # MPV의 재생 상태를 주기적으로 업데이트하기 위한 타이머 설정
            self.video_timer = QTimer(self)
            self.video_timer.timeout.connect(self.update_video_playback)  # 슬라이더 업데이트 호출
            self.video_timer.start(16)  # 16ms마다 업데이트 (약 60fps)
            
        except Exception as e:
            print(f"MPV 재생 오류: {e}")

    def slider_clicked(self, value):
        """슬라이더를 클릭했을 때 호출됩니다."""
        if hasattr(self, 'player'):
            try:
                # 클릭한 위치의 값을 초 단위로 변환
                seconds = value / 1000.0  # 밀리초를 초 단위로 변환
                # MPV의 seek 함수를 사용하여 정확한 위치로 이동
                self.player.command('seek', seconds, 'absolute')
            except Exception as e:
                print(f"비디오 위치 변경 중 오류 발생: {e}")

    def slider_pressed(self):
        """슬라이더를 드래그하기 시작할 때 호출됩니다."""
        self.is_slider_dragging = True

    def slider_released(self):
        """슬라이더 드래그가 끝날 때 호출됩니다."""
        self.is_slider_dragging = False

    def seek_video(self, value):
        """슬라이더 값에 따라 비디오 재생 위치를 변경합니다."""
        if hasattr(self, 'player') and self.is_slider_dragging:
            try:
                # 슬라이더 값을 초 단위로 변환 (value는 밀리초 단위)
                seconds = value / 1000.0  # 밀리초를 초 단위로 변환 (1000으로 나눔)
                # MPV의 seek 함수를 사용하여 정확한 위치로 이동
                self.player.command('seek', seconds, 'absolute')
            except Exception as e:
                print(f"비디오 위치 변경 중 오류 발생: {e}")

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
        """MPV의 재생 상태에 따라 버튼 텍스트 업데이트 및 슬라이더 동기화"""
        if hasattr(self, 'player'):
            try:
                if not self.player:  # MPV가 유효한지 확인
                    return  # 슬라이더 업데이트를 건너뜁니다.

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

        # 이미지 파일이 있을 때만 정보 표시
        if self.image_files:
            image_info = f"{self.current_index + 1} / {len(self.image_files)}"
            self.image_info_label.setText(image_info)
            
            # 창 크기에 따라 폰트 크기 동적 조절
            window_width = self.width()
            font_size = max(12, min(32, int(window_width * 0.02)))
            
            # 패딩과 마진도 창 크기에 비례하여 조절
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
            
            # 레이블 크기와 위치 조정
            self.image_info_label.adjustSize()
            
            # 우측 상단에 위치 (여백은 창 크기에 비례)
            x = self.width() - self.image_info_label.width() - margin
            y = margin + 20
            
            self.image_info_label.move(x, y)
            self.image_info_label.show()
            self.image_info_label.raise_()

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
        
        # 좌측 상단에 위치 (여백은 창 크기에 비례)
        self.message_label.move(margin, margin + 20)
        
        QTimer.singleShot(2000, self.message_label.close)

    # 현재 이미지를 다른 폴더로 복사하는 메서드입니다.
    def copy_image_to_folder(self, folder_path):
        # 현재 이미지 경로가 존재하고, 폴더 경로도 제공되었으면 복사를 시작합니다.
        if self.current_image_path and folder_path:
            try:
                # 이전에 표시된 메시지 레이블이 존재하면 닫습니다.
                if hasattr(self, 'message_label') and self.message_label.isVisible():
                    self.message_label.close()

                # 이미지 복사할 대상 경로를 생성합니다.
                target_path = self.get_unique_file_path(folder_path, self.current_image_path)  # 고유한 파일 경로 생성

                # 이미지 파일을 복사합니다.
                shutil.copy2(self.current_image_path, target_path)  # 파일 복사 (메타데이터도 함께 복사)
                print(f"Copied: {self.current_image_path} -> {target_path}")  # 복사된 경로 출력

                # 사용자에게 복사 완료 메시지를 보여줍니다.
                self.message_label = QLabel(f"경로 {target_path}로 이미지가 복사되었습니다.", self)
                self.message_label.setStyleSheet("QLabel {"
                    "color: white;"
                    "background-color: rgba(52, 73, 94, 0.9);"
                    "font-size: 32px;"
                    "padding: 8px 12px;"
                    "border-radius: 3px;"
                    "font-weight: normal;"
                "}")
                self.message_label.setAlignment(Qt.AlignCenter)  # 텍스트를 중앙 정렬
                self.message_label.show()  # 레이블을 화면에 표시

                # 메시지 레이블 크기를 자동으로 조정합니다.
                self.message_label.adjustSize()

                # 메시지 레이블을 좌측 상단에 위치시킵니다 (x+30, y+50)
                self.message_label.move(30, 50)

                # 2초 후 메시지 레이블을 자동으로 닫습니다.
                QTimer.singleShot(2000, self.message_label.close)  # 2000ms 후에 메시지 박스를 닫음

                # 이미지 복사 후 자동으로 다음 이미지로 이동합니다.
                self.show_next_image()  # 복사 후 다음 이미지 표시
            except Exception as e:
                print(f"Error copying {self.current_image_path} to {folder_path}: {e}")  # 에러 발생 시 출력

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
        if event.angleDelta().y() > 0:  # 마우스 휠을 위로 굴렸을 때
            self.show_previous_image()  # 이전 이미지로 이동
        elif event.angleDelta().y() < 0:  # 마우스 휠을 아래로 굴렸을 때
            self.show_next_image()  # 다음 이미지로 이동

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
        """앱 종료 시 MPV 정리"""
        self.stop_video()
        if hasattr(self, 'player'):
            try:
                self.player.terminate()
            except Exception as e:
                print(f"MPV 종료 중 오류 발생: {e}")
        
        # PSD 캐시 정리
        self.psd_cache.clear()
        
        if hasattr(self, 'message_label') and self.message_label.isVisible():
            self.message_label.close()
        event.accept()

    def toggle_mute(self):
        """음소거 상태를 토글합니다."""
        if hasattr(self, 'player'):
            self.player.mute = not self.player.mute  # MPV의 음소거 상태를 토글
            # 버튼 아이콘 변경 (음소거 상태에 따라)
            if self.player.mute:
                self.mute_button.setText("🔇")  # 음소거 해제 아이콘
            else:
                self.mute_button.setText("🔈")  # 음소거 아이콘

    def adjust_volume(self, volume):
        """음량을 조절합니다."""
        if hasattr(self, 'player'):
            # 현재 슬라이더 값을 가져와서 볼륨을 설정
            volume_value = self.volume_slider.value()  # 슬라이더의 현재 값
            self.player.volume = volume_value  # MPV의 볼륨 설정

# 메인 함수
def main():
    app = QApplication(sys.argv)  # Qt 애플리케이션 객체 생성
    viewer = ImageViewer()  # ImageViewer 클래스의 객체 생성
    viewer.show()  # 뷰어 창 표시
    sys.exit(app.exec_())  # 이벤트 루프 실행

# 프로그램 실행 시 main() 함수 실행
if __name__ == "__main__":
    main()  # 메인 함수 실행
