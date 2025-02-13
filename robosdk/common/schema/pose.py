# Copyright 2021 The KubeEdge Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import typing

from pydantic import BaseModel

__all__ = ("BasePose", "PoseSeq")


class BasePose(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 0.0

    def __str__(self):
        if self.w and self.w > 0.0:
            return f"x: {self.x} y: {self.y} z: {self.z} w: {self.w}"
        return f"x: {self.x} y: {self.y} z: {self.z}"

    def __sub__(self, other):
        return math.sqrt(
            math.pow(self.x - other.x, 2) + math.pow(self.y - other.y, 2)
        )


class PoseSeq(BaseModel):
    seq: int = 0
    point: typing.Union[typing.Tuple[float], typing.List[float]] = None
    position: BasePose = BasePose()
    prev: typing.Any = None
    next: typing.Any = None

    def __next__(self):
        return self.next

    def __iter__(self):
        return self
