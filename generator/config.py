from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    stages: int = field(init=False)
    A: List[List[float]]
    b: List[float]
    c: List[float]
    components: List[str]
    uuid: bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    system_size: int = field(init=False)

    def __post_init__(self):
        self.stages = len(self.A)
        self.system_size = len(self.components)

    def get_stage_config(self, stage_index):
        return StageConfig(stage_index, self.A[stage_index], self.c[stage_index], self.components)


@dataclass
class StageConfig:
    stage_index: int
    a: List[float]
    c: float
    components: List[str]
    system_size: int = field(init=False)

    def __post_init__(self):
        self.system_size = len(self.components)
        # TODO Check if config is wellformed

    def is_explicit(self):
        for i, f in enumerate(self.a):
            if f != 0 and i >= self.stage_index:
                return False
        return True
