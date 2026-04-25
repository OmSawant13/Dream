
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from friday.tools.wellness import log_hydration, check_wellness_status, log_posture_check

def test_wellness():
    print("--- TESTING WELLNESS PROTOCOLS ---")
    
    print(log_hydration(250))
    print(log_posture_check())
    
    status = check_wellness_status()
    print(f"Status: {status}")
    
    print("--- WELLNESS TEST COMPLETE ---")

if __name__ == "__main__":
    test_wellness()
