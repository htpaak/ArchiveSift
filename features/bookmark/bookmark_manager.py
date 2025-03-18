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
            viewer: 부모 위젯 (보통 ImageViewer 클래스)
        """
        self.viewer = viewer
        self.bookmarks = set()
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
    
    def toggle_bookmark(self):
        """
        현재 이미지의 북마크 상태를 전환해요 (있으면 제거, 없으면 추가).
        """
        if not hasattr(self.viewer, 'current_image_path') or not self.viewer.current_image_path:
            return
            
        if self.viewer.current_image_path in self.bookmarks:
            self.remove_bookmark()
            self.viewer.show_message("북마크가 제거되었습니다")
        else:
            self.add_bookmark()
            self.viewer.show_message("북마크가 추가되었습니다")
            
        self.update_bookmark_button_state()
        self.save_bookmarks()
    
    def add_bookmark(self):
        """
        현재 이미지를 북마크에 추가해요.
        """
        if hasattr(self.viewer, 'current_image_path') and self.viewer.current_image_path:
            self.bookmarks.add(self.viewer.current_image_path)
            
    def remove_bookmark(self):
        """
        현재 이미지를 북마크에서 제거해요.
        """
        if hasattr(self.viewer, 'current_image_path') and self.viewer.current_image_path:
            self.bookmarks.discard(self.viewer.current_image_path)
            
    def save_bookmarks(self):
        """
        북마크 정보를 JSON 파일로 저장해요.
        """
        bookmark_file = os.path.join(get_user_data_directory(), "bookmarks.json")
        try:
            with open(bookmark_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.bookmarks), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"북마크 저장 중 오류 발생: {e}")
    
    def load_bookmarks(self):
        """
        JSON 파일에서 북마크 정보를 불러와요.
        """
        bookmark_file = os.path.join(get_user_data_directory(), "bookmarks.json")
        try:
            if os.path.exists(bookmark_file):
                with open(bookmark_file, 'r', encoding='utf-8') as f:
                    self.bookmarks = set(json.load(f))
        except Exception as e:
            print(f"북마크 로드 중 오류 발생: {e}")
            self.bookmarks = set()
    
    def load_bookmarked_image(self, path):
        """북마크된 이미지를 불러옵니다."""
        if os.path.exists(path):
            # 이미지가 있는 폴더의 모든 이미지 불러오기
            folder = os.path.dirname(path)
            self.viewer.image_files = self.viewer.get_image_files(folder)
            
            if self.viewer.image_files:
                self.viewer.image_files.sort()
                # 현재 인덱스 설정
                try:
                    self.viewer.current_index = self.viewer.image_files.index(path)
                except ValueError:
                    self.viewer.current_index = 0
            
            # AnimationHandler 정리 (중요!)
            if hasattr(self.viewer, 'animation_handler'):
                self.viewer.animation_handler.cleanup()
            
            # 기존 미디어 중지
            self.viewer.stop_video()
            
            # 애니메이션 정지 (GIF/WEBP)
            if hasattr(self.viewer, 'current_movie') and self.viewer.current_movie:
                try:
                    self.viewer.current_movie.stop()
                    self.viewer.current_movie = None
                except Exception as e:
                    print(f"애니메이션 정지 오류: {e}")
            
            # 이미지 레이블 초기화 (중요!)
            if hasattr(self.viewer, 'image_label'):
                self.viewer.image_label.clear()
            
            # 현재 이미지 경로 명시적 설정
            self.viewer.current_image_path = path
            
            # 파일 이름을 제목표시줄에 표시
            file_name = os.path.basename(path)
            title_text = f"Image Viewer - {file_name}"
            
            # 제목표시줄 라벨 찾아서 텍스트 업데이트
            if hasattr(self.viewer, 'title_bar'):
                for child in self.viewer.title_bar.children():
                    if isinstance(child, QLabel):
                        child.setText(title_text)
                        break
            
            # 시간 딜레이를 추가하여 기존 이미지가 제거될 시간을 확보
            QApplication.processEvents()
            
            # show_image 호출로 통합 (AnimationHandler를 사용하도록)
            self.viewer.show_image(path)
            
            # 이미지 정보 업데이트 (인덱스 표시 등)
            self.viewer.update_image_info()
            
            # 비디오 파일인 경우에만 추가 처리
            try:
                # media.format_detector 모듈 import
                from media.format_detector import FormatDetector
                file_format = FormatDetector.detect_format(path)
                
                # 비디오 파일만 추가 처리
                if file_format == 'video':
                    self.viewer.play_video(path)
                    
            except ImportError:
                # FormatDetector 모듈을 찾을 수 없는 경우 확장자로 판단
                print("FormatDetector 모듈을 로드할 수 없습니다. 확장자로 판단합니다.")
                file_ext = os.path.splitext(path)[1].lower()
                
                # 비디오 파일만 추가 처리
                if file_ext in ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv']:
                    self.viewer.play_video(path)
            
            # 이미지 정보 업데이트 (인덱스 표시 등)
            self.viewer.update_image_info()
        else:
            # 파일이 없으면 북마크에서 제거
            self.bookmarks.discard(path)
            self.save_bookmarks()
            self.viewer.show_message("파일을 찾을 수 없습니다")

    def clear_bookmarks(self):
        """
        모든 북마크를 지워요.
        """
        # 북마크 목록 비우기
        self.bookmarks.clear()
        
        # 북마크 버튼 상태 업데이트
        self.update_bookmark_button_state()
        
        # 북마크 메뉴 업데이트
        self.update_bookmark_menu()
        
        # 메시지 표시
        self.viewer.show_message("모든 북마크가 삭제되었습니다.")
        
        # 북마크 저장
        self.save_bookmarks() 