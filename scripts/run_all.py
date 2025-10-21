import argparse
import math
import os
import sys
import subprocess
import glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def run(cmd, cwd=None):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=False)


def discover_week_dirs(selected=None):
    weeks = []
    if selected:
        for w in selected:
            p = os.path.join(ROOT, w)
            if os.path.isdir(p):
                weeks.append(w)
        return weeks
    for d in sorted(os.listdir(ROOT)):
        if d.startswith("week-") and os.path.isdir(os.path.join(ROOT, d)):
            weeks.append(d)
    return weeks


def discover_scripts(weeks, include=None, exclude=None):
    scripts = []
    for w in weeks:
        pattern = os.path.join(ROOT, w, "*.py")
        for path in sorted(glob.glob(pattern)):
            base = os.path.basename(path)
            name = os.path.splitext(base)[0]
            if include and all(inc not in name for inc in include):
                continue
            if exclude and any(exc in name for exc in exclude):
                continue
            scripts.append(os.path.relpath(path, ROOT))
    return scripts


def compute_grid(n):
    if n <= 0:
        return (0, 0)
    if n <= 3:
        return (1, n)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return (rows, cols)


def build_week_montage(week, outdir="outputs", exclude_in_montage=None):
    week_out = os.path.join(ROOT, outdir, week)
    if not os.path.isdir(week_out):
        return
    # Collect fig1 from each script folder under the week output
    images = []
    for d in sorted(os.listdir(week_out)):
        if d.lower() == "overview":
            continue
        if exclude_in_montage and any(exc in d for exc in exclude_in_montage):
            continue
        p = os.path.join(week_out, d, "fig1.png")
        if os.path.exists(p):
            images.append(p)
    if not images:
        return
    rows, cols = compute_grid(len(images))
    if rows == 0:
        return
    out_path = os.path.join(week_out, "overview", "overview.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = [
        sys.executable,
        os.path.join(ROOT, "scripts", "make_montage.py"),
        "--out",
        out_path,
        "--rows",
        str(rows),
        "--cols",
        str(cols),
    ] + images
    run(cmd)


def main():
    parser = argparse.ArgumentParser(description="Run all week scripts and generate montages")
    parser.add_argument("--weeks", nargs="*", help="Subset of week folders to run, e.g. week-02 week-03")
    parser.add_argument("--outdir", default="outputs", help="Output root directory")
    parser.add_argument("--exclude", nargs="*", default=[], help="Substring filters of script basenames to skip during run")
    parser.add_argument("--use-kagglehub", action="store_true", help="Pass KaggleHub flag to eigenfaces")
    args = parser.parse_args()

    weeks = discover_week_dirs(args.weeks)
    scripts = discover_scripts(weeks, include=None, exclude=args.exclude)

    # Ensure outputs root exists
    os.makedirs(os.path.join(ROOT, args.outdir), exist_ok=True)

    for rel in scripts:
        extra = []
        if os.path.basename(rel) == "eigenfaces.py" and args.use_kagglehub:
            extra = ["--", "--use-kagglehub"]
        cmd = [
            sys.executable,
            os.path.join(ROOT, "scripts", "run_and_save.py"),
            rel,
            "--outdir",
            args.outdir,
        ] + extra
        run(cmd, cwd=ROOT)

    # Build montages per week; exclude coursera_question by default from montages only
    for w in weeks:
        exclude_in_montage = ["coursera_question"]
        build_week_montage(w, outdir=args.outdir, exclude_in_montage=exclude_in_montage)


if __name__ == "__main__":
    sys.exit(main())

