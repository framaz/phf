from collections import Counter

import pytest

from factory_obj.file1 import Hook1, Provider1
from phf import factory

hook_names = ["hook", "Hook1", "Hook2", "AbstractHook"]
provider_names = ["Provider1", "BlockingContentProvider", ]


def test_add_class_to_dict():
    analyser = factory._HookAnalyser()

    analyser._add_class_to_dict("kek", object)
    analyser._add_class_to_dict("waw", object)
    with pytest.raises(factory.AliasDoublingError):
        analyser._add_class_to_dict("kek", int)

    assert list(analyser.get_hooks().keys()) == ["kek", "waw"]


class TestHookAnalyser:
    """Tests for _HookAnalyser class."""
    def test_hook_class_checker(self, hook):
        analyser = factory._HookAnalyser()
        assert analyser.right_class_type(hook.__class__)
        assert not analyser.right_class_type(int)

    @pytest.mark.parametrize("amount", [1, 2])
    def test_hook_analyser(self, amount):
        analyser = factory._HookAnalyser()
        for _ in range(amount):
            analyser.analyse("factory_obj")

        analyser_classes = Counter(analyser.get_hooks().keys())
        expected = Counter(hook_names)
        assert analyser_classes == expected

    def test_hook_same_ailas(self, ):
        analyser = factory._HookAnalyser()
        analyser.analyse("factory_obj")

        with pytest.raises(factory.AliasDoublingError):
            analyser.analyse("factory_obj/hooks_package/hook2.py")


class TestProviderAnalyser:
    """Tests for _ProviderAnalyser class."""
    def test_provider_class_checker(self, complex_provider):
        analyser = factory._ProviderAnalyser()
        assert analyser.right_class_type(complex_provider.__class__)
        assert not analyser.right_class_type(int)

    def test_provider_analyser(self, ):
        analyser = factory._ProviderAnalyser()
        analyser.analyse("factory_obj")

        analyser_classes = Counter(analyser.get_providers().keys())
        expected = Counter(provider_names)
        assert analyser_classes == expected


class TestFactory:
    """Tests for HookAndProviderFactory."""
    def test_factory_constructor(self):
        fact = factory.HookAndProviderFactory(["factory_obj"], ["factory_obj"])
        hooks = Counter(fact._hook_analyser.get_hooks().keys())
        assert hooks == Counter(hook_names)

        fact = factory.HookAndProviderFactory(
            ["factory_obj"],
            ["factory_obj", "factory_obj/hooks_package/hook3.py"],
        )
        hooks = Counter(fact._hook_analyser.get_hooks().keys())
        assert hooks == Counter(hook_names + ["Hook3"])

        fact = factory.HookAndProviderFactory()
        hooks = Counter(fact._hook_analyser.get_hooks().keys())
        assert hooks == Counter()

    def test_factory_import_after_constructor(self):
        fact = factory.HookAndProviderFactory()

        fact.import_hook_classes("factory_obj",
                                 "factory_obj/hooks_package/hook3.py")
        hooks = Counter(fact._hook_analyser.get_hooks().keys())
        assert hooks == Counter(hook_names + ["Hook3"])

        fact.import_provider_classes("factory_obj",
                                     "factory_obj/hooks_package/hook3.py")
        providers = Counter(fact._provider_analyser.get_providers().keys())

        assert providers == Counter(provider_names + ["Provider3",
                                                      "AbstractContentProvider"])

    class TestHookCreation:
        """Tests for hook creation."""
        def test_nonexistent_hook_creation(self, hook_provider_factory):
            with pytest.raises(KeyError):
                hook_provider_factory.create_hook("azaza", [], {})

        def test_existent_hook_creation_all_pos_args(self, hook_provider_factory):
            hook = hook_provider_factory.create_hook("hook", args=[0, 0])

            assert isinstance(hook, Hook1)
            assert hook.a == 0
            assert hook.b == 0

        def test_existent_hook_creation_all_keyword_args(self, hook_provider_factory):
            hook = hook_provider_factory.create_hook("hook", kwargs={"a": 0, "b": 0})

            assert isinstance(hook, Hook1)
            assert hook.a == 0
            assert hook.b == 0

        def test_existent_hook_creation_pos_keyword_args(self, hook_provider_factory):
            hook = hook_provider_factory.create_hook("hook", args=[0], kwargs={"b": 0})

            assert isinstance(hook, Hook1)
            assert hook.a == 0
            assert hook.b == 0

    class TestProviderCreation:
        """Tests for provider creation."""
        def test_nonexistent_provider_creation(self, hook_provider_factory):
            with pytest.raises(KeyError):
                hook_provider_factory.create_provider("azaza", [], {})

        def test_existent_prov_creation_all_pos_args(self, hook_provider_factory):
            hook = hook_provider_factory.create_provider("Provider1", args=[0, 0])

            assert isinstance(hook, Provider1)
            assert hook.a == 0
            assert hook.b == 0

        def test_existent_prov_creation_all_keyword_args(self, hook_provider_factory):
            hook = hook_provider_factory.create_provider("Provider1",
                                                         kwargs={"a": 0, "b": 0})

            assert isinstance(hook, Provider1)
            assert hook.a == 0
            assert hook.b == 0

        def test_existent_prov_creation_pos_keyword_args(self, hook_provider_factory):
            hook = hook_provider_factory.create_provider("Provider1",
                                                         args=[0],
                                                         kwargs={"b": 0})

            assert isinstance(hook, Provider1)
            assert hook.a == 0
            assert hook.b == 0
