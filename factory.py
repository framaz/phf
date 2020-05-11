import copy
import importlib
import inspect
import os
from abstracthook import AbstractHook
from provider import AbstractContentProvider


class _BasicAnalyser:
    def __init__(self):
        self._classes = {}

    def analyse_module(self, file_path):
        if file_path[~2:] != ".py" and not(os.path.isfile(os.path.join(file_path, "__init__.py"))):
            return
        file_path = file_path.replace("/", ".")
        if file_path[~2:] == ".py":
            file_path = file_path[:~2]

        module = importlib.import_module(file_path)
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and self.right_class_type(obj):
                if name in self._classes and obj is not self._classes[name]:
                    raise HookNameDoublingError(name, self._classes[name], obj)
                else:
                    self._classes[name] = obj

    def right_class_type(self, obj):
        raise NotImplementedError(f"Abstract right_class_type call of {self.__class__}")

    def analyse(self, *args):
        for file in args:
            if os.path.isdir(file):
                if os.path.isfile(os.path.join(file, "__init__.py")):
                    self.analyse_module(file)
                else:
                    strings = os.listdir(file)
                    strings = [os.path.join(file, string) for string in strings]
                    self.analyse(*strings)
            else:
                self.analyse_module(file)


class _HookAnalyser(_BasicAnalyser):
    def right_class_type(self, obj):
        return issubclass(obj, AbstractHook)

    @property
    def hooks(self):
        return copy.deepcopy(self._classes)


class _ProviderAnalyser(_BasicAnalyser):
    def right_class_type(self, obj):
        return issubclass(obj, AbstractContentProvider)

    @property
    def providers(self):
        return copy.deepcopy(self._classes)


class NameDoublingError(Exception):
    _obj_type_name = ""

    def __init__(self, class_name, first_class, second_class):
        message = f"Different {self.__class__._obj_type_name} with same name {class_name}"

        if first_class and second_class:
            self.first_class = first_class
            self.second_class = second_class
            message += f' at paths "{first_class.__module__}" and "{second_class.__module__}"'

        super().__init__(message)


class HookNameDoublingError(NameDoublingError):
    _obj_type_name = "hooks"


class ProviderNameDoublingError(NameDoublingError):
    _obj_type_name = "providers"


if __name__ == "__main__":
    kek = _ProviderAnalyser()
    kek.analyse("Sites")
    kek = kek
