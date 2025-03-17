"""
애니메이션 핸들러 모듈

이 모듈은 GIF 및 WEBP 애니메이션 처리를 담당합니다.
애니메이션 로딩, 크기 조정, 프레임 이동, 재생/정지 등의 기능을 제공합니다.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QMovie, QImageReader, QPixmap, QImage, QTransform
from PyQt5.QtCore import Qt, QTimer, QSize

class AnimationHandler:
    """
    GIF 및 WEBP 애니메이션을 처리하는 클래스
    """
    
    def __init__(self, image_label, parent=None):
        """
        애니메이션 핸들러 초기화
        
        Args:
            image_label (QLabel): 애니메이션을 표시할 레이블
            parent: 부모 객체 (일반적으로 ImageViewer)
        """
        self.image_label = image_label
        self.parent = parent
        self.current_movie = None
        self.animation_timer = None
        self.timers = []  # 타이머 관리 리스트
        self.current_rotation = 0
        self.is_dragging = False  # 슬라이더 드래그 상태
    
    def load_gif(self, file_path):
        """
        GIF 파일을 로드하고 표시합니다.
        
        Args:
            file_path (str): GIF 파일 경로
            
        Returns:
            str: 미디어 타입 ('gif_animation' 또는 'gif_image')
        """
        # GIF 파일 확인
        reader = QImageReader(file_path)
        media_type = 'gif_image'  # 기본값은 정적 이미지
        
        # 기존 리소스 정리
        self.cleanup()
        
        # 애니메이션 지원 여부 확인
        if reader.supportsAnimation():
            # 프레임 수가 1개 이상인지 확인 (애니메이션인지)
            frame_count = reader.imageCount()
            if frame_count > 1:
                media_type = 'gif_animation'
                
                # QMovie로 GIF 로드
                self.current_movie = QMovie(file_path)
                self.current_movie.setCacheMode(QMovie.CacheAll)
                self.current_movie.jumpToFrame(0)
                
                # 회전 처리
                if self.current_rotation != 0:
                    # 회전을 위한 변환 행렬 설정
                    transform = QTransform().rotate(self.current_rotation)
                    
                    # 프레임 변경 시 회전을 적용하는 함수 연결
                    def frame_changed(frame_number):
                        if not self.image_label:
                            return
                            
                        # 현재 프레임 가져오기
                        current_pixmap = self.current_movie.currentPixmap()
                        if current_pixmap and not current_pixmap.isNull():
                            # 프레임 회전
                            rotated_pixmap = current_pixmap.transformed(transform, Qt.SmoothTransformation)
                            
                            # 화면에 맞게 크기 조절
                            label_size = self.image_label.size()
                            scaled_pixmap = rotated_pixmap.scaled(
                                label_size,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                            
                            # 이미지 라벨에 표시
                            self.image_label.setPixmap(scaled_pixmap)
                    
                    # 프레임 변경 이벤트에 회전 함수 연결
                    self.current_movie.frameChanged.connect(frame_changed)
                    self.current_movie.start()
                    print(f"GIF에 회전 적용됨: {self.current_rotation}°")
                else:
                    # 회전이 없는 경우 일반적인 처리
                    self.scale_animation()
                    self.image_label.setMovie(self.current_movie)
                    self.current_movie.start()
                
                # 슬라이더 설정 및 타이머 설정
                if self.parent:
                    # 슬라이더 범위 설정
                    self.parent.playback_slider.setRange(0, frame_count - 1)
                    self.parent.playback_slider.setValue(0)
                    
                    # 슬라이더 시그널 연결
                    if hasattr(self.parent, 'disconnect_all_slider_signals'):
                        self.parent.disconnect_all_slider_signals()
                    
                    # 애니메이션 타이머 설정
                    self._setup_animation_timer(file_path)
                    
                    # 재생 버튼 상태 업데이트
                    if hasattr(self.parent, 'play_button'):
                        self.parent.play_button.setText("❚❚")  # 일시정지 아이콘 표시 (재생 중)
            else:
                # 단일 프레임 GIF 처리 (애니메이션 아님)
                self._handle_static_image(file_path)
        else:
            # 애니메이션을 지원하지 않는 경우 정적 이미지로 처리
            self._handle_static_image(file_path)
        
        return media_type
    
    def _handle_static_image(self, file_path):
        """정적 이미지 (애니메이션이 아닌 GIF/WEBP) 처리"""
        # 이미지 파일 로드
        image = QImage(file_path)
        if not image.isNull():
            pixmap = QPixmap.fromImage(image)
            
            # 회전 적용
            if self.current_rotation != 0:
                transform = QTransform().rotate(self.current_rotation)
                pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
            
            # 화면 크기에 맞게 이미지 조정 (비율 유지, 고품질 보간)
            if self.image_label:
                scaled_pixmap = pixmap.scaled(
                    self.image_label.width(),
                    self.image_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
        
        # 슬라이더 초기화 (정적 이미지인 경우)
        if self.parent:
            self.parent.playback_slider.setRange(0, 0)
            self.parent.playback_slider.setValue(0)
            self.parent.time_label.setText("00:00 / 00:00")
            self.parent.time_label.show()
    
    def _setup_animation_timer(self, file_path):
        """애니메이션 타이머 설정"""
        if not self.parent or not self.current_movie:
            return
            
        # 슬라이더 업데이트 함수
        def update_slider():
            if hasattr(self, 'current_movie') and self.current_movie:
                current_frame = self.current_movie.currentFrameNumber()
                if self.current_movie.state() == QMovie.Running:
                    self.parent.playback_slider.setValue(current_frame)
                    # 현재 프레임 / 총 프레임 표시 업데이트
                    self.parent.time_label.setText(f"{current_frame + 1} / {self.current_movie.frameCount()}")
        
        try:
            # 총 프레임 수와 애니메이션 속도 가져오기
            frame_count = self.current_movie.frameCount()
            animation_speed = self.current_movie.speed()  # 기본 속도는 100%
            
            # 프레임 지연 시간 계산 (근사값)
            reader = QImageReader(file_path)
            if reader.supportsAnimation() and frame_count > 0:
                # 첫 프레임 지연 시간 (밀리초)
                delay = reader.nextImageDelay()
                if delay <= 0:  # 유효하지 않은 경우 기본값 사용
                    delay = 100  # 기본값 100ms (약 10fps)
            else:
                delay = 100  # 정보를 얻을 수 없는 경우 기본값
            
            # 애니메이션 속도를 고려하여 지연 시간 조정
            timer_interval = int(delay * (100 / animation_speed))
            
            # 타이머 간격 범위 제한 (최소 10ms, 최대 200ms)
            timer_interval = max(10, min(timer_interval, 200))
        except Exception as e:
            print(f"GIF 프레임 레이트 계산 오류: {e}")
            timer_interval = 50  # 오류 발생 시 기본값 (50ms)
        
        # 타이머 생성 및 설정
        self.animation_timer = QTimer(self.parent)
        self.animation_timer.timeout.connect(update_slider)
        self.animation_timer.start(timer_interval)
        
        # 타이머 관리 리스트에 추가
        self.timers.append(self.animation_timer)
        
        # 부모 객체의 타이머 관리 리스트에도 추가
        if hasattr(self.parent, 'timers'):
            self.parent.timers.append(self.animation_timer)
            
        # 슬라이더 시그널 연결
        if hasattr(self.parent, 'playback_slider'):
            self.parent.playback_slider.valueChanged.connect(self.seek_to_frame)
            self.parent.playback_slider.sliderPressed.connect(self._slider_pressed)
            self.parent.playback_slider.sliderReleased.connect(self._slider_released)
    
    def load_webp(self, file_path):
        """
        WEBP 파일을 로드하고 표시합니다.
        
        Args:
            file_path (str): WEBP 파일 경로
            
        Returns:
            str: 미디어 타입 ('webp_animation' 또는 'webp_image')
        """
        # WEBP 파일 확인
        reader = QImageReader(file_path)
        media_type = 'webp_image'  # 기본값은 정적 이미지
        
        # 기존 리소스 정리
        self.cleanup()
        
        # 애니메이션 지원 여부 확인
        if reader.supportsAnimation():
            # 프레임 수가 1개 이상인지 확인 (애니메이션인지)
            frame_count = reader.imageCount()
            if frame_count > 1:
                media_type = 'webp_animation'
                
                # QMovie로 WEBP 로드
                self.current_movie = QMovie(file_path)
                self.current_movie.setCacheMode(QMovie.CacheAll)
                self.current_movie.jumpToFrame(0)
                
                # 회전 처리
                if self.current_rotation != 0:
                    # 회전을 위한 변환 행렬 설정
                    transform = QTransform().rotate(self.current_rotation)
                    
                    # 프레임 변경 시 회전을 적용하는 함수 연결
                    def frame_changed(frame_number):
                        if not self.image_label:
                            return
                            
                        # 현재 프레임 가져오기
                        current_pixmap = self.current_movie.currentPixmap()
                        if current_pixmap and not current_pixmap.isNull():
                            # 프레임 회전
                            rotated_pixmap = current_pixmap.transformed(transform, Qt.SmoothTransformation)
                            
                            # 화면에 맞게 크기 조절
                            label_size = self.image_label.size()
                            scaled_pixmap = rotated_pixmap.scaled(
                                label_size,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                            
                            # 이미지 라벨에 표시
                            self.image_label.setPixmap(scaled_pixmap)
                    
                    # 프레임 변경 이벤트에 회전 함수 연결
                    self.current_movie.frameChanged.connect(frame_changed)
                    self.current_movie.start()
                    print(f"WEBP에 회전 적용됨: {self.current_rotation}°")
                else:
                    # 회전이 없는 경우 일반적인 처리
                    self.scale_animation()
                    self.image_label.setMovie(self.current_movie)
                    self.current_movie.start()
                
                # 슬라이더 설정 및 타이머 설정
                if self.parent:
                    # 슬라이더 범위 설정
                    self.parent.playback_slider.setRange(0, frame_count - 1)
                    self.parent.playback_slider.setValue(0)
                    
                    # 슬라이더 시그널 연결
                    if hasattr(self.parent, 'disconnect_all_slider_signals'):
                        self.parent.disconnect_all_slider_signals()
                    
                    # 애니메이션 타이머 설정
                    self._setup_animation_timer(file_path)
                    
                    # 재생 버튼 상태 업데이트
                    if hasattr(self.parent, 'play_button'):
                        self.parent.play_button.setText("❚❚")  # 일시정지 아이콘 표시 (재생 중)
            else:
                # 단일 프레임 WEBP 처리 (애니메이션 아님)
                self._handle_static_image(file_path)
        else:
            # 애니메이션을 지원하지 않는 경우 정적 이미지로 처리
            self._handle_static_image(file_path)
        
        return media_type
    
    def scale_animation(self):
        """
        현재 로드된 애니메이션의 크기를 이미지 레이블에 맞게 조절합니다.
        
        Returns:
            bool: 성공 여부
        """
        # current_movie 속성이 있는지 확인
        if not hasattr(self, 'current_movie') or self.current_movie is None:
            return False
            
        try:
            # 현재 프레임 번호 저장
            current_frame = self.current_movie.currentFrameNumber()
            
            # 원본 크기와 표시 영역 크기 정보
            original_size = QSize(self.current_movie.currentImage().width(), self.current_movie.currentImage().height())
            label_size = self.image_label.size()
            
            # 높이가 0인 경우 예외 처리 (0으로 나누기 방지)
            if original_size.height() == 0:
                original_size.setHeight(1)
                
            # 화면 비율에 맞게 새 크기 계산
            if label_size.width() / label_size.height() > original_size.width() / original_size.height():
                # 세로 맞춤 (세로 기준으로 가로 계산)
                new_height = label_size.height()
                new_width = int(new_height * (original_size.width() / original_size.height()))
            else:
                # 가로 맞춤 (가로 기준으로 세로 계산)
                new_width = label_size.width()
                new_height = int(new_width * (original_size.height() / original_size.width()))
            
            # 애니메이션 크기 조정 및 원래 프레임으로 복원
            self.current_movie.setScaledSize(QSize(new_width, new_height))
            self.current_movie.jumpToFrame(current_frame)
            return True
        except Exception as e:
            print(f"애니메이션 크기 조정 중 오류 발생: {e}")
            return False
    
    def seek_to_frame(self, frame_number):
        """
        특정 프레임으로 이동합니다.
        
        Args:
            frame_number (int): 이동할 프레임 번호
            
        Returns:
            bool: 성공 여부
        """
        if hasattr(self, 'current_movie') and self.current_movie:
            try:
                self.current_movie.jumpToFrame(frame_number)
                return True
            except Exception as e:
                print(f"프레임 이동 중 오류 발생: {e}")
        return False
    
    def _slider_pressed(self):
        """슬라이더 드래그 시작 시 호출"""
        self.is_dragging = True
    
    def _slider_released(self):
        """슬라이더 드래그 종료 시 호출"""
        self.is_dragging = False
        if not self.current_movie:
            return
            
        # 현재 슬라이더 값으로 프레임 이동
        if hasattr(self.parent, 'playback_slider'):
            frame = self.parent.playback_slider.value()
            self.seek_to_frame(frame)
    
    def toggle_playback(self):
        """
        애니메이션 재생/일시정지를 토글합니다.
        
        Returns:
            bool: 현재 재생 상태 (True: 재생 중, False: 일시정지)
        """
        if hasattr(self, 'current_movie') and self.current_movie:
            try:
                # 현재 상태 확인
                is_paused = self.current_movie.state() != QMovie.Running
                # 상태 토글
                self.current_movie.setPaused(not is_paused)
                
                # 재생 버튼 상태 업데이트
                if hasattr(self.parent, 'play_button'):
                    if not is_paused:  # 재생 중 -> 일시정지로 변경
                        self.parent.play_button.setText("▶")  # 재생 아이콘 (현재 일시정지됨)
                    else:  # 일시정지 -> 재생으로 변경
                        self.parent.play_button.setText("❚❚")  # 일시정지 아이콘 (현재 재생 중)
                
                # 재생 상태 반환 (정지 상태의 반대)
                return not is_paused
            except Exception as e:
                print(f"애니메이션 재생 상태 토글 중 오류 발생: {e}")
        return False
    
    def cleanup(self):
        """
        리소스를 정리합니다. 애니메이션을 정지하고 메모리를 해제합니다.
        """
        # 타이머 정리
        for timer in self.timers:
            if timer and timer.isActive():
                timer.stop()
        self.timers.clear()
        
        # 현재 애니메이션 정리
        if self.current_movie:
            try:
                self.current_movie.stop()
                self.current_movie.deleteLater()
            except:
                pass
            self.current_movie = None 