from collections import Counter

import pytest

from ProviderHookFramework import factory


def test_hook_class_checker(hook):
    analyser = factory._HookAnalyser()
    assert analyser.right_class_type(hook.__class__)
    assert not analyser.right_class_type(int)


@pytest.mark.parametrize("amount", [1, 2])
def test_hook_analyser(amount):
    analyser = factory._HookAnalyser()
    for _ in range(amount):
        analyser.analyse("factory_obj")

    analyser_classes = Counter(analyser.get_hooks().keys())
    expected = Counter(["hook", "Hook1", "Hook2", "AbstractHook"])
    assert analyser_classes == expected


def test_add_class_to_dict():
    analyser = factory._HookAnalyser()
    analyser._add_class_to_dict("kek", object)
    analyser._add_class_to_dict("waw", object)
    with pytest.raises(factory.AliasDoublingError):
        analyser._add_class_to_dict("kek", int)
    assert list(analyser.get_hooks().keys()) == ["kek", "waw"]


def test_hook_same_ailas():
    analyser = factory._HookAnalyser()
    analyser.analyse("factory_obj")

    with pytest.raises(factory.AliasDoublingError):
        analyser.analyse("factory_obj/hooks_package/hook2.py")


def test_provider_class_checker(complex_provider):
    analyser = factory._ProviderAnalyser()
    assert analyser.right_class_type(complex_provider.__class__)
    assert not analyser.right_class_type(int)


def test_provider_analyser():
    analyser = factory._ProviderAnalyser()
    analyser.analyse("factory_obj")

    analyser_classes = Counter(analyser.get_providers().keys())
    expected = Counter(["Provider1", "BlockingContentProvider"])
    assert analyser_classes == expected
