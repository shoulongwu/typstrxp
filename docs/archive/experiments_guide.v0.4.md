# Procedural Prior Lock-in：C0–C2 实验实施协议

协议版本：`0.4.0-draft`，状态：审阅后草案，尚未预注册或冻结。
原稿完整保存在 [原始实验指导](docs/archive/experiments_guide.original.md)。
本版保留 C0 → C1 → C2 与 prefix compilation，按用户修订把编辑范围扩大为文档开头至目标 block 结束，允许修复先前定义。C0 使用 dsh + step-5-preview 建立并推进错误事件轨迹；被测模型只在 C0 generation、C1 和 C2 中调用。v0.2 的 block-only 和 v0.3 的同模型 C0 repair 版本均另存档，不同条件不能直接合并统计。
变更依据、限制和待决问题见 [审阅报告](docs/review.md)。

## 1. 研究问题和结论边界

- C0：被测模型的真实文档 generation 中，是否出现与竞争性 procedure 相符的错误？dsh oracle 能否在保留语义和后文的前提下修复当前事件并揭示后续错误？
- C1：同一模型配置是否在独立、低压力任务中展示过对应目标能力？
- C2：在提供原任务、事件首次出现时的源码、真实诊断和前缀编辑边界后，模型是否主动继续执行相同竞争性 procedure？

“错误”“修复失败”“出现 LaTeX 字符串”均不等于 PPL。
Strict PPL 是本协议下的操作性行为指标，不单凭本实验推断模型内部机制或训练来源。
C1 通过说明有可观察能力证据，并不证明任意复杂上下文下都必然具备相同能力。
实验结论应由结果决定，允许零 Strict PPL 结果。

## 2. 固定实验环境与条件

正式环境固定 Typst `0.12.0`；记录实际版本输出、二进制摘要、操作系统、字体清单、资源摘要和编译命令。
版本不符时阻止正式运行，不静默替换。系统默认编译器为 `0.15.1`；Qwen 冒烟测试已独立安装 `0.12.0 (737895d7)`，路径见 `configs/pilot.json` 的 `typst_binary`。不得将系统默认版本结果冒充固定版本结果。
锁定字体与资源后测 PDF 物理页数，源码行数不代表页数或质量。

每个模型条件记录 provider、精确 model ID / snapshot（如提供方可用）、调用日期、推理配置、temperature、top_p、输出上限、seed 支持情况、工具权限和完整请求。
参数不支持时记录 `unsupported`，不要伪装成已经设置；未知版本用 `unknown`。
被测模型承担 C0 generation、C1 atomic task 和 C2 repair replay。C0 trajectory repair 固定由 dsh headless + step-5-preview oracle 承担，用于建立错误事件库和推进到下一个 compiler-revealed event，不属于被测模型条件，也不进入 PPL repair 分子或分母。
主实验中的被测模型调用使用普通独立 API 请求、无浏览器/工具调用和跨请求聊天历史。dsh 的模型、版本、提示词、会话和每次输出必须单独记录；不得把 dsh 的修复能力归因给被测模型。
按用户最新 `apikey.config` 配置并实测：`glm-5.3-flash` 使用星渡 `https://xindu.xyz/v1` 的 glm 凭据；`qwen3.8-flash` 使用 `https://maas.qianwenaiapi.com/compatible-mode/v1` 的 qwen 凭据。
DeepSeek 原星渡 deepseek 凭据返回 401；用户文件明确注明 qwen 凭据也支持 `deepseek-v4.1-flash`，该备用连接实测 200 后设为当前路由。三个模型独立配置，不做未记录的凭据/服务回退。环境变量可按模型覆盖。
当前三个模型均有短 Chat Completions 连通证据；真实快照身份及完整实验参数支持仍需进一步核验。服务方/路由属于模型条件，不得把不同路由结果直接混合。用户不设金额预算上限；仍限制每事件/轨迹的调用次数。

