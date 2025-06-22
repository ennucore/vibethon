"""
Vibethon - Automatic Python Debugger with Interactive REPL
"""

from .vdb import CustomPdb
from .llm import ChatGPTPdbLLM

# Create a global instance that users can import
vdb = CustomPdb(ChatGPTPdbLLM())

__version__ = "1.0.1"
__all__ = ["vdb"]