"""Dependencias explícitas compartidas por las pantallas."""


class ScreenContext:
    def __init__(self, **values):
        self.__dict__.update(values)
