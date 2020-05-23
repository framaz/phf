"""Tools for dynamic creation of hooks and providers

Only HookAndProviderFactory class from this module should be used directly.
"""
from __future__ import annotations

import copy
import importlib
import inspect
import os
import typing

from abstracthook import AbstractHook
from provider import AbstractContentProvider


class HookAndProviderFactory:
    """Factory to create hooks and providers.

    Works as a facade for _HookAnalyser and _ProviderAnalyser.
    All runtime hook and provider creation in AsyncParser a made with this factory.
    The user doesnt have to directly interact with HookAndProviderFactory objects as
    AsyncParser crates the factory and works with the factory itself. AsyncParser also
    provides interface for reading hooks and providers from directories/files/packages.

    Usage tutorial:
        1. Create factory. provider_paths and hook_paths(both lists of string paths) args
        in __init__ can be used to get all hooks and providers.
        2. With import_hook_classes and import_provider_classes read provider and hook classes
        from paths.
        3. With create_hook and create_provider create classes by their aliases.

    Navigate to _BasicAnalyser for further information about reading classes from paths.

    Attributes:
        _hookAnalyser: Instance of _HookAnalyser class, most of hook-related actions is
            delegated to it.
        _providerAnalyser: Instance of _HookAnalyser class, most of hook-related actions is
            delegated to it.
    """

    def __init__(self,
                 provider_paths: typing.List[str] = None,
                 hook_paths: typing.List[str] = None):
        """Create factory with possibility to remember hooks and providers.

        Args:
            provider_paths: list of strings to search for providers(modules, packages
                and directories).
            hook_paths: list of strings to search for hooks(modules, packages
                and directories).
            """
        if provider_paths is None:
            provider_paths = []
        if hook_paths is None:
            hook_paths = []

        self._hookAnalyser = _HookAnalyser()
        self._hookAnalyser.analyse(*hook_paths)

        self._providerAnalyser = _ProviderAnalyser()
        self._providerAnalyser.analyse(*provider_paths)

    def import_hook_classes(self, *args) -> None:
        """Remember all hook classes from paths

        Just delegates to _HookAnalyser.analyse method.

        Args:
            *args: strings of files/hooks/directories paths
        """
        self._hookAnalyser.analyse(*args)

    def import_provider_classes(self, *args) -> None:
        """Remember all provider classes from paths

        Just delegates to _HookAnalyser.analyse method.

        Args:
            *args: strings of files/hooks/directories paths
        """
        self._providerAnalyser.analyse(*args)

    def create_hook(self, hook_alias: str,
                    args: typing.List = None,
                    kwargs: typing.Dict[str, typing.Any] = None) -> AbstractHook:
        """Create hook with following args and kwargs.

        Args:
            hook_alias: Alias for hook creation.
            args: A list of all positional arguments for constructor
            kwargs: A list of all keyword arguments for constructor

        Returns:
            Created hook.
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        all_hooks = self._hookAnalyser.get_hooks()
        if hook_alias not in all_hooks:
            raise Exception(f'No hook named "{hook_alias}"')

        return all_hooks[hook_alias](*args, **kwargs)

    def create_provider(self, provider_alias: str,
                        args: typing.List = None,
                        kwargs: typing.Dict[str, typing.Any] = None) -> AbstractContentProvider:
        """Create provider with following args and kwargs.

        Args:
            provider_alias: Alias for provider creation.
            args: A list of all positional arguments for constructor
            kwargs: A list of all keyword arguments for constructor

        Returns:
            Created hook.
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        all_providers = self._providerAnalyser.get_providers()
        if provider_alias not in all_providers:
            raise Exception(f'No hook named "{provider_alias}"')

        return all_providers[provider_alias](*args, **kwargs)


