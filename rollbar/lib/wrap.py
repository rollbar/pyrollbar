from functools import wraps
from inspect import getattr_static, isclass
from types import MethodType
from typing import Any, Callable, cast


def wrap_func(original: Callable[..., Any], patch_fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wrap a callable so calls are delegated through a patch function.

    :param original: The original callable to wrap.
    :param patch_fn: A callable that receives ``original`` followed by call args/kwargs.

    Returns:
        A wrapper callable that invokes ``patch_fn``.
    """

    @wraps(original)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return patch_fn(original, *args, **kwargs)

    return wrapper


def unwrap_func(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Return the wrapped target for a function when available.

    :param func: A potentially wrapped callable.

    Returns:
        The underlying callable referenced by ``__wrapped__`` or ``func`` itself.
    """

    return getattr(func, "__wrapped__", func)


def unmonkey_patch(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Restore access to the original callable from a monkey-patched wrapper.

    :param func: A callable expected to have been wrapped with ``functools.wraps``.

    Returns:
        The original callable referenced by ``func.__wrapped__``.

    Raises:
        ValueError: If ``func`` does not expose ``__wrapped__``.
    """

    if not hasattr(func, "__wrapped__"):
        raise ValueError("Function is not monkey patched")
    return cast(Callable[..., Any], getattr(func, "__wrapped__"))


def wrap_callable(owner: Any, name: str, patch_fn: Callable[..., Any]) -> Any:
    """
    Patch an attribute on an owner object with a wrapper.

    Supports classmethods by preserving descriptor behavior and binding the
    original method before passing it to ``patch_fn``.

    :param owner: The module, class, or object that owns the attribute.
    :param name: The attribute name to wrap.
    :param patch_fn: A callable receiving the original callable and invocation args.

    Returns:
        The original attribute value prior to wrapping.
    """

    attr = getattr_static(owner, name)

    if isinstance(attr, classmethod):
        original = attr.__func__

        @wraps(original)
        def classmethod_wrapper(cls: type[Any], *args: Any, **kwargs: Any) -> Any:
            return patch_fn(MethodType(original, cls), *args, **kwargs)

        setattr(owner, name, classmethod(cast(Callable[..., Any], classmethod_wrapper)))
        return attr

    original = getattr(owner, name)

    if isclass(owner):
        @wraps(original)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            return patch_fn(original.__get__(self, type(self)), *args, **kwargs)
    else:
        @wraps(original)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return patch_fn(original, *args, **kwargs)

    setattr(owner, name, wrapper)
    return original


def unwrap_callable(owner: Any, name: str, original: Any = None) -> None:
    """
    Restore a previously wrapped attribute on an owner object.

    :param owner: The module, class, or object that owns the attribute.
    :param name: The attribute name to restore.
    :param original: The original attribute value returned by ``wrap_callable``.
        If omitted, the value stored in ``__wrapped__`` by ``functools.wraps`` is used.
    """

    if original is None:
        attr = getattr(owner, name)
        original = getattr(attr, "__wrapped__", attr)
    setattr(owner, name, original)