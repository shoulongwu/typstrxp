# Procedural Prior Lock-in：C0–C2 实验实施协议

协议版本：`0.2.0-draft`，状态：审阅后草案，尚未预注册或冻结。
原稿完整保存在 [原始实验指导](docs/archive/experiments_guide.original.md)。
本版保留 C0 → C1 → C2 与 block-prefix compilation 的设计，修正判定与统计歧义。
变更依据、限制和待决问题见 [审阅报告](docs/review.md)。

## 1. 研究问题和结论边界

- C0：真实文档任务中，是否出现与竞争性 procedure 相符的错误？
- C1：同一模型配置是否在独立、低压力任务中展示过对应目标能力？
- C2：在提供原任务、事件首次出现时的源码、真实诊断和局部边界后，模型是否主动继续执行相同竞争性 procedure？

“错误”“修复失败”“出现 LaTeX 字符串”均不等于 PPL。
Strict PPL 是本协议下的操作性行为指标，不单凭本实验推断模型内部机制或训练来源。
C1 通过说明有可观察能力证据，并不证明任意复杂上下文下都必然具备相同能力。
实验结论应由结果决定，允许零 Strict PPL 结果。

## 2. 固定实验环境与条件

正式环境固定 Typst `0.12.0`；记录实际版本输出、二进制摘要、操作系统、字体清单、资源摘要和编译命令。
版本不符时阻止正式运行，不静默替换。当前工作机为 `0.15.1`，不能作为本协议正式编译结果。
锁定字体与资源后测 PDF 物理页数，源码行数不代表页数或质量。

每个模型条件记录 provider、精确 model ID / snapshot（如提供方可用）、调用日期、推理配置、temperature、top_p、输出上限、seed 支持情况、工具权限和完整请求。
参数不支持时记录 `unsupported`，不要伪装成已经设置；未知版本用 `unknown`。
C0 generation、C0 repair、C1、C2 默认同一模型条件；若使用不同 repair 模型，作为独立实验条件披露。
主实验默认普通独立 API 请求、无浏览器/工具调用和跨请求聊天历史。
用户指定星渡 Xindu（`https://xindu.xyz`），model ID：`qwen3.8-flash`、`glm-5.3-flash`、`deepseek-v4.1-flash`。基础地址配置为 `https://xindu.xyz/v1`，其 models 路径未认证访问返回 401；模型权限、真实版本、生成协议及参数支持仍须认证验证。用户不设金额预算上限；仍限制每事件/轨迹的调用次数。

在生成前固定任务顺序/随机种子、每题重复数、重试政策、预算上限和停止规则。
密钥只从环境读取，不写入实验记录。付费调用尚未实现。

## 3. 数据集与提示词

`data/c0_tasks.json` 是 C0 数据的唯一来源；`dataset.py` 提供加载、提示词构造、摘要与粗筛接口。
10 道题、5 类：讲义 3、论文 2、简历 2、考试 1、商业报告 2。
原来的 `C1_01`–`C1_10` 改为 `C0_01`–`C0_10`，保留 `legacy_id` 映射。
C1 atomic tasks 单独建立，不能把这 10 道真实任务拿来充当能力测试。

经用户授权放宽，所有任务统一 2–5 页（含端点）；页数为独立质量指标，不筛除编译错误事件。
移除页面/标题源码示例，数学需求使用描述性记法；不把数学内容本身视为语法教学。
任务仍包含数学表达式与“Typst”等必要上下文，因此不能声称实现了完全无提示的先验测量。
简历、商业数据是虚构案例，论文的模拟比较数据须标明，真实参考文献与模拟结果分开。
初版不依赖外部包、文件或网络；它测量的是受控的单文件真实任务，外部资源任务需作为另一个条件扩展。

`topic_screen` 仅返回关键词粗筛；不作为 C0 任务完成、C1 能力或 C2 修复成功判据。
C0 分开记录：编译成功、页数达标、内容达标、布局达标；质量检查失败不能删除已发生的 compiler events。
内容/布局使用冻结的题目 rubric（覆盖各题明确要求），初版人工复核。完整自动 checker 尚待实现。

## 4. 统计单位与不可变证据

三个层级：task → generation trajectory → error event；repair attempts 和 C2 runs 嵌套于 event。
同一事件的反复修复不生成多个独立 event。C0 中新揭示的独立错误才建立新 event。
每次发现保存事件首次出现时的完整快照，后续 C2 永远回放该快照；它可能是 S0，也可能是前几个 block 修复后的 Si。

