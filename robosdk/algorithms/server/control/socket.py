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

from typing import Dict

from robosdk.common.class_factory import ClassFactory
from robosdk.common.class_factory import ClassType
from robosdk.common.schema.stream import StreamClient

from .base import ControlServer

__all__ = ("SocketControlServer",)


@ClassFactory.register(ClassType.CLOUD_ROBOTICS_ALG, "socket_control_server")
class SocketControlServer(ControlServer):  # noqa
    def __init__(self, name: str = "server", logger=None):
        super(SocketControlServer, self).__init__(name=name, logger=logger)
        self._clients = {}

    def get_robot_by_id(self, id) -> StreamClient:
        return self._clients.get(id, None)

    def send(self, client: StreamClient, data: Dict, **kwargs):
        for to_client in self.robots:
            if client.name and to_client != client:
                continue
            self.logger.info(
                f"send data to Client {to_client} from {self._room}")
            to_client.client.send_json(data)

    async def async_send(self, client: StreamClient, data: Dict, **kwargs):
        for to_client in self.robots:
            if client.name and to_client != client:
                continue
            self.logger.info(
                f"send data to Client {to_client} from {self._room}")
            await to_client.client.send_json(data)

    def add(self, robot: StreamClient, **kwargs):
        if robot == self.controller or robot in self.robots:
            self.logger.warning(f"{robot.name} has already registered")
            return
        self.robots.append(robot)
        self._clients[robot.id] = robot

    def remove(self, robot: StreamClient, **kwargs):
        del self._clients[robot.id]
        if robot == self.controller:
            self.logger.warning(
                f"Attempt to close the controller {robot.name} which will "
                f"cause all related robots to be released")
            self.stop()
            self.controller = None
        if robot not in self.robots:
            self.logger.warning(
                f"{robot.name} not registered over {self._room}")
            return
        self.robots.remove(robot)

    def stop(self):
        self._clients = {}
        super(SocketControlServer, self).stop()

    def start(self):
        data = {"command": "start", }
        for to_client in self.robots:
            self.logger.info(f'Starting socket control for {to_client.name}')
            to_client.client.send_json(data)
