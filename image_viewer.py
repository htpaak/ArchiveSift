# GIF 크기를 조정하는 메서드입니다.
import sys
import os
import shutil
import re
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout, QSizePolicy, QSlider, QLayout
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QFont, QMovie, QCursor
from PyQt5.QtCore import Qt, QSize, QTimer, QEvent, QPoint, pyqtSignal
import cv2
from PIL import Image

# MPV DLL 경로를 PATH에 추가 (반드시 mpv 모듈을 import하기 전에 해야 함)
mpv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mpv')
os.environ["PATH"] = mpv_path + os.pathsep + os.environ["PATH"]

# 이제 mpv 모듈을 import
import mpv

# 커스텀 제목표시줄 클래스
class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setMouseTracking(True)
        
        # 제목표시줄 스타일 설정
        self.setStyleSheet("""
            background-color: rgba(52, 73, 94, 0.9);
            color: white;
        """)
        
        # 제목표시줄 레이아웃 설정
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 제목 라벨
        self.title_label = QLabel('Image Viewer')
        self.title_label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        # 최소화, 최대화, 닫기 버튼
        min_button = QPushButton('_')
        min_button.setStyleSheet("color: white; background: none; border: none;")
        min_button.clicked.connect(self.parent.showMinimized)
        
        max_button = QPushButton('□')
        max_button.setStyleSheet("color: white; background: none; border: none;")
        max_button.clicked.connect(self.toggle_maximize)
        
        close_button = QPushButton('×')
        close_button.setStyleSheet("color: white; background: none; border: none;")
        close_button.clicked.connect(self.parent.close)
        
        layout.addWidget(min_button)
        layout.addWidget(max_button)
        layout.addWidget(close_button)
        
        self.setFixedHeight(30)
        self.setLayout(layout)
    
    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.drag_position = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self.parent, 'drag_position'):
            if self.parent.isMaximized():
                self.parent.showNormal()
            
            self.parent.move(event.globalPos() - self.parent.drag_position)
            event.accept()
        super().mouseMoveEvent(event)

