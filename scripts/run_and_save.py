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
    "figure.figsize": (8, 6),
    "figure.constrained_layout.use": True,
})

_slug_rx = __import__("re").compile(r"[^a-z0-9_\-]+")
def _slug(s: str) -> str:
    s = (s or "misc").strip().lower().replace(" ", "-")
    return _slug_rx.sub("", s)

def _derive_fig_label(fig, default_base: str) -> str:
    """Derive a descriptive label for a figure using suptitle or axes title.
    Falls back to the script base name.
    """
    title = None
    try:
        st = getattr(fig, "_suptitle", None)
        if st is not None:
            text = st.get_text()
            if isinstance(text, str) and text.strip():
                title = text.strip()
    except Exception:
        pass
    if not title:
        try:
            for ax in fig.get_axes():
                t = ax.get_title()
                if isinstance(t, str) and t.strip():
                    title = t.strip()
                    break
        except Exception:
            pass
    if not title:
        title = default_base
    return _slug(title)


def main():
    parser = argparse.ArgumentParser(description="Run a Python script and save all open matplotlib figures")
    parser.add_argument("script", help="Path to the Python script to run")
    parser.add_argument("--outdir", default="outputs", help="Directory to save figures")
    parser.add_argument("--max-figs", type=int, default=2, help="Maximum number of figures to save per script")
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
    used_names = set()
    # Save at most max-figs, in stable order
    fig_nums = sorted(figs)[: max(0, int(args.max_figs))]
    for idx, num in enumerate(fig_nums, start=1):
        fig = plt.figure(num)
        try:
            # Ensure constrained layout if possible
            try:
                fig.set_constrained_layout(True)
            except Exception:
                pass
            fig.tight_layout()
        except Exception:
            pass
        # Derive a simple, non-redundant filename: 01.png or 01-<label>.png
        script_base = _slug(os.path.splitext(os.path.basename(script_path))[0])
        label = _derive_fig_label(fig, default_base=script_base)
        # Drop label if it's identical to the script base to avoid repetition
        if label == script_base:
            label = ""
        if len(label) > 64:
            label = label[:64].rstrip('-')
        fname = f"{idx:02d}{('-' + label) if label else ''}.png"
        while fname in used_names:
            fname = f"{idx:02d}{('-' + label) if label else ''}-dup.png"
        used_names.add(fname)

        descriptive_out = os.path.join(task_outdir, fname)
        fig.savefig(descriptive_out, dpi=300, bbox_inches='tight', pad_inches=0.1)
        print(f"Saved {descriptive_out}")
        try:
            plt.close(fig)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
