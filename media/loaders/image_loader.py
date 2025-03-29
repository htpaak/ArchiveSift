# 이미지 로딩 모듈
# 이미지 파일을 별도의 스레드에서 불러오는 기능을 제공해요.
# 이 모듈은 큰 이미지 파일이나 특수 형식(PSD, GIF 등)의 이미지를 
# 프로그램을 멈추지 않고 효율적으로 로드할 수 있게 해줘요.

import os  # 파일 경로와 크기 확인을 위한 운영체제 모듈
from PyQt5.QtCore import QThread, pyqtSignal, QObject  # 스레드 생성과 신호 전달 기능
from PyQt5.QtGui import QPixmap, QImageReader  # 이미지 표시와 읽기 기능
from PIL import Image, ImageCms  # 다양한 이미지 형식 지원과 ICC 프로파일 처리
from io import BytesIO  # 메모리에 이미지 데이터를 저장하는 기능

class ImageLoader(QObject):
    """
    이미지 로더 스레드를 관리하는 클래스예요.
    
    이 클래스는 여러 이미지 로더 스레드를 추적하고 관리해요.
    불필요한 로더를 취소하거나 새 로더를 시작할 수 있어요.
    """
    
    def __init__(self):
        """이미지 로더 매니저 초기화"""
        super().__init__()
        self.loader_threads = {}  # 경로: 로더 스레드
    
    def start_loading(self, image_path, file_type='image'):
        """
        이미지 로딩을 시작합니다.
        
        매개변수:
            image_path: 로드할 이미지 파일 경로
            file_type: 파일 타입 ('image', 'psd', 'gif' 등)
            
        반환값:
            loader: 생성된 ImageLoaderThread 인스턴스
        """
        # 이미 로딩 중인지 확인
        if image_path in self.loader_threads and self.loader_threads[image_path].isRunning():
            pass
            # print(f"이미 로딩 중인 이미지: {os.path.basename(image_path)}")
            return self.loader_threads[image_path]
        
        # 새 로더 생성
        loader = ImageLoaderThread(image_path, file_type)
        self.loader_threads[image_path] = loader
        loader.start()
        
        return loader
    
    def cancel_loading(self, image_path):
        """
        특정 이미지의 로딩을 취소합니다.
        
        매개변수:
            image_path: 취소할 이미지 경로
        """
        if image_path in self.loader_threads and self.loader_threads[image_path].isRunning():
            try:
                self.loader_threads[image_path].terminate()
                self.loader_threads[image_path].wait(100)  # 최대 100ms 대기
                pass
                # print(f"이미지 로딩 취소: {os.path.basename(image_path)}")
            except Exception as e:
                pass
                # print(f"로딩 취소 실패: {e}")
            finally:
                del self.loader_threads[image_path]
    
    def cancel_pending_loaders(self, current_path=None):
        """
        현재 로딩 중인 이미지를 제외한 모든 로더 스레드를 취소합니다.
        
        매개변수:
            current_path: 취소하지 않을 현재 이미지 경로 (있는 경우)
        """
        for path, loader in list(self.loader_threads.items()):
            if (current_path is None or path != current_path) and loader.isRunning():
                try:
                    loader.terminate()
                    loader.wait(100)  # 최대 100ms 대기
                except Exception as e:
                    pass
                    # print(f"로딩 취소 실패: {e}")
                del self.loader_threads[path]
                pass
                # print(f"이미지 로딩 취소: {os.path.basename(path)}")
    
    def cleanup(self):
        """모든 로더 스레드를 취소하고 정리합니다."""
        for path, loader in list(self.loader_threads.items()):
            if loader.isRunning():
                try:
                    loader.terminate()
                    loader.wait(100)
                except:
                    pass
                # print(f"이미지 로딩 취소 (정리): {os.path.basename(path)}")
        self.loader_threads.clear()
    
    def is_loading(self, image_path):
        """특정 이미지가 현재 로딩 중인지 확인합니다."""
        return image_path in self.loader_threads and self.loader_threads[image_path].isRunning()
    
    def get_active_loaders_count(self):
        """현재 활성화된 로더 수를 반환합니다."""
        return sum(1 for loader in self.loader_threads.values() if loader.isRunning())

