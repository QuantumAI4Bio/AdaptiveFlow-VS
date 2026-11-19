#!/usr/bin/env python3
"""A deterministic stand-in for a Vina family docking engine.

It accepts the same arguments the AdaptiveFlow worker passes to qvina02
(--config, --ligand, --out, --cpu), writes a pose file and prints a score
table in the output format the production docking_finish_vina parser
expects. The score is a fixed function of the ligand name, so a test can
tell whether a score was attributed to the right molecule.

This stub exists so that the storage and addressing contract can be
exercised on any platform. It is not a docking program and its scores have
no physical meaning.
"""

import argparse
import sys
from pathlib import Path


def expected_score(ligand_name):
    return -4.0 - (sum(ord(char) for char in ligand_name) % 50) / 10.0


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--config', required=True)
    parser.add_argument('--ligand', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--cpu', default="1")
    parser.add_argument('--exhaustiveness', default=None)
    args, _unknown = parser.parse_known_args(argv)

    ligand_path = Path(args.ligand)
    if not ligand_path.is_file():
        print(f"Cannot read ligand file {ligand_path}", file=sys.stderr)
        return 1

    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"Cannot read config file {config_path}", file=sys.stderr)
        return 1

    ligand_name = ligand_path.name.split(".")[0]
    score = expected_score(ligand_name)

    pose_path = Path(args.out)
    pose_path.parent.mkdir(parents=True, exist_ok=True)
    pose_lines = ["MODEL 1", f"REMARK VINA RESULT:  {score:.1f}      0.000      0.000"]
    pose_lines.extend(
        line for line in ligand_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("ATOM")
    )
    pose_lines.append("ENDMDL")
    pose_path.write_text("\n".join(pose_lines) + "\n", encoding="utf-8")

    print("mode |   affinity | dist from best mode")
    print("     | (kcal/mol) | rmsd l.b.| rmsd u.b.")
    print("-----+------------+----------+----------")
    print(f"   1       {score:>6.1f}      0.000      0.000")
    print("Writing output ... done.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
