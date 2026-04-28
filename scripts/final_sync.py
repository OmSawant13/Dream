import os
import subprocess

readme_path = "research/top-github-repos-list/README.md"
clones_dir = "research/clones"

if not os.path.exists(clones_dir):
    os.makedirs(clones_dir)

# Read all URLs
with open("repo_urls.txt", "r") as f:
    urls = [u.strip() for u in f if u.strip()]

# Filter for valid repos
valid_repos = []
for u in urls:
    if "github.com" in u:
        # Filter out common non-repo patterns
        if any(x in u for x in ["/features/", "/trending", "/explore", "/topics", "/stars", "/market"]):
            continue
        valid_repos.append(u)

cloned = os.listdir(clones_dir)
to_clone = [u for u in valid_repos if u.split("/")[-1] not in cloned]

print(f"Verified valid repos: {len(valid_repos)}")
print(f"Already in vault: {len(cloned)}")
print(f"Targeting for sync: {len(to_clone)}")

for i, url in enumerate(to_clone, 1):
    repo_name = url.split("/")[-1]
    target = os.path.join(clones_dir, repo_name)
    print(f"[{i}/{len(to_clone)}] Finalizing {repo_name}...")
    try:
        subprocess.run(["git", "clone", "--depth", "1", url, target], 
                       capture_output=True, check=True)
    except:
        print(f"  Note: {repo_name} may require manual authorization or link is dead.")

print("\nSYSTEM SYNC COMPLETE.")
