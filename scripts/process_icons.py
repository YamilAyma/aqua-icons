"""
Aqua Icons — Background Removal Pipeline
=========================================
Automates the workflow:
  raw-icons/ → rembg (BiRefNet) → icons/ → atomic git commit → update README

Usage:
  python scripts/process_icons.py
  python scripts/process_icons.py --dry-run
  python scripts/process_icons.py --no-commit
  python scripts/process_icons.py --model birefnet-general-lite
"""

import argparse
import io
import os
import subprocess
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DIR = PROJECT_ROOT / "raw-icons"
ICONS_DIR = PROJECT_ROOT / "icons"
UPDATE_README_SCRIPT = SCRIPT_DIR / "update-readme.js"

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DEFAULT_MODEL = "u2net"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str, icon: str = "ℹ️") -> None:
    print(f"  {icon} {msg}")


def log_header(msg: str) -> None:
    print(f"\n{'-' * 60}")
    print(f"  {msg}")
    print(f"{'-' * 60}")


def run_git(*args: str) -> subprocess.CompletedProcess:
    """Run a git command in the project root."""
    return subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )


def get_raw_images() -> list[Path]:
    """Return sorted list of supported image files in raw-icons/."""
    if not RAW_DIR.exists():
        return []
    return sorted(
        f for f in RAW_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    )


# ---------------------------------------------------------------------------
# Core Processing
# ---------------------------------------------------------------------------

def remove_background(
    input_path: Path,
    output_path: Path,
    session,
    alpha_matting: bool = True,
) -> None:
    """Remove background from a single image using rembg."""
    from rembg import remove

    with open(input_path, "rb") as f:
        input_data = f.read()

    result = remove(
        input_data,
        session=session,
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
    )

    with open(output_path, "wb") as f:
        f.write(result)


def process_single_icon(
    raw_path: Path,
    session,
    *,
    pack: str,
    alpha_matting: bool,
    force: bool,
    dry_run: bool,
    no_commit: bool,
    index: int,
    total: int,
) -> bool:
    """Process one icon: remove bg → save → commit. Returns True on success."""
    icon_name = raw_path.stem
    output_path = ICONS_DIR / pack / f"{icon_name}.png"
    prefix = f"[{index}/{total}]"

    # Check if already exists
    if output_path.exists() and not force:
        log(f"{prefix} ⏭️  {icon_name} — already exists in icons/{pack}/ (use --force to overwrite)")
        return True

    if dry_run:
        log(f"{prefix} 🔍 {icon_name} — would process {raw_path.name} → icons/{pack}/{icon_name}.png")
        return True

    # Process
    t0 = time.time()
    try:
        remove_background(raw_path, output_path, session, alpha_matting=alpha_matting)
    except Exception as e:
        log(f"{prefix} ❌ {icon_name} — error: {e}", "💥")
        return False

    elapsed = time.time() - t0
    size_kb = output_path.stat().st_size / 1024
    log(f"{prefix} ✅ {icon_name} — processed ({elapsed:.1f}s, {size_kb:.0f} KB)")

    # Git commit
    if not no_commit:
        try:
            run_git("add", f"icons/{pack}/{icon_name}.png")
            run_git("commit", "-m", f"🎨 icon (Aqua) [{pack}] - Add {icon_name} icon")
            log(f"{prefix} 📦 committed", "  ")
        except subprocess.CalledProcessError as e:
            log(f"{prefix} ⚠️  git commit failed: {e.stderr.strip()}", "  ")

    return True


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(args: argparse.Namespace) -> int:
    """Main pipeline orchestrator. Returns exit code."""

    # ── Discover images ───────────────────────────────────────────────────
    log_header("🔍 Scanning raw-icons/")

    raw_images = get_raw_images()
    if not raw_images:
        log("No images found in raw-icons/. Nothing to do.")
        return 0

    log(f"Found {len(raw_images)} image(s):")
    for img in raw_images:
        log(f"  • {img.name} ({img.stat().st_size / 1024:.0f} KB)")

    # ── Initialize rembg session ──────────────────────────────────────────
    if not args.dry_run:
        log_header(f"🧠 Loading model: {args.model}")
        from rembg import new_session
        t_load = time.time()
        session = new_session(args.model)
        log(f"Model loaded in {time.time() - t_load:.1f}s")
    else:
        session = None

    # ── Process each image ────────────────────────────────────────────────
    log_header("🎨 Processing icons")
    total = len(raw_images)
    successes = 0
    failures = 0
    t_pipeline = time.time()

    # Ensure pack directory exists
    if not args.dry_run:
        (ICONS_DIR / args.pack).mkdir(parents=True, exist_ok=True)

    for i, raw_path in enumerate(raw_images, 1):
        ok = process_single_icon(
            raw_path,
            session,
            pack=args.pack,
            alpha_matting=args.alpha_matting,
            force=args.force,
            dry_run=args.dry_run,
            no_commit=args.no_commit,
            index=i,
            total=total,
        )
        if ok:
            successes += 1
        else:
            failures += 1

    # ── Update README ─────────────────────────────────────────────────────
    if not args.dry_run and not args.no_readme and not args.no_commit:
        log_header("📝 Updating README")
        try:
            subprocess.run(
                ["node", str(UPDATE_README_SCRIPT)],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            run_git("add", "README.md")
            run_git("commit", "-m", "📝 docs (README) - Update icon gallery table")
            log("README updated and committed")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.strip() if e.stderr else str(e)
            log(f"README update failed: {stderr}", "⚠️")

    # ── Cleanup raw images ────────────────────────────────────────────────
    if not args.dry_run and successes > 0:
        log_header("🧹 Cleaning up raw-icons/")
        for raw_path in raw_images:
            icon_name = raw_path.stem
            output_path = ICONS_DIR / args.pack / f"{icon_name}.png"
            if output_path.exists():
                raw_path.unlink()
                log(f"Deleted {raw_path.name}")

    # ── Summary ───────────────────────────────────────────────────────────
    elapsed_total = time.time() - t_pipeline
    log_header("📊 Summary")
    log(f"Processed: {successes}/{total}")
    if failures > 0:
        log(f"Failed:    {failures}/{total}", "❌")
    log(f"Time:      {elapsed_total:.1f}s")
    if args.dry_run:
        log("Mode:      DRY RUN (no changes made)")

    return 1 if failures > 0 else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aqua Icons — Background Removal Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"rembg model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--alpha-matting", "-a",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable alpha matting for smoother edges (default: disabled)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing icons in icons/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate processing without making changes",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Process images without creating git commits",
    )
    parser.add_argument(
        "--no-readme",
        action="store_true",
        help="Skip README update after processing",
    )
    parser.add_argument(
        "--pack",
        default="pack1",
        help="The target pack directory under icons/ (default: pack1)",
    )

    args = parser.parse_args()
    sys.exit(run_pipeline(args))


if __name__ == "__main__":
    main()
