from tests import BaseTest
from rollbar.lib.wrap import wrap_callable, unwrap_callable

# Fixtures
class _SampleClass:
    def instance_method(self, x):
        return f"original:{x}"

    @classmethod
    def class_method(cls, x):
        return f"original_cm:{x}"


class WrapCallableClassTest(BaseTest):
    def setUp(self):
        # Each test gets a fresh subclass so mutations don't bleed between tests.
        self.owner = type("_Owner", (_SampleClass,), {})
        self.calls = []

    def _patch_fn(self, wrapped, *args, **kwargs):
        self.calls.append(("patch_fn", args, kwargs))
        return wrapped(*args, **kwargs)

    def test_class_patch_calls_patch_fn_without_self(self):
        """patch_fn must NOT receive the transport self in args."""
        wrap_callable(self.owner, "instance_method", self._patch_fn)
        instance = self.owner()
        instance.instance_method("hello")
        _, args, _ = self.calls[0]
        # args should be ("hello",), NOT (instance, "hello")
        self.assertEqual(args, ("hello",))

    def test_class_patch_original_still_called(self):
        """The original method must still execute and return its value."""
        wrap_callable(self.owner, "instance_method", self._patch_fn)
        result = self.owner().instance_method("hello")
        self.assertEqual(result, "original:hello")

    def test_class_patch_wrapped_is_bound_method(self):
        """patch_fn's first argument (wrapped) must be a bound method."""
        received = []

        def capturing_patch_fn(wrapped, *args, **kwargs):
            received.append(wrapped)
            return wrapped(*args, **kwargs)

        wrap_callable(self.owner, "instance_method", capturing_patch_fn)
        instance = self.owner()
        instance.instance_method("x")
        import inspect
        self.assertTrue(inspect.ismethod(received[0]))

    def test_class_patch_unwrap_restores_original(self):
        original = self.owner.instance_method
        wrap_callable(self.owner, "instance_method", self._patch_fn)
        unwrap_callable(self.owner, "instance_method", original)
        # After unwrap, patch_fn must NOT be called
        self.owner().instance_method("x")
        self.assertEqual(self.calls, [])

    def test_classmethod_patch_calls_patch_fn_without_cls(self):
        """Classmethod variant: patch_fn args must NOT include cls."""
        wrap_callable(self.owner, "class_method", self._patch_fn)
        self.owner.class_method("y")
        _, args, _ = self.calls[0]
        self.assertEqual(args, ("y",))

    def test_classmethod_patch_original_still_called(self):
        wrap_callable(self.owner, "class_method", self._patch_fn)
        result = self.owner.class_method("y")
        self.assertEqual(result, "original_cm:y")


class WrapCallableInstanceTest(BaseTest):
    def setUp(self):
        self.instance = _SampleClass()
        self.calls = []

    def _patch_fn(self, wrapped, *args, **kwargs):
        self.calls.append(("patch_fn", args, kwargs))
        return wrapped(*args, **kwargs)

    def test_instance_patch_calls_patch_fn_without_self(self):
        """Instance-level patch: patch_fn args must be just the method args."""
        wrap_callable(self.instance, "instance_method", self._patch_fn)
        self.instance.instance_method("hello")
        _, args, _ = self.calls[0]
        self.assertEqual(args, ("hello",))

    def test_instance_patch_original_still_called(self):
        wrap_callable(self.instance, "instance_method", self._patch_fn)
        result = self.instance.instance_method("hello")
        self.assertEqual(result, "original:hello")

    def test_instance_patch_does_not_affect_other_instances(self):
        other = _SampleClass()
        wrap_callable(self.instance, "instance_method", self._patch_fn)
        other.instance_method("x")
        # patch_fn should not have been called for the other instance
        self.assertEqual(self.calls, [])

    def test_instance_patch_unwrap_restores_original(self):
        wrap_callable(self.instance, "instance_method", self._patch_fn)
        unwrap_callable(self.instance, "instance_method")
        self.instance.instance_method("x")
        self.assertEqual(self.calls, [])

    def test_class_and_instance_patch_args_are_identical(self):
        """Class-level and instance-level patches must pass the same args to patch_fn."""
        class_calls = []
        instance_calls = []

        owner_cls = type("_Owner", (_SampleClass,), {})
        owner_inst = owner_cls()

        wrap_callable(owner_cls, "instance_method", lambda w, *a, **kw: class_calls.append(a) or w(*a, **kw))
        wrap_callable(owner_inst, "instance_method", lambda w, *a, **kw: instance_calls.append(a) or w(*a, **kw))

        owner_inst.instance_method("z")

        self.assertEqual(class_calls, instance_calls)
