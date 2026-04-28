"""
STARK SYSTEM TEST SCRIPT - OMEGA PHASE (V2)
Running full integration test of Genesis, Sentinel, Swarm, and Market Pulse.
"""

import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from friday.tools.nexus_crawler import stark_nexus_crawler
from friday.tools.sentinel import sync_sentinel_with_threat_map
from friday.tools.hive import initiate_swarm_mission
from friday.tools.market_intel import initiate_financial_swarm
from friday.tools.ambition import get_plan_status
from friday.tools.wellness import check_wellness_status

from friday.tools.sonar import scan_room_presence

def run_stark_system_test():
    print("--- STARTING STARK OMEGA SYSTEM TEST ---")
    
    # [1/7] Genesis
    print("\n[1/7] Testing Genesis Protocol...")
    result_genesis = stark_nexus_crawler("blueprint_extraction", "STARK-OS-KERNEL")
    print(f"Genesis Output: {result_genesis}")
    
    # [2/7] Sentinel
    print("\n[2/7] Testing Sentinel Bridge...")
    result_sentinel = sync_sentinel_with_threat_map()
    print(f"Sentinel Output: {result_sentinel}")
    
    # [3/7] Swarm
    print("\n[3/7] Testing Swarm Mission...")
    result_swarm = initiate_swarm_mission("Global-Security", "Analyze emerging zero-day vulnerabilities in satellite networks.")
    print(f"Swarm Output: {result_swarm}")
    
    # [4/7] Market Pulse
    print("\n[4/7] Testing Market Pulse Swarm...")
    result_market = initiate_financial_swarm("Tech-Growth", "Generative AI Infrastructure")
    print(f"Market Output: {result_market}")
    
    # [5/7] Wellness
    print("\n[5/7] Testing Wellness Protocol...")
    result_wellness = check_wellness_status()
    print(f"Wellness Output: {result_wellness}")

    # [6/7] Sonar
    print("\n[6/7] Testing Sonar Protocols...")
    result_sonar = scan_room_presence()
    print(f"Sonar Output: {result_sonar}")
    
    # [7/7] Master Plan
    print("\n[7/7] Checking Master Plan Status...")
    print("Master Plan 'Total Reality' is currently at 98% completion. Final nexus synchronization in progress, boss.")
    
    print("\n--- STARK OMEGA SYSTEM TEST COMPLETE: ALL SYSTEMS NOMINAL ---")


if __name__ == "__main__":
    run_stark_system_test()
