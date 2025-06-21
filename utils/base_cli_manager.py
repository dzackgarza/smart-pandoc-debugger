# manager_utils/base_cli_manager.py - V1.7
# Provides a base class for CLI manager applications.
# Enforces contracts by relying on Python's default exception propagation.

import os
import sys
import argparse
import subprocess

from .logger_utils import logger 


class TeamMemberCrashError(subprocess.CalledProcessError):
    """Exception for when a called script (team member) crashes.
       Assumes self.cmd is a non-empty list [executable, ...]."""
    def __init__(self, proc: subprocess.CompletedProcess, message_prefix="Team member script crashed"):
        super().__init__(proc.returncode, proc.args, output=proc.stdout, stderr=proc.stderr)
        self.script_name = os.path.basename(self.cmd[0]) # Crashes if self.cmd is not list[0]
        self.message_prefix = message_prefix

    def __str__(self):
        details = f"{self.message_prefix}: '{self.script_name}' failed with RC {self.returncode}."
        if self.stderr: 
            details += f"\n  Stderr from '{self.script_name}':\n{self.stderr.strip()}"
        return details

class ManagerSetupError(Exception):
    """Exception for logical errors during manager setup."""
    pass


class BaseCliManager:
    """Base class for CLI applications with subcommand dispatching."""
    def __init__(self, manager_name: str, description: str = "Manager Application"):
        self.manager_name = manager_name
        self.arg_parser = argparse.ArgumentParser(description=description)
        self.subparsers = None 
        logger.debug(f"{self.manager_name}: Initialized.", manager_name=self.manager_name)

    def _add_subparsers_support(self, title="Commands", help_text="Available commands", required=True) -> argparse._SubParsersAction:
        """Initializes and returns subparsers. Call once if using subcommands."""
        self.subparsers = self.arg_parser.add_subparsers(
            dest="command", required=required, title=title, help=help_text
        )
        return self.subparsers

    def _setup_cli_commands(self):
        """Subclasses MUST implement this to define CLI arguments/subcommands."""
        raise NotImplementedError(f"{self.manager_name}: _setup_cli_commands not implemented.")

    def _dispatch_command(self, args: argparse.Namespace):
        """Subclasses MUST implement this to execute logic based on parsed CLI args."""
        raise NotImplementedError(f"{self.manager_name}: _dispatch_command not implemented.")

    def run_cli(self):
        """Main CLI execution entry point for manager applications."""
        self._setup_cli_commands()
        
        logger.debug(f"{self.manager_name} CLI: Raw args: {sys.argv[1:]}", manager_name=self.manager_name)
        args = self.arg_parser.parse_args() # Exits on CLI parsing error (status 2 from argparse)
        logger.debug(f"{self.manager_name} CLI: Parsed: '{getattr(args, 'command', 'N/A')}', Args: {vars(args)}", manager_name=self.manager_name)
        
        self._dispatch_command(args) # Core logic. Exceptions propagate and crash script.
        
        logger.debug(f"{self.manager_name} CLI: Command '{getattr(args, 'command', 'N/A')}' completed.", manager_name=self.manager_name)
        sys.exit(0)
