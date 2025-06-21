# manager_utils/logger_utils.py - V1.0
# Purpose: Provides a simple, globally accessible logger for the SDE.
# Debug messages are conditional on the 'DEBUG' environment variable.

import os
import sys
from datetime import datetime

class SdeLogger:
    def __init__(self):
        # DEBUG_MODE is determined once when the logger is instantiated.
        # Scripts should import 'logger' from this module to get this instance.
        self.DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true"
        self.log_prefix_override = None # For testing or special contexts

    def _get_prefix(self, level: str, manager_name: str = None) -> str:
        """Generates a standardized log prefix."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] # Milliseconds
        prefix_parts = [timestamp, level.upper()]
        
        # Attempt to get the calling script's name for more context if manager_name not provided
        # This can be a bit fragile, so it's a best-effort.
        actual_prefix = self.log_prefix_override
        if not actual_prefix:
            if manager_name:
                actual_prefix = manager_name.upper()
            else:
                try:
                    # Get the name of the script that called the logger method.
                    # This involves looking up the call stack, which can be complex.
                    # A simpler way is for each manager to pass its name.
                    # For now, let's keep it simple or require manager_name.
                    # Using sys.argv[0] as a proxy for the current script.
                    calling_script = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "SDE"
                    actual_prefix = calling_script.upper().replace(".PY","")

                except Exception:
                    actual_prefix = "SDE_LOG" # Fallback
        
        prefix_parts.append(f"({actual_prefix})")
        return " ".join(prefix_parts) + ":"

    def debug(self, message: str, manager_name: str = None):
        """Prints a debug message to stderr if DEBUG_MODE is enabled."""
        if self.DEBUG_MODE:
            print(f"{self._get_prefix('debug', manager_name)} {message}", file=sys.stderr)
            sys.stderr.flush() # Ensure immediate output for debugging

    def info(self, message: str, manager_name: str = None):
        """Prints an informational message to stderr (always prints)."""
        # Info messages are generally always shown, not dependent on DEBUG_MODE,
        # but for this tool, stderr is primarily for debug/errors.
        # Let's make info also conditional on DEBUG for now to keep stderr clean unless debugging.
        # If truly general info is needed on stderr, this condition can be removed.
        if self.DEBUG_MODE:
            print(f"{self._get_prefix('info', manager_name)} {message}", file=sys.stderr)
            sys.stderr.flush()

    def warning(self, message: str, manager_name: str = None):
        """Prints a warning message to stderr (always prints)."""
        print(f"{self._get_prefix('warning', manager_name)} {message}", file=sys.stderr)
        sys.stderr.flush()

    def error(self, message: str, manager_name: str = None):
        """Prints an error message to stderr (always prints)."""
        print(f"{self._get_prefix('error', manager_name)} {message}", file=sys.stderr)
        sys.stderr.flush()

    def set_log_prefix_override(self, prefix: str = None):
        """Allows overriding the script name prefix, useful for tests."""
        self.log_prefix_override = prefix

# Create a single, globally accessible logger instance.
# Other modules will do: from manager_utils.logger_utils import logger
logger = SdeLogger()

if __name__ == "__main__":
    # Example usage and test for the logger
    print("Testing SdeLogger (these messages go to stderr if DEBUG is true, or only WARNING/ERROR otherwise):")
    
    # Test with DEBUG off (default unless DEBUG=true is in env)
    print("\n--- Testing with DEBUG potentially OFF ---")
    logger.debug("This is a debug message (should not appear unless DEBUG=true).", manager_name="LoggerTest")
    logger.info("This is an info message (should not appear unless DEBUG=true).", manager_name="LoggerTest")
    logger.warning("This is a warning message (should appear).", manager_name="LoggerTest")
    logger.error("This is an error message (should appear).", manager_name="LoggerTest")

    # Test with DEBUG explicitly enabled for this block
    print("\n--- Testing with DEBUG explicitly ON for logger instance ---")
    logger.DEBUG_MODE = True # Force debug mode for this test
    logger.set_log_prefix_override("TEST_LOGGER") # Test prefix override
    logger.debug("This is a debug message (should appear).")
    logger.info("This is an info message (should appear).")
    logger.warning("This is a warning message (should appear).")
    logger.error("This is an error message (should appear).")
    logger.set_log_prefix_override() # Clear override
    logger.DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true" # Reset to env

    print("\nTo see debug/info messages above, run with DEBUG=true environment variable:")
    print("  DEBUG=true python3 manager_utils/logger_utils.py")
