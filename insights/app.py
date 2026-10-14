import hashlib
import json
from pathlib import Path
import sys
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from insights.core import LABELS, analyze, export_csv, load_csv, validate
from insights.provider import classify_with_model

st.set_page_config(page_title="AI 产品反馈分析台", page_icon="📊", layout="wide")
st.title("AI 产品反馈分析台")
st.caption("将分散反馈整理为可复核的主题与需求优先级，保留每个建议的原始证据。")
with st.sidebar:
    file = st.file_uploader("导入 CSV", type=["csv"])
    st.caption("列名：id、user_id、text、rating（1–5）。请使用匿名用户标识。")
    st.info("未导入时展示 30 条自建演示反馈，不代表真实用户数据。")
    ai_enabled = st.checkbox("使用 AI 建议分类")
    st.caption("将发送反馈文本至服务端配置的模型。提交前请完成脱敏。")
try:
    content = file.getvalue().decode("utf-8-sig") if file else (Path(__file__).parent / "data/demo.csv").read_text(encoding="utf-8-sig")
    rows = load_csv(content)
    clean, duplicate_n = validate(rows)
except (ValueError, UnicodeDecodeError) as exc:
    st.error(str(exc))
    st.stop()
fingerprint = hashlib.sha256(content.encode()).hexdigest()
if st.session_state.get("fingerprint") != fingerprint:
    st.session_state.update(fingerprint=fingerprint, overrides={}, labels={}, estimates={})
if ai_enabled and st.button("分析反馈（发送至模型）"):
    try:
        st.session_state.labels = classify_with_model(clean)
    except (ValueError, KeyError):
        st.warning("AI 服务未配置或返回未通过校验，继续展示本地规则分类。")
report = analyze(rows, st.session_state.overrides, st.session_state.estimates, st.session_state.labels)
a, b, c = st.columns(3)
a.metric("原始反馈", report["input_n"])
b.metric("去重后有效反馈", report["valid_n"])
c.metric("需求主题", len(report["backlog"]))
st.subheader("需求优先级")
st.caption("RICE = 本批次独立用户数 × 影响 × 信心 ÷ 工作量。默认影响、信心和工作量为假设，需人工确认；分数不等于业务收益。")
st.dataframe(report["backlog"], hide_index=True, width="stretch")
if report["backlog"]:
    with st.expander("修改优先级估算"):
        theme = st.selectbox("主题", [r["theme"] for r in report["backlog"]])
        with st.form("estimate_form"):
            impact = st.select_slider("影响", [.25, .5, 1., 2., 3.], value=2.)
            confidence = st.slider("信心（人工估计）", 0., 1., .5, .05)
            effort = st.number_input("工作量（人周估计）", min_value=.1, value=2., step=.1)
            if st.form_submit_button("应用估算"):
                st.session_state.estimates[theme] = {"impact":impact,"confidence":confidence,"effort":effort}
                st.rerun()
st.subheader("证据与人工复核")
st.dataframe(report["feedback"], hide_index=True, width="stretch")
if clean:
    with st.form("review"):
        target = st.selectbox("反馈 ID", [r["id"] for r in clean])
        label = st.selectbox("确认主题", [*LABELS, "待人工分类"])
        if st.form_submit_button("保存人工分类"):
            st.session_state.overrides[target] = label
            st.rerun()
st.download_button("导出需求清单 CSV", export_csv(report), "backlog.csv", "text/csv")
st.download_button("导出反馈证据 JSON", json.dumps(report, ensure_ascii=False, indent=2), "feedback-report.json", "application/json")
st.caption("本工具提供需求评审辅助。隐私问题应单独审查；去重仅处理同一用户的完全相同文本，不是语义聚类。")
