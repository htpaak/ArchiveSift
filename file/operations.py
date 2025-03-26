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
        파일을 지정된 폴더로 복사합니다.
        
        매개변수:
            file_path: 복사할 파일 경로
            folder_path: 대상 폴더 경로
            
        반환값:
            성공 여부(bool)와 복사된 파일 경로(string)
        """
        if not file_path or not folder_path:
            return False, None
            
        try:
            # 고유한 파일 경로 생성
            target_path = self.get_unique_file_path(folder_path, file_path)
            
            # 파일 복사 (메타데이터 포함)
            shutil.copy2(file_path, target_path)
            
            # 전체 경로가 너무 길 경우 표시용 경로 축약
            path_display = target_path
            if len(path_display) > 60:
                # 드라이브와 마지막 2개 폴더만 표시
                drive, tail = os.path.splitdrive(path_display)
                parts = tail.split(os.sep)
                if len(parts) > 2:
                    # 드라이브 + '...' + 마지막 2개 폴더
                    path_display = f"{drive}{os.sep}...{os.sep}{os.sep.join(parts[-2:])}"
            
            # 메시지 표시
            self.viewer.show_message(f"{path_display} 으로 파일 복사")
            
            return True, target_path
            
        except Exception as e:
            # 오류 발생 시 로그 출력
            print(f"파일 복사 중 오류 발생: {e}")
            self.viewer.show_message(f"파일 복사 실패: {str(e)}")
            return False, None
    
    def delete_file(self, file_path, confirm=True):
        """
        파일을 삭제합니다 (휴지통으로 이동).
        
        이 메서드는 파일을 안전하게 휴지통으로 이동합니다. 특히 GIF 및 애니메이션 파일에 대한
        특별 처리 로직을 포함하여 파일 핸들 관련 문제를 해결합니다.
        
        매개변수:
            file_path: 삭제할 파일 경로
            confirm: 삭제 전 확인 대화상자 표시 여부
            
        반환값:
            성공 여부(bool)와 다음 표시할 파일 경로(string)
        """
        log_info(f"삭제 시도: {file_path}")
        
        if not file_path:
            self.viewer.show_message("삭제할 이미지가 없습니다")
            return False, None
            
        try:
            # Path 객체 사용 (크로스 플랫폼 호환성 향상)
            file_path_obj = Path(file_path).resolve()
            file_name = file_path_obj.name
            file_path_str = str(file_path_obj)
            
            log_debug(f"경로 해석: {file_path_obj}")
            
            # 파일이 존재하는지 확인
            if not file_path_obj.is_file():
                self.viewer.show_message(f"파일이 존재하지 않습니다: {file_name}")
                log_error(f"파일 없음: {file_path_obj}")
                return False, None
                
            # 삭제 전 확인 메시지
            if confirm:
                msg_box = QMessageBox(self.viewer)
                msg_box.setWindowTitle('파일 삭제')
                msg_box.setText(f"정말로 파일을 휴지통으로 이동하시겠습니까?\n{file_name}")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                
                reply = msg_box.exec_()
                print(f"사용자 응답: {reply == QMessageBox.Yes}")  # 디버깅 로그
                
                if reply != QMessageBox.Yes:
                    return False, None
            
            print(f"파일 삭제 시작: {file_path_str}")
            
            # 타이머 정지 (있는 경우)
            if hasattr(self.viewer, 'pause_all_timers'):
                self.viewer.pause_all_timers()
            
            # GIF/애니메이션 관련 명시적 정리를 위한 특별 처리
            file_ext = os.path.splitext(file_path_str)[1].lower()
            if file_ext in ['.gif', '.webp']:
                print(f"GIF/애니메이션 파일 특별 정리 시작: {file_ext}")
                
                # 1. 애니메이션 핸들러의 QMovie 중지 및 해제
                if hasattr(self.viewer, 'animation_handler'):
                    print("애니메이션 핸들러 특별 정리...")
                    if hasattr(self.viewer.animation_handler, 'stop_animation'):
                        self.viewer.animation_handler.stop_animation()
                    
                    # 애니메이션 핸들러의 QMovie 객체 정리
                    if hasattr(self.viewer.animation_handler, 'current_movie') and self.viewer.animation_handler.current_movie:
                        print("현재 QMovie 객체 정리...")
                        try:
                            movie = self.viewer.animation_handler.current_movie
                            movie.stop()
                            # 시그널 연결 해제
                            try:
                                movie.frameChanged.disconnect()
                                movie.stateChanged.disconnect()
                                movie.finished.disconnect()
                            except:
                                pass
                            movie.setDevice(None)  # 파일에서 연결 해제
                            movie.deleteLater()
                            self.viewer.animation_handler.current_movie = None
                        except Exception as e:
                            print(f"QMovie 객체 정리 오류: {e}")
                            
                # 2. 이미지 레이블에서 QMovie 객체 제거
                if hasattr(self.viewer, 'image_label'):
                    print("이미지 레이블에서 QMovie 연결 해제...")
                    self.viewer.image_label.setMovie(None)
                    self.viewer.image_label.clear()
                
                # 3. GIF 캐시에서 해당 파일 항목 제거
                if hasattr(self.viewer, 'gif_cache') and self.viewer.gif_cache:
                    print("GIF 캐시에서 항목 제거...")
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
                                print(f"GIF 캐시에서 항목 제거 완료: {key}")
                                del self.viewer.gif_cache.cache[key]
                            except Exception as e:
                                print(f"GIF 캐시 항목 제거 오류: {key} - {e}")
            
            # 완전한 정리를 위한 이벤트 처리와 가비지 컬렉션
            for _ in range(3):
                QApplication.processEvents()
                gc.collect()
                time.sleep(0.1)
            
            # 파일 삭제 시도 (휴지통으로 이동만 지원)
            deleted = False
            next_file = None
            
            try:
                # 휴지통으로 이동 시도
                from send2trash import send2trash
                log_info(f"send2trash로 휴지통 이동 시도: {file_path_str}")
                
                # 파일 삭제 실행
                send2trash(file_path_str)
                deleted = not os.path.exists(file_path_str)
                
                log_info(f"휴지통 이동 결과: {'성공' if deleted else '실패'}")
            except Exception as e:
                log_error(f"휴지통 이동 실패: {e}")
                # 그냥 실패 처리
                deleted = False
                self.viewer.show_message("파일을 휴지통으로 이동할 수 없습니다")
                # 이벤트 처리
                QApplication.processEvents()
                time.sleep(0.1)
            
            # 삭제 성공 시 후처리
            if deleted:
                log_info("파일이 성공적으로 삭제되었습니다")
                
                # 북마크에서 제거 (있는 경우)
                if hasattr(self.viewer, 'bookmark_manager') and file_path in self.viewer.bookmark_manager.bookmarks:
                    self.viewer.bookmark_manager.bookmarks.discard(file_path)
                    self.viewer.bookmark_manager.save_bookmarks()
                    if hasattr(self.viewer.bookmark_manager, 'update_bookmark_button_state'):
                        self.viewer.bookmark_manager.update_bookmark_button_state()
                
                self.viewer.show_message("파일이 휴지통으로 이동되었습니다")
            else:
                self.viewer.show_message("파일 삭제에 실패했습니다. 다른 프로그램에서 사용 중일 수 있습니다.")
                
            return deleted, next_file
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"삭제 중 예외 발생: {e}\n{error_details}")
            self.viewer.show_message(f"삭제 중 오류 발생: {str(e)}")
            return False, None
    
    def _cleanup_resources_for_file(self, file_path):
        """
        파일 삭제 전에 관련 리소스를 정리합니다.
        
        매개변수:
            file_path: 삭제할 파일 경로
        """
        # 미디어 리소스 정리를 위해 ArchiveSift의 cleanup_current_media 메서드 사용
        if hasattr(self.viewer, 'cleanup_current_media'):
            self.viewer.cleanup_current_media()
        
        # 현재 이미지 경로 초기화
        if hasattr(self.viewer, 'current_image_path'):
            self.viewer.current_image_path = None
            
        # 여기서 Qt 이벤트 처리를 해줘서 리소스 해제가 실제로 일어나도록 함
        QApplication.processEvents()
        
        # 약간의 딜레이 추가 (리소스가 완전히 정리될 시간 제공)
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
        현재 이미지를 삭제하고 다음 이미지로 이동합니다.
        
        매개변수:
            confirm (bool): 삭제 전 확인 대화상자 표시 여부
            
        반환값:
            bool: 삭제 성공 여부
        """
        # 현재 파일 가져오기
        if not hasattr(self.viewer, 'file_navigator') or not self.viewer.file_navigator:
            self.viewer.show_message("파일 네비게이터가 초기화되지 않았습니다")
            return False
            
        current_file = self.viewer.file_navigator.get_current_file()
        if not current_file:
            self.viewer.show_message("삭제할 이미지가 없습니다")
            return False
        
        try:
            # 삭제 전에 미리 다음 파일 정보 가져오기 (필요한 경우)
            next_file = None
            if hasattr(self.viewer, 'image_files') and len(self.viewer.image_files) > 1:
                _, next_file = self.viewer.file_navigator.peek_next_file()
                
            # 파일 삭제 시도
            success, _ = self.delete_file(current_file, confirm=confirm)
            
            if not success:
                return False
                
            # 내비게이터에서 파일 제거
            nav_success, next_file_after_deletion = self.viewer.file_navigator.delete_current_file()
            
            if not nav_success:
                self.viewer.show_message("파일 목록 업데이트 실패")
                return False
                
            # 현재 인덱스와 파일 목록 업데이트
            self.viewer.current_index = self.viewer.file_navigator.get_current_index()
            self.viewer.image_files = self.viewer.file_navigator.get_files()
            
            # 이미지가 남아있는지 확인
            if not self.viewer.image_files:
                # 더 이상 표시할 이미지가 없음
                self.viewer.image_label.clear()
                self.viewer.current_image_path = ""
                self.viewer.show_message("모든 이미지가 삭제되었습니다")
                return True
                
            # 새로운 다음 파일 있으면 표시
            if next_file_after_deletion:
                print(f"삭제 후 다음 이미지로 이동: {next_file_after_deletion}")
                self.viewer.show_image(next_file_after_deletion)
            else:
                # 다음 파일이 없으면 현재 인덱스의 파일 표시
                current_file = self.viewer.file_navigator.get_current_file()
                if current_file:
                    print(f"현재 인덱스의 파일 표시: {current_file}")
                    self.viewer.show_image(current_file)
                else:
                    # 파일이 없으면 메시지만 표시
                    self.viewer.image_label.clear()
                    self.viewer.current_image_path = ""
            
            return True
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"이미지 삭제 중 오류 발생: {e}\n{error_details}")
            self.viewer.show_message(f"이미지 삭제 실패: {str(e)}")
            return False 