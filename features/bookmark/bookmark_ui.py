from PyQt5.QtWidgets import QMenu, QAction, QPushButton
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QIcon
import os

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
            
        if (hasattr(self.viewer, 'current_image_path') and 
            self.viewer.current_image_path and 
            self.viewer.current_image_path in self.bookmark_manager.bookmarks):
            # 북마크된 상태
            self.bookmark_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(241, 196, 15, 0.9);  /* 노란색 배경 */
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(241, 196, 15, 1.0);  /* 호버 시 더 진한 노란색 */
                }
            """)
        else:
            # 북마크되지 않은 상태
            self.bookmark_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(52, 73, 94, 0.6);
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: rgba(52, 73, 94, 1.0);
                }
            """)

    def create_bookmark_menu(self):
        """북마크 메뉴 생성"""
        self.bookmark_menu = QMenu(self.viewer)
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
        """)
        
        # 북마크 추가/제거 액션
        toggle_action = QAction("북마크 추가/제거", self.viewer)
        toggle_action.triggered.connect(self.bookmark_manager.toggle_bookmark)
        self.bookmark_menu.addAction(toggle_action)
        
        # 구분선 추가
        self.bookmark_menu.addSeparator()
        
        # 북마크된 항목들 추가
        for path in self.bookmark_manager.bookmarks:
            action = QAction(os.path.basename(path), self.viewer)
            action.setData(path)
            action.triggered.connect(lambda checked, p=path: self.bookmark_manager.load_bookmarked_image(p))
            self.bookmark_menu.addAction(action)
        
        # 북마크가 없는 경우 메시지 표시
        if not self.bookmark_manager.bookmarks:
            empty_action = QAction("북마크가 없습니다", self.viewer)
            empty_action.setEnabled(False)
            self.bookmark_menu.addAction(empty_action)
        else:
            # 구분선 추가
            self.bookmark_menu.addSeparator()
            # 모든 북마크 삭제 액션
            clear_action = QAction("모든 북마크 삭제", self.viewer)
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
        menu_x = pos.x()
        menu_y = pos.y() - menu.sizeHint().height()
        
        # 메뉴가 화면 위로 넘어가지 않도록 조정
        if menu_y < 0:
            menu_y = pos.y() + self.bookmark_button.height()
        
        # 메뉴 표시
        menu.popup(QPoint(menu_x, menu_y)) 