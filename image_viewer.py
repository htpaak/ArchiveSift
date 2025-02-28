import sys
import os
import shutil
import re
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QFont, QMovie
from PyQt5.QtCore import Qt, QSize, QTimer
import cv2
from PIL import Image

class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Image Viewer')
        self.setGeometry(100, 100, 800, 600)
        self.showMaximized()  # 창 최대화로 시작

        layout = QVBoxLayout()

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.image_info_label = QLabel(self)
        self.image_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_info_label)

        self.open_button = QPushButton('Open Image Folder', self)
        self.open_button.clicked.connect(self.open_folder)
        layout.addWidget(self.open_button)

        self.set_base_folder_button = QPushButton('Set Base Folder', self)
        self.set_base_folder_button.clicked.connect(self.set_base_folder)
        layout.addWidget(self.set_base_folder_button)

        # 12개의 빈 버튼 4줄 추가
        self.buttons = []  # 빈 버튼 리스트
        for _ in range(4):  # 4줄
            button_layout = QHBoxLayout()  # 가로 배치 레이아웃
            button_row = []  # 각 버튼을 저장할 리스트
            for _ in range(12):  # 12개의 버튼
                empty_button = QPushButton('')  # 빈 버튼
                empty_button.clicked.connect(self.on_button_click)  # 버튼 클릭 시 폴더 경로로 이동
                button_row.append(empty_button)
                button_layout.addWidget(empty_button)
            self.buttons.append(button_row)  # 각 줄을 리스트에 추가
            layout.addLayout(button_layout)

        self.setLayout(layout)

        self.image_files = []
        self.current_index = 0
        self.current_image_path = None
        self.base_folder = None  # 기준 폴더 변수 추가

        self.setFocusPolicy(Qt.StrongFocus)

        self.cap = None  # 비디오 캡처 객체
        self.timer = QTimer(self)  # 타이머 객체
        self.timer.timeout.connect(self.update_video_frame)  # 타이머가 작동할 때마다 호출

    def set_base_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Set Base Folder")
        if folder_path:
            self.base_folder = folder_path
            print(f"Base folder set to: {self.base_folder}")

            # 버튼들 초기화
            for row in self.buttons:
                for button in row:
                    button.setText('')  # 버튼 텍스트 비우기
                    button.setToolTip('')  # 툴팁 비우기

            # 하위 폴더들을 가져와서 버튼에 경로 설정
            subfolders = [f.path for f in os.scandir(self.base_folder) if f.is_dir()]
            subfolders.sort()

            # 빈 버튼에 하위 폴더 경로를 설정
            for i, row in enumerate(self.buttons):
                for j, button in enumerate(row):
                    index = i * 12 + j
                    if index < len(subfolders):
                        button.setText(os.path.basename(subfolders[index]))  # 버튼에 폴더 이름 설정
                        button.setToolTip(subfolders[index])  # 버튼 툴팁에 전체 경로 표시

    def on_button_click(self):
        button = self.sender()
        folder_path = button.toolTip()  # 버튼의 툴팁에서 폴더 경로 가져오기
        print(f"Selected folder: {folder_path}")
        self.copy_image_to_folder(folder_path)  # 해당 폴더로 이미지 복사

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Image Folder")

        if folder_path:
            self.image_files = self.get_image_files(folder_path)

            if self.image_files:
                self.image_files.sort()
                self.show_image(self.image_files[0])
                self.current_index = 0
            else:
                print("No valid image files found in the folder.")

    def get_image_files(self, folder_path):
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.psd', '.gif', '.mp4']
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if any(f.lower().endswith(ext) for ext in valid_extensions)]

    def stop_video(self):
        """현재 재생 중인 MP4를 즉시 정리하는 함수"""
        if self.cap is not None:  # self.cap이 존재할 때만 해제
            self.cap.release()  # 비디오 캡처 객체 해제
            self.cap = None

        if self.timer.isActive():
            self.timer.stop()  # 타이머 중지


    def show_image(self, image_path):
        # 새 이미지나 GIF가 들어오면 즉시 MP4 정리
        self.stop_video()
        
        if image_path.lower().endswith('.psd'):
            # PSD 파일을 PNG로 변환
            image = Image.open(image_path)
            temp_path = 'temp_image.png'
            image.save(temp_path)
            pixmap = QPixmap(temp_path)
            os.remove(temp_path)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        elif image_path.lower().endswith('.gif'):
            # GIF 파일 처리 (QMovie 사용)
            movie = QMovie(image_path)
            self.scale_gif(movie)  # GIF 크기 비율 맞추기
            self.image_label.setMovie(movie)
            movie.start()
        elif image_path.lower().endswith('.webp'):
            # WEBP 애니메이션 처리
            self.show_webp_animation(image_path)
        elif image_path.lower().endswith('.mp4'):
            # MP4 비디오 파일 처리
            self.play_video(image_path)
        else:
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.current_image_path = image_path
        self.update_image_info()  # 이미지 정보를 업데이트

    def show_webp_animation(self, image_path):
        # WEBP 애니메이션을 처리하기 위해 QImageReader를 사용
        reader = QImageReader(image_path)

        # 이미지를 로드하고 애니메이션으로 처리
        if reader.supportsAnimation():
            movie = QMovie(image_path)
            movie.setCacheMode(QMovie.CacheAll)
            self.scale_gif(movie)  # GIF와 동일하게 크기 비율 맞추기

            self.image_label.setMovie(movie)
            movie.start()

    def scale_gif(self, movie):
        # 첫 번째 프레임을 얻어서 GIF의 원본 비율을 계산합니다.
        movie.jumpToFrame(0)  # 첫 번째 프레임으로 이동
        image = movie.currentImage()

        # 원본 이미지에서 비율 계산
        original_width = image.width()
        original_height = image.height()

        # GIF 비율 계산 (가로 / 세로)
        if original_height == 0:
            original_height = 1  # 0으로 나누는 것을 방지
        aspect_ratio = original_width / original_height

        # image_label의 크기
        label_width = self.image_label.width()
        label_height = self.image_label.height()

        # 원본 비율에 맞게 크기를 계산
        if label_width / label_height > aspect_ratio:
            # 세로가 더 좁은 경우, 세로에 맞춰 크기 조정
            new_height = label_height
            new_width = int(new_height * aspect_ratio)
        else:
            # 가로가 더 좁은 경우, 가로에 맞춰 크기 조정
            new_width = label_width
            new_height = int(new_width / aspect_ratio)

        # 스케일된 크기 설정
        movie.setScaledSize(QSize(new_width, new_height))

    def play_video(self, video_path):
        # OpenCV로 비디오 캡처 객체 생성
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            print("Error: Could not open video.")
            return

        # 타이머를 33ms로 설정하여 대략 30fps로 업데이트
        self.timer.start(33)

    def update_video_frame(self):
        # 비디오에서 프레임을 읽어옴
        ret, frame = self.cap.read()

        if ret:
            # OpenCV의 BGR 형식을 RGB로 변환
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # numpy 배열을 QImage로 변환
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            qimg = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)

            # QImage를 QPixmap으로 변환하여 라벨에 표시
            pixmap = QPixmap.fromImage(qimg)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # 비디오의 끝에 도달하면 처음으로 돌아가기
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def update_image_info(self):
        # 현재 이미지의 순서와 전체 개수를 하단에 표시
        if self.image_files:
            image_info = f"{self.current_index + 1} / {len(self.image_files)}"
            self.image_info_label.setText(image_info)

            # 폰트 크기 조정 (세로 길이가 너무 길지 않도록)
            font = QFont()
            font.setPointSize(10)  # 폰트 크기 설정 (최소로 설정)
            self.image_info_label.setFont(font)

            # 레이아웃 크기 제한
            self.image_info_label.setFixedHeight(30)  # 레이블의 세로 길이를 최소로 설정

    def show_next_image(self):
        if self.image_files:
            self.current_index = (self.current_index + 1) % len(self.image_files)
            self.show_image(self.image_files[self.current_index])

    def show_previous_image(self):
        if self.image_files:
            self.current_index = (self.current_index - 1) % len(self.image_files)
            self.show_image(self.image_files[self.current_index])


    def copy_image_to_folder(self, folder_path):
        if self.current_image_path and folder_path:
            try:

                # 이전 메시지 레이블이 존재하면 닫기
                if hasattr(self, 'message_label') and self.message_label.isVisible():
                    self.message_label.close()

                # 이미지 복사할 대상 경로 생성
                target_path = self.get_unique_file_path(folder_path, self.current_image_path)
                
                # 이미지 복사
                shutil.copy2(self.current_image_path, target_path)
                print(f"Copied: {self.current_image_path} -> {target_path}")
                
                # QLabel을 사용하여 메시지 표시
                self.message_label = QLabel(f"경로 {target_path}로 이미지가 복사되었습니다.", self)
                self.message_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); background-color: rgba(0, 0, 0, 0.8); font-size: 72px; ")  # 글자 크기 3배로 키우기
                self.message_label.setAlignment(Qt.AlignCenter)
                self.message_label.show()

                # 텍스트에 맞게 QLabel 크기 자동 조정
                self.message_label.adjustSize()

                # 메시지 위치 살짝 이동 (Y 좌표 50픽셀, X 좌표 30픽셀 이동)
                self.message_label.move(self.message_label.x() + 30, self.message_label.y() + 50)  # 오른쪽으로 30, 아래로 50픽셀 이동

                # 0.5초 후 메시지 박스 자동 닫기
                QTimer.singleShot(2000, self.message_label.close)  # 500ms 후에 메시지 박스 닫기
                
                # 이미지 복사 후 다음 이미지로 자동 이동
                self.show_next_image()  
            except Exception as e:
                print(f"Error copying {self.current_image_path} to {folder_path}: {e}")





    def get_unique_file_path(self, folder_path, image_path):
        # 파일 이름이 중복되지 않도록 새로운 파일 이름을 생성
        base_name = os.path.basename(image_path)
        name, ext = os.path.splitext(base_name)

        # 기존에 '(숫자)' 형식이 있으면 제거
        name = re.sub(r'\s?\(\d+\)', '', name)  # '(숫자)' 패턴 제거

        target_path = os.path.join(folder_path, f"{name}{ext}")
        
        counter = 1
        while os.path.exists(target_path):
            # 파일 이름이 존재하면 카운트를 증가시키면서 이름을 변경
            target_path = os.path.join(folder_path, f"{name} ({counter}){ext}")
            counter += 1

        return target_path

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.show_previous_image()
        elif event.key() == Qt.Key_Right:
            self.show_next_image()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.show_previous_image()
        elif event.angleDelta().y() < 0:
            self.show_next_image()

def main():
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()