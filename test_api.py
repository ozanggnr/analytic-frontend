import sys
sys.path.insert(0, r'c:\Users\ozang\OneDrive\Desktop\wolfeemarket\wolfee\backend')

try:
    from main import get_quick_market_data
    print("Calling get_quick_market_data()...")
    result = get_quick_market_data()
    print(f"Success! Got {len(result['stocks'])} stocks")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
