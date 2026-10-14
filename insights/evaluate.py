import json
from pathlib import Path
from insights.core import analyze, load_csv


if __name__ == "__main__":
    folder = Path(__file__).parent
    rows = load_csv((folder / "data/demo.csv").read_text(encoding="utf-8-sig"))
    report = analyze(rows)
    expected = {r["id"]: r["expected_label"] for r in rows}
    hit = sum(r["label"] == expected[r["id"]] for r in report["feedback"])
    report["evaluation"] = {"dataset":"self-authored keyword-aligned synthetic examples; not independent validation",
                            "correct":hit, "n":report["valid_n"], "label_agreement":hit / report["valid_n"],
                            "live_model_tested":False}
    output = folder / "reports/evaluation.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"input_n":report["input_n"],"valid_n":report["valid_n"],"duplicate_n":report["duplicate_n"],
                      "themes":len(report["backlog"]),"evaluation":report["evaluation"]}))
