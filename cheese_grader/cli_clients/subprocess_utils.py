"""
Reduce friction of working with subprocess
"""
import logging
import subprocess  # nosec
from typing import Dict, List, Optional

LOGGER = logging.getLogger(__name__)


def execute_get_text(
    command: List[str],
    ignore_error: bool = False,
    # shell: bool = True, # causes cross plat problems, security warnings, etc.
    env: Optional[Dict[str, str]] = None,
) -> str:
    """
    Execute shell command and return stdout txt
    """

    completed = None
    try:
        completed = subprocess.run(  # nosec
            command,
            check=not ignore_error,
            # shell=shell, # causes cross plat problems, security warnings, etc.
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    except subprocess.CalledProcessError as cpe:
        if ignore_error and completed:
            return completed.stdout.decode("utf-8") + completed.stderr.decode("utf-8")
        LOGGER.debug(cpe)
        raise
    else:
        return completed.stdout.decode("utf-8") + completed.stderr.decode("utf-8")
