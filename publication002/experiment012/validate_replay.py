import sys
import json
from pathlib import Path

root = Path(__file__).resolve().parent
module_dir = root.parent / "cubff_instrumented" / "bin"
sys.path.insert(0, str(module_dir))

try:
    import cubff
except ImportError as exc:
    print("Could not import cubff:", exc)
    print("Python executable:", sys.executable)
    print("Module directory:", module_dir)
    raise SystemExit(1)

print("Python:", sys.version.split()[0])
print("Module:", cubff.__file__)

data = json.loads((root / "causal_assay_cases.json").read_text())
cases = data["cases"]

language = cubff.GetLanguage("bff_noheads")

def replay(first, second):
    tape = cubff.VectorUint8()
    for byte in first + second:
        tape.append(byte)
    return bytes(language.RunSingleParsedProgramState(
        tape, 8192, False
    ))

matched = 0
failed = []

for i, case in enumerate(cases):
    first = bytes.fromhex(case["second_pair_first_hex"])
    second = bytes.fromhex(case["second_pair_second_hex"])

    expected = (
        bytes.fromhex(case["second_after_first_hex"]) +
        bytes.fromhex(case["second_after_second_hex"])
    )

    actual = replay(first, second)

    if actual == expected:
        matched += 1
    else:
        failed.append({
            "case": i,
            "different_bytes": sum(
                a != b for a, b in zip(actual, expected)
            ),
            "actual_length": len(actual),
        })

print("\n=== EXACT REPLAY VALIDATION ===")
print("Cases:", len(cases))
print("Byte-for-byte matches:", matched)
print("Failures:", len(failed))

for failure in failed[:10]:
    print(failure)

if matched == len(cases):
    print("\nPASS: Replay reproduces all sampled interactions.")
else:
    print("\nFAIL: Resolve discrepancies before causal testing.")