class _BasicAnalyser:
    """Analyses modules, packages and directory trees and searches for classes.

    The decision whether concrete class it is saved is determined in function right_class_type.

    Attributes:
        _classes: a dict of classes in format {alias: class}.
    """

    def __init__(self):
        """Simple initiation."""
        self._classes = {}

    def analyse_module(self, file_path: str) -> None:
        """Get all classes from file/ at path.

        It can work with .py files or packages with __init__.py.
        All classes are remembered by their __name__ and _aliases. So if you have
        a class MyHook and do "tmp_name = MyHook", then MyHook won't be remembered by "tmp_name" alias
        Be warned that this method checks all objects in module's scope.

        Example:
            You want to analyse module "myhooks.py" which has following code and have ability
            to create MyHook at dynamically at runtime:

                from abstracthook import AbstractHook
                class MyHook(AbstractHook):
                    ...

            As AbstractHook is in the module's scope, it will be added too.

        If you want to stop that from happening when doing "from hook_file import hook_class"
        then just use "del(hook_class)" at the end of file.

        Args:
            file_path: path to file/directory/package.
        """
        # Works only with packages and .py files
        if file_path[~2:] != ".py" and not (os.path.isfile(os.path.join(file_path, "__init__.py"))):
            return

        file_path = file_path.replace("/", ".")
        file_path = file_path.replace("\\", ".")
        if file_path[~2:] == ".py":
            file_path = file_path[:~2]

        module = importlib.import_module(file_path)
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and self.right_class_type(obj):
                name = obj.__name__
                self._add_class_to_dict(name, obj)
                for alias in obj.get_aliases():
                    self._add_class_to_dict(alias, obj)

    def _add_class_to_dict(self, alias: str, cls) -> None:
        """Remember alias: cls mapping.

        Also checks for alias conflicts.

        Args:
            alias: string alias for the class.
            cls: class that needs to be added.

        Raises:
            HookAliasDoublingError
            ProviderAliasDoublingError
        """
        if alias in self._classes and cls is not self._classes[alias]:
            raise HookAliasDoublingError(alias, self._classes[alias], cls)
        else:
            self._classes[alias] = cls

    def right_class_type(self, obj) -> bool:
        """Check if obj is remembered by the method.

        Not implemented in base class.
        """
        raise NotImplementedError(f"Abstract right_class_type call of {self.__class__}")

    def analyse(self, *args) -> None:
        """Search all *args paths for needed classes.

        Can search in:
            .py files,
            directories - searches in all files and subdirectories,
            packages - searches in package's __init__.py

        Args:
            *args: strings of paths.

        Example:
            Analysing a "module1.py", all files(recursively) in "directory/subdir" and
            package "package"
            analyser.analyse("module1.py", "directory/subdir", "package")
        """
        for file in args:
            if os.path.isdir(file):
                # If package
                if os.path.isfile(os.path.join(file, "__init__.py")):
                    self.analyse_module(file)
                # Otherwise is a directory
                else:
                    strings = os.listdir(file)
                    strings = [os.path.join(file, string) for string in strings]
                    self.analyse(*strings)
            else:
                self.analyse_module(file)


class _HookAnalyser(_BasicAnalyser):
    """Class for analysing files and search for hooks."""

    def right_class_type(self, obj) -> bool:
        """Check if obj is a AbstractHook subclass.

        Args:
            obj: object to check.

        Returns:
            True if obj is AbstractHook or it's subclass, False otherwise.
        """
        return issubclass(obj, AbstractHook)

    @property
    def hooks(self) -> typing.Dict[str, typing.Type[AbstractHook]]:
        """Return copy of dict of all analysed hook classes.

        Dict is copied to keep it protected from modifying outside of the class.

        Returns:
            Copy of dict of all analysed hook classes
        """
        return copy.deepcopy(self._classes)

    def get_hooks(self) -> typing.Dict[str, typing.Type[AbstractHook]]:
        """Return all hooks. Delegates to hooks property."""
        return self.hooks


class _ProviderAnalyser(_BasicAnalyser):
    """Class for analysing files and search for providers."""

    def right_class_type(self, obj) -> bool:
        """Check if obj is a AbstractContentProvider subclass.

        Args:
            obj: object to check.

        Returns:
            True if obj is AbstractContentProvider or it's subclass, False otherwise.
        """
        return issubclass(obj, AbstractContentProvider)

    @property
    def providers(self) -> typing.Dict[str, typing.Type[AbstractContentProvider]]:
        """Return copy of dict of all analysed providers classes.

        Dict is copied to keep it protected from modifying outside of the class.

        Returns:
            Copy of dict of all analysed provider classes
        """
        return copy.deepcopy(self._classes)

    def get_providers(self) -> typing.Dict[str, typing.Type[AbstractContentProvider]]:
        """Return all hooks. Delegates to providers property."""
        return self.providers


class AliasDoublingError(Exception):
    """Base exception that occurs when two hooks/providers have same aliases.

    Class attributes:
        _obj_type_name: String, specifies if its hook or provider.

    Attributes:
        first_class: First class with conflict in aliases, AbstractContentProvider or AbstractHook.
        second_class: Second class with conflict in aliases, AbstractContentProvider or AbstractHook.
    """
    _obj_type_name = ""

    def __init__(self, conflicting_alias: str,
                 first_class: typing.Union[AbstractContentProvider, AbstractHook],
                 second_class: typing.Union[AbstractContentProvider, AbstractHook]):
        """Create exception with conflicting alias from two classes.

        Args:
            conflicting_alias: string of conflicting alias.
            first_class:
            second_class:
        """
        message = f"Different {self.__class__._obj_type_name} with same name {conflicting_alias}"

        self.first_class = first_class
        self.second_class = second_class
        message += f' at paths "{first_class.__module__}" and "{second_class.__module__}"'

        super().__init__(message)


class HookAliasDoublingError(AliasDoublingError):
    """Exception that occurs when two hooks have same aliases."""
    _obj_type_name = "hooks"


class ProviderAliasDoublingError(AliasDoublingError):
    """Exception that occurs when two providers have same aliases."""
    _obj_type_name = "providers"


if __name__ == "__main__":
    kek = HookAndProviderFactory(provider_paths=["providers"], hook_paths=["hooks"])
    kek = kek
