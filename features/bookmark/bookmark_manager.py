"""
북마크 관리 모듈

이 모듈은 북마크(즐겨찾기)를 관리하는 기능을 담당해요.
사용자가 자주 보는 이미지나 비디오를 북마크에 추가하고 나중에 쉽게 다시 볼 수 있게 해줘요.
"""

import os
import json
from PyQt5.QtWidgets import QAction, QApplication, QPushButton, QSizePolicy, QMenu, QWidget, QLabel
from PyQt5.QtCore import QPoint, Qt

from core.utils.path_utils import get_user_data_directory
from ui.components.scrollable_menu import ScrollableMenu

class BookmarkManager:
    """
    북마크 관리 클래스
    
    이 클래스는 북마크를 추가, 제거, 저장, 불러오기하는 기능을 담당해요.
    또한 북마크 메뉴와 북마크 버튼 상태도 관리해요.
    """
    
    def __init__(self, parent_widget):
        """
        북마크 관리자를 초기화해요.
        
        매개변수:
            parent_widget: 부모 위젯 (보통 ImageViewer 클래스)
        """
        self.parent = parent_widget  # 부모 위젯 저장 (메인 화면)
        self.bookmarks = []  # 북마크 목록 (파일 경로 저장)
        self.bookmark_menu = None  # 북마크 메뉴 객체
        self.bookmark_button = None  # 북마크 버튼 (★ 모양 버튼)
        
        # 북마크 불러오기
        self.load_bookmarks()
    
    def set_bookmark_button(self, button):
        """
        북마크 버튼을 설정해요.
        
        매개변수:
            button: 북마크 버튼 (★ 모양 버튼)
        """
        self.bookmark_button = button
        self.update_bookmark_button_state()
    
    def toggle_bookmark(self):
        """
        현재 이미지의 북마크 상태를 전환해요 (있으면 제거, 없으면 추가).
        """
        # 현재 이미지 경로가 없으면 종료
        if not hasattr(self.parent, 'current_image_path') or not self.parent.current_image_path:
            return
            
        # 현재 이미지가 북마크에 있으면 제거, 없으면 추가
        if self.parent.current_image_path in self.bookmarks:
            # 북마크에서 제거
            self.bookmarks.remove(self.parent.current_image_path)
            self.parent.show_message("북마크에서 제거되었습니다.")
        else:
            # 북마크에 추가
            self.bookmarks.append(self.parent.current_image_path)
            self.parent.show_message("북마크에 추가되었습니다.")
            
        # 북마크 버튼 상태 업데이트
        self.update_bookmark_button_state()
        
        # 북마크 메뉴 업데이트
        self.update_bookmark_menu()
        
        # 북마크 저장
        self.save_bookmarks()
    
    def add_bookmark(self):
        """
        현재 이미지를 북마크에 추가해요.
        """
        # 현재 이미지 경로가 없으면 종료
        if not hasattr(self.parent, 'current_image_path') or not self.parent.current_image_path:
            return
            
        # 이미 북마크에 있으면 메시지만 표시하고 종료
        if self.parent.current_image_path in self.bookmarks:
            self.parent.show_message("이미 북마크에 추가되어 있습니다.")
            return
            
        # 북마크에 추가
        self.bookmarks.append(self.parent.current_image_path)
        self.parent.show_message("북마크에 추가되었습니다.")
        
        # 북마크 버튼 상태와 메뉴 업데이트
        self.update_bookmark_button_state()
        self.update_bookmark_menu()
        
        # 북마크 저장
        self.save_bookmarks()
    
    def remove_bookmark(self):
        """
        현재 이미지를 북마크에서 제거해요.
        """
        # 현재 이미지 경로가 없으면 종료
        if not hasattr(self.parent, 'current_image_path') or not self.parent.current_image_path:
            return
            
        # 북마크에 없으면 메시지만 표시하고 종료
        if self.parent.current_image_path not in self.bookmarks:
            self.parent.show_message("북마크에 없는 이미지입니다.")
            return
            
        # 북마크에서 제거
        self.bookmarks.remove(self.parent.current_image_path)
        self.parent.show_message("북마크에서 제거되었습니다.")
        
        # 북마크 버튼 상태와 메뉴 업데이트
        self.update_bookmark_button_state()
        self.update_bookmark_menu()
        
        # 북마크 저장
        self.save_bookmarks()
    
    def save_bookmarks(self):
        """
        북마크 정보를 JSON 파일로 저장해요.
        """
        try:
            # 앱 데이터 폴더 확인 및 생성
            app_data_dir = get_user_data_directory()
            if not os.path.exists(app_data_dir):
                os.makedirs(app_data_dir)
                
            # 북마크 파일 저장 경로
            bookmarks_file = os.path.join(app_data_dir, "bookmarks.json")
            
            # 현재 북마크 목록을 JSON으로 저장
            with open(bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=4)
                
            # 디버깅용 메시지
            print(f"북마크가 저장되었습니다: {bookmarks_file}")
        except Exception as e:
            print(f"북마크 저장 중 오류 발생: {e}")
    
    def load_bookmarks(self):
        """
        JSON 파일에서 북마크 정보를 불러와요.
        """
        try:
            # 앱 데이터 폴더 경로
            app_data_dir = get_user_data_directory()
            bookmarks_file = os.path.join(app_data_dir, "bookmarks.json")
            
            # 파일이 존재하면 불러오기
            if os.path.exists(bookmarks_file):
                with open(bookmarks_file, 'r', encoding='utf-8') as f:
                    loaded_bookmarks = json.load(f)
                    
                # 북마크 중 존재하는 파일만 리스트에 추가
                valid_bookmarks = []
                for bookmark in loaded_bookmarks:
                    if os.path.exists(bookmark):
                        valid_bookmarks.append(bookmark)
                
                # 유효한 북마크만 설정
                self.bookmarks = valid_bookmarks
                
                # 디버깅용 메시지
                print(f"북마크 {len(self.bookmarks)}개가 로드되었습니다")
        except Exception as e:
            print(f"북마크 불러오기 중 오류 발생: {e}")
            # 오류 발생 시 빈 리스트로 초기화
            self.bookmarks = []
    
    def update_bookmark_button_state(self):
        """
        북마크 버튼의 상태를 업데이트해요.
        현재 이미지가 북마크에 있으면 노란색 배경, 없으면 기본 배경으로 표시해요.
        """
        # 북마크 버튼이 설정되지 않았으면 종료
        if not self.bookmark_button:
            return
            
        # 현재 이미지가 북마크에 있는지 확인
        if (hasattr(self.parent, 'current_image_path') and 
            self.parent.current_image_path and 
            self.parent.current_image_path in self.bookmarks):
            # 북마크에 있으면 노란색 배경의 버튼으로 표시
            self.bookmark_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(241, 196, 15, 0.9);  /* 노란색 배경 */
                    color: white;
                    font-weight: bold;
                    border: none;
                    border-radius: 3px;
                    padding: 8px;
                    font-size: 16px;
                }
                
                QPushButton:hover {
                    background-color: rgba(241, 196, 15, 1.0);  /* 호버 시 더 진한 노란색 */
                }
            """)
        else:
            # 북마크에 없으면 기본 배경의 버튼으로 표시
            self.bookmark_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(52, 73, 94, 0.6);
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 8px;
                    font-size: 16px;
                }
                
                QPushButton:hover {
                    background-color: rgba(52, 73, 94, 1.0);
                }
            """)
    
    def update_bookmark_menu(self):
        """
        북마크 메뉴를 업데이트해요.
        북마크 목록에 있는 항목들로 메뉴를 다시 만들어요.
        """
        # 북마크 메뉴가 없으면 새로 만들기
        if not self.bookmark_menu:
            self.bookmark_menu = ScrollableMenu(self.parent)
            
        # 메뉴 내용 지우기
        self.bookmark_menu.clear()
        
        # 북마크 추가 메뉴 항목
        add_bookmark_action = QAction("북마크 추가", self.parent)
        add_bookmark_action.triggered.connect(self.add_bookmark)  # 추가 기능 연결
        self.bookmark_menu.addAction(add_bookmark_action)
        
        # 북마크 제거 메뉴 항목
        remove_bookmark_action = QAction("현재 북마크 삭제", self.parent)
        remove_bookmark_action.triggered.connect(self.remove_bookmark)  # 삭제 기능 연결
        
        # 현재 이미지가 북마크에 없으면 비활성화
        if not hasattr(self.parent, 'current_image_path') or self.parent.current_image_path not in self.bookmarks:
            remove_bookmark_action.setEnabled(False)
            
        self.bookmark_menu.addAction(remove_bookmark_action)
        
        # 모든 북마크 지우기 메뉴 항목
        clear_action = QAction("모든 북마크 지우기", self.parent)
        clear_action.triggered.connect(self.clear_bookmarks)
        
        # 북마크가 없으면 비활성화
        if not self.bookmarks:
            clear_action.setEnabled(False)
            
        self.bookmark_menu.addAction(clear_action)
        
        # 구분선 추가
        self.bookmark_menu.addSeparator()
        
        # 북마크가 없으면 "북마크 없음" 메뉴 항목 추가
        if not self.bookmarks:
            empty_action = QAction("북마크 없음", self.parent)
            empty_action.setEnabled(False)
            self.bookmark_menu.addAction(empty_action)
            
        # 북마크 개수 표시 메뉴 항목
        bookmark_count_action = QAction(f"총 북마크: {len(self.bookmarks)}개", self.parent)
        bookmark_count_action.setEnabled(False)
        self.bookmark_menu.addAction(bookmark_count_action)
        
        # 또 다른 구분선 추가
        self.bookmark_menu.addSeparator()
        
        # 북마크가 많으면 최대 100개만 표시
        max_bookmarks = min(100, len(self.bookmarks))
        
        # 북마크 목록 메뉴에 추가
        for idx, path in enumerate(self.bookmarks[:max_bookmarks]):
            # 파일 이름만 추출 (경로는 툴팁에 표시)
            file_name = os.path.basename(path)
            
            # 북마크 번호 (1부터 시작)
            number = idx + 1
            
            # 표시할 텍스트 (번호 + 파일 이름)
            display_text = f"{number}. {file_name}"
            
            # 경로 표시 (줄이기)
            path_display = path
            if len(path_display) > 60:
                path_display = path_display[:30] + "..." + path_display[-27:]
                
            # 메뉴 항목 생성
            bookmark_action = QAction(display_text, self.parent)
            bookmark_action.setToolTip(path_display)  # 전체 경로는 툴팁으로 표시
            
            # 클릭 시 처리할 함수 만들기
            def create_bookmark_handler(bookmark_path):
                return lambda: self.load_bookmarked_image(bookmark_path)
                
            # 클릭 이벤트 연결
            bookmark_action.triggered.connect(create_bookmark_handler(path))
            self.bookmark_menu.addAction(bookmark_action)
            
        # 북마크가 100개 이상이면 "더 있음" 표시
        if len(self.bookmarks) > 100:
            more_action = QAction(f"... 외 {len(self.bookmarks) - 100}개 더 있습니다.", self.parent)
            more_action.setEnabled(False)
            self.bookmark_menu.addAction(more_action)
            
        # 메뉴가 스크롤 가능하도록 설정
        self.bookmark_menu.setProperty("_q_scrollable", True)
        
        # 북마크가 많으면 최대 높이 설정
        if len(self.bookmarks) > 7:
            desktop = QApplication.desktop().availableGeometry()
            max_height = min(800, desktop.height() * 0.8)  # 화면 높이의 80%까지 사용
            self.bookmark_menu.setMaximumHeight(int(max_height))
            
        # 스타일 업데이트
        self.bookmark_menu.setStyle(self.bookmark_menu.style())
    
    def load_bookmarked_image(self, path):
        """북마크된 이미지를 불러옵니다."""
        # 파일 존재 확인
        if not os.path.exists(path):
            self.parent.show_message(f"파일을 찾을 수 없습니다: {path}")
            return
        
        # 이미지가 있는 폴더의 모든 파일 불러오기
        folder_path = os.path.dirname(path)
        self.parent.image_files = self.parent.get_image_files(folder_path)
        
        if self.parent.image_files:
            self.parent.image_files.sort()
            # 현재 인덱스 설정
            try:
                self.parent.current_index = self.parent.image_files.index(path)
            except ValueError:
                self.parent.current_index = 0
        
        # AnimationHandler 정리 (중요!)
        if hasattr(self.parent, 'animation_handler'):
            self.parent.animation_handler.cleanup()
        
        # 기존 미디어 중지
        self.parent.stop_video()
        
        # 애니메이션 정지 (GIF/WEBP)
        if hasattr(self.parent, 'current_movie') and self.parent.current_movie:
            try:
                self.parent.current_movie.stop()
                self.parent.current_movie = None
            except Exception as e:
                print(f"애니메이션 정지 오류: {e}")
        
        # 이미지 레이블 초기화 (중요!)
        if hasattr(self.parent, 'image_label'):
            self.parent.image_label.clear()
        
        # 현재 이미지 경로 명시적 설정
        self.parent.current_image_path = path
        
        # 파일 이름을 제목표시줄에 표시
        file_name = os.path.basename(path)
        title_text = f"Image Viewer - {file_name}"
        
        # 제목표시줄 라벨 찾아서 텍스트 업데이트
        if hasattr(self.parent, 'title_bar'):
            for child in self.parent.title_bar.children():
                if isinstance(child, QLabel):
                    child.setText(title_text)
                    break
        
        # 시간 딜레이를 추가하여 기존 이미지가 제거될 시간을 확보
        QApplication.processEvents()
        
        # show_image 호출로 통합 (AnimationHandler를 사용하도록)
        self.parent.show_image(path)
        
        # 이미지 정보 업데이트 (인덱스 표시 등)
        self.parent.update_image_info()
        
        # 비디오 파일인 경우에만 추가 처리
        try:
            # media.format_detector 모듈 import
            from media.format_detector import FormatDetector
            file_format = FormatDetector.detect_format(path)
            
            # 비디오 파일만 추가 처리
            if file_format == 'video':
                self.parent.play_video(path)
                
        except ImportError:
            # FormatDetector 모듈을 찾을 수 없는 경우 확장자로 판단
            print("FormatDetector 모듈을 로드할 수 없습니다. 확장자로 판단합니다.")
            file_ext = os.path.splitext(path)[1].lower()
            
            # 비디오 파일만 추가 처리
            if file_ext in ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv']:
                self.parent.play_video(path)
        
        # 이미지 정보 업데이트 (인덱스 표시 등)
        self.parent.update_image_info()

    def clear_bookmarks(self):
        """
        모든 북마크를 지워요.
        """
        # 북마크 목록 비우기
        self.bookmarks = []
        
        # 북마크 버튼 상태 업데이트
        self.update_bookmark_button_state()
        
        # 북마크 메뉴 업데이트
        self.update_bookmark_menu()
        
        # 메시지 표시
        self.parent.show_message("모든 북마크가 삭제되었습니다.")
        
        # 북마크 저장
        self.save_bookmarks()
    
    def show_menu_above_button(self):
        """
        북마크 메뉴를 버튼 위에 표시해요.
        """
        # 북마크 버튼이 없거나 메뉴가 없으면 종료
        if not self.bookmark_button or not self.bookmark_menu:
            return
            
        # 메뉴를 표시하기 전에 업데이트하여 크기를 정확히 계산
        self.update_bookmark_menu()
        
        # 버튼 좌표를 전역 좌표로 변환
        pos = self.bookmark_button.mapToGlobal(QPoint(0, 0))
        
        # 메뉴 사이즈 계산
        menu_width = self.bookmark_menu.sizeHint().width()
        button_width = self.bookmark_button.width()
        
        # 최대 높이 설정
        desktop = QApplication.desktop().availableGeometry()
        max_height = min(800, desktop.height() * 0.8)  # 화면 높이의 80%까지 사용
        self.bookmark_menu.setMaximumHeight(int(max_height))
        
        # 메뉴 높이가 화면 높이보다 크면 화면의 80%로 제한
        menu_height = min(self.bookmark_menu.sizeHint().height(), max_height)
        
        # 기준을 버튼의 오른쪽 변으로 설정 (메뉴의 오른쪽 가장자리를 버튼의 오른쪽 가장자리에 맞춤)
        button_right_edge = pos.x() + button_width
        x_pos = button_right_edge - menu_width  # 메뉴의 오른쪽 끝이 버튼의 오른쪽 끝과 일치하도록 계산
        y_pos = pos.y() - menu_height  # 버튼 위에 메뉴가 나타나도록 설정
        
        # 메뉴가 화면 왼쪽 경계를 벗어나는지 확인
        if x_pos < desktop.left():
            x_pos = desktop.left()
        
        # 메뉴가 화면 위로 넘어가지 않도록 조정
        if y_pos < desktop.top():
            # 화면 위로 넘어가면 버튼 아래에 표시
            y_pos = pos.y() + self.bookmark_button.height()
        
        # 메뉴가 화면 아래로 넘어가지 않도록 조정
        if y_pos + menu_height > desktop.bottom():
            # 화면 아래로 넘어가면 버튼 위에 표시하되, 필요한 만큼만 위로 올림
            y_pos = desktop.bottom() - menu_height
        
        # 메뉴 팝업 (스크롤이 필요한 경우를 위해 높이 속성 명시적 설정)
        self.bookmark_menu.setProperty("_q_scrollable", True)
        self.bookmark_menu.popup(QPoint(x_pos, y_pos)) 