# dsh C0 Oracle 冒烟结果

日期：2026-09-22。输入事件来自历史 `qwen-smoke-002` 的首个完整 target block，仅用于验证 v0.4 的 C0 oracle 通路，不进入正式统计。

## 配置演进

1. 完整源码输出、默认推理强度：Step-5 消耗输出进行冗长推理，没有最终结构化正文，记 `INVALID_ORACLE_OUTPUT`。
2. 单 primary diagnostic、只返回 editable prefix、默认推理强度：仍没有最终正文，记 `INVALID_ORACLE_OUTPUT`。
3. 固定 `reasoning_effort=low`：15 秒内返回合法 JSON 和后文不变的候选前缀，但只修复 primary `emph` 错误，没有处理同一 target block 内的两个 code-mode `#` 错误；prefix 编译失败。
4. 向 oracle 提供该 target block 内全部 6 条共位诊断，并明确要求完整 prefix 可编译：两个独立 attempt 都只修改 `emph`，均记 `ORACLE_REPAIR_FAIL`。

target block 外的行 17、21、182、186 诊断没有进入最终 oracle prompt。所有候选都由运行器与冻结后文拼接，后文逐字符不变。

## 结论

dsh + step-5-preview 已能稳定返回结构化前缀，但该事件上连续两次未产生可编译修复。C0 oracle 只能作为候选修复者；真实 Typst 0.12.0 prefix compile、locality 和独立语义审核共同决定候选能否成为下一快照。失败结果不能交给被测模型，也不能计为 PPL repair。

原始输出、reasoning、编译诊断及 metadata 位于被 `.gitignore` 排除的 `runs/dsh-oracle-smoke-001` 至 `005`。
