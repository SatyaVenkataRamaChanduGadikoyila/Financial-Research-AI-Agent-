#!/usr/bin/env python3
"""Portfolio feature verification"""
import sys
import ast

try:
    # Check syntax by parsing the file
    with open(r'd:\AIProject\app.py', 'r') as f:
        code = f.read()
    
    ast.parse(code)
    print("✓ app.py syntax is valid")
    
    # Check for required functions
    required_functions = [
        'get_portfolio_metrics',
        'add_to_portfolio',
        'remove_from_portfolio'
    ]
    
    for func in required_functions:
        if f'def {func}' in code:
            print(f"✓ Function '{func}' found")
        else:
            print(f"✗ Function '{func}' NOT found")
            sys.exit(1)
    
    # Check for portfolio session state
    if 'st.session_state.portfolio' in code:
        print("✓ Portfolio session state found")
    else:
        print("✗ Portfolio session state NOT found")
        sys.exit(1)
    
    # Check for portfolio UI section
    if '💼 Portfolio' in code:
        print("✓ Portfolio UI section found")
    else:
        print("✗ Portfolio UI section NOT found")
        sys.exit(1)
    
    # Check for portfolio metrics display
    if 'get_portfolio_metrics' in code and 'total_value' in code:
        print("✓ Portfolio metrics calculation found")
    else:
        print("✗ Portfolio metrics NOT properly implemented")
        sys.exit(1)
    
    print("\n✓ All portfolio features verified successfully!")
    
except SyntaxError as e:
    print(f"✗ Syntax error in app.py: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
