"""
Simple test to verify that the debugger has access to original frame locals.
"""

from llm import DummyLLM
from vdb import CustomPdb
import vibezz

def test_function():
    """A test function with local variables that should be accessible in the debugger."""
    x = 42
    y = "hello world"
    data = [1, 2, 3, 4, 5]
    
    print(f"Before error: x={x}, y={y}, data={data}")
    
    # This will trigger the debugger
    result = x / 0  # Division by zero
    
    return result

def main():
    print("Testing debugger context...")
    
    # Set up dummy LLM for manual testing
    vibezz.llm = DummyLLM()
    
    # Instrument the test function
    instrumented_test = vibezz.instrument_function(test_function)
    
    print("Calling instrumented function (this will trigger debugger)...")
    print("When the debugger starts, try these commands:")
    print("  debug_frame")
    print("  locals")
    print("  pp x")
    print("  pp y") 
    print("  pp data")
    print("  !result = 42  # Try to set result variable")
    print("  pp result")
    print("  list")
    print("  continue")
    print()
    
    try:
        result = instrumented_test()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    main() 