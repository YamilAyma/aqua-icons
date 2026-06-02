import os
import io
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

def main():
    icons_dir = Path(__file__).resolve().parent.parent / "icons"
    if not icons_dir.exists():
        print("No icons folder found.")
        return
    
    # Busca subcarpetas de packs
    packs = sorted([
        d for d in icons_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ], key=lambda x: x.name)

    if not packs:
        print("No icon packs found inside icons/.")
        return

    print(f"Total packs found: {len(packs)}")
    print("=" * 40)

    total_icons_count = 0

    for pack in packs:
        icons = sorted([
            f.stem for f in pack.iterdir()
            if f.is_file() and f.suffix.lower() == ".png"
        ])
        total_icons_count += len(icons)
        print(f"\n📦 {pack.name} ({len(icons)} icons)")
        print("-" * 30)
        if not icons:
            print("  (empty)")
        else:
            for icon in icons:
                print(f"  • {icon}")

    print("\n" + "=" * 40)
    print(f"Grand Total: {total_icons_count} icons across {len(packs)} pack(s).")

if __name__ == "__main__":
    main()
