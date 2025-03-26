"""
애니메이션 핸들러 모듈

이 모듈은 GIF 및 WEBP 애니메이션 처리를 담당합니다.
애니메이션 로딩, 크기 조정, 프레임 이동, 재생/정지 등의 기능을 제공합니다.
"""

from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtGui import QMovie, QImageReader, QPixmap, QImage, QTransform
from PyQt5.QtCore import Qt, QTimer, QSize, QObject, pyqtSignal
import os
import weakref

class AnimationHandler(QObject):
    """
    GIF 및 WEBP 애니메이션을 처리하는 클래스
    """
    
    # 재생 상태 변경 시그널 추가
    playback_state_changed = pyqtSignal(bool)  # True: 재생 중, False: 일시정지
    
    def __init__(self, image_label, parent=None):
        """
        애니메이션 핸들러 초기화
        
        Args:
            image_label (QLabel): 애니메이션을 표시할 레이블
            parent: 부모 객체 (일반적으로 ArchiveSift)
        """
        super(AnimationHandler, self).__init__(parent)
        self.image_label = image_label
        self.parent = parent
        self.current_movie = None
        self.animation_timer = None
        self.timers = []  # 타이머 관리 리스트
        self.current_rotation = 0
        self.is_dragging = False  # 슬라이더 드래그 상태
        self.current_frame_changed_handler = None  # 프레임 변경 핸들러 함수 저장
    
    def show_gif(self, image_path):
        """GIF 애니메이션을 표시합니다."""
        # AnimationHandler를 통해 GIF 로드
        self.load_gif(image_path)
        
        # 미디어 타입 설정
        if self.parent:
            self.parent.current_media_type = 'gif_animation'
            self.parent.current_image_path = image_path
    
    def show_webp(self, image_path):
        """WEBP 애니메이션을 표시합니다."""
        # AnimationHandler를 통해 WEBP 로드
        self.load_webp(image_path)
        
        # 미디어 타입 설정
        if self.parent:
            self.parent.current_media_type = 'webp_animation'
            self.parent.current_image_path = image_path
    
    def load_gif(self, file_path):
        """
        GIF 파일을 로드하고 표시합니다.
        
        Args:
            file_path (str): GIF 파일 경로
            
        Returns:
            str: 미디어 타입 ('gif_animation' 또는 'gif_image')
        """
        # 이전 핸들러 참조 초기화
        self.current_frame_changed_handler = None
        
        # 파일 크기 계산 (MB 단위)
        size_mb = 0
        try:
            if os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)  # 바이트 -> 메가바이트
        except Exception as e:
            print(f"파일 크기 계산 오류: {e}")
        
        # 로딩 인디케이터 표시
        if self.parent and hasattr(self.parent, 'show_loading_indicator'):
            self.parent.show_loading_indicator()
            filename = os.path.basename(file_path)
            self.parent.show_message(f"GIF 로딩 시작: {filename}")
        
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
                    
                    # 프레임 변경 시 회전을 적용하는 함수를 클래스 속성으로 저장
                    self.current_frame_changed_handler = lambda frame_number: self._handle_rotated_frame(frame_number, transform)
                    
                    # 프레임 변경 이벤트에 회전 함수 연결
                    self.current_movie.frameChanged.connect(self.current_frame_changed_handler)
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
        
        # 로딩 인디케이터 숨김
        if self.parent and hasattr(self.parent, 'hide_loading_indicator'):
            self.parent.hide_loading_indicator()
            filename = os.path.basename(file_path)
            # 애니메이션인 경우에도 프레임 수 정보 제거
            if media_type == 'gif_animation':
                self.parent.show_message(f"GIF 이미지 로드 완료: {filename}, 크기: {size_mb:.2f}MB")
            else:
                self.parent.show_message(f"GIF 이미지 로드 완료: {filename}, 크기: {size_mb:.2f}MB")
        
        # 이미지 정보 업데이트 (현재 미디어 인덱스/총 갯수 등)
        if self.parent and hasattr(self.parent, 'update_image_info'):
            self.parent.update_image_info()
        
        return media_type
    
    def load_webp(self, file_path):
        """
        WEBP 파일을 로드하고 표시합니다.
        
        Args:
            file_path (str): WEBP 파일 경로
            
        Returns:
            str: 미디어 타입 ('webp_animation' 또는 'webp_image')
        """
        # 이전 핸들러 참조 초기화
        self.current_frame_changed_handler = None
        
        # 파일 크기 계산 (MB 단위)
        size_mb = 0
        try:
            if os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)  # 바이트 -> 메가바이트
        except Exception as e:
            print(f"파일 크기 계산 오류: {e}")
        
        # 로딩 인디케이터 표시
        if self.parent and hasattr(self.parent, 'show_loading_indicator'):
            self.parent.show_loading_indicator()
            filename = os.path.basename(file_path)
            self.parent.show_message(f"WEBP 로딩 시작: {filename}")
        
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
                    
                    # 프레임 변경 시 회전을 적용하는 함수를 클래스 속성으로 저장
                    self.current_frame_changed_handler = lambda frame_number: self._handle_rotated_frame(frame_number, transform)
                    
                    # 프레임 변경 이벤트에 회전 함수 연결
                    self.current_movie.frameChanged.connect(self.current_frame_changed_handler)
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
                print("단일 프레임 WEBP 이미지 처리 시작")
                self._handle_static_image(file_path)
                media_type = 'webp_image'
        else:
            # 애니메이션을 지원하지 않는 경우 정적 이미지로 처리
            print("정적 WEBP 이미지 처리 시작")
            self._handle_static_image(file_path)
            media_type = 'webp_image'
        
        # 로딩 인디케이터 숨김
        if self.parent and hasattr(self.parent, 'hide_loading_indicator'):
            self.parent.hide_loading_indicator()
            filename = os.path.basename(file_path)
            # 애니메이션인 경우에도 프레임 수 정보 제거
            if media_type == 'webp_animation':
                self.parent.show_message(f"WEBP 이미지 로드 완료: {filename}, 크기: {size_mb:.2f}MB")
            else:
                self.parent.show_message(f"WEBP 이미지 로드 완료: {filename}, 크기: {size_mb:.2f}MB")
        
        # 이미지 정보 업데이트 (현재 미디어 인덱스/총 갯수 등)
        if self.parent and hasattr(self.parent, 'update_image_info'):
            self.parent.update_image_info()
        
        return media_type
    
    def scale_animation(self):
        """
        애니메이션 크기를 조정합니다. QMovie 객체가 이미지 라벨 크기에 맞게 스케일링됩니다.
        현재 프레임과 재생 상태를 유지합니다.
        """
        if not self.current_movie:
            return False
            
        try:
            # 현재 재생 상태 저장
            was_running = (self.current_movie.state() == QMovie.Running)
            
            # 현재 프레임 번호 저장
            current_frame = self.current_movie.currentFrameNumber()
            
            # 원본 크기와 표시 영역 크기 정보
            original_size = QSize(self.current_movie.currentImage().width(), self.current_movie.currentImage().height())
            if not self.image_label:
                return False
                
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
            
            # 원래 재생 상태로 복원
            if was_running and self.current_movie.state() != QMovie.Running:
                self.current_movie.start()
                print("애니메이션 리사이징 후 재생 재개")
                
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
                
                # 상태가 변경되었음을 알리는 시그널 발생
                is_playing = not is_paused
                self.playback_state_changed.emit(is_playing)
                
                # 재생 상태 반환 (정지 상태의 반대)
                return is_playing
            except Exception as e:
                print(f"애니메이션 재생 상태 토글 중 오류 발생: {e}")
        return False
    
    def cleanup(self):
        """
        리소스를 정리합니다. 애니메이션을 정지하고 메모리를 해제합니다.
        """
        print("애니메이션 핸들러 리소스 정리 시작...")
        
        # 이미지 라벨 초기화를 명시적으로 수행
        if hasattr(self, 'image_label') and self.image_label:
            try:
                # 이미지 라벨에서 QMovie 참조 제거 (순서 중요: 먼저 setMovie(None), 그 다음 clear)
                self.image_label.setMovie(None)
                self.image_label.clear()
                
                # 이벤트 처리 강제로 수행하여 UI 갱신 (중요)
                QApplication.processEvents()
                print("이미지 라벨 초기화 완료")
            except Exception as e:
                print(f"이미지 라벨 정리 중 오류: {e}")
                
        # 애니메이션 타이머 별도 정리 (첫번째로 정리해야 함)
        if hasattr(self, 'animation_timer') and self.animation_timer:
            try:
                print("애니메이션 타이머 정리 시작...")
                if self.animation_timer.isActive():
                    print("활성화된 타이머 중지")
                    self.animation_timer.stop()
                
                # 연결된 모든 슬롯 해제
                try:
                    print("타이머 timeout 시그널에서 _update_slider_timer 메서드 연결 해제 시도")
                    self.animation_timer.timeout.disconnect(self._update_slider_timer)
                    print("특정 슬롯에서 타이머 연결 해제 성공")
                except TypeError:
                    # 연결된 슬롯이 없을 경우 발생하는 예외 무시
                    print("타이머에 연결된 특정 슬롯이 없음, 모든 슬롯 연결 해제 시도")
                    try:
                        self.animation_timer.timeout.disconnect()
                        print("모든 슬롯 연결 해제 성공")
                    except TypeError:
                        print("타이머에 연결된 슬롯이 없음")
                    
                # 부모의 타이머 목록에서 제거
                if hasattr(self.parent, 'timers') and self.animation_timer in self.parent.timers:
                    self.parent.timers.remove(self.animation_timer)
                    print("부모 객체의 타이머 목록에서 제거 완료")
                
                # 삭제 예약
                self.animation_timer.deleteLater()
                # 이벤트 처리 강제로 수행하여 삭제 요청 처리
                QApplication.processEvents()
                self.animation_timer = None
                print("애니메이션 타이머 삭제 예약 완료")
            except Exception as e:
                print(f"애니메이션 타이머 정리 중 오류: {e}")
                # 오류가 발생해도 참조는 해제
                self.animation_timer = None
        
        # 다른 모든 타이머 정리
        for timer in self.timers:
            if timer and timer is not self.animation_timer:  # animation_timer는 이미 처리했으므로 건너뜀
                try:
                    if timer.isActive():
                        timer.stop()
                    
                    # 연결된 모든 시그널 해제
                    try:
                        timer.timeout.disconnect()
                    except TypeError:
                        pass  # 연결된 시그널이 없을 경우
                        
                    # 부모의 타이머 목록에서도 제거
                    if hasattr(self.parent, 'timers') and timer in self.parent.timers:
                        self.parent.timers.remove(timer)
                    
                    timer.deleteLater()
                    # 각 타이머마다 이벤트 처리
                    QApplication.processEvents()
                except Exception as e:
                    print(f"타이머 정리 중 오류: {e}")
        
        # 타이머 리스트 초기화
        self.timers.clear()
        
        # 현재 애니메이션 정리
        if self.current_movie:
            try:
                # 애니메이션 정지
                self.current_movie.stop()
                
                # 이미지 라벨과의 연결 해제 (이미 위에서 처리했으므로 중복 코드 제거)
                
                # 저장된 프레임 변경 핸들러가 있으면 명시적으로 연결 해제
                if hasattr(self, 'current_frame_changed_handler') and self.current_frame_changed_handler:
                    try:
                        print("프레임 변경 핸들러 연결 해제 시도...")
                        # 시그널이 여전히 연결되어 있는지 먼저 확인
                        is_connected = False
                        try:
                            # disconnect 시도로 확인
                            self.current_movie.frameChanged.disconnect(self.current_frame_changed_handler)
                            is_connected = True
                        except (TypeError, RuntimeError):
                            # 이미 연결이 해제되었거나 연결이 없는 경우
                            print("프레임 변경 핸들러가 이미 연결 해제되었거나 연결되지 않았습니다.")
                            
                        if is_connected:
                            print("프레임 변경 핸들러 연결 해제 완료")
                        
                        # 참조 해제
                        self.current_frame_changed_handler = None
                    except Exception as e:
                        print(f"프레임 변경 핸들러 연결 해제 중 예상치 못한 오류: {e}")
                        # 참조는 여전히 해제
                        self.current_frame_changed_handler = None
                else:
                    print("저장된 프레임 변경 핸들러가 없습니다.")
                
                # QMovie에 연결된 모든 시그널 해제
                try:
                    print("QMovie의 모든 시그널 연결 해제 시도...")
                    
                    # 각 시그널의 모든 연결을 더 안전하게 해제
                    signal_names = {
                        "frameChanged": self.current_movie.frameChanged,
                        "stateChanged": self.current_movie.stateChanged,
                        "error": self.current_movie.error,
                        "finished": self.current_movie.finished,
                        "started": self.current_movie.started
                    }
                    
                    for name, signal in signal_names.items():
                        try:
                            signal.disconnect()
                            print(f"시그널 '{name}'의 모든 연결 해제 성공")
                        except (TypeError, RuntimeError):
                            # 연결된 슬롯이 없거나 이미 연결 해제됨 - 오류 메시지 출력하지 않음
                            pass
                    
                    print("QMovie의 모든 시그널 연결 해제 완료")
                    
                except Exception as e:
                    print(f"QMovie 시그널 연결 해제 중 일반 오류: {e}")
                
                # 핸들러 참조 해제
                self.current_frame_changed_handler = None
                
                # 메모리 해제 요청
                if self.current_movie:
                    try:
                        self.current_movie.stop()  # 먼저 애니메이션 중지
                        self.current_movie.deleteLater()
                        # 이벤트 처리를 강제로 수행하여 삭제 요청 처리
                        QApplication.processEvents()
                        print("QMovie 객체 삭제 요청 완료")
                    except Exception as e:
                        print(f"QMovie 객체 삭제 요청 중 오류: {e}")
                
                # 부모 클래스에도 current_movie가 있을 수 있으므로 정리 요청
                if self.parent and hasattr(self.parent, 'current_movie'):
                    try:
                        if self.parent.current_movie == self.current_movie:
                            self.parent.current_movie = None
                            print("부모 객체의 QMovie 참조 해제 완료")
                    except Exception as e:
                        print(f"부모 객체의 QMovie 참조 해제 중 오류: {e}")
                
                print("애니메이션 리소스 정리 완료")
            except Exception as e:
                print(f"애니메이션 정리 중 오류 발생: {e}")
            
            # 참조 해제
            self.current_movie = None
            
            # 가비지 컬렉션 명시적 호출 - 두 번 연속 호출하여 효과 증대
            try:
                import gc
                gc.collect()
                # 이벤트 처리를 강제로 수행하여 가비지 컬렉션 결과 반영
                QApplication.processEvents()
                # 한번 더 수행
                gc.collect()
                QApplication.processEvents()
                print("가비지 컬렉션 실행 완료")
            except Exception as e:
                print(f"가비지 컬렉션 호출 중 오류: {e}")
                
        else:
            print("정리할 애니메이션 객체가 없습니다.")
    
    def rotate_static_image(self, file_path=None):
        """
        정적 이미지를 회전합니다.
        
        Args:
            file_path (str, optional): 이미지 파일 경로. 제공되지 않으면 현재 로드된 이미지 사용.
            
        Returns:
            bool: 회전 성공 여부
        """
        file_path = file_path or self.current_file_path
        if not file_path or not os.path.exists(file_path):
            print("회전할 이미지 파일이 없습니다.")
            return False
        
        # 이미지 로드
        image = QImage(file_path)
        if image.isNull():
            print("이미지 로드 실패")
            return False
            
        # 이미지를 QPixmap으로 변환
        pixmap = QPixmap.fromImage(image)
        
        # 회전 적용
        transform = QTransform().rotate(self.current_rotation)
        rotated_pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
        
        # 화면 크기에 맞게 이미지 조정
        if self.image_label:
            label_size = self.image_label.size()
            scaled_pixmap = rotated_pixmap.scaled(
                label_size.width(),
                label_size.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            # MediaDisplay의 display_pixmap 메서드 호출 (있는 경우)
            if hasattr(self.image_label, 'display_pixmap'):
                self.image_label.display_pixmap(scaled_pixmap, 'image')
            else:
                # 일반 QLabel인 경우 기존 방식으로 이미지 표시
                self.image_label.setPixmap(scaled_pixmap)
            
            print(f"회전된 이미지 표시 완료: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            
            # 이미지 정보 업데이트
            if self.parent and hasattr(self.parent, 'update_image_info'):
                self.parent.update_image_info()
                
            return True
        return False
    
    def _handle_static_image(self, file_path):
        """
        정적 이미지를 처리합니다.
        
        Args:
            file_path (str): 이미지 파일 경로
        """
        # 파일 크기 계산 (MB 단위)
        size_mb = 0
        try:
            if os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)  # 바이트 -> 메가바이트
        except Exception as e:
            print(f"파일 크기 계산 오류: {e}")
        
        # 로딩 시작 메시지 표시
        filename = os.path.basename(file_path)
        print(f"정적 이미지 로딩 시작: {filename}")
        
        # 이미지 로드
        image = QImage(file_path)
        if not image.isNull():
            # 회전 처리
            pixmap = QPixmap.fromImage(image)
            if self.current_rotation != 0:
                transform = QTransform().rotate(self.current_rotation)
                pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
            
            # 라벨 크기에 맞게 이미지 스케일링
            if self.image_label:
                label_size = self.image_label.size()
                scaled_pixmap = pixmap.scaled(
                    label_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                # MediaDisplay의 display_pixmap 메서드 호출 (있는 경우)
                if hasattr(self.image_label, 'display_pixmap'):
                    # 파일 확장자에 따라 미디어 타입 결정
                    if file_path.lower().endswith('.gif'):
                        media_type = 'gif_image'
                    elif file_path.lower().endswith('.webp'):
                        media_type = 'webp_image'
                    else:
                        media_type = 'image'
                    self.image_label.display_pixmap(scaled_pixmap, media_type)
                else:
                    # 일반 QLabel인 경우 기존 방식으로 이미지 표시
                    self.image_label.setPixmap(scaled_pixmap)
            
            # 이미지 정보 업데이트 (너비, 높이 등)
            if self.parent and hasattr(self.parent, 'update_image_info'):
                self.parent.update_image_info()
            
            # 로딩 완료 메시지
            file_type = "GIF" if file_path.lower().endswith('.gif') else "WEBP"
            self.parent.show_message(f"{file_type} 이미지 로드 완료: {filename}, 크기: {size_mb:.2f}MB")
        else:
            print(f"이미지 로드 실패: {file_path}")
            if self.parent:
                self.parent.show_message(f"이미지 로드 실패: {filename}")
        
        # 재생 슬라이더 초기화
        if self.parent and hasattr(self.parent, 'playback_slider'):
            self.parent.playback_slider.setValue(0)
        
        # 로딩 인디케이터 숨김
        if self.parent and hasattr(self.parent, 'hide_loading_indicator'):
            self.parent.hide_loading_indicator()
    
    def _update_slider_timer(self):
        """애니메이션 슬라이더 업데이트 메서드 - 타이머에 의해 호출됨"""
        try:
            # 객체가 유효한지 확인
            if self.current_movie and self.current_movie.state() == QMovie.Running:
                current_frame = self.current_movie.currentFrameNumber()
                if hasattr(self.parent, 'playback_slider'):
                    self.parent.playback_slider.setValue(current_frame)
                # 현재 프레임 / 총 프레임 표시 업데이트
                if hasattr(self.parent, 'time_label'):
                    self.parent.time_label.setText(f"{current_frame + 1} / {self.current_movie.frameCount()}")
        except Exception as e:
            # 오류 발생 시 타이머 중지
            print(f"슬라이더 업데이트 중 오류, 타이머를 중지합니다: {e}")
            try:
                if hasattr(self, 'animation_timer') and self.animation_timer and self.animation_timer.isActive():
                    self.animation_timer.stop()
            except Exception:
                pass
    
    def _setup_animation_timer(self, file_path):
        """애니메이션 타이머 설정"""
        if not self.parent or not self.current_movie:
            return
        
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
        
        # 이전 타이머가 있으면 정리
        if hasattr(self, 'animation_timer') and self.animation_timer:
            try:
                if self.animation_timer.isActive():
                    self.animation_timer.stop()
                # 연결된 모든 슬롯 해제
                try:
                    self.animation_timer.timeout.disconnect()
                except TypeError:
                    # 연결된 슬롯이 없을 경우 발생하는 예외 무시
                    pass
                
                self.animation_timer.deleteLater()
                # 타이머 목록에서 제거
                if self.animation_timer in self.timers:
                    self.timers.remove(self.animation_timer)
                # 부모의 타이머 목록에서도 제거
                if hasattr(self.parent, 'timers') and self.animation_timer in self.parent.timers:
                    self.parent.timers.remove(self.animation_timer)
            except Exception as e:
                print(f"타이머 정리 중 오류: {e}")
        
        # 타이머 생성 및 설정
        self.animation_timer = QTimer(self.parent)
        self.animation_timer.timeout.connect(self._update_slider_timer)
        self.animation_timer.start(timer_interval)
        
        # 타이머 관리 리스트에 추가
        self.timers.append(self.animation_timer)
        
        # 부모 객체의 타이머 관리 리스트에도 추가
        if hasattr(self.parent, 'timers'):
            self.parent.timers.append(self.animation_timer)
            
        # 슬라이더 시그널 연결 (ClickableSlider의 메서드 사용)
        if hasattr(self.parent, 'playback_slider'):
            # 슬라이더 신호를 애니메이션 핸들러 메서드에 연결
            self.parent.playback_slider.connect_to_animation_control(
                self.seek_to_frame,
                self._slider_pressed,
                self._slider_released
            )
    
    def is_playing(self):
        """
        현재 애니메이션이 재생 중인지 확인합니다.
        
        Returns:
            bool: 재생 중이면 True, 일시정지 또는 정지 상태면 False
        """
        if not self.current_movie:
            return False
            
        try:
            # QMovie.Running 상태이면 재생 중
            return self.current_movie.state() == QMovie.Running
        except Exception as e:
            print(f"재생 상태 확인 오류: {e}")
            return False
    
    def _handle_rotated_frame(self, frame_number, transform):
        """회전된 프레임을 처리하는 메서드"""
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
            
            # MediaDisplay의 display_pixmap 메서드 호출 (있는 경우)
            if hasattr(self.image_label, 'display_pixmap'):
                # 미디어 타입 감지 - current_movie의 파일명으로 판단
                if hasattr(self, 'current_file_path'):
                    file_path = self.current_file_path
                    if file_path and file_path.lower().endswith('.gif'):
                        media_type = 'gif_animation'
                    elif file_path and file_path.lower().endswith('.webp'):
                        media_type = 'webp_animation'
                    else:
                        media_type = 'animation'
                else:
                    media_type = 'animation'
                
                self.image_label.display_pixmap(scaled_pixmap, media_type)
            else:
                # 일반 QLabel인 경우 기존 방식으로 이미지 표시
                self.image_label.setPixmap(scaled_pixmap)
    
    def scale_webp(self):
        """WEBP 애니메이션 크기 조정"""
        if self.parent and self.parent.current_media_type == 'webp_animation':
            success = self.scale_animation()
            if success:
                print("WEBP 애니메이션 크기 조정 완료")
            else:
                print("WEBP 애니메이션 크기 조정 실패")
        return success
    
    def scale_gif(self):
        """GIF 애니메이션 크기 조정"""
        if self.parent and self.parent.current_media_type == 'gif_animation':
            success = self.scale_animation()
            if success:
                print("GIF 애니메이션 크기 조정 완료")
            else:
                print("GIF 애니메이션 크기 조정 실패")
        return success
    