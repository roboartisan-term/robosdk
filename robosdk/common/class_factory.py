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

import warnings
from inspect import isclass
from inspect import isfunction
from typing import List


class ClassType:
    """Const class saved defined class type."""
    GENERAL = 'general'
    BACKEND = 'backend'
    EVENT = 'event'

    CONTROL = "control"
    SENSOR = "sensor"

    NAVIGATION = "navigation"
    LOCALIZE = "localize"
    PERCEPTION = "perception"

    CLOUD_ROBOTICS = "cloud_robotics"
    CLOUD_ROBOTICS_ALG = "cloud_robotics_algorithms"

    ROBOTICS_SKILL = "robotics_skill"


class ClassFactory(object):
    """
    A Factory Class to manage all class need to register with config.
    """

    __registry__ = {}

    @classmethod
    def register(cls, type_name=ClassType.GENERAL, alias=None):
        """
        Register class into registry.
        :param type_name: type_name: type name of class registry
        :param alias: alias of class name
        :return: wrapper
        """

        def wrapper(t_cls):
            """
            Register class with wrapper function.
            :param t_cls: class need to register
            :return: wrapper of t_cls
            """
            t_cls_name = alias if alias is not None else t_cls.__name__
            if type_name not in cls.__registry__:
                cls.__registry__[type_name] = {t_cls_name: t_cls}
            else:
                if t_cls_name in cls.__registry__:
                    raise ValueError(
                        "Cannot register duplicate class ({})".format(
                            t_cls_name))
                cls.__registry__[type_name].update({t_cls_name: t_cls})
            return t_cls

        return wrapper

    @classmethod
    def register_cls(cls, t_cls, type_name=ClassType.GENERAL, alias=None):
        """
        Register class with type name.
        :param t_cls: class need to register.
        :param type_name: type name.
        :param alias: class name.
        :return:
        """
        t_cls_name = alias if alias is not None else t_cls.__name__
        if type_name not in cls.__registry__:
            cls.__registry__[type_name] = {t_cls_name: t_cls}
        else:
            if t_cls_name in cls.__registry__:
                raise ValueError(
                    "Cannot register duplicate class ({})".format(t_cls_name))
            cls.__registry__[type_name].update({t_cls_name: t_cls})
        return t_cls

    @classmethod
    def register_from_package(cls, package, type_name=ClassType.GENERAL):
        """
        Register all public class from package.
        :param package: package need to register.
        :param type_name: type name.
        :return:
        """
        for _name in dir(package):
            if _name.startswith("_"):
                continue
            _cls = getattr(package, _name)
            if not isclass(_cls) and not isfunction(_cls):
                continue
            ClassFactory.register_cls(_cls, type_name)

    @classmethod
    def is_exists(cls, type_name, cls_name=None):
        """
        Determine whether class name is in the current type group.
        :param type_name: type name of class registry
        :param cls_name: class name
        :return: True/False
        """
        if cls_name is None:
            return type_name in cls.__registry__
        return ((type_name in cls.__registry__) and
                (cls_name in cls.__registry__.get(type_name)))

    @classmethod
    def get_cls(cls, type_name, t_cls_name=None):
        """
        Get class and bind config to class.
        :param type_name: type name of class registry
        :param t_cls_name: class name
        :return: t_cls
        """
        if not cls.is_exists(type_name, t_cls_name):
            warnings.warn(
                f"can't find class type {type_name} class name"
                f" {t_cls_name} in class registry")
            return None
        # create instance without configs
        if t_cls_name is None:
            raise ValueError(
                "can't find class. class type={}".format(type_name))
        t_cls = cls.__registry__.get(type_name).get(t_cls_name)
        return t_cls

    @classmethod
    def list(cls, type_name) -> List:
        if not cls.is_exists(type_name):
            warnings.warn(
                f"can't find class type {type_name} in class registry")
            return []
        return list(cls.__registry__.get(type_name).keys())
