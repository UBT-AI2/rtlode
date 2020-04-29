from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    stages: int = field(init=False)
    A: List[List[float]]
    b: List[float]
    c: List[float]
    components: List[str]
    nbr_solver: int = 1
    uuid: bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    system_size: int = field(init=False)

    def __post_init__(self):
        self.stages = len(self.A)
        self.system_size = len(self.components)
        if self.nbr_solver is None:
            self.nbr_solver = 1

    def get_stage_config(self, stage_index):
        return StageConfig(stage_index, self.A[stage_index], self.c[stage_index], self.components)

    @staticmethod
    def from_dict(config):
        return Config(
            config['method']['A'],
            config['method']['b'],
            config['method']['c'],
            config['components'],
            config['nbr_solver'] if 'nbr_solver' in config else None,
            # Needed if convert is called outside the normal build process.
            uuid=config['build_info']['uuid'] if 'build_info' in config else 'BEEFBEEFBEEFBEEFBEEFBEEFBEEFBEEF'
        )


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
