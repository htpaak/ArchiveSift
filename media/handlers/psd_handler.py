"""
PSD 파일 처리를 위한 핸들러 모듈

이 모듈은 Photoshop PSD 파일을 로드하고 표시하기 위한
PSDHandler 클래스를 제공합니다.
"""

import os
import time
from PyQt5.QtGui import QPixmap, QImage, QTransform
from PyQt5.QtCore import Qt, QSize
from PIL import Image, ImageCms
from io import BytesIO

from media.handlers.base_handler import MediaHandler
from media.loaders.cache_manager import LRUCache
from media.loaders.image_loader import ImageLoaderThread

class PSDHandler(MediaHandler):
    """
    PSD 파일 처리를 위한 클래스
    
    Photoshop PSD 파일을 로드하고 표시하는 기능을 제공합니다.
    
    Attributes:
        parent: 부모 위젯 (ImageSortingPAAK 클래스의 인스턴스)
        display_label: 이미지를 표시할 QLabel 위젯
        psd_cache: PSD 파일 캐시 (LRUCache 인스턴스)
        loader_threads: 로더 스레드를 추적하는 딕셔너리
    """
    
    def __init__(self, parent, display_label):
        """
        PSDHandler 클래스 초기화
        
        Args:
            parent: 부모 위젯 (ImageSortingPAAK 클래스의 인스턴스)
            display_label: 이미지를 표시할 QLabel 위젯
        """
        super().__init__(parent, display_label)
        self.current_pixmap = None
        self.original_pixmap = None
        
        # PSD 파일용 캐시 생성 (최대 3개 항목)
        self.psd_cache = LRUCache(3)
        
        # 로더 스레드 추적용 딕셔너리
        self.loader_threads = {}
    
    def load(self, psd_path):
        """
        PSD 파일을 로드합니다.
        
        Args:
            psd_path: 로드할 PSD 파일 경로
            
        Returns:
            bool: 로드 성공 여부
        """
        if not os.path.exists(psd_path):
            self.parent.show_message(f"file not found: {psd_path}")
            return False
            
        # 파일 이름과 확장자 추출
        filename = os.path.basename(psd_path)
        
        # 이미 로딩 중인지 확인
        loading_in_progress = False
        for path, loader in list(self.loader_threads.items()):
            if path == psd_path and loader.isRunning():
                loading_in_progress = True
                break
        
        if loading_in_progress:
            # 이미 로딩 중이면 다시 시작하지 않음
            return False
        
        # 로딩 표시 시작
        self.parent.show_loading_indicator()
        
        # LRUCache에서 캐시된 이미지 확인
        pixmap = self.psd_cache.get(psd_path)
        
        if pixmap is not None:
            # If found in cache, use it immediately
            if hasattr(self.parent, 'current_rotation') and self.parent.current_rotation != 0:
                # Apply rotation transformation
                transform = QTransform().rotate(self.parent.current_rotation)
                pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
            
            # 이미지 크기 조정 후 표시
            self.original_pixmap = pixmap
            self._apply_pixmap(pixmap)
            
            # 로딩 인디케이터 숨기기
            self.parent.hide_loading_indicator()
            
            # 현재 경로 설정
            self.current_media_path = psd_path
            
            # 현재 미디어 타입 설정
            if hasattr(self.parent, 'current_media_type'):
                self.parent.current_media_type = 'psd'
            
            return True
        else:
            # 캐시에 없는 경우 로더 스레드로 로드
            
            # 진행 중인 모든 로더 스레드 정리 (새 작업 시작 전)
            for path, loader in list(self.loader_threads.items()):
                if loader.isRunning():
                    try:
                        loader.loaded.disconnect()
                        loader.error.disconnect()
                    except Exception:
                        pass
            
            # 로더 스레드 목록 비우기 (새 시작 전에)
            self.loader_threads.clear()
            
            # 현재 미디어 경로 설정
            self.current_media_path = psd_path
            
            # 비동기 로딩 시작
            # self.parent.show_message(f"PSD image loading started: {filename}")
            
            # 로더 스레드 생성 및 시작
            loader = ImageLoaderThread(psd_path, file_type='psd')
            loader.loaded.connect(self._on_psd_loaded)
            loader.error.connect(self._on_psd_error)
            loader.start()
            
            # 로더 스레드 추적
            self.loader_threads[psd_path] = loader
            
            return True
    
    def _on_psd_loaded(self, path, image, size_mb):
        """
        PSD 이미지 로딩이 완료되었을 때 호출되는 콜백
        
        Args:
            path: 로드된 PSD 파일 경로
            image: 로드된 QPixmap 객체
            size_mb: 이미지 크기(MB)
        """
        # 로딩 인디케이터 숨기기
        self.parent.hide_loading_indicator()
        
        # 이미지 크기 제한 (메모리 관리)
        large_image_threshold = 50  # MB 단위
        
        # 너무 큰 이미지는 캐시하지 않음
        if size_mb < large_image_threshold:
            # Store image in cache  // 캐시에 이미지 저장
            self.psd_cache.put(path, image, size_mb)
        else:
            pass 
        
        # Display only if the current path matches the loaded image path  // 현재 경로가 로드된 이미지 경로와 일치하는 경우에만 표시
        if path == self.current_media_path:
            # Apply rotation if the rotation angle is non-zero  // 회전 각도가 0이 아니면 회전 적용
            if hasattr(self.parent, 'current_rotation') and self.parent.current_rotation != 0:
                # Apply rotation transform  // 회전 변환 적용
                transform = QTransform().rotate(self.parent.current_rotation)
                image = image.transformed(transform, Qt.SmoothTransformation)
            
            # 원본 픽스맵 저장
            self.original_pixmap = image
            
            # 이미지 크기 조정 후 표시
            self._apply_pixmap(image)
            
            # 파일 크기 계산
            size_mb = os.path.getsize(path) / (1024 * 1024)
            
            # 로딩 완료 메시지 제거
            # self.parent.show_message(f"PSD image load complete: {filename}, size: {size_mb:.2f}MB")
    
    def _on_psd_error(self, path, error_msg):
        """
        PSD 이미지 로딩 중 오류가 발생했을 때 호출되는 콜백
        
        Args:
            path: 오류가 발생한 PSD 파일 경로
            error_msg: 오류 메시지
        """
        # 로딩 인디케이터 숨기기
        self.parent.hide_loading_indicator()
        
        # Display error message  // 오류 메시지 표시
        self.parent.show_message(f"PSD file load error: {error_msg}")
    
    def _apply_pixmap(self, pixmap):
        """
        QPixmap을 라벨에 적용하고 크기 조정
        
        Args:
            pixmap: 적용할 QPixmap 객체
        """
        if not pixmap or not self.display_label:
            return
        
        # 라벨 크기 가져오기
        label_size = self.display_label.size()
        
        # 이미지 크기 조정 (AspectRatioMode는 비율 유지)
        scaled_pixmap = pixmap.scaled(
            label_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # 현재 픽스맵 설정
        self.current_pixmap = scaled_pixmap
        
        # MediaDisplay의 display_pixmap 메서드 호출 (있는 경우)
        if hasattr(self.display_label, 'display_pixmap'):
            self.display_label.display_pixmap(scaled_pixmap, 'psd')
        else:
            # 일반 QLabel인 경우 기존 방식으로 이미지 표시
            self.display_label.setPixmap(scaled_pixmap)
        
        # 이미지 정보 업데이트
        if hasattr(self.parent, 'update_image_info'):
            self.parent.update_image_info()
    
    def unload(self):
        """현재 로드된 PSD 이미지를 언로드합니다."""
        # 진행 중인 로더 스레드 정리
        for path, loader in list(self.loader_threads.items()):
            if loader.isRunning():
                try:
                    loader.loaded.disconnect()
                    loader.error.disconnect()
                except Exception:
                    pass
        
        # 로더 스레드 목록 비우기
        self.loader_threads.clear()
        
        # 현재 이미지 초기화
        self.current_pixmap = None
        self.original_pixmap = None
        self.current_media_path = None
    
    def resize(self):
        """창 크기가 변경되었을 때 PSD 이미지 크기를 조정합니다."""
        if self.original_pixmap:
            self._apply_pixmap(self.original_pixmap)
    
    def get_original_size(self):
        """
        원본 PSD 이미지의 크기를 반환합니다.
        
        Returns:
            QSize: 원본 이미지 크기
        """
        if self.original_pixmap:
            return self.original_pixmap.size()
        return QSize(0, 0)
    
    def get_current_size(self):
        """
        현재 표시된 PSD 이미지의 크기를 반환합니다.
        
        Returns:
            QSize: 현재 표시된 이미지 크기
        """
        if self.current_pixmap:
            return self.current_pixmap.size()
        return QSize(0, 0)
    
    def clear_cache(self):
        """PSD 캐시를 비웁니다."""
        if hasattr(self, 'psd_cache'):
            self.psd_cache.clear() 