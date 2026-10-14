"""Explainable feedback triage, with optional LLM labels and human review."""
import csv
import io
import json
import re
import unicodedata
from collections import Counter

LABELS = {
    "回答可信度": ["编造", "幻觉", "引用", "来源", "错误答案", "不准确"],
    "响应性能": ["慢", "超时", "等待", "卡顿", "延迟"],
    "交互体验": ["按钮", "找不到", "看不清", "界面", "导出", "历史记录"],
    "知识覆盖": ["知识库", "文档", "无法回答", "不支持", "没有相关"],
    "隐私安全": ["隐私", "泄露", "身份证", "密码", "其他用户"],
}


def normalize(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text)).lower().strip("。！!？?")


def validate(rows):
    if len(rows) > 5000:
        raise ValueError("单次最多分析 5000 条反馈")
    clean, seen = [], set()
    duplicate_n = 0
    for row in rows:
        text = str(row.get("text", "")).strip()
        user = str(row.get("user_id", "anonymous")).strip() or "anonymous"
        if not text:
            continue
        if len(text) > 2000:
            raise ValueError("单条反馈不能超过 2000 字符")
        try:
            rating = int(row.get("rating", 3))
        except (TypeError, ValueError):
            raise ValueError("rating 必须为 1 至 5 的整数") from None
        if not 1 <= rating <= 5:
            raise ValueError("rating 必须为 1 至 5 的整数")
        key = (user, normalize(text))
        if key in seen:
            duplicate_n += 1
            continue
        seen.add(key)
        clean.append({"id": str(row.get("id") or f"F{len(clean)+1:04d}"),
                      "user_id": user, "text": text, "rating": rating})
    if len({r["id"] for r in clean}) != len(clean):
        raise ValueError("反馈 id 重复，请使用唯一 id")
    return clean, duplicate_n


def classify(text):
    matches = [(label, [term for term in terms if term in text]) for label, terms in LABELS.items()]
    matches = [(label, terms) for label, terms in matches if terms]
    # Safety-related feedback receives explicit attention regardless of frequency.
    if any(label == "隐私安全" for label, _ in matches):
        label, terms = next(m for m in matches if m[0] == "隐私安全")
    elif matches:
        label, terms = sorted(matches, key=lambda m: -len(m[1]))[0]
    else:
        label, terms = "待人工分类", []
    return {"label": label, "evidence": terms, "method": "关键词规则", "review_required": True}


def analyze(rows, overrides=None, estimates=None, labels=None):
    clean, duplicates = validate(rows)
    overrides, estimates, labels = overrides or {}, estimates or {}, labels or {}
    enriched = []
    for row in clean:
        info = labels.get(row["id"]) or classify(row["text"])
        if row["id"] in overrides:
            label = overrides[row["id"]]
            if label not in {*LABELS, "待人工分类"}:
                raise ValueError("人工分类不在允许范围内")
            info = {**info, "label": label, "method": "人工复核", "review_required": False}
        enriched.append({**row, **info})
    backlog = []
    for label in sorted({r["label"] for r in enriched}):
        group = [r for r in enriched if r["label"] == label]
        reach = len({r["user_id"] for r in group})
        negative = sum(r["rating"] <= 2 for r in group)
        defaults = {"impact": 2 if negative else 1, "confidence": .5, "effort": 2}
        estimate = {**defaults, **estimates.get(label, {})}
        impact, confidence, effort = (float(estimate[k]) for k in ("impact", "confidence", "effort"))
        if not .25 <= impact <= 3 or not 0 <= confidence <= 1 or effort <= 0:
            raise ValueError("RICE 参数超出范围")
        backlog.append({"theme": label, "feedback_n": len(group), "unique_users": reach,
                        "negative_n": negative, "negative_rate": round(negative / len(group), 3),
                        "reach": reach, "impact": impact, "confidence": confidence, "effort": effort,
                        "rice": round(reach * impact * confidence / effort, 3),
                        "evidence_ids": [r["id"] for r in group],
                        "attention": "优先人工审查" if label == "隐私安全" else "常规评审"})
    return {"input_n": len(rows), "valid_n": len(clean), "duplicate_n": duplicates,
            "feedback": enriched, "backlog": sorted(backlog, key=lambda r: -r["rice"])}


def load_csv(content):
    reader = csv.DictReader(io.StringIO(content))
    if not {"text", "rating"}.issubset(reader.fieldnames or []):
        raise ValueError("CSV 至少需要 text 和 rating 列，可选 id、user_id")
    return list(reader)


def export_csv(report):
    buffer = io.StringIO(newline="")
    fields = ["theme", "feedback_n", "unique_users", "negative_n", "negative_rate", "reach", "impact", "confidence", "effort", "rice", "evidence_ids", "attention"]
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for row in report["backlog"]:
        safe = {}
        for key, value in row.items():
            value = ",".join(value) if isinstance(value, list) else value
            # Prevent spreadsheet formulas in imported/exported user text.
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value
            safe[key] = value
        writer.writerow(safe)
    return "\ufeff" + buffer.getvalue()
