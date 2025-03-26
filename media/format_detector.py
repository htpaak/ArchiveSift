import os
from PIL import Image
from PyQt5.QtGui import QImageReader
from io import BytesIO

class FormatDetector:
    """
    이미지 및 미디어 파일의 형식을 감지하고 분류하는 클래스입니다.
    정적/애니메이션 GIF와 WEBP를 구분하는 기능을 제공합니다.
    """
    
    @staticmethod
    def detect_media_format(image_path):
        """파일 형식을 감지하고 적절한 형식을 반환합니다."""
        # 파일 확장자 확인 (소문자로 변환)
        file_ext = os.path.splitext(image_path)[1].lower()
        
        # FormatDetector를 사용하여 파일 형식 감지
        file_format = FormatDetector.detect_format(image_path)
        print(f"FormatDetector 감지 결과: {file_format}")
        
        return file_format, file_ext
        
    @staticmethod
    def detect_format(file_path):
        """
        파일 경로를 기반으로 미디어 파일의 형식을 감지합니다.
        
        Args:
            file_path (str): 감지할 파일의 경로
            
        Returns:
            str: 감지된 파일 형식 ('image', 'gif_image', 'gif_animation', 
                'webp_image', 'webp_animation', 'video', 'psd', 'raw_image', 'avif' 등)
        """
        if not os.path.exists(file_path):
            return None
            
        # 파일 확장자 추출
        _, ext = os.path.splitext(file_path.lower())
        ext = ext[1:]  # 점(.) 제거
        
        # 기본 미디어 타입 분류
        if ext in ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm']:
            return 'video'
        elif ext == 'psd':
            return 'psd'
        elif ext in ['heic', 'heif']:
            return FormatDetector._handle_heic_heif(file_path)
        elif ext == 'avif':
            return 'avif'
        elif ext in ['cr2', 'nef', 'arw', 'orf', 'rw2', 'dng', 'pef', 'raf', 'srw']:
            return 'raw_image'
        
        # GIF 및 WEBP 파일 상세 분석
        if ext == 'gif':
            return FormatDetector._analyze_gif(file_path)
        elif ext == 'webp':
            return FormatDetector._analyze_webp(file_path)
        
        # 일반 이미지 파일 반환
        if ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'jpe', 'jps', 'jfif', 'jp2', 'tga']:
            return 'image'
            
        # 확장자로 판단 불가능한 경우 파일 내용 분석 시도
        try:
            with Image.open(file_path) as img:
                return 'image'
        except:
            return None
    
    @staticmethod
    def _handle_heic_heif(file_path):
        """
        HEIC/HEIF 파일을 처리합니다.
        
        Args:
            file_path (str): HEIC/HEIF 파일 경로
            
        Returns:
            str: 'image' 또는 None (오류 발생 시)
        """
        try:
            # pillow-heif 라이브러리를 사용하여 HEIC/HEIF 파일 읽기 시도
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
                
                # 등록 후 Image.open으로 열기 시도
                with Image.open(file_path) as img:
                    return 'image'
            except ImportError:
                print("pillow-heif 라이브러리가 설치되지 않았습니다.")
                return None
        except Exception as e:
            print(f"HEIC/HEIF 파일 처리 중 오류 발생: {e}")
            return None
    
    @staticmethod
    def _analyze_gif(file_path):
        """
        GIF 파일이 애니메이션인지 정적 이미지인지 분석합니다.
        
        Args:
            file_path (str): GIF 파일 경로
            
        Returns:
            str: 'gif_animation' 또는 'gif_image'
        """
        try:
            # QImageReader를 사용하여 애니메이션 지원 여부 확인
            reader = QImageReader(file_path)
            if reader.supportsAnimation():
                # 프레임 수를 확인하여 1개 이상이면 애니메이션으로 간주
                frame_count = reader.imageCount()
                if frame_count > 1:
                    return 'gif_animation'
            
            # PIL을 사용한 추가 확인 방법
            try:
                with Image.open(file_path) as img:
                    # getdata() 메서드는 PIL에서 프레임 수를 확인하는 방법
                    # 프레임 수가 1보다 크면 애니메이션
                    if hasattr(img, "n_frames") and img.n_frames > 1:
                        return 'gif_animation'
            except Exception:
                # PIL로 확인 실패 시 QImageReader 결과 사용
                pass
                
            # 애니메이션이 아닌 경우
            return 'gif_image'
        except Exception:
            # 오류 발생 시 기본값으로 정적 이미지 반환
            return 'gif_image'
    
    @staticmethod
    def _analyze_webp(file_path):
        """
        WEBP 파일이 애니메이션인지 정적 이미지인지 분석합니다.
        
        Args:
            file_path (str): WEBP 파일 경로
            
        Returns:
            str: 'webp_animation' 또는 'webp_image'
        """
        try:
            print(f"WEBP 분석 시작: {file_path}")
            # QImageReader를 사용하여 애니메이션 지원 여부 확인
            reader = QImageReader(file_path)
            if reader.supportsAnimation():
                # 프레임 수를 확인하여 1개 이상이면 애니메이션으로 간주
                frame_count = reader.imageCount()
                print(f"QImageReader 프레임 수: {frame_count}")
                if frame_count > 1:
                    print("WEBP 애니메이션으로 감지됨")
                    return 'webp_animation'
            
            # PIL을 사용한 추가 확인 방법
            try:
                with Image.open(file_path) as img:
                    # WEBP 애니메이션 확인 (PIL에서는 n_frames 속성으로 확인)
                    is_animated = False
                    if hasattr(img, "is_animated"):
                        is_animated = img.is_animated
                        print(f"PIL is_animated: {is_animated}")
                    n_frames = 1
                    if hasattr(img, "n_frames"):
                        n_frames = img.n_frames
                        print(f"PIL n_frames: {n_frames}")
                        
                    if is_animated or n_frames > 1:
                        print("PIL에서 WEBP 애니메이션으로 감지됨")
                        return 'webp_animation'
            except Exception as e:
                # PIL로 확인 실패 시 QImageReader 결과 사용
                print(f"PIL로 WEBP 확인 실패: {e}")
                pass
                
            # 애니메이션이 아닌 경우
            print("정적 WEBP 이미지로 감지됨")
            return 'webp_image'
        except Exception as e:
            # 오류 발생 시 기본값으로 정적 이미지 반환
            print(f"WEBP 분석 중 오류 발생: {e}")
            return 'webp_image' 