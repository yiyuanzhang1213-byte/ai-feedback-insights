# AI 产品反馈分析与需求优先级工作台

在开源反馈采集组件之上新增分析层：CSV 导入、同用户文本去重、主题分类建议、证据追踪、人工复核、可调整 RICE 评分和需求清单导出。

本仓库为 AI 产品经理求职作品集的开源二次开发原型，开发时间为 2026-10-14。演示样本均为自建合成数据，尚无真实用户或生产业务收益。

## 快速运行

在仓库根目录执行（Python 3.11+）：

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r insights/requirements.txt
.venv\Scripts\python.exe -m streamlit run insights/app.py
```

无需 API Key 即可使用本地规则/检索模式。模型功能需在服务端自行配置 LLM_BASE_URL（包含 /v1 的基础地址）、LLM_MODEL、LLM_API_KEY；禁止提交真实凭据。可选模型适配器已实现，不把 mock 测试等同于真实模型验收。

```powershell
python -m insights.evaluate
python -m unittest insights.test_core -v
```

## 产品材料与验证

- [产品需求说明](insights/PRD.md)
- [可复现评测数据](insights/data/)
- [评测结果及逐条证据](insights/reports/evaluation.json)
- 验证范围：12 项核心测试，另见 UI 核验记录。

## 开源来源与本次贡献

- 上游：https://github.com/trubrics/streamlit-feedback
- 基线提交：`582194fefb536789ecf3dce86f59238e3aefc4ca`
- 原许可证：MIT，完整保留 LICENSE。
- 原始介绍：[README.upstream.md](README.upstream.md)。
- 上游文件保持原样；本次新增功能全部位于 `insights/`。根 README 与忽略规则按作品集用途更新。
- 新增内容采用与上游相同许可证。原组件、示例和原提交作者不归属于本次开发者。

## 适用范围

本地演示、产品设计讨论和评测方法展示。发布到公网之前需要补齐认证、权限、存储策略和真实模型验证。当前合成数据结果不能用于宣称生产质量、真实用户规模或商业提效。
