import sys
import json
import csv
from pathlib import Path
from collections import Counter

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / "cubff_instrumented" / "bin"))

import cubff

cases = json.loads(
    (root / "causal_assay_cases.json").read_text()
)["cases"]

language = cubff.GetLanguage("bff_noheads")
blank = bytes(64)

def replay(donor, recipient):
    tape = cubff.VectorUint8()
    for byte in donor + recipient:
        tape.append(byte)
    output = bytes(
        language.RunSingleParsedProgramState(tape, 8192, False)
    )
    assert len(output) == 128
    return output[:64], output[64:]

rows = []

for i, case in enumerate(cases):
    ancestor = bytes.fromhex(
        case["second_pair_first_hex"]
    )
    current = ancestor

    for generation in range(3):
        parent_after, offspring = replay(current, blank)

        successful = (
            offspring == current[::-1]
            and offspring != blank
            and parent_after == current
        )

        rows.append({
            "case": i,
            "generation": generation,
            "parent_hex": current.hex(),
            "offspring_hex": offspring.hex(),
            "success": int(successful),
            "parent_retained": int(parent_after == current),
            "offspring_matches_ancestor": int(offspring == ancestor),
            "offspring_matches_reversed_ancestor": int(
                offspring == ancestor[::-1]
            ),
        })

        if not successful:
            break

        current = offspring

    print(f"Completed lineage {i+1}/{len(cases)}",
          file=sys.stderr, flush=True)

output = root / "functional_heredity.csv"

with output.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\n=== FUNCTIONAL HEREDITY RESULTS ===")

for generation in range(3):
    group = [r for r in rows if r["generation"] == generation]
    successes = sum(r["success"] for r in group)
    print(
        f"Generation {generation} -> {generation+1}: "
        f"{successes}/{len(group)} successful"
    )

completed = Counter(r["case"] for r in rows if r["success"])
full = sum(completed[i] == 3 for i in range(len(cases)))

print(f"\nLineages completing all three transitions: {full}/50")
print("Distinct starting donors:", len(set(
    bytes.fromhex(c["second_pair_first_hex"])
    for c in cases
)))
print("Saved:", output)
