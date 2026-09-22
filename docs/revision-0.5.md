# v0.5 修订：C0 oracle 同会话多轮修复

日期：2026-09-22。

v0.4 的 dsh oracle 每个 attempt 只获得一次模型输出，因此真实 Typst compiler 发现的剩余 prefix 错误无法返回给修复者。首个复合 target 的两个独立 attempt 都只修复了 `emph`，遗漏 footer 的 code-mode `#`，说明一次性输出不足以稳定推进 C0 轨迹。

v0.5 将一个 C0 oracle attempt 定义为一个独立 dsh SDK session。会话内最多 4 轮：候选先经过 immutable-suffix locality 检查，再只编译 editable prefix；失败时仅回传这个 prefix 的真实编译诊断。prefix 成功后才编译完整文档并进入独立语义审核。完整文档的后续错误不会泄漏回当前会话。

连续两轮出现相同 candidate-prefix hash、diagnostic hash 和 failure kind 时，以 `NO_PROGRESS` 停止；达到轮数上限记为 `ROUND_LIMIT`。每事件仍最多 3 个独立 attempt，各 attempt 从同一冻结快照开始。每轮的提示、模型响应、候选、编译结果及哈希均保存，便于复核。

这些中间 compiler diagnostics 标记为 `ORACLE_REPAIR_DIAGNOSTIC`，不计作被测模型的 C0 error event。多轮反馈不用于 C2；C2 仍是同一被测模型从冻结事件独立执行的一次 repair，因此不会因 oracle 获得额外信息而改变 PPL 分母或成功判据。

第一次 SDK 开发复测发现默认 profile 暴露 shell，模型自行调用了系统 Typst，因此该 run 不作为合规 oracle 证据。入口现以最高优先级 DSH patch 禁用全部模型工具，并在日志层拒绝任何残余 tool call。

禁用工具后的真实复测中，第 1 轮生成合法候选但仍有两处 prefix 编译错误，第 2 轮依据运行器返回的原样诊断修复并通过 prefix compile；两轮均无 tool call。此后完整编译才揭示 target 后的既存错误，且这些诊断未回传给 oracle。结果保留为 `CANDIDATE_REQUIRES_SEMANTIC_REVIEW`。
