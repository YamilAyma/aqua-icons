import os
from pathlib import Path

def main():
    icons_dir = Path(__file__).resolve().parent.parent / "icons"
    if not icons_dir.exists():
        print("No icons folder found.")
        return
    
    icons = sorted([
        f.stem for f in icons_dir.iterdir() 
        if f.is_file() and f.suffix.lower() == ".png"
    ])
    
    print(f"Total icons: {len(icons)}")
    print("-" * 30)
    for icon in icons:
        print(f"• {icon}")

if __name__ == "__main__":
    main()
