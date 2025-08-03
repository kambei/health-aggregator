# check_oura_path.py
try:
    import oura_ring as oura
    import os

    print("\n--- Oura Library Diagnostic ---")
    print("The 'oura' module is being imported from this file path:")
    print(f"-> {oura.__file__}")

    module_path = oura.__file__

    if 'oura_ring' in module_path:
        print("\nResult: This looks CORRECT. The module is from the 'oura-ring' package you installed.")
        print("If you still have errors, the problem may be in the script's logic itself.")
    else:
        print("\nResult: !!! THIS IS THE PROBLEM !!!")
        print("The module is NOT from the 'oura-ring' package.")
        print("This is an old, conflicting library that must be removed.")
        print("\nACTION: Please find and DELETE the directory containing this file, then run 'pip install --upgrade oura-ring' again.")

except ImportError:
    print("\nCould not import the 'oura' library at all.")
    print("Please try installing with 'pip install oura-ring'")

except Exception as e:
    print(f"An unexpected error occurred: {e}")

