"""
Multicall execution engine.
"""

from __future__ import annotations

from collections.abc import Awaitable
from collections.abc import Generator
from collections.abc import Mapping
from collections.abc import Sequence
from typing import cast
from typing import NoReturn
from typing import TYPE_CHECKING
import warnings

from ._implementation import HookImpl
from ._result import HookCallError
from ._result import Result
from ._warnings import PluggyTeardownRaisedWarning


if TYPE_CHECKING:
    from ._async import Submitter


# Type for generator-based hook wrappers
Teardown = Generator[None, object, object]


def old_style_wrapper_to_new_style(
    hook_impl: HookImpl, hook_name: str, args: Sequence[object]
) -> Teardown:
    """
    Adapter that converts an old-style hookwrapper to a new-style wrapper.

    Old-style wrappers receive a Result object and can change the result
    via outcome.force_result() or outcome.force_exception().
    """
    # Call the old-style hookwrapper
    gen: Teardown = cast(Teardown, hook_impl.function(*args))

    # Run the setup phase
    try:
        next(gen)
    except StopIteration:
        _raise_wrapfail(gen, "did not yield")

    # Wait for the result from multicall
    outcome: Result[object]
    try:
        result = yield
    except BaseException as exc:
        # Got an exception - wrap it in Result for old-style
        outcome = Result(None, exc)
        try:
            gen.send(outcome)
        except StopIteration:
            pass
        except BaseException as e:
            _warn_teardown_exception(hook_name, hook_impl, e)
            # Re-raise teardown exceptions from old-style wrappers
            raise
        else:
            _raise_wrapfail(gen, "has second yield")
        finally:
            gen.close()

        # Check if the old-style wrapper forced a different result/exception
        try:
            return outcome.get_result()
        except BaseException as forced_exc:
            raise forced_exc
    else:
        # Got a result - wrap it in Result for old-style
        outcome = Result(result, None)
        try:
            gen.send(outcome)
        except StopIteration:
            pass
        except BaseException as e:
            _warn_teardown_exception(hook_name, hook_impl, e)
            # Re-raise teardown exceptions from old-style wrappers
            raise
        else:
            _raise_wrapfail(gen, "has second yield")
        finally:
            gen.close()

        # Return the result (possibly forced by the old-style wrapper)
        try:
            return outcome.get_result()
        except BaseException as forced_exc:
            raise forced_exc


def _raise_wrapfail(
    wrap_controller: Generator[None, object, object],
    msg: str,
) -> NoReturn:
    co = wrap_controller.gi_code  # type: ignore[attr-defined]
    raise RuntimeError(
        f"wrap_controller at {co.co_name!r} {co.co_filename}:{co.co_firstlineno} {msg}"
    )


def _warn_teardown_exception(
    hook_name: str, hook_impl: HookImpl, e: BaseException
) -> None:
    msg = "A plugin raised an exception during an old-style hookwrapper teardown.\n"
    msg += f"Plugin: {hook_impl.plugin_name}, Hook: {hook_name}\n"
    msg += f"{type(e).__name__}: {e}\n"
    msg += "For more information see https://pluggy.readthedocs.io/en/stable/api_reference.html#pluggy.PluggyTeardownRaisedWarning"  # noqa: E501
    warnings.warn(PluggyTeardownRaisedWarning(msg), stacklevel=6)


def _multicall(
    hook_name: str,
    hook_impls: Sequence[HookImpl],
    caller_kwargs: Mapping[str, object],
    firstresult: bool,
    submitter: Submitter | None = None,
) -> object | list[object]:
    """Execute a call into multiple python functions/methods and return the
    result(s).

    ``caller_kwargs`` comes from HookCaller.__call__().
    """
    __tracebackhide__ = True
    results: list[object] = []
    exception: BaseException | None = None
    teardowns: list[Teardown] = []

    # Execute setup phase and normal hooks
    try:
        for hook_impl in reversed(hook_impls):
            # Build arguments for this implementation
            try:
                args = [caller_kwargs[argname] for argname in hook_impl.argnames]
            except KeyError as e:
                for argname in hook_impl.argnames:  # pragma: no cover
                    if argname not in caller_kwargs:
                        raise HookCallError(
                            f"hook call must provide argument {argname!r}"
                        ) from e

            if hook_impl.hookwrapper:
                # Convert old-style wrapper to new-style and run it
                gen = old_style_wrapper_to_new_style(hook_impl, hook_name, args)
                try:
                    next(gen)  # Run setup
                    teardowns.append(gen)
                except StopIteration:
                    _raise_wrapfail(gen, "did not yield")

            elif hook_impl.wrapper:
                # New-style wrapper
                gen = cast(Teardown, hook_impl.function(*args))
                try:
                    next(gen)  # Run setup
                    teardowns.append(gen)
                except StopIteration:
                    _raise_wrapfail(gen, "did not yield")

            else:
                # Normal hook implementation
                res = hook_impl.function(*args)

                # Handle awaitables if submitter is available
                if submitter is not None and isinstance(res, Awaitable):
                    res = submitter.maybe_submit(res)

                if res is not None:
                    results.append(res)
                    if firstresult:  # halt further impl calls
                        break

    except BaseException as exc:
        exception = exc

    # Determine the result
    if firstresult:
        result = results[0] if results else None
    else:
        result = results

    # Execute teardowns in LIFO order (all are now new-style)
    for teardown in reversed(teardowns):
        try:
            if exception is not None:
                # Send exception to teardown
                teardown.throw(exception)
            else:
                # Send result to teardown
                teardown.send(result)
        except StopIteration as si:
            # Teardown completed - check if it returned a value
            if si.value is not None:
                result = si.value
                exception = None
        except RuntimeError as re:
            # Handle RuntimeError from StopIteration in generator
            if isinstance(exception, StopIteration) and re.__cause__ is exception:
                teardown.close()
                continue
            else:
                exception = re
        except BaseException as e:
            exception = e
            continue
        else:
            _raise_wrapfail(teardown, "has second yield")
        finally:
            try:
                teardown.close()
            except Exception:
                pass

    if exception is not None:
        raise exception
    return result


# Note: Completion hooks are no longer needed since we unified the wrapper handling