至少保存：

```text
trajectory_id, event_id, parent_event_id, task_id, generation_repeat
protocol_version, dataset_version, prompt_hash, model_config_hash
raw_request, raw_response, finish_reason, usage, API_attempt_id
source_before, source_sha256, full compiler stdout/stderr/exit_code
selected_diagnostic_index, diagnostic_span, diagnostic_selection_policy
block range/text/type, target occurrence ranges, semantic_target
prefix gate status/evidence, origin status/evidence
repair attempt before/after, raw prefix, compile artifacts, outside-block diff
C1 run artifacts, C2 run artifacts, classifications, adjudications
```

未知值为 `null` / `UNKNOWN`，不可默认 true、FIXED 或 strict_ppl=false。
轨迹文件只追加、独立命名，不覆盖；分析重跑另存 analysis_version。
人工改判保存旧值、新值、审核者、时间与理由。

## 5. Repair Block 与位置约定

选择包含所选主诊断的最小完整、语义连贯的局部单元。
候选包括完整公式、heading（含 label）、list item 或必要的嵌套子树、函数调用、content/code block。
不能只数括号：必须处理字符串、注释、raw、数学/代码/markup 模式和错误恢复。
不可证明边界可靠时标 `BLOCK_PARSE_FAILURE` 并停止该自动轨迹或送审；禁止悄悄扩大成整个文件。

规范源码统一 UTF-8、LF，保留原始 response bytes 与规范化规则。
存储偏移为 Python Unicode code-point、0-based 半开区间 `[start,end)`；行号 1-based。
Typst 诊断坐标先保留原值；与内部偏移的转换须用中文、emoji、tab 样例验证，禁止直接等同。
C2 固定原始事件边界，不沿用 C0 修复后的偏移。
诊断存在多个 primary error 时，取编译器输出顺序的第一个 error，忽略 warning；顺序不等于源码从上至下。
若主诊断在文件外、找不到 span 或无法落到本地 block，送审并记录，不伪造位置。

## 6. Block 外变更检查

设原文 `S=P+B+Q`。模型返回完整源码 `T` 必须满足：

```text
T starts with P
T ends with Q
len(T) >= len(P) + len(Q)
```

新 block 为 `T[len(P):len(T)-len(Q)]`，Q 为空时用文末。
这避免 block 长度变化后错误地复用旧 end offset，也防止 P/Q 重叠的假合规。
不搜索“相似 block”，不 trim 空格，不重排，也不拼回原后文掩盖模型的越界修改。
返回格式要求纯源码；代码围栏或解释文字原样作为响应处理，不静默剥除。
原始响应、规范源码、外围 diff 均保存。

## 7. Prefix 可验证性门控

`Prefix = source[:block_end]`；修改后用新 block 的 end。
prefix 和完整文件使用相同项目根、字体、环境和资源。
语法嵌套、前向引用、文档查询、计数器/状态、后置标签等可能使截断改变结果。
因此“原始 prefix 出现同一错误”不是独立可验证的充分证明；目标错误可能遮蔽依赖问题。

gate 是 `VERIFIED / NON_SELF_CONTAINED / UNKNOWN`，以静态依赖检查或有记录的人工审查为依据，在观察 C2 outcome 前完成。
只有 VERIFIED 进入自动主分析；不确定即 UNKNOWN，不默认 true。
即使 prefix 编译通过，也要确认它仍然测量原语义目标。
不得临时人工补代码让 prefix 通过。未来若加入 dependency-preserving builder，必须新版本预注册并另报结果。

## 8. C0：生成和串行修复

1. 每次 generation 为新会话；保存完整输出、截断状态、配置与用量。
2. 编译完整 source；所有诊断与编译状态留存。
3. 若失败，选首个主 error、定位 block、建立 event 并检查 gate。
4. gate 通过后调用局部 repair，进行外围检查、prefix 编译与目标语义核验。
5. 只有 FIXED 才把修复后的完整文件提交为新 Si，并重新编译以揭示下一事件。
6. 失败 attempt 保留，不能把无效修复当成新正确基线。试点每事件最多 3 次，从同一事件快照发起新请求，不串联失败结果。
7. 每 trajectory 最多 20 次 repair 调用（试点暂定）；事件 3 次均未 FIXED、定位失败、gate 不通过、基础设施失败或预算达到上限即停止并报告原因。

完整文件编译通过后另行检查文档质量，不用质量退回修改来悄悄改变原 C0 轨迹。
被停止轨迹的下游错误尚未观察到，属于截尾；不能当作“没有其他错误”。

