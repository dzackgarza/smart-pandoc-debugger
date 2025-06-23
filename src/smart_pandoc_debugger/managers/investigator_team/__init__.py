# This file makes the investigator-team directory a Python package

from .undefined_environment_proofer import (
    find_undefined_environment as find_undefined_environment,
    suggest_package as suggest_environment_package,
    create_actionable_lead as create_environment_lead,
    main as environment_main
)

from .undefined_command_proofer import (
    find_undefined_commands,
    suggest_package as suggest_command_package,
    create_actionable_lead as create_command_lead,
    run_undefined_command_proofer,
    main as command_main
)

__all__ = [
    # Environment proofer exports
    'find_undefined_environment',
    'suggest_environment_package',
    'create_environment_lead',
    'environment_main',
    
    # Command proofer exports
    'find_undefined_commands',
    'suggest_command_package',
    'create_command_lead',
    'run_undefined_command_proofer',
    'command_main'
]
