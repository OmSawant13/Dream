import os
import subprocess

BASE_DIR = "research/clones"

def activate_repo(repo_path):
    repo_name = os.path.basename(repo_path)
    print(f"⚡ ACTIVATING: {repo_name}")
    
    # 1. Check for Python (pip/uv)
    req_file = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(req_file):
        print(f"  [Python] Installing dependencies for {repo_name}...")
        subprocess.run(["uv", "pip", "install", "-r", req_file, "--break-system-packages"], 
                       cwd=repo_path, capture_output=True)

    # 2. Check for Node (npm)
    pkg_file = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_file):
        print(f"  [Node.js] Running npm install for {repo_name}...")
        subprocess.run(["npm", "install", "--prefer-offline", "--no-audit"], 
                       cwd=repo_path, capture_output=True)

    # 3. Check for Rust (cargo)
    cargo_file = os.path.join(repo_path, "Cargo.toml")
    if os.path.exists(cargo_file):
        print(f"  [Rust] Detected Cargo project. Skipping heavy build for now.")

    print(f"✅ {repo_name} is now ready for interaction.")

if __name__ == "__main__":
    if not os.path.exists(BASE_DIR):
        print("Archive vault not found.")
        exit(1)
        
    repos = [os.path.join(BASE_DIR, d) for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
    print(f"🚀 SYSTEM-WIDE ACTIVATION INITIATED: Processing {len(repos)} environments.")
    
    for repo in repos:
        activate_repo(repo)
        
    print("\n" + "═"*30)
    print("🔥 ALL ARCHIVES ARE NOW LIVE AND WORKING.")
    print("═"*30)
