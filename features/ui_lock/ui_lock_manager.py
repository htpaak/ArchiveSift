from PyQt5.QtCore import QObject, pyqtSignal

class UILockManager(QObject):
    """UI 잠금 상태를 관리하는 클래스"""
    
    # 상태 변경 시그널
    ui_lock_changed = pyqtSignal(bool)
    title_lock_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ui_locked = True  # 시작 시 UI 잠금 상태
        self._title_locked = True  # 시작 시 타이틀 잠금 상태
        self._parent = parent
        
        # 부모 객체에 호환성 변수 설정
        if parent:
            parent.is_bottom_ui_locked = self._ui_locked
            parent.is_title_ui_locked = self._title_locked
        
        # 초기 상태 신호 발생
        self.ui_lock_changed.emit(self._ui_locked)
        self.title_lock_changed.emit(self._title_locked)
    
    @property
    def ui_locked(self):
        """UI 잠금 상태 반환"""
        return self._ui_locked
    
    @property
    def title_locked(self):
        """타이틀 잠금 상태 반환"""
        return self._title_locked
    
    def toggle_ui_lock(self):
        """UI 잠금 상태 토글"""
        self._ui_locked = not self._ui_locked
        
        # 호환성을 위한 변수 설정
        if self._parent:
            self._parent.is_bottom_ui_locked = self._ui_locked
        
        # 신호 발생
        self.ui_lock_changed.emit(self._ui_locked)
        print(f"UI 잠금 상태: {self._ui_locked}")
        return self._ui_locked
    
    def toggle_title_lock(self):
        """타이틀 잠금 상태 토글"""
        self._title_locked = not self._title_locked
        
        # 호환성을 위한 변수 설정
        if self._parent:
            self._parent.is_title_ui_locked = self._title_locked
        
        # 신호 발생
        self.title_lock_changed.emit(self._title_locked)
        print(f"타이틀 잠금 상태: {self._title_locked}")
        return self._title_locked 