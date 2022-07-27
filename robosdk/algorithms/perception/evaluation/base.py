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

from typing import List

from robosdk.algorithms.base import AlgorithmBase

__all__ = ("SampleEvaluateBase", )


class SampleEvaluateBase(AlgorithmBase):  # noqa

    def __init__(self, logger=None):
        super(SampleEvaluateBase, self).__init__(logger=logger)

    def evaluation(self, samples: List):
        raise NotImplementedError
