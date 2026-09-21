# Typst Procedural Prior Lock-in 实验

C0 真实任务 → C1 原子能力验证 → C2 独立前缀范围修复。
当前完成协议/数据审阅、范围检查、分模型凭据加载、API 连通性检查和外部审核入口；完整 C0–C2 运行器尚待实现。

## 入口

- [实施协议](experiments_guide.md)：`0.3.0-draft`。目标 block 用于定位，允许修改从文件开头至目标 block 结束的完整前缀，后文保持不变。
- [原始审阅报告](docs/review.md) / [本轮修订记录](docs/revision-0.3.md)。
- [C0 数据集](data/c0_tasks.json)：10 题、5 类，统一 2–5 页。
- [试点配置](configs/pilot.json)：模型、路由、凭据映射及 reviewer 配置。
- [原稿备份](docs/archive/experiments_guide.original.md) / [v0.2 协议](docs/archive/experiments_guide.v0.2.md)；旧 block-only 与新 prefix 条件分开统计。

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

## 一次真实 C0 冒烟测试

下面会请求 Qwen 生成一道完整任务，并用固定编译器编译，保存源码、原始响应、诊断、用量及 PDF 页数。运行目录必须未存在：

```bash
python3 scripts/smoke_qwen.py --run-dir runs/qwen-smoke-new --task-id C0_01 --typst .runtime/typst-0.12.0/typst-x86_64-unknown-linux-musl/typst
```

若失败，人工确认首个诊断的 target block 与 prefix gate，写出含 `start`、`end`、`prefix_gate: "VERIFIED"` 和 `evidence` 的 JSON，再用同一命令增加 `--repair-boundary 边界文件.json` 进行一次独立修复。偏移为 0-based Unicode code-point 半开区间。脚本检查后文不变，并分别编译修复前缀和完整文件。

这是一题、最多一次修复的开发冒烟，不运行 C1/C2，不给 Strict PPL 结论，也不把编译成功当成语义审核通过。

首次实际结果见 [Qwen 冒烟测试 001](docs/qwen-smoke-001.md)：生成成功但出现一个明确的 LaTeX `\\times` prior candidate；唯一一次 repair 返回空 assistant content，因此保持不可判定。

## dsh + step-5-preview 审核

使用本机已配置的 dsh step provider；桥接脚本额外需要 PyYAML，见 `requirements-review.txt`。
每次创建独立 headless 会话、独立运行目录，并显式固定 step-5-preview，不修改用户全局 dsh 配置。

```bash
python3 scripts/review_with_dsh.py --packet runs/event-evidence.json --output-dir runs/review-new
```

packet 使用 `review_type=event_review`，必填 original_task、source_before、source_after、target_block、diagnostics、compile_results；可附 semantic_target、dependency_spans、diff。
协议审阅使用 `review_type=protocol_review` 和 protocol，可附 dataset、implementation。
不得附被测模型身份、密钥或 C1 结果；脚本限制顶层字段。source 字符串内部仍需由生成 packet 的流程检查，字段白名单不等于全内容脱敏。
结果含原始输出、提示词摘要、dsh 版本、结构化建议和运行状态。超时/非 JSON/缺证据保持 PENDING_REVIEW；不会自动改实验标签，也不向被测模型反馈。
已完成一个真实编译开发案例的端到端审核，返回有效 PASS；两次大范围审核未取得有效结论，因此默认按单个错误事件提交。审核建议不是编译证明。Strict PPL 阳性、低置信和抽样阴性按协议人工复核。

所有原始记录放 `runs/`，不覆盖；凭据文件与临时运行目录不纳入 Git。尚无正式模型实验结果。
