from PyQt5.QtWidgets import QMenu, QAction, QPushButton
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon
import os

class BookmarkMenu(QMenu):
    """북마크 메뉴 커스텀 클래스 - 툴팁 표시 지원"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 툴팁 활성화
        self.setToolTipsVisible(True)

class BookmarkUI:
    def __init__(self, bookmark_manager):
        self.bookmark_manager = bookmark_manager
        self.viewer = bookmark_manager.viewer
        self.bookmark_menu = None
        self.bookmark_button = None
        
    def set_bookmark_button(self, button):
        """북마크 버튼 설정"""
        self.bookmark_button = button
        self.update_bookmark_button_state()
        
    def update_bookmark_button_state(self):
        """북마크 버튼의 상태(스타일)를 업데이트"""
        if not self.bookmark_button:
            return
            
        is_bookmarked = (hasattr(self.viewer, 'current_image_path') and 
                         self.viewer.current_image_path and 
                         self.viewer.current_image_path in self.bookmark_manager.bookmarks)
            
        # If the bookmark button has the set_bookmark_state method, use it
        if hasattr(self.bookmark_button, 'set_bookmark_state'):
            self.bookmark_button.set_bookmark_state(is_bookmarked)
        else:
            # Legacy method (for legacy code support, remove if not needed)
            pass

    def create_bookmark_menu(self):
        """북마크 메뉴 생성"""
        # 일반 QMenu 대신 툴팁을 표시하는 커스텀 BookmarkMenu 사용
        self.bookmark_menu = BookmarkMenu(self.viewer)
        self.bookmark_menu.setStyleSheet("""
            QMenu {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                border: 1px solid transparent;
            }
            QMenu::item:selected {
                background-color: #34495e;
            }
            QMenu::separator {
                height: 1px;
                background: #34495e;
                margin: 5px 0;
            }
            QToolTip {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
                padding: 2px;
            }
        """)
        
        # 북마크 추가/제거 액션
        toggle_action = QAction("Toggle Bookmark", self.viewer)  # "Toggle Bookmark" replaces "북마크 추가/제거"
        toggle_action.triggered.connect(self.bookmark_manager.toggle_bookmark)
        self.bookmark_menu.addAction(toggle_action)
        
        # 구분선 추가
        self.bookmark_menu.addSeparator()
        
        # 북마크된 항목들 추가 (원래 순서대로 추가하면 최신 북마크가 아래에 표시됨)
        # bookmarks 리스트는 북마크 추가 순서대로 저장되어 있음 (최신 항목이 마지막)
        for path in self.bookmark_manager.bookmarks:
            # 파일 이름만 표시
            action = QAction(os.path.basename(path), self.viewer)
            action.setData(path)
            # 파일 전체 경로를 툴팁으로 설정
            action.setToolTip(path)
            action.setStatusTip(path)  # 상태바에도 표시 (지원되는 경우)
            action.triggered.connect(lambda checked, p=path: self.bookmark_manager.load_bookmarked_image(p))
            self.bookmark_menu.addAction(action)
        
        # 북마크가 없는 경우 메시지 표시
        if not self.bookmark_manager.bookmarks:
            empty_action = QAction("No Bookmarks", self.viewer)  # "No Bookmarks" replaces "북마크가 없습니다"
            empty_action.setEnabled(False)
            self.bookmark_menu.addAction(empty_action)
        else:
            # 구분선 추가
            self.bookmark_menu.addSeparator()
            # 모든 북마크 삭제 액션
            clear_action = QAction("Clear All Bookmarks", self.viewer)  # "Clear All Bookmarks" replaces "모든 북마크 삭제"
            clear_action.triggered.connect(self.bookmark_manager.clear_bookmarks)
            self.bookmark_menu.addAction(clear_action)
        
        return self.bookmark_menu

    def show_menu_above_button(self):
        """북마크 메뉴를 버튼 위에 표시"""
        if not self.bookmark_button:
            return
            
        # 새로운 메뉴 생성
        menu = self.create_bookmark_menu()
        
        # 버튼 위치 계산
        pos = self.bookmark_button.mapToGlobal(QPoint(0, 0))
        button_width = self.bookmark_button.width()
        menu_width = menu.sizeHint().width()
        
        # 메뉴 위치 계산 (오른쪽 모서리 기준)
        menu_x = pos.x() + button_width - menu_width  # 버튼의 오른쪽 모서리에 메뉴의 오른쪽 모서리 맞춤
        menu_y = pos.y() - menu.sizeHint().height()  # 버튼 위에 메뉴 표시
        
        # 메뉴가 화면 왼쪽으로 넘어가지 않도록 조정
        if menu_x < 0:
            menu_x = 0
        
        # 메뉴가 화면 위로 넘어가지 않도록 조정
        if menu_y < 0:
            menu_y = pos.y() + self.bookmark_button.height()  # 버튼 아래에 표시
        
        # 메뉴 표시
        menu.popup(QPoint(menu_x, menu_y)) 