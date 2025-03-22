"""
마우스 이벤트 처리 모듈

이 모듈은 마우스 이벤트(클릭, 더블클릭, 휠, 이동 등)를 처리하는 MouseHandler 클래스를 정의합니다.
ImageViewer 클래스에서 마우스 이벤트 처리 코드를 분리하여 모듈화했습니다.
"""

import time
from PyQt5.QtCore import QObject, Qt, QEvent, QPoint, QRect, QTimer
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtGui import QCursor

class MouseHandler(QObject):
    """
    마우스 이벤트 처리 클래스
    
    이 클래스는 ImageViewer의 마우스 이벤트 처리를 담당합니다.
    """
    
    def __init__(self, parent=None):
        """
        MouseHandler 초기화
        
        Args:
            parent: 부모 객체 (ImageViewer 인스턴스)
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
        # 현재 미디어 타입 확인
        current_media_type = getattr(self.parent, 'current_media_type', 'unknown')
        
        # 애니메이션이나 비디오 재생 중인 경우 필요한 정리 작업 수행
        if current_media_type in ['gif_animation', 'webp_animation', 'video']:
            # 비디오 재생 중인 경우
            if current_media_type == 'video':
                # 비디오 중지
                self.parent.stop_video()
            
            # 애니메이션 재생 중인 경우 (GIF/WEBP)
            elif current_media_type in ['gif_animation', 'webp_animation']:
                # 리소스 정리를 위해 먼저 cleanup_current_media 호출
                self.parent.cleanup_current_media()
        
        # 방향 체크 후 이미지 전환
        if delta > 0:
            # 휠을 위로 돌린 경우 - 이전 이미지
            self.parent.show_previous_image()
        elif delta < 0:
            # 휠을 아래로 돌린 경우 - 다음 이미지
            self.parent.show_next_image()
            
    def handle_double_click(self, event=None):
        """
        더블 클릭 시 전체화면 또는 최대화 상태 전환
        """
        # 이벤트 객체가 전달되었는지 확인 (디버깅)
        print(f"마우스 더블 클릭 처리: event={event}")
        
        if self.parent.isFullScreen():
            # 전체화면 모드에서는 전체화면 토글 함수 호출
            self.parent.toggle_fullscreen()
        else:
            # 일반 모드에서는 최대화/일반 창 전환
            self.parent.toggle_maximize_state()
            
    def wheel_event(self, event):
        """휠 이벤트 처리"""
        current_time = time.time() * 1000  # 현재 시간(밀리초)
        
        # 기본 쿨다운 값 설정 (일반적인 경우 500ms)
        cooldown_ms = 500
        
        # 쿨다운 체크 - 상수 시간 연산 O(1)
        if current_time - self.last_wheel_time < cooldown_ms:
            event.accept()  # 이벤트 처리됨으로 표시하고 무시
            return
        
        # 현재 미디어 타입 확인
        current_media_type = getattr(self.parent, 'current_media_type', 'unknown')
        
        # 애니메이션이나 비디오 재생 중인 경우 필요한 정리 작업 수행
        if current_media_type in ['gif_animation', 'webp_animation', 'video']:
            # 비디오 재생 중인 경우
            if current_media_type == 'video':
                # 비디오 중지
                self.parent.stop_video()
            
            # 애니메이션 재생 중인 경우 (GIF/WEBP)
            elif current_media_type in ['gif_animation', 'webp_animation']:
                # 리소스 정리를 위해 먼저 cleanup_current_media 호출
                self.parent.cleanup_current_media()
        
        # 방향 체크 후 이미지 전환
        if event.angleDelta().y() > 0:
            # 휠을 위로 돌린 경우 - 이전 이미지
            self.parent.show_previous_image()
        elif event.angleDelta().y() < 0:
            # 휠을 아래로 돌린 경우 - 다음 이미지
            self.parent.show_next_image()
        
        self.last_wheel_time = current_time  # 마지막 처리 시간 업데이트

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

    def event_filter(self, obj, event):
        """모든 마우스 이벤트를 필터링"""
        if event.type() == QEvent.MouseMove:
            global_pos = event.globalPos()
            local_pos = self.parent.mapFromGlobal(global_pos)
            
            # 변수를 조건문 외부에서 정의 (이 부분이 중요합니다)
            title_bar_area_height = 50  # 마우스가 상단 50px 이내일 때 타이틀바 표시
            bottom_area_height = 250  # 마우스가 하단 250px 이내일 때 컨트롤 표시

            # UI 상태 변경 여부를 추적하기 위한 변수
            ui_state_changed = False

            # 마우스가 상단 영역에 있는 경우 (타이틀바 영역)
            if local_pos.y() <= title_bar_area_height or local_pos.y() >= self.parent.height() - bottom_area_height:
                # UI 일시적으로 표시
                ui_state_changed = self.handle_ui_visibility(show_temporary=True)
            else:
                # 마우스가 상/하단 영역을 벗어난 경우 UI 조건부 숨김
                ui_state_changed = self.handle_ui_visibility(show_temporary=False)
            
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
                            QApplication.restoreOverrideCursor()
                            self.parent.resize_direction = None
                else:
                    # 제목표시줄 버튼 영역에서는 기본 커서 사용
                    QApplication.setOverrideCursor(Qt.ArrowCursor)
                    self.parent.resize_direction = None

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