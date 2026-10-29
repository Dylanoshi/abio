import sys
import json
import csv
from pathlib import Path
from collections import defaultdict

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parent / "cubff_instrumented" / "bin"))

import cubff

cases = json.loads(
    (root / "causal_assay_cases.json").read_text()
)["cases"]

language = cubff.GetLanguage("bff_noheads")
zero = bytes(64)

def replay(a, b):
    tape = cubff.VectorUint8()
    for x in a + b:
        tape.append(x)
    result = bytes(
        language.RunSingleParsedProgramState(tape, 8192, False)
    )
    assert len(result) == 128
    return result[:64], result[64:]

def outcome(a, b):
    a2, b2 = replay(a, b)

    changed = b2 != b
    exact = changed and b2 == a
    reversed_copy = changed and b2 == a[::-1]

    return {
        "copy": int(exact or reversed_copy),
        "exact": int(exact),
        "reversed": int(reversed_copy and not exact),
        "recipient_changed": int(changed),
        "donor_retained": int(a2 == a),
        "donor_changed": int(a2 != a),
        "recipient_diff_bytes": sum(
            x != y for x, y in zip(b, b2)
        ),
    }

conditions = defaultdict(list)
rows = []

for i, case in enumerate(cases):
    b = bytes.fromhex(case["second_pair_first_hex"])
    c = bytes.fromhex(case["second_pair_second_hex"])

    other = cases[(i + 1) % len(cases)]
    b_alt = bytes.fromhex(
        other["second_pair_first_hex"]
    )
    c_alt = bytes.fromhex(
        other["second_pair_second_hex"]
    )

    tests = {
        "original": (b, c),
        "blank_donor": (zero, c),
        "alternative_donor": (b_alt, c),
        "blank_partner": (b, zero),
        "alternative_partner": (b, c_alt),
        "swapped": (c, b),
    }

    for name, (a, partner) in tests.items():
        result = outcome(a, partner)
        conditions[name].append(result)
        rows.append({
            "case": i,
            "condition": name,
            **result
        })

    print(f"Completed case {i+1}/{len(cases)}",
          file=sys.stderr, flush=True)

output = root / "causal_interventions.csv"
with output.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\n=== CAUSAL INTERVENTION RESULTS ===")
for name, results in conditions.items():
    n = len(results)
    print(f"\n{name} (n={n})")
    for key in (
        "copy",
        "exact",
        "reversed",
        "recipient_changed",
        "donor_retained",
    ):
        count = sum(r[key] for r in results)
        print(f"  {key}: {count}/{n} ({count/n:.1%})")

print("\nSaved:", output)
