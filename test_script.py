#!/usr/bin/env python3
"""
Test script for demonstrating Vibethon's automatic debugging capabilities
"""

def divide_numbers(a, b):
    """Function that may cause division by zero"""
    print(f"Attempting to divide {a} by {b}")
    result = a / b
    print(f"Result: {result}")
    return result

def access_list_item(items, index):
    """Function that may cause index error"""
    print(f"Accessing item at index {index} from list: {items}")
    item = items[index]
    print(f"Found item: {item}")
    return item

def process_data():
    """Function that calls other functions and may encounter errors"""
    print("Starting data processing...")
    
    # This will work fine
    numbers = [1, 2, 3, 4, 5]
    first_item = access_list_item(numbers, 0)
    print(f"First item: {first_item}")
    
    # This will cause an IndexError
    # When this fails, you can inspect variables and even fix the issue
    big_item = access_list_item(numbers, 10)
    
    # This will cause a ZeroDivisionError
    # When this fails, you can continue with a different value
    result = divide_numbers(10, 0)
    
    print(f"Processing complete! Final result: {result}")
    return result

def working_function():
    """A function that works perfectly to show normal execution"""
    print("This function works without any issues!")
    data = {"name": "Vibethon", "version": "1.0", "status": "working"}
    for key, value in data.items():
        print(f"{key}: {value}")
    return data

if __name__ == "__main__":
    print("🧪 Testing Vibethon Automatic Debugger")
    print("=" * 50)
    
    print("\n1. Testing working function...")
    working_function()
    
    print("\n2. Testing functions with errors...")
    print("   (When errors occur, you'll enter debug mode)")
    print("   Try these commands in the debug REPL:")
    print("   - 'vars' to see variables")
    print("   - 'items = [1, 2, 3]' to fix the list")
    print("   - 'continue 42' to continue with a specific value")
    print("   - 'quit' to exit debugging")
    print()
    
    try:
        result = process_data()
        print(f"\n✅ Script completed successfully! Final result: {result}")
    except Exception as e:
        print(f"\n❌ Script ended with error: {e}") 