统一 repair 指令（C0 与 C2 共用，减少措辞混杂）：

> The following source was produced for the original Typst task.
> The Typst compiler reports an error inside the specified repair block.
> Fix only this repair block. You may make any necessary changes inside it,
> but do not alter source code outside it. Preserve the intended semantics and formatting.
> Return the complete corrected Typst source only, without code fences or commentary.

依次附原任务、完整 source、block 的 offset/行范围和单独的 block 文本、所选真实 diagnostic。
标记位于提示词元数据，不能插进 source 改变诊断行号。
不提示 prior 来源，不提供正确语法或映射。

## 9. Prior candidate 与 origin

taxonomy 分轴记录，避免把来源与错误领域混在同一 enum：

```text
error_category: SYNTAX / API / MATH / MATRIX / HEADING / LIST /
                LABEL_REFERENCE / NUMBERING / STRUCTURE / SEMANTIC / OTHER / UNKNOWN
prior_family: LATEX / MARKDOWN / OTHER / NONE / UNKNOWN
procedure_family: FRACTION / ROOT / MATRIX / HEADING / ... / UNKNOWN
is_prior_candidate: true / false / null
```

正则只生成线索；人工或可靠语法分析须确认 occurrence 在执行上下文、在目标 block 内，且与目标失败相关。
注释、字符串、raw、用户要求展示的源码不是 prior 执行证据。
Typst 与 Markdown 共享部分表面形式，不能仅凭符号判定来源。
能够编译却渲染错误的 prior-like 行为另建 semantic-error 探索集，不混入 compiler-triggered 主链。

origin：初始事件 `INITIAL_SOURCE`；后续事件 `PREEXISTING_HIDDEN / REPAIR_INDUCED / UNCERTAIN`。
错误在未改的 suffix 中，也可能由前面 definition/set/show 改动引起；错误在改过的 block 中也可能原已存在。
位置只记 `location_relation`，不得自动推断因果。只有有反事实/依赖证据时才给确定 origin，否则 UNCERTAIN。
原始生成自然错误与 repair-induced candidates 分层报告，后者不混入“自然生成错误”主结论。

## 10. C1：Atomic Capability

根据事件的 procedure_family 和 semantic_target 生成最小自然语言任务；不暴露原始错误、修复结果、Typst 语法、转换映射或 few-shot。
先冻结 atomic prompt 与 checker，再运行 3 次新会话；C2 不接收任何 C1 输出。
成功 = 编译通过 + semantic target 实现，后者使用对应结构/数值/渲染检查或盲审，不能靠源码关键词。
例如分数要核实分子、分母及分数排版，而不是发现字符 `/` 即通过。
2/3 为 `C1Capable`，3/3 为严格能力敏感性分析。
如基础设施问题导致不足 3 个可判定输出，C1 为 INCOMPLETE，不判模型“不会”。
主分析仅纳入能力已判定且 gate VERIFIED 的候选；报告所有未进入 C2 的数量与原因。

## 11. C2：三次独立回放

每个合格 event 固定 3 次模型生成机会，每次从同一任务、首次事件 source、诊断、原边界、模型配置和相同提示词开始。
不将前一 run、C0 repair、C1 结果或审核结论传给下一 run。
协议违规也消耗一次机会，不补跑直到凑满 3 个“好结果”。
传输失败可按预先固定政策重试；记录每次 API attempt，已收到模型输出的失败不能假装为传输重试。
输出上限截断记录 `TRUNCATED_RESPONSE`，保留原文，不把截断输出直接当作能力失败或 PPL。

判定优先级：

| 顺序 | 条件 | outcome |
| --- | --- | --- |
| 1 | 请求/编译基础设施失败、超时、截断、未知 gate | 对应状态或 PENDING_REVIEW，非可判定 run |
| 2 | block 外变更 | PROTOCOL_VIOLATION |
| 3 | prefix 编译通过，语义检查通过 | FIXED |
| 4 | prefix 编译通过，语义检查失败 | SEMANTIC_REGRESSION |
| 5 | 必要证据或语义审查无法判定 | PENDING_REVIEW |
| 6 | prefix 失败，目标 occurrence 未有效修改（含只改无关空白） | NO_TARGET_EDIT |
| 7 | prefix 失败，目标被主动修改且同一 prior + procedure 的 occurrence 仍执行并与失败有关 | SAME_PRIOR_PERSIST |
| 8 | 原 occurrence 已修复，但 block 内新生成相同 prior + procedure 并与失败有关 | SAME_PRIOR_RECURRED |
| 9 | prefix 失败，已无目标竞争 procedure，失败归于新目标实现 | OTHER_REPAIR_FAIL |

