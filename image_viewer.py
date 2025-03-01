# GIF 크기를 조정하는 메서드입니다.
import sys
import os
import shutil
import re
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QFileDialog, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QFont, QMovie
from PyQt5.QtCore import Qt, QSize, QTimer
import cv2
from PIL import Image

class ImageViewer(QWidget):  # 이미지 뷰어 클래스를 정의
    def __init__(self):
        super().__init__()  # QWidget의 초기화 메소드 호출

        self.setWindowTitle('Image Viewer')  # 창의 제목을 'Image Viewer'로 설정
        self.setGeometry(100, 100, 800, 600)  # 창의 위치(100, 100)과 크기(800x600) 설정
        self.showMaximized()  # 창을 최대화된 상태로 시작

        layout = QVBoxLayout()  # 수직 레이아웃을 생성

        self.image_label = QLabel(self)  # 이미지를 표시할 QLabel 생성
        self.image_label.setAlignment(Qt.AlignCenter)  # QLabel의 텍스트를 중앙 정렬
        layout.addWidget(self.image_label)  # 이미지 레이블을 레이아웃에 추가

        self.image_info_label = QLabel(self)  # 이미지 정보 표시를 위한 QLabel 생성
        self.image_info_label.setAlignment(Qt.AlignCenter)  # QLabel의 텍스트를 중앙 정렬
        layout.addWidget(self.image_info_label)  # 이미지 정보 레이블을 레이아웃에 추가

        self.open_button = QPushButton('Open Image Folder', self)  # 'Open Image Folder' 버튼 생성
        self.open_button.clicked.connect(self.open_folder)  # 버튼 클릭 시 open_folder 메소드 연결
        layout.addWidget(self.open_button)  # 버튼을 레이아웃에 추가

        self.set_base_folder_button = QPushButton('Set Base Folder', self)  # 'Set Base Folder' 버튼 생성
        self.set_base_folder_button.clicked.connect(self.set_base_folder)  # 버튼 클릭 시 set_base_folder 메소드 연결
        layout.addWidget(self.set_base_folder_button)  # 버튼을 레이아웃에 추가

        # 12개의 빈 버튼 4줄 추가
        self.buttons = []  # 빈 버튼 리스트 초기화
        for _ in range(4):  # 4줄을 생성
            button_layout = QHBoxLayout()  # 가로 배치 레이아웃 생성
            button_row = []  # 각 버튼을 저장할 리스트
            for _ in range(12):  # 각 줄에 12개의 버튼 생성
                empty_button = QPushButton('')  # 빈 버튼 생성
                empty_button.clicked.connect(self.on_button_click)  # 버튼 클릭 시 on_button_click 메소드 연결
                button_row.append(empty_button)  # 버튼을 행에 추가
                button_layout.addWidget(empty_button)  # 버튼을 가로 배치 레이아웃에 추가
            self.buttons.append(button_row)  # 각 버튼 행을 전체 버튼 리스트에 추가
            layout.addLayout(button_layout)  # 가로 배치 레이아웃을 수직 레이아웃에 추가

        self.setLayout(layout)  # 전체 레이아웃을 설정

        self.image_files = []  # 이미지 파일 리스트 초기화
        self.current_index = 0  # 현재 이미지의 인덱스 초기화
        self.current_image_path = None  # 현재 이미지 경로 초기화
        self.base_folder = None  # 기준 폴더 변수 초기화

        self.setFocusPolicy(Qt.StrongFocus)  # 강한 포커스를 설정 (위젯이 포커스를 받을 수 있도록 설정)

        self.cap = None  # 비디오 캡처 객체 초기화
        self.timer = QTimer(self)  # 타이머 객체 생성
        self.timer.timeout.connect(self.update_video_frame)  # 타이머가 작동할 때마다 update_video_frame 메소드 호출

    def set_base_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Set Base Folder")  # 폴더 선택 대화상자 열기
        if folder_path:  # 폴더가 선택되었으면
            self.base_folder = folder_path  # 선택한 폴더 경로를 기준 폴더로 설정
            print(f"Base folder set to: {self.base_folder}")  # 기준 폴더 경로 출력

            # 버튼들 초기화
            for row in self.buttons:  # 버튼 행마다
                for button in row:  # 버튼마다
                    button.setText('')  # 버튼 텍스트 초기화
                    button.setToolTip('')  # 버튼 툴팁 초기화

            # 하위 폴더들을 가져와서 버튼에 경로 설정
            subfolders = [f.path for f in os.scandir(self.base_folder) if f.is_dir()]  # 하위 폴더 경로 목록 가져오기
            subfolders.sort()  # 하위 폴더 목록을 정렬

            # 빈 버튼에 하위 폴더 경로를 설정
            for i, row in enumerate(self.buttons):  # 각 행에 대해
                for j, button in enumerate(row):  # 각 버튼에 대해
                    index = i * 12 + j  # 2D 배열에서 버튼의 인덱스 계산
                    if index < len(subfolders):  # 하위 폴더가 버튼보다 많지 않으면
                        button.setText(os.path.basename(subfolders[index]))  # 버튼 텍스트를 폴더 이름으로 설정
                        button.setToolTip(subfolders[index])  # 버튼 툴팁에 폴더 경로 설정

    def on_button_click(self):
        button = self.sender()  # 클릭된 버튼을 가져옴
        folder_path = button.toolTip()  # 버튼의 툴팁에서 폴더 경로 가져오기
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
        """현재 재생 중인 MP4를 즉시 정리하는 함수"""
        if self.cap is not None:  # 비디오 캡처 객체가 존재하면
            self.cap.release()  # 비디오 캡처 객체 해제
            self.cap = None  # 캡처 객체를 None으로 설정

        if self.timer.isActive():  # 타이머가 활성화 되어 있으면
            self.timer.stop()  # 타이머 중지

    def show_image(self, image_path):
        # 새 이미지나 GIF가 들어오면 즉시 MP4 정리
        self.stop_video()  # 비디오 중지
        
        if image_path.lower().endswith('.psd'):  # PSD 파일 처리
            # PSD 파일을 PNG로 변환
            image = Image.open(image_path)  # PIL을 사용하여 PSD 파일 열기
            temp_path = 'temp_image.png'  # 임시 파일 경로
            image.save(temp_path)  # PNG로 저장
            pixmap = QPixmap(temp_path)  # QPixmap으로 이미지 변환
            os.remove(temp_path)  # 임시 파일 삭제
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))  # QLabel에 이미지 표시
        elif image_path.lower().endswith('.gif'):  # GIF 파일 처리
            movie = QMovie(image_path)  # QMovie를 사용하여 GIF 파일 처리
            self.scale_gif(movie)  # GIF 크기 비율 맞추기
            self.image_label.setMovie(movie)  # GIF를 QLabel에 표시
            movie.start()  # GIF 재생 시작
        elif image_path.lower().endswith('.webp'):  # WEBP 파일 처리
            self.show_webp_animation(image_path)  # WEBP 애니메이션 처리
        elif image_path.lower().endswith('.mp4'):  # MP4 파일 처리
            self.play_video(image_path)  # MP4 비디오 재생
        else:
            pixmap = QPixmap(image_path)  # 그 외의 이미지 파일 처리
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))  # 이미지를 QLabel에 표시

        self.current_image_path = image_path  # 현재 이미지 경로 업데이트
        self.update_image_info()  # 이미지 정보 업데이트 메소드 호출

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

    # 비디오 파일을 재생하는 메서드입니다.
    def play_video(self, video_path):
        # OpenCV를 사용하여 비디오 캡처 객체를 생성합니다.
        self.cap = cv2.VideoCapture(video_path)  # video_path 경로의 비디오를 읽기 위한 캡처 객체 생성

        if not self.cap.isOpened():  # 비디오 파일이 제대로 열리지 않으면 에러 메시지를 출력
            print("Error: Could not open video.")
            return  # 비디오가 열리지 않으면 함수 종료

        # 타이머를 33ms로 설정하여 약 30fps로 비디오를 업데이트합니다.
        self.timer.start(33)  # 타이머를 시작하고, 33ms마다 프레임을 갱신

    # 비디오의 프레임을 업데이트하는 메서드입니다.
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
        # 이미지 파일 목록이 있으면 정보를 표시합니다.
        if self.image_files:
            # 현재 이미지의 순서와 전체 개수를 계산하여 텍스트로 표시합니다.
            image_info = f"{self.current_index + 1} / {len(self.image_files)}"  # 현재 이미지 번호와 전체 개수를 표시
            self.image_info_label.setText(image_info)  # 레이블에 정보 설정

            # 폰트 크기 설정 (텍스트가 너무 커지지 않도록 최소 크기로 설정)
            font = QFont()  # QFont 객체 생성
            font.setPointSize(10)  # 폰트 크기를 10으로 설정
            self.image_info_label.setFont(font)  # 레이블에 폰트 설정

            # 레이아웃의 높이를 제한하여 텍스트가 너무 길어지지 않도록 합니다.
            self.image_info_label.setFixedHeight(30)  # 레이블의 높이를 고정하여 30픽셀로 설정

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
        # 이전에 표시된 메시지 레이블이 존재하면 닫습니다
        if hasattr(self, 'message_label') and self.message_label.isVisible():
            self.message_label.close()

        # 메시지 레이블 생성 및 설정
        self.message_label = QLabel(message, self)
        self.message_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(52, 73, 94, 0.9);
                font-size: 36px;
                padding: 15px 25px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.show()

        # 메시지 레이블 크기를 자동으로 조정
        self.message_label.adjustSize()

        # 메시지 레이블을 좌측 상단에 위치 (x+30, y+50)
        self.message_label.move(30, 50)

        # 2초 후 메시지 레이블을 자동으로 닫음
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
                self.message_label.setStyleSheet("""
                    QLabel {
                        color: white;
                        background-color: rgba(52, 73, 94, 0.9);
                        font-size: 36px;
                        padding: 15px 25px;
                        border-radius: 5px;
                    }
                """)
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

# 메인 함수
def main():
    app = QApplication(sys.argv)  # Qt 애플리케이션 객체 생성
    viewer = ImageViewer()  # ImageViewer 클래스의 객체 생성
    viewer.show()  # 뷰어 창 표시
    sys.exit(app.exec_())  # 이벤트 루프 실행

# 프로그램 실행 시 main() 함수 실행
if __name__ == "__main__":
    main()  # 메인 함수 실행
