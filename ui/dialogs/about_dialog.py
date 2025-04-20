"""
프로그램 정보 대화상자 모듈

이 모듈은 프로그램의 정보를 보여주는 대화상자 클래스를 제공합니다.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QScrollArea, QWidget, QFrame)
from PyQt5.QtCore import Qt
from core.version import get_version_string, get_full_version_string, get_version_info

class AboutDialog(QDialog):
    """
    프로그램 정보를 표시하는 대화상자
    
    이 클래스는 프로그램의 정보를 보여주는 창을 만들어요.
    여기에는 프로그램 이름, 버전, 기능 설명, 만든 사람 등의 정보가 들어있어요.
    사용자가 프로그램에 대해 알고 싶을 때 이 창을 보여줘요.
    """
    
    def __init__(self, parent=None):
        """
        대화상자를 초기화하고 화면에 나타낼 내용을 설정해요.
        
        매개변수:
            parent: 이 창의 부모 창. 보통 메인 창이에요.
        """
        super().__init__(parent)
        # 버전 정보 가져오기
        version_info = get_version_info()
        
        self.setWindowTitle(f"ArchiveSift {get_full_version_string()}")  # 창의 제목에 버전 표시
        self.setMinimumWidth(500)  # 창의 최소 너비를 설정해요
        self.setMinimumHeight(400)  # 창의 최소 높이를 설정해요
        
        # 전체 레이아웃을 수직으로 배치해요
        # 레이아웃은 창 안에 있는 요소들을 어떻게 배치할지 정하는 거예요
        layout = QVBoxLayout(self)
        
        # 프로그램 제목 - 맨 위에 큰 글씨로 표시해요
        title_label = QLabel("ArchiveSift")
        title_label.setAlignment(Qt.AlignCenter)  # 가운데 정렬해요
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: rgba(52, 73, 94, 1.0);")  # 글씨 스타일을 설정해요
        layout.addWidget(title_label)
        
        # 버전 정보 - 프로그램의 버전과 만든 날짜를 보여줘요
        version_label = QLabel(f"Version: {version_info['full_version']} (Build Date: {version_info['build_date']})")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 구분선 - 제목과 내용을 구분하는 가로선이에요
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 스크롤 영역 추가 - 내용이 많아도 스크롤해서 볼 수 있게 해요
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # 내용에 맞게 크기가 조절되도록 해요
        scroll_area.setFrameShape(QFrame.NoFrame)  # 테두리를 없애요
        
        scroll_content = QWidget()  # 스크롤 영역 안에 들어갈 내용을 담을 위젯이에요
        scroll_layout = QVBoxLayout(scroll_content)  # 스크롤 내용도 수직으로 배치해요
        
        # 프로그램 설명 - 프로그램이 무엇인지 간단히 설명해요
        description = QLabel(
            "ArchiveSift is a powerful file organization tool designed to help you "
            "easily and quickly categorize and manage various media files, "
            "including images, videos, and animations. With its intuitive interface, "
            "you can view your media and instantly copy or move them to your desired folders."
        )
        description.setWordWrap(True)  # 글이 길면 자동으로 줄바꿈 해요
        description.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬해요
        description.setStyleSheet("font-size: 11pt;")  # 글씨 크기를 설정해요
        scroll_layout.addWidget(description)
        
        # 추가: 링크 섹션
        links_label = QLabel("<b>Links:</b>")
        links_label.setStyleSheet("font-size: 11pt; margin-top: 10px;") # 위쪽 여백 추가
        scroll_layout.addWidget(links_label)

        links_detail = QLabel(
            '• <a href="https://github.com/htpaak/ArchiveSift">GitHub Repository</a><br>'
            '• <a href="https://github.com/htpaak/ArchiveSift/releases/latest">Download Latest Version</a><br>'
            '• <a href="https://github.com/htpaak/ArchiveSift/discussions">Feedback</a>'
        )
        links_detail.setOpenExternalLinks(True) # 링크 클릭 시 외부 브라우저에서 열기
        links_detail.setStyleSheet("margin-left: 15px;")
        links_detail.setWordWrap(True)
        scroll_layout.addWidget(links_detail)
        # 링크 섹션 끝
        
        # Supported formats - Shows what file types this program can open
        # 지원 형식 관련 주석을 영어로 변경함 -> 영어: Supported formats - Shows what file types this program can open
        formats_label = QLabel("<b>Supported Formats:</b>")  # <b> tag makes text bold
        formats_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(formats_label)
        
        formats_detail = QLabel(
            "• Images: JPG, JPEG, PNG, GIF, WEBP, BMP, TIFF, TIF, ICO, PSD, HEIC, HEIF, AVIF, JPE, JPS, JFIF, JP2\n"  # • is a bullet symbol
            "• Camera RAW: CR2 (Canon), NEF (Nikon), ARW (Sony)\n"
            "• Videos: MP4, AVI, MKV, MOV, WMV, TS, M2TS, FLV, WEBM, 3GP, M4V, MPG, MPEG, VOB\n"
            "• Audio: WAV, FLAC, MP3, AAC, M4A, OGG\n"
            "• Animations: GIF, WEBP"
        )
        formats_detail.setStyleSheet("margin-left: 15px;")  # 왼쪽에 여백을 줘서 들여쓰기 효과를 줘요
        formats_detail.setWordWrap(True)
        scroll_layout.addWidget(formats_detail)
        
        # 주요 기능 - 이 프로그램으로 무엇을 할 수 있는지 보여줘요
        features_label = QLabel("<b>Main Features:</b>")
        features_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(features_label)
        
        features_detail = QLabel(
            "• Supports various image and video formats\n"
            "• Image zooming/scaling and rotation\n"
            "• Bookmarking feature for frequently used files\n"
            "• Custom keyboard shortcuts\n"
            "• Animation control for GIF and WEBP\n"
            "• Video playback and control\n"
            "• File copying and management\n"
            "• Quick folder navigation and movement"
        )
        features_detail.setStyleSheet("margin-left: 15px;")
        features_detail.setWordWrap(True)
        scroll_layout.addWidget(features_detail)
        
        # 사용된 라이브러리 - 이 프로그램을 만들 때 사용한 도구들이에요
        libs_label = QLabel("<b>Used Main Libraries:</b>")
        libs_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(libs_label)
        
        libs_detail = QLabel(
            "• PyQt5 - GUI framework\n"  # English: "• PyQt5 - GUI framework" | Korean: "• PyQt5 - GUI framework"
            "• OpenCV (cv2) - video and image processing\n"  # English: "• OpenCV (cv2) - video and image processing" | Korean: "• OpenCV (cv2) - video and image processing"
            "• Pillow (PIL) - image processing and conversion\n"  # English: "• Pillow (PIL) - image processing and conversion" | Korean: "• Pillow (PIL) - image processing and conversion"
            "• JSON - saving and loading settings"  # English: "• JSON - saving and loading settings" | Korean: "• JSON - saving and loading settings"
        )
        libs_detail.setStyleSheet("margin-left: 15px;")
        libs_detail.setWordWrap(True)
        scroll_layout.addWidget(libs_detail)
        
        # 개발자 정보 - 프로그램을 만든 사람의 연락처예요
        developer_label = QLabel("<b>Developer:</b>")
        developer_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(developer_label)
        
        developer_detail = QLabel("htpaak@gmail.com")
        developer_detail.setStyleSheet("margin-left: 15px;")
        developer_detail.setWordWrap(True)
        scroll_layout.addWidget(developer_detail)
        
        # 저작권 정보 - 프로그램의 저작권에 대한 정보예요
        copyright_label = QLabel("<b>Copyright:</b>")
        copyright_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(copyright_label)
        
        # 버전 정보에서 빌드 날짜를 이용하여 연도 추출
        year = version_info['build_date'].split('-')[0]
        copyright_detail = QLabel(f"© {year} All rights reserved.")
        copyright_detail.setStyleSheet("margin-left: 15px;")
        copyright_detail.setWordWrap(True)
        scroll_layout.addWidget(copyright_detail)
        
        # 스페이서 추가 - 내용 아래에 빈 공간을 추가해서 보기 좋게 만들어요
        scroll_layout.addStretch()
        
        # 스크롤 영역에 위젯 설정 - 우리가 만든 내용을 스크롤 영역에 넣어요
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # 확인 버튼 - 창을 닫을 수 있는 버튼이에요
        ok_button = QPushButton("OK")
        ok_button.setFixedWidth(100)  # 버튼의 너비를 고정해요
        ok_button.clicked.connect(self.accept)  # 버튼을 클릭하면 창이 닫혀요
        
        # 버튼 레이아웃 - 버튼을 오른쪽 아래에 배치해요
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 왼쪽에 빈 공간을 추가해서 버튼이 오른쪽으로 가게 해요
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout) 