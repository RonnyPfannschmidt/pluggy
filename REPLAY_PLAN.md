### Pluggy refactorings replay plan (for LLM agent)

This document instructs an LLM agent to re-apply the local experimental changes from branch `try-claude` onto a fresh branch from `main`, but as a sequence of clean, full-scope refactorings. Each step is intended to be one commit with a coherent purpose, a clear API boundary, and updated tests. Do not cherry-pick; re-implement with intent.

## Summary of changes made in `try-claude` branch:

The branch contains a substantial refactoring of pluggy's internals with multiple iterations and back-and-forth changes:

1. **Module reorganization**: Split monolithic `_hooks.py` into specialized modules:
   - `_hook_config.py`: Configuration classes (HookspecConfiguration, HookimplConfiguration)
   - `_hook_markers.py`: Marker decorators (HookspecMarker, HookimplMarker)
   - `_hook_callers.py`: Hook caller implementations (HookCaller, HistoricHookCaller, HookImpl)
   - `_project.py`: ProjectSpec unification layer

## Proposed improved module naming:

Current module layout has some confusion - both `_callers.py` and `_hook_callers.py` exist, and the `_hook_` prefix is inconsistent. Here's a cleaner organization:

**Proposed structure:**
- `_config.py`: Configuration classes (HookspecConfiguration, HookimplConfiguration, TypedDicts)
- `_decorators.py`: Marker decorators (HookspecMarker, HookimplMarker) and HookSpec
- `_caller.py`: Hook caller implementations (HookCaller protocol, NormalHookCaller, HistoricHookCaller, SubsetHookCaller)
- `_implementation.py`: Hook implementation classes (HookImpl, NormalImpl, WrapperImpl)
- `_execution.py`: Execution engine (_multicall, CompletionHook pattern) - currently in `_callers.py`
- `_project.py`: ProjectSpec (unchanged - good name)
- `_async.py`: Async support (unchanged - good name)
- `_hooks.py`: Compatibility re-export layer (unchanged - needed for backward compat)

2. **Architecture improvements**:
   - Split HookCaller into protocol + concrete implementations (NormalHookCaller, HistoricHookCaller)
   - Separated normal and wrapper hook implementations with distinct storage lists
   - Introduced completion hook pattern for simplified wrapper execution

3. **Configuration migration**:
   - Replaced legacy TypedDict options with typed configuration classes
   - Markers now attach configuration objects directly to functions
   - Added validation (e.g., historic and firstresult cannot both be true)

4. **Async support**:
   - Added greenlet-based async support in `_async.py`
   - Integrated Submitter pattern for awaitable handling
   - PluginManager.run_async() method for async context

5. **ProjectSpec unification**:
   - Central project management class that creates markers and managers
   - Consistent project_name handling across all components

6. **Notable implementation details**:
   - Multiple commits show refactoring done then undone (e.g., commits ef390af then e58e3c9)
   - Some commits are fixups of rebase artifacts (e1c1289)
   - Duplication in git log suggests multiple attempts at same changes

Constraints:
- Base branch: `main` (upstream)
- Preserve public API behavior unless explicitly stated. Maintain back-compat via re-exports and aliases where indicated.
- Keep changes self-contained per step; ensure tests pass after each step.
- Prefer readable, explicit types; keep `Final` annotations at class level; use `__slots__` consistently.
- Avoid incidental formatting churn. Only touch files listed by the step’s scope.

Execution checklist for every step:
- Implement code changes (files listed in Scope).
- Update or add tests as specified; ensure the test suite passes for that step.
- Run static checks and linters.
- Commit with the provided message template.


### 1) Module reorganization foundation (no behavior change)
Goal: Split monolithic hook code into organized modules with back-compat re-exports.

Scope:
- Create new modules by moving existing content out of `src/pluggy/_hooks.py` without behavior changes:
  - `src/pluggy/_config.py`: Configuration types and helpers
  - `src/pluggy/_decorators.py`: Marker decorators and HookSpec
  - `src/pluggy/_caller.py`: Hook caller classes
  - `src/pluggy/_implementation.py`: Hook implementation classes
  - `src/pluggy/_execution.py`: Multicall execution logic
- Update `src/pluggy/_hooks.py` to re-export public symbols from the new modules to preserve old import paths.

Details:
- Move configuration TypedDicts (HookspecOpts, HookimplOpts) to `_config.py`.
- Move marker decorators (HookspecMarker, HookimplMarker) and HookSpec to `_decorators.py`.
- Move HookCaller and HookRelay to `_caller.py`.
- Move HookImpl to `_implementation.py`.
- Move _multicall and execution logic to `_execution.py`.
- Keep `_hooks.py` as a compatibility layer that re-exports everything.
- Preserve internal names like `_HookCaller`, `_HookRelay` as aliases.

