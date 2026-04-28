import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

REPOS_FILE = "repo_urls.txt"
CLONE_DIR = "research/clones"
MAX_WORKERS = 8  # Parallel uplink: 8 streams at once

if not os.path.exists(CLONE_DIR):
    os.makedirs(CLONE_DIR)

with open(REPOS_FILE, "r") as f:
    urls = [line.strip() for line in f if line.strip()]

def clone_repo(url):
    repo_name = url.split("/")[-1]
    target_path = os.path.join(CLONE_DIR, repo_name)
    
    if os.path.exists(target_path):
        return f"SKIP: {repo_name}"
        
    try:
        subprocess.run(["git", "clone", "--depth", "1", url, target_path], 
                       check=True, capture_output=True)
        return f"SUCCESS: {repo_name}"
    except Exception as e:
        return f"FAILED: {repo_name} - {e}"

print(f"🚀 INITIALIZING PARALLEL UPLINK: {len(urls)} targets across {MAX_WORKERS} streams.")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    results = list(executor.map(clone_repo, urls))

print("\n" + "═"*30)
print("✅ MASS UPLINK COMPLETE.")
print(f"Total processed: {len(results)}")
print("═"*30)