class ImageLoaderThread(QThread):
    """
    이미지를 별도의 스레드에서 로드하는 클래스예요.
    
    이 클래스는 프로그램이 멈추지 않고 이미지를 불러올 수 있게 해줘요.
    큰 이미지나 PSD 파일 같은 복잡한 이미지를 열 때 유용해요.
    
    신호(Signals):
        loaded: 이미지 로딩이 완료되면 발생 (경로, 이미지, 크기)
        error: 오류 발생 시 발생 (경로, 오류 메시지)
    """
    # 작업 완료 시 발생하는 신호 (경로, 픽스맵, 크기)
    loaded = pyqtSignal(str, object, float)
    error = pyqtSignal(str, str)  # 오류 발생 시 신호 (경로, 오류 메시지)
    
    def __init__(self, image_path, file_type='image'):
        """
        이미지 로더 스레드 초기화
        
        매개변수:
            image_path: 로드할 이미지 파일 경로
            file_type: 파일 타입 ('image', 'psd', 'gif' 등)
        """
        super().__init__()
        self.image_path = image_path
        self.file_type = file_type  # 'image', 'psd', 'gif' 등
        
    def run(self):
        """
        스레드 실행 함수 - 이미지를 실제로 로드해요.
        
        이미지 타입에 따라 다른 방식으로 로드하고,
        완료되면 loaded 신호를 발생시켜요.
        오류가 발생하면 error 신호를 발생시켜요.
        """
        try:
            if self.file_type == 'psd':
                # PSD 파일 로딩 로직
                from PIL import Image, ImageCms
                from io import BytesIO
                
                # PSD 파일을 PIL Image로 열기
                pass
                # print(f"PSD 파일 로딩 시작: {self.image_path}")
                
                # 이미지 크기 사전 확인 (매우 큰 이미지인 경우 축소 사본 사용)
                try:
                    with Image.open(self.image_path) as preview_img:
                        original_width, original_height = preview_img.size
                        original_size_mb = (original_width * original_height * 4) / (1024 * 1024)
                        
                        # 너무 큰 파일은 축소하여 로드 (100MB 이상 이미지)
                        if original_size_mb > 100:
                            # 크기를 조정하여 다시 로드 (1/2 크기로 로드)
                            max_size = (original_width // 2, original_height // 2)
                            image = Image.open(self.image_path)
                            image.thumbnail(max_size, Image.LANCZOS)
                            pass
                            # print(f"대형 PSD 파일 크기 조정: {original_size_mb:.2f}MB → 약 {original_size_mb/4:.2f}MB")
                        else:
                            image = Image.open(self.image_path)
                except Exception as e:
                    # 미리보기 로드 실패 시 일반적인 방법으로 로드
                    pass
                    # print(f"이미지 크기 확인 실패: {e}")
                    image = Image.open(self.image_path)
                
                # RGB 모드로 변환
                if image.mode != 'RGB':
                    pass
                    # print(f"이미지 모드 변환: {image.mode} → RGB")
                    image = image.convert('RGB')
                
                # ICC 프로파일 처리
                if 'icc_profile' in image.info:
                    try:
                        pass
                        # print("ICC 프로파일 변환 중...")
                        srgb_profile = ImageCms.createProfile('sRGB')
                        icc_profile = BytesIO(image.info['icc_profile'])
                        image = ImageCms.profileToProfile(
                            image,
                            ImageCms.ImageCmsProfile(icc_profile),
                            ImageCms.ImageCmsProfile(srgb_profile),
                            outputMode='RGB'
                        )
                    except Exception as icc_e:
                        pass
                        # print(f"ICC 프로파일 변환 실패: {icc_e}")
                        image = image.convert('RGB')
                
                # 변환된 이미지를 QPixmap으로 변환
                buffer = BytesIO()
                pass
                # print("이미지를 PNG로 변환하는 중...")
                
                # 메모리 사용량 최적화 - 압축률 조정 (0이 최소 압축, 9가 최대 압축)
                compression_level = 6  # 기본값 6: 속도와 크기의 균형
                image.save(buffer, format='PNG', compress_level=compression_level, icc_profile=None)
                pixmap = QPixmap()
                
                buffer_value = buffer.getvalue()
                pass
                # print(f"Buffer 크기: {len(buffer_value) / 1024:.2f} KB")
                
                if not pixmap.loadFromData(buffer_value):
                    raise ValueError("Unable to load image data into QPixmap")
                    
                buffer.close()
                pass
                # print("PSD 변환 완료")
                
            else:  # 일반 이미지
                pass
                # print(f"일반 이미지 로딩 시작: {self.image_path}")
                
                # 파일 크기 확인
                file_size_mb = os.path.getsize(self.image_path) / (1024 * 1024)
                
                # 이미지 크기에 따라 로딩 방식 변경
                if file_size_mb > 30:  # 30MB보다 큰 이미지
                    reader = QImageReader(self.image_path)
                    # 품질 우선순위를 속도로 설정
                    reader.setQuality(25)  # 25% 품질 (더 빠른 로딩)
                    image = reader.read()
                    pixmap = QPixmap.fromImage(image)
                else:
                    # 일반적인 방식으로 이미지 로드
                    pixmap = QPixmap(self.image_path)
            
            if not pixmap.isNull():
                # 메모리 사용량 계산
                img_size_mb = (pixmap.width() * pixmap.height() * 4) / (1024 * 1024)
                # 로딩 완료 신호 발생
                self.loaded.emit(self.image_path, pixmap, img_size_mb)
            else:
                self.error.emit(self.image_path, "Image data is invalid")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            pass
            # print(f"이미지 로딩 오류: {e}\n{error_details}")
            self.error.emit(self.image_path, str(e))
