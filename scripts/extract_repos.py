import re
import os

readme_path = "research/top-github-repos-list/README.md"
urls_file = "repo_urls.txt"

with open(readme_path, "r") as f:
    content = f.read()

# Match standard markdown links and plain URLs
# Focus on github.com
# Also extract from within google search links if they contain a github URL
pattern = r"https?://(?:www\.)?github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+"
raw_urls = re.findall(pattern, content)

# Clean up URLs (remove trailing characters that might be caught)
clean_urls = set()
for url in raw_urls:
    # Remove trailing ), ], ., , etc.
    u = url.rstrip(").,]>")
    # If it's just the organization, it might not be a repo, but we'll try
    if u.count("/") >= 4: # https://github.com/user/repo
        clean_urls.add(u)

# Sort for consistency
final_urls = sorted(list(clean_urls))

with open(urls_file, "w") as f:
    for url in final_urls:
        f.write(url + "\n")

print(f"Extraction complete: {len(final_urls)} unique repositories identified.")
