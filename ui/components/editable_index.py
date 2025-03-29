#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
편집 가능한 인덱스 레이블 모듈

인덱스 숫자를 클릭하여 직접 편집할 수 있는 인터페이스를 제공합니다.
"1 / 10" 같은 형식에서 숫자 부분만 편집 가능하게 합니다.
"""

from PyQt5.QtWidgets import QLabel, QLineEdit, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer, QRect, QPoint
from PyQt5.QtGui import QIntValidator, QFont

class EditableIndexLabel(QLabel):
    """클릭하면 직접 편집 가능한 인덱스 레이블 클래스"""
    
    # 사용자 정의 시그널
    indexChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """
        EditableIndexLabel 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("인덱스를 클릭하여 편집")
        self.setAlignment(Qt.AlignCenter)
        
        # 경계 영역 추가
        self.setContentsMargins(5, 5, 5, 5)
        
        # 편집 필드 초기화 - 부모 없이 생성 (독립적인 팝업)
        self._editor = QLineEdit()  # 부모를 지정하지 않음
        self._editor.setValidator(QIntValidator(1, 999999))
        self._editor.returnPressed.connect(self.apply_change)
        self._editor.installEventFilter(self)
        
        # 팝업으로 설정
        self._editor.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        
        # 에디터 스타일 설정
        self._editor.setAlignment(Qt.AlignCenter)
        self._editor.setStyleSheet("""
            QLineEdit {
                border: 2px solid #2980b9;
                border-radius: 4px;
                background-color: #f9f9f9;
                color: #2c3e50;
                padding: 2px 4px;
                margin: 0px;
                font-weight: bold;
                selection-background-color: #3498db;
            }
        """)
        
        # 레이블의 폰트 복사 및 크기 증가
        font = self.font()
        font.setPointSize(font.pointSize() + 3)  # 폰트 크기 더 크게 증가
        font.setBold(True)  # 굵게 설정
        self._editor.setFont(font)
        
        # 초기에는 보이지 않음
        self._editor.hide()
        
        # 변수 초기화
        self.total_files = 0
        self.current_index = 0
        self.editing_mode = False
        self.click_pos = None
        self.ignore_focus_out = False
        
        # 기본 텍스트 설정
        self.setText("0 / 0")
    
    def setText(self, text):
        """
        텍스트 설정
        
        Args:
            text: 표시할 텍스트 (형식: "1 / 10")
        """
        super().setText(text)
        
        # 현재 인덱스와 총 파일 수 추출
        try:
            parts = text.split('/')
            self.current_index = int(parts[0].strip())
            self.total_files = int(parts[1].strip())
        except:
            self.current_index = 0
            self.total_files = 0
    
    def update_index(self, index, total):
        """
        인덱스 및 총 파일 수 업데이트
        
        Args:
            index: 현재 인덱스 (0-기반)
            total: 총 파일 수
        """
        # 편집 모드 활성화 상태인 경우 종료
        if self.editing_mode:
            self.end_editing_mode()
            
        self.current_index = index + 1  # 표시용 인덱스는 1부터 시작
        self.total_files = total
        self.setText(f"{self.current_index} / {self.total_files}")
        
        # 편집기가 있으면 유효성 검사기 범위 업데이트
        if self._editor is not None:
            self._editor.validator().setRange(1, total if total > 0 else 1)
    
    def end_editing_mode(self):
        """편집 모드 강제 종료"""
        if not self.editing_mode:
            return
            
        # 일시적으로 포커스 아웃 이벤트 무시
        self.ignore_focus_out = True
        
        # 편집 모드 비활성화
        self.editing_mode = False
        
        # 에디터 숨기기
        if self._editor:
            self._editor.hide()
        
        # 포커스 아웃 이벤트 무시 해제
        self.ignore_focus_out = False
    
    def eventFilter(self, obj, event):
        """이벤트 필터"""
        if obj == self._editor:
            # 키 이벤트 처리
            if event.type() == QEvent.KeyPress:
                # Escape 키 처리
                if event.key() == Qt.Key_Escape:
                    self.cancel_editing()
                    return True
            
            # 포커스 아웃 이벤트 처리
            elif event.type() == QEvent.FocusOut:
                # 무시 플래그가 설정되지 않은 경우에만 적용
                if not self.ignore_focus_out and self.editing_mode:
                    # 변경사항 적용 (약간의 지연으로 다른 이벤트 처리 후)
                    QTimer.singleShot(100, self.apply_change)
                return False
        
        return super().eventFilter(obj, event)
    
    def mousePressEvent(self, event):
        """마우스 버튼 누름 이벤트"""
        if event.button() == Qt.LeftButton and self.total_files > 0:
            # 클릭 위치 저장
            self.click_pos = event.pos()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """마우스 버튼 뗌 이벤트"""
        if event.button() == Qt.LeftButton and self.total_files > 0 and self.click_pos is not None:
            # 같은 위치에서 클릭했다 뗐는지 확인 (드래그 아님)
            if (event.pos() - self.click_pos).manhattanLength() < 5:
                self.start_editing()
            self.click_pos = None
        super().mouseReleaseEvent(event)
    
    def _calculate_editor_geometry(self):
        """에디터 위치 및 크기 계산"""
        # 텍스트 영역 계산
        metrics = self.fontMetrics()
        text = str(self.current_index)
        # 여백 유지
        text_width = metrics.boundingRect(text).width() + 30
        
        # 높이는 그대로 유지
        height = self.contentsRect().height() + 8
        
        # 전체 텍스트에서 숫자 부분 위치 계산
        full_text = self.text()
        index_pos = full_text.find(str(self.current_index))
        
        if index_pos >= 0:
            # 레이블 내 상대 좌표 계산
            rect = self.contentsRect()
            text_rect = metrics.boundingRect(rect, self.alignment(), full_text)
            
            # 중앙 정렬의 경우 적절한 위치 계산
            x_offset = (rect.width() - text_rect.width()) / 2
            if self.alignment() & Qt.AlignHCenter:
                x_offset += rect.left()
            else:
                x_offset = rect.left()
                
            # 숫자 부분의 x 위치 계산 (왼쪽으로 15px 더 이동)
            num_pos_x = x_offset + metrics.boundingRect(full_text[:index_pos]).width() - 15
            
            # Y 위치는 약간 위로 조정 (중앙 정렬을 위해)
            y_pos = rect.top() - 4
            
            return QRect(int(num_pos_x), y_pos, text_width, height)
        else:
            # 위치를 찾을 수 없으면 전체 영역 사용 (왼쪽으로 이동)
            rect = self.contentsRect()
            return QRect(rect.left() - 10, rect.top() - 4, rect.width() * 0.7, height + 8)
    
    def start_editing(self):
        """인덱스 직접 편집 시작"""
        if self.editing_mode or self.total_files <= 0:
            return
            
        # 편집 모드 활성화
        self.editing_mode = True
        
        # 에디터 위치 및 크기 설정
        editor_rect = self._calculate_editor_geometry()
        
        # 에디터 위치를 전역 좌표로 변환
        global_pos = self.mapToGlobal(QPoint(editor_rect.x(), editor_rect.y()))
        self._editor.setGeometry(QRect(global_pos.x(), global_pos.y(), 
                                       editor_rect.width(), editor_rect.height()))
        
        # 현재 인덱스를 에디터에 설정
        self._editor.setText(str(self.current_index))
        
        # 일시적으로 포커스 아웃 이벤트 무시
        self.ignore_focus_out = True
        
        # 에디터 표시
        self._editor.show()
        
        # 포커스 설정
        self._editor.setFocus(Qt.MouseFocusReason)
        
        # 전체 텍스트 선택 - 바로 숫자를 입력할 수 있도록
        self._editor.selectAll()
        
        # 이벤트 처리 후 포커스 아웃 이벤트 무시 해제
        QTimer.singleShot(200, self._reset_focus_flag)
    
    def _reset_focus_flag(self):
        """포커스 플래그 초기화"""
        self.ignore_focus_out = False
        
        # 편집기가 보이는 상태라면 활성화
        if self._editor.isVisible():
            self._editor.activateWindow()
            self._editor.setFocus()
            
            # 여기서도 텍스트가 선택되어 있는지 확인하고 필요시 다시 선택
            if not self._editor.hasSelectedText():
                self._editor.selectAll()
    
    def apply_change(self):
        """변경사항 적용"""
        # 이미 처리중이거나 편집 모드가 아니면 무시
        if not self.editing_mode or self._editor is None:
            return
        
        try:
            # 일시적으로 포커스 아웃 이벤트 무시
            self.ignore_focus_out = True
            
            # 에디터에서 값 가져오기
            new_index = int(self._editor.text())
            
            # 범위 검증
            if new_index < 1:
                new_index = 1
            elif new_index > self.total_files:
                new_index = self.total_files
            
            # 편집 모드 비활성화
            self.editing_mode = False
            
            # 에디터 숨기기
            self._editor.hide()
            
            # 인덱스 변경 필요 시에만 시그널 발생
            if new_index != self.current_index:
                # 0-기반 인덱스로 변환하여 시그널 발생
                self.indexChanged.emit(new_index - 1)
        
        except (ValueError, AttributeError):
            # 오류 발생 시 편집 취소
            self.cancel_editing()
        finally:
            # 포커스 아웃 이벤트 무시 해제
            self.ignore_focus_out = False
    
    def cancel_editing(self):
        """편집 취소"""
        self.end_editing_mode()
    
    def keyPressEvent(self, event):
        """키 입력 이벤트 처리"""
        # Enter 키 누르면 편집 모드 시작
        if event.key() == Qt.Key_Return and not self.editing_mode:
            self.start_editing()
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event):
        """크기 변경 이벤트 처리"""
        super().resizeEvent(event)
        
        # 편집 모드일 때 에디터 위치 조정
        if self.editing_mode and self._editor:
            editor_rect = self._calculate_editor_geometry()
            self._editor.setGeometry(editor_rect)