"""
미디어 처리를 위한 기본 클래스 모듈

이 모듈은 다양한 미디어 타입(이미지, PSD, GIF, WEBP, 비디오 등)을 처리하기 위한
기본 클래스를 제공합니다. 모든 미디어 핸들러는 이 클래스를 상속받아 구현됩니다.
"""

from abc import ABC, abstractmethod
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QSize


class MediaHandler(ABC):
    """
    미디어 처리를 위한 추상 기본 클래스
    
    모든 미디어 타입 핸들러(이미지, PSD, GIF, WEBP, 비디오 등)는 
    이 클래스를 상속받아 공통 인터페이스를 구현해야 합니다.
    
    Attributes:
        parent: 부모 위젯 (보통 ArchiveSift 클래스의 인스턴스)
        display_label: 미디어를 표시할 QLabel 위젯
    """
    
    def __init__(self, parent, display_label):
        """
        MediaHandler 클래스 초기화
        
        Args:
            parent: 부모 위젯 (보통 ArchiveSift 클래스의 인스턴스)
            display_label: 미디어를 표시할 QLabel 위젯
        """
        self.parent = parent
        self.display_label = display_label
        self.current_media_path = None
    
    @abstractmethod
    def load(self, path):
        """
        미디어 파일을 로드하는 추상 메서드
        
        모든 하위 클래스는 이 메서드를 구현하여 해당 미디어 타입을 로드해야 합니다.
        
        Args:
            path: 로드할 미디어 파일 경로
            
        Returns:
            bool: 로드 성공 여부
        """
        pass
    
    @abstractmethod
    def unload(self):
        """
        현재 로드된 미디어를 언로드하는 추상 메서드
        
        모든 하위 클래스는 이 메서드를 구현하여 리소스를 정리해야 합니다.
        """
        pass
    
    def get_current_path(self):
        """
        현재 로드된 미디어 경로 반환
        
        Returns:
            str: 현재 로드된 미디어 파일 경로
        """
        return self.current_media_path
    
    def is_loaded(self):
        """
        미디어가 로드되었는지 확인
        
        Returns:
            bool: 미디어 로드 여부
        """
        return self.current_media_path is not None
    
    def resize(self):
        """창 크기가 변경되었을 때 미디어 크기를 조정합니다."""
        raise NotImplementedError("서브클래스에서 구현해야 합니다.")
        
    def get_original_size(self):
        """
        원본 미디어의 크기를 반환합니다.
        
        Returns:
            QSize: 원본 미디어 크기
        """
        return QSize(0, 0)
        
    def get_current_size(self):
        """
        현재 표시된 미디어의 크기를 반환합니다.
        
        Returns:
            QSize: 현재 표시된 미디어 크기
        """
        return QSize(0, 0) 