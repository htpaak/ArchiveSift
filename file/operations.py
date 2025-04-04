"""
파일 작업 모듈

이 모듈은 파일 작업(복사, 삭제, 이름 변경 등)을 수행하는 기능을 담당합니다.
"""

import os
import re
import shutil
import sys
import time
import gc
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtGui import QMovie

# 디버깅용 로깅 활성화 (프로덕션 환경에서는 False로 설정)
DEBUG = False

def log_debug(message):
    """디버그 메시지 로깅"""
    if DEBUG:
        print(f"[DEBUG] {message}")
        
def log_info(message):
    """정보 메시지 로깅"""
    print(f"[INFO] {message}")
    
def log_error(message):
    """오류 메시지 로깅"""
    print(f"[ERROR] {message}")

class FileOperations:
    """
    파일 작업 클래스
    
    이 클래스는 이미지 및 비디오 파일 작업(복사, 삭제, 이동 등)을 처리합니다.
    ArchiveSift 클래스와 협력하여 UI 표시 및 파일 내비게이터 업데이트를 수행합니다.
    """
    
    def __init__(self, viewer):
        """
        FileOperations 클래스를 초기화합니다.
        
        매개변수:
            viewer: ArchiveSift 인스턴스 (UI 표시 및 파일 내비게이터 제공)
        """
        self.viewer = viewer
    
    def copy_file_to_folder(self, file_path, folder_path):
        """
        Copies the file to the specified folder.
        파일을 지정된 폴더로 복사합니다.
        
        Parameters:
            file_path: the source file path to copy
            file_path: 복사할 파일 경로
            folder_path: the target folder path
            folder_path: 대상 폴더 경로
            
        Return value:
            A tuple containing a boolean indicating success and the copied file path (string)
            성공 여부(bool)와 복사된 파일 경로(string)를 포함하는 튜플
        """
        if not file_path or not folder_path:
            return False, None
            
        try:
            # Generate a unique file path
            # 고유한 파일 경로 생성
            target_path = self.get_unique_file_path(folder_path, file_path)
            
            # Copy the file (including metadata)
            # 파일 복사 (메타데이터 포함)
            shutil.copy2(file_path, target_path)
            
            # If the full path is too long, shorten the displayed path
            # 전체 경로가 너무 길 경우 표시용 경로 축약
            path_display = target_path
            if len(path_display) > 60:
                # Display only the drive and the last 2 folders
                # 드라이브와 마지막 2개 폴더만 표시
                drive, tail = os.path.splitdrive(path_display)
                parts = tail.split(os.sep)
                if len(parts) > 2:
                    # Drive + '...' + the last 2 folders
                    # 드라이브 + '...' + 마지막 2개 폴더
                    path_display = f"{drive}{os.sep}...{os.sep}{os.sep.join(parts[-2:])}"
            
            # 복사 작업 추적 (Undo 가능하도록)
            if hasattr(self.viewer, 'undo_manager'):
                self.viewer.undo_manager.track_copied_file(file_path, target_path, True)
            
            # Display message
            # 메시지 표시
            self.viewer.show_message(f"Copied file to {path_display}")
            
            return True, target_path
            
        except Exception as e:
            # Log error
            # 오류 발생 시 로그 출력
            error_msg = str(e)
            # Replace Korean error message with English equivalent if present
            if "[WinError 123]" in error_msg and "파일 이름, 디렉터리 이름 또는 볼륨 레이블 구문이 잘못되었습니다" in error_msg:
                error_msg = error_msg.replace("파일 이름, 디렉터리 이름 또는 볼륨 레이블 구문이 잘못되었습니다", 
                                             "The filename, directory name, or volume label syntax is incorrect")
            elif "[WinError 32]" in error_msg and "다른 프로세스가 파일을 사용 중이기 때문에 프로세스가 액세스 할 수 없습니다" in error_msg:
                error_msg = error_msg.replace("다른 프로세스가 파일을 사용 중이기 때문에 프로세스가 액세스 할 수 없습니다", 
                                             "The process cannot access the file because it is being used by another process")
            
            self.viewer.show_message(f"File copy failed: {error_msg}")
            return False, None
    
    def move_file_to_folder(self, file_path, folder_path):
        """
        Moves the file to the specified folder.
        파일을 지정된 폴더로 이동합니다.
        
        Parameters:
            file_path: the source file path to move
            file_path: 이동할 파일 경로
            folder_path: the target folder path
            folder_path: 대상 폴더 경로
            
        Return value:
            A tuple containing a boolean indicating success and the moved file path (string)
            성공 여부(bool)와 이동된 파일 경로(string)를 포함하는 튜플
        """
        if not file_path or not folder_path:
            return False, None
            
        try:
            # 디버그 로그만 출력 (DEBUG=True 일 때만 표시됨)
            log_debug(f"Moving file: {file_path} -> {folder_path}")
            
            # 현재 인덱스 백업
            current_index = -1
            if hasattr(self.viewer, 'current_index'):
                current_index = self.viewer.current_index
            
            # First, clean up any resources related to the file
            self._cleanup_resources_for_file(file_path)
            
            # Generate a unique file path
            target_path = self.get_unique_file_path(folder_path, file_path)
            
            # Move the file (shutil.move preserves metadata)
            shutil.move(file_path, target_path)
            
            # If the full path is too long, shorten the displayed path
            path_display = target_path
            if len(path_display) > 60:
                # Display only the drive and the last 2 folders
                drive, tail = os.path.splitdrive(path_display)
                parts = tail.split(os.sep)
                if len(parts) > 2:
                    # Drive + '...' + the last 2 folders
                    path_display = f"{drive}{os.sep}...{os.sep}{os.sep.join(parts[-2:])}"
            
            # 이동 작업 추적 (Undo 가능하도록)
            if hasattr(self.viewer, 'undo_manager'):
                self.viewer.undo_manager.track_moved_file(file_path, target_path, True)
            
            # Remove from bookmarks if exists
            if hasattr(self.viewer, 'bookmark_manager') and file_path in self.viewer.bookmark_manager.bookmarks:
                self.viewer.bookmark_manager.bookmarks.remove(file_path)
                self.viewer.bookmark_manager.save_bookmarks()
                if hasattr(self.viewer.bookmark_manager, 'update_bookmark_button_state'):
                    self.viewer.bookmark_manager.update_bookmark_button_state()
            
            # 파일 목록 및 인덱스 업데이트
            if hasattr(self.viewer, 'image_files') and file_path in self.viewer.image_files:
                self.viewer.image_files.remove(file_path)
                
                # 파일 네비게이터 업데이트
                if hasattr(self.viewer, 'file_navigator'):
                    self.viewer.file_navigator.set_files(self.viewer.image_files, current_index)
                
                # 파일 이동 후 다음 이미지 표시 로직
                if not self.viewer.image_files:
                    self.viewer.show_message("No more images in the folder")
                    # 모든 이미지가 사라졌을 때 UI 요소들 정리
                    if hasattr(self.viewer, 'image_label'):
                        self.viewer.image_label.clear()
                    if hasattr(self.viewer, 'current_image_path'):
                        self.viewer.current_image_path = ""
                    # 인덱스 표시창 숨기기
                    if hasattr(self.viewer, 'image_info_label') and self.viewer.image_info_label.isVisible():
                        self.viewer.image_info_label.hide()
                elif current_index >= len(self.viewer.image_files):
                    # 마지막 이미지를 이동한 경우, 새로운 마지막 이미지 표시
                    self.viewer.current_index = max(0, len(self.viewer.image_files) - 1)
                    if hasattr(self.viewer, 'state_manager'):
                        self.viewer.state_manager.set_state("current_index", self.viewer.current_index)
                    if self.viewer.image_files and hasattr(self.viewer, 'show_image'):
                        self.viewer.show_image(self.viewer.image_files[self.viewer.current_index])
                else:
                    # 동일한 인덱스 유지 (이제 다음 이미지를 가리킴)
                    if hasattr(self.viewer, 'show_image') and len(self.viewer.image_files) > current_index:
                        self.viewer.show_image(self.viewer.image_files[current_index])
            
            # Display message
            self.viewer.show_message(f"Moved file to {path_display}")
            
            return True, target_path
            
        except Exception as e:
            # Log error
            error_msg = str(e)
            # Replace Korean error message with English equivalent if present
            if "[WinError 123]" in error_msg and "파일 이름, 디렉터리 이름 또는 볼륨 레이블 구문이 잘못되었습니다" in error_msg:
                error_msg = error_msg.replace("파일 이름, 디렉터리 이름 또는 볼륨 레이블 구문이 잘못되었습니다", 
                                              "The filename, directory name, or volume label syntax is incorrect")
            elif "[WinError 32]" in error_msg and "다른 프로세스가 파일을 사용 중이기 때문에 프로세스가 액세스 할 수 없습니다" in error_msg:
                error_msg = error_msg.replace("다른 프로세스가 파일을 사용 중이기 때문에 프로세스가 액세스 할 수 없습니다", 
                                              "The process cannot access the file because it is being used by another process")
            
            log_error(f"File move failed: {error_msg}")
            self.viewer.show_message(f"File move failed: {error_msg}")
            return False, None
    
    def delete_file(self, file_path, confirm=True):
        """
        Deletes the file (moves to recycle bin).
        
        This method safely moves the file to the recycle bin. It includes special handling logic for GIF and animated files to resolve file handle issues.
        
        Parameters:
            file_path: the file path to delete
            confirm: whether to display a confirmation dialog before deletion
            
        Returns:
            A tuple containing a boolean indicating success and the next file path to display (string)
        """
        
        if not file_path:
            self.viewer.show_message("No image to delete")
            return False, None
            
        try:
            # Using Path object (Enhanced cross-platform compatibility)
            file_path_obj = Path(file_path).resolve()
            file_name = file_path_obj.name
            file_path_str = str(file_path_obj)
            
            log_debug(f"Path resolved: {file_path_obj}")
            
            # Check if file exists
            if not file_path_obj.is_file():
                self.viewer.show_message(f"File does not exist: {file_name}")
                log_error(f"File not found: {file_path_obj}")
                return False, None
                
            # Confirmation message before deletion
            if confirm:
                msg_box = QMessageBox(self.viewer)
                msg_box.setWindowTitle('File Deletion')
                msg_box.setText(f"Are you sure you want to move this file to the recycle bin?\n{file_name}")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                
                reply = msg_box.exec_()
                
                if reply != QMessageBox.Yes:
                    return False, None
            
            # 리소스 정리 - 중앙화된 메서드 사용
            self._cleanup_resources_for_file(file_path)
            
            # 파일 삭제 시도 (휴지통으로 이동만 지원)
            deleted = False
            next_file = None
            
            try:
                # Attempt to move to trash  // 휴지통으로 이동 시도 → 영어로 번역됨
                from send2trash import send2trash
                # Execute file deletion  // 파일 삭제 실행 → 영어로 번역됨
                send2trash(file_path_str)
                deleted = not os.path.exists(file_path_str)
            except Exception as e:
                # Just handle failure  // 그냥 실패 처리 → 영어로 번역됨
                deleted = False
                self.viewer.show_message("Cannot move file to trash")  
                # Process events  // 이벤트 처리 → 영어로 번역됨
                QApplication.processEvents()
                time.sleep(0.1)
            
            # Post-processing after successful deletion  // 삭제 성공 시 후처리 → 영어로 번역됨
            if deleted:
                # 삭제 작업 추적 (Undo 가능하도록)
                if hasattr(self.viewer, 'undo_manager'):
                    self.viewer.undo_manager.track_deleted_file(file_path_str, deleted)
                
                # Remove from bookmarks (if exists)  // 북마크에서 제거 (있는 경우) → 영어로 번역됨
                if hasattr(self.viewer, 'bookmark_manager') and file_path in self.viewer.bookmark_manager.bookmarks:
                    self.viewer.bookmark_manager.bookmarks.remove(file_path)
                    self.viewer.bookmark_manager.save_bookmarks()
                    if hasattr(self.viewer.bookmark_manager, 'update_bookmark_button_state'):
                        self.viewer.bookmark_manager.update_bookmark_button_state()
                
                # 파일 목록에서 해당 파일 제거 - 네비게이터가 처리하므로 여기서는 제거하지 않음
                # 중복 제거 문제를 방지하기 위해 주석 처리
                # if hasattr(self.viewer, 'image_files') and file_path in self.viewer.image_files:
                #     self.viewer.image_files.remove(file_path)
                #     
                #     # 파일이 모두 삭제되었는지 확인
                #     if not self.viewer.image_files:
                #         # 인덱스 표시창 숨기기
                #         if hasattr(self.viewer, 'image_info_label') and self.viewer.image_info_label.isVisible():
                #             self.viewer.image_info_label.hide()
                
                self.viewer.show_message("The file has been moved to trash")
            else:
                self.viewer.show_message("File deletion failed. It may be in use by another program.")  
                
            return deleted, next_file
                
        except Exception as e:
            error_msg = str(e)
            # Replace Korean error message with English equivalent if present
            if "[WinError 123]" in error_msg and "파일 이름, 디렉터리 이름 또는 볼륨 레이블 구문이 잘못되었습니다" in error_msg:
                error_msg = error_msg.replace("파일 이름, 디렉터리 이름 또는 볼륨 레이블 구문이 잘못되었습니다", 
                                             "The filename, directory name, or volume label syntax is incorrect")
            elif "[WinError 32]" in error_msg and "다른 프로세스가 파일을 사용 중이기 때문에 프로세스가 액세스 할 수 없습니다" in error_msg:
                error_msg = error_msg.replace("다른 프로세스가 파일을 사용 중이기 때문에 프로세스가 액세스 할 수 없습니다", 
                                             "The process cannot access the file because it is being used by another process")
            
            self.viewer.show_message(f"Error occurred during deletion: {error_msg}")
            return False, None
    
    def _cleanup_resources_for_file(self, file_path):
        """
        파일 삭제 또는 이동 전에 관련 리소스를 정리합니다.
        
        매개변수:
            file_path: 처리할 파일 경로
        """
        # 타이머 정지 (있는 경우)
        if hasattr(self.viewer, 'pause_all_timers'):
            self.viewer.pause_all_timers()
        
        # Special handling for explicit cleanup related to GIF/animation
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.gif', '.webp']:
            # 1. Stop and release the QMovie of the animation handler
            if hasattr(self.viewer, 'animation_handler'):
                if hasattr(self.viewer.animation_handler, 'stop_animation'):
                    self.viewer.animation_handler.stop_animation()
                
                # Clean up the QMovie object of the animation handler
                if hasattr(self.viewer.animation_handler, 'current_movie') and self.viewer.animation_handler.current_movie:
                    try:
                        movie = self.viewer.animation_handler.current_movie
                        movie.stop()
                        # Disconnect signal connections
                        try:
                            movie.frameChanged.disconnect()
                            movie.stateChanged.disconnect()
                            movie.finished.disconnect()
                        except:
                            pass
                        movie.setDevice(None)  # Disconnect from file
                        movie.deleteLater()
                        self.viewer.animation_handler.current_movie = None
                    except Exception as e:
                        pass
                        
            # 2. 이미지 레이블에서 QMovie 객체 제거
            if hasattr(self.viewer, 'image_label'):
                self.viewer.image_label.setMovie(None)
                self.viewer.image_label.clear()
            
            # 3. GIF 캐시에서 해당 파일 항목 제거
            file_path_str = str(Path(file_path).resolve())
            if hasattr(self.viewer, 'gif_cache') and self.viewer.gif_cache:
                for key in list(self.viewer.gif_cache.cache.keys()):
                    if isinstance(key, str) and file_path_str in key:
                        try:
                            item = self.viewer.gif_cache.cache[key]
                            if isinstance(item, QMovie):
                                item.stop()
                                item.setDevice(None)
                                try:
                                    item.finished.disconnect()
                                    item.frameChanged.disconnect()
                                except:
                                    pass
                                item.deleteLater()
                            del self.viewer.gif_cache.cache[key]
                        except Exception as e:
                            pass
        
        # 미디어 리소스 정리를 위해 ArchiveSift의 cleanup_current_media 메서드 사용
        if hasattr(self.viewer, 'cleanup_current_media'):
            self.viewer.cleanup_current_media()
        
        # 현재 이미지 경로 초기화
        if hasattr(self.viewer, 'current_image_path'):
            self.viewer.current_image_path = None
            
        # 완전한 정리를 위한 이벤트 처리와 가비지 컬렉션
        for _ in range(3):
            QApplication.processEvents()
            gc.collect()
            time.sleep(0.1)
        
        # 추가 딜레이 - 리소스가 완전히 정리될 시간 제공
        time.sleep(0.5)
    
    def get_unique_file_path(self, folder_path, file_path):
        """
        파일 이름이 중복되지 않는 고유한 파일 경로를 생성합니다.
        
        매개변수:
            folder_path: 대상 폴더 경로
            file_path: 원본 파일 경로
            
        반환값:
            고유한 파일 경로 문자열
        """
        # 파일 이름과 확장자 분리
        base_name = os.path.basename(file_path)
        name, ext = os.path.splitext(base_name)
        
        # 파일 이름에서 '(숫자)' 패턴 제거
        name = re.sub(r'\s?\(\d+\)', '', name)
        
        # 초기 대상 경로 생성
        target_path = os.path.join(folder_path, f"{name}{ext}")
        
        # 중복 확인 및 순차적 번호 부여
        counter = 1
        while os.path.exists(target_path):
            target_path = os.path.join(folder_path, f"{name} ({counter}){ext}")
            counter += 1
            
        return target_path
    
    def delete_current_image(self, confirm=True):
        """
        Deletes the current image and moves to the next image.
        현재 이미지를 삭제하고 다음 이미지로 이동합니다.
        
        Parameters:
            confirm (bool): Whether to display a confirmation dialog before deletion
            confirm (bool): 삭제 전 확인 대화상자 표시 여부
            
        Return Value:
            bool: Deletion success status
            bool: 삭제 성공 여부
        """
        # Get the current file
        # 현재 파일 가져오기
        if not hasattr(self.viewer, 'file_navigator') or not self.viewer.file_navigator:
            self.viewer.show_message("File navigator is not initialized")
            # 파일 네비게이터가 초기화되지 않았습니다 -> File navigator is not initialized
            return False
            
        current_file = self.viewer.file_navigator.get_current_file()
        if not current_file:
            self.viewer.show_message("No image available for deletion")
            # 삭제할 이미지가 없습니다 -> No image available for deletion
            return False
        
        try:
            # Get the next file information before deletion (if needed)
            # 삭제 전에 미리 다음 파일 정보 가져오기 (필요한 경우)
            next_file = None
            if hasattr(self.viewer, 'image_files') and len(self.viewer.image_files) > 1:
                _, next_file = self.viewer.file_navigator.peek_next_file()
                
            # Attempt to delete the file
            # 파일 삭제 시도
            success, _ = self.delete_file(current_file, confirm=confirm)
            
            if not success:
                return False
                
            # Remove the file from the navigator
            # 내비게이터에서 파일 제거
            nav_success, next_file_after_deletion = self.viewer.file_navigator.delete_current_file()
            
            if not nav_success:
                self.viewer.show_message("Failed to update file list")
                # 파일 목록 업데이트 실패 -> Failed to update file list
                return False
                
            # Update current index and file list
            # 현재 인덱스와 파일 목록 업데이트
            self.viewer.current_index = self.viewer.file_navigator.get_current_index()
            self.viewer.image_files = self.viewer.file_navigator.get_files()
            
            # Check if any images remain
            # 이미지가 남아있는지 확인
            if not self.viewer.image_files:
                # No images left to display
                # 더 이상 표시할 이미지가 없음
                self.viewer.image_label.clear()
                self.viewer.current_image_path = ""
                # 인덱스 표시창 숨기기
                if hasattr(self.viewer, 'image_info_label') and self.viewer.image_info_label.isVisible():
                    self.viewer.image_info_label.hide()
                self.viewer.show_message("All images have been deleted")
                # 모든 이미지가 삭제되었습니다 -> All images have been deleted
                return True
                
            # Display the next image if available
            # 새로운 다음 파일 있으면 표시
            if next_file_after_deletion:
                self.viewer.show_image(next_file_after_deletion)
            else:
                # If no next file, display the file at the current index
                # 다음 파일이 없으면 현재 인덱스의 파일 표시
                current_file = self.viewer.file_navigator.get_current_file()
                if current_file:
                    self.viewer.show_image(current_file)
                else:
                    # If no file exists, display only a message
                    # 파일이 없으면 메시지만 표시
                    self.viewer.image_label.clear()
                    self.viewer.current_image_path = ""
            
            return True
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.viewer.show_message(f"Image deletion failed: {str(e)}")
            # 이미지 삭제 중 오류 발생 -> Image deletion failed
            return False 