class ImageViewer(QWidget):  # 이미지 뷰어 클래스를 정의
    def __init__(self):
        super().__init__()  # QWidget의 초기화 메소드 호출

        # 프레임리스 윈도우 설정
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # 최대화 플래그를 설정
        self.setWindowState(Qt.WindowMaximized)
        
        # 배경색을 흰색으로 설정
        self.setStyleSheet("background-color: white;")

        # 버튼 스타일 설정
        button_style = """
            QPushButton {
                background-color: rgba(52, 73, 94, 0.9);
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
        """

        # 전체 레이아웃 설정
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
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
        container_layout.addWidget(self.image_label)
        
        # 재생 컨트롤 바 생성
        self.create_media_controls()
        
        # 이미지 정보 레이블 생성
        self.image_info_label = QLabel(self)
        self.image_info_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(52, 73, 94, 0.9);
                font-size: 32px;
                padding: 8px 12px;
                border-radius: 3px;
                font-weight: normal;
            }
        """)
        self.image_info_label.setAlignment(Qt.AlignCenter)
        self.image_info_label.hide()  # 초기에는 숨김
        
        # 제목표시줄 생성
        self.title_bar = QWidget(self)
        self.title_bar.setStyleSheet("background-color: rgba(52, 73, 94, 0.9);")
        self.title_bar.setFixedHeight(30)
        
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
        
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("color: white; background: none; border: none;")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(min_btn)
        title_layout.addWidget(max_btn)
        title_layout.addWidget(close_btn)
        
        # 초기에 제목표시줄 숨기기
        self.title_bar.hide()
        
        # 제목표시줄이 다른 위젯보다 앞에 표시되도록 설정
        self.title_bar.raise_()
        
        # 하단 버튼 레이아웃 생성
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # 상단 버튼들을 위한 수평 레이아웃 - Open Image Folder와 Set Base Folder 버튼을 한 줄로 배치
        top_buttons_layout = QHBoxLayout()
        top_buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # Open Image Folder 버튼에 스타일 적용
        self.open_button = QPushButton('Open Image Folder', self)
        self.open_button.setStyleSheet(button_style)
        self.open_button.clicked.connect(self.open_folder)
        top_buttons_layout.addWidget(self.open_button)
        
        # Set Base Folder 버튼에 스타일 적용
        self.set_base_folder_button = QPushButton('Set Base Folder', self)
        self.set_base_folder_button.setStyleSheet(button_style)
        self.set_base_folder_button.clicked.connect(self.set_base_folder)
        top_buttons_layout.addWidget(self.set_base_folder_button)
        
        # 수평 레이아웃을 하단 레이아웃에 추가
        bottom_layout.addLayout(top_buttons_layout)
        
        # 48개의 폴더 버튼에 스타일 적용
        self.buttons = []
        for _ in range(4):
            button_layout = QHBoxLayout()
            button_row = []
            for _ in range(12):
                empty_button = QPushButton('')
                empty_button.setStyleSheet(button_style)
                empty_button.clicked.connect(self.on_button_click)
                button_row.append(empty_button)
                button_layout.addWidget(empty_button)
            self.buttons.append(button_row)
            bottom_layout.addLayout(button_layout)

        # 메인 레이아웃에 위젯 추가
        main_layout.addWidget(self.image_container, 1)  # 이미지 컨테이너에 확장 비율 1 부여
        main_layout.addLayout(bottom_layout)

        self.image_files = []  # 이미지 파일 리스트 초기화
        self.current_index = 0  # 현재 이미지의 인덱스 초기화
        self.current_image_path = None  # 현재 이미지 경로 초기화
        self.base_folder = None  # 기준 폴더 변수 초기화

        self.setFocusPolicy(Qt.StrongFocus)  # 강한 포커스를 설정 (위젯이 포커스를 받을 수 있도록 설정)

        self.cap = None  # 비디오 캡처 객체 초기화
        self.timer = QTimer(self)  # 타이머 객체 생성
        self.timer.timeout.connect(self.update_video_frame)  # 타이머가 작동할 때마다 update_video_frame 메소드 호출

        # 지연된 최대화 확인을 위한 타이머 설정
        QTimer.singleShot(100, self.ensure_maximized)

        # 창이 최대화된 상태로 표시되도록 설정
        self.showMaximized()

        # 마우스 트래킹 활성화
        self.setMouseTracking(True)
        self.image_container.setMouseTracking(True)
        self.image_label.setMouseTracking(True)
        
        # 마우스 움직임을 감지하는 타이머 설정
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        self.mouse_check_timer.start(100)  # 100ms마다 확인
        
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

        # MPV 플레이어 생성
        self.player = mpv.MPV(ytdl=True, input_default_bindings=True, input_vo_keyboard=True)

    def ensure_maximized(self):
        """창이 최대화 상태인지 확인하고 그렇지 않으면 다시 최대화합니다."""
        if not self.isMaximized():
            self.showMaximized()

    def resizeEvent(self, event):
        """창 크기 변경 이벤트 처리"""
        if hasattr(self, 'title_bar'):
            self.title_bar.setGeometry(0, 0, self.width(), 30)
            # 항상 맨 앞에 표시
            self.title_bar.raise_()
        
        # 이미지 정보 레이블 위치 업데이트
        if hasattr(self, 'image_info_label') and self.image_info_label.isVisible():
            # 레이블 크기를 내용에 맞게 조정
            self.image_info_label.adjustSize()
            
            # 우측 상단에 위치 (30px 여백)
            x = self.width() - self.image_info_label.width() - 30
            self.image_info_label.move(x, 50)
        
        # 미디어 컨트롤 바 위치 및 크기 업데이트
        self.position_media_controls()
        self.update_controls_width()
        
        super().resizeEvent(event)
        # 창이 최대화 상태가 아니면 다시 최대화
        if not self.isMaximized():
            QTimer.singleShot(10, self.showMaximized)

    def mouseDoubleClickEvent(self, event):
        """더블 클릭 시 최대화 및 일반 창 상태를 전환합니다."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def set_base_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Set Base Folder")  # 폴더 선택 대화상자 열기
        if folder_path:  # 폴더가 선택되었으면
            self.base_folder = folder_path  # 선택한 폴더 경로를 기준 폴더로 설정
            print(f"Base folder set to: {self.base_folder}")  # 기준 폴더 경로 출력

            # 버튼들 초기화
            for row in self.buttons:  # 버튼 행마다
                for button in row:  # 버튼마다
                    button.setText('')  # 버튼 텍스트 초기화
                    button.setToolTip('')  # 버튼 툴크 초기화

            # 하위 폴더들을 가져와서 버튼에 경로 설정
            subfolders = [f.path for f in os.scandir(self.base_folder) if f.is_dir()]  # 하위 폴더 경로 목록 가져오기
            subfolders.sort()  # 하위 폴더 목록을 정렬

            # 빈 버튼에 하위 폴더 경로를 설정
            for i, row in enumerate(self.buttons):  # 각 행에 대해
                for j, button in enumerate(row):  # 각 버튼에 대해
                    index = i * 12 + j  # 2D 배열에서 버튼의 인덱스 계산
                    if index < len(subfolders):  # 하위 폴더가 버튼보다 많지 않으면
                        button.setText(os.path.basename(subfolders[index]))  # 버튼 텍스트를 폴더 이름으로 설정
                        button.setToolTip(subfolders[index])  # 버튼 툴크에 폴더 경로 설정

    def on_button_click(self):
        button = self.sender()  # 클릭된 버튼을 가져옴
        folder_path = button.toolTip()  # 버튼의 툴크에서 폴더 경로 가져오기
        print(f"Selected folder: {folder_path}")  # 선택된 폴더 경로 출력
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
        
        # MPV 정지
        if hasattr(self, 'player'):
            try:
                self.player.stop()
            except:
                pass

    def show_image(self, image_path):
        # 새 이미지나 GIF가 들어오면 즉시 MP4 정리
        self.stop_video()  # 비디오 중지
        
        # 모든 파일에 대해 컨트롤 바 표시 (미디어 파일 여부와 관계없이)
        self.media_controls_widget.show()
        self.media_controls_widget.raise_()  # 이미지 위에 표시
        
        # 파일 확장자 확인 (소문자로 변환)
        file_ext = os.path.splitext(image_path)[1].lower()
        
        # 미디어 파일 여부에 따라 처리
        is_media_file = file_ext in ['.gif', '.webp', '.mp4']
        
        if file_ext == '.psd':  # PSD 파일 처리
            # PSD 파일을 PNG로 변환
            image = Image.open(image_path)  # PIL을 사용하여 PSD 파일 열기
            temp_path = 'temp_image.png'  # 임시 파일 경로
            image.save(temp_path)  # PNG로 저장
            pixmap = QPixmap(temp_path)  # QPixmap으로 이미지 변환
            os.remove(temp_path)  # 임시 파일 삭제
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))  # QLabel에 이미지 표시
        elif file_ext == '.gif':  # GIF 파일 처리
            movie = QMovie(image_path)  # QMovie를 사용하여 GIF 파일 처리
            self.scale_gif(movie)  # GIF 크기 비율 맞추기
            self.image_label.setMovie(movie)  # GIF를 QLabel에 표시
            movie.start()  # GIF 재생 시작
        elif file_ext == '.webp':  # WEBP 파일 처리
            self.show_webp_animation(image_path)  # WEBP 애니메이션 처리
        elif file_ext == '.mp4':  # MP4 파일 처리
            self.play_video(image_path)  # MP4 비디오 재생
        else:
            pixmap = QPixmap(image_path)  # 그 외의 이미지 파일 처리
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))  # 이미지를 QLabel에 표시

        # 컨트롤 바 내 버튼 상태 조정 (미디어 파일 여부에 따라)
        if hasattr(self, 'play_button'):
            self.play_button.setEnabled(is_media_file)
            # 미디어 파일이 아닌 경우 버튼 투명도 낮춤
            if not is_media_file:
                self.play_button.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: rgba(255, 255, 255, 0.5);  /* 반투명 */
                        border: none;
                        font-size: 22px;
                        padding: 3px;
                    }
                """)
            else:
                self.play_button.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: white;
                        border: none;
                        font-size: 22px;
                        padding: 3px;
                    }
                    QPushButton:hover {
                        background-color: rgba(80, 80, 80, 0.5);
                    }
                """)

        self.current_image_path = image_path  # 현재 이미지 경로 업데이트
        self.update_image_info()  # 이미지 정보 업데이트 메소드 호출
        
        # 제목표시줄과 이미지 정보 레이블을 앞으로 가져옴
        if hasattr(self, 'title_bar'):
            self.title_bar.raise_()
        if hasattr(self, 'image_info_label'):
            self.image_info_label.raise_()
        # 미디어 컨트롤 바도 앞으로 가져옴
        if hasattr(self, 'media_controls_widget') and self.media_controls_widget.isVisible():
            self.media_controls_widget.raise_()

    def show_webp_animation(self, image_path):
        # WEBP 애니메이션을 처리하기 위해 QImageReader를 사용
        reader = QImageReader(image_path)  # QImageReader 객체 생성

        # 이미지를 로드하고 애니메이션으로 처리
        if reader.supportsAnimation():  # 애니메이션을 지원하면
            movie = QMovie(image_path)  # QMovie 객체로 애니메이션 처리
            movie.setCacheMode(QMovie.CacheAll)  # 애니메이션 전체를 캐시로 설정
            self.scale_gif(movie)  # GIF와 동일하게 크기 비율 맞추기

            self.image_label.setMovie(movie)  # 애니메이션을 QLabel에 표시
            movie.start()  # 애니메이션 시작

    def scale_gif(self, movie):
        # 첫 번째 프레임으로 이동하여 이미지 데이터를 얻어옵니다.
        movie.jumpToFrame(0)  # 첫 번째 프레임으로 이동
        image = movie.currentImage()  # 현재 프레임의 이미지를 얻음

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

        # 새로 계산된 크기로 GIF를 설정합니다.
        movie.setScaledSize(QSize(new_width, new_height))  # 크기를 새로 계산된 크기로 설정

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
            
            # 비디오 파일 재생
            self.player.play(video_path)
            
            # 컨트롤 연결
            if hasattr(self, 'play_button'):
                self.play_button.clicked.connect(self.toggle_play_pause)
            if hasattr(self, 'volume_slider'):
                self.volume_slider.valueChanged.connect(self.set_volume)
            if hasattr(self, 'mute_button'):
                self.mute_button.clicked.connect(self.toggle_mute)
            
            # 비디오 정보 업데이트
            self.current_image_path = video_path
            
        except Exception as e:
            print(f"MPV 재생 오류: {e}")

    def toggle_play_pause(self):
        """재생/일시정지 토글"""
        if not hasattr(self, 'player'):
            return
        
        # MPV 재생 상태 토글
        paused = self.player.pause
        self.player.pause = not paused
        
        # 버튼 텍스트 업데이트
        self.play_button.setText("❚❚" if not paused else "▶")

    def set_volume(self, value):
        """볼륨 설정"""
        if not hasattr(self, 'player'):
            return
        
        self.player.volume = value

    def toggle_mute(self):
        """음소거 토글"""
        if not hasattr(self, 'player'):
            return
        
        muted = self.player.mute
        self.player.mute = not muted
        self.mute_button.setText("🔇" if not muted else "🔊")

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

    # 이미지 정보 (현재 이미지 번호와 전체 이미지 개수)를 하단에 표시하는 메서드입니다.
    def update_image_info(self):
        if self.image_files:
            # 현재 이미지의 순서와 전체 개수를 계산하여 텍스트로 표시
            image_info = f"{self.current_index + 1} / {len(self.image_files)}"
            self.image_info_label.setText(image_info)
            
            # 레이블 크기를 내용에 맞게 조정
            self.image_info_label.adjustSize()
            
            # 우측 상단에 위치 (30px 여백)
            x = self.width() - self.image_info_label.width() - 30
            self.image_info_label.move(x, 50)
            
            # 레이블을 표시하고 앞으로 가져오기
            self.image_info_label.show()
            self.image_info_label.raise_()  # 다른 위젯보다 앞으로 가져옴

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
        self.message_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(52, 73, 94, 0.9);
                font-size: 32px;
                padding: 8px 12px;
                border-radius: 3px;
                font-weight: normal;
            }
        """)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.show()
        self.message_label.adjustSize()
        self.message_label.move(30, 50)
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
            
            # 마우스가 제목표시줄 영역(상단 30픽셀)에 있는지 확인
            if local_pos.y() < 30:
                if not self.title_bar.isVisible():
                    print("마우스가 상단에 있어 제목표시줄 표시")  # 디버깅용
                    self.title_bar.show()
                    self.title_bar.raise_()  # 다른 위젯보다 앞으로 가져옴
            else:
                if self.title_bar.isVisible():
                    self.title_bar.hide()
        
        return super().eventFilter(obj, event)

    # toggle_maximize 메소드 추가 (이름을 toggle_maximize_state로 변경)
    def toggle_maximize_state(self):
        """최대화 상태와 일반 상태를 토글합니다."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def check_mouse_position(self):
        """타이머로 주기적으로 마우스 위치를 확인합니다."""
        global_pos = QCursor.pos()
        local_pos = self.mapFromGlobal(global_pos)
        
        # 마우스가 윈도우 내에 있고, Y 좌표가 30 미만인지 확인
        if self.rect().contains(local_pos) and local_pos.y() < 30:
            if not self.title_bar.isVisible():
                print("타이머: 마우스가 상단에 있어 제목표시줄 표시")  # 디버깅용
                self.title_bar.show()
                self.title_bar.raise_()  # 다른 위젯보다 앞으로 가져옴
        else:
            if self.title_bar.isVisible():
                self.title_bar.hide()

    def mousePressEvent(self, event):
        """마우스 버튼 누름 이벤트 처리"""
        if event.button() == Qt.LeftButton and event.y() < 30:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트 처리"""
        # 창 드래그 처리
        if hasattr(self, 'drag_position') and event.buttons() == Qt.LeftButton and event.y() < 30:
            if self.isMaximized():
                self.showNormal()
            self.move(event.globalPos() - self.drag_position)
        
        super().mouseMoveEvent(event)

    def create_media_controls(self):
        """재생 컨트롤 바 UI 생성"""
        # 재생 컨트롤 바 스타일
        controls_style = """
            background-color: rgba(40, 40, 40, 0.7);  /* 반투명 배경 */
            color: white;
            border: none;
            border-radius: 5px;  /* 약간의 둥근 모서리 추가 */
        """
        
        button_style = """
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 22px;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 80, 0.5);
            }
        """
        
        slider_style = """
            QSlider::groove:horizontal {
                height: 3px;
                background: #555555;
                margin: 0px;
                border-radius: 1px;
            }
            QSlider::handle:horizontal {
                background: #1E90FF;
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }
            QSlider::sub-page:horizontal {
                background: #1E90FF;
                border-radius: 1px;
            }
        """
        
        # 미디어 컨트롤 메인 컨테이너 - 부모를 self로 설정하여 이미지 위에 표시
        self.media_controls_widget = QWidget(self)
        self.media_controls_widget.setStyleSheet("background-color: transparent;")
        
        # 가운데 정렬을 위한 수평 레이아웃
        main_layout = QHBoxLayout(self.media_controls_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 실제 컨트롤 위젯
        controls_widget = QWidget()
        controls_widget.setStyleSheet(controls_style)
        controls_widget.setFixedHeight(45)  # 컨트롤 바 높이 유지
        
        # 컨트롤 위젯의 너비 설정 - 화면 너비의 40%로 확대
        screen_width = self.width()
        controls_widget.setFixedWidth(int(screen_width * 0.40))  # 화면 너비의 40% 유지
        
        # 레이아웃 균형을 맞추기 위한 여백 조정
        main_layout.addStretch(1)  # 왼쪽 여백
        main_layout.addWidget(controls_widget)
        main_layout.addStretch(1)  # 오른쪽 여백
        
        # 실제 컨트롤 요소를 위한 레이아웃
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(6, 0, 6, 0)  # 여백 유지
        controls_layout.setSpacing(3)  # 요소 간 간격 유지
        
        # 재생/일시정지 버튼
        self.play_button = QPushButton("▶")
        self.play_button.setStyleSheet(button_style)
        self.play_button.setFixedSize(32, 32)  # 버튼 크기 유지
        
        # 좌측 회전 버튼 - 아이콘만 사용
        self.rotate_left_button = QPushButton("⟲")
        self.rotate_left_button.setStyleSheet(button_style)
        self.rotate_left_button.setFixedSize(32, 32)  # 원래 크기로 복원
        
        # 우측 회전 버튼 - 아이콘만 사용
        self.rotate_right_button = QPushButton("⟳")
        self.rotate_right_button.setStyleSheet(button_style)
        self.rotate_right_button.setFixedSize(32, 32)  # 원래 크기로 복원
        
        # 현재 시간 레이블
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: white; font-size: 18px;")  # 폰트 크기 유지
        self.current_time_label.setFixedWidth(50)  # 너비 유지
        
        # 재생 슬라이더 - 비율 유지하면서 조정 (40%에 맞게 조정)
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setStyleSheet(slider_style)
        self.time_slider.setRange(0, 100)
        self.time_slider.setValue(0)
        self.time_slider.setMinimumWidth(int(screen_width * 0.10))  # 비율 유지 (9% * 40/35 = 약 10%)
        
        # 총 시간 레이블
        self.total_time_label = QLabel("00:01")
        self.total_time_label.setStyleSheet("color: white; font-size: 18px;")  # 폰트 크기 유지
        self.total_time_label.setFixedWidth(50)  # 너비 유지
        
        # 음소거 버튼
        self.mute_button = QPushButton("🔊")
        self.mute_button.setStyleSheet(button_style)
        self.mute_button.setFixedSize(32, 32)  # 버튼 크기 유지
        
        # 음량 조절 슬라이더 - 비율 유지하면서 조정
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setStyleSheet(slider_style)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)  # 기본값 100%
        self.volume_slider.setFixedWidth(int(120 * (40/25)))  # 비율 유지 (약 192px)
        
        # 레이아웃에 위젯 추가 - 요청한 순서대로 배치
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.rotate_left_button)
        controls_layout.addWidget(self.rotate_right_button)
        controls_layout.addWidget(self.current_time_label)
        controls_layout.addWidget(self.time_slider, 1)
        controls_layout.addWidget(self.total_time_label)
        controls_layout.addWidget(self.mute_button)
        controls_layout.addWidget(self.volume_slider)
        
        # 초기에는 컨트롤 바 숨기기
        self.media_controls_widget.hide()
        
        # 미디어 컨트롤 위젯 초기 위치 설정 - 하단에 배치
        self.position_media_controls()

    def position_media_controls(self):
        """미디어 컨트롤 바의 위치를 이미지 영역 하단에 배치"""
        if hasattr(self, 'media_controls_widget') and self.media_controls_widget:
            # 이미지 컨테이너 정보 가져오기
            container_rect = self.image_container.geometry()
            
            # 컨트롤 바 높이
            control_height = 45
            
            # 이미지 컨테이너 하단에 배치 (5px 여백)
            control_y = container_rect.y() + container_rect.height() - control_height - 5
            
            # 수평 가운데 정렬
            self.media_controls_widget.setGeometry(
                0, 
                control_y, 
                self.width(), 
                control_height
            )
            
            # 항상 다른 위젯보다 앞에 표시
            self.media_controls_widget.raise_()

    def update_controls_width(self):
        """미디어 컨트롤 바의 너비를 창 크기에 맞게 업데이트"""
        if hasattr(self, 'media_controls_widget') and self.media_controls_widget:
            # media_controls_widget의 자식 중 스타일이 설정된 실제 컨트롤 위젯 찾기
            for widget in self.media_controls_widget.findChildren(QWidget):
                if widget != self.media_controls_widget and "rgba(40, 40, 40, 0.7)" in widget.styleSheet():
                    # 화면 너비의 40%로 설정
                    widget.setFixedWidth(int(self.width() * 0.40))
                    # 타임 슬라이더 너비도 함께 업데이트
                    if hasattr(self, 'time_slider'):
                        self.time_slider.setMinimumWidth(int(self.width() * 0.10))  # 비율 유지
                    # 볼륨 슬라이더 너비도 함께 업데이트
                    if hasattr(self, 'volume_slider'):
                        self.volume_slider.setFixedWidth(int(120 * (40/25)))  # 비율 유지
                    break

    def closeEvent(self, event):
        """앱 종료 시 MPV 정리"""
        self.stop_video()
        if hasattr(self, 'player'):
            try:
                self.player.terminate()
            except:
                pass
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
