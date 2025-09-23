# Claude Development Guide for Pluggy

This document provides guidance for AI assistants working on the pluggy codebase.

## Project Overview

Pluggy is a plugin management and hook calling system for Python. It provides:
- A hook specification and implementation system
- Plugin registration and discovery
- Hook calling with various ordering and result handling options
- Support for both normal hooks and wrapper hooks

## Architecture

### Module Organization (as of the refactoring)

The codebase has been reorganized into specialized modules:

- `src/pluggy/_config.py` - Configuration classes (HookspecConfiguration, HookimplConfiguration)
- `src/pluggy/_decorators.py` - Hook markers and decorators
- `src/pluggy/_caller.py` - Hook caller classes (HookCaller, NormalHookCaller, HistoricHookCaller)
- `src/pluggy/_implementation.py` - Hook implementation classes (HookImpl, NormalImpl, WrapperImpl)
- `src/pluggy/_execution.py` - Multicall execution engine
- `src/pluggy/_project.py` - ProjectSpec for unified project configuration
- `src/pluggy/_async.py` - Async support via greenlets
- `src/pluggy/_manager.py` - PluginManager implementation
- `src/pluggy/_hooks.py` - Compatibility layer re-exporting symbols

### Key Design Patterns

1. **Configuration Objects**: Use HookspecConfiguration and HookimplConfiguration instead of dicts
2. **Split Storage**: Normal and wrapper hooks are stored separately in HookCaller
3. **Type Safety**: Extensive use of Final annotations and __slots__ for immutability
4. **Backward Compatibility**: Legacy APIs maintained through compatibility layers

## Testing

When making changes:
1. Run tests: `uv run pytest testing/`
2. Run linting: `uv run pre-commit run --all-files`
3. Run type checking: `uv run mypy src/`

### Test Organization

- `testing/test_*.py` - Unit tests for specific components
- `testing/benchmark.py` - Performance benchmarks
- `testing/test_configuration.py` - Configuration class tests
- `testing/test_async.py` - Async functionality tests
- `testing/test_project_spec.py` - ProjectSpec tests

## Common Tasks

### Adding a New Hook Type

1. Update configuration classes in `_config.py` if needed
2. Modify HookCaller in `_caller.py` for special handling
3. Update `_execution.py` if execution logic changes
4. Add tests for the new functionality

### Modifying Hook Execution

The main execution logic is in `_execution._multicall()`. This function:
1. Builds arguments for each hook implementation
2. Executes hooks in the correct order
3. Handles wrappers (both old-style and new-style)
4. Manages results and exceptions

### Working with Wrappers

There are two types of wrappers:
- **New-style** (`wrapper=True`): Generator-based, receive results via yield
- **Old-style** (`hookwrapper=True`): Receive Result object, can force results

The adapter `old_style_wrapper_to_new_style()` converts old-style to new-style internally.

## Important Compatibility Notes

1. **pytest compatibility**: The parse methods in PluginManager must remain for pytest
2. **TypedDict exports**: HookspecOpts and HookimplOpts must remain exported
3. **Private attributes**: Many attributes start with `_` but are used by pytest

## Code Style

- Use type hints extensively
- Follow existing patterns for new code
- Maintain backward compatibility
- Write comprehensive tests for new features
- Keep commits atomic and well-described

## Async Support

The async support uses greenlets to bridge sync and async code:
- `Submitter` class manages async context
- `PluginManager.run_async()` enables async hook execution
- Hooks can return awaitables when in async context

Note: Full async/await support requires event loop integration.

## Performance Considerations

- Hook calling is performance-critical
- Benchmarks in `testing/benchmark.py` should not regress
- Use `__slots__` for frequently instantiated classes
- Avoid unnecessary allocations in hot paths

## Future Improvements

Areas that could use enhancement:
- Complete async/await integration with event loops
- Better error messages for configuration validation
- Performance optimizations in multicall
- More comprehensive documentation
