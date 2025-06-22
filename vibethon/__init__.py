"""
Vibethon - Automatic Python Debugger with Interactive REPL
"""

from .vdb import CustomPdb
from .llm import ChatGPTPdbLLM

# Create a global instance that users can import
import os
vdb = CustomPdb(ChatGPTPdbLLM(interactive_mode=os.environ.get('VIBETHON_INTERACTIVE_MODE', 'true').lower() == 'true'))

__version__ = "1.0.1"
__all__ = ["vdb"]