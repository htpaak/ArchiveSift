"""
마우스 이벤트 처리 모듈

이 모듈은 마우스 이벤트(클릭, 더블클릭, 휠, 이동 등)를 처리하는 MouseHandler 클래스를 정의합니다.
MediaSorterPAAK 클래스에서 마우스 이벤트 처리 코드를 분리하여 모듈화했습니다.
"""

import time
from PyQt5.QtCore import QObject, Qt, QEvent, QPoint, QRect, QTimer
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtGui import QCursor

class MouseHandler(QObject):
    """
    마우스 이벤트 처리 클래스
    
    이 클래스는 MediaSorterPAAK의 마우스 이벤트 처리를 담당합니다.
    """
    
    def __init__(self, parent=None):
        """
        MouseHandler 초기화
        
        Args:
            parent: 부모 객체 (MediaSorterPAAK 인스턴스)
        """
        super().__init__(parent)
        self.parent = parent
        self.last_wheel_time = 0  # 마지막 휠 이벤트 시간
        
    def handle_wheel_event(self, delta):
        """
        MediaDisplay에서 전달된 휠 이벤트를 처리합니다.
        
        Args:
            delta (int): 휠 스크롤 값 (양수: 위로, 음수: 아래로)
        """
        # 쿨다운 체크
        current_time = time.time() * 1000  # 현재 시간(밀리초)
        cooldown_ms = self.parent.mouse_settings.get("wheel_cooldown_ms", 500)
        
        if current_time - self.last_wheel_time < cooldown_ms:
            return  # 쿨다운 중이면 이벤트 무시
        
        # 수정자 키 확인
        modifiers = QApplication.keyboardModifiers()
        is_ctrl_pressed = bool(modifiers & Qt.ControlModifier)
        is_shift_pressed = bool(modifiers & Qt.ShiftModifier)
        
        print(f"[DEBUG] handle_wheel_event: delta={delta}, Ctrl={is_ctrl_pressed}, Shift={is_shift_pressed}")
        
        # Check direction and execute action based on settings
        if delta > 0:  # Wheel Up
            if is_ctrl_pressed:
                # Ctrl + Wheel Up
                action = self.parent.mouse_settings.get("ctrl_wheel_up", "volume_up")
                self.execute_mouse_action(action)
            elif is_shift_pressed:
                # Shift + Wheel Up
                action = self.parent.mouse_settings.get("shift_wheel_up", "rotate_counterclockwise")
                self.execute_mouse_action(action)
            else:
                # Normal Wheel Up
                wheel_up_action = self.parent.mouse_settings.get("wheel_up", "prev_image")
                self.execute_mouse_action(wheel_up_action)
        elif delta < 0:  # Wheel Down
            if is_ctrl_pressed:
                # Ctrl + Wheel Down
                action = self.parent.mouse_settings.get("ctrl_wheel_down", "volume_down")
                self.execute_mouse_action(action)
            elif is_shift_pressed:
                # Shift + Wheel Down
                action = self.parent.mouse_settings.get("shift_wheel_down", "rotate_clockwise")
                self.execute_mouse_action(action)
            else:
                # Normal Wheel Down
                wheel_down_action = self.parent.mouse_settings.get("wheel_down", "next_image")
                self.execute_mouse_action(wheel_down_action)
        
        # 마지막 휠 이벤트 시간 업데이트
        self.last_wheel_time = current_time
        
    def handle_mouse_button(self, button):
        """
        Handles mouse button click events.
        
        Args:
            button: Clicked mouse button (Qt.LeftButton, Qt.MiddleButton, Qt.RightButton)
        """
        # Use default values if mouse settings are not available
        if not hasattr(self.parent, 'mouse_settings'):
            if button == Qt.MiddleButton:
                self.execute_mouse_action("toggle_play")
            elif button == Qt.RightButton:
                self.execute_mouse_action("context_menu")
            return
        
        # Determine and execute action based on mouse button
        if button == Qt.MiddleButton:
            action = self.parent.mouse_settings.get("middle_click", "toggle_play")
            self.execute_mouse_action(action)
        elif button == Qt.RightButton:
            action = self.parent.mouse_settings.get("right_click", "context_menu")
            self.execute_mouse_action(action)
            
    def execute_mouse_action(self, action):
        """
        Executes the configured mouse action.
        
        Args:
            action: The action to execute (e.g., "prev_image", "next_image", etc.)
        """
        # Prepare media transition before executing the action (same logic as keyboard handler)
        if action in ["prev_image", "next_image"]:
            self.prepare_media_transition()
        
        # Process based on action type
        if action == "prev_image":
            self.parent.show_previous_image()
        elif action == "next_image":
            self.parent.show_next_image()
        elif action == "rotate_clockwise":
            self.parent.rotate_image(True)
        elif action == "rotate_counterclockwise":
            self.parent.rotate_image(False)
        elif action == "toggle_play" or action == "toggle_animation_playback":
            # Toggle play/pause (both names supported for backward compatibility)
            self.parent.toggle_animation_playback()
        elif action == "toggle_fullscreen":
            self.parent.toggle_fullscreen()
        elif action == "toggle_maximize_state":
            self.parent.toggle_maximize_state()
        elif action == "volume_up":
            # Volume increase logic - works across all media types
            if hasattr(self.parent, 'volume_slider'):
                current_volume = self.parent.volume_slider.value()
                new_volume = min(current_volume + 5, 100)
                self.parent.volume_slider.setValue(new_volume)
                
                # Directly call video handler's set_volume (if available)
                if hasattr(self.parent, 'video_handler'):
                    self.parent.video_handler.set_volume(new_volume)
                else:
                    # Use adjust_volume if video handler is not available
                    self.parent.adjust_volume(new_volume)
        elif action == "volume_down":
            # Volume decrease logic - works across all media types
            if hasattr(self.parent, 'volume_slider'):
                current_volume = self.parent.volume_slider.value()
                new_volume = max(current_volume - 5, 0)
                self.parent.volume_slider.setValue(new_volume)
                
                # Directly call video handler's set_volume (if available)
                if hasattr(self.parent, 'video_handler'):
                    self.parent.video_handler.set_volume(new_volume)
                else:
                    # Use adjust_volume if video handler is not available
                    self.parent.adjust_volume(new_volume)
        elif action == "toggle_mute":
            # Toggle mute (works across all media types)
            if hasattr(self.parent, 'toggle_mute'):
                self.parent.toggle_mute()
        elif action == "delete_image":
            # Delete current image
            if hasattr(self.parent, 'delete_current_image'):
                self.parent.delete_current_image()
        elif action == "context_menu":
            # Display context menu
            if hasattr(self.parent, 'show_context_menu'):
                self.parent.show_context_menu()
        
    def prepare_media_transition(self):
        """이미지 전환 전 미디어 상태를 정리합니다."""
        # 현재 미디어 타입 확인
        current_media_type = getattr(self.parent, 'current_media_type', 'unknown')

        # --- 제거: 비디오 플레이어 정지 로직 제거 ---
        # # 비디오 플레이어 정지만 수행 (정리는 show_image 내부에서 처리)
        # if current_media_type == 'video':
        #     # 비디오 중지
        #     self.parent.stop_video()
        # --- 제거 끝 ---
        # 이제 비디오 정리는 show_image 내부에서만 처리됩니다.

        return True  # 준비 작업 수행됨 (실제 하는 일은 없음)
        
    def handle_double_click(self, event=None):
        """
        더블 클릭 이벤트를 처리합니다.
        """
        # 이벤트 객체가 전달되었는지 확인 (디버깅)
        print(f"마우스 더블 클릭 처리: event={event}")
        
        # 마우스 설정에서 double_click 액션에 할당된 기능 실행
        double_click_action = self.parent.mouse_settings.get("double_click", "toggle_fullscreen")
        self.execute_mouse_action(double_click_action)
            
    def wheel_event(self, event):
        """Handle wheel event"""
        current_time = time.time() * 1000  # Current time (milliseconds)
        
        # Use set cooldown value (default 500ms)
        cooldown_ms = self.parent.mouse_settings.get("wheel_cooldown_ms", 500)
        
        # Cooldown check - constant time O(1)
        if current_time - self.last_wheel_time < cooldown_ms:
            event.accept()  # Mark event as accepted and ignore
            return
        
        # Check modifier keys
        modifiers = QApplication.keyboardModifiers()
        is_ctrl_pressed = bool(modifiers & Qt.ControlModifier)
        is_shift_pressed = bool(modifiers & Qt.ShiftModifier)
        
        # (Debug messages removed)
        
        # Check direction and change image according to settings
        if event.angleDelta().y() > 0:  # Wheel up
            if is_ctrl_pressed:
                # Ctrl + wheel up
                action = self.parent.mouse_settings.get("ctrl_wheel_up", "volume_up")
                # (Debug message removed)
                self.execute_mouse_action(action)
            elif is_shift_pressed:
                # Shift + wheel up
                action = self.parent.mouse_settings.get("shift_wheel_up", "rotate_counterclockwise")
                # (Debug message removed)
                self.execute_mouse_action(action)
            else:
                # Regular wheel up
                action = self.parent.mouse_settings.get("wheel_up", "prev_image")
                self.execute_mouse_action(action)
        elif event.angleDelta().y() < 0:  # Wheel down
            if is_ctrl_pressed:
                # Ctrl + wheel down
                action = self.parent.mouse_settings.get("ctrl_wheel_down", "volume_down")
                # (Debug message removed)
                self.execute_mouse_action(action)
            elif is_shift_pressed:
                # Shift + wheel down
                action = self.parent.mouse_settings.get("shift_wheel_down", "rotate_clockwise")
                # (Debug message removed)
                self.execute_mouse_action(action)
            else:
                # Regular wheel down
                action = self.parent.mouse_settings.get("wheel_down", "next_image")
                self.execute_mouse_action(action)
        
        self.last_wheel_time = current_time  # Update last processing time

    def handle_ui_visibility(self, show_temporary=False):
        """
        UI 요소의 표시 여부를 관리하는 메서드
        
        Args:
            show_temporary: 일시적으로 UI를 표시할지 여부
            
        Returns:
            bool: UI 상태가 실제로 변경되었으면 True, 아니면 False
        """
        # UI 상태 관리자가 있으면 위임
        if hasattr(self.parent, 'ui_state_manager'):
            if show_temporary:
                return self.parent.ui_state_manager.show_ui_temporarily()
            else:
                return self.parent.ui_state_manager.hide_ui_conditionally()
        return False

    def handle_top_ui_visibility(self, show):
        """
        상단 UI 요소(제목표시줄) 가시성 처리
        
        Args:
            show (bool): 표시 여부
        
        Returns:
            bool: 상태 변경 여부
        """
        # UI 상태 관리자 존재 확인
        if not hasattr(self.parent, 'ui_state_manager'):
            return False
        
        # 기존 상태 확인
        previous_state = self.parent.ui_state_manager.get_ui_visibility('title_bar')
        
        # 잠금 상태 확인 - 잠금된 경우 항상 표시
        if hasattr(self.parent, 'ui_lock_manager') and self.parent.ui_lock_manager.title_locked:
            show = True
        
        # 상태가 변경된 경우만 처리
        if previous_state != show:
            # 타이틀바 표시/숨김 설정
            self.parent.ui_state_manager._update_ui_visibility({'title_bar': show})
            # 레이아웃 비율 업데이트는 제거 (자동으로 apply_ui_visibility에서 처리됨)
            return True
        
        return False

    def handle_bottom_ui_visibility(self, show):
        """
        하단 UI 요소(컨트롤바, 슬라이더) 가시성 처리
        
        Args:
            show (bool): 표시 여부
        
        Returns:
            bool: 상태 변경 여부
        """
        # UI 상태 관리자 존재 확인
        if not hasattr(self.parent, 'ui_state_manager'):
            return False
        
        # 기존 상태 확인
        previous_state = self.parent.ui_state_manager.get_ui_visibility('bottom_ui')
        
        # 잠금 상태 확인 - 잠금된 경우 항상 표시
        if hasattr(self.parent, 'ui_lock_manager') and self.parent.ui_lock_manager.ui_locked:
            show = True
        
        # 상태가 변경된 경우만 처리
        if previous_state != show:
            # UI 가시성 업데이트
            self.parent.ui_state_manager._update_ui_visibility({
                'bottom_ui': show
            })
            return True
        
        return False

    def event_filter(self, obj, event):
        """모든 마우스 이벤트를 필터링"""
        if event.type() == QEvent.MouseMove:
            global_pos = event.globalPos()
            local_pos = self.parent.mapFromGlobal(global_pos)
            
            # UI 잠금 상태 확인 - 둘 다 잠겨있으면 UI 가시성 변경하지 않음
            title_locked = False
            bottom_locked = False
            
            if hasattr(self.parent, 'ui_lock_manager'):
                title_locked = self.parent.ui_lock_manager.title_locked
                bottom_locked = self.parent.ui_lock_manager.ui_locked
            
            # UI가 잠금 상태가 아닐 때만 UI 가시성 변경 처리
            if not (title_locked and bottom_locked):
                # 변수를 조건문 외부에서 정의
                title_bar_area_height = 50  # 마우스가 상단 50px 이내일 때 타이틀바 표시
                # bottom_area_height = 250  # -> 제거: 동적 영역 계산으로 변경
    
                # UI 상태 변경 여부를 추적하기 위한 변수
                ui_state_changed = False
                
                # --- 추가: 예상 하단 UI 영역 계산 ---
                is_over_expected_bottom_area = False
                try:
                    window_height = self.parent.height()
                    bottom_stretch = self.parent.total_bottom_stretch
                    # 비율이 0일 경우 최소 높이 보장 (예: 10px)
                    expected_bottom_height = max(10, int(window_height * (bottom_stretch / 100.0)))
                    expected_bottom_rect = QRect(0, window_height - expected_bottom_height, self.parent.width(), expected_bottom_height)
                    is_over_expected_bottom_area = expected_bottom_rect.contains(local_pos)
                except AttributeError:
                    # 속성이 없는 경우 이전 방식과 유사하게 고정 높이 사용 (안전 장치)
                    fallback_bottom_area_height = 100 # 이전 250보다 작게 설정
                    if local_pos.y() >= self.parent.height() - fallback_bottom_area_height:
                         is_over_expected_bottom_area = True
                # --- 추가 끝 ---
    
                # 마우스가 상단 영역에 있는 경우 (타이틀바 영역) - 타이틀바만 표시
                if local_pos.y() <= title_bar_area_height:
                    # 상단 UI만 표시 (제목표시줄이 잠긴 경우 이미 표시된 상태)
                    if not title_locked:
                        ui_state_changed = self.handle_top_ui_visibility(True)
                # --- 수정: 하단 영역 체크 변경 ---
                # 마우스가 예상 하단 영역에 있는 경우 - 컨트롤만 표시
                # elif is_over_bottom_ui: # 실제 bottom_ui_container 영역 기준 -> 변경
                elif is_over_expected_bottom_area: # 예상 하단 영역 기준
                # --- 수정 끝 ---
                    # 하단 UI만 표시 (하단 UI가 잠긴 경우 이미 표시된 상태)
                    if not bottom_locked:
                        ui_state_changed = self.handle_bottom_ui_visibility(True)
                else:
                    # 마우스가 중앙 영역에 있는 경우 - 모든 UI 숨김
                    ui_state_changed_top = False
                    ui_state_changed_bottom = False
                    
                    # 제목표시줄이 잠기지 않은 경우만 숨김
                    if not title_locked:
                        ui_state_changed_top = self.handle_top_ui_visibility(False)
                    
                    # --- 수정: 하단 UI 숨김 조건 추가 ---
                    # 하단 UI가 잠기지 않고, 마우스가 예상 하단 영역 밖에 있는 경우만 숨김
                    # if not bottom_locked:
                    if not bottom_locked and not is_over_expected_bottom_area:
                    # --- 수정 끝 ---
                        ui_state_changed_bottom = self.handle_bottom_ui_visibility(False)
                    
                    ui_state_changed = ui_state_changed_top or ui_state_changed_bottom
                
                # UI 상태가 변경되었으면 이미지 크기 조정
                if ui_state_changed:
                    # 기존 타이머가 실행 중이면 중지
                    if self.parent.ui_update_timer.isActive():
                        self.parent.ui_update_timer.stop()
                    
                    # 일정 시간 후 UI 업데이트 실행
                    self.parent.ui_update_timer.start(50)
            
            # 창이 최대화 상태가 아닐 때만 크기 조절 가능
            if not self.parent.isMaximized():
                # 리사이징 중이면 크기 조절 처리
                if self.parent.resizing:
                    diff = event.globalPos() - self.parent.resize_start_pos
                    new_geometry = self.parent.resize_start_geometry.adjusted(0, 0, 0, 0)
                    
                    if self.parent.resize_direction in ['left', 'top_left', 'bottom_left']:
                        new_geometry.setLeft(self.parent.resize_start_geometry.left() + diff.x())
                    if self.parent.resize_direction in ['right', 'top_right', 'bottom_right']:
                        new_geometry.setRight(self.parent.resize_start_geometry.right() + diff.x())
                    if self.parent.resize_direction in ['top', 'top_left', 'top_right']:
                        new_geometry.setTop(self.parent.resize_start_geometry.top() + diff.y())
                    if self.parent.resize_direction in ['bottom', 'bottom_left', 'bottom_right']:
                        new_geometry.setBottom(self.parent.resize_start_geometry.bottom() + diff.y())
                    
                    # 최소 크기 제한
                    if new_geometry.width() >= 400 and new_geometry.height() >= 300:
                        self.parent.setGeometry(new_geometry)
                    return True

                # 제목 표시줄 드래그 중이면 창 이동
                elif hasattr(self.parent, 'drag_start_pos') and event.buttons() == Qt.LeftButton:
                    if self.parent.isMaximized():
                        # 최대화 상태에서 드래그하면 일반 크기로 복원
                        cursor_x = event.globalPos().x()
                        window_width = self.parent.width()
                        ratio = cursor_x / window_width
                        self.parent.showNormal()
                        # 마우스 위치 비율에 따라 창 위치 조정
                        new_x = int(event.globalPos().x() - (self.parent.width() * ratio))
                        self.parent.move(new_x, 0)
                        self.parent.drag_start_pos = event.globalPos()
                    else:
                        # 창 이동
                        self.parent.move(event.globalPos() - self.parent.drag_start_pos)
                    return True
                
                # 리사이징 중이 아닐 때 커서 모양 변경
                # --- 수정 시작: 전체 화면 아닐 때만 커서 변경 ---
                if not self.parent.isFullScreen():
                    edge_size = 4

                    # 제목표시줄의 버튼 영역인지 확인
                    is_in_titlebar = local_pos.y() <= 30

                    # 버튼 영역 판단 수정 - 버튼 위젯 객체를 직접 확인
                    is_in_titlebar_buttons = False
                    if is_in_titlebar:
                        # 제목 표시줄의 모든 자식 버튼 검사
                        for child in self.parent.title_bar.children():
                            if isinstance(child, QPushButton):
                                # 버튼의 전역 위치와 크기로 사각형 생성
                                button_pos = child.mapToGlobal(QPoint(0, 0))
                                button_rect = QRect(button_pos, child.size())
                                # 마우스 포인터가 버튼 위에 있는지 확인
                                if button_rect.contains(event.globalPos()):
                                    is_in_titlebar_buttons = True
                                    QApplication.setOverrideCursor(Qt.ArrowCursor)  # 버튼 위에서는 항상 화살표 커서
                                    break

                    # 마우스 커서 위치에 따른 크기 조절 방향 결정
                    if not is_in_titlebar_buttons:  # 버튼 영역이 아닐 때만 리사이징 방향 결정
                        if local_pos.x() <= edge_size and local_pos.y() <= edge_size:
                            QApplication.setOverrideCursor(Qt.SizeFDiagCursor)
                            self.parent.resize_direction = 'top_left'
                        elif local_pos.x() >= self.parent.width() - edge_size and local_pos.y() <= edge_size:
                            QApplication.setOverrideCursor(Qt.SizeBDiagCursor)
                            self.parent.resize_direction = 'top_right'
                        elif local_pos.x() <= edge_size and local_pos.y() >= self.parent.height() - edge_size:
                            QApplication.setOverrideCursor(Qt.SizeBDiagCursor)
                            self.parent.resize_direction = 'bottom_left'
                        elif local_pos.x() >= self.parent.width() - edge_size and local_pos.y() >= self.parent.height() - edge_size:
                            QApplication.setOverrideCursor(Qt.SizeFDiagCursor)
                            self.parent.resize_direction = 'bottom_right'
                        elif local_pos.x() <= edge_size:
                            QApplication.setOverrideCursor(Qt.SizeHorCursor)
                            self.parent.resize_direction = 'left'
                        elif local_pos.x() >= self.parent.width() - edge_size:
                            QApplication.setOverrideCursor(Qt.SizeHorCursor)
                            self.parent.resize_direction = 'right'
                        elif local_pos.y() <= edge_size:
                            QApplication.setOverrideCursor(Qt.SizeVerCursor)
                            self.parent.resize_direction = 'top'
                        elif local_pos.y() >= self.parent.height() - edge_size:
                            QApplication.setOverrideCursor(Qt.SizeVerCursor)
                            self.parent.resize_direction = 'bottom'
                        else:
                            if is_in_titlebar and not is_in_titlebar_buttons:
                                QApplication.setOverrideCursor(Qt.ArrowCursor)
                                self.parent.resize_direction = None
                            elif hasattr(self.parent, 'image_label') and self.parent.image_label.geometry().contains(local_pos) or \
                                any(button.geometry().contains(local_pos) for row in self.parent.buttons for button in row):
                                QApplication.setOverrideCursor(Qt.ArrowCursor)
                                self.parent.resize_direction = None
                            else:
                                # 다른 영역에서는 커서 리셋
                                QApplication.restoreOverrideCursor()
                                self.parent.resize_direction = None
                # --- 수정 끝 ---

        elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            local_pos = self.parent.mapFromGlobal(event.globalPos())
            is_in_titlebar = local_pos.y() <= 30
            
            # 버튼 영역 판단 수정 - 버튼 위젯 객체를 직접 확인
            is_in_titlebar_buttons = False
            if is_in_titlebar:
                # 제목 표시줄의 모든 자식 버튼 검사
                for child in self.parent.title_bar.children():
                    if isinstance(child, QPushButton):
                        button_pos = child.mapToGlobal(QPoint(0, 0))
                        button_rect = QRect(button_pos, child.size())
                        if button_rect.contains(event.globalPos()):
                            is_in_titlebar_buttons = True
                            return False  # 버튼 클릭은 이벤트 필터에서 처리하지 않고 버튼에게 전달
            
            if self.parent.resize_direction and not self.parent.isMaximized() and not is_in_titlebar_buttons:
                # 리사이징 시작
                self.parent.resizing = True
                self.parent.resize_start_pos = event.globalPos()
                self.parent.resize_start_geometry = self.parent.geometry()
                return True
            elif is_in_titlebar and not is_in_titlebar_buttons:
                # 제목 표시줄 드래그 시작
                self.parent.drag_start_pos = event.globalPos() - self.parent.pos()
                # 제목 표시줄 드래그 시 창에 포커스 설정
                self.parent.setFocus()
                return True
            return False

        elif event.type() == QEvent.MouseButtonRelease:
            # 리사이징 또는 드래그 종료
            was_resizing = self.parent.resizing
            if self.parent.resizing:
                self.parent.resizing = False
                QApplication.restoreOverrideCursor()
            if hasattr(self.parent, 'drag_start_pos'):
                delattr(self.parent, 'drag_start_pos')
            
            # 버튼이나 슬라이더 조작 후에 창 전체에 포커스 설정
            QTimer.singleShot(10, self.parent.setFocus)
            
            return was_resizing

        # 애플리케이션 활성화/비활성화 상태 처리
        elif event.type() == QEvent.WindowStateChange:
            if self.parent.windowState() & Qt.WindowMinimized:  # 창이 최소화되었을 때
                self.parent.pause_all_timers()
            elif event.oldState() & Qt.WindowMinimized:  # 창이 최소화 상태에서 복구되었을 때
                self.parent.resume_all_timers()
                
        # 창 활성화/비활성화 처리
        elif event.type() == QEvent.WindowActivate:  # 창이 활성화될 때
            self.parent.resume_all_timers()
        elif event.type() == QEvent.WindowDeactivate:  # 창이 비활성화될 때
            self.parent.pause_all_timers()

        return False  # 이벤트 필터에서 처리하지 않았음을 의미 