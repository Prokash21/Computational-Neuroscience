import argparse
import os
import sys
import runpy

# Force non-interactive backend before importing pyplot
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use(os.environ.get("MPLBACKEND", "Agg"), force=True)
import matplotlib.pyplot as plt
import matplotlib as mpl

# Apply a publication-friendly style
try:
    plt.style.use("seaborn-v0_8-paper")
except Exception:
    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except Exception:
        pass

mpl.rcParams.update({
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "axes.grid": False,
})

_slug_rx = __import__("re").compile(r"[^a-z0-9_\-]+")
def _slug(s: str) -> str:
    s = (s or "misc").strip().lower().replace(" ", "-")
    return _slug_rx.sub("", s)


def main():
    parser = argparse.ArgumentParser(description="Run a Python script and save all open matplotlib figures")
    parser.add_argument("script", help="Path to the Python script to run")
    parser.add_argument("--outdir", default="outputs", help="Directory to save figures")
    parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments to pass through to the script (prefix with --)")
    args = parser.parse_args()

    script_path = os.path.abspath(args.script)
    os.makedirs(args.outdir, exist_ok=True)

    # Execute target script in its own globals, with its working directory
    cwd = os.getcwd()
    try:
        os.chdir(os.path.dirname(script_path))
        # Pass-through args to script
        sys.argv = [script_path] + ([a for a in args.script_args if a != "--"])  # drop the '--' separator
        runpy.run_path(script_path, run_name='__main__')
    finally:
        os.chdir(cwd)

    base = _slug(os.path.splitext(os.path.basename(script_path))[0])
    parent = _slug(os.path.basename(os.path.dirname(script_path)) or "misc")
    task_outdir = os.path.join(args.outdir, parent, base)
    os.makedirs(task_outdir, exist_ok=True)
    figs = plt.get_fignums()
    if not figs:
        print(f"No matplotlib figures detected for {script_path}")
        return
    for num in figs:
        fig = plt.figure(num)
        try:
            fig.tight_layout()
        except Exception:
            pass
        out = os.path.join(task_outdir, f"fig{num}.png")
        fig.savefig(out, dpi=300, bbox_inches='tight')
        print(f"Saved {out}")


if __name__ == "__main__":
    sys.exit(main())
