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
        except Exception as e:
            print(f"파일 확장자 확인 오류: {e}")
            return
            
        try:
            if file_ext == '.psd':
                # PSD 파일은 PSDHandler를 통해 다시 로드
                if hasattr(self.viewer, 'psd_handler'):
                    self.viewer.psd_handler.load(self.viewer.current_image_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.ico', '.heic', '.heif', '.tga']:
                # 일반 이미지는 ImageHandler를 통해 다시 로드
                if hasattr(self.viewer, 'image_handler'):
                    self.viewer.image_handler.load(self.viewer.current_image_path)
                    print(f"일반 이미지 회전 적용: {self._rotation_angle}°")
            elif file_ext == '.webp':
                # WEBP 일반 이미지 (AnimationHandler를 통해 처리)
                if hasattr(self.viewer, 'animation_handler'):
                    self.viewer.animation_handler.rotate_static_image(self.viewer.current_image_path)
                    print(f"WEBP 이미지 회전 AnimationHandler로 적용: {self._rotation_angle}°")
                else:
                    # 예전 방식 (직접 처리)
                    self._rotate_webp_directly()
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