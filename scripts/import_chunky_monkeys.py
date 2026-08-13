#!/usr/bin/env python3
"""Import accepted Chunky Monkey images and generate matching token metadata."""

from argparse import ArgumentParser
import json
from pathlib import Path
import shutil

from PIL import Image


RAW_ROOT = (
    "https://raw.githubusercontent.com/tomzlabs/flap-token-metadata/"
    "main/chunky-monkeys/images"
)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("collection_root", type=Path)
    parser.add_argument("destination_root", type=Path)
    args = parser.parse_args()

    manifest_path = args.collection_root / "accepted-batches.json"
    manifest = json.loads(manifest_path.read_text())
    accepted_count = manifest["acceptedCount"]
    legendary_ids = set(manifest["legendaryChickenPoop"]["tokenIds"])

    images_dir = args.destination_root / "chunky-monkeys" / "images"
    metadata_dir = args.destination_root / "chunky-monkeys" / "metadata"
    images_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    imported = 0
    resized = 0
    for batch in manifest["batches"]:
        batch_dir = args.collection_root / batch["path"]
        for token_id in range(batch["from"], batch["to"] + 1):
            source = batch_dir / f"monkey-{token_id:05d}.png"
            if not source.exists():
                raise SystemExit(f"Missing accepted image: {source}")

            destination = images_dir / f"{token_id}.png"
            with Image.open(source) as image:
                if image.format != "PNG":
                    raise SystemExit(f"Expected PNG image: {source}")
                if image.size == (512, 512):
                    shutil.copyfile(source, destination)
                elif image.width == image.height:
                    image.convert("RGB").resize(
                        (512, 512), Image.Resampling.NEAREST
                    ).save(destination, optimize=True)
                    resized += 1
                else:
                    raise SystemExit(f"Expected a square image: {source} is {image.size}")

            attributes = [{"trait_type": "Edition", "value": token_id}]
            if token_id in legendary_ids:
                attributes.append(
                    {"trait_type": "Legendary", "value": "Chicken Poop"}
                )
            metadata = {
                "name": f"Chunky Monkeys #{token_id}",
                "description": "A pastel large-pixel monkey from the Chunky Monkeys collection.",
                "image": f"{RAW_ROOT}/{token_id}.png",
                "attributes": attributes,
            }
            (metadata_dir / f"{token_id}.json").write_text(
                json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
                + "\n"
            )
            imported += 1

    expected_ids = set(range(1, accepted_count + 1))
    actual_image_ids = {int(path.stem) for path in images_dir.glob("*.png")}
    actual_metadata_ids = {int(path.stem) for path in metadata_dir.glob("*.json")}
    if imported != accepted_count or actual_image_ids != expected_ids:
        raise SystemExit("Imported image IDs do not match accepted manifest")
    if actual_metadata_ids != expected_ids:
        raise SystemExit("Generated metadata IDs do not match accepted manifest")

    print(f"Imported {imported} images; normalized {resized} square images to 512x512")


if __name__ == "__main__":
    main()
