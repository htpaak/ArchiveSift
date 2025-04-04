"""
실행 취소 관리 모듈

이 모듈은 삭제된 파일을 추적하고 복원하는 기능을 담당합니다.
"""

import os
import shutil
from collections import deque
import time
import platform
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QObject, pyqtSignal

# Windows 환경에서 사용할 winshell 패키지
try:
    import winshell
    WINSHELL_AVAILABLE = True
except ImportError:
    WINSHELL_AVAILABLE = False

class UndoManager(QObject):
    """
    실행 취소 관리 클래스
    
    이 클래스는 삭제된 파일을 추적하고 복원하는 기능을 담당합니다.
    파일이 휴지통으로 이동된 경우 원본 경로를 기억하고, 나중에 복원할 수 있습니다.
    """
    
    # 작업 실행 취소 가능 상태 변경 시그널
    undo_status_changed = pyqtSignal(bool)
    
    def __init__(self, viewer):
        """
        UndoManager 초기화
        
        Args:
            viewer: 메인 뷰어 인스턴스 (ArchiveSift)
        """
        super().__init__()
        self.viewer = viewer
        self.deleted_files = deque(maxlen=10)  # 최대 10개 파일 추적
        self.trash_to_original = {}  # 휴지통 경로 -> 원본 경로 매핑
    
    def track_deleted_file(self, original_path, deleted_success):
        """
        삭제된 파일 추적하기
        
        Args:
            original_path: 원본 파일 경로
            deleted_success: 삭제 성공 여부
        """
        if deleted_success:
            # 파일의 원래 인덱스를 저장
            original_index = -1
            if hasattr(self.viewer, 'file_navigator'):
                original_index = self.viewer.file_navigator.get_current_index()
            
            # 파일 경로, 삭제 시간, 원래 인덱스 저장
            self.deleted_files.appendleft((original_path, time.time(), original_index))
            self.undo_status_changed.emit(True)  # Undo 가능 상태로 변경
    
    def can_undo(self):
        """
        실행 취소 가능 여부 확인
        
        Returns:
            bool: 실행 취소 가능 여부
        """
        return len(self.deleted_files) > 0
    
    def undo_last_deletion(self):
        """
        마지막 삭제 작업 취소
        
        Returns:
            tuple: (성공 여부, 복원된 파일 경로)
        """
        if not self.deleted_files:
            self.viewer.show_message("실행 취소할 작업이 없습니다")
            return False, None
        
        # 원래 정보 추출
        if len(self.deleted_files[0]) >= 3:
            original_path, delete_time, original_index = self.deleted_files.popleft()
        else:
            # 하위 호환성 유지 (이전 버전에서 인덱스 정보 없는 경우)
            original_path, delete_time = self.deleted_files.popleft()
            original_index = -1
        
        # 삭제 취소가 가능한지 확인 (파일이 이미 존재하는지)
        if os.path.exists(original_path):
            self.viewer.show_message(f"이미 해당 경로에 파일이 존재합니다: {os.path.basename(original_path)}")
            # 더 이상 실행 취소할 항목이 없으면 상태 업데이트
            if not self.deleted_files:
                self.undo_status_changed.emit(False)
            return False, None
        
        # 휴지통에서 원본 위치로 복원
        try:
            # 원본 디렉토리가 존재하는지 확인
            original_dir = os.path.dirname(original_path)
            if not os.path.exists(original_dir):
                os.makedirs(original_dir, exist_ok=True)
                
            # 파일 복원 시도
            self.viewer.show_message(f"파일 복원 중: {os.path.basename(original_path)}")
            
            # 실제 파일 복원 시도
            restored_file = self._restore_from_trash(original_path)
            
            # 파일 목록에 다시 추가
            list_updated = False
            if restored_file:
                # 실제 파일이 복원된 경우 파일 목록 업데이트
                list_updated = self._add_to_file_list(original_path, original_index)
            
            # 더 이상 실행 취소할 항목이 없으면 상태 업데이트
            if not self.deleted_files:
                self.undo_status_changed.emit(False)
                
            if restored_file and list_updated:
                self.viewer.show_message(f"파일이 복원되었습니다: {os.path.basename(original_path)}")
                return True, original_path
            elif restored_file:
                self.viewer.show_message(f"파일은 복원되었지만 목록에 추가하지 못했습니다: {os.path.basename(original_path)}")
                return True, original_path
            else:
                self.viewer.show_message(f"파일 복원 실패: {os.path.basename(original_path)}")
                return False, None
                
        except Exception as e:
            self.viewer.show_message(f"파일 복원 실패: {str(e)}")
            return False, None
    
    def _restore_from_trash(self, original_path):
        """
        휴지통에서 파일 복원 시도
        
        Args:
            original_path: 원본 파일 경로
            
        Returns:
            bool: 복원 성공 여부
        """
        try:
            file_name = os.path.basename(original_path)
            
            # Windows 환경에서 winshell을 사용하여 휴지통 검색
            if platform.system() == 'Windows' and WINSHELL_AVAILABLE:
                # 휴지통의 모든 항목을 검색
                recycled_items = list(winshell.recycle_bin())
                
                # 원본 파일명과 일치하는 항목 찾기
                for item in recycled_items:
                    # 항목 이름 가져오기 (전체 경로에서 파일명만)
                    item_name = os.path.basename(item.original_filename())
                    
                    # 원본 파일명과 일치하면 복원
                    if item_name.lower() == file_name.lower():
                        # 원본 위치로 복원
                        winshell.undelete(item.original_filename())
                        
                        # 가끔 원래 위치가 아닌 경로로 복원될 수 있으므로 확인
                        if os.path.exists(original_path):
                            return True
                        
                        # 다른 위치에 복원된 경우 원하는 위치로 이동
                        restored_path = item.original_filename()
                        if os.path.exists(restored_path):
                            shutil.move(restored_path, original_path)
                            return True
                
                # 파일을 찾지 못한 경우
                self.viewer.show_message(f"휴지통에서 {file_name}을(를) 찾을 수 없습니다")
                return False
                
            # 다른 OS 환경에서는 대체 방법 제공
            else:
                # 파일 목록에만 추가 (실제 파일은 복원하지 않음)
                self.viewer.show_message("이 운영체제에서는 휴지통 복원 기능이 제한됩니다.")
                return True
                
        except Exception as e:
            self.viewer.show_message(f"휴지통 복원 실패: {str(e)}")
            return False
    
    def _add_to_file_list(self, file_path, original_index=-1):
        """
        파일 목록에 파일 추가
        
        Args:
            file_path: 추가할 파일 경로
            original_index: 원래 파일의 인덱스 (기본값 -1: 알 수 없음)
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 파일이 이미 목록에 있는지 확인
            if hasattr(self.viewer, 'image_files') and file_path in self.viewer.image_files:
                return True
                
            # 파일 목록에 추가
            if hasattr(self.viewer, 'file_navigator'):
                if original_index >= 0:
                    # 원래 인덱스 위치에 파일 삽입
                    navigator = self.viewer.file_navigator
                    
                    # 파일 목록 가져오기
                    files = navigator.get_files()
                    
                    # 인덱스가 현재 목록 길이보다 큰 경우 조정
                    if original_index > len(files):
                        original_index = len(files)
                    
                    # 직접 파일 목록에 삽입
                    files.insert(original_index, file_path)
                    
                    # 파일 목록 업데이트
                    navigator.set_files(files, original_index)
                    self.viewer.image_files = navigator.get_files()
                    
                    # 복원된 파일로 이동
                    self.viewer.show_image(file_path)
                else:
                    # 원래 인덱스를 모르는 경우 기본 add_file 사용
                    self.viewer.file_navigator.add_file(file_path)
                    self.viewer.image_files = self.viewer.file_navigator.get_files()
                    
                    # 복원된 파일 표시
                    self.viewer.show_image(file_path)
                
                return True
                
            return False
        except Exception as e:
            print(f"파일 목록 추가 실패: {str(e)}")
            return False 