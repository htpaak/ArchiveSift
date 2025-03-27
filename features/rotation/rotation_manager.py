"""
회전 상태 관리를 위한 모듈
"""
from PyQt5.QtGui import QTransform, QImage, QPixmap
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication

# 회전 상수 정의
ROTATE_0 = 0
ROTATE_90 = 90
ROTATE_180 = 180
ROTATE_270 = 270

class RotationManager(QObject):
    """
    이미지 회전 상태를 관리하는 클래스
    """
    # 회전 상태가 변경되었을 때 발생하는 시그널
    rotation_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        """
        RotationManager 초기화
        
        Args:
            parent: 부모 객체 (일반적으로 ArchiveSift)
        """
        super().__init__(parent)
        self._rotation_angle = ROTATE_0  # 현재 회전 각도
        self.viewer = parent  # 부모 객체 참조
    
    @property
    def rotation_angle(self):
        """현재 회전 각도 반환"""
        return self._rotation_angle
    
    def set_rotation(self, angle):
        """
        회전 각도 설정
        
        Args:
            angle: 회전 각도 (0, 90, 180, 270)
        """
        # 각도를 0, 90, 180, 270 중 하나로 정규화
        angle = angle % 360
        if angle not in (ROTATE_0, ROTATE_90, ROTATE_180, ROTATE_270):
            angle = ROTATE_0
            
        if self._rotation_angle != angle:
            self._rotation_angle = angle
            self.rotation_changed.emit(angle)
    
    def get_transform(self):
        """현재 회전 각도에 따른 QTransform 객체 반환"""
        transform = QTransform()
        transform.rotate(self._rotation_angle)
        return transform
    
    def rotate_clockwise(self):
        """시계 방향으로 90도 회전"""
        new_angle = (self._rotation_angle + 90) % 360
        self.set_rotation(new_angle)
        return self._rotation_angle
    
    def rotate_counterclockwise(self):
        """반시계 방향으로 90도 회전"""
        new_angle = (self._rotation_angle - 90) % 360
        self.set_rotation(new_angle)
        return self._rotation_angle
    
    def reset_rotation(self):
        """회전 각도를 0으로 리셋"""
        self.set_rotation(ROTATE_0)
        
    def apply_rotation(self, clockwise=True):
        """
        회전을 적용하고 현재 미디어에 따라 UI를 업데이트합니다.
        
        Args:
            clockwise (bool): 시계 방향 회전 여부
        """
        if not self.viewer or not hasattr(self.viewer, 'current_image_path') or not self.viewer.current_image_path:
            return
            
        # 회전 방향에 따라 회전 각도 변경
        if clockwise:
            self.rotate_clockwise()
        else:
            self.rotate_counterclockwise()
            
        # 뷰어의 current_rotation 속성 업데이트 (이전 코드와의 호환성)
        if hasattr(self.viewer, 'current_rotation'):
            self.viewer.current_rotation = self._rotation_angle
        
        # AnimationHandler에 회전 각도 전달
        if hasattr(self.viewer, 'animation_handler'):
            self.viewer.animation_handler.current_rotation = self._rotation_angle
        
        # 현재 미디어 타입에 따라 다르게 처리
        if not hasattr(self.viewer, 'current_media_type'):
            return
            
        media_type = self.viewer.current_media_type
        
        if media_type == 'image' or media_type == 'webp_image':
            self._rotate_static_image()
        elif media_type in ['gif_animation', 'webp_animation']:
            self._rotate_animation()
        elif media_type == 'video':
            self._rotate_video()
        
        # 회전 상태 메시지 표시
        self._show_rotation_message()
    
    def _rotate_static_image(self):
        """정적 이미지 회전 처리"""
        file_ext = ''
        try:
            import os
            file_ext = os.path.splitext(self.viewer.current_image_path)[1].lower()
            print(f"🔄 이미지 회전 시작: 파일={os.path.basename(self.viewer.current_image_path)}, 확장자={file_ext}, 회전각={self._rotation_angle}°")
        except Exception as e:
            print(f"파일 확장자 확인 오류: {e}")
            return
            
        try:
            # 화면 갱신 전 처리
            try:
                from PyQt5.QtWidgets import QApplication
                QApplication.instance().processEvents()
            except Exception as e:
                print(f"화면 갱신 중 오류: {e}")
            
            # 직접 이미지 파일 다시 처리하기 - 가장 효율적인 방법
            if hasattr(self.viewer, 'image_handler') and hasattr(self.viewer.image_handler, 'original_pixmap') and self.viewer.image_handler.original_pixmap:
                # 이미지 핸들러의 rotation_applied 플래그 초기화
                print(f"🔄 이미지 핸들러 rotation_applied 플래그 상태: {getattr(self.viewer.image_handler, 'rotation_applied', False)}")
                
                # 회전 적용 (원본 이미지에 직접 적용)
                if hasattr(self.viewer.image_handler, 'rotation_applied'):
                    # 원래 원본 이미지 복제 (필요한 경우)
                    if not hasattr(self.viewer.image_handler, '_plain_original_pixmap'):
                        self.viewer.image_handler._plain_original_pixmap = self.viewer.image_handler.original_pixmap.copy()
                    
                    # 저장된 원본 이미지가 있으면 그것을 사용하여 회전 적용
                    try:
                        transform = QTransform().rotate(self._rotation_angle)
                        rotated_pixmap = self.viewer.image_handler._plain_original_pixmap.transformed(transform, Qt.SmoothTransformation)
                        
                        # 회전된 이미지 저장 및 플래그 설정
                        self.viewer.image_handler.original_pixmap = rotated_pixmap
                        self.viewer.image_handler.rotation_applied = True
                        
                        # 이미지 리사이징 및 표시
                        self.viewer.image_handler._resize_and_display()
                        print(f"직접 원본 이미지에 회전 적용 성공: {self._rotation_angle}°")
                        
                        # 회전 처리 후 화면 업데이트 요청
                        print(f"🔄 이미지 회전 처리 후 화면 업데이트 요청")
                        try:
                            from PyQt5.QtWidgets import QApplication
                            QApplication.instance().processEvents()
                        except Exception as e:
                            print(f"화면 갱신 중 오류: {e}")
                        
                        # 이미지 라벨 갱신 요청
                        if hasattr(self.viewer, 'image_label') and hasattr(self.viewer.image_label, 'repaint'):
                            self.viewer.image_label.repaint()
                        
                        print(f"🔄 이미지 회전 처리 완료: 각도={self._rotation_angle}°")
                        return
                    except Exception as e:
                        print(f"원본 이미지 회전 중 오류: {e}")
            
            # 아래는 기존 코드 (위 방식이 실패할 경우 실행)
            if file_ext == '.psd':
                # PSD 파일은 PSDHandler를 통해 다시 로드
                if hasattr(self.viewer, 'psd_handler'):
                    print(f"🔄 PSD 이미지 회전: PSDHandler를 통해 다시 로드")
                    self.viewer.psd_handler.load(self.viewer.current_image_path)
                    print(f"PSD 이미지 회전 적용: {self._rotation_angle}°")
            elif file_ext == '.webp':
                # WEBP 일반 이미지 (AnimationHandler를 통해 처리)
                if hasattr(self.viewer, 'animation_handler'):
                    print(f"🔄 WEBP 이미지 회전: AnimationHandler를 통해 처리")
                    self.viewer.animation_handler.rotate_static_image(self.viewer.current_image_path)
                    print(f"WEBP 이미지 회전 AnimationHandler로 적용: {self._rotation_angle}°")
                else:
                    # 예전 방식 (직접 처리)
                    print(f"🔄 WEBP 이미지 회전: 직접 처리 방식 사용")
                    self._rotate_webp_directly()
            elif file_ext in standard_image_exts or file_ext in raw_image_exts:
                # 일반 이미지와 RAW 이미지 모두 ImageHandler를 통해 다시 로드
                if hasattr(self.viewer, 'image_handler'):
                    # 이미지 형식 결정
                    format_type = 'image'
                    if file_ext in raw_image_exts:
                        format_type = 'raw_image'
                    elif file_ext == '.avif':
                        format_type = 'avif'
                    
                    img_type = "일반" if file_ext in standard_image_exts else "RAW"
                    print(f"🔄 {img_type} 이미지 회전: ImageHandler.load_static_image 호출, 형식={format_type}")
                    
                    # load_static_image 메서드 호출 - load 대신
                    if hasattr(self.viewer.image_handler, 'load_static_image'):
                        self.viewer.image_handler.load_static_image(self.viewer.current_image_path, format_type, file_ext)
                    else:
                        self.viewer.image_handler.load(self.viewer.current_image_path)
                    
                    # 회전 후 이미지 다시 표시
                    if hasattr(self.viewer.image_handler, '_resize_and_display'):
                        print(f"🔄 이미지 회전 후 리사이징 적용")
                        self.viewer.image_handler._resize_and_display()
                    
                    print(f"{img_type} 이미지 회전 적용: {self._rotation_angle}°")
            else:
                # 알 수 없는 확장자는 기본적으로 ImageHandler로 처리 시도
                if hasattr(self.viewer, 'image_handler'):
                    # 알 수 없는 형식도 load_static_image 메서드로 처리
                    print(f"🔄 알 수 없는 이미지 유형 회전: ImageHandler.load_static_image 호출")
                    if hasattr(self.viewer.image_handler, 'load_static_image'):
                        self.viewer.image_handler.load_static_image(self.viewer.current_image_path, 'image', file_ext)
                    else:
                        self.viewer.image_handler.load(self.viewer.current_image_path)
                    
                    # 회전 후 이미지 다시 표시
                    if hasattr(self.viewer.image_handler, '_resize_and_display'):
                        print(f"🔄 알 수 없는 유형 이미지 회전 후 리사이징 적용")
                        self.viewer.image_handler._resize_and_display()
                    
                    print(f"알 수 없는 이미지 유형 회전 시도: {file_ext}, 각도: {self._rotation_angle}°")
            
            # 회전 처리 후 화면 업데이트 요청
            print(f"🔄 이미지 회전 처리 후 화면 업데이트 요청")
            try:
                from PyQt5.QtWidgets import QApplication
                QApplication.instance().processEvents()
            except Exception as e:
                print(f"화면 갱신 중 오류: {e}")
            
            # 이미지 라벨 갱신 요청
            if hasattr(self.viewer, 'image_label') and hasattr(self.viewer.image_label, 'repaint'):
                self.viewer.image_label.repaint()
            
            # 최종 이미지 업데이트
            try:
                from PyQt5.QtWidgets import QApplication
                QApplication.instance().processEvents()
            except Exception as e:
                print(f"화면 갱신 중 오류: {e}")
                
            print(f"🔄 이미지 회전 처리 완료: 각도={self._rotation_angle}°")
            
        except Exception as e:
            print(f"이미지 회전 중 오류 발생: {e}")
            if hasattr(self.viewer, 'show_message'):
                self.viewer.show_message(f"이미지 회전 중 오류 발생: {e}")
    
    def _rotate_webp_directly(self):
        """WEBP 이미지를 직접 회전하는 내부 메서드"""
        if not hasattr(self.viewer, 'current_image_path') or not hasattr(self.viewer, 'image_label'):
            return
            
        try:
            image = QImage(self.viewer.current_image_path)
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                transform = QTransform().rotate(self._rotation_angle)
                rotated_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
                
                # 회전된 이미지를 화면에 맞게 크기 조절
                label_size = self.viewer.image_label.size()
                scaled_pixmap = rotated_pixmap.scaled(
                    label_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.viewer.image_label.setPixmap(scaled_pixmap)
            print(f"WEBP 일반 이미지 회전 직접 적용: {self._rotation_angle}°")
        except Exception as e:
            print(f"WEBP 직접 회전 중 오류: {e}")
    
    def _rotate_animation(self):
        """애니메이션(GIF, WEBP) 회전 처리"""
        if not hasattr(self.viewer, 'animation_handler'):
            # AnimationHandler가 없는 경우 생성
            from media.handlers.animation_handler import AnimationHandler
            self.viewer.animation_handler = AnimationHandler(self.viewer.image_label, self.viewer)
            
            # 애니메이션 핸들러로 다시 로드
            if self.viewer.current_media_type == 'gif_animation':
                self.viewer.animation_handler.load_gif(self.viewer.current_image_path)
            elif self.viewer.current_media_type == 'webp_animation':
                self.viewer.animation_handler.load_webp(self.viewer.current_image_path)
            return
            
        try:
            # 현재 재생 상태 및 프레임 기억
            was_playing = self.viewer.animation_handler.is_playing()
            current_frame = 0
            
            if self.viewer.animation_handler.current_movie:
                current_frame = self.viewer.animation_handler.current_movie.currentFrameNumber()
            
            # 이미지 레이블 초기화 (중요: 깜빡임 방지)
            self.viewer.image_label.clear()
            
            # 애니메이션 핸들러 정리
            self.viewer.animation_handler.cleanup()
            
            # 이벤트 처리로 UI 갱신 시간 확보
            QApplication.processEvents()
            
            # AnimationHandler를 통해 다시 로드
            if self.viewer.current_media_type == 'gif_animation':
                self.viewer.animation_handler.load_gif(self.viewer.current_image_path)
            elif self.viewer.current_media_type == 'webp_animation':
                self.viewer.animation_handler.load_webp(self.viewer.current_image_path)
                
            # 프레임 및 재생 상태 복원
            if self.viewer.animation_handler.current_movie:
                if current_frame < self.viewer.animation_handler.current_movie.frameCount():
                    self.viewer.animation_handler.seek_to_frame(current_frame)
                
                # 재생 상태 복원
                if not was_playing:
                    self.viewer.animation_handler.current_movie.setPaused(True)
                    if hasattr(self.viewer, 'play_button'):
                        self.viewer.play_button.setText("▶")  # 재생 아이콘
        except Exception as e:
            print(f"애니메이션 회전 중 오류 발생: {e}")
            if hasattr(self.viewer, 'show_message'):
                self.viewer.show_message(f"애니메이션 회전 중 오류 발생: {e}")
    
    def _rotate_video(self):
        """비디오 회전 처리"""
        try:
            if hasattr(self.viewer, 'video_handler') and self.viewer.video_handler:
                # 비디오 핸들러의 rotate 메서드 호출
                self.viewer.video_handler.rotate(self._rotation_angle)
        except Exception as e:
            print(f"비디오 회전 중 오류 발생: {e}")
            if hasattr(self.viewer, 'show_message'):
                self.viewer.show_message(f"비디오 회전 중 오류 발생: {str(e)}")
    
    def _show_rotation_message(self):
        """회전 관련 메시지 표시"""
        if not hasattr(self.viewer, 'show_message'):
            return
            
        media_type = self.viewer.current_media_type if hasattr(self.viewer, 'current_media_type') else 'unknown'
        
        if media_type == 'video':
            self.viewer.show_message(f"비디오 회전: {self._rotation_angle}°")
        else:
            self.viewer.show_message(f"이미지 회전: {self._rotation_angle}°") 