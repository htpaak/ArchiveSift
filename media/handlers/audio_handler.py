"""
오디오 처리를 위한 핸들러 모듈

이 모듈은 오디오 파일을 로드하고 재생하기 위한
AudioHandler 클래스를 제공합니다.
"""

import os
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
        # 오류가 발생해도 모듈 정의는 필요
        mpv = None

class AudioHandler(MediaHandler):
    """
    오디오 처리를 위한 클래스
    
    오디오 파일을 로드하고 재생하는 기능을 제공합니다.
    
    Attributes:
        parent: 부모 위젯 (ArchiveSift 클래스의 인스턴스)
        display_label: 오디오를 표시할 QLabel 위젯
        mpv_player: libmpv 기반 오디오 플레이어
        is_playing: 현재 재생 중인지 여부
    """
    
    def __init__(self, parent, display_label):
        """
        AudioHandler 클래스 초기화
        
        Args:
            parent: 부모 위젯 (ArchiveSift 클래스의 인스턴스)
            display_label: 오디오를 표시할 QLabel 위젯
        """
        super().__init__(parent, display_label)
        
        # 오디오 관련 변수 초기화
        self.mpv_player = None
        self.is_playing = False
        self.current_media_path = None
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self._update_audio_time)
        self.audio_duration = 0
        self.audio_position = 0

    def load(self, audio_path):
        """
        오디오 파일을 로드합니다.
        
        Args:
            audio_path: 로드할 오디오 파일 경로
            
        Returns:
            bool: 로드 성공 여부
        """
        if not os.path.exists(audio_path):
            self.parent.show_message(f"파일을 찾을 수 없습니다: {audio_path}")
            return False
        
        try:
            # 로딩 인디케이터 표시
            if hasattr(self.parent, 'show_loading_indicator'):
                self.parent.show_loading_indicator()
            
            # 기존 플레이어가 있으면 정리
            if self.mpv_player:
                self.unload()
            
            # MPV 플레이어 생성 및 설정
            self.mpv_player = mpv.MPV(
                log_handler=print,
                ytdl=True,
                input_default_bindings=True,
                input_vo_keyboard=True
            )
            
            # MPV 옵션 설정
            self.mpv_player.loop = True  # 오디오 반복 재생
            self.mpv_player.volume = 100  # 볼륨 100%로 설정
            self.mpv_player.seekable = True  # seek 가능하도록 설정
            
            # 오디오 파일 로드
            self.mpv_player.play(audio_path)
            self.mpv_player.pause = False  # 바로 재생 시작
            self.is_playing = True
            
            # 오디오 정보를 가져오기 위한 콜백 설정
            self.mpv_player.observe_property("duration", self._on_duration_change)
            self.mpv_player.observe_property("time-pos", self._on_position_change)
            self.mpv_player.observe_property("eof-reached", self._on_audio_end)
            
            # 현재 미디어 경로 저장
            self.current_media_path = audio_path
            
            # 타이머 시작
            self.audio_timer.start(100)  # 100ms 간격으로 업데이트
            
            # 오디오 파일 정보 표시
            filename = os.path.basename(audio_path)
            self.display_label.setText(f"🎵 오디오 파일: {filename}")
            self.display_label.setAlignment(Qt.AlignCenter)
            self.display_label.setStyleSheet("font-size: 18px; color: white; background-color: #2c3e50;")
            
            # 로딩 인디케이터 숨김
            if hasattr(self.parent, 'hide_loading_indicator'):
                self.parent.hide_loading_indicator()
            
            # 현재 미디어 타입 설정 (parent에 current_media_type이 있다면)
            if hasattr(self.parent, 'current_media_type'):
                self.parent.current_media_type = 'audio'
            
            # 타이머 객체를 부모의 타이머 목록에 추가 (parent에 timers가 있다면)
            if hasattr(self.parent, 'timers'):
                self.parent.timers.append(self.audio_timer)
            
            # 이미지 정보 업데이트 (현재 미디어 인덱스/총 갯수 등)
            if hasattr(self.parent, 'update_image_info'):
                self.parent.update_image_info()
            
            # 재생 버튼 업데이트 (parent에 update_play_button 메서드가 있다면)
            if hasattr(self.parent, 'update_play_button'):
                self.parent.update_play_button()
                
            return True
            
        except Exception as e:
            if hasattr(self.parent, 'show_message'):
                self.parent.show_message(f"오디오 로드 중 오류 발생: {str(e)}")
            if hasattr(self.parent, 'hide_loading_indicator'):
                self.parent.hide_loading_indicator()
            return False

    def play_audio(self, audio_path):
        """
        오디오 파일을 로드하고 재생합니다.
        
        Args:
            audio_path: 오디오 파일 경로
            
        Returns:
            bool: 재생 성공 여부
        """
        # 경로 확인
        if not os.path.exists(audio_path):
            self.parent.show_message(f"파일을 찾을 수 없습니다: {audio_path}")
            return False
            
        # 오디오 파일 로드
        if self.load(audio_path):
            # 로드 성공 시 재생 상태로 설정
            self.is_playing = True
            if self.mpv_player:
                self.mpv_player.pause = False
            return True
        else:
            # 로드 실패 시 오류 메시지
            self.parent.show_message(f"오디오 파일 로드 실패: {audio_path}")
            return False

    def stop_audio(self):
        """
        오디오 재생을 중지합니다.
        """
        if self.mpv_player:
            self.mpv_player.pause = True
        self.is_playing = False

    def unload(self):
        """
        현재 로드된 오디오를 언로드합니다.
        MediaHandler의 추상 메서드를 구현합니다.
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
                pass
            
            # mpv 플레이어 객체 정리
            try:
                self.mpv_player.terminate()
                self.mpv_player = None
            except Exception as e:
                pass
        
        # 오디오 타이머 정지
        if self.audio_timer.isActive():
            self.audio_timer.stop()
        
        # 표시 레이블 초기화
        if self.display_label:
            self.display_label.clear()
            # 배경색을 검은색으로 다시 설정
            self.display_label.setStyleSheet("background-color: #000000;")
        
        # 현재 미디어 경로 초기화
        self.current_media_path = None
        self.is_playing = False

    def _update_audio_time(self):
        """
        오디오 재생 시간을 업데이트합니다.
        """
        if self.mpv_player:
            self.audio_position = self.mpv_player.playback_time
            self.audio_duration = self.mpv_player.duration

    def _on_duration_change(self, name, value):
        """
        오디오 재생 시간이 변경될 때 호출되는 콜백 함수
        
        Args:
            name: 속성 이름
            value: 변경된 값 (재생 시간)
        """
        self.audio_duration = value
        
        # 만약 부모에 슬라이더와 시간 레이블이 있다면 업데이트
        if hasattr(self.parent, 'playback_slider') and value is not None:
            self.parent.playback_slider.setRange(0, int(value))
        
        if hasattr(self.parent, 'time_label') and value is not None:
            formatted_duration = self.format_time(value)
            current_time = self.format_time(self.audio_position or 0)
            self.parent.time_label.setText(f"{current_time} / {formatted_duration}")

    def _on_position_change(self, name, value):
        """
        오디오 재생 위치가 변경될 때 호출되는 콜백 함수
        
        Args:
            name: 속성 이름
            value: 변경된 값 (재생 위치)
        """
        self.audio_position = value
        
        # 시간 레이블과 슬라이더 업데이트
        if hasattr(self.parent, 'time_label') and value is not None:
            formatted_duration = self.format_time(self.audio_duration or 0)
            current_time = self.format_time(value)
            self.parent.time_label.setText(f"{current_time} / {formatted_duration}")
        
        # 슬라이더 업데이트 (슬라이더가 드래그 중이 아닐 때만)
        if hasattr(self.parent, 'playback_slider') and value is not None:
            if not self.parent.playback_slider.isSliderDown():
                # 슬라이더의 valueChanged 신호가 발생하지 않도록 블록
                self.parent.playback_slider.blockSignals(True)
                self.parent.playback_slider.setValue(int(value))
                self.parent.playback_slider.blockSignals(False)

    def _on_audio_end(self, name, value):
        """
        오디오 재생이 끝났을 때 호출되는 콜백 함수
        
        Args:
            name: 속성 이름
            value: 변경된 값
        """
        # 오디오가 끝났고, 반복 재생이 꺼져 있으면 재생 정지
        if value and not self.mpv_player.loop:
            self.stop_audio()
            # 재생 버튼 업데이트 (parent에 update_play_button 메서드가 있다면)
            if hasattr(self.parent, 'update_play_button'):
                self.parent.update_play_button()

    def toggle_audio_playback(self):
        """
        오디오 재생/일시정지를 토글합니다.
        """
        if not self.mpv_player:
            return
            
        if self.is_playing:
            self.mpv_player.pause = True
            self.is_playing = False
        else:
            self.mpv_player.pause = False
            self.is_playing = True
            
        # 재생 버튼 업데이트 (parent에 update_play_button 메서드가 있다면)
        if hasattr(self.parent, 'update_play_button'):
            self.parent.update_play_button()
    
    def format_time(self, seconds):
        """
        초를 'MM:SS' 형식으로 변환하는 메서드
        
        Args:
            seconds: 초 단위 시간
            
        Returns:
            str: 'MM:SS' 형식의 시간 문자열
        """
        if seconds is None:
            return "00:00"
            
        seconds = max(0, seconds)
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

    def cleanup_audio_resources(self):
        """
        오디오 리소스를 정리합니다.
        """
        self.unload()
        
    def seek(self, position):
        """
        오디오 재생 위치를 변경합니다.
        
        Args:
            position (float): 이동할 재생 위치 (초 단위)
        """
        if self.mpv_player:
            try:
                self.mpv_player.seek(position)
            except Exception as e:
                print(f"오디오 탐색 중 오류: {str(e)}")
                pass 