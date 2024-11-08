import datetime
from typing import Dict, Type, Union

from aiologger.levels import LogLevel
from yaspin.spinners import Spinners

from metrikflow.logging.spinner import ProgressText

from .config import LoggingConfig
from .logger_types import (
    AsyncFilesystemLogger,
    AsyncLogger,
    AsyncSpinner,
    Logger,
    LoggerTypes,
    LoggerTypesMap,
    SyncFilesystemLogger,
    SyncLogger,
)
from .logger_types.handlers.async_file_handler import RolloverInterval
from .logging_manager import logging_manager


class MetrikflowLogger:

    def __init__(self) -> None:
        self.loggers: Dict[str, Logger[Union[AsyncLogger, AsyncFilesystemLogger, AsyncSpinner], Union[SyncLogger, SyncFilesystemLogger]]] = {}

        self.logger_names = logging_manager.logger_types.names
        self.logger_types = logging_manager.logger_types.types
        self.log_level: LogLevel = None
        self.logger_types_map = LoggerTypesMap()

    def initialize(self, config: LoggingConfig=LoggingConfig()):

        for logger_type in self.logger_types:
            
            logger_name = logging_manager.logger_types.get_name(logger_type)
            logger_enabled = logging_manager.get_logger_enabled_state(logger_type)
            self.log_level = logging_manager.log_level

            config.from_dict({
                'logger_name': logger_name,
                'logger_enabled': logger_enabled,
                'logger_type': logger_type,
                'log_level': logging_manager.log_level,
                'logfiles_directory': logging_manager.logfiles_directory,
                'spinner_display': logging_manager.progress_display
            })

            ASYNC_TYPE = Type[AsyncLogger]
            SYNC_TYPE = Type[SyncLogger]
            
            if logger_type == LoggerTypes.SPINNER:
                ASYNC_TYPE = Type[AsyncSpinner]
                SYNC_TYPE = None

            elif logger_type == LoggerTypes.FILESYSTEM:
                ASYNC_TYPE = Type[AsyncFilesystemLogger]
                SYNC_TYPE = Type[SyncFilesystemLogger]

            logger: Logger[ASYNC_TYPE, SYNC_TYPE] = Logger(config)

            if logger_type == LoggerTypes.CONSOLE:
                logger.set_patterns('%(message)s')

            elif logger_type == LoggerTypes.DISTRIBUTED or logger_type == LoggerTypes.METRIKFLOW:

                logger.set_patterns(
                    '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                    datefmt_pattern='%Y-%m-%dT%H:%M:%S.%f.%z'
                )

            self.loggers[logger_name] = logger

    def __getitem__(self, logger_name: str) -> Logger[Union[AsyncLogger, AsyncFilesystemLogger, AsyncSpinner], Union[SyncLogger, SyncFilesystemLogger]]:
        logger = self.loggers.get(logger_name)
        if logger is None:
            logger = Logger(
                logger_name,
                LoggerTypes.CONSOLE,
                log_level=logging_manager.log_level
            )

            logger.set_patterns('%(message)s')

        return logger

    @property
    def console(self) -> Logger[AsyncLogger, SyncLogger]:
        return self.loggers['console']

    @property
    def distributed(self) -> Logger[AsyncLogger, SyncLogger]:
        return self.loggers['distributed']

    @property
    def metrikflow(self) -> Logger[AsyncLogger, SyncLogger]:
        return self.loggers['metrikflow'] 

    @property
    def filesystem(self) -> Logger[AsyncFilesystemLogger, SyncFilesystemLogger]:
        return self.loggers['filesystem']

    @property
    def distributed_filesystem(self) -> Logger[AsyncFilesystemLogger, SyncFilesystemLogger]:
        return self.loggers['distributed_filesystem']

    @property
    def spinner(self) -> AsyncSpinner:
        return self.loggers['spinner'].aio

    def create_logger(
        self,
        logger_name: str,
        logger_type: LoggerTypes,
        spinner_type: Spinners=None,
        spinner_display: ProgressText=None,
        rotation_interval_type: RolloverInterval=RolloverInterval.DAYS,
        rotation_interval: int=1,
        backups: int=1,
        rotation_time: datetime.time=None
    ):

        logger_enabled = logging_manager.get_logger_enabled_state(logger_type)

        ASYNC_TYPE = Type[AsyncLogger]
        SYNC_TYPE = Type[SyncLogger]

        if logger_type == LoggerTypes.FILESYSTEM:
            ASYNC_TYPE = Type[AsyncFilesystemLogger]
            SYNC_TYPE = Type[SyncFilesystemLogger]

        config = LoggingConfig()
        config.from_dict({
            'logger_name': logger_name,
            'logger_type': logger_type,
            'log_level': logging_manager.log_level,
            'logger_enabled': logger_enabled,
            'spinner_type': spinner_type,
            'spinner_display': spinner_display,
            'rotation_interval_type': rotation_interval_type,
            'rotation_interval': rotation_interval,
            'backup_count': backups,
            'rotation_time': rotation_time
        })
        
        self.loggers[logger_name]: Logger[ASYNC_TYPE, SYNC_TYPE] = Logger(config)

    def disable_logger(self, logger_name):
        logger = self.loggers.get(logger_name)
        if logger:
            logger.logger_enabled = False

    def enable_logger(self, logger_name):
        logger = self.loggers.get(logger_name)
        if logger:
            logger.logger_enabled = True