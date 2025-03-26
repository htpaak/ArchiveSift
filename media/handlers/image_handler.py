"""
일반 이미지 처리를 위한 핸들러 모듈

이 모듈은 일반 이미지 파일(JPG, PNG 등)을 로드하고 표시하기 위한
ImageHandler 클래스를 제공합니다.
"""

import os
import time
from PyQt5.QtGui import QPixmap, QImage, QTransform
from PyQt5.QtCore import Qt, QSize
from PIL import Image
from io import BytesIO

# RAW 이미지 처리를 위한 라이브러리 추가
import rawpy
import numpy as np

# AVIF 이미지 처리를 위한 플러그인 등록
try:
    from pillow_avif import register_avif_opener
    register_avif_opener()
    AVIF_SUPPORT = True
except ImportError:
    AVIF_SUPPORT = False
    print("pillow-avif-plugin이 설치되지 않았습니다. AVIF 지원이 제한적일 수 있습니다.")

from media.handlers.base_handler import MediaHandler

class ImageHandler(MediaHandler):
    """
    일반 이미지 처리를 위한 클래스
    
    일반 이미지 파일(JPG, PNG 등)을 로드하고 표시하는 기능을 제공합니다.
    
    Attributes:
        parent: 부모 위젯 (ArchiveSift 클래스의 인스턴스)
        display_label: 이미지를 표시할 QLabel 위젯
        current_pixmap: 현재 로드된 이미지의 QPixmap 객체
        original_pixmap: 원본 크기의 QPixmap 객체 (크기 조정 전)
    """
    
    def __init__(self, parent, display_label):
        """
        ImageHandler 클래스 초기화
        
        Args:
            parent: 부모 위젯 (ArchiveSift 클래스의 인스턴스)
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
        elif format_type == 'raw_image':
            # RAW 이미지 파일 처리
            self.parent.current_media_type = 'image'  # 미디어 타입 업데이트
            
            # RAW 이미지 로드
            self.load(image_path)
            
            # 이미지 정보 업데이트
            self.parent.update_image_info()
        elif format_type == 'avif':
            # AVIF 이미지 파일 처리
            self.parent.current_media_type = 'image'  # 미디어 타입 업데이트
            
            # AVIF 이미지 로드
            self.load(image_path)
            
            # 이미지 정보 업데이트
            self.parent.update_image_info()
        elif format_type == 'image' or file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif', '.jpe', '.jps', '.jfif', '.jp2', '.tga']:
            # 일반 이미지 파일 처리
            self.parent.current_media_type = 'image'  # 미디어 타입 업데이트
            
            # ImageHandler를 사용하여 이미지 로드
            self.load(image_path)
            
            # 이미지 정보 업데이트
            self.parent.update_image_info()
    
    def load(self, image_path):
        """이미지 파일을 로드하고 화면에 표시합니다."""
        try:
            # 이미지 경로 확인
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {image_path}")
            
            # 이미지 크기 확인
            file_size_bytes = os.path.getsize(image_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            # 파일 확장자 확인
            _, file_ext = os.path.splitext(image_path.lower())
            
            # AVIF 이미지 파일 처리
            if file_ext == '.avif':
                try:
                    # 로딩 인디케이터 표시
                    if hasattr(self.parent, 'show_loading_indicator'):
                        self.parent.show_loading_indicator()
                    
                    # 로딩 메시지 표시
                    if hasattr(self.parent, 'show_message'):
                        self.parent.show_message(f"AVIF 이미지 로딩 중... {os.path.basename(image_path)}")
                    
                    # pillow-avif-plugin이 설치되었는지 확인
                    if not AVIF_SUPPORT:
                        self.parent.show_message("AVIF 파일을 처리하기 위해 pillow-avif-plugin이 필요합니다.")
                    
                    # PIL로 AVIF 이미지 로드
                    with Image.open(image_path) as pil_image:
                        # 이미지 메타데이터 출력 (디버깅 용도)
                        print(f"AVIF 이미지 정보: {pil_image.format}, {pil_image.mode}, {pil_image.size}")
                        
                        # RGBA 모드로 변환 (투명도 유지)
                        if pil_image.mode != 'RGBA':
                            pil_image = pil_image.convert('RGBA')
                        
                        # QImage로 변환 (PNG로 변환하여 메모리에 저장)
                        img_data = BytesIO()
                        pil_image.save(img_data, format='PNG')
                        qimg = QImage()
                        qimg.loadFromData(img_data.getvalue())
                        
                        if qimg.isNull():
                            raise ValueError("AVIF 이미지 변환 실패")
                        
                        # QPixmap으로 변환
                        pixmap = QPixmap.fromImage(qimg)
                        
                        # 이미지 표시
                        self.display_image(pixmap, image_path, file_size_mb)
                        
                        # 로딩 인디케이터 숨김
                        if hasattr(self.parent, 'hide_loading_indicator'):
                            self.parent.hide_loading_indicator()
                        
                        # 로딩 완료 메시지
                        if hasattr(self.parent, 'show_message'):
                            self.parent.show_message(f"AVIF 이미지 로드 완료: {os.path.basename(image_path)}, 크기: {file_size_mb:.2f}MB")
                        
                        return
                except Exception as e:
                    if hasattr(self.parent, 'hide_loading_indicator'):
                        self.parent.hide_loading_indicator()
                    if hasattr(self.parent, 'show_message'):
                        self.parent.show_message(f"AVIF 이미지 처리 중 오류 발생: {e}")
                    print(f"AVIF 이미지 처리 중 오류 발생: {e}")
                    # 오류 발생 시 일반 이미지 로드 방식으로 진행
            
            # RAW 이미지 파일 처리 (CR2, NEF, ARW, ORF, RW2, DNG, PEF, RAF, SRW)
            if file_ext in ['.cr2', '.nef', '.arw', '.orf', '.rw2', '.dng', '.pef', '.raf', '.srw']:
                try:
                    # 로딩 인디케이터 표시
                    if hasattr(self.parent, 'show_loading_indicator'):
                        self.parent.show_loading_indicator()
                        
                    # 로딩 메시지 표시
                    if hasattr(self.parent, 'show_message'):
                        self.parent.show_message(f"RAW 이미지 로딩 중... {os.path.basename(image_path)}")
                    
                    # rawpy 라이브러리를 사용하여 RAW 파일 로드
                    with rawpy.imread(image_path) as raw:
                        if hasattr(self.parent, 'show_message'):
                            self.parent.show_message(f"RAW 이미지 처리 중... {os.path.basename(image_path)}")
                        
                        # 이미지 처리 및 변환 (대용량 파일 처리를 위한 최적화)
                        # 파일 크기에 따라 처리 옵션 조정
                        if file_size_mb > 30:  # 30MB 이상의 대용량 RAW 파일
                            # 절반 크기로 처리하여 메모리 사용량과 처리 시간 감소
                            rgb = raw.postprocess(
                                use_camera_wb=True,  # 카메라 화이트밸런스 사용
                                half_size=True,      # 절반 크기로 처리 (빠른 로딩)
                                no_auto_bright=True, # 자동 밝기 조정 비활성화
                                output_bps=8,        # 8비트 출력 (기본)
                                demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD  # 빠른 알고리즘
                            )
                        else:  # 일반 크기 RAW 파일
                            # 고품질 처리 (기본 크기 유지)
                            rgb = raw.postprocess(
                                use_camera_wb=True,      # 카메라 화이트밸런스 사용
                                half_size=False,         # 원본 크기 유지
                                no_auto_bright=False,    # 자동 밝기 조정 활성화
                                output_bps=8,            # 8비트 출력
                                demosaic_algorithm=rawpy.DemosaicAlgorithm.DCB,  # 고품질 알고리즘
                                bright=1.0,              # 기본 밝기
                                median_filter_passes=0    # 미디안 필터 패스 수
                            )
                        
                        # RGB 배열을 QImage로 변환
                        height, width, channel = rgb.shape
                        bytes_per_line = 3 * width
                        
                        # NumPy 배열을 QImage로 변환 (RGB888 형식)
                        qimg = QImage(rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
                        
                        if qimg.isNull():
                            raise ValueError("RAW 이미지 변환 실패")
                        
                        # QImage의 깊은 복사본 생성 (원본 데이터에 대한 참조 제거)
                        qimg_copy = qimg.copy()
                        
                        # 메모리 정리
                        del rgb  # NumPy 배열 명시적 해제
                        
                        # QPixmap으로 변환
                        pixmap = QPixmap.fromImage(qimg_copy)
                        
                        # QImage 객체 해제 (명시적 메모리 관리)
                        del qimg
                        del qimg_copy
                        
                        # 가비지 컬렉션 요청 (선택적)
                        import gc
                        gc.collect()
                        
                        # 이미지 표시
                        self.display_image(pixmap, image_path, file_size_mb)
                        
                        # 로딩 인디케이터 숨김
                        if hasattr(self.parent, 'hide_loading_indicator'):
                            self.parent.hide_loading_indicator()
                        
                        # 로딩 완료 메시지
                        if hasattr(self.parent, 'show_message'):
                            self.parent.show_message(f"RAW 이미지 로드 완료: {os.path.basename(image_path)}, 크기: {file_size_mb:.2f}MB")
                        
                        return
                        
                except ImportError:
                    self.parent.show_message("RAW 이미지 처리를 위한 rawpy 라이브러리가 필요합니다.")
                    # rawpy가 없을 경우 PIL 폴백 사용
                    try:
                        with Image.open(image_path) as pil_image:
                            img_data = BytesIO()
                            pil_image.save(img_data, format='PNG')
                            qimg = QImage()
                            qimg.loadFromData(img_data.getvalue())
                            
                            if qimg.isNull():
                                raise ValueError("RAW 이미지 변환 실패")
                            
                            pixmap = QPixmap.fromImage(qimg)
                            self.display_image(pixmap, image_path, file_size_mb)
                            return
                    except Exception as pil_error:
                        self.parent.show_message(f"RAW 이미지 처리 실패: {pil_error}")
                        # 계속 진행하여 일반 이미지 로드 방식 시도
                except Exception as e:
                    self.parent.show_message(f"RAW 이미지 처리 중 오류 발생: {e}")
                    print(f"RAW 이미지 처리 중 오류 발생: {e}")
                    # 오류 발생 시 일반 이미지 로드 방식으로 진행
            
            # HEIC/HEIF 파일 처리
            if file_ext in ['.heic', '.heif']:
                try:
                    # pillow-heif 라이브러리를 사용
                    from pillow_heif import register_heif_opener
                    register_heif_opener()
                    
                    # PIL로 이미지 로드
                    with Image.open(image_path) as pil_image:
                        # QImage로 변환
                        img_data = BytesIO()
                        pil_image.save(img_data, format='PNG')
                        qimg = QImage()
                        qimg.loadFromData(img_data.getvalue())
                        
                        if qimg.isNull():
                            raise ValueError("이미지 변환 실패")
                        
                        # QPixmap으로 변환
                        pixmap = QPixmap.fromImage(qimg)
                        self.display_image(pixmap, image_path, file_size_mb)
                        return
                except ImportError:
                    raise ImportError("HEIC/HEIF 파일을 처리하기 위한 pillow-heif 라이브러리가 필요합니다")
                except Exception as e:
                    raise Exception(f"HEIC/HEIF 이미지 처리 중 오류 발생: {e}")
            
            # 일반 이미지 파일 처리
            pixmap = QPixmap(image_path)
            
            if pixmap.isNull():
                # QPixmap으로 직접 로드 실패 시 PIL 시도
                try:
                    # PIL을 사용하여 이미지 로드
                    with Image.open(image_path) as pil_image:
                        # QImage로 변환
                        img_data = BytesIO()
                        pil_image.save(img_data, format='PNG')
                        qimg = QImage()
                        qimg.loadFromData(img_data.getvalue())
                        
                        if qimg.isNull():
                            raise ValueError("이미지 변환 실패")
                        
                        # QPixmap으로 변환
                        pixmap = QPixmap.fromImage(qimg)
                except Exception as pil_error:
                    # 모든 방법 실패 시 오류 발생
                    raise ValueError(f"이미지 로드 실패: {pil_error}")
            
            # 이미지 표시
            self.display_image(pixmap, image_path, file_size_mb)
            
        except Exception as e:
            # 에러 핸들링
            self.on_error(image_path, str(e))
            # 오류가 발생한 경우 클라이언트에게 알림
            if hasattr(self.parent, 'show_message'):
                self.parent.show_message(f"이미지 로드 중 오류 발생: {e}")
    
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
        elif file_format == 'psd' or file_format == 'raw_image' or file_format == 'avif' or file_format == 'image' or file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif', '.cr2', '.nef', '.arw', '.avif', '.jpe', '.jps', '.jfif', '.jp2']:
            # 정적 이미지 처리 (일반 이미지, PSD, RAW, AVIF, JPEG 계열)
            self.parent.load_static_image(image_path, file_format, file_ext)
        elif file_format == 'video':
            # 비디오 미디어 처리
            self.parent.load_video_media(image_path)
        else:
            self.parent.current_media_type = 'unknown'  # 미디어 타입 업데이트
        
        # 미디어 로딩 후 최종 처리
        self.parent.finalize_media_loading(image_path)

    def prepare_image_for_display(self, image, size_mb):
        """
        이미지 변환(회전, 크기 조정)을 처리하는 메서드
        
        Args:
            image: 표시할 QPixmap 이미지
            size_mb: 이미지 크기 (MB)
            
        Returns:
            QPixmap: 크기 조정 및 회전이 적용된 이미지
        """
        # 회전 각도가 0이 아니면 이미지 회전 적용 (원본 이미지에 직접 적용)
        display_image = image  # 기본적으로 원본 이미지 사용
        if hasattr(self.parent, 'current_rotation') and self.parent.current_rotation != 0:
            transform = QTransform().rotate(self.parent.current_rotation)
            display_image = image.transformed(transform, Qt.SmoothTransformation)
            print(f"이미지에 회전 적용됨: {self.parent.current_rotation}°")
        
        # 이미지 크기에 따라 스케일링 방식 결정
        # 작은 이미지는 고품질 변환, 큰 이미지는 빠른 변환 사용
        transform_method = Qt.SmoothTransformation if size_mb < 20 else Qt.FastTransformation
        
        # 화면 크기 얻기
        label_size = self.display_label.size()
        
        # 이미지 크기가 화면보다 훨씬 크면 2단계 스케일링 적용
        if size_mb > 30 and (display_image.width() > label_size.width() * 2 or display_image.height() > label_size.height() * 2):
            # 1단계: 빠른 방식으로 대략적인 크기로 축소
            # float 값을 int로 변환 (타입 오류 수정)
            intermediate_pixmap = display_image.scaled(
                int(label_size.width() * 1.2),  # float를 int로 변환
                int(label_size.height() * 1.2),  # float를 int로 변환
                Qt.KeepAspectRatio,
                Qt.FastTransformation  # 빠른 변환 사용
            )
            
            # 2단계: 고품질 방식으로 최종 크기로 조정
            scaled_pixmap = intermediate_pixmap.scaled(
                label_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation  # 고품질 변환 사용
            )
        else:
            # 일반 크기 이미지는 바로 스케일링
            scaled_pixmap = display_image.scaled(
                label_size,
                Qt.KeepAspectRatio,
                transform_method  # 이미지 크기에 따라 결정된 변환 방식 사용
            )
            
        return scaled_pixmap
    
    def display_image(self, pixmap, image_path, file_size_mb):
        """
        이미지를 화면에 표시합니다.
        
        Args:
            pixmap (QPixmap): 표시할 이미지 픽스맵
            image_path (str): 이미지 파일 경로
            file_size_mb (float): 파일 크기 (MB)
        """
        try:
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
            if hasattr(self.parent, 'hide_loading_indicator'):
                self.parent.hide_loading_indicator()
            
            # 이미지 정보 업데이트
            filename = os.path.basename(image_path)
            extension = os.path.splitext(filename)[1].upper().lstrip('.')
            
            # 스케일링된 이미지 표시
            if hasattr(self, 'display_label') and self.display_label:
                self.display_label.setPixmap(self.current_pixmap)
            
            if hasattr(self.parent, 'show_message'):
                self.parent.show_message(f"{extension} 이미지 로드 완료: {filename}, 크기: {file_size_mb:.2f}MB")
            
            # 현재 미디어 타입 설정
            self.parent.current_media_type = 'image'
            
        except Exception as e:
            if hasattr(self.parent, 'show_message'):
                self.parent.show_message(f"이미지 표시 중 오류 발생: {str(e)}")
            raise e
    
    def on_error(self, image_path, error_message):
        """
        이미지 로드 오류 처리
        
        Args:
            image_path (str): 실패한 이미지 파일 경로
            error_message (str): 오류 메시지
        """
        print(f"이미지 로드 오류: {error_message}")
        
        # 로딩 인디케이터 숨김
        if hasattr(self.parent, 'hide_loading_indicator'):
            self.parent.hide_loading_indicator()
    
    def handle_image_caching(self, path, image, size_mb):
        """
        이미지 캐싱을 처리하는 메서드
        
        Args:
            path: 이미지 파일 경로
            image: 캐싱할 QPixmap 이미지
            size_mb: 이미지 크기 (MB)
        """
        # 이미지 크기 제한 (메모리 관리)
        large_image_threshold = 50  # MB 단위
        
        # 너무 큰 이미지는 캐시하지 않음
        if size_mb < large_image_threshold:
            # 캐시에 이미지 저장 (파일 확장자에 따라 적절한 캐시 선택)
            file_ext = os.path.splitext(path)[1].lower()
            
            if file_ext == '.psd':
                self.parent.psd_cache.put(path, image, size_mb)
            elif file_ext in ['.gif', '.webp']:
                self.parent.gif_cache.put(path, image, size_mb)
            else:
                # 원본 이미지를 캐시 (회전하지 않은 상태)
                self.parent.image_cache.put(path, image, size_mb)
        else:
            print(f"크기가 너무 큰 이미지는 캐시되지 않습니다: {os.path.basename(path)} ({size_mb:.2f}MB)") 