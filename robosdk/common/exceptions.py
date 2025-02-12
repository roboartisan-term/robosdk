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
"""Basic Exceptions"""


class RoboError(Exception):
    """Base class for APP exceptions"""
    pass


class SensorError(Exception):
    """Base class for sensor exceptions"""
    pass


class ComponentError(Exception):
    """Base class for component exceptions"""
    pass


class RequiredParameterException(Exception):
    def __init__(self, cls_name):
        super().__init__(f"`{cls_name}` require parameter")


class CloudError(Exception):
    """Base class for cloud service exceptions"""

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super(CloudError, self).__init__()

    def __str__(self):
        return self.message