Back-compat:
- Maintain all existing imports from `pluggy._hooks` via re-exports.
- Keep varnames() utility in `_decorators.py` with re-export.

Tests:
- No semantic changes; only adapt imports in tests if necessary. All existing tests must pass.

Commit message:
- chore(structure): reorganize into _config, _decorators, _caller, _implementation, and _execution modules


### 2) Introduce configuration classes in `_config`
Goal: Add `HookspecConfiguration` and `HookimplConfiguration` alongside legacy `HookspecOpts`/`HookimplOpts` in the config module.

Scope:
- Add `HookspecConfiguration` and `HookimplConfiguration` classes to `src/pluggy/_config.py`.
- Keep `HookspecOpts`/`HookimplOpts` (TypedDict) in the same module for backward compatibility.
- Add type aliases and helper functions for configuration handling.

Details:
- `HookspecConfiguration(firstresult: bool = False, historic: bool = False, warn_on_impl: Warning | None = None, warn_on_impl_args: Mapping[str, Warning] | None = None)` with validation that historic and firstresult are not both true.
- `HookimplConfiguration(wrapper: bool = False, hookwrapper: bool = False, optionalhook: bool = False, tryfirst: bool = False, trylast: bool = False, specname: str | None = None)` with validation.
- Add helper functions to convert between legacy dicts and configuration objects.
- Keep existing TypedDicts for compatibility.

Back-compat:
- Full backward compatibility maintained - existing code using dicts continues to work.
- Internal code gradually migrates to configuration objects.

Tests:
- Add unit tests for the configuration classes' validation and conversion helpers.
- Ensure existing tests pass without modification.

Commit message:
- feat(config): add HookspecConfiguration and HookimplConfiguration classes alongside legacy TypedDicts


### 3) Update markers to attach configuration objects
Goal: Modify HookspecMarker and HookimplMarker to attach configuration objects to decorated functions.

Scope:
- Update `HookspecMarker.__call__` and `HookimplMarker.__call__` in `src/pluggy/_decorators.py`.
- Markers attach configuration objects as `<project_name>_spec` and `<project_name>_impl` attributes.
- Support both direct decoration and factory patterns.

Details:
- When markers are called, they create HookspecConfiguration or HookimplConfiguration objects.
- These are attached to the function with project-specific attribute names.
- Markers continue to accept the same parameters as before for compatibility.
- The configuration objects are used internally instead of legacy dicts.

Back-compat:
- Markers accept the same parameters as before.
- Functions decorated with markers get configuration objects attached.
- Existing code that looks for legacy attributes still works via compatibility layer.

Tests:
- Update marker tests to verify configuration objects are attached.
- Ensure both decoration patterns work correctly.

Commit message:
- feat(decorators): attach configuration objects to decorated functions


### 4) Split HookCaller architecture and hook implementation types
Goal: Create protocol-based hook caller architecture with separate normal and historic callers, and split hook implementations.

Scope:
- Define `HookCaller` protocol in `src/pluggy/_caller.py`.
- Implement `NormalHookCaller` and `HistoricHookCaller` concrete classes in `_caller.py`.
- Move hook implementations to `src/pluggy/_implementation.py`:
  - Base `HookImpl` class
  - `NormalImpl` for regular hooks
  - `WrapperImpl` for wrapper hooks
- Add `_insert_hookimpl_into_list()` helper in `_caller.py` for proper ordering.

Details:
- HookCaller protocol defines common interface (name, spec, get_hookimpls, etc.).
- HistoricHookCaller handles historic hooks with call history replay.
- NormalHookCaller maintains two lists: `_normal_hookimpls` and `_wrapper_hookimpls`.
- Historic hooks don't support wrappers.
- Keep `_HookCaller` and `_HookRelay` as compatibility aliases.

Back-compat:
- All existing public APIs preserved through protocol and aliases.
- Internal split is transparent to users.

Tests:
- Update tests to cover new architecture.
- Add tests for proper hook ordering in split lists.

Commit message:
- refactor(caller): split HookCaller into protocol and concrete implementations with separate implementation types


### 5) Simplify execution with completion hooks
Goal: Refactor _multicall to use completion hooks for cleaner wrapper execution.

Scope:
- Update `src/pluggy/_execution.py` to introduce `CompletionHook` pattern.
- Modify `_multicall()` to collect completion hooks from wrappers.
- Move argument verification from _multicall to HookImpl classes in `_implementation.py`.

Details:
- Wrappers yield once for setup, then return a completion hook.
- Completion hooks are executed LIFO after all normal hooks.
- Exception handling defers raising until after completion hooks.
- Cleaner separation of setup/teardown phases.

Back-compat:
- Observable behavior unchanged.
- All existing wrapper patterns continue to work.

