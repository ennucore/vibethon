# Vibethon - Automatic Python Debugger 🐍✨

Vibethon is an enhanced Python debugger that automatically instruments your code to provide interactive debugging capabilities whenever errors occur. No more adding `breakpoint()` calls or struggling with complex debugger setups!

## 🌟 Features

- **🔧 Automatic Function Instrumentation**: All functions are automatically wrapped with error handling as they're defined or imported
- **🎯 Interactive REPL**: When errors occur, you get an interactive debugging session right in the error context
- **🚀 Runtime Instrumentation**: Functions are instrumented dynamically as modules are loaded
- **➡️ Continue Execution**: Fix issues and continue execution from the error point
- **🔗 Compatible**: Works transparently with any existing Python script or module
- **🎮 User-Friendly**: Simple command-line interface, just like running `python` but with superpowers

## 📦 Installation

### Option 1: Install from source (recommended for development)

```bash
# Clone or navigate to the vibethon directory
cd /path/to/vibethon

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Option 2: Direct usage (without installation)

You can also run vibethon directly after setting up dependencies:

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run directly
python vibethon_cli.py script.py
```

### Option 3: Development with Cursor DevContainer (Recommended for contributors)

This project includes a pre-configured devcontainer for seamless development in Cursor:

1. **Open in Cursor**: Open the vibethon directory in Cursor
2. **Reopen in Container**: When prompted, click "Reopen in Container" or use `Cmd/Ctrl + Shift + P` and select "Dev Containers: Reopen in Container"
3. **Automatic Setup**: The devcontainer will automatically:
   - Install Python and all dependencies
   - Set up the virtual environment
   - Install the package in development mode
   - Configure the development environment

**Benefits of using the devcontainer:**
- Consistent development environment across all contributors
- No need to manually manage Python versions or dependencies
- Pre-configured debugging and linting tools
- Isolated environment that doesn't affect your system Python installation

**To use Vibethon in the devcontainer:**
```bash
# The environment is already set up, just run:
vibethon script.py

# Or for development:
python vibethon_cli.py script.py
```

## 🚀 Usage

Once installed, you can use the `vibethon` command just like you would use `python`:

```bash
# Run a Python script with automatic debugging
vibethon script.py

# Run with command-line arguments
vibethon my_script.py arg1 arg2 --flag

# Run a Python module
vibethon -m my_package.my_module

# Execute Python code directly
vibethon -c "print('Hello from Vibethon!')"
```

## 🎮 Interactive Debugging

When an error occurs in your code, Vibethon automatically starts an interactive debugging session:

```
🐛 ERROR DETECTED: ZeroDivisionError: division by zero
==================================================
Traceback:
  File "test_script.py", line 28, in divide_numbers
    result = a / b

🔍 DEBUG REPL - You are now in the scope where ZeroDivisionError occurred
Available commands:
  - Type any Python expression to evaluate it
  - Use 'locals()' to see local variables
  - Use 'globals()' to see global variables
  - Type 'continue <value>' to continue execution with a return value
  - Type 'continue' to continue execution with None
  - Type 'quit' or 'exit' to exit the debugger
  - Type 'vars' to see current local variables

Current local variables:
  a = 10
  b = 0

debug> 
```

### Debugging Commands

In the debug REPL, you can:

- **Inspect variables**: `print(my_variable)` or just `my_variable`
- **Modify variables**: `my_variable = new_value`
- **See all local variables**: `vars`
- **Run any Python code**: Execute any valid Python expression or statement
- **Continue execution**: `continue` or `continue some_return_value`
- **Exit debugger**: `quit`, `exit`, or `q`

### Example Debugging Session

```python
debug> vars
Local variables:
  a = 10  
  b = 0

debug> b = 1  # Fix the problematic variable
debug> a / b  # Test the fix
→ 10.0

debug> continue a / b  # Continue execution with the corrected result
Continuing execution by setting return value: 10.0
```

## 📝 Example

Here's a simple example to try:

**test_example.py**:
```python
def problematic_function():
    numbers = [1, 2, 3]
    result = numbers[10]  # This will cause an IndexError
    return result

def main():
    print("Starting the program...")
    value = problematic_function()
    print(f"Got value: {value}")

if __name__ == "__main__":
    main()
```

Run it with Vibethon:
```bash
vibethon test_example.py
```

When the IndexError occurs, you'll be dropped into a debug session where you can:
- Inspect the `numbers` list
- Fix the index or modify the list
- Continue execution with a proper value

## 🔧 How It Works

1. **Import Hook**: Vibethon installs a custom import hook that automatically instruments functions as modules are loaded
2. **AST Transformation**: Each function's body is wrapped in try/catch blocks that preserve original line numbers
3. **Error Interception**: When errors occur, instead of crashing, you get an interactive REPL in the error context
4. **Scope Preservation**: The debug session has access to all local and global variables at the point of failure

## 🎯 Advanced Usage

### Multiple Frame Selection

When errors occur in nested function calls, Vibethon lets you choose which frame to debug:

```
Multiple frames available:
  0: test_script.py:45 in main
  1: test_script.py:32 in process_data  
  2: test_script.py:28 in divide_numbers
Select frame (0-2, or press Enter for innermost):
```

### Continuing with Values

You can continue execution and provide return values for failed functions:

```python
debug> continue 42  # The function will return 42 instead of failing
debug> continue [1, 2, 3]  # Return a list
debug> continue {"status": "fixed"}  # Return a dictionary
```

## 🤝 Contributing

Contributions are welcome! The codebase consists of:

- `vibezz.py` - Core debugging functionality
- `vibethon_cli.py` - Command-line interface and import hooks  
- `setup.py` - Package installation configuration

## 📄 License

MIT License - feel free to use this for your debugging needs!

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure `vibezz.py` is in the same directory as `vibethon_cli.py`
2. **Permission errors**: You may need to use `pip install --user .` for user-only installation
3. **Python version**: Requires Python 3.6 or later

### Getting Help

If you encounter issues:
1. Check that all files are in the correct location
2. Try running with `python -v vibethon_cli.py script.py` for verbose output
3. Make sure your script works normally with `python script.py` first

---

**Happy debugging with Vibethon! 🎉** 