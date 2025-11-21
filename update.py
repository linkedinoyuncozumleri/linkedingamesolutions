#!/usr/bin/env python3
import os
import re
import sys
import subprocess
from datetime import datetime

# Turkish month names
MONTHS_TR = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}

def format_turkish_date(yyyymmdd: str) -> str:
    """Convert YYYYMMDD into 'DD Ay YYYY' format in Turkish."""
    date_obj = datetime.strptime(yyyymmdd, "%Y%m%d")
    return f"{MONTHS_TR[date_obj.month]} {date_obj.day}, {date_obj.year}"

def parse_li_line(line: str):
    """Extract date from <li> line if possible."""
    match = re.search(r'href="(\d{8})\.html"', line)
    if match:
        yyyymmdd = match.group(1)
        return yyyymmdd, line
    return None, None

def add_entry_to_index(folder: str, yyyymmdd: str) -> bool:
    """Insert and sort a new <li> entry in folder/index.html. Returns True if file changed."""
    index_path = os.path.join(folder, "index.html")
    if not os.path.exists(index_path):
        print(f"❌ {index_path} not found.")
        return False

    display_date = format_turkish_date(yyyymmdd)
    new_line = f'    <li><a href="{yyyymmdd}.html">{display_date}</a></li>\n'

    with open(index_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find <ul> ... </ul> block
    try:
        start = next(i for i, line in enumerate(lines) if "<ul>" in line) + 1
        end = next(i for i, line in enumerate(lines) if "</ul>" in line)
    except StopIteration:
        print(f"❌ No <ul> block found in {index_path}")
        return False

    # Extract all existing li lines
    li_lines = lines[start:end]

    # Parse existing dates
    existing = {}
    for line in li_lines:
        date_str, full_line = parse_li_line(line)
        if date_str:
            existing[date_str] = full_line

    # Add new entry if not duplicate
    changed = False
    if yyyymmdd not in existing:
        existing[yyyymmdd] = new_line
        print(f"✅ Added {yyyymmdd} → {display_date} to {index_path}")
        changed = True
    else:
        print(f"⚠️ {yyyymmdd} already exists in {index_path}, skipping insert.")

    # Sort by date descending
    sorted_dates = sorted(existing.keys(), reverse=True)
    sorted_li_lines = [existing[d] for d in sorted_dates]

    # Rebuild file
    new_lines = lines[:start] + sorted_li_lines + lines[end:]

    with open(index_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return changed

def create_daily_file(folder: str, yyyymmdd: str) -> bool:
    """Create YYYYMMDD.html file in folder with the correct content."""
    daily_path = os.path.join(folder, f"{yyyymmdd}.html")
    if os.path.exists(daily_path):
        print(f"⚠️ {daily_path} already exists, skipping.")
        return False

    display_date = format_turkish_date(yyyymmdd)
    dict_title={"minisudoku": "Mini Sudoku", "zip": "Zip", "queens":"Queens","tango":"Tango"}
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{dict_title[folder]} Solution – {display_date}</title>
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <header>
    <div class="container">
      <a href="/" class="logo">LinkedIn <span>Games</span></a>
      <nav>
        <a href="/">Home</a>
        <a href="/today/">Today's Solutions</a>
        <a href="/about.html">About</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <h1>{dict_title[folder]} – {display_date}</h1>

    <img src="../images/{folder}_{yyyymmdd}.jpeg" alt="{dict_title[folder]} Solution" style="max-width: 60%;">

    <footer>
      <hr>
      <a href="../today/" class="nav">← Back to Today's Solutions</a>
    </footer>
  </main>
</body>
</html>
"""

    with open(daily_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Created {daily_path}")
    return True

def update_root_index(yyyymmdd: str) -> bool:
    """Update root index.html: 🎯 line, <title>, and <meta og:title> with the new date."""
    index_path = "index.html"
    if not os.path.exists(index_path):
        print(f"❌ {index_path} not found.")
        return False

    display_date = format_turkish_date(yyyymmdd)

    # New replacements
    new_list_item = f'    <li><a href="/today/">🎯 {display_date}</a></li>\n'
    new_title = f'  <title>LinkedIn Games Solutions – Mini Sudoku, Zip, Queens & Tango</title>\n'
    new_og_title = f'  <meta property="og:title" content="LinkedIn Games Solutions">\n'

    with open(index_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    changed = False
    for i, line in enumerate(lines):
        if '<a href="/today/">' in line:
            if new_list_item != line:
                lines[i] = new_list_item
                changed = True
        elif line.strip().startswith("<title>"):
            if new_title.strip() != line.strip():
                lines[i] = new_title
                changed = True
        elif 'property="og:title"' in line:
            if new_og_title.strip() != line.strip():
                lines[i] = new_og_title
                changed = True

    if changed:
        with open(index_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"✅ Updated root index.html with {display_date}")
    else:
        print(f"⚠️ Root index.html already up to date.")

    return changed

def update_today_index(yyyymmdd: str) -> bool:
    """Update today/index.html with new date and game card links."""
    today_path = os.path.join("today", "index.html")
    if not os.path.exists(today_path):
        print(f"❌ {today_path} not found.")
        return False

    display_date = format_turkish_date(yyyymmdd)
    changed = False

    with open(today_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("<h1>"):
            new_lines.append(f"    <h1>{display_date}</h1>\n")
            changed = True
        # Match game-card divs and update their links
        elif '<div class="game-card">' in line and i + 2 < len(lines) and lines[i + 1].strip().startswith("<h3>"):
            # This is a game card - find which game it is
            h3_line = lines[i + 1]
            next_a_line_idx = None

            # Find the <a> tag in this game card
            for j in range(i + 2, min(i + 6, len(lines))):
                if '<a href=' in lines[j] and '../' in lines[j]:
                    next_a_line_idx = j
                    break

            new_lines.append(line)  # Add opening div
            new_lines.append(h3_line)  # Add h3

            # Add lines until we find the <a> tag
            i += 2
            while i < len(lines) and i < next_a_line_idx:
                new_lines.append(lines[i])
                i += 1

            # Update the <a> tag with correct date
            if next_a_line_idx and i < len(lines):
                a_line = lines[i]
                if "../minisudoku/" in a_line:
                    new_lines.append(f'        <a href="../minisudoku/{yyyymmdd}.html">View Solution</a>\n')
                    changed = True
                elif "../zip/" in a_line:
                    new_lines.append(f'        <a href="../zip/{yyyymmdd}.html">View Solution</a>\n')
                    changed = True
                elif "../queens/" in a_line:
                    new_lines.append(f'        <a href="../queens/{yyyymmdd}.html">View Solution</a>\n')
                    changed = True
                elif "../tango/" in a_line:
                    new_lines.append(f'        <a href="../tango/{yyyymmdd}.html">View Solution</a>\n')
                    changed = True
                else:
                    new_lines.append(a_line)
        else:
            new_lines.append(line)

        i += 1

    if changed:
        with open(today_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✅ Updated today/index.html for {display_date}")
    else:
        print(f"⚠️ today/index.html already up to date.")

    return changed

def git_commit_changes(yyyymmdd: str, changed_files: list):
    """Create or reuse a git branch, add changes, and commit."""
    if not changed_files:
        print("⚠️ No changes to commit.")
        return

    branch_name = yyyymmdd

    # Check if branch exists
    result = subprocess.run(
        ["git", "branch", "--list", branch_name],
        capture_output=True, text=True
    )

    if result.stdout.strip():
        # Branch exists → checkout
        subprocess.run(["git", "checkout", branch_name], check=True)
        print(f"ℹ️ Branch '{branch_name}' already exists, checking it out.")
    else:
        # Branch does not exist → create new
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        print(f"✅ Created new branch '{branch_name}'.")

    # Stage files
    subprocess.run(["git", "add"] + changed_files, check=True)

    # Commit
    commit_msg = f"Add {yyyymmdd} entry"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)

    print(f"✅ Committed changes in branch '{branch_name}'.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_entry.py YYYYMMDD")
        sys.exit(1)

    yyyymmdd = sys.argv[1]

    if not re.fullmatch(r"\d{8}", yyyymmdd):
        print("❌ Date must be in format YYYYMMDD, e.g., 20250923")
        sys.exit(1)

    folders = ["minisudoku", "zip", "queens", "tango"]
    changed_files = []

    for folder in folders:
        if add_entry_to_index(folder, yyyymmdd):
            changed_files.append(os.path.join(folder, "index.html"))
        if create_daily_file(folder, yyyymmdd):
            changed_files.append(os.path.join(folder, f"{yyyymmdd}.html"))

    if update_root_index(yyyymmdd):
        changed_files.append("index.html")

    if update_today_index(yyyymmdd):
        changed_files.append(os.path.join("today", "index.html"))

    # Run git only if something changed
    if changed_files:
        git_commit_changes(yyyymmdd, changed_files)

