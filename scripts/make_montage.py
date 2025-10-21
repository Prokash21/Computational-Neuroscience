import argparse
import os
from PIL import Image


def load_images(paths):
    images = []
    for p in paths:
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        images.append(Image.open(p).convert("RGB"))
    return images


def make_montage(images, rows, cols, tile_size=None, padding=8, bg=(255, 255, 255)):
    assert len(images) <= rows * cols, "Too many images for grid"
    if tile_size is None:
        # Use max width/height among inputs
        w = max(im.width for im in images)
        h = max(im.height for im in images)
        tile_size = (w, h)
    tw, th = tile_size
    out_w = cols * tw + (cols + 1) * padding
    out_h = rows * th + (rows + 1) * padding
    canvas = Image.new("RGB", (out_w, out_h), bg)

    for idx, im in enumerate(images):
        r = idx // cols
        c = idx % cols
        x = padding + c * (tw + padding)
        y = padding + r * (th + padding)
        im_resized = im.resize((tw, th), Image.LANCZOS)
        canvas.paste(im_resized, (x, y))

    return canvas


def main():
    parser = argparse.ArgumentParser(description="Create a montage image from multiple inputs")
    parser.add_argument("--out", required=True, help="Output file path (png)")
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--tile-width", type=int, default=None)
    parser.add_argument("--tile-height", type=int, default=None)
    parser.add_argument("images", nargs='+', help="Input image paths in order")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    ims = load_images(args.images)
    size = None
    if args.tile_width and args.tile_height:
        size = (args.tile_width, args.tile_height)
    montage = make_montage(ims, args.rows, args.cols, tile_size=size)
    montage.save(args.out)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()

