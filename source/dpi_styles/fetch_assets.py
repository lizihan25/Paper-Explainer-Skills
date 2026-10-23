"""Fetch author-hosted assets for local reproduction of the DPI-Net example.

Downloaded images retain their original rights; this script grants no reuse
license. Figure 4 must be supplied locally as the documented full-figure crop.
"""

from pathlib import Path
import argparse
from io import BytesIO
import shutil
from urllib.request import Request, urlopen

from PIL import Image


ASSETS = [
    ("dpi_net_method.png", "https://dpi.csail.mit.edu/imgs/method.png", (1852, 860)),
    ("yunzhu-li.jpg", "https://yunzhuli.github.io/files/profile.jpg", None),
]


def download_image(url, destination, required_size=None):
    request = Request(url, headers={"User-Agent": "PaperExplainerExamples/1.0"})
    with urlopen(request, timeout=30) as response:
        payload = response.read(25 * 1024 * 1024 + 1)
    if len(payload) > 25 * 1024 * 1024:
        raise ValueError("Image exceeds the 25 MiB download limit")
    with Image.open(BytesIO(payload)) as image:
        image.load()
        if required_size and image.size != required_size:
            raise ValueError(
                f"Source diagram is now {image.size}; expected {required_size}. "
                "Review the source image and update the renderer's ROI coordinates."
            )
    destination.write_bytes(payload)
    print(f"Downloaded {destination.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "assets")
    parser.add_argument("--figure4", type=Path, help="Local 1836 x 1230 full Figure 4 crop")
    parser.add_argument("--skip-portrait", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, url, size in ASSETS:
        if args.skip_portrait and filename == "yunzhu-li.jpg":
            continue
        download_image(url, args.output_dir / filename, size)
    if args.figure4:
        with Image.open(args.figure4) as image:
            if image.size != (1836, 1230):
                raise ValueError("Figure 4 must be the 1836 x 1230 full-figure crop; see README.md")
        destination = args.output_dir / "dpi_net_fig4.png"
        if args.figure4.resolve() != destination.resolve():
            shutil.copy2(args.figure4, destination)
        print("Copied dpi_net_fig4.png")
    else:
        print("Provide assets/dpi_net_fig4.png before rendering; see README.md.")


if __name__ == "__main__":
    main()
