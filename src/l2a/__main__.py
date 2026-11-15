"""`python -m l2a …` runs the same command as the `l2a` launcher.

The launcher (`Scripts\\l2a.exe`) stores the absolute path of the venv's Python, so it stops working when the venv
is moved. This entry point depends only on the Python that runs it.
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
