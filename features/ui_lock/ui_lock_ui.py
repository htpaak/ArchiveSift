from PyQt5.QtCore import QTimer, Qt

class UILockUI:
    """UI 잠금 관련 UI 요소를 관리하는 클래스"""
    
    def __init__(self, parent, manager):
        self.parent = parent
        self.manager = manager
        self.ui_lock_btn = getattr(parent, 'ui_lock_btn', None)
        self.title_lock_btn = getattr(parent, 'title_lock_btn', None)
        
        # 시그널 연결
        self._connect_signals()
        
        # 초기 UI 상태 설정
        QTimer.singleShot(100, self._update_button_states)
    
    def _connect_signals(self):
        """시그널을 슬롯에 연결"""
        if self.manager:
            self.manager.ui_lock_changed.connect(self._handle_ui_lock_change)
            self.manager.title_lock_changed.connect(self._handle_title_lock_change)
    
    def _update_button_states(self):
        """버튼 상태 업데이트"""
        self.update_ui_lock_button_state()
        self.update_title_lock_button_state()
    
    def _handle_ui_lock_change(self, locked):
        """UI 잠금 상태 변경 처리"""
        if locked:
            # UI 요소 표시
            if hasattr(self.parent, 'slider_widget'):
                self.parent.slider_widget.show()
            
            if hasattr(self.parent, 'buttons'):
                for row in self.parent.buttons:
                    for button in row:
                        button.show()
        
        # 버튼 상태 업데이트
        self.update_ui_lock_button_state()
    
    def _handle_title_lock_change(self, locked):
        """타이틀 잠금 상태 변경 처리"""
        if hasattr(self.parent, 'title_bar'):
            if locked:
                # 타이틀바 표시 및 위치 설정
                self.parent.title_bar.show()
                # resizeEvent에서 타이틀바 크기가 조정되도록 함
                # 명시적으로 크기를 변경하지 않고 표시와 숨김만 처리
        
        # 버튼 상태 업데이트
        self.update_title_lock_button_state()
    
    def update_ui_lock_button_state(self):
        """UI 잠금 버튼 상태 업데이트"""
        if not self.ui_lock_btn:
            return
        
        is_locked = self.manager.ui_locked
        
        # 버튼 텍스트 및 스타일 설정
        self.ui_lock_btn.setText('🔒' if is_locked else '🔓')
        
        # 버튼 스타일 설정
        color = "rgba(231, 76, 60, 0.9)" if is_locked else "rgba(52, 73, 94, 0.6)"
        hover_color = "rgba(231, 76, 60, 1.0)" if is_locked else "rgba(52, 73, 94, 1.0)"
        
        self.ui_lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
    
    def update_title_lock_button_state(self):
        """타이틀 잠금 버튼 상태 업데이트"""
        if not self.title_lock_btn:
            return
        
        is_locked = self.manager.title_locked
        
        # 버튼 텍스트 및 스타일 설정
        self.title_lock_btn.setText('🔒' if is_locked else '🔓')
        
        # 버튼 스타일 설정
        color = "rgba(231, 76, 60, 0.9)" if is_locked else "rgba(52, 73, 94, 0.6)"
        hover_color = "rgba(231, 76, 60, 1.0)" if is_locked else "rgba(52, 73, 94, 1.0)"
        
        self.title_lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """) 