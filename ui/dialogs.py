# 대화상자 모듈
# ==========================================================
# 이 파일에는 프로그램에서 사용하는 모든 대화상자들이 들어있어요.
# 대화상자란, 프로그램을 사용하다가 새로 뜨는 작은 창들을 말해요.
# 예를 들면, '프로그램 정보'를 보여주는 창이나 '설정'을 바꾸는 창이에요.
#
# 이 파일에 있는 중요한 클래스들:
# 1. AboutDialog: 프로그램 정보를 보여주는 창이에요. 버전, 만든 사람 등의 정보가 있어요.
# 2. KeyInputEdit: 키보드의 키를 입력받는 특별한 텍스트 상자에요. 단축키를 설정할 때 사용해요.
# 3. PreferencesDialog: 프로그램의 설정을 바꿀 수 있는 창이에요. 키보드 단축키 등을 바꿀 수 있어요.
# ==========================================================

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QFrame, QLineEdit, QScrollArea, QWidget, QStackedWidget)  # UI 요소
from PyQt5.QtCore import Qt, QSize, QEvent, pyqtSignal  # Qt 기본 기능
from PyQt5.QtGui import QFont, QIcon, QKeySequence  # 폰트, 아이콘 등

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
        self.setWindowTitle("프로그램 정보")  # 창의 제목을 설정해요
        self.setMinimumWidth(500)  # 창의 최소 너비를 설정해요
        self.setMinimumHeight(400)  # 창의 최소 높이를 설정해요
        
        # 전체 레이아웃을 수직으로 배치해요
        # 레이아웃은 창 안에 있는 요소들을 어떻게 배치할지 정하는 거예요
        layout = QVBoxLayout(self)
        
        # 프로그램 제목 - 맨 위에 큰 글씨로 표시해요
        title_label = QLabel("이미지 뷰어")
        title_label.setAlignment(Qt.AlignCenter)  # 가운데 정렬해요
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: rgba(52, 73, 94, 1.0);")  # 글씨 스타일을 설정해요
        layout.addWidget(title_label)
        
        # 버전 정보 - 프로그램의 버전과 만든 날짜를 보여줘요
        version_label = QLabel("버전: 1.1.0 (빌드 날짜: 2025-03-12)")
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
            "이 프로그램은 다양한 이미지 형식과 비디오를 볼 수 있는 고성능 뷰어입니다."
        )
        description.setWordWrap(True)  # 글이 길면 자동으로 줄바꿈 해요
        description.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬해요
        description.setStyleSheet("font-size: 11pt;")  # 글씨 크기를 설정해요
        scroll_layout.addWidget(description)
        
        # 지원 형식 - 이 프로그램이 어떤 파일들을 열 수 있는지 보여줘요
        formats_label = QLabel("<b>지원하는 형식:</b>")  # <b>태그는 글씨를 굵게 만들어요
        formats_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(formats_label)
        
        formats_detail = QLabel(
            "• 이미지: JPG, PNG, GIF, WEBP, BMP, TIFF, ICO, PSD 등\n"  # • 는 점 모양의 기호예요
            "• 비디오: MP4, AVI, MKV, MOV, WMV 등\n"
            "• 애니메이션: GIF, WEBP"
        )
        formats_detail.setStyleSheet("margin-left: 15px;")  # 왼쪽에 여백을 줘서 들여쓰기 효과를 줘요
        formats_detail.setWordWrap(True)
        scroll_layout.addWidget(formats_detail)
        
        # 주요 기능 - 이 프로그램으로 무엇을 할 수 있는지 보여줘요
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
        
        # 사용된 라이브러리 - 이 프로그램을 만들 때 사용한 도구들이에요
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
        
        # 개발자 정보 - 프로그램을 만든 사람의 연락처예요
        developer_label = QLabel("<b>개발:</b>")
        developer_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(developer_label)
        
        developer_detail = QLabel("htpaak@gmail.com")
        developer_detail.setStyleSheet("margin-left: 15px;")
        developer_detail.setWordWrap(True)
        scroll_layout.addWidget(developer_detail)
        
        # 저작권 정보 - 프로그램의 저작권에 대한 정보예요
        copyright_label = QLabel("<b>저작권:</b>")
        copyright_label.setStyleSheet("font-size: 11pt;")
        scroll_layout.addWidget(copyright_label)
        
        copyright_detail = QLabel("© 2025 저작권 소유자. 모든 권리 보유.")
        copyright_detail.setStyleSheet("margin-left: 15px;")
        copyright_detail.setWordWrap(True)
        scroll_layout.addWidget(copyright_detail)
        
        # 스페이서 추가 - 내용 아래에 빈 공간을 추가해서 보기 좋게 만들어요
        scroll_layout.addStretch()
        
        # 스크롤 영역에 위젯 설정 - 우리가 만든 내용을 스크롤 영역에 넣어요
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        # 확인 버튼 - 창을 닫을 수 있는 버튼이에요
        ok_button = QPushButton("확인")
        ok_button.setFixedWidth(100)  # 버튼의 너비를 고정해요
        ok_button.clicked.connect(self.accept)  # 버튼을 클릭하면 창이 닫혀요
        
        # 버튼 레이아웃 - 버튼을 오른쪽 아래에 배치해요
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 왼쪽에 빈 공간을 추가해서 버튼이 오른쪽으로 가게 해요
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)

