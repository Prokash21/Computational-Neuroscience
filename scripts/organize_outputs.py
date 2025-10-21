import os
import re
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
OUT = os.path.join(ROOT, "outputs")

def build_script_index(root):
    index = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.lower().endswith(".py"):
                continue
            base = os.path.splitext(fn)[0]
            index.setdefault(base, os.path.join(dirpath, fn))
    return index

_slug_rx = re.compile(r"[^a-z0-9_\-]+")
def slug(s: str) -> str:
    s = (s or "misc").strip().lower().replace(" ", "-")
    return _slug_rx.sub("", s)

def main():
    if not os.path.isdir(OUT):
        print(f"No outputs directory at {OUT}")
        return
    index = build_script_index(ROOT)
    pattern = re.compile(r"^(?P<base>.+)-fig(?P<num>\d+)\.png$")

    for fn in list(os.listdir(OUT)):
        m = pattern.match(fn)
        full = os.path.join(OUT, fn)
        if not m or not os.path.isfile(full):
            continue
        base = m.group("base")
        num = m.group("num")
        script_path = index.get(base)
        if script_path:
            parent = os.path.basename(os.path.dirname(script_path)) or "misc"
        else:
            parent = "misc"
        dest_dir = os.path.join(OUT, slug(parent), slug(base))
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, f"fig{num}.png")
        # Move and overwrite if exists
        try:
            shutil.move(full, dest)
            print(f"Moved {full} -> {dest}")
        except Exception as e:
            print(f"Skip {full}: {e}")

    # Second pass: slugify any directories under outputs
    for dirpath, dirnames, _ in os.walk(OUT, topdown=False):
        for d in list(dirnames):
            old_path = os.path.join(dirpath, d)
            new_name = slug(d)
            if new_name == d:
                continue
            new_path = os.path.join(dirpath, new_name)
            try:
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    print(f"Renamed {old_path} -> {new_path}")
                else:
                    # Merge contents then remove old
                    for child in os.listdir(old_path):
                        shutil.move(os.path.join(old_path, child), os.path.join(new_path, child))
                    os.rmdir(old_path)
                    print(f"Merged and removed {old_path}")
            except Exception as e:
                print(f"Skip dir {old_path}: {e}")

if __name__ == "__main__":
    main()