在生成前固定任务顺序/随机种子、每题重复数、重试政策、预算上限和停止规则。
密钥只从环境读取，不写入实验记录。已完成开发冒烟调用；完整付费实验运行尚未实现。

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
target_block range/text/type, target occurrence ranges, semantic_target
repair_scope=prefix_through_target, editable_start=0, editable_end=target_block_end
dependency_spans_before, target_locator_after, changed_spans, upstream_semantics_check
prefix gate status/evidence, origin status/evidence
C0 oracle repair before/after, oracle identity/session, raw prefix, compile artifacts, outside-block diff
C1 run artifacts, C2 run artifacts, classifications, adjudications
```

未知值为 `null` / `UNKNOWN`，不可默认 true、FIXED 或 strict_ppl=false。
轨迹文件只追加、独立命名，不覆盖；分析重跑另存 analysis_version。
人工改判保存旧值、新值、审核者、时间与理由。

## 5. Target Block 与 Editable Prefix

Target Block 是包含所选主诊断的最小完整、语义连贯的局部单元，用于定位错误和确定截断终点。
Editable Prefix 则是 `[0, target_block_end)`，包含整个目标 block 和全部先前源码，才是模型允许编辑的范围。两者不能混称。
候选包括完整公式、heading（含 label）、list item 或必要的嵌套子树、函数调用、content/code block。
不能只数括号：必须处理字符串、注释、raw、数学/代码/markup 模式和错误恢复。
不可证明目标边界可靠时标 `BLOCK_PARSE_FAILURE` 并停止该自动轨迹或送审。目标 block 恰位于文末时，前缀编辑范围自然覆盖全文；记录该事实和覆盖比例，不额外禁止。

规范源码统一 UTF-8、LF，保留原始 response bytes 与规范化规则。
存储偏移为 Python Unicode code-point、0-based 半开区间 `[start,end)`；行号 1-based。
Typst 诊断坐标先保留原值；与内部偏移的转换须用中文、emoji、tab 样例验证，禁止直接等同。
C2 固定原始事件 target block 和 editable prefix 的边界，不沿用 C0 修复后的偏移。修复后前文可能变长，不能复用原 target start/end 定位新目标；需要结构或语义重新定位并记录证据，无法定位则送审。
诊断存在多个 primary error 时，取编译器输出顺序的第一个 error，忽略 warning；顺序不等于源码从上至下。
若主诊断在文件外、找不到 span 或无法落到本地 block，送审并记录，不伪造位置。

## 6. 编辑范围检查：只冻结后文

设原文 `S=P+B+Q`，B 为目标 block，P 为先前源码，Q 为 block 之后的后文。
允许修改 `E=P+B`；模型返回的完整源码 T 必须满足：

```text
T ends with Q
len(T) >= len(Q)
E_after = T[:len(T)-len(Q)]  # Q 为空时取全文
```

不再要求 P 不变。`prefix_unchanged` 只作为描述性字段，不能用来判协议违规。
Q 逐字符相同是文本合规条件；删除整个 E 仍可能合规，但属于语义退化，不是 FIXED。
`new_end` 是编辑前缀的新终点，不等于通过旧 start 定位的 target block 终点。
不搜索“相似后文”、不 trim、不拼回旧后文掩盖违规。
原始响应、规范源码、E 的 diff、后文是否不变和前文修改区域都保存。

默认条件名为 `prefix_through_target`；可选 `block_only` 仅作为独立对照，不能混用提示词、分母或结果。
后文文本未改不保证其语义不变：上游 definition/set/show 的修改可能影响后文，必须在完整编译及后续事件归因中记录。

## 7. Prefix 可验证性门控

`Prefix_before = source[:target_block_end]`；修改后通过不变后文 Q 恢复 `E_after`，直接编译整个 E_after。
新目标可在 E_after 中迁移或重构，但必须保留原本目标和前文内容的意图。
prefix 和完整文件使用相同项目根、字体、环境和资源。
语法嵌套、前向引用、文档查询、计数器/状态、后置标签等可能使截断改变结果。
因此“原始 prefix 出现同一错误”不是独立可验证的充分证明；目标错误可能遮蔽依赖问题。

gate 是 `VERIFIED / NON_SELF_CONTAINED / UNKNOWN`，以静态依赖检查或有记录的人工审查为依据，在观察 C2 outcome 前完成。
只有 VERIFIED 进入自动主分析；不确定即 UNKNOWN，不默认 true。
即使 prefix 编译通过，也要确认它仍然测量原语义目标。
不得临时人工补代码让 prefix 通过。未来若加入 dependency-preserving builder，必须新版本预注册并另报结果。

## 8. C0：被测模型生成与 dsh oracle 串行修复

1. 每次 generation 为新会话；保存完整输出、截断状态、配置与用量。
2. 编译完整 source；所有诊断与编译状态留存。
3. 若失败，选首个主 error、定位 block、建立 event 并检查 gate。
4. gate 通过后先冻结事件快照、诊断、边界和初步 taxonomy；再由全新 dsh headless + step-5-preview 会话执行局部 oracle repair，进行后文不变检查、prefix 编译、目标和受影响前文的语义核验。
5. 只有 FIXED 才把修复后的完整文件提交为新 Si，并重新编译以揭示下一事件。
6. oracle 失败 attempt 保留，不能把无效修复当成新正确基线。试点每事件最多 3 次，从同一事件快照发起新的 dsh 会话，不串联失败结果。
7. 每 trajectory 最多 20 次 oracle repair 调用（试点暂定）；事件 3 次均未 FIXED、定位失败、gate 不通过、基础设施失败或预算达到上限即停止并报告原因。

完整文件编译通过后另行检查文档质量，不用质量退回修改来悄悄改变原 C0 轨迹。
被停止轨迹的下游错误尚未观察到，属于截尾；不能当作“没有其他错误”。

统一 repair 核心任务（C0 oracle 与 C2 被测模型共用，调用角色、输出契约和元数据分开）：

> The following source was produced for the original Typst task.
> The compiler reports an error in the specified target block; its cause may lie in earlier code.
> Fix the error by modifying the target block and/or any necessary source before it.
> You may edit only the prefix from the beginning of the document through the end of the target block.
> Do not change any source after the target block. Preserve the intended semantics and formatting
> of the target and all preceding content. Keep changes focused on the reported error and its dependencies.

C0 oracle 输出契约：

> The following source was produced for the original Typst task.
> The compiler reports an error in the specified target block; its cause may lie in earlier code.
> Fix the error by modifying the target block and/or any necessary source before it.
> You may edit only the prefix from the beginning of the document through the end of the target block.
> Do not change any source after the target block. Preserve the intended semantics and formatting
> of the target and all preceding content. Keep changes focused on the reported error and its dependencies.
> Return only the complete corrected editable prefix from document start through the repaired target,
> in the requested response field, without code fences or commentary.

C2 被测模型输出契约：

> The following source was produced for the original Typst task.
> The compiler reports an error in the specified target block; its cause may lie in earlier code.
> Fix the error by modifying the target block and/or any necessary source before it.
> You may edit only the prefix from the beginning of the document through the end of the target block.
> Do not change any source after the target block. Preserve the intended semantics and formatting
> of the target and all preceding content. Keep changes focused on the reported error and its dependencies.
> Return the complete corrected Typst source only, without code fences or commentary.

C0 返回 prefix 是 oracle 的传输优化：运行器只能把它与冻结 Q 拼接，仍对拼接结果执行 locality、prefix compile 和完整编译。C2 必须返回完整源码，因为是否修改 Q 本身就是被测 outcome 的一部分。

依次附原任务、完整 source、target block 的 offset/行范围和单独文本、editable prefix `[0,end)` 范围、一个所选真实 primary diagnostic，以及诊断 span 同样落在该 target block 内的共位 diagnostics。target block 外的后续 diagnostics 不得交给当前 repair。

事件统计以 selected primary diagnostic 为索引；同一次编译产生的全部 raw diagnostics 另存。共位 diagnostics 是使完整 target/prefix 可验证所需的 repair context，不额外计作独立 event；若需独立研究其中某项，必须从冻结的原始快照建立明确关联的 secondary event，不能重复计数。
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

正则只生成线索；人工或可靠语法分析须确认 occurrence 在执行上下文、在 editable prefix 的目标或相关依赖内，且与目标失败相关。候选 occurrence 可位于目标 block 或前缀内相关依赖定义，不能因为定义位于 block 前就排除。
注释、字符串、raw、用户要求展示的源码不是 prior 执行证据。
Typst 与 Markdown 共享部分表面形式，不能仅凭符号判定来源。
能够编译却渲染错误的 prior-like 行为另建 semantic-error 探索集，不混入 compiler-triggered 主链。

origin：初始事件 `INITIAL_SOURCE`；后续事件 `PREEXISTING_HIDDEN / ORACLE_INDUCED / UNCERTAIN`。
错误在未改的 suffix 中，也可能由前面 definition/set/show 改动引起；错误在改过的 block 中也可能原已存在。
位置只记 `location_relation`，不得自动推断因果。只有有反事实/依赖证据时才给确定 origin，否则 UNCERTAIN。
原始生成自然错误与 oracle-induced candidates 分层报告，后者不混入“自然生成错误”主结论。

## 10. C1：Atomic Capability

根据事件的 procedure_family 和 semantic_target 生成最小自然语言任务；不暴露原始错误、修复结果、Typst 语法、转换映射或 few-shot。
先冻结 atomic prompt 与 checker，再运行 3 次新会话；C2 不接收任何 C1 输出。
成功 = 编译通过 + semantic target 实现，后者使用对应结构/数值/渲染检查或盲审，不能靠源码关键词。
例如分数要核实分子、分母及分数排版，而不是发现字符 `/` 即通过。
2/3 为 `C1Capable`，3/3 为严格能力敏感性分析。
如基础设施问题导致不足 3 个可判定输出，C1 为 INCOMPLETE，不判模型“不会”。
主分析仅纳入能力已判定且 gate VERIFIED 的候选；报告所有未进入 C2 的数量与原因。

## 11. C2：三次独立回放

每个合格 event 固定 3 次被测模型 repair 机会，每次从同一任务、首次事件 source、诊断、原边界、被测模型配置和相同提示词开始。
不将前一 run、C0 oracle repair、C1 结果或审核结论传给下一 run。
协议违规也消耗一次机会，不补跑直到凑满 3 个“好结果”。
传输失败可按预先固定政策重试；记录每次 API attempt，已收到模型输出的失败不能假装为传输重试。
输出上限截断记录 `TRUNCATED_RESPONSE`，保留原文，不把截断输出直接当作能力失败或 PPL。

判定优先级：

| 顺序 | 条件 | outcome |
| --- | --- | --- |
| 1 | 请求/编译基础设施失败、超时、截断、未知 gate | 对应状态或 PENDING_REVIEW，非可判定 run |
| 2 | 目标 block 后的后文 Q 变更 | PROTOCOL_VIOLATION |
| 3 | prefix 编译通过，目标与受影响前文语义检查通过 | FIXED |
| 4 | prefix 编译通过，目标或受影响前文语义检查失败 | SEMANTIC_REGRESSION |
| 5 | 必要证据或语义审查无法判定 | PENDING_REVIEW |
| 6 | prefix 失败，目标及其因果依赖均未有效修改（含只改无关空白） | NO_TARGET_EDIT |
| 7 | prefix 失败，目标或因果依赖被主动修改，且同一 prior + procedure 的 occurrence 仍执行并与失败有关 | SAME_PRIOR_PERSIST |
| 8 | 原 occurrence 已修复，但 editable prefix 的目标/因果依赖中新增相同 prior + procedure 并与同一目标失败有关 | SAME_PRIOR_RECURRED |
| 9 | prefix 失败，已无目标竞争 procedure，失败归于新目标实现 | OTHER_REPAIR_FAIL |

第 6 项先于第 7/8 项：目标及因果依赖均未有效修改时，即使旧文本还在，也不是 Strict PPL。
仅修改先前错误定义可以是有效修复；目标 block 文本未变并不等于 NO_TARGET_EDIT。判断 target_or_dependency_modified 需依赖证据，不能用“prefix 有任意变化”替代。
“相同 prior”必须同时匹配 prior_family、procedure_family、语义目标和执行上下文；只同属 LaTeX 不够。
新旧 occurrence 不能可靠对齐时送审，不用字符串出现次数猜测 recurrence。
`strict_ppl=true` 只对应第 7/8 项；排除或待审 run 为 null，不是 false。
FIXED 需要目标与受影响前文语义保持；删公式、换成原样代码、隐藏内容或破坏先前正确定义不是成功。
若上游新错误遮蔽原目标，无法确认 prior 是否仍实际导致同一目标失败，记 PENDING_REVIEW；不因前缀里有旧字符串就判持续。
C0 使用同一前缀判据与语义门控，避免污染后续轨迹。

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

C0 错误统计由确定性的编译结果、事件记录和冻结规则计算；dsh 可提出 target、依赖、taxonomy 和语义判断建议，但不能直接写入或改写最终计数。所有建议须保存 evidence spans，并通过 schema、编译证据和人工抽查。

C0 RQ1 同时报 initial-generation 层面的 prior candidate incidence：
含至少一个确认初始 prior candidate 的 generation / 已完成初次编译的 generations。
串行 PCR 是 dsh-oracle-assisted compiler-revealed sequence 的条件指标，不是初始源码所有错误的无偏计数。必须另报 oracle 停止率、oracle repair 成功率，以及 `PREEXISTING_HIDDEN / ORACLE_INDUCED / UNCERTAIN` origin；oracle 修改后出现的错误不得自动算作被测模型的自然错误。
按任务、模型、procedure、origin 分层，报告停止/截尾率。
同一任务事件高度相关；正式置信区间优先按 task 聚类重采样，报告 event-macro 与 run-micro 两种汇总；10 题试点只做描述，不作广泛显著性结论。
报告协议违规/待审缺失的选择偏差，并给排除 run 全部为 PPL / 全部非 PPL 的上下界敏感性分析（清楚注明分母改变）。

## 13. 人工审核和冻结

试点由独立 dsh 会话辅助定位和审核 target block 边界、prefix 依赖、prior 上下文、目标/依赖有效修改、前文及目标语义保持与 occurrence 对齐。错误盘点/分类会话应在看到 oracle repair 结果前冻结；repair 会话不得兼任自身输出的最终语义裁决。
审核者可见必要完整前缀/依赖信息，隐藏模型身份、C1 结果和全局统计；不能为了盲审隐藏判断所必需的上下文。
使用 dsh headless + step-5-preview 的独立会话分别承担 C0 oracle repair 与错误事件初筛/结构化建议。两类会话必须使用不同运行目录并记录用途，避免同一上下文既修复又裁决。
dsh 不替代真实 Typst compiler，不直接修改冻结的事件快照；oracle 输出只作为候选 `source_after` 保存，经 locality、编译和语义门控通过后才能成为下一 Si。任何 dsh 修复、解释或审核反馈都不得进入 C1/C2 提示词。
每个审核任务使用独立会话和原任务、必要源码/依赖及真实诊断；inventory 会话不接收 oracle 输出，repair 后审核才接收 source_after 与修改 diff。所有审核隐藏被测模型身份、密钥、C1 结果和总统计。
记录 reviewer 模型/版本、dsh 版本、提示词摘要、原始返回、置信度和证据。低置信、规则冲突、Strict PPL 阳性和抽样阴性进入人工复核。
自动建议未通过模式校验与证据核对时保持 PENDING_REVIEW；正式自动裁决须先有人工标注集验证并冻结阈值。
争议例双人独立标注后裁决，保存一致率和改判记录。

10 题可作为最小 pilot，扩大任务集和正式留出集应在试点结束前计划。
任何改变提示词、dataset、parser、gate、语义 checker 或 outcome 规则都提升版本；不得合并不可比的正式数据。
冻结前必须补齐：模型配置/预算、字体与 Typst 0.12.0、每题 rubric、atomic task/checker、标注手册、采样与统计方案、明确的覆盖率验收阈值。
阈值尚未确定，不能以“足够高”视为通过。

## 14. 仓库实施顺序

1. 已提供：版本化任务、原稿备份、协议审阅、数据校验、前缀范围 locality 检查、分模型凭据加载、dsh oracle repair/审核入口及核心回归测试。
2. 下一步：0.12.0 compiler harness、结构化诊断、可靠 block parser/人工 fallback、prefix gate；用公式/矩阵/标题/列表/函数/content/code fixtures 验证。
3. 实现不可变 artifact store、模型 adapter、C0 串行状态机。
4. 建立候选 detector、origin evidence、题目/atomic rubrics 与审核记录。
5. 接入独立 C1/C2 与上述 outcome classifier、聚类分析和 pilot 报告。

本仓库目前是审阅与实施基础，尚不能自动跑完整 C0–C2；不得用模拟输出替代真实模型实验。
