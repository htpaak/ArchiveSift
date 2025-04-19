"""
UI 상태 관리 모듈

이 모듈은 UI 요소의 표시 상태를 관리하는 UIStateManager 클래스를 정의합니다.
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout

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
            'bottom_ui': True,  # 기존 'controls'와 'sliders'를 'bottom_ui'로 통합
            'info_label': False
        }
        
        # 이전 코드와의 호환성을 위해 내부적으로 추적
        # 기본값을 True로 설정하여 초기 상태에서도 슬라이더 표시
        self._media_has_slider = True
    
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
                'bottom_ui': bottom_locked
            })
        else:
            # 전체화면 모드로 전환 시 UI 잠금 상태에 따라 UI 결정
            title_locked = self._get_title_locked()
            bottom_locked = self._get_bottom_locked()
            
            self._update_ui_visibility({
                'title_bar': title_locked,
                'bottom_ui': bottom_locked
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
            'bottom_ui': True
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
            'bottom_ui': bottom_locked
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
        # 비디오나 애니메이션인 경우를 내부적으로 기록 (슬라이더 표시 결정용)
        slider_needed = media_type in ['video', 'gif_animation', 'webp_animation']
        
        # 슬라이더 상태가 변경된 경우에만 UI 업데이트
        if self._media_has_slider != slider_needed:
            self._media_has_slider = slider_needed
            # 슬라이더 상태 변경 후 즉시 UI에 적용
            self.apply_ui_visibility()
    
    def apply_ui_visibility(self):
        """UI 가시성 설정을 실제 UI 요소에 적용"""
        # 실제 변경 여부 추적
        has_changed = False
        
        # 타이틀바 가시성 설정
        if hasattr(self.parent, 'title_bar'):
            title_visible = self._ui_visibility['title_bar']
            if (title_visible and self.parent.title_bar.isHidden()) or \
               (not title_visible and not self.parent.title_bar.isHidden()):
                has_changed = True
                if title_visible:
                    self.parent.title_bar.show()
                else:
                    self.parent.title_bar.hide()
        
        # 하단 UI 가시성 설정 (통합 관리)
        bottom_visible = self._ui_visibility['bottom_ui']
        
        # 슬라이더 위젯 가시성 설정
        if hasattr(self.parent, 'slider_widget'):
            slider_target_visible = bottom_visible and self._media_has_slider
            if (slider_target_visible and self.parent.slider_widget.isHidden()) or \
               (not slider_target_visible and not self.parent.slider_widget.isHidden()):
                has_changed = True
                if slider_target_visible:
                    self.parent.slider_widget.show()
                else:
                    self.parent.slider_widget.hide()
        
        # 버튼 컨테이너 가시성 설정
        if hasattr(self.parent, 'button_container'):
            button_target_visible = bottom_visible
            if (button_target_visible and self.parent.button_container.isHidden()) or \
               (not button_target_visible and not self.parent.button_container.isHidden()):
                has_changed = True
                if button_target_visible:
                    self.parent.button_container.show()
                else:
                    self.parent.button_container.hide()
        
        # 정보 레이블 가시성 설정
        if hasattr(self.parent, 'image_info_label'):
            info_visible = self._ui_visibility['info_label']
            if (info_visible and self.parent.image_info_label.isHidden()) or \
               (not info_visible and not self.parent.image_info_label.isHidden()):
                has_changed = True
                if info_visible:
                    self.parent.image_info_label.show()
                    self.parent.image_info_label.raise_()
                else:
                    self.parent.image_info_label.hide()
        
        # UI 가시성이 실제로 변경된 경우에만 레이아웃 비율 업데이트
        if has_changed:
            self.update_layout_ratios()
    
    def update_layout_ratios(self):
        """UI 요소 가시성에 따라 레이아웃 비율 동적 조정"""
        # 부모 객체 확인
        if not self.parent:
            return
            
        # UI 잠금 상태 확인 - 둘 다 잠겨있으면 레이아웃 비율 변경하지 않음
        title_locked = self._get_title_locked()
        bottom_locked = self._get_bottom_locked()
        
        # 잠금 상태일 때는 기본 비율 유지 -> _reset_layout_ratios 호출로 변경
        if title_locked and bottom_locked:
            self._reset_layout_ratios()
            return
            
        # 부모 객체의 레이아웃 확인
        layout = self.parent.layout()
        if not layout or not isinstance(layout, QVBoxLayout):
            return
            
        # 기본 비율 정의 (새로운 구조 반영)
        title_ratio = 2     # 타이틀바 2%
        main_ratio = 85     # 메인 영역 85%
        slider_ratio = 3    # 슬라이더 영역 3%
        button_ratio = 10   # 버튼 영역 10%
        
        # _ui_visibility에 저장된 UI 상태와 잠금 상태를 함께 고려
        # 제목표시줄 가시성 확인
        if not title_locked and not self._ui_visibility['title_bar']:
            # 제목표시줄이 잠기지 않고 숨겨진 경우, 그 비율을 메인 영역에 추가
            main_ratio += title_ratio
            title_ratio = 0
        
        # 하단 컨트롤 영역 전체 가시성 확인 (통합 UI 영역)
        if not bottom_locked and not self._ui_visibility['bottom_ui']:
            # 하단 컨트롤 전체가 잠기지 않고 숨겨진 경우, 슬라이더와 버튼 비율을 메인 영역에 추가
            main_ratio += slider_ratio + button_ratio
            slider_ratio = 0
            button_ratio = 0
            
        # 레이아웃 비율 업데이트
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue
                
            widget = item.widget()
            if not widget:
                continue
                
            # 위젯 종류에 따라 비율 설정 (새로운 구조 반영)
            if widget == self.parent.title_bar:
                layout.setStretch(i, title_ratio)
            elif widget == self.parent.main_layout:
                layout.setStretch(i, main_ratio)
            elif widget == self.parent.slider_widget:
                layout.setStretch(i, slider_ratio)
            elif widget == self.parent.button_container:
                layout.setStretch(i, button_ratio)
    
    def _reset_layout_ratios(self):
        """레이아웃 비율을 기본값으로 초기화"""
        # 부모 객체의 레이아웃 확인
        if not self.parent:
            return
            
        layout = self.parent.layout()
        if not layout or not isinstance(layout, QVBoxLayout):
            return
        
        # 기본 비율 설정 (새로운 구조 반영)
        title_ratio = 2     # 타이틀바 2%
        main_ratio = 85     # 메인 영역 85%
        slider_ratio = 3    # 슬라이더 영역 3%
        button_ratio = 10   # 버튼 영역 10%
        
        # 레이아웃 비율 초기화
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue
                
            widget = item.widget()
            if not widget:
                continue
            
            # 위젯 종류에 따라 비율 설정 (새로운 구조 반영)
            if widget == self.parent.title_bar:
                layout.setStretch(i, title_ratio)
            elif widget == self.parent.main_layout:
                layout.setStretch(i, main_ratio)
            elif widget == self.parent.slider_widget:
                layout.setStretch(i, slider_ratio)
            elif widget == self.parent.button_container:
                layout.setStretch(i, button_ratio)
    
    def get_ui_visibility(self, component_name):
        """
        UI 요소의 현재 가시성 상태를 반환합니다.
        
        Args:
            component_name (str): UI 요소 이름 ('title_bar', 'bottom_ui', 'info_label')
            
        Returns:
            bool: UI 요소 가시성 상태
        """
        # 이전 코드와의 호환성을 위한 처리
        if component_name == 'controls' or component_name == 'sliders':
            return self._ui_visibility.get('bottom_ui', True)
            
        if component_name in self._ui_visibility:
            return self._ui_visibility[component_name]
        return True  # 기본값: 표시 