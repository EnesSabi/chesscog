import argparse
import typing
from pathlib import Path
import cv2
import json
import numpy as np
import logging

from chesscog.utils.dataset import Datasets
from chesscog.utils.io import URI
from chesscog.utils.config import CfgNode as CN
from chesscog.utils import sort_corner_points
from chesscog.corner_detection import find_corners

logger = logging.getLogger(__name__)


def evaluate(cfg: CN, dataset: Datasets, output_folder: Path, find_mistakes: bool = False, include_heading: bool = False) -> str:
    mistakes = 0
    total = 0
    folder = URI("data://render") / dataset.value
    for img_file in folder.glob("*.png"):
        total += 1
        img = cv2.imread(str(img_file))
        json_file = folder / f"{img_file.stem}.json"
        with json_file.open("r") as f:
            label = json.load(f)
        actual = np.array(label["corners"])
        predicted = find_corners(cfg, img)

        if predicted is not None:
            actual = sort_corner_points(actual)
            predicted = sort_corner_points(predicted)

        if predicted is None or np.linalg.norm(actual - predicted, axis=-1).max() > 10.:
            mistakes += 1
    return mistakes, total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate the chessboard corner detector.")
    parser.add_argument("--config",
                        help="path to a folder with YAML config files",
                        type=str, default="config://corner_detection")
    parser.add_argument("--dataset", help="the dataset to evaluate (if unspecified, train and val will be evaluated)",
                        type=str, default=None, choices=[x.value for x in Datasets])
    parser.add_argument("--out", help="output folder", type=str,
                        default=f"results://corner_detector")
    parser.add_argument("--find-mistakes", help="whether to output all incorrectly detected images",
                        dest="find_mistakes", action="store_true")
    parser.set_defaults(find_mistakes=False)
    args = parser.parse_args()

    datasets = [Datasets.TRAIN, Datasets.VAL] \
        if args.dataset is None else [d for d in Datasets if d.value == args.dataset]
    cfgs = URI(args.config).glob("*.yaml")
    cfgs = filter(lambda x: not x.name.startswith("_"), cfgs)
    cfgs = map(CN.load_yaml_with_base, cfgs)
    cfgs = list(cfgs)

    output_folder = URI(args.out)
    output_folder.mkdir(parents=True, exist_ok=True)
    with (output_folder / "evaluate.csv").open("w") as f:
        cfg_headers = None
        for i, cfg in enumerate(cfgs, 1):
            params = cfg.params_dict()
            if cfg_headers is None:
                cfg_headers = list(params.keys())
                values = ["dataset", "mistakes", "total"]
                values.extend(f"config.{x}" for x in cfg_headers)
                f.write(",".join(values) + "\n")
            for dataset in datasets:
                mistakes, total = evaluate(
                    cfg, dataset, args.out, args.find_mistakes)
                values = [dataset.name, mistakes, total]
                values.extend(params[k] for k in cfg_headers)
                values = map(str, values)
                f.write(",".join(values) + "\n")
            f.flush()
            logger.info(f"Completed {i}/{len(cfgs)} configs")