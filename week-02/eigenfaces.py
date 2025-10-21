# -*- coding: utf-8 -*-
"""
Compute eigenfaces with flexible data sources.

Options:
- Provide a local AT&T (ORL) faces directory via --data-dir or FACES_DATA_DIR
- Use KaggleHub to download kasikrit/att-database-of-faces via --use-kagglehub
- Fallback to scikit-learn's Olivetti faces via --use-sklearn
"""

import argparse
import glob
import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


def _find_subjects_root(root_dir):
    """Return directory that contains s1, s2, ... subfolders if present."""
    if not root_dir:
        return None
    candidates = [
        root_dir,
        os.path.join(root_dir, "att-database-of-faces"),
        os.path.join(root_dir, "att_faces"),
        os.path.join(root_dir, "orl_faces"),
    ]
    for cand in candidates:
        if all(os.path.isdir(os.path.join(cand, f"s{i}")) for i in (1, 2, 3)):
            return cand
    # Walk as a last resort
    for dirpath, dirnames, _ in os.walk(root_dir):
        if all(os.path.isdir(os.path.join(dirpath, f"s{i}")) for i in (1, 2, 3)):
            return dirpath
    return None


def _load_att_faces_from_dir(base_dir, width=50, height=60, first_only=True):
    n_subjects = 40
    faces = []
    for i in range(1, n_subjects + 1):
        subject_folder = os.path.join(base_dir, f"s{i}")
        if not os.path.isdir(subject_folder):
            continue
        if first_only:
            paths = [os.path.join(subject_folder, "1.pgm")]
        else:
            paths = sorted(glob.glob(os.path.join(subject_folder, "*.pgm")))[:10]
        for p in paths:
            if not os.path.exists(p):
                continue
            img = Image.open(p).resize((width, height))
            faces.append(np.asarray(img, dtype=np.float32).flatten())
    if not faces:
        raise FileNotFoundError("No PGM faces found under provided directory")
    # Shape: (pixels, n_faces)
    return np.stack(faces, axis=1)


def _try_kagglehub_download(dataset="kasikrit/att-database-of-faces"):
    try:
        import kagglehub  # type: ignore

        path = kagglehub.dataset_download(dataset)
        return path
    except Exception:
        return None


def _load_faces_any(args):
    # 1) Explicit dir or env var
    data_dir = args.data_dir or os.getenv("FACES_DATA_DIR")
    root = _find_subjects_root(data_dir) if data_dir else None
    if root:
        return _load_att_faces_from_dir(root, args.width, args.height, first_only=True)

    # 2) KaggleHub (if requested)
    if args.use_kagglehub:
        kh_root = _try_kagglehub_download()
        kh_subjects = _find_subjects_root(kh_root)
        if kh_subjects:
            return _load_att_faces_from_dir(kh_subjects, args.width, args.height, first_only=True)

    # 3) scikit-learn fallback (Olivetti faces)
    if args.use_sklearn:
        try:
            from sklearn.datasets import fetch_olivetti_faces

            data = fetch_olivetti_faces()
            images = (data.images * 255.0).astype(np.float32)
            # Pick first image for each of 40 subjects (10 images/subject)
            faces = []
            for subj in range(40):
                idx = subj * 10
                img = Image.fromarray(images[idx]).resize((args.width, args.height))
                faces.append(np.asarray(img, dtype=np.float32).flatten())
            return np.stack(faces, axis=1)
        except Exception as e:
            raise RuntimeError(
                "Failed to load faces via scikit-learn. Install scikit-learn or provide --data-dir."
            ) from e

    raise RuntimeError(
        "Could not locate faces dataset. Provide --data-dir, use --use-kagglehub, or --use-sklearn."
    )


def main():
    parser = argparse.ArgumentParser(description="Compute eigenfaces with flexible data sources")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory containing s1..s40 subfolders of AT&T faces")
    parser.add_argument("--use-kagglehub", action="store_true", help="Download AT&T faces from Kaggle via kagglehub")
    parser.add_argument("--use-sklearn", action="store_true", help="Use scikit-learn's Olivetti faces as fallback")
    parser.add_argument("--width", type=int, default=50, help="Resize width for processing")
    parser.add_argument("--height", type=int, default=60, help="Resize height for processing")
    args = parser.parse_args()

    face_data = _load_faces_any(args)

    # Pre-processing: standardize per pixel
    mean_face = np.mean(face_data, axis=1)
    sd_face = np.std(face_data, axis=1)
    sd_face[sd_face == 0] = 1.0
    face_std = (face_data - mean_face[:, np.newaxis]) / sd_face[:, np.newaxis]

    # Eigenfaces via covariance matrix
    cov = np.cov(face_std)
    # Use eigh for symmetric matrices
    w, v = np.linalg.eigh(cov)
    l_indices = np.argsort(w)

    eigenface_1 = np.real(np.reshape(v[:, l_indices[-1]], (args.height, args.width)))
    eigenface_2 = np.real(np.reshape(v[:, l_indices[-2]], (args.height, args.width)))

    # Reconstruction with N eigenfaces
    n_eigen_faces = [5, 10, 40]
    recon = np.zeros((3, face_std.shape[0]))
    for f in range(3):
        for i in range(n_eigen_faces[f]):
            loading = np.dot(face_std[:, 0], v[:, l_indices[-1 - i]])
            recon[f, :] += np.real(loading * v[:, l_indices[-1 - i]])

    # Compose a clean 2x3 grid:
    # [Eigenface #1] [Original] [Eigenface #2]
    # [EF = 5     ] [EF = 10 ] [EF = 40     ]
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), constrained_layout=True)

    axes[0, 0].imshow(eigenface_1, cmap="gray", aspect="equal")
    axes[0, 0].set_title("Eigenface #1")
    axes[0, 0].axis("off")

    axes[0, 1].imshow(np.reshape(face_std[:, 0], (args.height, args.width)), cmap="gray", aspect="equal")
    axes[0, 1].set_title("Original (standardized)")
    axes[0, 1].axis("off")

    axes[0, 2].imshow(eigenface_2, cmap="gray", aspect="equal")
    axes[0, 2].set_title("Eigenface #2")
    axes[0, 2].axis("off")

    axes[1, 0].imshow(np.reshape(recon[0, :], (args.height, args.width)), cmap="gray", aspect="equal")
    axes[1, 0].set_title("EF = 5")
    axes[1, 0].axis("off")

    axes[1, 1].imshow(np.reshape(recon[1, :], (args.height, args.width)), cmap="gray", aspect="equal")
    axes[1, 1].set_title("EF = 10")
    axes[1, 1].axis("off")

    axes[1, 2].imshow(np.reshape(recon[2, :], (args.height, args.width)), cmap="gray", aspect="equal")
    axes[1, 2].set_title("EF = 40")
    axes[1, 2].axis("off")

    plt.show()


if __name__ == "__main__":
    main()
