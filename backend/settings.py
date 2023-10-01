from typing import overload, Dict, Any
import json
from pathlib import Path


class Setting:
    def __init__(self, name: str, value: Any) -> None:
        self.__name = name
        self.__value = value

        if isinstance(value, dict):
            for key in value.keys():
                prop = property(
                    lambda self, key=key: self.__value[key],
                    lambda self, value, key=key: self.__value.update({key: value}),
                )
                setattr(self.__class__, key, prop)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def value(self) -> Any:
        return self.__value


class Settings:
    def __init__(self, settings_file: str) -> None:
        self.__settings_file = settings_file
        self.__settings = self.__load_settings()

    def __load_settings(self) -> Dict[str, Any]:
        with open(self.__settings_file, "r") as f:
            content = json.load(f)

        settings = {}
        for name, value in content.items():
            settings[name] = Setting(name, value)

        return settings

    def __save(self) -> None:
        content = {setting.name: setting.value for setting in self.__settings.values()}
        with open(self.__settings_file, "w") as f:
            json.dump(content, f, indent=2, sort_keys=True)

    @overload
    def get(self, name: str) -> Any:
        ...

    @overload
    def get(self, name: str, default: Any) -> Any:
        ...

    @overload
    def get(self, name: str, subname: str) -> Any:
        ...

    @overload
    def get(self, name: str, subname: str, default: Any) -> Any:
        ...

    def get(self, name: str, subname: str = None, default: Any = None) -> Any:
        if subname is None:
            return self.__settings[name].value
        else:
            setting = self.__settings[name]
            return getattr(setting, subname, default)

    @overload
    def set(self, name: str, value: Any) -> None:
        ...

    @overload
    def set(self, name: str, subname: str, value: Any) -> None:
        ...

    def set(self, name: str, subname: str = None, value: Any = None) -> None:
        if subname is None:
            self.__settings[name].value = value
        else:
            setting = self.__settings[name]
            setattr(setting, subname, value)
        self.__save()
