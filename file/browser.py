"""
폴더 브라우저 모듈

이 모듈은 폴더를 열고 폴더 내의 미디어 파일을 관리하는 기능을 제공합니다.
사용자가 폴더를 선택하고 그 안의 미디어 파일들을 열람할 수 있도록 합니다.
"""

import os
from PyQt5.QtWidgets import QFileDialog
from core.utils.sort_utils import natural_keys  # 파일 이름 자연 정렬을 위한 유틸리티 함수 추가


class FileBrowser:
    """
    파일 브라우저 클래스
    
    이 클래스는 폴더 선택 및 폴더 내의 미디어 파일을 관리하는 기능을 제공합니다.
    사용자가 폴더를 선택하고 그 안의 미디어 파일들을 확인하는 데 사용됩니다.
    또한, 폴더 내의 지원되는 미디어 파일을 필터링하여 제공합니다.
    """
    
    def __init__(self, parent=None):
        """
        FileBrowser 클래스 초기화
        
        매개변수:
            parent: 부모 위젯 (일반적으로 메인 어플리케이션 창)
        """
        self.parent = parent
        self.current_folder = None
        
        # 지원하는 파일 확장자 목록 (이미지, 비디오, 오디오 파일)
        self.valid_extensions = [
            # 이미지 형식
            '.jpg', '.jpeg', '.png', '.webp', '.psd', '.gif', '.bmp', 
            '.tiff', '.tif', '.ico', '.heic', '.heif', '.avif',
            # RAW 이미지 형식
            '.cr2', '.nef', '.arw',
            # 비디오 형식
            '.mp4', '.avi', '.wav', '.ts', '.m2ts', '.mov', '.qt', 
            '.mkv', '.flv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', 
            '.vob', '.wmv', 
            # 오디오 형식
            '.mp3', '.flac', '.aac', '.m4a', '.ogg'
        ]
    
    def open_folder_dialog(self):
        """
        폴더 선택 대화상자를 표시하고 선택된 폴더 경로를 반환합니다.
        
        반환값:
            str: 선택된 폴더 경로 또는 취소 시 None
        """
        folder_path = QFileDialog.getExistingDirectory(self.parent, "Open Image Folder")
        if folder_path:
            self.current_folder = folder_path
            return folder_path
        return None
    
    def process_folder(self, folder_path):
        """
        지정된 폴더에서 미디어 파일을 가져와 정렬합니다.
        
        매개변수:
            folder_path (str): 미디어 파일을 검색할 폴더 경로
            
        반환값:
            list: 정렬된 미디어 파일 경로 목록
            int: 첫 번째 이미지의 인덱스 (일반적으로 0)
        """
        if not folder_path:
            return [], -1
            
        # 미디어 파일 가져오기
        media_files = self.get_media_files(folder_path)
        
        if media_files:
            # 파일 목록을 자연 정렬 적용 (숫자가 포함된 파일명 정렬에 적합)
            media_files.sort(key=natural_keys)
            return media_files, 0
        else:
            print(f"No valid media files found in the folder: {folder_path}")
            return [], -1
    
    def get_media_files(self, folder_path):
        """
        지정된 폴더에서 지원하는 모든 미디어 파일 목록을 가져옵니다.
        
        매개변수:
            folder_path (str): 미디어 파일을 검색할 폴더 경로
            
        반환값:
            list: 미디어 파일 경로 목록
        """
        # 폴더가 존재하지 않으면 빈 목록 반환
        if not os.path.exists(folder_path):
            print(f"폴더가 존재하지 않습니다: {folder_path}")
            return []
            
        try:
            # 폴더 내에서 지원하는 확장자를 가진 모든 파일 경로 목록 반환
            return [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                    if any(f.lower().endswith(ext) for ext in self.valid_extensions)]
        except Exception as e:
            print(f"폴더에서 파일을 가져오는 중 오류 발생: {e}")
            return []
            
    def get_folder_name(self, path):
        """
        파일 경로에서 폴더 이름을 추출합니다.
        
        매개변수:
            path (str): 파일 또는 폴더 경로
            
        반환값:
            str: 폴더 이름
        """
        if not path:
            return ""
            
        if os.path.isfile(path):
            path = os.path.dirname(path)
            
        return os.path.basename(path) 