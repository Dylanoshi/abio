import argparse
import csv
import json
import sys
from pathlib import Path
from collections import Counter

BASE = Path.home() / "abio"
OUT = BASE / "experiment013a"
sys.path.insert(
    0, str(BASE / "experiment012/cubff_instrumented/bin")
)

import cubff

language = cubff.GetLanguage("bff_noheads")
blank = bytes(64)

def replay(donor):
    tape = cubff.VectorUint8()
    for b in donor + blank:
        tape.append(b)
    result = bytes(
        language.RunSingleParsedProgramState(
            tape, 8192, False
        )
    )
    if len(result) != 128:
        raise RuntimeError("Unexpected simulator output")
    return result[:64], result[64:]

def lineage(donor):
    current = donor
    history = []
    for generation in range(3):
        parent, child = replay(current)
        success = (
            parent == current
            and child == current[::-1]
            and child != blank
        )
        history.append({
            "generation": generation,
            "success": success,
            "parent_hex": current.hex(),
            "offspring_hex": child.hex()
        })
        if not success:
            break
        current = child
    return history

parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=int, default=10)
parser.add_argument("--all", action="store_true")
args = parser.parse_args()

with (OUT / "founders.csv").open() as f:
    founders = [
        bytes.fromhex(r["founder_hex"])
        for r in csv.DictReader(f)
    ]

assert len(founders) == 39
assert all(len(f) == 64 for f in founders)

alphabet = sorted(set(b for f in founders for b in f))

print("Founders:", len(founders), flush=True)
print("Observed byte alphabet:", alphabet, flush=True)

# Verify all founders before mutation testing.
for i, founder in enumerate(founders):
    history = lineage(founder)
    if len(history) != 3 or not all(
        h["success"] for h in history
    ):
        raise RuntimeError(
            f"Founder {i} failed positive control"
        )

print("Positive controls: 39/39 passed", flush=True)

results = []
counts = Counter()
tested = 0
limit = None if args.all else args.limit

output = OUT / (
    "mutations_all.csv" if args.all
    else "mutations_pilot.csv"
)

fields = [
    "founder", "position", "original_byte",
    "replacement_byte", "mutant_hex",
    "transitions_attempted", "transitions_successful",
    "three_generation_success", "last_offspring_hex"
]

with output.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    stop = False
    for i, founder in enumerate(founders):
        for pos in range(64):
            if stop:
                break
            for replacement in alphabet:
                if replacement == founder[pos]:
                    continue

                mutant = bytearray(founder)
                mutant[pos] = replacement
                mutant = bytes(mutant)

                history = lineage(mutant)
                successful = sum(
                    h["success"] for h in history
                )
                complete = (
                    len(history) == 3
                    and successful == 3
                )

                writer.writerow({
                    "founder": i,
                    "position": pos,
                    "original_byte": founder[pos],
                    "replacement_byte": replacement,
                    "mutant_hex": mutant.hex(),
                    "transitions_attempted": len(history),
                    "transitions_successful": successful,
                    "three_generation_success": int(complete),
                    "last_offspring_hex":
                        history[-1]["offspring_hex"]
                })
                f.flush()

                tested += 1
                counts["tested"] += 1
                if successful >= 1:
                    counts["first_transition"] += 1
                if complete:
                    counts["three_generations"] += 1

                if tested % 100 == 0:
                    print(
                        f"Tested {tested} mutations; "
                        f"three-generation successes: "
                        f"{counts['three_generations']}",
                        flush=True
                    )

                if limit is not None and tested >= limit:
                    stop = True
                    break
        if stop:
            break

summary = {
    "founders": len(founders),
    "observed_alphabet": alphabet,
    "scope": "observed-byte substitutions",
    "mutations_tested": counts["tested"],
    "first_transition_successes":
        counts["first_transition"],
    "three_generation_successes":
        counts["three_generations"],
    "three_generation_fraction":
        counts["three_generations"] / tested
        if tested else None,
    "output": str(output)
}

summary_path = OUT / (
    "summary_all.json" if args.all
    else "summary_pilot.json"
)
summary_path.write_text(json.dumps(summary, indent=2))

print("\n=== EXPERIMENT 013A ===")
print(json.dumps(summary, indent=2))
