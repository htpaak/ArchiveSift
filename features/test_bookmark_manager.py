"""
북마크 관리자 테스트

이 파일은 BookmarkManager 클래스를 테스트해요.
북마크 추가, 제거, 저장, 불러오기 등의 기능이 제대로 작동하는지 확인해요.
"""

import os
import tempfile
import json
import unittest
from unittest.mock import MagicMock, patch

from features.bookmark_manager import BookmarkManager

class MockParent:
    """
    테스트용 부모 클래스 (ImageViewer 대신 사용)
    """
    def __init__(self):
        self.current_image_path = None
        self.messages = []
    
    def show_message(self, message):
        self.messages.append(message)
        print(f"메시지: {message}")
    
    def update_bookmark_button_state(self):
        pass
    
    def show_image(self, path):
        self.current_image_path = path
        print(f"이미지 표시: {path}")
    
    def play_video(self, path):
        self.current_image_path = path
        print(f"비디오 재생: {path}")
    
    def show_gif(self, path):
        self.current_image_path = path
        print(f"GIF 표시: {path}")
    
    def show_webp(self, path):
        self.current_image_path = path
        print(f"WEBP 표시: {path}")
    
    def show_psd(self, path):
        self.current_image_path = path
        print(f"PSD 표시: {path}")

class TestBookmarkManager(unittest.TestCase):
    """
    BookmarkManager 클래스 테스트
    """
    
    def setUp(self):
        """
        테스트 준비: 임시 파일과 가짜 부모 객체 생성
        """
        self.parent = MockParent()
        
        # 임시 폴더 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_path = os.path.join(self.temp_dir.name, "test.jpg")
        
        # 가짜 이미지 파일 생성
        with open(self.test_path, 'w') as f:
            f.write("테스트 이미지 파일")
        
        # 현재 이미지 경로 설정
        self.parent.current_image_path = self.test_path
        
        # 북마크 관리자 생성
        self.bookmark_manager = BookmarkManager(self.parent)
        
        # 저장 경로 설정을 패치하여 임시 경로 사용
        self.temp_bookmark_file = os.path.join(self.temp_dir.name, "bookmarks.json")
        self.patcher = patch('features.bookmark_manager.get_user_data_directory', 
                         return_value=self.temp_dir.name)
        self.mock_get_dir = self.patcher.start()
    
    def tearDown(self):
        """
        테스트 후 정리: 임시 파일 삭제
        """
        self.patcher.stop()
        self.temp_dir.cleanup()
    
    def test_add_bookmark(self):
        """
        북마크 추가 기능 테스트
        """
        # 처음에는 북마크가 없어야 함
        self.assertEqual(len(self.bookmark_manager.bookmarks), 0)
        
        # 북마크 추가
        self.bookmark_manager.add_bookmark()
        
        # 북마크가 추가되었는지 확인
        self.assertEqual(len(self.bookmark_manager.bookmarks), 1)
        self.assertIn(self.test_path, self.bookmark_manager.bookmarks)
        
        # 메시지가 표시되었는지 확인
        self.assertIn("북마크에 추가되었습니다.", self.parent.messages)
        
        # 북마크 파일이 생성되었는지 확인
        self.assertTrue(os.path.exists(self.temp_bookmark_file))
        
        # 북마크 파일 내용 확인
        with open(self.temp_bookmark_file, 'r') as f:
            saved_bookmarks = json.load(f)
            self.assertEqual(len(saved_bookmarks), 1)
            self.assertEqual(saved_bookmarks[0], self.test_path)
    
    def test_remove_bookmark(self):
        """
        북마크 제거 기능 테스트
        """
        # 먼저 북마크 추가
        self.bookmark_manager.add_bookmark()
        self.assertEqual(len(self.bookmark_manager.bookmarks), 1)
        
        # 북마크 제거
        self.bookmark_manager.remove_bookmark()
        
        # 북마크가 제거되었는지 확인
        self.assertEqual(len(self.bookmark_manager.bookmarks), 0)
        
        # 메시지가 표시되었는지 확인
        self.assertIn("북마크에서 제거되었습니다.", self.parent.messages)
        
        # 북마크 파일이 업데이트되었는지 확인
        with open(self.temp_bookmark_file, 'r') as f:
            saved_bookmarks = json.load(f)
            self.assertEqual(len(saved_bookmarks), 0)
    
    def test_toggle_bookmark(self):
        """
        북마크 토글(추가/제거) 기능 테스트
        """
        # 처음에는 북마크가 없어야 함
        self.assertEqual(len(self.bookmark_manager.bookmarks), 0)
        
        # 북마크 토글 (추가)
        self.bookmark_manager.toggle_bookmark()
        self.assertEqual(len(self.bookmark_manager.bookmarks), 1)
        self.assertIn(self.test_path, self.bookmark_manager.bookmarks)
        
        # 북마크 토글 (제거)
        self.bookmark_manager.toggle_bookmark()
        self.assertEqual(len(self.bookmark_manager.bookmarks), 0)
        self.assertNotIn(self.test_path, self.bookmark_manager.bookmarks)
    
    def test_clear_bookmarks(self):
        """
        모든 북마크 제거 기능 테스트
        """
        # 여러 개의 가짜 북마크 추가
        self.bookmark_manager.bookmarks = [
            self.test_path,
            os.path.join(self.temp_dir.name, "test2.jpg"),
            os.path.join(self.temp_dir.name, "test3.jpg")
        ]
        
        # 북마크 모두 제거
        self.bookmark_manager.clear_bookmarks()
        
        # 북마크가 모두 제거되었는지 확인
        self.assertEqual(len(self.bookmark_manager.bookmarks), 0)
        
        # 메시지가 표시되었는지 확인
        self.assertIn("모든 북마크가 삭제되었습니다.", self.parent.messages)

if __name__ == "__main__":
    # 테스트 실행
    unittest.main() 