第 6 项先于第 7/8 项：完全不动目标即使旧文本还在，也不是 Strict PPL。
“相同 prior”必须同时匹配 prior_family、procedure_family、语义目标和执行上下文；只同属 LaTeX 不够。
新旧 occurrence 不能可靠对齐时送审，不用字符串出现次数猜测 recurrence。
`strict_ppl=true` 只对应第 7/8 项；排除或待审 run 为 null，不是 false。
FIXED 需要语义保持；删公式、换成原样代码或隐藏内容不是成功。
C0 使用同一局部判据与语义门控，避免污染后续轨迹。

## 12. 指标、分母和缺失

记 V 为：C1 capable、gate VERIFIED、未发生基础设施/截断问题、protocol compliant、完成裁决的 C2 runs。
V 包含 FIXED、SEMANTIC_REGRESSION、NO_TARGET_EDIT、SAME_PRIOR_PERSIST、SAME_PRIOR_RECURRED、OTHER_REPAIR_FAIL。

```text
PCR = unique prior candidate events / unique observed compiler error events
CR = C1 capable candidates / candidates with complete C1 adjudication
SPR = (SAME_PRIOR_PERSIST + SAME_PRIOR_RECURRED) / |V|
PPLScore(event) = that event's strict-PPL runs / that event's valid runs
```

空分母输出 NA/null。C1 覆盖率与 gate 覆盖率另报，不能把未测者当失败。
每 event 报计划数 3、收到输出数、valid 数、排除状态和 score；不声称一定有三个有效 run。
`PPLPositive` 仅在 valid=3 时按至少 2 次 strict PPL 定义；不足 3 次记 null。
另报 V 上的修复成功、语义退化、普通修复失败和 NO_TARGET_EDIT 各比例。
protocol violation rate 分母为已收到完整响应且可评估 locality 的 C2 输出；基础设施/截断率用计划 run 数并另报未执行数。

C0 RQ1 同时报 initial-generation 层面的 prior candidate incidence：
含至少一个确认初始 prior candidate 的 generation / 已完成初次编译的 generations。
串行 PCR 是 compiler-revealed sequence 的条件指标，不是初始源码所有错误的无偏计数。
按任务、模型、procedure、origin 分层，报告停止/截尾率。
同一任务事件高度相关；正式置信区间优先按 task 聚类重采样，报告 event-macro 与 run-micro 两种汇总；10 题试点只做描述，不作广泛显著性结论。
报告协议违规/待审缺失的选择偏差，并给排除 run 全部为 PPL / 全部非 PPL 的上下界敏感性分析（清楚注明分母改变）。

## 13. 人工审核和冻结

试点审核 block 边界、prefix 依赖、prior 上下文、目标有效修改、语义保持与 occurrence 对齐。
审核者可见必要完整前缀/依赖信息，隐藏模型身份、C1 结果和全局统计；不能为了盲审隐藏判断所必需的上下文。
争议例双人独立标注后裁决，保存一致率和改判记录。

10 题可作为最小 pilot，扩大任务集和正式留出集应在试点结束前计划。
任何改变提示词、dataset、parser、gate、语义 checker 或 outcome 规则都提升版本；不得合并不可比的正式数据。
冻结前必须补齐：模型配置/预算、字体与 Typst 0.12.0、每题 rubric、atomic task/checker、标注手册、采样与统计方案、明确的覆盖率验收阈值。
阈值尚未确定，不能以“足够高”视为通过。

## 14. 仓库实施顺序

1. 已提供：版本化任务、原稿备份、协议审阅、数据校验、纯函数 locality 检查及核心回归测试。
2. 下一步：0.12.0 compiler harness、结构化诊断、可靠 block parser/人工 fallback、prefix gate；用公式/矩阵/标题/列表/函数/content/code fixtures 验证。
3. 实现不可变 artifact store、模型 adapter、C0 串行状态机。
4. 建立候选 detector、origin evidence、题目/atomic rubrics 与审核记录。
5. 接入独立 C1/C2 与上述 outcome classifier、聚类分析和 pilot 报告。

本仓库目前是审阅与实施基础，尚不能自动跑完整 C0–C2；不得用模拟输出替代真实模型实验。
