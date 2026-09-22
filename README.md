# Typst Procedural Prior Lock-in 实验

C0 真实任务 → C1 原子能力验证 → C2 独立前缀范围修复。
当前完成协议/数据审阅、范围检查、分模型凭据加载、API 连通性检查和外部审核入口；完整 C0–C2 运行器尚待实现。

## 入口

- [实施协议](experiments_guide.md)：`0.6.0-draft`。C0 由被测模型生成；自动 trajectory repair 当前停用，待新 backend 通过审阅和冻结后再启用。C1/C2 调用同一被测模型做能力与 PPL 验证。目标 block 用于定位，允许修改从文件开头至目标 block 结束的完整前缀，后文保持不变。
- [原始审阅报告](docs/review.md) / [v0.6 修订记录](docs/revision-0.6.md) / [repair 接口](docs/repair-interface.md)。
- [C0 数据集](data/c0_tasks.json)：10 题、5 类，统一 2–5 页。
- [试点配置](configs/pilot.json)：模型、路由、凭据映射、repair 接口状态及 DSH 审核配置。
- [单题试点 001](docs/pilot-one-task-001.md)：Qwen generation、5 个因果错误事件、前 4 个历史 DSH repair 候选和第 5 个事件截尾。
- [原稿备份](docs/archive/experiments_guide.original.md) / [v0.5 协议](docs/archive/experiments_guide.v0.5.md)；旧 block-only、同模型 C0 repair 和 DSH-oracle 条件分开统计。

## 离线检查

