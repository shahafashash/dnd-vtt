from typing import overload, Dict, Any, List
import json
import pygame as pg


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


class Controls:
    def __init__(self, settings: Settings) -> None:
        self.__settings = settings
        self.__key_name_to_pygame_key = self.__create_keys_mapping()
        self.__pygame_key_to_key_name = {
            v: k for k, v in self.__key_name_to_pygame_key.items()
        }
        self.__key_name_to_pygame_mode = self.__create_modes_mapping()
        self.__controls = self.__settings.get("controls")

    def __create_keys_mapping(self) -> Dict[str, int]:
        mapping = {}
        # get all pygame key constants
        for key in dir(pg):
            if key.startswith("K_"):
                pg_key = getattr(pg, key)
                name = pg.key.name(pg_key)
                mapping[name] = pg_key

        # add some missing keys
        # mapping["mousebuttonleft"] = pg.MOUSEBUTTONDOWN  # 1
        # mapping["mousebuttonmiddle"] = pg.MOUSEBUTTONDOWN  # 2
        # mapping["mousebuttonright"] = pg.MOUSEBUTTONDOWN  # 3
        # mapping["mousebuttonwheelup"] = pg.MOUSEWHEEL  # 4
        # mapping["mousebuttonwheeldown"] = pg.MOUSEWHEEL  # 5

        return mapping

    def __create_modes_mapping(self) -> Dict[str, int]:
        mapping = {}
        # get all pygame key constants
        pg_locals = dir(pg)
        for key in pg_locals:
            if key.startswith("KMOD_"):
                pg_mode = getattr(pg, key)
                name = key.replace("KMOD_", "K_")
                if name in pg_locals:
                    pg_key = getattr(pg, name)
                    key_name = pg.key.name(pg_key)
                    mapping[key_name] = pg_mode

        return mapping

    @overload
    def get(self, action: str, with_mode: bool = True) -> List[int]:
        ...

    @overload
    def get(self, action: str, with_mode: bool = False) -> int:
        ...

    def get(self, action: str, with_mode: bool = False) -> List[int] | int:
        keys = self.__controls.get(action)
        keys_as_pygame_keys = []
        for key in keys:
            keys_as_pygame_keys.append(self.__key_name_to_pygame_key[key])

        if with_mode:
            return keys_as_pygame_keys

        elif len(keys_as_pygame_keys) == 0:
            raise ValueError(f"Action '{action}' has no keys assigned")

        return keys_as_pygame_keys[-1]

    @overload
    def set(self, action: str, keys: List[int]) -> None:
        ...

    @overload
    def set(self, action: str, keys: int) -> None:
        ...

    def set(self, action: str, keys: List[int] | int) -> None:
        if isinstance(keys, int):
            keys = [keys]
        pygame_keys_as_key_names = []
        for key in keys:
            pygame_keys_as_key_names.append(self.__pygame_key_to_key_name[key])
        self.__controls.set(action, pygame_keys_as_key_names)

    def is_action_a_mode(self, action: str) -> bool:
        keys = self.get(action, with_mode=True)
        keys_to_names = [self.__pygame_key_to_key_name[key] for key in keys]
        for key in keys_to_names:
            if key in self.__key_name_to_pygame_mode:
                return True
        return False

    def get_action_mode(self, action: str) -> List[int]:
        is_mode = self.is_action_a_mode(action)
        if not is_mode:
            return []

        keys = self.get(action, with_mode=True)
        keys_to_names = [self.__pygame_key_to_key_name[key] for key in keys]
        modes = []
        for key in keys_to_names:
            if key in self.__key_name_to_pygame_mode:
                modes.append(self.__key_name_to_pygame_mode[key])

        return modes
