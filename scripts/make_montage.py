import argparse
import os
from PIL import Image, ImageDraw, ImageFont


def load_images(paths):
    images = []
    for p in paths:
        if not os.path.exists(p):
            raise FileNotFoundError(p)
        images.append(Image.open(p).convert("RGB"))
    return images


def make_montage(
    images,
    rows,
    cols,
    tile_size=None,
    padding=16,
    bg=(255, 255, 255),
    border_width=0,
    border_color=(0, 0, 0),
    labels=None,
    label_height=0,
    label_color=(0, 0, 0),
    label_bg=None,
):
    assert len(images) <= rows * cols, "Too many images for grid"
    if tile_size is None:
        # Use max width/height among inputs
        w = max(im.width for im in images)
        h = max(im.height for im in images)
        tile_size = (w, h)
    tw, th = tile_size
    # Reserve label band if labels provided
    has_labels = bool(labels)
    if has_labels and label_height <= 0:
        label_height = 24
    out_w = cols * tw + (cols + 1) * padding
    out_h = rows * (th + (label_height if has_labels else 0)) + (rows + 1) * padding
    canvas = Image.new("RGB", (out_w, out_h), bg)
    draw = ImageDraw.Draw(canvas)
    # Load a font
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 12)
    except Exception:
        font = ImageFont.load_default()

    for idx, im in enumerate(images):
        r = idx // cols
        c = idx % cols
        x = padding + c * (tw + padding)
        y = padding + r * (th + (label_height if has_labels else 0) + padding)
        im_resized = im.resize((tw, th), Image.LANCZOS)
        canvas.paste(im_resized, (x, y))
        if border_width and border_width > 0:
            # Draw border rectangle around the tile
            x0, y0 = x, y
            x1, y1 = x + tw - 1, y + th - 1
            for k in range(border_width):
                draw.rectangle([x0 - k, y0 - k, x1 + k, y1 + k], outline=border_color)
        # Draw label if provided
        if has_labels:
            label = labels[idx] if idx < len(labels) else None
            if label:
                # Optional label background band
                if label_bg is not None:
                    yb0 = y + th + 1
                    yb1 = y + th + label_height - 1
                    draw.rectangle([x, yb0, x + tw - 1, yb1], fill=label_bg)
                # Center text
                try:
                    text_w = draw.textlength(label, font=font)
                except Exception:
                    text_w, _ = draw.textsize(label, font=font)
                tx = x + max(0, (tw - int(text_w)) // 2)
                ty = y + th + max(0, (label_height - (font.size + 2)) // 2)
                draw.text((tx, ty), label, fill=label_color, font=font)

    return canvas


def main():
    parser = argparse.ArgumentParser(description="Create a montage image from multiple inputs")
    parser.add_argument("--out", required=True, help="Output file path (png)")
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--tile-width", type=int, default=None)
    parser.add_argument("--tile-height", type=int, default=None)
    parser.add_argument("--padding", type=int, default=16, help="Padding between tiles in pixels")
    parser.add_argument("--bg", type=str, default="255,255,255", help="Background color as R,G,B")
    parser.add_argument("--border-width", type=int, default=0, help="Optional border width around tiles")
    parser.add_argument("--border-color", type=str, default="0,0,0", help="Border color as R,G,B")
    parser.add_argument("--labels", nargs='*', default=None, help="Optional labels for each image (same order)")
    parser.add_argument("--label-height", type=int, default=24, help="Height of label band (pixels)")
    parser.add_argument("--label-color", type=str, default="0,0,0", help="Label text color as R,G,B")
    parser.add_argument("--label-bg", type=str, default=None, help="Optional label background as R,G,B")
    parser.add_argument("images", nargs='+', help="Input image paths in order")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    ims = load_images(args.images)
    size = None
    if args.tile_width and args.tile_height:
        size = (args.tile_width, args.tile_height)
    try:
        bg = tuple(int(c) for c in args.bg.split(","))
    except Exception:
        bg = (255, 255, 255)
    try:
        border_color = tuple(int(c) for c in args.border_color.split(","))
    except Exception:
        border_color = (0, 0, 0)
    labels = args.labels
    try:
        label_color = tuple(int(c) for c in (args.label_color or "").split(",")) if args.label_color else (0,0,0)
    except Exception:
        label_color = (0,0,0)
    label_bg = None
    if args.label_bg:
        try:
            label_bg = tuple(int(c) for c in args.label_bg.split(","))
        except Exception:
            label_bg = None
    montage = make_montage(
        ims,
        args.rows,
        args.cols,
        tile_size=size,
        padding=args.padding,
        bg=bg,
        border_width=args.border_width,
        border_color=border_color,
        labels=labels,
        label_height=args.label_height,
        label_color=label_color,
        label_bg=label_bg,
    )
    montage.save(args.out)
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
