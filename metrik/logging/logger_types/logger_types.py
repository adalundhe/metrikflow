from enum import Enum


class LoggerTypes(Enum):
    CONSOLE='console'
    DISTRIBUTED='distributed'
    FILESYSTEM='filesystem'
    DISTRIBUTED_FILESYSTEM='distributed_filesysem'
    METRIK='metrik'
    SPINNER='spinner'

