import sys
import os
import shutil
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QLineEdit, QHBoxLayout
from PyQt5.QtGui import QPixmap, QMovie, QImageReader
from PyQt5.QtCore import Qt, QSize
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

        self.image_order_label = QLabel(self)
        self.image_order_label.setAlignment(Qt.AlignCenter)
        self.image_order_label.setFixedHeight(30)
        layout.addWidget(self.image_order_label)

        self.open_button = QPushButton('Open Image Folder', self)
        self.open_button.clicked.connect(self.open_folder)
        layout.addWidget(self.open_button)

        self.set_base_folder_button = QPushButton('Set Base Folder', self)
        self.set_base_folder_button.clicked.connect(self.set_base_folder)
        layout.addWidget(self.set_base_folder_button)

        self.folder_input = QLineEdit(self)
        self.folder_input.setPlaceholderText("Enter folder name and press Enter (Copy & Next)")
        self.folder_input.returnPressed.connect(self.copy_image)  # 복사 후 다음 이미지로 이동
        layout.addWidget(self.folder_input)

        # 12개의 빈 버튼 10줄 추가
        self.buttons = []  # 빈 버튼 리스트
        for _ in range(4):  # 10줄
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

    def set_base_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Set Base Folder")
        if folder_path:
            self.base_folder = folder_path
            print(f"Base folder set to: {self.base_folder}")

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
        # 이 부분에서 폴더를 열거나 다른 작업을 할 수 있습니다.

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Image Folder")

        if folder_path:
            self.image_files = self.get_image_files(folder_path)

            if self.image_files:
                self.image_files.sort()
                self.show_image(self.image_files[0])
                self.current_index = 0
                self.update_image_order()
            else:
                print("No valid image files found in the folder.")

    def get_image_files(self, folder_path):
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.psd', '.gif']
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if any(f.lower().endswith(ext) for ext in valid_extensions)]

    def show_image(self, image_path):
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

            # GIF의 크기를 미리 조정하기 전에 movie를 QLabel에 설정하지 않음
            self.scale_gif(movie)  # GIF 크기 비율 맞추기

            self.image_label.setMovie(movie)
            movie.start()
        elif image_path.lower().endswith('.webp'):
            # WEBP 애니메이션 처리
            self.show_webp_animation(image_path)
        else:
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        self.current_image_path = image_path

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

    def update_image_order(self):
        if self.image_files:
            self.image_order_label.setText(f"{self.current_index + 1} / {len(self.image_files)}")

    def show_next_image(self):
        if self.image_files:
            self.current_index = (self.current_index + 1) % len(self.image_files)
            self.show_image(self.image_files[self.current_index])
            self.update_image_order()

    def show_previous_image(self):
        if self.image_files:
            self.current_index = (self.current_index - 1) % len(self.image_files)
            self.show_image(self.image_files[self.current_index])
            self.update_image_order()

    def copy_image(self):
        if self.current_image_path and self.base_folder:
            folder_name = self.folder_input.text().strip()

            if folder_name:
                target_folder = os.path.join(self.base_folder, folder_name)

                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)

                try:
                    target_path = os.path.join(target_folder, os.path.basename(self.current_image_path))
                    shutil.copy2(self.current_image_path, target_path)  # ✅ 이동 대신 복사
                    print(f"Copied: {self.current_image_path} -> {target_path}")

                    self.folder_input.clear()
                    self.show_next_image()  # ✅ 복사 후 다음 이미지로 자동 이동
                except Exception as e:
                    print(f"Error copying {self.current_image_path}: {e}")
            else:
                print("Please enter a folder name.")
        else:
            print("No image selected or base folder not set.")

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec_())