Tests:
- Update test_multicall.py for new execution model.
- Add tests for completion hook ordering.

Commit message:
- refactor(execution): introduce completion hooks for wrapper teardown


### 6) Async support via greenlets
Goal: Allow hook implementations to return awaitables that are consumed when run within an async-enabled context.

Scope:
- Add `src/pluggy/_async.py` with `Submitter` and utilities to bridge awaitables using greenlets.
- Integrate async submitter into `PluginManager` (new `run_async` method) and `_multicall` (use `async_submitter.maybe_submit` for awaitables returned by hooks).

Details:
- `PluginManager.run_async(func)` temporarily wraps `_inner_hookexec` so `maybe_submit` is threaded through.
- `_multicall` checks `isinstance(res, Awaitable)` and funnels through submitter.

Back-compat:
- No change when not using `run_async`. Raise clear errors if `greenlet` is missing.

Tests:
- Add `testing/test_async.py` covering awaiting hook results and error cases.

Commit message:
- feat(async): add greenlet-based async support and integrate into hook execution


### 7) Add ProjectSpec unification layer
Goal: Introduce ProjectSpec class for unified project configuration.

Scope:
- Create `src/pluggy/_project.py` with `ProjectSpec` class.
- ProjectSpec manages project_name, creates markers and plugin managers.
- Update PluginManager to accept ProjectSpec.
- Update markers to work with ProjectSpec.

Details:
- `ProjectSpec(project_name, plugin_manager_cls=None)` creates hookspec/hookimpl markers.
- Provides `create_plugin_manager()` method.
- Has `get_hookspec_config()` and `get_hookimpl_config()` helpers.
- All components share the same project_name.

Back-compat:
- PluginManager still accepts string project_name.
- Existing code continues to work unchanged.

Tests:
- Add test_project_spec.py for ProjectSpec functionality.
- Update existing tests to also test ProjectSpec path.

Commit message:
- feat(project): add ProjectSpec for unified project configuration


### 8) Type quality and robustness sweep
Goal: Improve type clarity and internal invariants without behavior change.

Scope:
- Move `Final` annotations to class level where appropriate; annotate `__slots__` classes more explicitly.
- Tidy minor internal dependencies.

Tests:
- No new tests required; ensure suite remains green.

Commit message:
- chore(types): move `Final` to class level; annotate `__slots__` classes




### 9) Update public API exports
Goal: Update __init__.py and ensure all new components are properly exported.

Scope:
- Update `src/pluggy/__init__.py` to export new classes.
- Add HistoricHookCaller to exports.
- Add configuration classes to exports.
- Add ProjectSpec to exports.

Details:
- Maintain all existing exports.
- Add new exports for public API components.
- Ensure proper organization of imports.

Back-compat:
- All existing exports maintained.
- New exports are additive only.

Tests:
- Verify all public APIs are accessible.

Commit message:
- feat(api): export new public API components


### 10) Tests and benchmarks adaptations
Goal: Align tests and benchmarks with new APIs and structure.

Scope:
- Update `testing/benchmark.py` to use new configuration extraction.
- Add comprehensive tests for new features.
- Add async tests if implementing async support.

Commit message:
- test: update tests for new architecture and features


### 11) Documentation and tooling
Goal: Add development documentation and tooling configuration.

Scope:
- Add CLAUDE.md with development guidance.
- Update pre-commit and CI configurations.
- Add any necessary tooling files.

Commit message:
- docs(tooling): add development documentation and tooling updates


### Final notes for the agent

**Important learnings from the experimental branch:**
1. The branch had multiple attempts and reversals - avoid this by implementing each step cleanly and completely
2. Some refactorings were attempted multiple times (see duplicate commits) - plan carefully before implementing
3. Module split should happen early to establish clean boundaries
4. Configuration objects should be introduced gradually alongside legacy support
5. Async support can be added as an optional feature without breaking existing code

**Key principles:**
- Verify after each step that the public API surface preserved by `pluggy` remains compatible (imports from `pluggy._hooks` continue to work due to re-exports).
- When in doubt, keep backward-compat names (`_HookCaller`, `_HookRelay`) via aliases.
- Each step should result in a working system with all tests passing.
- Avoid temporary breakage or partial implementations.
- Keep commits focused and atomic - one concept per commit.

**Implementation order rationale:**
1. First split modules to establish structure
2. Add configuration classes while maintaining compatibility
3. Update markers to use configuration objects
4. Split hook caller architecture for cleaner separation
5. Simplify multicall execution model
6. Add async as optional feature
7. Add ProjectSpec for better API
8. Clean up types and exports
9. Update tests comprehensively
10. Add documentation

This order ensures each step builds on the previous one without requiring later changes to earlier work.
