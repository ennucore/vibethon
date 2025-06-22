#!/usr/bin/env python3
"""
Demo script showing how the VDB debugging system works.
This creates a simple function with an error and demonstrates the debugging flow.
"""

import os
from llm import ChatGPTPdbLLM, DummyLLM
from vdb import CustomPdb
import sys

def create_buggy_function():
    """Create a function that will trigger an error for debugging."""
    def buggy_math(a, b, c):
        """A function with a deliberate bug."""
        x = a + b
        y = x * 2
        z = y / c  # This will fail if c is 0
        result = z + 10
        return result
    return buggy_math

def demo_with_dummy_llm():
    """Demo using the DummyLLM (human input) for debugging."""
    print("=== VDB Demo with Manual Input ===")
    print("This demo will trigger an error and let you manually debug it.")
    print("You'll be prompted to enter debugger commands manually.")
    print("Try commands like: list, pp locals(), next, continue")
    print("=" * 50)
    
    # Create the buggy function
    buggy_func = create_buggy_function()
    
    # Create dummy LLM (uses human input)
    llm = DummyLLM()
    
    try:
        # This will trigger the error and start debugging
        result = buggy_func(5, 3, 0)  # Division by zero!
        print(f"Result: {result}")
    except Exception as e:
        print(f"\n🐛 Exception caught: {e}")
        print("Starting debugging session...")
        
        # Create debugger and attach to the exception
        vdb = CustomPdb(llm)
        import traceback
        tb = e.__traceback__
        if tb:
            vdb.set_trace(tb.tb_frame)

def demo_with_chatgpt_llm():
    """Demo using ChatGPT for automated debugging."""
    print("=== VDB Demo with ChatGPT Automation ===")
    print("This demo will trigger an error and let ChatGPT debug it automatically.")
    
    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not found in environment variables")
        print("Please set it with: export OPENAI_API_KEY='your-api-key-here'")
        print("Falling back to manual input demo...")
        demo_with_dummy_llm()
        return
    
    print("=" * 50)
    
    # Create the buggy function
    buggy_func = create_buggy_function()
    
    # Create ChatGPT LLM
    try:
        llm = ChatGPTPdbLLM()
        print("✅ ChatGPT LLM initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ChatGPT LLM: {e}")
        print("Falling back to manual input demo...")
        demo_with_dummy_llm()
        return
    
    try:
        # This will trigger the error and start debugging
        result = buggy_func(10, 5, 0)  # Division by zero!
        print(f"Result: {result}")
    except Exception as e:
        print(f"\n🐛 Exception caught: {e}")
        print("Starting automated debugging session with ChatGPT...")
        
        # Create debugger and attach to the exception
        vdb = CustomPdb(llm)
        import traceback
        tb = e.__traceback__
        if tb:
            vdb.set_trace(tb.tb_frame)

def demo_vibezz_integration():
    """Demo showing integration with the vibezz auto-instrumentation."""
    print("=== VDB Demo with Vibezz Auto-Instrumentation ===")
    print("This demo shows how VDB integrates with vibezz's automatic instrumentation.")
    print("=" * 50)
    
    try:
        # Import vibezz and set up auto-instrumentation
        import vibezz
        
        # Set up the LLM for vibezz
        if os.environ.get('OPENAI_API_KEY'):
            print("Using ChatGPT for debugging...")
            vibezz.llm = ChatGPTPdbLLM()
        else:
            print("No OPENAI_API_KEY found, using manual input...")
            vibezz.llm = DummyLLM()
        
        # Enable auto-instrumentation
        vibezz.vibezz_debugger.auto_instrument()
        print("✅ Auto-instrumentation enabled")
        
        # Create and run a buggy function
        def another_buggy_function():
            """Another function with a bug for testing."""
            data = [1, 2, 3, 4, 5]
            index = 10  # This will cause IndexError
            return data[index]
        
        # This should automatically trigger the debugger when it fails
        result = another_buggy_function()
        print(f"Result: {result}")
        
    except ImportError:
        print("❌ vibezz module not found. Make sure vibezz.py is available.")
    except Exception as e:
        print(f"Demo completed with exception: {e}")

def show_test_function_source():
    """Show the source of the test function for reference."""
    print("\n" + "=" * 50)
    print("TEST FUNCTION SOURCE CODE:")
    print("=" * 50)
    
    import inspect
    func = create_buggy_function()
    source = inspect.getsource(func)
    lines = source.split('\n')
    
    for i, line in enumerate(lines, 1):
        if line.strip():
            print(f"{i:2d}: {line}")
    
    print("\nThis function will fail when c=0 due to division by zero.")
    print("The debugger will stop at the line: z = y / c")

def main():
    """Main demo function."""
    print("🔬 VDB (Vibezz Debugger) Demo")
    print("=" * 50)
    
    show_test_function_source()
    
    print("\nChoose a demo mode:")
    print("1. Manual input (DummyLLM) - You control the debugger")
    print("2. ChatGPT automation - AI controls the debugger") 
    print("3. Vibezz integration - Auto-instrumentation demo")
    print("4. Run all demos")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            demo_with_dummy_llm()
        elif choice == "2":
            demo_with_chatgpt_llm()
        elif choice == "3":
            demo_vibezz_integration()
        elif choice == "4":
            print("\n" + "🔄 Running all demos..." + "\n")
            demo_with_dummy_llm()
            print("\n" + "─" * 50 + "\n")
            demo_with_chatgpt_llm()
            print("\n" + "─" * 50 + "\n")
            demo_vibezz_integration()
        else:
            print("Invalid choice. Running manual demo...")
            demo_with_dummy_llm()
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Demo complete!")

if __name__ == "__main__":
    main() 