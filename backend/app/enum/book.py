from enum import StrEnum


class Status(StrEnum):
    active = 'active'
    unavailable = 'unavailable'


class ReadingStatus(StrEnum):
    planned = 'planned'
    reading = 'reading'
    finished = 'finished'