class KeyInputEdit(QLineEdit):
    """
    키 입력을 위한 특별한 텍스트 상자
    
    이 클래스는 사용자가 키보드로 단축키를 입력할 때 사용해요.
    사용자가 눌러준 키 조합(예: Ctrl+S)을 인식하고 텍스트로 보여줘요.
    설정 창에서 단축키를 바꿀 때 사용돼요.
    """
    
    def __init__(self, parent=None):
        """
        키 입력 텍스트 상자를 초기화해요.
        
        매개변수:
            parent: 이 위젯의 부모 위젯
        """
        super().__init__(parent)
        self.key_value = None  # 입력된 키 값을 저장할 변수
        self.setReadOnly(True)  # 직접 텍스트를 입력할 수 없게 해요
        self.setPlaceholderText("여기를 클릭하고 키를 누르세요")  # 안내 텍스트를 설정해요
        
        # 예쁜 스타일을 추가해요
        self.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                font-weight: bold;
                color: #333;
            }
            
            QLineEdit:focus {
                background-color: #e0e8f0;
                border: 1px solid rgba(52, 73, 94, 1.0);
            }
        """)
        
        # 텍스트를 가운데 정렬해요
        self.setAlignment(Qt.AlignCenter)
        
    def keyPressEvent(self, event):
        """
        키가 눌렸을 때 호출되는 함수에요.
        눌린 키를 기억하고 화면에 표시해요.
        
        매개변수:
            event: 키 이벤트 정보(어떤 키가 눌렸는지 등)
        """
        modifiers = event.modifiers()  # Ctrl, Alt, Shift 같은 조합키가 눌렸는지 확인해요
        key = event.key()  # 어떤 키가 눌렸는지 가져와요
        
        # ESC, Tab 등의 특수 키는 무시해요
        # 이 키들은 대화상자나 프로그램 제어에 사용되므로 단축키로 설정하면 안 돼요
        if key in (Qt.Key_Escape, Qt.Key_Tab):
            return
        
        # 모디파이어(Ctrl, Alt, Shift)만 눌렀을 때는 처리하지 않아요
        # 단축키는 보통 모디파이어 + 일반 키의 조합이니까요
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        
        # 키 조합을 만들어요
        # 예: Ctrl+S는 Ctrl 모디파이어와 S 키의 조합이에요
        self.key_value = key  # 기본 키를 저장해요
        
        # 조합키가 함께 눌렸으면 추가해요
        if modifiers & Qt.ControlModifier:  # Ctrl 키가
            self.key_value |= Qt.ControlModifier
        if modifiers & Qt.AltModifier:  # Alt 키가 눌렸는지 확인하고 추가해요
            self.key_value |= Qt.AltModifier
        if modifiers & Qt.ShiftModifier:  # Shift 키가 눌렸는지 확인하고 추가해요
            self.key_value |= Qt.ShiftModifier
        
        # 눌린 키 조합을 사람이 읽을 수 있는 텍스트로 만들어요
        # 예: "Ctrl+S"
        text = ""
        
        # 각 모디파이어가 눌렸는지 확인하고 텍스트에 추가해요
        if modifiers & Qt.ControlModifier:
            text += "Ctrl+"
        if modifiers & Qt.AltModifier:
            text += "Alt+"
        if modifiers & Qt.ShiftModifier:
            text += "Shift+"
        
        # 일반 키의 이름을 가져와서 추가해요
        # 예: A, B, 1, F1 등
        key_text = QKeySequence(key).toString()
        
        # Enter/Return 키인 경우 특별히 처리
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            key_text = "Enter"  # 화면에는 'Enter'로 표시
            
        text += key_text
        self.setText(text)  # 만든 텍스트를 화면에 표시해요
        
        # 이벤트를 처리했다고 표시해요
        # 이렇게 하면 다른 곳에서 이 키 이벤트를 다시 처리하지 않아요
        event.accept()

class PreferencesDialog(QDialog):
    """
    환경 설정을 변경할 수 있는 대화상자
    
    이 클래스는 프로그램의 설정을 바꿀 수 있는 창을 만들어요.
    사용자가 자신이 원하는 대로 프로그램을 설정할 수 있어요.
    지금은 키보드 단축키 설정만 있지만, 나중에 다른 설정들도 추가할 수 있어요.
    """
    
    def __init__(self, parent=None, key_settings=None):
        """
        환경 설정 대화상자를 초기화해요.
        
        매개변수:
            parent: 이 창의 부모 창
            key_settings: 현재 저장된 키보드 단축키 설정 (없으면 기본값 사용)
        """
        super().__init__(parent)
        self.setWindowTitle("환경 설정")  # 창의 제목을 설정해요
        self.setMinimumWidth(900)  # 창의 최소 너비
        self.setMinimumHeight(600)  # 창의 최소 높이
        
        # 전체 창에 스타일을 적용해요
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                gridline-color: #e0e0e0;
                alternate-row-color: #f9f9f9;
                selection-background-color: rgba(52, 73, 94, 1.0);
                selection-color: white;
            }
            
            QPushButton {
                background-color: rgba(52, 73, 94, 1.0);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
            
            QPushButton:pressed {
                background-color: rgba(52, 73, 94, 1.0);
            }
            
            #resetButton {
                background-color: rgba(231, 76, 60, 0.9);
            }
            
            #resetButton:hover {
                background-color: rgba(231, 76, 60, 1.0);
            }
            
            #saveButton {
                background-color: #2ecc71;
            }
            
            #saveButton:hover {
                background-color: #27ae60;
            }
            
            #cancelButton {
                background-color: #95a5a6;
            }
            
            #cancelButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        # 기본 키 설정 정의
        # 이 설정은 사용자가 아무것도 설정하지 않았을 때 사용해요
        default_settings = {
            "next_image": Qt.Key_Right,                        # 오른쪽 화살표: 다음 이미지
            "prev_image": Qt.Key_Left,                         # 왼쪽 화살표: 이전 이미지
            "rotate_clockwise": Qt.Key_R,                      # R: 시계 방향 회전
            "rotate_counterclockwise": Qt.Key_L,               # L: 반시계 방향 회전
            "play_pause": Qt.Key_Space,                        # 스페이스바: 재생/일시정지
            "volume_up": Qt.Key_Up,                            # 위 화살표: 볼륨 증가
            "volume_down": Qt.Key_Down,                        # 아래 화살표: 볼륨 감소
            "toggle_mute": Qt.Key_M,                           # M: 음소거 전환
            "delete_image": Qt.Key_Delete,                     # Delete: 이미지 삭제
            "toggle_fullscreen": Qt.ControlModifier | Qt.Key_Return,  # Ctrl+Enter: 전체화면 전환
            "toggle_maximize_state": Qt.Key_Return             # Enter: 최대화 전환
        }
        
        # 전달받은 키 설정이 있으면 사용, 없으면 기본값 사용
        # copy()를 사용하는 이유는 원래 설정을 변경하지 않기 위해서예요
        self.key_settings = key_settings.copy() if key_settings else default_settings.copy()

        # 누락된 키가 있으면 기본값에서 추가
        # 프로그램을 업데이트하면서 새로운 단축키가 추가될 수 있어요
        for key, value in default_settings.items():
            if key not in self.key_settings:
                self.key_settings[key] = value
        
        # 키 이름 매핑은 그대로 유지
        # 코드에서 사용하는 키 이름을 사용자에게 보여줄 때 이 이름으로 바꿔요
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
            "toggle_maximize_state": "최대화 전환"
        }
        
        # 메인 레이아웃 - 수평 레이아웃으로 변경
        # 왼쪽에는 설정 메뉴 버튼들, 오른쪽에는 설정 내용이 표시돼요
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
                color: white;
                border-radius: 3px;
                margin: 2px;
            }
            
            QPushButton:hover {
                background-color: rgba(52, 73, 94, 1.0);
            }
            
            QPushButton:checked {
                background-color: rgba(52, 73, 94, 1.0);
                border-left: 4px solid rgba(231, 76, 60, 0.9);
            }
        """

        # 왼쪽 버튼들 생성 - 설정 카테고리 선택용
        self.left_buttons = []
        
        # 키보드 단축키 버튼
        self.keyboard_button = QPushButton("키보드 단축키")
        self.keyboard_button.setCheckable(True)  # 버튼을 체크 가능하게 만들어요 (눌렀을 때 눌린 상태 유지)
        self.keyboard_button.setChecked(True)    # 처음에는 이 버튼이 선택된 상태로 시작해요
        self.keyboard_button.setStyleSheet(button_style)
        self.keyboard_button.setIcon(QIcon("./icons/keyboard.png"))
        self.keyboard_button.setObjectName("keyboardButton")  # CSS에서 이 버튼을 참조할 수 있는 이름을 지정해요
        self.keyboard_button.clicked.connect(self.on_left_button_clicked)
        left_panel.addWidget(self.keyboard_button)
        self.left_buttons.append(self.keyboard_button)
        
        # 테마 버튼 (지금은 작동하지 않지만 나중에 추가할 기능이에요)
        self.theme_button = QPushButton("마우스 설정")
        self.theme_button.setCheckable(True)
        self.theme_button.setStyleSheet(button_style)
        self.theme_button.setIcon(QIcon("./icons/theme.png"))
        self.theme_button.setObjectName("themeButton")
        self.theme_button.clicked.connect(self.on_left_button_clicked)
        left_panel.addWidget(self.theme_button)
        self.left_buttons.append(self.theme_button)
        
        # 일반 설정 버튼 (지금은 작동하지 않지만 나중에 추가할 기능이에요)
        self.general_button = QPushButton("일반 설정")
        self.general_button.setCheckable(True)
        self.general_button.setStyleSheet(button_style)
        self.general_button.setIcon(QIcon("./icons/settings.png"))
        self.general_button.setObjectName("generalButton")
        self.general_button.clicked.connect(self.on_left_button_clicked)
        left_panel.addWidget(self.general_button)
        self.left_buttons.append(self.general_button)
        
        # 스페이서 추가 - 버튼들을 위쪽에 몰아넣기 위해 아래 공간을 채워요
        left_panel.addStretch()
        
        # 오른쪽 설정 내용 패널
        right_panel = QVBoxLayout()
        
        # 스택 위젯 생성 - 여러 설정 페이지를 쌓아두고 하나씩 보여주는 위젯이에요
        self.stack = QStackedWidget()
        
        # 키보드 설정 페이지 생성
        keyboard_page = QWidget()
        keyboard_layout = QVBoxLayout(keyboard_page)
        
        # 키 설정 테이블 생성
        self.table = QTableWidget()
        self.table.setColumnCount(2)  # 2개 열: 기능, 단축키
        self.table.setHorizontalHeaderLabels(["기능", "단축키"])  # 열 제목 설정
        
        # 테이블 설정
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # 첫 번째 열도 늘려서 채워요
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 두 번째 열도 늘려서 채워요
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # 행 단위로 선택되게 해요
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # 직접 편집은 불가능하게 해요
        self.table.verticalHeader().setVisible(False)  # 세로 헤더(행 번호)는 숨겨요
        self.table.setAlternatingRowColors(True)  # 행마다 배경색을 번갈아 가며 설정해요
        
        # 테이블 채우기
        self.table.setRowCount(len(self.key_settings))  # 설정 개수만큼 행 생성
        
        # 각 키 설정에 대한 행 추가
        row = 0
        for key, value in self.key_settings.items():
            # 기능 이름 칸
            name_item = QTableWidgetItem(self.key_names.get(key, key))
            self.table.setItem(row, 0, name_item)
            
            # 단축키 칸 - 특별한 키 처리 (Return/Enter 일관성 유지)
            key_text = QKeySequence(value).toString()
            
            # Return 키를 Enter로 일관되게 표시
            if (value & ~Qt.ControlModifier) == Qt.Key_Return:
                # Ctrl+Return 조합인 경우
                if value & Qt.ControlModifier:
                    key_text = "Ctrl+Enter"
                else:
                    key_text = "Enter"
            
            key_item = QTableWidgetItem(key_text)
            self.table.setItem(row, 1, key_item)
            
            # 행 번호와 키 이름 매핑 (나중에 어떤 단축키가 변경되었는지 알기 위해)
            key_item.setData(Qt.UserRole, key)
            
            row += 1
        
        # 테이블 클릭 시 호출될 함수 연결
        self.table.cellClicked.connect(self.cell_clicked)
        
        # 키 입력을 위한 위젯 생성 - 눌린 키를 감지하는 특별한 텍스트 상자
        self.key_input = KeyInputEdit()
        
        # 주석 처리: 아래 라인은 타입 에러를 유발하기 때문에 제거했어요
        # self.table.setItemDelegateForColumn(1, self.key_input)
        
        # 설명 라벨 추가
        help_label = QLabel("단축키를 변경하려면 해당 행을 클릭하세요. 그런 다음 원하는 키를 누르면 됩니다.")
        help_label.setStyleSheet("color: #555; font-style: italic;")
        
        # 버튼 생성
        button_layout = QHBoxLayout()
        
        # 기본값으로 초기화 버튼
        self.reset_button = QPushButton("기본값으로 초기화")
        self.reset_button.setObjectName("resetButton")  # CSS에서 참조할 이름
        self.reset_button.clicked.connect(self.reset_to_default)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()  # 중간에 빈 공간 추가
        
        # 취소 버튼
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)  # 취소 버튼은 대화상자를 닫아요
        button_layout.addWidget(self.cancel_button)
        
        # 저장 버튼
        self.save_button = QPushButton("저장")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.accept)  # 저장 버튼은 대화상자를 수락하고 닫아요
        button_layout.addWidget(self.save_button)
        
        # 키보드 페이지 레이아웃에 위젯들 추가
        keyboard_layout.addWidget(self.table)
        keyboard_layout.addWidget(help_label)
        keyboard_layout.addLayout(button_layout)
        
        # 테마 설정 페이지 (미구현 - 나중에 추가될 기능)
        theme_page = QWidget()
        theme_layout = QVBoxLayout(theme_page)
        theme_layout.addWidget(QLabel("마우스 설정은 아직 개발 중입니다."))
        
        # 일반 설정 페이지 (미구현 - 나중에 추가될 기능)
        general_page = QWidget()
        general_layout = QVBoxLayout(general_page)
        general_layout.addWidget(QLabel("일반 설정은 아직 개발 중입니다."))
        
        # 스택 위젯에 페이지 추가
        self.stack.addWidget(keyboard_page)  # 인덱스 0: 키보드 설정
        self.stack.addWidget(theme_page)     # 인덱스 1: 테마 설정
        self.stack.addWidget(general_page)   # 인덱스 2: 일반 설정
        
        # 첫 번째 페이지(키보드 설정)를 기본으로 표시
        self.stack.setCurrentIndex(0)
        
        # 스택 위젯을 오른쪽 패널에 추가
        right_panel.addWidget(self.stack)
        
        # 메인 레이아웃에 패널 추가
        main_layout.addLayout(left_panel, 1)  # 왼쪽 패널 (비율 1)
        main_layout.addLayout(right_panel, 3)  # 오른쪽 패널 (비율 3)
        
        # 키 편집 중인지 표시하는 플래그
        self.editing = False
        self.current_row = -1

    def on_left_button_clicked(self):
        """
        왼쪽 버튼이 클릭되었을 때 호출되는 함수에요.
        버튼에 따라 다른 설정 페이지를 보여줘요.
        
        이 함수는 왼쪽 버튼 패널에 있는 버튼이 클릭되면 호출돼요.
        클릭된 버튼을 확인하고 그에 맞는 설정 페이지를 보여줘요.
        """
        # 모든 버튼의 체크 상태를 해제하고
        for button in self.left_buttons:
            button.setChecked(False)
        
        # 클릭된 버튼만 체크 상태로 변경해요
        sender = self.sender()  # 클릭된 버튼을 가져와요
        sender.setChecked(True)
        
        # 버튼에 따라 스택 위젯의 페이지를 변경해요
        if sender == self.keyboard_button:
            self.stack.setCurrentIndex(0)  # 키보드 설정 페이지
        elif sender == self.theme_button:
            self.stack.setCurrentIndex(1)  # 테마 설정 페이지
        elif sender == self.general_button:
            self.stack.setCurrentIndex(2)  # 일반 설정 페이지

    def cell_clicked(self, row, col):
        """
        테이블의 셀을 클릭했을 때 호출되는 함수에요.
        
        사용자가 테이블에서 단축키를 클릭하면, 그 단축키를 변경할 수 있도록
        KeyInputEdit 위젯을 보여주고 새 키 입력을 기다려요.
        
        매개변수:
            row: 클릭된 행 번호
            col: 클릭된 열 번호
        """
        # 이미 편집 중이면 현재 편집을 중단하고
        # 이전에 편집 중이던 셀의 상태를 원래대로 복원해요
        if self.editing and self.current_row != -1:
            key_name = self.table.item(self.current_row, 1).data(Qt.UserRole)
            value = self.key_settings[key_name]
            
            # 키 표시 텍스트 생성 - Return 키를 특별히 처리
            key_text = QKeySequence(value).toString()
            
            # Return 키를 Enter로 일관되게 표시
            if (value & ~Qt.ControlModifier) == Qt.Key_Return:
                # Ctrl+Return 조합인 경우
                if value & Qt.ControlModifier:
                    key_text = "Ctrl+Enter"
                else:
                    key_text = "Enter"
            
            self.table.item(self.current_row, 1).setText(key_text)
        
        # 키 입력 열(1번 열)을 클릭했을 때만 편집 모드 시작
        if col == 1:  # 1번 열은 단축키 열이에요
            self.editing = True
            self.current_row = row
            
            # 키 이름 가져오기
            key_name = self.table.item(row, 1).data(Qt.UserRole)
            
            # 현재 값 가져오기
            value = self.key_settings[key_name]
            
            # KeyInputEdit 초기화
            self.key_input.key_value = value
            
            # 키 표시 텍스트 생성 - Return 키를 특별히 처리
            key_text = QKeySequence(value).toString()
            
            # Return 키를 Enter로 일관되게 표시
            if (value & ~Qt.ControlModifier) == Qt.Key_Return:
                # Ctrl+Return 조합인 경우
                if value & Qt.ControlModifier:
                    key_text = "Ctrl+Enter"
                else:
                    key_text = "Enter"
            
            # 키 입력 위젯에 설정된 텍스트 표시
            self.key_input.setText(key_text)
            
            # 셀 위치 계산
            rect = self.table.visualItemRect(self.table.item(row, col))
            global_pos = self.table.viewport().mapToGlobal(rect.topLeft())
            
            # KeyInputEdit 위치 및 크기 설정
            self.key_input.setParent(self)
            self.key_input.setGeometry(
                self.mapFromGlobal(global_pos).x(),
                self.mapFromGlobal(global_pos).y(),
                rect.width(),
                rect.height()
            )
            
            # 이벤트 필터 설치
            self.key_input.installEventFilter(self)
            
            # 보이게 하고 포커스 주기
            self.key_input.show()
            self.key_input.setFocus()

    def eventFilter(self, obj, event):
        """
        이벤트 필터 함수에요. 키 입력 상자의 이벤트를 처리해요.
        
        키 입력 상자가 포커스를 잃으면 입력을 마치고
        새로운 단축키를 저장해요. Enter 키는 단축키로 등록 가능하도록 변경했어요.
        """
        # KeyInputEdit 객체에 대한 이벤트 처리
        if obj == self.key_input:
            # 포커스를 잃었을 때만 처리 (Enter 키는 단축키로 등록할 수 있게 변경)
            if event.type() == QEvent.FocusOut:
                
                if self.editing and self.current_row != -1:
                    # 변경된 키 값 적용
                    key_name = self.table.item(self.current_row, 1).data(Qt.UserRole)
                    
                    # KeyInputEdit에서 입력된 키 값을 가져와요
                    if self.key_input.key_value is not None:
                        # 키 설정에 새 값 저장
                        self.key_settings[key_name] = self.key_input.key_value
                        
                        # 테이블에 새 값 표시 - Enter/Return 키를 특별히 처리
                        key_text = QKeySequence(self.key_input.key_value).toString()
                        # Qt.Key_Return과 Qt.ControlModifier의 조합인 경우 "Ctrl+Enter"로 표시
                        if (self.key_input.key_value & ~Qt.ControlModifier) == Qt.Key_Return:
                            # Ctrl 키가 있는지 확인
                            if self.key_input.key_value & Qt.ControlModifier:
                                key_text = "Ctrl+Enter"
                            else:
                                key_text = "Enter"
                        
                        self.table.item(self.current_row, 1).setText(key_text)
                    
                    # KeyInputEdit 숨기기
                    self.key_input.hide()
                    self.editing = False
                    self.current_row = -1
                    
                    # 포커스를 테이블로 돌려요
                    self.table.setFocus()
                    
                # 처리 완료
                return True
            # 키 입력 상자가 보이는 상태에서 Escape 키를 누르면 취소
            elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
                # 키 입력 취소
                self.key_input.hide()
                self.editing = False
                self.current_row = -1
                
                # 포커스를 테이블로 돌려요
                self.table.setFocus()
                
                # 처리 완료
                return True
                
        # 기본 이벤트 처리
        return super().eventFilter(obj, event)

    def reset_to_default(self):
        """
        모든 단축키를 기본값으로 초기화하는 함수에요.
        
        '기본값으로 초기화' 버튼을 클릭하면 호출되며,
        모든 단축키 설정을 원래 기본값으로 되돌려요.
        """
        # 기본 키 설정 정의 - __init__에 있는 것과 동일해요
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
            "toggle_fullscreen": Qt.ControlModifier | Qt.Key_Return,
            "toggle_maximize_state": Qt.Key_Return
        }
        
        # 모든 키 설정을 기본값으로 업데이트
        self.key_settings = default_settings.copy()
        
        # 테이블 업데이트
        for row in range(self.table.rowCount()):
            key_name = self.table.item(row, 1).data(Qt.UserRole)
            if key_name in self.key_settings:
                value = self.key_settings[key_name]
                
                # 키 표시 텍스트 생성 - Return 키를 특별히 처리
                key_text = QKeySequence(value).toString()
                
                # Return 키를 Enter로 일관되게 표시
                if (value & ~Qt.ControlModifier) == Qt.Key_Return:
                    # Ctrl+Return 조합인 경우
                    if value & Qt.ControlModifier:
                        key_text = "Ctrl+Enter"
                    else:
                        key_text = "Enter"
                
                self.table.item(row, 1).setText(key_text)
        
        # 편집 중이었다면 중단
        if self.editing:
            self.key_input.hide()
            self.editing = False
            self.current_row = -1

    def get_key_settings(self):
        """
        현재 설정된 단축키 값들을 반환하는 함수에요.
        
        대화상자가 '저장' 버튼으로 수락되면 이 함수를 통해
        메인 프로그램에서 변경된 단축키 설정을 가져갈 수 있어요.
        
        반환값:
            dictionary: 키 이름과 값이 담긴 사전 형태의 설정
        """
        return self.key_settings.copy()  # copy를 사용하여 원본이 변경되지 않도록 보호해요
