"""
북마크 관리 모듈

이 모듈은 북마크(즐겨찾기)를 관리하는 기능을 담당해요.
사용자가 자주 보는 이미지나 비디오를 북마크에 추가하고 나중에 쉽게 다시 볼 수 있게 해줘요.
"""

import os
import json
from PyQt5.QtWidgets import QAction, QApplication, QPushButton, QSizePolicy, QMenu, QWidget, QLabel
from PyQt5.QtCore import QPoint, Qt, QTimer

from core.utils.path_utils import get_user_data_directory
from core.utils.sort_utils import natural_keys
from ui.components.scrollable_menu import ScrollableMenu
from .bookmark_ui import BookmarkUI

class BookmarkManager:
    """
    북마크 관리 클래스
    
    이 클래스는 북마크를 추가, 제거, 저장, 불러오기하는 기능을 담당해요.
    또한 북마크 메뉴와 북마크 버튼 상태도 관리해요.
    """
    
    def __init__(self, viewer):
        """
        북마크 관리자를 초기화해요.
        
        매개변수:
            viewer: 부모 위젯 (보통 ArchiveSift 클래스)
        """
        self.viewer = viewer
        self.bookmarks = []  # 북마크를 set 대신 list로 사용하여 순서 유지
        self.ui = BookmarkUI(self)
        self.load_bookmarks()
    
    def set_bookmark_button(self, button):
        """
        북마크 버튼을 설정해요.
        
        매개변수:
            button: 북마크 버튼 (★ 모양 버튼)
        """
        self.ui.set_bookmark_button(button)
    
    def update_bookmark_button_state(self):
        """
        북마크 버튼의 상태를 업데이트해요.
        현재 이미지가 북마크에 있으면 노란색 배경, 없으면 기본 배경으로 표시해요.
        """
        self.ui.update_bookmark_button_state()
    
    def update_bookmark_menu(self):
        """
        북마크 메뉴를 업데이트해요.
        북마크 목록에 있는 항목들로 메뉴를 다시 만들어요.
        """
        self.ui.create_bookmark_menu()
    
    def show_menu_above_button(self):
        """
        북마크 메뉴를 버튼 위에 표시해요.
        """
        self.ui.show_menu_above_button()
    
    def is_bookmarked(self, path):
        """
        주어진 경로가 북마크에 있는지 확인해요.
        
        매개변수:
            path: 확인할 파일 경로
            
        반환값:
            bool: 북마크에 있으면 True, 없으면 False
        """
        return path in self.bookmarks
    
    def toggle_bookmark(self):
        """
        현재 이미지의 북마크 상태를 전환해요 (있으면 제거, 없으면 추가).
        """
        if not hasattr(self.viewer, 'current_image_path') or not self.viewer.current_image_path:
            return
            
        if self.viewer.current_image_path in self.bookmarks:
            self.remove_bookmark()
            # 메시지 표시, 북마크 버튼 상태 업데이트, 저장은 remove_bookmark에서 처리
        else:
            self.add_bookmark()
            # 메시지 표시
            if hasattr(self.viewer, 'show_message'):
                self.viewer.show_message(f"Bookmark added: {os.path.basename(self.viewer.current_image_path)}")
        # 북마크 버튼 상태 업데이트, 메뉴 업데이트, 저장은 add_bookmark, remove_bookmark에서 처리
    
    def add_bookmark(self):
        """
        현재 이미지를 북마크에 추가해요.
        """
        if hasattr(self.viewer, 'current_image_path') and self.viewer.current_image_path:
            # 이미 북마크에 있는 경우 제거
            if self.viewer.current_image_path in self.bookmarks:
                self.bookmarks.remove(self.viewer.current_image_path)
            # 리스트 마지막에 추가하여 최신 북마크가 아래에 표시되도록 함
            self.bookmarks.append(self.viewer.current_image_path)
            
            # 북마크 저장
            self.save_bookmarks()
            
            # 북마크 버튼 상태 업데이트
            self.update_bookmark_button_state()
            
            # 북마크 메뉴 업데이트
            self.update_bookmark_menu()
    
    def remove_bookmark(self):
        """
        현재 이미지를 북마크에서 제거해요.
        """
        if hasattr(self.viewer, 'current_image_path') and self.viewer.current_image_path:
            if self.viewer.current_image_path in self.bookmarks:
                path = self.viewer.current_image_path
                self.bookmarks.remove(path)
                
                # 북마크 저장
                self.save_bookmarks()
                
                # 북마크 버튼 상태 업데이트
                self.update_bookmark_button_state()
                
                # 북마크 메뉴 업데이트
                self.update_bookmark_menu()
                
                # 메시지 표시
                if hasattr(self.viewer, 'show_message'):
                    self.viewer.show_message(f"Bookmark removed: {os.path.basename(path)}")
    
    def save_bookmarks(self):
        """
        북마크 정보를 JSON 파일로 저장해요.
        """
        bookmark_file = os.path.join(get_user_data_directory(), "bookmarks.json")
        try:
            with open(bookmark_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error occurred while saving bookmarks: {e}")
    
    def load_bookmarks(self):
        """
        JSON 파일에서 북마크 정보를 불러와요.
        """
        bookmark_file = os.path.join(get_user_data_directory(), "bookmarks.json")
        try:
            if os.path.exists(bookmark_file):
                with open(bookmark_file, 'r', encoding='utf-8') as f:
                    loaded_bookmarks = json.load(f)
                    # 기존 JSON이 리스트가 아닌 경우 (이전 버전 호환성)
                    if isinstance(loaded_bookmarks, list):
                        self.bookmarks = loaded_bookmarks
                    else:
                        # set이나 다른 형태로 저장된 경우 리스트로 변환
                        self.bookmarks = list(loaded_bookmarks)
        except Exception as e:
            print(f"Error occurred while loading bookmarks: {e}")
            self.bookmarks = []
    
    def load_bookmarked_image(self, path):
        """
        북마크된 이미지를 불러옵니다.
        해당 이미지가 포함된 폴더의 모든 파일을 로드하고,
        정렬된 목록에서 해당 이미지의 정확한 인덱스를 설정합니다.
        """
        if not os.path.exists(path):
            print(f"Bookmark error: File does not exist - {path}")
            self.viewer.show_message(f"Error: Bookmarked file not found.")
            # 존재하지 않는 북마크 제거
            if path in self.bookmarks:
                self.bookmarks.remove(path)
                self.save_bookmarks()
                self.update_bookmark_menu()
            return

        folder = os.path.dirname(path)
        
        # FileBrowser 인스턴스를 통해 파일 목록 가져오기 및 정렬
        # viewer에 file_browser가 있는지 확인
        if not hasattr(self.viewer, 'file_browser'):
             print("Error: FileBrowser not found in viewer.")
             self.viewer.show_message("Error: Cannot process folder.")
             return
             
        # FileBrowser의 process_folder를 사용하여 정렬된 파일 목록 가져오기
        # process_folder는 (파일 리스트, 시작 인덱스)를 반환하므로 리스트만 사용
        full_path_files, _ = self.viewer.file_browser.process_folder(folder)

        if not full_path_files:
            print(f"Bookmark error: No valid media files found in folder - {folder}")
            self.viewer.show_message(f"Error: No media files found in the bookmarked folder.")
            return

        # 정렬된 리스트에서 북마크된 파일의 인덱스 찾기
        try:
            current_index = full_path_files.index(path)
        except ValueError:
            print(f"Bookmark error: Bookmarked file '{path}' not found in the processed list for folder '{folder}'.")
            self.viewer.show_message("Error: Could not locate the bookmarked file within its folder.")
            # 파일을 찾을 수 없으면 첫 번째 파일로 이동 (또는 오류 처리)
            current_index = 0 
            path = full_path_files[0] # 표시할 경로도 첫 번째 파일로 변경

        # --- 기존 미디어 정리 ---
        self.viewer.cleanup_current_media() # 통합된 정리 함수 사용

        # --- 메인 뷰어 상태 업데이트 ---
        self.viewer.image_files = full_path_files
        self.viewer.current_index = current_index
        self.viewer.current_image_path = path
        
        # 상태 관리자 업데이트 (존재하는 경우)
        if hasattr(self.viewer, 'state_manager'):
            self.viewer.state_manager.set_state("current_index", current_index)
            self.viewer.state_manager.set_state("current_image_path", path)
            
        # 파일 내비게이터 업데이트
        if hasattr(self.viewer, 'file_navigator'):
            self.viewer.file_navigator.set_files(full_path_files, current_index)
            
        # 이미지 레이블 초기화 (선택적이지만, 이전 상태 제거에 도움될 수 있음)
        if hasattr(self.viewer, 'image_label'):
            self.viewer.image_label.clear()
            
        # --- 새 미디어 표시 ---
        # 창 제목 업데이트
        self.viewer.update_window_title(path)
        
        # UI 즉시 업데이트 (필요 시)
        QApplication.processEvents()

        # show_image 호출하여 이미지/미디어 표시
        self.viewer.show_image(path)

        # 이미지 정보 레이블 업데이트 (인덱스 등)
        self.viewer.update_image_info()
        
        # 북마크 버튼 상태 업데이트
        self.update_bookmark_button_state()

    def clear_bookmarks(self):
        """
        Clear all bookmarks.
        """
        # 북마크 목록 비우기
        self.bookmarks.clear()
        
        # 북마크 버튼 상태 업데이트
        self.update_bookmark_button_state()
        
        # 북마크 메뉴 업데이트
        self.update_bookmark_menu()
        
        # 메시지 표시
        self.viewer.show_message("All bookmarks have been deleted.")
        
        # 북마크 저장
        self.save_bookmarks() 