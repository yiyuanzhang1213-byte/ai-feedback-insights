"""Adapter for the upstream widget's on_submit callback.

Usage: streamlit_feedback(feedback_type='thumbs', on_submit=record_feedback)
This adapter retains the original widget; adds a session CSV export for this dashboard.
"""
import csv
import io
import uuid


def record_feedback(response):
    import streamlit as st
    scores = {"👍":5, "👎":1, "😀":5, "🙂":4, "😐":3, "🙁":2, "😞":1}
    item = {"id":uuid.uuid4().hex[:12],"user_id":"anonymous",
            "text":response.get("text") or "未填写文字反馈",
            "rating":scores.get(response.get("score"), 3)}
    st.session_state.setdefault("collected_feedback", []).append(item)
    return response


def collected_csv(rows):
    output = io.StringIO()
    writer = csv.DictWriter(output,fieldnames=["id","user_id","text","rating"])
    writer.writeheader()
    for row in rows:
        safe = dict(row)
        for key,value in safe.items():
            if isinstance(value,str) and value.lstrip().startswith(("=","+","-","@")):
                safe[key] = "'" + value
        writer.writerow(safe)
    return output.getvalue()
