"""
환경 설정 대화상자 모듈

이 모듈은 프로그램의 환경 설정을 변경할 수 있는 대화상자 클래스를 제공합니다.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QFrame, QStackedWidget, QWidget, QComboBox)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QIcon, QKeySequence

from events.handlers.keyboard_handler import KeyInputEdit
from events.handlers.mouse_input import MouseButtonWidget

class PreferencesDialog(QDialog):
    """
    환경 설정을 변경할 수 있는 대화상자
    
    이 클래스는 프로그램의 설정을 바꿀 수 있는 창을 만들어요.
    사용자가 자신이 원하는 대로 프로그램을 설정할 수 있어요.
    지금은 키보드 단축키 설정만 있지만, 나중에 다른 설정들도 추가할 수 있어요.
    """
    
    def __init__(self, parent=None, key_settings=None, mouse_settings=None):
        """
        환경 설정 대화상자를 초기화해요.
        
        매개변수:
            parent: 이 창의 부모 창
            key_settings: 현재 저장된 키보드 단축키 설정 (없으면 기본값 사용)
            mouse_settings: 현재 저장된 마우스 설정 (없으면 기본값 사용)
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
        default_key_settings = {
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
        
        # 기본 마우스 설정 정의
        default_mouse_settings = {
            "middle_click": "toggle_play",         # 중간 버튼: 재생/일시정지
            "right_click": "context_menu",         # 오른쪽 버튼: 컨텍스트 메뉴
            "double_click": "toggle_fullscreen",   # 더블 클릭: 전체화면
            "wheel_up": "prev_image",              # 휠 위로: 이전 이미지
            "wheel_down": "next_image",            # 휠 아래로: 다음 이미지
            "ctrl_wheel_up": "volume_up",          # Ctrl + 휠 위로: 볼륨 증가
            "ctrl_wheel_down": "volume_down",      # Ctrl + 휠 아래로: 볼륨 감소
            "shift_wheel_up": "rotate_counterclockwise",  # Shift + 휠 위로: 반시계방향 회전
            "shift_wheel_down": "rotate_clockwise",  # Shift + 휠 아래로: 시계방향 회전
            "wheel_cooldown_ms": 500               # 휠 이벤트 쿨다운 (밀리초)
        }
        
        # 전달받은 키 설정이 있으면 사용, 없으면 기본값 사용
        # copy()를 사용하는 이유는 원래 설정을 변경하지 않기 위해서예요
        self.key_settings = key_settings.copy() if key_settings else default_key_settings.copy()
        
        # 전달받은 마우스 설정이 있으면 사용, 없으면 기본값 사용
        self.mouse_settings = mouse_settings.copy() if mouse_settings else default_mouse_settings.copy()

        # 누락된 키가 있으면 기본값에서 추가
        # 프로그램을 업데이트하면서 새로운 단축키가 추가될 수 있어요
        for key, value in default_key_settings.items():
            if key not in self.key_settings:
                self.key_settings[key] = value
                
        # 누락된 마우스 설정이 있으면 기본값에서 추가
        for key, value in default_mouse_settings.items():
            if key not in self.mouse_settings:
                self.mouse_settings[key] = value
        
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
        
        # 마우스 버튼 이름 매핑
        self.mouse_button_names = {
            "middle_click": "중간 버튼 클릭",
            "right_click": "오른쪽 버튼 클릭",
            "double_click": "더블 클릭",
            "wheel_up": "휠 위로",
            "wheel_down": "휠 아래로",
            "ctrl_wheel_up": "Ctrl + 휠 위로",
            "ctrl_wheel_down": "Ctrl + 휠 아래로",
            "shift_wheel_up": "Shift + 휠 위로",
            "shift_wheel_down": "Shift + 휠 아래로"
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
        
        # 테이블 높이 강제 적용 (여러 방법 시도)
        self.table.setMinimumHeight(400)  # 최소 높이 설정
        self.table.setFixedHeight(400)    # 고정 높이 설정
        
        # 스크롤 정책 설정
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
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
        
        # 설명 라벨 추가 - 여백 추가
        help_label = QLabel("단축키를 변경하려면 해당 행을 클릭하세요. 그런 다음 원하는 키를 누르면 됩니다.")
        help_label.setStyleSheet("color: #555; margin-top: 15px;")
        
        # 버튼 생성 - 여백 추가
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 15, 0, 0)  # 위쪽 여백 15픽셀 추가
        
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
        
        # 테마 설정 페이지 (마우스 설정으로 변경)
        theme_page = QWidget()
        theme_layout = QVBoxLayout(theme_page)
        
        # 마우스 설정 테이블 생성
        self.mouse_table = QTableWidget()
        self.mouse_table.setColumnCount(2)  # 2개 열: 기능, 단축키
        self.mouse_table.setHorizontalHeaderLabels(["기능", "단축키"])  # 열 제목 설정
        
        # 테이블 설정
        self.mouse_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # 첫 번째 열 늘려서 채움
        self.mouse_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 두 번째 열 늘려서 채움
        self.mouse_table.setSelectionBehavior(QTableWidget.SelectRows)  # 행 단위로 선택
        self.mouse_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 직접 편집 불가능
        self.mouse_table.verticalHeader().setVisible(False)  # 세로 헤더(행 번호) 숨김
        self.mouse_table.setAlternatingRowColors(True)  # 행마다 배경색 번갈아 설정
        self.mouse_table.setMinimumHeight(400)  # 테이블 최소 높이 설정 (300에서 400으로 늘림)
        
        # 헤더 볼드체 제거
        header_style = "QHeaderView::section { font-weight: normal; }"
        self.mouse_table.horizontalHeader().setStyleSheet(header_style)
        
        # 마우스 버튼과 액션 매핑 설정
        mouse_action_names = {
            "prev_image": "이전 이미지",
            "next_image": "다음 이미지",
            "rotate_clockwise": "시계 방향 회전",
            "rotate_counterclockwise": "반시계 방향 회전",
            "toggle_play": "재생/일시정지",
            "volume_up": "볼륨 증가",
            "volume_down": "볼륨 감소",
            "toggle_mute": "음소거 토글",
            "toggle_fullscreen": "전체화면 전환",
            "toggle_maximize_state": "최대화 전환",
            "context_menu": "컨텍스트 메뉴",
            "delete_image": "이미지 삭제"
        }
        
        # 테이블 채우기
        self.mouse_widgets = {}
        rows_to_add = len(self.mouse_button_names)
        self.mouse_table.setRowCount(rows_to_add)
        
        row = 0
        for button_name, button_display_name in self.mouse_button_names.items():
            # 현재 설정된 액션 가져오기
            current_action = self.mouse_settings.get(button_name)
            
            # 기능 이름 칸
            name_item = QTableWidgetItem(button_display_name)
            self.mouse_table.setItem(row, 0, name_item)
            
            # 액션 칸
            action_display_name = ""
            for code, name in mouse_action_names.items():
                if code == current_action:
                    action_display_name = name
                    break
            
            action_item = QTableWidgetItem(action_display_name)
            action_item.setData(Qt.UserRole, button_name)  # 버튼 이름 저장
            self.mouse_table.setItem(row, 1, action_item)
            
            row += 1
        
        # 테이블 클릭 시 호출될 함수 연결
        self.mouse_table.cellClicked.connect(self.mouse_cell_clicked)
        
        # 레이아웃에 테이블 추가
        theme_layout.addWidget(self.mouse_table)
        
        # 설명 라벨 추가
        help_label = QLabel("단축키를 변경하려면 해당 셀을 클릭하세요. 그런 다음 원하는 키를 누르면 됩니다.")
        help_label.setStyleSheet("color: #555; margin-top: 15px;")
        theme_layout.addWidget(help_label)
        
        # 휠 쿨다운 설정 추가
        cooldown_layout = QHBoxLayout()
        cooldown_layout.setContentsMargins(0, 15, 0, 0)  # 위쪽 여백 15픽셀 추가
        
        cooldown_label = QLabel("휠 이벤트 쿨다운 (밀리초):")
        cooldown_label.setStyleSheet("min-width: 120px; padding: 5px;")
        
        from PyQt5.QtWidgets import QSpinBox
        self.cooldown_spinner = QSpinBox()
        self.cooldown_spinner.setMinimum(0)
        self.cooldown_spinner.setMaximum(2000)
        self.cooldown_spinner.setSingleStep(50)
        self.cooldown_spinner.setValue(self.mouse_settings.get("wheel_cooldown_ms", 500))
        self.cooldown_spinner.valueChanged.connect(self.on_cooldown_changed)
        
        cooldown_layout.addWidget(cooldown_label)
        cooldown_layout.addWidget(self.cooldown_spinner)
        cooldown_layout.addStretch()
        
        theme_layout.addLayout(cooldown_layout)
        
        # 버튼 레이아웃 추가
        mouse_button_layout = QHBoxLayout()
        mouse_button_layout.setContentsMargins(0, 15, 0, 0)  # 위쪽 여백 15픽셀 추가
        
        # 기본값으로 초기화 버튼
        self.mouse_reset_button = QPushButton("기본값으로 초기화")
        self.mouse_reset_button.setObjectName("resetButton")
        self.mouse_reset_button.clicked.connect(self.reset_mouse_to_default)
        mouse_button_layout.addWidget(self.mouse_reset_button)
        
        # 중간 여백 추가
        mouse_button_layout.addStretch()
        
        # 취소 버튼
        self.mouse_cancel_button = QPushButton("취소")
        self.mouse_cancel_button.setObjectName("cancelButton")
        self.mouse_cancel_button.clicked.connect(self.reject)
        mouse_button_layout.addWidget(self.mouse_cancel_button)
        
        # 저장 버튼
        self.mouse_save_button = QPushButton("저장")
        self.mouse_save_button.setObjectName("saveButton")
        self.mouse_save_button.clicked.connect(self.accept)
        mouse_button_layout.addWidget(self.mouse_save_button)
        
        theme_layout.addLayout(mouse_button_layout)
        theme_layout.addStretch()
        
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
        # 열려있는 콤보박스 정리
        for child in self.findChildren(QComboBox):
            if isinstance(child, QComboBox) and child.isVisible():
                child.hide()
        
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

    def on_mouse_action_changed(self, button_name, new_action):
        """
        마우스 액션이 변경되었을 때 호출되는 함수
        
        Args:
            button_name: 버튼 이름 (예: "middle_click")
            new_action: 새 액션 (예: "toggle_play")
        """
        # 설정 업데이트
        self.mouse_settings[button_name] = new_action
        print(f"마우스 설정 변경: {button_name} -> {new_action}")
    
    def on_cooldown_changed(self, value):
        """
        휠 쿨다운 값이 변경되었을 때 호출되는 함수
        
        Args:
            value: 새 쿨다운 값 (밀리초)
        """
        # 설정 업데이트
        self.mouse_settings["wheel_cooldown_ms"] = value
        print(f"휠 쿨다운 설정 변경: {value} ms")
    
    def reset_mouse_to_default(self):
        """
        마우스 설정을 기본값으로 초기화
        """
        # 기본 마우스 설정
        default_mouse_settings = {
            "middle_click": "toggle_play",         # 중간 버튼: 재생/일시정지
            "right_click": "context_menu",         # 오른쪽 버튼: 컨텍스트 메뉴
            "double_click": "toggle_fullscreen",   # 더블 클릭: 전체화면
            "wheel_up": "prev_image",              # 휠 위로: 이전 이미지
            "wheel_down": "next_image",            # 휠 아래로: 다음 이미지
            "ctrl_wheel_up": "volume_up",          # Ctrl + 휠 위로: 볼륨 증가
            "ctrl_wheel_down": "volume_down",      # Ctrl + 휠 아래로: 볼륨 감소
            "shift_wheel_up": "rotate_counterclockwise",  # Shift + 휠 위로: 반시계방향 회전
            "shift_wheel_down": "rotate_clockwise",  # Shift + 휠 아래로: 시계방향 회전
            "wheel_cooldown_ms": 500               # 휠 이벤트 쿨다운 (밀리초)
        }
        
        # 설정 업데이트
        self.mouse_settings = default_mouse_settings.copy()
        
        # UI 업데이트 - 테이블 형식에 맞게 변경
        # 마우스 버튼과 액션 매핑 설정
        mouse_action_names = {
            "prev_image": "이전 이미지",
            "next_image": "다음 이미지",
            "rotate_clockwise": "시계 방향 회전",
            "rotate_counterclockwise": "반시계 방향 회전",
            "toggle_play": "재생/일시정지",
            "volume_up": "볼륨 증가",
            "volume_down": "볼륨 감소",
            "toggle_mute": "음소거 토글",
            "toggle_fullscreen": "전체화면 전환",
            "toggle_maximize_state": "최대화 전환",
            "context_menu": "컨텍스트 메뉴",
            "delete_image": "이미지 삭제"
        }
        
        # 테이블 업데이트
        for row in range(self.mouse_table.rowCount()):
            item = self.mouse_table.item(row, 1)
            if item:
                button_name = item.data(Qt.UserRole)
                if button_name in self.mouse_settings:
                    action_code = self.mouse_settings[button_name]
                    action_name = ""
                    for code, name in mouse_action_names.items():
                        if code == action_code:
                            action_name = name
                            break
                    item.setText(action_name)
        
        # 쿨다운 값 업데이트
        self.cooldown_spinner.setValue(self.mouse_settings["wheel_cooldown_ms"])

    def get_mouse_settings(self):
        """
        현재 설정된 마우스 설정 값들을 반환하는 함수
        
        Returns:
            dictionary: 마우스 설정 값이 담긴 사전
        """
        return self.mouse_settings.copy() 

    def mouse_cell_clicked(self, row, col):
        """
        마우스 설정 테이블의 셀을 클릭했을 때 호출되는 함수
        
        마우스 버튼 액션을 변경할 수 있도록 콤보박스 메뉴를 표시합니다.
        
        매개변수:
            row: 클릭된 행 번호
            col: 클릭된 열 번호
        """
        # 액션 열(1번 열)을 클릭했을 때만 메뉴 표시
        if col == 1:
            # 현재 버튼 이름 가져오기
            button_name = self.mouse_table.item(row, 1).data(Qt.UserRole)
            
            # 콤보박스 메뉴 생성
            from events.handlers.mouse_input import MouseActionCombo
            combo = MouseActionCombo(self)
            
            # 현재 액션 설정
            current_action = self.mouse_settings.get(button_name)
            combo.set_current_action(current_action)
            
            # 위치 계산
            rect = self.mouse_table.visualItemRect(self.mouse_table.item(row, col))
            global_pos = self.mouse_table.viewport().mapToGlobal(rect.topLeft())
            
            # 위치 및 크기 설정
            combo.setParent(self)
            combo.setGeometry(
                self.mapFromGlobal(global_pos).x(),
                self.mapFromGlobal(global_pos).y(),
                rect.width(),
                rect.height()
            )
            
            # 콤보박스 표시
            combo.show()
            combo.showPopup()  # 드롭다운 메뉴 바로 표시
            
            # 아이템 선택 시 처리
            combo.currentIndexChanged.connect(lambda idx: self.on_mouse_action_selected(button_name, combo))
    
    def on_mouse_action_selected(self, button_name, combo):
        """
        마우스 액션 콤보박스에서 항목이 선택되었을 때 호출되는 함수
        
        Args:
            button_name: 버튼 이름 (예: "middle_click")
            combo: 선택이 발생한 콤보박스
        """
        # 선택된 액션 가져오기
        new_action = combo.get_current_action()
        
        # 설정 업데이트
        self.mouse_settings[button_name] = new_action
        
        # 테이블 업데이트
        for row in range(self.mouse_table.rowCount()):
            item = self.mouse_table.item(row, 1)
            if item and item.data(Qt.UserRole) == button_name:
                # 선택된 액션의 표시 이름 찾기
                display_text = combo.currentText()
                item.setText(display_text)
                break
        
        # 콤보박스 닫기
        combo.close() 