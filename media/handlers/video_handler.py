"""
비디오 처리를 위한 핸들러 모듈

이 모듈은 비디오 파일을 로드하고 재생하기 위한
VideoHandler 클래스를 제공합니다.
"""

import os
import time
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel

from media.handlers.base_handler import MediaHandler
from core.utils.path_utils import get_app_directory

# MPV DLL 경로 설정 (mpv 모듈 import 전에 필수)
# main.py에서 이미 설정되었을 수 있지만, 모듈 단독 사용 시 필요
if 'mpv' not in globals():
    try:
        mpv_path = os.path.join(get_app_directory(), 'mpv')
        if os.path.exists(mpv_path):
            # 환경 변수 PATH에 추가
            os.environ["PATH"] = mpv_path + os.pathsep + os.environ["PATH"]
            # Windows에서는 os.add_dll_directory()가 더 확실한 방법
            if hasattr(os, 'add_dll_directory'):  # Python 3.8 이상에서만 사용 가능
                os.add_dll_directory(mpv_path)
        # MPV 모듈 import
        import mpv
    except ImportError as e:
        print(f"MPV 모듈 로드 실패: {e}")
        # 오류가 발생해도 모듈 정의는 필요
        mpv = None

class VideoHandler(MediaHandler):
    """
    비디오 처리를 위한 클래스
    
    비디오 파일을 로드하고 재생하는 기능을 제공합니다.
    
    Attributes:
        parent: 부모 위젯 (ArchiveSift 클래스의 인스턴스)
        display_label: 비디오를 표시할 QLabel 위젯
        mpv_player: libmpv 기반 비디오 플레이어
        is_playing: 현재 재생 중인지 여부
    """
    
    def __init__(self, parent, display_label):
        """
        VideoHandler 클래스 초기화
        
        Args:
            parent: 부모 위젯 (ArchiveSift 클래스의 인스턴스)
            display_label: 비디오를 표시할 QLabel 위젯
        """
        super().__init__(parent, display_label)
        self.mpv_player = None
        self.is_playing = False
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self._update_video_time)
        self.video_duration = 0
        self.video_position = 0

    def load(self, video_path):
        """
        비디오 파일을 로드합니다.
        
        Args:
            video_path: 로드할 비디오 파일 경로
            
        Returns:
            bool: 로드 성공 여부
        """
        if not os.path.exists(video_path):
            self.parent.show_message(f"파일을 찾을 수 없습니다: {video_path}")
            return False
        
        # 파일 확장자 추출
        filename = os.path.basename(video_path)
        extension = os.path.splitext(filename)[1].upper().lstrip('.')
        
        # 비디오 로딩 메시지 표시
        self.parent.show_message(f"{extension} 영상 로딩 시작: {filename}")
        
        # 로딩 인디케이터 표시
        self.parent.show_loading_indicator()
        
        try:
            # 기존 플레이어가 있으면 정리
            if self.mpv_player:
                self.unload()
            
            # MPV 플레이어 생성 및 설정
            self.mpv_player = mpv.MPV(
                wid=str(int(self.display_label.winId())),
                log_handler=print,
                ytdl=True,
                input_default_bindings=True, 
                input_vo_keyboard=True,
                hwdec='no'  # 하드웨어 가속 비활성화
            )
            
            # MPV 옵션 설정
            self.mpv_player.loop = True  # 비디오 반복 재생
            self.mpv_player.volume = 100  # 볼륨 100%로 설정
            self.mpv_player.seekable = True  # seek 가능하도록 설정
            
            # 회전 각도 설정 (parent에 current_rotation이 있다면)
            if hasattr(self.parent, 'current_rotation'):
                self.mpv_player['video-rotate'] = str(self.parent.current_rotation)
            
            # 비디오 파일 로드
            self.mpv_player.play(video_path)
            self.mpv_player.pause = True  # 일단 일시정지 상태로 시작
            self.is_playing = False
            
            # 비디오 정보를 가져오기 위한 콜백 설정
            self.mpv_player.observe_property("duration", self._on_duration_change)
            self.mpv_player.observe_property("time-pos", self._on_position_change)
            self.mpv_player.observe_property("eof-reached", self._on_video_end)
            
            # 현재 미디어 경로 저장
            self.current_media_path = video_path
            
            # 타이머 시작
            self.video_timer.start(100)  # 100ms 간격으로 업데이트
            
            # 현재 미디어 타입 설정
            self.parent.current_media_type = 'video'
            
            # 로딩 인디케이터 숨김
            self.parent.hide_loading_indicator()
            
            # 이미지 정보 업데이트 (현재 미디어 인덱스/총 갯수 등)
            if hasattr(self.parent, 'update_image_info'):
                self.parent.update_image_info()
            
            # 로드 완료 메시지
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            self.parent.show_message(f"{extension} 영상 로드 완료: {filename}, 크기: {file_size_mb:.2f}MB")
            
            # 재생 버튼 업데이트 (parent에 update_play_button 메서드가 있다면)
            if hasattr(self.parent, 'update_play_button'):
                self.parent.update_play_button()
            
            return True
            
        except Exception as e:
            self.parent.show_message(f"비디오 로드 중 오류 발생: {str(e)}")
            self.parent.hide_loading_indicator()
            return False

    def unload(self):
        """
        현재 로드된 비디오를 언로드합니다.
        """
        # MPV 플레이어 정지 (플레이어가 존재하는 경우)
        if self.mpv_player:
            try:
                # 플레이어가 재생 중인지 확인
                if self.mpv_player.playback_time is not None:
                    self.mpv_player.stop()  # 재생 중지
                    # mpv 속성 초기화
                    self.mpv_player.loop = False
                    self.mpv_player.mute = False
            except Exception as e:
                print(f"비디오 정지 에러: {e}")
        
        # 비디오 타이머 정지
        if self.video_timer.isActive():
            self.video_timer.stop()
        
        # 현재 미디어 경로 초기화
        self.current_media_path = None
        self.is_playing = False

    def _update_video_time(self):
        """
        비디오 재생 시간을 업데이트합니다.
        """
        if self.mpv_player:
            self.video_position = self.mpv_player.playback_time
            self.video_duration = self.mpv_player.duration

    def _on_duration_change(self, name, value):
        """
        비디오 재생 시간이 변경될 때 호출되는 콜백 함수
        
        Args:
            name: 속성 이름
            value: 변경된 값 (재생 시간)
        """
        self.video_duration = value

    def _on_position_change(self, name, value):
        """
        비디오 재생 위치가 변경될 때 호출되는 콜백 함수
        
        Args:
            name: 속성 이름
            value: 변경된 값 (재생 위치)
        """
        self.video_position = value

    def _on_video_end(self, name, value):
        """
        비디오 재생이 끝났을 때 호출되는 콜백 함수
        
        Args:
            name: 속성 이름
            value: 변경된 값 (비디오 종료 상태)
        """
        if value:  # 종료 상태가 참(True)인 경우에만 처리
            self.is_playing = False
            self.video_position = 0
            self.video_duration = 0
            self.video_timer.stop()
            
            # 비디오 종료 처리를 위한 on_video_end 메서드 호출
            self.on_video_end(name, value)

    def play(self):
        """
        비디오를 재생합니다.
        """
        if self.mpv_player:
            self.mpv_player.pause = False
            self.is_playing = True
            self.video_timer.start(100)

    def pause(self):
        """
        비디오를 일시정지합니다.
        """
        if self.mpv_player:
            self.mpv_player.pause = True
            self.is_playing = False
            self.video_timer.stop()

    def seek(self, position):
        """
        비디오를 특정 위치로 이동합니다.
        
        Args:
            position: 이동할 비디오 위치 (초 단위)
        """
        if self.mpv_player:
            try:
                # seek 함수 대신 command 메서드 사용 (더 안정적)
                self.mpv_player.command('seek', position, 'absolute')
                self.video_position = position
                print(f"비디오 위치 이동: {position}초")
            except Exception as e:
                print(f"비디오 위치 이동 오류: {e}")

    def get_duration(self):
        """
        비디오의 전체 재생 시간을 반환합니다.
        
        Returns:
            float: 비디오의 전체 재생 시간 (초 단위)
        """
        return self.video_duration

    def get_position(self):
        """
        비디오의 현재 재생 위치를 반환합니다.
        
        Returns:
            float: 비디오의 현재 재생 위치 (초 단위)
        """
        return self.video_position

    def is_video_playing(self):
        """
        비디오가 현재 재생 중인지 여부를 반환합니다.
        
        Returns:
            bool: 비디오가 현재 재생 중인지 여부
        """
        return self.is_playing

    def get_current_media_path(self):
        """
        현재 로드된 비디오 파일의 경로를 반환합니다.
        
        Returns:
            str: 현재 로드된 비디오 파일의 경로
        """
        return self.current_media_path

    def rotate(self, angle):
        """
        비디오의 회전 각도를 설정합니다.
        
        Args:
            angle: 설정할 회전 각도 (0, 90, 180, 270)
        """
        if self.mpv_player:
            try:
                self.mpv_player['video-rotate'] = str(angle)
                print(f"비디오 회전 즉시 적용: {angle}°")
            except Exception as e:
                print(f"비디오 회전 설정 오류: {e}")
                
    def set_volume(self, volume):
        """
        비디오의 볼륨을 설정합니다.
        
        Args:
            volume: 설정할 볼륨 (0-100)
        """
        if self.mpv_player:
            try:
                self.mpv_player.volume = volume
                print(f"비디오 볼륨 설정: {volume}")
                return True
            except Exception as e:
                print(f"비디오 볼륨 설정 오류: {e}")
                return False
        return False
        
    def toggle_mute(self):
        """
        비디오의 음소거 상태를 토글합니다.
        
        Returns:
            bool: 토글 후 음소거 상태 (True: 음소거, False: 음소거 해제)
        """
        if self.mpv_player:
            try:
                current_mute = self.mpv_player.mute
                self.mpv_player.mute = not current_mute
                print(f"음소거 상태 변경: {not current_mute}")
                return not current_mute
            except Exception as e:
                print(f"음소거 토글 오류: {e}")
                return None
        return None
        
    def is_muted(self):
        """
        현재 음소거 상태인지 확인합니다.
        
        Returns:
            bool: 음소거 상태 여부
        """
        if self.mpv_player:
            return self.mpv_player.mute
        return False
        
    def play_video(self, video_path):
        """비디오 파일을 재생합니다."""
        try:
            # 비디오 로드
            result = self.load(video_path)
            
            if result:
                # 현재 이미지 경로 및 미디어 타입 설정
                if self.parent:
                    self.parent.current_image_path = video_path
                    if hasattr(self.parent, 'state_manager') and self.parent.state_manager:
                        self.parent.state_manager.set_state("current_image_path", video_path)  # 상태 관리자 업데이트
                    self.parent.current_media_type = 'video'
                
                    # 슬라이더 초기화 및 설정
                    if hasattr(self.parent, 'playback_slider'):
                        self.parent.playback_slider.setRange(0, 0)  # 슬라이더 범위를 0으로 설정
                        self.parent.playback_slider.setValue(0)  # 슬라이더 초기값을 0으로 설정
                    
                    # 재생 버튼 상태 업데이트
                    if hasattr(self.parent, 'play_button'):
                        self.parent.play_button.set_play_state(True)  # 일시정지 아이콘으로 설정
                    
                    # 슬라이더에 비디오 컨트롤 연결
                    if hasattr(self.parent, 'playback_slider'):
                        self.parent.playback_slider.connect_to_video_control(
                            self.parent.seek_video,
                            self.parent.slider_pressed,
                            self.parent.slider_released,
                            self.parent.slider_clicked
                        )
                    
                    # 현재 볼륨 슬라이더 값 적용
                    if hasattr(self.parent, 'volume_slider'):
                        current_volume = self.parent.volume_slider.value()
                        # 비디오 로드 직후 볼륨 설정
                        print(f"[DEBUG] 비디오 로드 시 볼륨 적용: {current_volume}")
                        self.set_volume(current_volume)
                
                # 비디오 재생
                self.play()
                
                # 진행 중 로딩 표시기 숨기기
                if self.parent and hasattr(self.parent, 'hide_loading_indicator'):
                    self.parent.hide_loading_indicator()
                
                return True
            return False
        except Exception as e:
            print(f"비디오 재생 오류: {str(e)}")
            if self.parent and hasattr(self.parent, 'hide_loading_indicator'):
                self.parent.hide_loading_indicator()
            if self.parent and hasattr(self.parent, 'show_message'):
                self.parent.show_message(f"비디오를 재생할 수 없습니다: {str(e)}")
            return False 
            
    def stop_video_timer(self):
        """타이머를 중지하는 메서드입니다."""
        if self.video_timer.isActive():
            self.video_timer.stop()
            # parent가 있고 timers 리스트가 있다면 거기서도 제거
            if self.parent and hasattr(self.parent, 'timers') and self.video_timer in self.parent.timers:
                self.parent.timers.remove(self.video_timer)
                
    def on_video_end(self, name, value):
        """비디오가 종료될 때 호출되는 메서드입니다."""
        # 메인 스레드에서 안전하게 타이머를 중지하기 위해 QTimer.singleShot 사용
        QTimer.singleShot(0, self.stop_video_timer) 
        
    def stop_video(self):
        """비디오 재생 중지 및 관련 리소스 정리"""
        self.unload()
        # 슬라이더 값 초기화
        if self.parent and hasattr(self.parent, 'playback_slider'):
            self.parent.playback_slider.setValue(0)
        # 시간 표시 초기화
        if self.parent and hasattr(self.parent, 'time_label'):
            self.parent.time_label.setText("00:00 / 00:00")
            
    def cleanup_video_resources(self):
        """비디오 관련 리소스 정리"""
        # 비디오 재생 중지
        self.stop_video()
        return True
            
    def restore_video_state(self, was_playing, position):
        """비디오 재생 상태를 복구합니다"""
        try:
            # 위치 복구
            self.seek(position)
            
            # 재생 상태 복구
            if was_playing:
                self.play()
                if self.parent and hasattr(self.parent, 'update_play_button'):
                    self.parent.update_play_button()
            
            # 슬라이더 위치 업데이트 강제
            if self.parent and hasattr(self.parent, 'update_video_playback'):
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(50, self.parent.update_video_playback)
        except Exception as e:
            print(f"비디오 상태 복구 실패: {e}")
            
    def seek_video(self, value):
        """슬라이더 값에 따라 비디오 재생 위치를 변경합니다.
        
        Args:
            value: 슬라이더 값 (밀리초 단위)
        """
        try:
            if self.mpv_player:
                # 슬라이더 값을 초 단위로 변환 (value는 밀리초 단위)
                seconds = value / 1000.0  # 밀리초를 초 단위로 변환
                # seek 메서드를 사용하여 정확한 위치로 이동
                self.seek(seconds)
        except Exception as e:
            print(f"비디오 위치 이동 오류: {str(e)}")
            
    def update_video_playback(self):
        """비디오의 재생 위치에 따라 슬라이더 값과 시간 표시를 업데이트합니다."""
        if not self.parent or not hasattr(self.parent, 'is_slider_dragging') or self.parent.is_slider_dragging:
            return
            
        try:
            position = self.get_position()  # 현재 재생 위치
            duration = self.get_duration()  # 총 길이
            
            # 재생 위치 값이 None인 경우 처리
            if position is None:
                return  # 슬라이더 업데이트를 건너뜁니다.

            # 슬라이더 범위 설정
            if duration is not None and duration > 0 and hasattr(self.parent, 'playback_slider'):
                # 슬라이더 범위를 밀리초 단위로 설정 (1000으로 곱해서 더 세밀하게)
                self.parent.playback_slider.setRange(0, int(duration * 1000))
                
                # 현재 위치가 duration을 초과하면 0으로 리셋
                if position >= duration:
                    self.parent.playback_slider.setValue(0)
                    self.seek(0)
                else:
                    # 슬라이더 값을 밀리초 단위로 설정 (1000으로 곱해서 더 세밀하게)
                    self.parent.playback_slider.setValue(int(position * 1000))
                
                # time_label이 있는 경우 시간 표시 업데이트
                if hasattr(self.parent, 'time_label'):
                    # self의 format_time 메서드 사용
                    self.parent.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

            # 현재 위치를 이전 위치로 저장
            if hasattr(self.parent, 'previous_position'):
                self.parent.previous_position = position

        except Exception as e:
            print(f"비디오 업데이트 에러: {e}")
            # 타이머가 활성화되어 있으면 중지
            if hasattr(self.parent, 'video_timer') and self.parent.video_timer.isActive():
                self.parent.video_timer.stop()  # 타이머 중지 
                
    def format_time(self, seconds):
        """
        초를 'MM:SS' 형식으로 변환합니다.
        
        Args:
            seconds (float): 변환할 시간(초)
            
        Returns:
            str: 'MM:SS' 형식의 시간 문자열
        """
        # core.utils.time_utils의 format_time 함수 사용
        from core.utils.time_utils import format_time as utils_format_time
        return utils_format_time(seconds)
        
    def adjust_volume(self, volume):
        """
        비디오 볼륨을 조절합니다.
        
        Args:
            volume: 볼륨 값 (0-100)
            
        Returns:
            bool: 볼륨 설정 성공 여부
        """
        try:
            # 부모 객체가 있고 볼륨 슬라이더가 있는 경우 현재 슬라이더 값을 사용
            if self.parent and hasattr(self.parent, 'volume_slider'):
                volume_value = self.parent.volume_slider.value()
            else:
                volume_value = volume
                
            # set_volume 메서드를 사용하여 볼륨 설정
            success = self.set_volume(volume_value)
            
            if success:
                print(f"볼륨 설정 완료: {volume_value}")
            else:
                print(f"볼륨 설정 실패: {volume_value}")
                
            return success
        except Exception as e:
            print(f"볼륨 조절 오류: {e}")
            return False 
            
    def toggle_video_playback(self):
        """비디오 재생/일시정지를 토글합니다."""
        try:
            is_playing = self.is_video_playing()
            if is_playing:
                self.pause()  # 재생 중이면 일시정지
            else:
                self.play()  # 일시정지 중이면 재생
            
            # 버튼 상태 업데이트
            if self.parent and hasattr(self.parent, 'update_play_button'):
                self.parent.update_play_button()
                
            return True
        except Exception as e:
            print(f"비디오 재생/일시정지 토글 오류: {e}")
            return False 