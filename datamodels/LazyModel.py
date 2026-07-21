from dataclasses import fields


class LazyValues:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in {f.name for f in fields(self)}:
                setattr(self, key, value)
