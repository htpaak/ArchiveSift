"""
일반 이미지 처리를 위한 핸들러 모듈

이 모듈은 일반 이미지 파일(JPG, PNG 등)을 로드하고 표시하기 위한
ImageHandler 클래스를 제공합니다.
"""

import os
import time
from PyQt5.QtGui import QPixmap, QImage, QTransform
from PyQt5.QtCore import Qt, QSize

from media.handlers.base_handler import MediaHandler

class ImageHandler(MediaHandler):
    """
    일반 이미지 처리를 위한 클래스
    
    일반 이미지 파일(JPG, PNG 등)을 로드하고 표시하는 기능을 제공합니다.
    
    Attributes:
        parent: 부모 위젯 (ImageViewer 클래스의 인스턴스)
        display_label: 이미지를 표시할 QLabel 위젯
        current_pixmap: 현재 로드된 이미지의 QPixmap 객체
        original_pixmap: 원본 크기의 QPixmap 객체 (크기 조정 전)
    """
    
    def __init__(self, parent, display_label):
        """
        ImageHandler 클래스 초기화
        
        Args:
            parent: 부모 위젯 (ImageViewer 클래스의 인스턴스)
            display_label: 이미지를 표시할 QLabel 위젯
        """
        super().__init__(parent, display_label)
        self.current_pixmap = None
        self.original_pixmap = None
    
    def load_static_image(self, image_path, format_type, file_ext):
        """일반 이미지와 PSD 이미지를 로드하고 표시합니다."""
        if format_type == 'psd':
            # PSD 파일 처리
            self.parent.current_media_type = 'image'  # 미디어 타입 업데이트
            
            # PSDHandler를 사용하여 PSD 파일 로드
            self.parent.psd_handler.load(image_path)
            
            # 이미지 정보 업데이트
            self.parent.update_image_info()
        elif format_type == 'image' or file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif']:
            # 일반 이미지 파일 처리
            self.parent.current_media_type = 'image'  # 미디어 타입 업데이트
            
            # ImageHandler를 사용하여 이미지 로드
            self.load(image_path)
            
            # 이미지 정보 업데이트
            self.parent.update_image_info()
    
    def load(self, image_path):
        """
        이미지 파일을 로드합니다.
        
        Args:
            image_path: 로드할 이미지 파일 경로
            
        Returns:
            bool: 로드 성공 여부
        """
        if not os.path.exists(image_path):
            self.parent.show_message(f"파일을 찾을 수 없습니다: {image_path}")
            return False
        
        # 파일 확장자 추출
        filename = os.path.basename(image_path)
        extension = os.path.splitext(filename)[1].upper().lstrip('.')
        
        # 이미지 로딩 시작 메시지
        self.parent.show_message(f"{extension} 이미지 로딩 시작: {filename}")
        
        # 로딩 인디케이터 표시
        self.parent.show_loading_indicator()
        
        # 이미지 로딩 시도
        try:
            # 이미지를 QPixmap으로 로드
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                self.parent.show_message(f"이미지 로드 실패: {filename}")
                self.parent.hide_loading_indicator()
                return False
            
            # 회전 적용 (parent의 current_rotation 값 사용)
            if hasattr(self.parent, 'current_rotation') and self.parent.current_rotation != 0:
                # 회전 변환 적용
                transform = QTransform().rotate(self.parent.current_rotation)
                pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                print(f"이미지에 회전 적용됨: {self.parent.current_rotation}°")
            
            # 이미지 로드 성공
            self.original_pixmap = pixmap
            self.current_pixmap = pixmap
            self.current_media_path = image_path
            
            # 이미지 크기 조정 및 표시
            self._resize_and_display()
            
            # 로딩 인디케이터 숨김
            self.parent.hide_loading_indicator()
            
            # 이미지 정보 업데이트
            file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
            self.parent.show_message(f"{extension} 이미지 로드 완료: {filename}, 크기: {file_size_mb:.2f}MB")
            
            # 현재 미디어 타입 설정
            self.parent.current_media_type = 'image'
            
            return True
            
        except Exception as e:
            self.parent.show_message(f"이미지 로드 중 오류 발생: {str(e)}")
            self.parent.hide_loading_indicator()
            return False
    
    def unload(self):
        """현재 로드된 이미지를 언로드합니다."""
        self.current_pixmap = None
        self.original_pixmap = None
        self.current_media_path = None
    
    def _resize_and_display(self):
        """이미지 크기를 조정하고 화면에 표시합니다."""
        if not self.original_pixmap or not self.display_label:
            return
        
        # 라벨 크기 가져오기
        label_size = self.display_label.size()
        
        # 이미지 크기 조정 (AspectRatioMode는 비율 유지)
        self.current_pixmap = self.original_pixmap.scaled(
            label_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # MediaDisplay의 display_pixmap 메서드 호출 (있는 경우)
        if hasattr(self.display_label, 'display_pixmap'):
            self.display_label.display_pixmap(self.current_pixmap, 'image')
        else:
            # 일반 QLabel인 경우 기존 방식으로 이미지 표시
            self.display_label.setPixmap(self.current_pixmap)
        
        # 이미지 정보 업데이트
        if hasattr(self.parent, 'update_image_info'):
            self.parent.update_image_info()
    
    def resize(self):
        """창 크기가 변경되었을 때 이미지 크기를 조정합니다."""
        self._resize_and_display()
        
    def get_original_size(self):
        """
        원본 이미지의 크기를 반환합니다.
        
        Returns:
            QSize: 원본 이미지 크기
        """
        if self.original_pixmap:
            return self.original_pixmap.size()
        return QSize(0, 0)
        
    def get_current_size(self):
        """
        현재 표시된 이미지의 크기를 반환합니다.
        
        Returns:
            QSize: 현재 표시된 이미지 크기
        """
        if self.current_pixmap:
            return self.current_pixmap.size()
        return QSize(0, 0)
        
    def show_image(self, image_path):
        """이미지/미디어 파일 표시 및 관련 UI 업데이트"""
        # 미디어 로딩 준비
        image_size_mb = self.parent.prepare_for_media_loading(image_path)
        
        # 현재 미디어 상태 업데이트
        self.parent.update_current_media_state(image_path)
        
        # 파일 형식 감지
        file_format, file_ext = self.parent.detect_media_format(image_path)
        
        # 파일 형식 감지 결과에 따라 적절한 핸들러 호출
        if file_format == 'gif_image' or file_format == 'gif_animation':
            # 애니메이션 미디어 (GIF) 처리
            self.parent.load_animation_media(image_path, file_format)
        elif file_format == 'webp_image' or file_format == 'webp_animation':
            # 애니메이션 미디어 (WEBP) 처리
            self.parent.load_animation_media(image_path, file_format)
        elif file_format == 'psd' or file_format == 'image' or file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif']:
            # 정적 이미지 처리 (일반 이미지, PSD)
            self.parent.load_static_image(image_path, file_format, file_ext)
        elif file_format == 'video':
            # 비디오 미디어 처리
            self.parent.load_video_media(image_path)
        else:
            self.parent.current_media_type = 'unknown'  # 미디어 타입 업데이트
        
        # 미디어 로딩 후 최종 처리
        self.parent.finalize_media_loading(image_path) 