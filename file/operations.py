"""
파일 작업 모듈

이 모듈은 파일 작업(복사, 삭제, 이름 변경 등)을 수행하는 기능을 담당합니다.
"""

import os
import re
import shutil
import sys
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer


class FileOperations:
    """
    파일 작업 클래스
    
    이 클래스는 이미지 및 비디오 파일 작업(복사, 삭제, 이동 등)을 처리합니다.
    ImageViewer 클래스와 협력하여 UI 표시 및 파일 내비게이터 업데이트를 수행합니다.
    """
    
    def __init__(self, viewer):
        """
        FileOperations 클래스를 초기화합니다.
        
        매개변수:
            viewer: ImageViewer 인스턴스 (UI 표시 및 파일 내비게이터 제공)
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
        
        매개변수:
            file_path: 삭제할 파일 경로
            confirm: 삭제 전 확인 대화상자 표시 여부
            
        반환값:
            성공 여부(bool)
        """
        print(f"삭제 시도: {file_path}")  # 디버깅 로그
        
        if not file_path:
            self.viewer.show_message("삭제할 파일이 없습니다")
            return False
            
        try:
            # Path 객체 사용 (크로스 플랫폼 호환성 향상)
            file_path_obj = Path(file_path).resolve()
            print(f"경로 해석: {file_path_obj}")  # 디버깅 로그
            
            # 파일이 존재하는지 확인
            if not file_path_obj.is_file():
                self.viewer.show_message(f"파일이 존재하지 않습니다: {file_path_obj.name}")
                print(f"파일 없음: {file_path_obj}")  # 디버깅 로그
                return False
                
            # 삭제 전 확인 메시지
            if confirm:
                msg_box = QMessageBox(self.viewer)
                msg_box.setWindowTitle('파일 삭제')
                msg_box.setText(f"정말로 파일을 삭제하시겠습니까?\n{file_path_obj.name}")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.No)
                
                reply = msg_box.exec_()
                print(f"사용자 응답: {reply == QMessageBox.Yes}")  # 디버깅 로그
                
                if reply != QMessageBox.Yes:
                    return False
            
            # send2trash 모듈 사용해서 휴지통으로 이동
            try:
                # 먼저 send2trash 모듈이 있는지 확인
                try:
                    from send2trash import send2trash
                    print(f"send2trash 모듈 로드 성공")  # 디버깅 로그
                except ImportError:
                    # 자동으로 설치 시도
                    self.viewer.show_message("send2trash 모듈 설치 중...")
                    import subprocess
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "send2trash"])
                    from send2trash import send2trash
                    print(f"send2trash 모듈 설치 및 로드 성공")  # 디버깅 로그
                
                # 현재 파일이 사용 중인지 확인
                if file_path == self.viewer.current_image_path:
                    # 파일 핸들이 열려있는 상태이므로 cleanup 후 약간 대기
                    self.viewer.cleanup_current_media()
                    # Qt 이벤트 처리를 통해 리소스 해제 적용
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()
                    # 약간의 지연
                    import time
                    time.sleep(0.3)
                
                # Windows에서는 파일 사용 중인 경우 삭제 실패할 수 있음
                # 대안으로 os.remove 시도
                try:
                    # 휴지통으로 이동 시도
                    send2trash(str(file_path_obj))
                    print(f"send2trash 성공")  # 디버깅 로그
                except Exception as e:
                    print(f"send2trash 실패: {e}, 직접 삭제 시도")
                    # 직접 삭제 시도
                    import os
                    os.remove(str(file_path_obj))
                    print(f"os.remove 성공")
                
                # 북마크에서 제거 (BookmarkManager를 통해 처리)
                if hasattr(self.viewer, 'bookmark_manager') and file_path in self.viewer.bookmark_manager.bookmarks:
                    self.viewer.bookmark_manager.bookmarks.discard(file_path)
                    self.viewer.bookmark_manager.save_bookmarks()
                    self.viewer.bookmark_manager.update_bookmark_button_state()
                
                self.viewer.show_message("파일이 휴지통으로 이동되었습니다")
                return True
                
            except Exception as e:
                # 오류 시 상세 로그 출력
                import traceback
                error_details = traceback.format_exc()
                print(f"휴지통 이동 중 오류: {e}\n{error_details}")
                self.viewer.show_message(f"휴지통 이동 실패: {str(e)}")
                return False
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"삭제 중 예외 발생: {e}\n{error_details}")
            self.viewer.show_message(f"삭제 중 오류 발생: {str(e)}")
            return False
    
    def _cleanup_resources_for_file(self, file_path):
        """
        파일 삭제 전에 관련 리소스를 정리합니다.
        
        매개변수:
            file_path: 삭제할 파일 경로
        """
        # 미디어 리소스 정리를 위해 ImageViewer의 cleanup_current_media 메서드 사용
        if hasattr(self.viewer, 'cleanup_current_media'):
            self.viewer.cleanup_current_media()
        
        # 현재 이미지 경로 초기화
        if hasattr(self.viewer, 'current_image_path'):
            self.viewer.current_image_path = None
            
        # 여기서 Qt 이벤트 처리를 해줘서 리소스 해제가 실제로 일어나도록 함
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        # 약간의 딜레이 추가 (리소스가 완전히 정리될 시간 제공)
        import time
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