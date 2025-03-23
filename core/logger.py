"""
애플리케이션 로깅 시스템 모듈

이 모듈은 애플리케이션의 로깅을 처리하며, 다양한 로그 레벨과 
출력 대상(콘솔, 파일 등)을 지원합니다.
"""
import os
import logging
import datetime
from typing import Optional, Dict, Any, Union
from pathlib import Path

from core.utils.path_utils import get_user_data_directory


class Logger:
    """
    애플리케이션 로깅 시스템
    
    다양한 로그 레벨을 지원하며 콘솔 및 파일 출력이 가능합니다.
    """
    
    # 로거 인스턴스 캐시
    _loggers: Dict[str, 'Logger'] = {}
    
    @classmethod
    def get_logger(cls, name: str) -> 'Logger':
        """
        이름으로 로거 인스턴스 가져오기 (싱글톤 패턴)
        
        Args:
            name: 로거 이름
            
        Returns:
            Logger 인스턴스
        """
        if name not in cls._loggers:
            cls._loggers[name] = Logger(name)
        return cls._loggers[name]
    
    def __init__(self, name: str, log_dir: Optional[str] = None):
        """
        Logger 초기화
        
        Args:
            name: 로거 이름
            log_dir: 로그 파일 저장 디렉토리 (없으면 기본 위치 사용)
        """
        self.name = name
        
        # 로그 디렉토리 설정
        if log_dir is None:
            log_dir = os.path.join(get_user_data_directory(), 'logs')
        
        # 로그 디렉토리가 없으면 생성
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # 로그 파일 경로
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(log_dir, f"{date_str}.log")
        
        # Python 로거 설정
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 이미 핸들러가 설정되어 있는지 확인
        if not self.logger.handlers:
            # 콘솔 핸들러
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_fmt = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
            console_handler.setFormatter(console_fmt)
            
            # 파일 핸들러
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_fmt = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
            file_handler.setFormatter(file_fmt)
            
            # 핸들러 추가
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """
        디버그 레벨 로그 기록
        
        Args:
            message: 로그 메시지
            **kwargs: 추가 컨텍스트 정보
        """
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """
        정보 레벨 로그 기록
        
        Args:
            message: 로그 메시지
            **kwargs: 추가 컨텍스트 정보
        """
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """
        경고 레벨 로그 기록
        
        Args:
            message: 로그 메시지
            **kwargs: 추가 컨텍스트 정보
        """
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """
        오류 레벨 로그 기록
        
        Args:
            message: 로그 메시지
            **kwargs: 추가 컨텍스트 정보
        """
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """
        심각한 오류 레벨 로그 기록
        
        Args:
            message: 로그 메시지
            **kwargs: 추가 컨텍스트 정보
        """
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs) -> None:
        """
        로그 메시지 기록 (내부 메서드)
        
        Args:
            level: 로그 레벨
            message: 로그 메시지
            **kwargs: 추가 컨텍스트 정보
        """
        # 추가 컨텍스트가 있으면 메시지에 포함
        if kwargs:
            context_str = ' | '.join(f"{k}={v}" for k, v in kwargs.items())
            full_message = f"{message} [Context: {context_str}]"
        else:
            full_message = message
        
        self.logger.log(level, full_message)
    
    @staticmethod
    def set_global_level(level: Union[int, str]) -> None:
        """
        전역 로깅 레벨 설정
        
        Args:
            level: 로그 레벨 (logging.DEBUG, logging.INFO 등 또는 'DEBUG', 'INFO' 등 문자열)
        """
        # 문자열 레벨을 숫자로 변환
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        
        # 모든 로거에 레벨 적용
        for logger in Logger._loggers.values():
            logger.logger.setLevel(level) 