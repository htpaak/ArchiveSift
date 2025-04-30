"""
실행 취소 관리 모듈

이 모듈은 삭제된 파일을 추적하고 복원하는 기능을 담당합니다.
"""

import os
import shutil
import gc
from collections import deque
import time
import platform
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

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
    
    # 작업 유형 상수
    ACTION_DELETE = "delete"
    ACTION_MOVE = "move"
    ACTION_COPY = "copy"
    
    def __init__(self, viewer):
        """
        UndoManager 초기화
        
        Args:
            viewer: 메인 뷰어 인스턴스 (ImageSortingPAAK)
        """
        super().__init__()
        self.viewer = viewer
        # 이제 deleted_files 대신 actions 큐를 사용해 삭제뿐만 아니라 모든 작업 추적
        self.actions = deque(maxlen=10)  # 최대 10개 작업 추적
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
            self.actions.appendleft({
                'type': self.ACTION_DELETE,
                'path': original_path,
                'time': time.time(),
                'index': original_index
            })
            self.undo_status_changed.emit(True)  # Undo 가능 상태로 변경
    
    def track_moved_file(self, original_path, new_path, moved_success):
        """
        이동된 파일 추적하기
        
        Args:
            original_path: 원본 파일 경로
            new_path: 이동된 파일 경로
            moved_success: 이동 성공 여부
        """
        if moved_success:
            # 파일의 원래 인덱스를 저장
            original_index = -1
            if hasattr(self.viewer, 'file_navigator'):
                original_index = self.viewer.file_navigator.get_current_index()
            
            # 파일 이동 정보 저장
            self.actions.appendleft({
                'type': self.ACTION_MOVE,
                'original_path': original_path,
                'new_path': new_path,
                'time': time.time(),
                'index': original_index
            })
            self.undo_status_changed.emit(True)  # Undo 가능 상태로 변경
    
    def track_copied_file(self, original_path, copied_path, copied_success):
        """
        복사된 파일 추적하기
        
        Args:
            original_path: 원본 파일 경로
            copied_path: 복사된 파일 경로
            copied_success: 복사 성공 여부
        """
        if copied_success:
            # 파일의 원래 인덱스를 저장
            original_index = -1
            if hasattr(self.viewer, 'file_navigator'):
                original_index = self.viewer.file_navigator.get_current_index()
            
            # 파일 복사 정보 저장
            self.actions.appendleft({
                'type': self.ACTION_COPY,
                'original_path': original_path,
                'copied_path': copied_path,
                'time': time.time(),
                'index': original_index
            })
            self.undo_status_changed.emit(True)  # Undo 가능 상태로 변경
    
    def can_undo(self):
        """
        실행 취소 가능 여부 확인
        
        Returns:
            bool: 실행 취소 가능 여부
        """
        return len(self.actions) > 0
    
    def undo_last_action(self):
        """
        마지막 작업 취소 (삭제, 이동, 복사)
        
        Returns:
            tuple: (성공 여부, 복원된 파일 경로)
        """
        if not self.actions:
            self.viewer.show_message("No actions to undo")
            return False, None
        
        # 마지막 작업 가져오기
        last_action = self.actions.popleft()
        action_type = last_action.get('type')
        
        # 작업 유형에 따라 처리
        if action_type == self.ACTION_DELETE:
            return self._undo_deletion(last_action)
        elif action_type == self.ACTION_MOVE:
            return self._undo_move(last_action)
        elif action_type == self.ACTION_COPY:
            return self._undo_copy(last_action)
        else:
            self.viewer.show_message(f"Unknown action type: {action_type}")
            return False, None
    
    def undo_last_deletion(self):
        """
        마지막 삭제 작업 취소 (이전 버전과의 호환성을 위해 유지)
        
        Returns:
            tuple: (성공 여부, 복원된 파일 경로)
        """
        # 삭제 작업만 필터링
        delete_actions = [action for action in self.actions if action.get('type') == self.ACTION_DELETE]
        
        if not delete_actions:
            self.viewer.show_message("No delete actions to undo")
            return False, None
        
        # 첫 번째 삭제 작업 처리
        last_delete = delete_actions[0]
        
        # actions 큐에서 해당 작업 제거
        self.actions.remove(last_delete)
        
        return self._undo_deletion(last_delete)
    
    def _undo_deletion(self, delete_action):
        """
        삭제 작업 취소 내부 처리 메소드
        
        Args:
            delete_action: 삭제 작업 정보 딕셔너리
            
        Returns:
            tuple: (성공 여부, 복원된 파일 경로)
        """
        original_path = delete_action.get('path')
        original_index = delete_action.get('index', -1)
        
        # 삭제 취소가 가능한지 확인 (파일이 이미 존재하는지)
        if os.path.exists(original_path):
            self.viewer.show_message(f"File already exists at this location: {os.path.basename(original_path)}")
            # 더 이상 실행 취소할 항목이 없으면 상태 업데이트
            if not self.actions:
                self.undo_status_changed.emit(False)
            return False, None
        
        # 휴지통에서 원본 위치로 복원
        try:
            # 원본 디렉토리가 존재하는지 확인
            original_dir = os.path.dirname(original_path)
            if not os.path.exists(original_dir):
                os.makedirs(original_dir, exist_ok=True)
                
            # 파일 복원 시도
            self.viewer.show_message(f"Restoring file: {os.path.basename(original_path)}")
            
            # 실제 파일 복원 시도
            restored_file = self._restore_from_trash(original_path)
            
            # 파일 목록에 다시 추가
            list_updated = False
            if restored_file:
                # 실제 파일이 복원된 경우 파일 목록 업데이트
                list_updated = self._add_to_file_list(original_path, original_index)
            
            # 더 이상 실행 취소할 항목이 없으면 상태 업데이트
            if not self.actions:
                self.undo_status_changed.emit(False)
                
            if restored_file and list_updated:
                self.viewer.show_message(f"File restored successfully: {os.path.basename(original_path)}")
                return True, original_path
            elif restored_file:
                self.viewer.show_message(f"File restored but could not be added to the list: {os.path.basename(original_path)}")
                return True, original_path
            else:
                self.viewer.show_message(f"Failed to restore file: {os.path.basename(original_path)}")
                return False, None
                
        except Exception as e:
            self.viewer.show_message(f"File restoration failed: {str(e)}")
            return False, None
    
    def _undo_move(self, move_action):
        """
        이동 작업 취소 내부 처리 메소드
        
        Args:
            move_action: 이동 작업 정보 딕셔너리
            
        Returns:
            tuple: (성공 여부, 복원된 파일 경로)
        """
        original_path = move_action.get('original_path')
        new_path = move_action.get('new_path')
        original_index = move_action.get('index', -1)
        
        # 이동 취소가 가능한지 확인
        if not os.path.exists(new_path):
            self.viewer.show_message(f"Moved file does not exist: {os.path.basename(new_path)}")
            # 더 이상 실행 취소할 항목이 없으면 상태 업데이트
            if not self.actions:
                self.undo_status_changed.emit(False)
            return False, None
            
        if os.path.exists(original_path):
            self.viewer.show_message(f"File already exists at original location: {os.path.basename(original_path)}")
            if not self.actions:
                self.undo_status_changed.emit(False)
            return False, None
        
        try:
            # 원본 디렉토리가 존재하는지 확인
            original_dir = os.path.dirname(original_path)
            if not os.path.exists(original_dir):
                os.makedirs(original_dir, exist_ok=True)
                
            # 파일을 원래 위치로 다시 이동
            self.viewer.show_message(f"Moving file: {os.path.basename(new_path)} -> {os.path.basename(original_path)}")
            
            # 현재 열려있는 파일이라면 리소스 정리
            if hasattr(self.viewer, 'current_image_path') and self.viewer.current_image_path == new_path:
                if hasattr(self.viewer, 'file_operations') and hasattr(self.viewer.file_operations, '_cleanup_resources_for_file'):
                    self.viewer.file_operations._cleanup_resources_for_file(new_path)
            
            # 파일 이동
            shutil.move(new_path, original_path)
            
            # 파일 목록 업데이트
            list_updated = False
            
            # 파일 목록에 추가 (이동된 파일이 목록에서 제거되었을 것이므로)
            if os.path.exists(original_path):
                list_updated = self._add_to_file_list(original_path, original_index)
            
            # 더 이상 실행 취소할 항목이 없으면 상태 업데이트
            if not self.actions:
                self.undo_status_changed.emit(False)
                
            if list_updated:
                self.viewer.show_message(f"File restored to original location: {os.path.basename(original_path)}")
                return True, original_path
            else:
                self.viewer.show_message(f"File restored but could not be added to the list: {os.path.basename(original_path)}")
                return True, original_path
                
        except Exception as e:
            self.viewer.show_message(f"Failed to undo move operation: {str(e)}")
            return False, None
    
    def _undo_copy(self, copy_action):
        """
        복사 작업 취소 내부 처리 메소드
        
        Args:
            copy_action: 복사 작업 정보 딕셔너리
            
        Returns:
            tuple: (성공 여부, 복원된 파일 경로 - 복사 취소는 null 반환)
        """
        copied_path = copy_action.get('copied_path')
        original_path = copy_action.get('original_path') # 원래 이미지 경로도 가져옴 (네비게이션용)
        original_index = copy_action.get('index', -1) # 원래 인덱스도 가져옴

        # 복사된 파일이 존재하는지 확인
        if not os.path.exists(copied_path):
            self.viewer.show_message(f"Copied file not found, cannot undo: {os.path.basename(copied_path)}")
            # 더 이상 실행 취소할 항목이 없으면 상태 업데이트
            if not self.actions:
                self.undo_status_changed.emit(False)
            return False, None
        
        # 복사된 파일 삭제 시도
        try:
            # 파일 삭제 (휴지통으로 보내지 않음)
            os.remove(copied_path)
            self.viewer.show_message(f"Copy undone, file deleted: {os.path.basename(copied_path)}")
            
            # --- 추가: 복사 취소 후 이전 이미지로 이동 ---
            # 원래 파일이 여전히 존재하고, viewer에 show_previous_image 메서드가 있는지 확인
            if original_path and os.path.exists(original_path) and hasattr(self.viewer, 'show_previous_image'):
                 # 현재 표시되는 이미지가 (복사 작업 직후 넘어간) 다음 이미지일 가능성이 높으므로,
                 # show_previous_image를 호출하여 원래 복사했던 이미지로 돌아갑니다.
                 # show_previous_image는 내부적으로 index 등을 업데이트합니다.
                 QTimer.singleShot(0, self.viewer.show_previous_image) # UI 업데이트를 위해 singleShot 사용
            # --- 추가 끝 ---

            # 더 이상 실행 취소할 항목이 없으면 상태 업데이트
            if not self.actions:
                self.undo_status_changed.emit(False)
                
            return True, None # 복사 취소는 특정 경로를 복원하는 것이 아니므로 None 반환
                
        except Exception as e:
            self.viewer.show_message(f"Failed to delete copied file during undo: {str(e)}")
            # 실패 시 작업 큐에 다시 넣기 (선택 사항)
            # self.actions.appendleft(copy_action)
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
                self.viewer.show_message(f"Could not find {file_name} in the recycle bin")
                return False
                
            # 다른 OS 환경에서는 대체 방법 제공
            else:
                # 파일 목록에만 추가 (실제 파일은 복원하지 않음)
                self.viewer.show_message("Recycle bin restoration is limited on this operating system")
                return True
                
        except Exception as e:
            self.viewer.show_message(f"Failed to restore from recycle bin: {str(e)}")
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
            print(f"Failed to add file to list: {str(e)}")
            return False 