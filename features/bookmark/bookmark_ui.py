from PyQt5.QtWidgets import QMenu, QAction, QPushButton, QWidgetAction, QLabel
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QIcon
import os

class BookmarkAction(QAction):
    """북마크 메뉴 아이템 클래스 - 우클릭 메뉴 지원"""
    def __init__(self, text, parent, path, bookmark_manager):
        super().__init__(text, parent)
        self.path = path
        self.bookmark_manager = bookmark_manager
        self.setToolTip(path)
        self.setStatusTip(path)
        self.setData(path)

class BookmarkMenu(QMenu):
    """북마크 메뉴 커스텀 클래스 - 툴팁 표시 지원"""
    def __init__(self, parent=None, bookmark_manager=None):
        super().__init__(parent)
        self.bookmark_manager = bookmark_manager
        # 툴팁 활성화
        self.setToolTipsVisible(True)
        # 우클릭 이벤트 처리를 위한 설정
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
    def mouseReleaseEvent(self, event):
        """마우스 버튼 해제 이벤트 처리"""
        action = self.actionAt(event.pos())
        
        # 유효한 북마크 액션인지 확인
        if action and hasattr(action, 'path'):
            # 오른쪽 버튼 클릭 (우클릭) - 컨텍스트 메뉴 표시
            if event.button() == Qt.RightButton:
                self._show_context_menu(action, event.globalPos())
                event.accept()
                return
                
            # 왼쪽 버튼 클릭 (좌클릭) - 북마크 이미지 로드
            elif event.button() == Qt.LeftButton:
                # 메뉴 숨기기
                self.hide()
                # 북마크된 이미지 로드
                if self.bookmark_manager:
                    self.bookmark_manager.load_bookmarked_image(action.path)
                event.accept()
                return
                
        # 다른 모든 경우에는 기본 처리
        super().mouseReleaseEvent(event)
    
    def contextMenuEvent(self, event):
        """컨텍스트 메뉴 이벤트 처리 - 우클릭 메뉴 표시용"""
        # 이미 mouseReleaseEvent에서 처리했으므로 이 메서드는 무시
        event.accept()
    
    def _show_context_menu(self, action, global_pos):
        """북마크에 대한 컨텍스트 메뉴 표시"""
        context_menu = QMenu(self)
        context_menu.setStyleSheet(self.styleSheet())
        
        # 북마크 열기 옵션
        open_action = QAction(f"Open Bookmark", self)
        open_action.triggered.connect(lambda: self._open_bookmark(action.path))
        context_menu.addAction(open_action)
        
        # 구분선 추가
        context_menu.addSeparator()
        
        # 북마크 삭제 액션
        remove_action = QAction(f"Remove Bookmark", self)
        remove_action.triggered.connect(lambda: self._remove_bookmark(action.path))
        context_menu.addAction(remove_action)
        
        # 컨텍스트 메뉴 표시
        context_menu.exec_(global_pos)
    
    def _open_bookmark(self, path):
        """북마크 이미지 열기"""
        if self.bookmark_manager:
            # 메뉴 숨기기
            self.hide()
            # 북마크된 이미지 로드
            self.bookmark_manager.load_bookmarked_image(path)
    
    def _remove_bookmark(self, path):
        """특정 북마크 삭제"""
        if self.bookmark_manager:
            # 해당 북마크만 제거
            if path in self.bookmark_manager.bookmarks:
                # 1. 북마크 리스트에서 삭제
                self.bookmark_manager.bookmarks.remove(path)
                self.bookmark_manager.save_bookmarks()
                
                # 2. 메시지 표시
                if hasattr(self.bookmark_manager.viewer, 'show_message'):
                    self.bookmark_manager.viewer.show_message(f"Bookmark removed: {os.path.basename(path)}")
                    
                # 3. 현재 이미지가 삭제된 북마크인 경우 북마크 버튼 상태 업데이트
                self.bookmark_manager.update_bookmark_button_state()
                
                # 4. 메뉴에서 해당 항목만 제거 (메뉴를 닫지 않음)
                try:
                    # 삭제 전 메뉴 위치와 크기 기억
                    current_pos = self.pos()
                    old_height = self.height()
                    
                    # 메뉴에서 path 속성이 일치하는 모든 액션 찾기
                    actions_to_remove = []
                    for action in self.actions():
                        if hasattr(action, 'path') and action.path == path:
                            actions_to_remove.append(action)
                    
                    # 찾은 액션들 제거
                    for action in actions_to_remove:
                        self.removeAction(action)
                    
                    # 메뉴가 비어있는지 확인
                    bookmark_items = [action for action in self.actions() 
                                     if hasattr(action, 'path') and action.path in self.bookmark_manager.bookmarks]
                    
                    if not bookmark_items:
                        # 북마크가 모두 삭제되었다면 "No Bookmarks" 메시지 추가
                        empty_action = QAction("No Bookmarks", self)
                        empty_action.setEnabled(False)
                        
                        # 토글 액션과 구분선 다음에 추가
                        insert_pos = 2  # 토글 액션(0)과 구분선(1) 이후 위치
                        if len(self.actions()) > insert_pos:
                            self.insertAction(self.actions()[insert_pos], empty_action)
                        else:
                            self.addAction(empty_action)
                            
                        # "Clear All Bookmarks" 액션이 있다면 제거
                        clear_actions = [action for action in self.actions() 
                                       if action.text() == "Clear All Bookmarks"]
                        for action in clear_actions:
                            self.removeAction(action)
                    
                    # 메뉴 내용이 변경된 후 지연시켜 크기와 위치 조정
                    QTimer.singleShot(10, lambda: self._adjust_menu_position(current_pos, old_height))
                    
                except Exception as e:
                    # 메뉴 업데이트 중 오류 발생 시 로그 출력
                    print(f"Error updating bookmark menu: {e}")
                    
                    # 대체 방법: 메뉴 전체 재생성 (기존 방식)
                    self.hide()
                    if hasattr(self.bookmark_manager, 'ui') and hasattr(self.bookmark_manager.ui, 'show_menu_above_button'):
                        QTimer.singleShot(100, self.bookmark_manager.ui.show_menu_above_button)
    
    def _adjust_menu_position(self, old_pos, old_height):
        """메뉴 위치 재조정 - 항목 삭제 후 메뉴 위치 조정"""
        try:
            # 새 높이 계산
            new_height = self.sizeHint().height()
            
            # 위치 조정 (하단은 동일하게 유지하고 상단을 조정)
            height_diff = old_height - new_height
            new_pos = QPoint(old_pos.x(), old_pos.y() + height_diff)
            
            # 새 위치로 이동
            self.move(new_pos)
            
            # 메뉴 크기 업데이트
            self.adjustSize()
            self.update()
        except Exception as e:
            print(f"Error adjusting menu position: {e}")

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
        self.bookmark_menu = BookmarkMenu(self.viewer, self.bookmark_manager)
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
        
        # 현재 이미지가 북마크된 경우 '북마크 제거' 액션 추가
        if hasattr(self.viewer, 'current_image_path') and self.viewer.current_image_path and \
           self.viewer.current_image_path in self.bookmark_manager.bookmarks:
            remove_action = QAction("Remove Bookmark", self.viewer)
            remove_action.triggered.connect(self.bookmark_manager.remove_bookmark)
            self.bookmark_menu.addAction(remove_action)
        
        # 구분선 추가
        self.bookmark_menu.addSeparator()
        
        # 북마크된 항목들 추가 (원래 순서대로 추가하면 최신 북마크가 아래에 표시됨)
        # bookmarks 리스트는 북마크 추가 순서대로 저장되어 있음 (최신 항목이 마지막)
        for path in self.bookmark_manager.bookmarks:
            # 북마크 액션 생성 (파일 이름만 표시)
            action = BookmarkAction(os.path.basename(path), self.viewer, path, self.bookmark_manager)
            
            # 좌클릭에만 로드 이벤트 연결 (기존 triggered 대신 더 구체적인 시그널 사용)
            # Qt 5.10 이상에서는 triggered(bool) 대신 triggered(QAction::Trigger) 사용 가능
            # 하지만 Qt 5.10 미만 호환성을 위해 mousePressEvent에서 클릭 구분
            
            # 더 이상 전체 클릭을 로드 이벤트에 연결하지 않음
            # 대신 좌클릭만 로드하도록 BookmarkMenu 클래스에서 처리
            action.setProperty("bookmark_path", path)  # 속성으로 path 저장
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