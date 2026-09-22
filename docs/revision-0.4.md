# v0.4 角色分离修订

日期：2026-09-22。状态：draft。

## 修订原因

v0.3 让被测模型同时承担 C0 generation、C0 repair、C1 和 C2。这样会把两个目的混在一起：C0 需要尽可能稳定地修复当前错误并继续揭示文档中的错误事件；C2 才需要观察被测模型面对原错误时是否继续使用相同竞争性 procedure。

## 新角色

| 阶段 | 调用者 | 作用 |
| --- | --- | --- |
| C0 generation | 被测模型 | 生成真实 Typst 文档 |
| C0 event inventory | 编译器、确定性记录器、独立 dsh 会话 | 冻结错误事件、提出边界/依赖/taxonomy 建议 |
| C0 trajectory repair | dsh + step-5-preview oracle | 修复当前前缀并推进到下一 compiler-revealed event |
| C1 | 同一被测模型条件 | 独立验证目标能力 |
| C2 | 同一被测模型条件 | 从冻结事件快照独立执行 repair，形成 PPL outcome |

dsh oracle 的修复、解释和审核结果不进入 C1/C2 提示词。C0 oracle repair 和事件审核必须使用不同会话；同一输出不能由生成它的上下文自行作最终语义裁决。

C0 oracle 接收一个 selected primary diagnostic，以及 span 位于同一完整 target block 内的共位 diagnostics，并只返回修复后的 editable prefix。运行器将该 prefix 与冻结后文拼接；这样避免让 oracle 重写整份文档或被 target 外尚未轮到的错误分散，同时 C2 仍要求被测模型返回完整源码，以测量是否修改后文。

第一次完整源码 oracle 冒烟和第一次单诊断/前缀冒烟都消耗了输出进行冗长推理而没有最终结构化正文，因此记为 `INVALID_ORACLE_OUTPUT`，不算 repair 失败。C0 oracle 随后显式固定 `reasoning_effort=low`；它能快速返回结构化前缀，但仅给 primary diagnostic 时没有修复同一 target block 内的共位错误，prefix 编译失败并记为 `ORACLE_REPAIR_FAIL`。协议因此允许向 oracle 提供同一 target block 内的共位 diagnostics，同时继续隐藏 target 外的后续错误。

首次共位诊断 attempt 中，Step-5 将两个真实的 code-mode `#` 错误误判为 primary error 的级联，只修复了 `emph`，被真实 prefix compile 拒绝。oracle 提示因此明确要求返回的整个 editable prefix 可独立编译，并逐项检查共位诊断；失败 attempt 不作为下一快照，也不向被测模型披露。

增加该要求后的第二个独立 attempt 仍只修复 `emph`，再次由 prefix compile 判为 `ORACLE_REPAIR_FAIL`。这说明 dsh oracle 是修复提议者而非真值源；编译器门控不可省略。本次为开发 smoke，没有为了得到成功样本而继续补跑到上限。

## 统计边界

C0 最终计数由不可变事件记录、真实 Typst 诊断和冻结规则计算。dsh 可以生成结构化建议，但不能直接覆盖编译证据或最终计数。

串行发现的后续错误依赖 dsh oracle 的前序修改，因此单独标记 `PREEXISTING_HIDDEN / ORACLE_INDUCED / UNCERTAIN`，并报告 oracle 成功率和停止率。initial-generation incidence 与 dsh-oracle-assisted 串行 PCR 分开报告。

v0.3 的 Qwen repair 冒烟数据继续保留为历史基础设施证据，但不能混入 v0.4 的 C0 oracle 统计。
