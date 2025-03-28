"""
UI 상태 관리 모듈

이 모듈은 UI 요소의 표시 상태를 관리하는 UIStateManager 클래스를 정의합니다.
"""

from PyQt5.QtCore import QObject, pyqtSignal

class UIStateManager(QObject):
    """
    UI 상태 관리 클래스
    
    이 클래스는 UI 요소(타이틀바, 컨트롤바 등)의 표시 상태를 관리합니다.
    """
    
    # 상태 변경 신호
    fullscreen_changed = pyqtSignal(bool)
    ui_visibility_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """
        UIStateManager 초기화
        
        Args:
            parent: 부모 객체 (ArchiveSift 인스턴스)
        """
        super().__init__(parent)
        self.parent = parent
        
        # UI 요소 상태
        self._fullscreen = False
        self._ui_visibility = {
            'title_bar': True,
            'controls': True,
            'sliders': True,
            'info_label': False
        }
    
    @property
    def is_fullscreen(self):
        """전체화면 상태 반환"""
        return self._fullscreen
    
    @is_fullscreen.setter
    def is_fullscreen(self, value):
        """전체화면 상태 설정"""
        if self._fullscreen != value:
            self._fullscreen = value
            self.fullscreen_changed.emit(value)
    
    def update_fullscreen_state(self, is_fullscreen):
        """
        전체화면 상태 업데이트
        
        Args:
            is_fullscreen: 전체화면 여부
        """
        self.is_fullscreen = is_fullscreen
        
        # UI 잠금 상태에 따라 UI 요소 표시 여부 결정
        if not is_fullscreen:
            # 일반 모드로 전환 시 UI 잠금 상태에 따라 UI 결정
            title_locked = self._get_title_locked()
            bottom_locked = self._get_bottom_locked()
            
            self._update_ui_visibility({
                'title_bar': title_locked,
                'controls': bottom_locked,
                'sliders': bottom_locked
            })
        else:
            # 전체화면 모드로 전환 시 UI 잠금 상태에 따라 UI 결정
            title_locked = self._get_title_locked()
            bottom_locked = self._get_bottom_locked()
            
            self._update_ui_visibility({
                'title_bar': title_locked,
                'controls': bottom_locked,
                'sliders': bottom_locked
            })
    
    def _get_title_locked(self):
        """타이틀바 잠금 상태 반환"""
        # ui_lock_manager가 있으면 그것을 사용
        if hasattr(self.parent, 'ui_lock_manager'):
            return self.parent.ui_lock_manager.title_locked
        # 이전 코드와의 호환성을 위해 is_title_ui_locked도 확인
        elif hasattr(self.parent, 'is_title_ui_locked'):
            return self.parent.is_title_ui_locked
        return True  # 기본값
    
    def _get_bottom_locked(self):
        """하단 UI 잠금 상태 반환"""
        # ui_lock_manager가 있으면 그것을 사용
        if hasattr(self.parent, 'ui_lock_manager'):
            return self.parent.ui_lock_manager.ui_locked
        # 이전 코드와의 호환성을 위해 is_bottom_ui_locked도 확인
        elif hasattr(self.parent, 'is_bottom_ui_locked'):
            return self.parent.is_bottom_ui_locked
        return True  # 기본값
    
    def _update_ui_visibility(self, visibility_dict):
        """
        Update UI element visibility
        
        Args:
            visibility_dict: A dictionary containing the visibility of each UI element.
                             None values maintain the current state.
        """
        # Update state using the provided values (only if not None)
        updated = False
        for key, value in visibility_dict.items():
            if key in self._ui_visibility and value is not None:
                if self._ui_visibility[key] != value:
                    self._ui_visibility[key] = value
                    updated = True
        
        # Emit signal only if changes occur
        if updated:
            self.ui_visibility_changed.emit(self._ui_visibility)
            return True
        return False
    
    # UIStateManager class method modification
    def show_ui_temporarily(self):
        """Temporarily display the UI based on mouse movement"""
        # Store current state
        old_visibility = self._ui_visibility.copy()
        
        # Update UI element visibility
        new_visibility = {
            'title_bar': True,
            'controls': True,
            'sliders': True
        }
        
        # Check if there are any changes
        has_changes = False
        for key, value in new_visibility.items():
            if key in old_visibility and old_visibility[key] != value:
                has_changes = True
                break
        
        # Update only if changes exist
        if has_changes:
            self._update_ui_visibility(new_visibility)
            return True
        return False
    
    def hide_ui_conditionally(self):
        """Determine UI visibility based on UI lock status"""
        title_locked = self._get_title_locked()
        bottom_locked = self._get_bottom_locked()
        
        # Store current state
        old_visibility = self._ui_visibility.copy()
        
        # Calculate new UI state
        new_visibility = {
            'title_bar': title_locked,
            'controls': bottom_locked,
            'sliders': bottom_locked
        }
        
        # Check if there are any changes - improved previous logic
        has_changes = False
        changed_keys = []
        for key, value in new_visibility.items():
            if key in old_visibility and old_visibility[key] != value:
                has_changes = True
                changed_keys.append(key)
        
        # Update only if changes exist
        if has_changes:
            self._update_ui_visibility(new_visibility)
            return True
        return False
    
    def update_ui_for_media_type(self, media_type):
        """
        미디어 타입에 따라 UI 업데이트
        
        Args:
            media_type: 미디어 타입 ('image', 'video', 'animation' 등)
        """
        # 비디오나 애니메이션인 경우 슬라이더 표시
        sliders_visible = media_type in ['video', 'gif_animation', 'webp_animation']
        
        self._update_ui_visibility({
            'sliders': sliders_visible and self._get_bottom_locked()
        })
        
    def apply_ui_visibility(self):
        """UI 가시성 설정을 실제 UI 요소에 적용"""
        # 타이틀바 가시성 설정
        if hasattr(self.parent, 'title_bar'):
            if self._ui_visibility['title_bar']:
                self.parent.title_bar.show()
            else:
                self.parent.title_bar.hide()
        
        # 컨트롤 버튼 가시성 설정
        if hasattr(self.parent, 'buttons'):
            for row in self.parent.buttons:
                for button in row:
                    if self._ui_visibility['controls']:
                        button.show()
                    else:
                        button.hide()
        
        # 슬라이더 가시성 설정
        if hasattr(self.parent, 'slider_widget'):
            if self._ui_visibility['sliders']:
                self.parent.slider_widget.show()
            else:
                self.parent.slider_widget.hide()
        
        # 정보 레이블 가시성 설정
        if hasattr(self.parent, 'image_info_label'):
            if self._ui_visibility['info_label']:
                self.parent.image_info_label.show()
                self.parent.image_info_label.raise_()
            else:
                self.parent.image_info_label.hide()
                
    def get_ui_visibility(self, component_name):
        """
        UI 요소의 현재 가시성 상태를 반환합니다.
        
        Args:
            component_name (str): UI 요소 이름 ('title_bar', 'controls', 'sliders', 'info_label')
            
        Returns:
            bool: UI 요소 가시성 상태
        """
        if component_name in self._ui_visibility:
            return self._ui_visibility[component_name]
        return True  # 기본값: 표시 