Python 3.10+，基础模块仅用标准库，不调用 API：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_repository.py
python3 scripts/validate_repository.py --require-ready
```

`--require-ready` 目前应失败：完整运行器和协议冻结尚未完成。已在 `.runtime/typst-0.12.0/` 独立安装官方 Typst 0.12.0，并在试点配置中指定；系统的 `typst` 命令保持原版本。该本地二进制不进入 Git，其他机器需安装相同版本。
关键词仅粗筛；locality 只验证后文文本未变，不证明语义正确。`block_only` 参数仅保留为明确的对照条件。

## 分模型连接

`apikey.config` 按用户原格式读取，不重写文件。环境变量覆盖该模型的本地密钥。

| 模型 | 基础地址 | 本地 key 标签 | 环境变量覆盖 |
| --- | --- | --- | --- |
| qwen3.8-flash | https://maas.qianwenaiapi.com/compatible-mode/v1 | qwen | QWEN_API_KEY |
| glm-5.3-flash | https://xindu.xyz/v1 | glm | GLM_API_KEY |
| deepseek-v4.1-flash | https://maas.qianwenaiapi.com/compatible-mode/v1 | qwen（配置明确支持） | DEEPSEEK_API_KEY |

DeepSeek 原 `deepseek` 标签在星渡返回 401，已保存为 inactive_connection；配置中明确列出的另一组凭据在上表路由验证成功后设为当前连接。这里是显式路由选择，不会在正式实验中偷偷跨服务重试。
三个模型独立配置，绝不默认共用一个 XINDU_API_KEY。不同服务方也属于模型条件的一部分，必须记录。

可选连通性检查（会发起 API 请求，不是实验试次）：

```bash
python3 scripts/probe_models.py --output runs/connectivity-new.json
```

输出文件必须未存在，避免覆盖旧证据。短回复通过只代表接口可调用，不代表模型质量或全部参数兼容。

## 被测模型 generation / repair 通路冒烟测试

下面会请求 Qwen 生成一道完整任务，并用固定编译器编译，保存源码、原始响应、诊断、用量及 PDF 页数。若增加 repair boundary，调用的是被测模型 repair 通路，用于验证未来 C2 基础设施，不作为 v0.4 的 C0 oracle repair。运行目录必须未存在：

```bash
python3 scripts/smoke_qwen.py --run-dir runs/qwen-smoke-new --task-id C0_01 --typst .runtime/typst-0.12.0/typst-x86_64-unknown-linux-musl/typst
```

若失败，人工确认首个诊断的 target block 与 prefix gate，写出含 `start`、`end`、`prefix_gate: "VERIFIED"` 和 `evidence` 的 JSON，再用同一命令增加 `--repair-boundary 边界文件.json` 进行一次独立修复。偏移为 0-based Unicode code-point 半开区间。脚本检查后文不变，并分别编译修复前缀和完整文件。

这是一题、最多一次被测模型修复的开发冒烟，不构成完整 C0/C1/C2，不给 Strict PPL 结论，也不把编译成功当成语义审核通过。

首次实际结果见 [Qwen 冒烟测试 001](docs/qwen-smoke-001.md)：生成成功但出现一个明确的 LaTeX `\\times` prior candidate；唯一一次 repair 返回空 assistant content，因此保持不可判定。

异常修复与复测见 [Qwen 冒烟测试 002](docs/qwen-smoke-002.md)。Qwen 请求现显式使用 `reasoning_effort=medium`、SSE 流式传输和 usage 回传；只有收到非空正文及最终 `finish_reason=stop` 才进入编译。复测的 generation 与 repair 均得到完整响应，repair 后文逐字符不变且修复前缀可编译，验证了被测模型/C2 通路；运行器也会明确拒绝同类空正文响应。该历史 Qwen repair 不属于 v0.4 的 C0 oracle 数据。

## Repair 接口与 DSH 审核

v0.6 没有启用的 C0 repair backend。通用输入/响应、locality、prefix compiler 和状态契约见 [repair 接口](docs/repair-interface.md)，机器可读结构见 [`c0-repair-packet.schema.json`](schemas/c0-repair-packet.schema.json) 和 [`c0-repair-response.schema.json`](schemas/c0-repair-response.schema.json)。新 backend 不得仅因实现了该接口就进入正式试验；还需独立审阅、留出冒烟测试和新版本冻结。

`scripts/repair_with_dsh.py` 保留为历史、禁用的实验适配器。它曾验证同会话 compiler feedback 管道，也在单题试点的长前缀上多次只生成内部推理而无修复正文，因此不再执行正式 trajectory repair。历史入口仅用于复现：

```bash
python3 scripts/repair_with_dsh.py --allow-disabled-adapter --packet runs/event-frozen.json --output-dir runs/oracle-repair-new --typst .runtime/typst-0.12.0/typst-x86_64-unknown-linux-musl/typst
```

错误盘点和独立审核仍可使用本机 DSH step provider，并使用禁用模型工具的独立 SDK 会话。它的输出是建议，不直接修改冻结源码、错误计数或 PPL 标签：

```bash
python3 scripts/review_with_dsh.py --packet runs/event-evidence.json --output-dir runs/review-new
```

错误盘点使用 `review_type=inventory_review`，只能查看修复前的 original_task、source_before、target_block、diagnostics、compile_results；不得包含 oracle 输出或 diff。修复后审核使用 `review_type=event_review`，额外要求 source_after；可附 semantic_target、dependency_spans、diff。审核器固定 low reasoning 并禁用模型工具，避免长推理耗尽输出或自行获取实验包之外的信息。
协议审阅使用 `review_type=protocol_review` 和 protocol，可附 dataset、implementation。
不得附被测模型身份、密钥或 C1 结果；脚本限制顶层字段。source 字符串内部仍需由生成 packet 的流程检查，字段白名单不等于全内容脱敏。
结果含原始输出、提示词摘要、dsh 版本、结构化建议和运行状态。若只是 JSON/schema 格式错误，审核器会在同一 SDK 会话内最多纠正 3 轮，不重发 evidence packet。超时/无效结构/缺证据保持 PENDING_REVIEW；不会自动改实验标签，也不向被测模型反馈。
已完成一个真实编译开发案例的端到端审核，返回有效 PASS；两次大范围审核未取得有效结论，因此默认按单个错误事件提交。审核建议不是编译证明。Strict PPL 阳性、低置信和抽样阴性按协议人工复核。

所有原始记录放 `runs/`，不覆盖；凭据文件与临时运行目录不纳入 Git。尚无正式模型实验结果。
