"""
버튼 이벤트 핸들러 모듈

이 모듈은 버튼 클릭 이벤트를 처리하기 위한 핸들러 클래스를 제공합니다.
특히 DualActionButton과 같은 복합 기능 버튼의 이벤트 처리를 담당합니다.
"""

from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtWidgets import QApplication

class ButtonEventHandler(QObject):
    """
    버튼 이벤트 핸들러 클래스
    
    DualActionButton 등 복합 기능 버튼의 이벤트를 처리합니다.
    버튼의 왼쪽/오른쪽 영역 클릭에 따라 다른 동작을 수행합니다.
    """
    
    def __init__(self, parent):
        """
        ButtonEventHandler 초기화
        
        Args:
            parent: 부모 객체 (ArchiveSift 인스턴스)
        """
        super().__init__(parent)
        self.parent = parent  # 메인 애플리케이션 참조 저장
    
    def handle_button_click(self, button):
        """
        버튼 클릭 이벤트 처리
        
        클릭된 버튼의 종류와 클릭 위치에 따라 적절한 동작을 수행합니다.
        
        Args:
            button: 클릭된 버튼 객체
        """
        # 툴팁(또는 folder_path 속성)에서 폴더 경로 가져오기
        folder_path = self._get_folder_path(button)
        if not folder_path:
            return
            
        # 커서를 일반 모양으로 복원
        QApplication.restoreOverrideCursor()
        
        # DualActionButton인 경우 클릭 위치에 따라 다른 동작 수행
        if hasattr(button, 'last_click_region'):
            if button.last_click_region == 'left':
                # 왼쪽 클릭 - 복사
                self._copy_to_folder(folder_path)
            elif button.last_click_region == 'right':
                # 오른쪽 클릭 - 이동
                self._move_to_folder(folder_path)
        else:
            # 기존 버튼 호환성 - 기본 동작은 복사
            self._copy_to_folder(folder_path)
        
        # 버튼 클릭 후 약간의 지연을 두고 창에 포커스를 돌려줌
        self._restore_focus()
    
    def _get_folder_path(self, button):
        """
        버튼에서 폴더 경로 정보 추출
        
        Args:
            button: 버튼 객체
            
        Returns:
            str: 폴더 경로 (경로가 없으면 None)
        """
        # folder_path 속성이 있는 경우 (DualActionButton)
        if hasattr(button, 'folder_path') and button.folder_path:
            return button.folder_path
            
        # 툴팁에서 경로 가져오기 (기존 버튼과의 호환성)
        tooltip = button.toolTip()
        if tooltip:
            # 툴팁에 "Copy: " 또는 "Move: " 접두사가 있는 경우 제거
            if tooltip.startswith("Copy: "):
                return tooltip[6:]
            elif tooltip.startswith("Move: "):
                return tooltip[6:]
            return tooltip
            
        return None
    
    def _copy_to_folder(self, folder_path):
        """
        현재 이미지를 지정된 폴더로 복사
        
        Args:
            folder_path: 대상 폴더 경로
        """
        print(f"Copy to folder: {folder_path}")
        if hasattr(self.parent, 'copy_image_to_folder'):
            self.parent.copy_image_to_folder(folder_path)
    
    def _move_to_folder(self, folder_path):
        """
        현재 이미지를 지정된 폴더로 이동
        
        Args:
            folder_path: 대상 폴더 경로
        """
        print(f"Move to folder: {folder_path}")
        if hasattr(self.parent, 'move_image_to_folder'):
            self.parent.move_image_to_folder(folder_path)
    
    def _restore_focus(self):
        """
        동작 완료 후 메인 창에 포커스 복원
        """
        if hasattr(self.parent, 'create_single_shot_timer') and hasattr(self.parent, 'setFocus'):
            self.parent.create_single_shot_timer(50, self.parent.setFocus)
        else:
            # create_single_shot_timer가 없는 경우 QTimer 직접 사용
            QTimer.singleShot(50, lambda: self.parent.setFocus() if hasattr(self.parent, 'setFocus') else None) 