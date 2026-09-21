# Procedural Prior Lock-in：C0–C2 Typst 实验实施指南

## 1. 实验背景

大型语言模型在生成相对低频或较新的程序语言、标记语言时，可能受到训练中更强、更高频的已有程序性模式影响。

以 Typst 为例，模型可能具备正确的 Typst 能力，但在真实复杂任务中仍生成来自 LaTeX、Markdown 等其他体系的 procedure，例如：

```latex
\frac{a}{b}
\section{...}
\begin{pmatrix}
\label{...}
\ref{...}
```

而不是目标 Typst procedure。

本研究将这种现象称为：

\[
\boxed{\text{Procedural Prior Lock-in, PPL}}
\]

研究中特别区分：

\[
\text{不会正确 procedure}
\neq
\text{PPL}
\]

以及：

\[
\text{普通生成/修复错误}
\neq
\text{PPL}
\]

真正需要验证的是：

> 模型已经被证明具备正确 Typst procedure 的能力，但在真实任务中调用了竞争性的旧 procedure；在获得原始任务、原始错误代码和真实 compiler error 后，只要求修复对应局部 block，模型仍然继续执行相同的 competing procedure。

因此实验采用三级结构：

\[
\boxed{
C0:\ Realistic\ Failure
\rightarrow
C1:\ Capability
\rightarrow
C2:\ Strict\ PPL
}
\]

---

# 2. 核心研究问题

## RQ1：真实场景中是否自然出现 procedural-prior errors？

\[
P(\text{PriorError}\mid \text{realistic task})
\]

由 C0 回答。

---

## RQ2：这些错误是不是因为模型根本不会相应 Typst procedure？

对每一个候选错误，在简单、低压力环境下独立验证对应能力。

由 C1 回答。

---

## RQ3：已经证明会正确 procedure 后，给出明确真实错误信息并将任务缩小至单个 block，模型是否仍继续使用旧 procedure？

\[
P(
\text{Same Prior Persists}
\mid
Capability=1,\ ErrorEvidence,\ LocalBlockRepair
)
\]

由 C2 回答。

这是 Strict PPL 的核心验证。

---

# 3. 总体流程

```text
真实场景任务
    ↓
LLM 生成完整 Typst
    ↓
Typst compiler
    ↓
发现第一个 compiler error
    ↓
定位包含该 error 的最小完整 Repair Block
    ↓
保存完整 source + block + compiler error
    ↓
Agent 只允许修改这个 block
    ↓
检查 block 外代码是否完全不变
    ↓
截断 block 之后全部源码
    ↓
编译 [文件开头 → 当前 block 结束] 的 prefix
    ↓
判断当前 block 是否修复成功
    ↓
若成功，将修复后的完整文件继续 compile
    ↓
发现下一个 error
    ↓
重复直到完整文件 compile success / 终止
    ↓
得到 error-event registry
    ↓
筛选 PPL candidates
    ↓
C1 capability verification
    ↓
C1 通过的事件进入 C2
    ↓
C2：原任务 + 原答案 + compiler error
        只修当前 Repair Block
    ↓
相同 block-prefix compilation 验证
    ↓
FIXED / SAME_PRIOR_PERSIST /
OTHER_REPAIR_FAIL / NO_TARGET_EDIT /
PROTOCOL_VIOLATION
    ↓
计算 PPL 指标
```

实验基本统计单位不是整道题，而是：

\[
\boxed{\text{Error Event}}
\]

同一真实任务可以产生多个 Error Event。

---

# 4. 实验环境

统一固定：

```text
Typst 0.12.0
```

每次实验保存实际：

```bash
typst --version
```

结果。

尽量使用 Typst 0.12.0 之前已经稳定存在的核心功能，避免把版本知识不足误判为 PPL。

---

# 5. Repair Block：核心定义

从本版本开始，所有 C0 repair 和 C2 repair 的最小操作单位不再是“单个 token / 单行 error”，而是：

\[
\boxed{\text{Repair Block}}
\]

Repair Block 定义为：

> **包含当前 compiler error 的最小完整、语义连贯、语法完整的局部单元，并允许模型在该单元内部自由修复，但禁止修改该单元之外的源码。**

例如：

### 公式错误

```typst
$ ... $
```

整个 equation/math block 为 Repair Block。

---

### 矩阵错误

若 matrix 位于：

```typst
$ mat(...) $
```

则整个相关 math/equation block 为 Repair Block，而不是只允许替换某个 `\frac` token。

---

### Heading 错误

对应完整 heading：

```typst
= Heading <label>
```

---

### List 错误

如果 compiler error 位于一个列表 item 内，应根据错误实际依赖范围选择：

```typst
+ 当前 item
```

或者必要时选择其完整局部 nested-list subtree。

---

### 函数调用错误

例如：

```typst
#figure(
  ...
)
```

整个函数调用作为 block。

---

### Content/code block

对于：

```typst
#[...]
```

```typst
#{
  ...
}
```

应包含完整的 balanced block。

---

# 6. Repair Block 的选择原则

选择：

\[
\boxed{\text{smallest complete block that safely contains the error}}
\]

而不是：

\[
\text{smallest textual span}
\]

也不是：

\[
\text{整个文件}
\]

选择 Repair Block 时遵守：

1. 必须完整包含当前 compiler diagnostic 对应位置；
2. 括号、content block、code block 等必须完整闭合；
3. 允许模型修改修复该错误所需的相关局部结构；
4. 不应包含明显无关的后续 block；
5. 一旦选定，C0/C2 所有对应 replay 使用完全相同的 block boundary。

保存：

```text
block_start_offset
block_end_offset
block_start_line
block_end_line
block_type
block_text_before
```

---

# 7. Block Local-Compilability Gate

block-prefix compilation 是核心 oracle，因此必须先判断当前 event 是否适合该验证方式。

定义原文 prefix：

\[
Prefix_i
=
Source[0:\mathrm{BlockEnd}_i]
\]

即：

> 从文档第一字符开始，到当前 Repair Block 结束为止，删除所有下文。

但是某些 block 可能依赖被截断的后文，例如：

- 后置 label；
- 后置 definition；
- 后文资源；
- 其他必须存在的结构。

这种情况下，截断本身会制造一个与当前 error 无关的新 failure。

因此每个事件保存：

```text
prefix_verifiable: true / false
```

如果无法可靠进行 block-prefix 验证：

```text
prefix_verifiable = false
```

标记：

```text
NON_SELF_CONTAINED
```

该 event 可以保留用于错误统计，但：

\[
\boxed{\text{不得进入自动 Strict-PPL 主分析}}
\]

除非实现了明确、预注册的 dependency-preserving prefix builder。

不得为了让它编译而临时人工补代码。

---

# 8. C0：真实场景生成

C0 目标：

> 观察真实 Typst 工作任务中自然出现的错误及 procedural-prior errors。

模型首先生成完整源码：

\[
S_0
\]

保存：

```text
task_id
model
model_version
configuration
reasoning_mode
temperature
seed_if_available

original_prompt
raw_response
extracted_typst
```

执行：

```bash
typst compile source.typ output.pdf
```

---

# 9. C0 Serial Block Repair

如果：

\[
Compile(S_0)=Fail
\]

得到第一个：

\[
e_1
\]

定位其 Repair Block：

\[
B_1
\]

形成：

```text
Event 1:
    source_before = S0
    compiler_error = e1
    repair_block = B1
```

然后调用 Agent。

---

# 10. Repair Agent 指令

统一提示词：

> The Typst compiler reports an error inside the marked repair block.
>
> Fix only this repair block so that this local part of the document becomes valid.
>
> You may modify anything necessary inside the marked block, but do not change any source code outside the block.
>
> Preserve the intended semantics and formatting.
>
> Return the complete Typst source only.

提供：

```text
Original Task

Full Current Source

Repair Block boundaries

Current Compiler Diagnostic
```

核心约束从：

> 只修一个 error

修改为：

\[
\boxed{\text{只修一个 Repair Block}}
\]

这样允许模型正确处理一个错误涉及多行、多 token 或局部结构联动的情况。

---

# 11. 为什么使用 block 而不是单 error 修改

单 token / 单行限制容易产生额外 confound。

例如：

```latex
\begin{pmatrix}
...
\end{pmatrix}
```

正确修复可能需要整体重构 matrix。

如果强制：

> 只能修改 compiler 指出的那个 token

模型即使知道答案也可能无法完成合法 repair。

因此实验真正需要控制的是：

\[
\text{locality}
\]

而不是：

\[
\text{number of edited characters}
\]

Repair Block 允许：

\[
\text{local structural correction}
\]

同时防止模型顺便重写整篇文件。

---

# 12. Block 外修改检测

不能仅依靠 prompt 相信模型只修改了 block。

必须自动检查。

令：

\[
S_{before}
\]

为修复前完整源码，

\[
S_{after}
\]

为模型返回的完整源码。

将源码分成：

\[
S=P+B+Q
\]

其中：

- \(P\)：block 之前的 prefix；
- \(B\)：Repair Block；
- \(Q\)：block 之后的 suffix。

标准 repair 必须满足：

\[
\boxed{
P_{before}=P_{after}
}
\]

以及：

\[
\boxed{
Q_{before}=Q_{after}
}
\]

仅：

\[
B
\]

允许发生变化。

实现时可预先统一：

- newline format；
- 文件编码；

但不得进行会掩盖源码变化的语义 normalize。

如果 block 外发生任何实质变化：

```text
protocol_violation = true
```

该 run 分类：

```text
PROTOCOL_VIOLATION
```

不得进入标准 repair 成功率和 PPL numerator。

保存：

```text
prefix_unchanged
suffix_unchanged
outside_block_changed
outside_block_diff
```

---

# 13. C0 的核心验证方式：Block-Prefix Compilation

从本版本起，废除原来的：

```text
diagnostic disappearance
→ target checker
→ truncation fallback
```

多级验证优先级。

主要 oracle 统一改为：

\[
\boxed{\text{Block-Prefix Compilation}}
\]

修复后构造：

\[
Prefix_{after}
=
S_{after}[0:\mathrm{end}(B_{after})]
\]

也就是：

```text
文档开头
...
当前修复后的 block
<EOF>
```

当前 block 后的所有源码全部舍弃。

然后执行：

```bash
typst compile prefix.typ prefix.pdf
```

---

# 14. Block-Prefix Compilation 判定

如果：

\[
Compile(Prefix_{after})=Success
\]

则：

\[
\boxed{CurrentBlockFixed=1}
\]

此时无需考虑原始完整文件的后续错误。

如果：

\[
Compile(Prefix_{after})=Fail
\]

则：

\[
CurrentBlockFixed=0
\]

随后根据源码变化和 prior detector 判断属于：

```text
SAME_PRIOR_PERSIST
OTHER_REPAIR_FAIL
NO_TARGET_EDIT
```

---

# 15. 为什么 prefix compilation 比完整文件 compilation 更合适

假设原文有：

```text
Block A   ← 当前 error
Block B   ← 隐藏 error
Block C   ← 隐藏 error
```

修复 A 后，完整 compiler 很可能立即报告 B。

因此：

\[
Compile(FullDocument)=Fail
\]

不能说明：

\[
A\text{ 没修好}
\]

使用：

\[
DocumentStart\rightarrow End(BlockA)
\]

的 prefix compilation，可以把 B、C 完全排除。

当前 experiment event 只回答：

> 当前 block 是否已经能够正确工作？

这与 serial repair 的实验单位一致。

---

# 16. 修复成功后如何继续 Serial Repair

如果：

\[
Compile(Prefix_{after})=Success
\]

说明当前 block 修复完成。

此时保留：

\[
S_{after}
\]

的**完整文件版本**，包括原样未修改的 suffix。

然后重新：

```bash
typst compile full_source.typ output.pdf
```

得到下一条真实 compiler error：

\[
e_{i+1}
\]

再定位：

\[
B_{i+1}
\]

重复流程。

因此：

\[
S_i
\rightarrow
B_i
\rightarrow
LocalRepair
\rightarrow
PrefixCompile
\rightarrow
S_{i+1}
\]

不断推进。

---

# 17. C0 Serial Repair 终止条件

### A. 完整文档 compile success

```text
compile_success = true
```

---

### B. 最大 block repair rounds

建议 pilot：

```text
max_repair_rounds = 20
```

正式实验前根据 pilot 冻结。

---

### C. Repair loop

连续多轮：

- 同一 block；
- 同一 prior；
- 没有有效进展；

例如 3 次后终止：

```text
repair_loop = true
```

---

### D. 无法可靠定位 Repair Block

标记：

```text
BLOCK_PARSE_FAILURE
```

停止当前自动 trajectory 或进入人工审核。

---

### E. Prefix 无法独立验证

标记：

```text
NON_SELF_CONTAINED
```

该 error 记录，但不进入标准 block-local repair 主分析。

---

# 18. Error Taxonomy

每个 error 至少保存：

```text
LATEX_PRIOR
MARKDOWN_PRIOR

TYPST_NATIVE_SYNTAX
API_OR_FUNCTION
MATH
MATRIX
HEADING
LIST
LABEL_REFERENCE
NUMBERING
STRUCTURE
SEMANTIC
OTHER
UNKNOWN
```

另存：

```text
is_prior_candidate
prior_family
procedure_family
```

例如：

```latex
\frac{a}{b}
```

可记录：

```text
error_category = MATH
procedure_family = FRACTION
prior_family = LATEX
is_prior_candidate = true
```

而：

```typst
frac(a)
```

是错误的 target procedure：

```text
is_prior_candidate = false
```

---

# 19. Error Origin

新的 compiler error 可能是：

```text
PREEXISTING_HIDDEN
REPAIR_INDUCED
UNCERTAIN
```

由于新版强制：

\[
\text{block 外源码完全不变}
\]

origin 判断变得更简单。

如果下一 error 位于之前未修改的 downstream suffix：

```text
PREEXISTING_HIDDEN
```

如果位于刚修改的 Repair Block：

```text
REPAIR_INDUCED
```

否则：

```text
UNCERTAIN
```

---

# 20. Candidate PPL 筛选

只有：

```text
is_prior_candidate = true
```

的 C0 Error Event 进入 C1。

典型包括：

- LaTeX procedure in Typst；
- Markdown procedure in Typst；
- 其他具有明确 competing procedural origin 的错误。

普通 Typst typo 仍保存，可作为 ordinary-error baseline，但不进入 PPL 主链。

---

# 21. C1：Atomic Capability Verification

C1 回答：

> 模型是真的不会这个 procedure，还是只在真实环境中调用错？

对于每一个 PPL candidate 提取：

```text
procedure_family
semantic_target
```

然后生成简单 atomic task。

例如 C0：

```latex
\frac{a}{b}
```

C1：

> 创建一个最小 Typst 文档，其中正确表示分数 a/b。只输出源码。

禁止提供：

- 正确 Typst syntax；
- syntax guide；
- LaTeX→Typst mapping；
- few-shot example。

C1 测的是模型已有能力。

---

# 22. C1 验证

优先使用：

\[
compiler + target\ semantic\ checker
\]

每个 capability test：

\[
3\ independent\ runs
\]

定义：

\[
C1Capable=1
\iff
\ge2/3\text{ 正确}
\]

同时保存：

\[
C1Strict=1
\iff
3/3
\]

只有：

\[
C1Capable=1
\]

的 candidate error 进入 C2。

---

# 23. C2：Local Block PPL Verification

C2 是整个实验最严格的 PPL 验证。

对于 C1 通过的 error event，重新创建独立 branch。

提供：

1. 原始真实任务；
2. **该 error 首次出现时的完整原始 source snapshot**；
3. 原始真实 compiler diagnostic；
4. 与 C0 完全相同的 Repair Block boundary。

不得使用已经修复过的版本。

---

# 24. C2 Prompt

统一：

> The following source was produced for the original Typst task.
>
> The Typst compiler reports an error inside the marked repair block.
>
> Fix only this repair block.
>
> You may make any necessary changes inside the block, but do not alter any source code outside it.
>
> Preserve the intended semantics.
>
> Return the complete corrected Typst source only.

附：

```text
[Original Task]

...

[Current Source]

...

[Repair Block]

...

[Compiler Error]

...
```

禁止：

```text
This is a LaTeX error.
Do not use LaTeX.
Use frac(...).
```

否则会泄漏目标 procedure。

---

# 25. C2 独立重复

每个 event：

\[
3\ independent\ runs
\]

三次必须从完全相同：

```text
original task
original erroneous source
original repair block
original compiler diagnostic
model configuration
```

开始。

不得：

```text
run1 result → run2
```

---

# 26. C2 第一层判定：Protocol Compliance

首先判断 block 外源码：

\[
P_{before}=P_{after}
\]

\[
Q_{before}=Q_{after}
\]

如果不满足：

```text
PROTOCOL_VIOLATION
```

该 run 不进入标准 Strict-PPL numerator 或 denominator。

单独报告 protocol violation rate。

---

# 27. C2 第二层判定：Block-Prefix Compilation

对于 protocol-compliant run：

构造：

\[
Prefix_{after}
\]

即：

> 文档开头 → 修复后 Repair Block 结束。

如果：

\[
Compile(Prefix_{after})=Success
\]

则：

```text
FIXED
```

并：

\[
PPL=0
\]

---

# 28. 如果 Prefix Compile 仍失败：判断失败类型

不能定义：

\[
CompileFail\Rightarrow PPL
\]

必须检测 competing prior 是否仍存在。

---

## 28.1 SAME_PRIOR_PERSIST

修复后的 block 中仍存在与原事件相同的 competing procedure。

例如原：

```latex
\frac{a}{b}
```

修后仍使用 LaTeX fraction procedure。

定义：

\[
\boxed{StrictPPL=1}
\]

---

## 28.2 OTHER_REPAIR_FAIL

模型已经放弃旧 prior，但新的 target-side repair 仍错误。

例如：

```latex
\frac{a}{b}
```

被改为：

```typst
frac(a)
```

说明：

\[
\pi_{old}
\]

已经被成功 override。

只是 target procedure 执行不完整。

因此：

```text
PPL = 0
repair_success = 0
```

---

## 28.3 NO_TARGET_EDIT

Repair Block 完全没有发生有效变化，或者没有修改与当前错误相关的部分。

标记：

```text
NO_TARGET_EDIT
```

主要解释为：

- attention failure；
- localization failure；
- instruction-following failure。

不纳入 Strict PPL numerator。

---

## 28.4 SAME_PRIOR_RECURRED

如果原来的 prior occurrence 被修复，但模型在同一个 Repair Block 的其他新生成部分重新写出相同 prior family：

```text
SAME_PRIOR_RECURRED
```

属于非常强的 PPL evidence。

可与：

```text
SAME_PRIOR_PERSIST
```

共同计入 Strict PPL。

---

# 29. Strict PPL 定义

对于 protocol-compliant、prefix-verifiable 的 C2 run：

\[
StrictPPL=1
\]

当且仅当：

\[
C1Capable=1
\]

且：

\[
Outcome\in
\{
SAME\_PRIOR\_PERSIST,
SAME\_PRIOR\_RECURRENT
\}
\]

明确：

\[
\boxed{
OTHER\_REPAIR\_FAIL\neq PPL
}
\]

\[
\boxed{
NO\_TARGET\_EDIT\neq StrictPPL
}
\]

\[
\boxed{
PROTOCOL\_VIOLATION\neq valid\ C2\ trial
}
\]

---

# 30. Event-level PPL Score

每个 event 有三个有效独立 run：

\[
PPLScore(e)
=
\frac{
\#SamePriorPersist+\#SamePriorRecurred
}{
\#ValidC2Runs
}
\]

若三个均有效，则：

\[
PPLScore\in
\left\{
0,\frac13,\frac23,1
\right\}
\]

可定义 descriptive binary：

\[
PPLPositive=1
\iff
PPLScore\ge\frac23
\]

但统计分析优先保留原始 score。

---

# 31. Prior Detector

为明显 competing procedures 实现 detector。

例如 LaTeX：

```regex
\\frac\s*\{
\\sqrt\s*\{
\\begin\s*\{
\\section\s*\{
\\textbf\s*\{
\\label\s*\{
\\ref\s*\{
```

Markdown 根据 family 编写对应 detector。

Detector 只用于：

```text
candidate generation
```

不能直接决定最终 Strict-PPL label。

需要确认命中：

- 位于可执行 source；
- 位于 Repair Block；
- 不是 raw/code block；
- 不是 comment；
- 不是用户要求显示的 literal source。

---

# 32. 自动化数据结构

每个 Error Event：

```json
{
  "event_id": "",
  "task_id": "",

  "model": "",
  "model_version": "",
  "configuration": "",
  "reasoning_mode": "",

  "typst_version": "0.12.0",

  "original_prompt": "",
  "source_before": "",
  "compiler_error": "",

  "error_line": null,
  "error_column": null,

  "error_category": "",
  "procedure_family": "",
  "prior_family": "",
  "is_prior_candidate": false,

  "repair_round": 0,
  "error_origin": "",

  "block_type": "",
  "block_start_offset": null,
  "block_end_offset": null,
  "block_start_line": null,
  "block_end_line": null,
  "block_text_before": "",

  "prefix_verifiable": true,
  "prefix_verification_reason": "",

  "c0_repair_source": "",
  "block_text_after": "",

  "prefix_unchanged": true,
  "suffix_unchanged": true,
  "protocol_violation": false,

  "prefix_compile_success": false,
  "prefix_compiler_stdout": "",
  "prefix_compiler_stderr": "",

  "c1_runs": [],
  "c1_pass_count": 0,
  "c1_capable": false,
  "c1_strict_capable": false,

  "c2_runs": []
}
```

---

# 33. C2 Run 结构

```json
{
  "run_id": 1,

  "input_task": "",
  "input_source": "",
  "input_block": "",
  "input_compiler_error": "",

  "raw_response": "",
  "repaired_source": "",
  "repaired_block": "",

  "prefix_unchanged": true,
  "suffix_unchanged": true,
  "protocol_violation": false,

  "prefix_verifiable": true,
  "prefix_compile_success": false,

  "same_prior_present": false,
  "same_prior_recurred": false,
  "target_region_modified": false,

  "outcome": "FIXED",
  "strict_ppl": false
}
```

---

# 34. 原始数据不可覆盖

必须永久保存：

```text
raw response
full source before repair
full source after repair
repair block before
repair block after
truncated prefix source
compiler stdout/stderr
outside-block diff
classification result
human override
```

后续 detector/checker 升级只能重新分析原始数据。

不得覆盖原轨迹。

---

# 35. 主指标

## C0 Prior Candidate Rate

\[
PCR=
\frac{
\#PriorCandidateErrors
}{
\#AllErrorEvents
}
\]

同时按：

- task；
- model；
- procedure family；

报告。

---

## C1 Capability Rate

\[
CR=
\frac{
\#C1Capable
}{
\#PriorCandidateErrors
}
\]

回答：

> 自然出现的 prior-like errors 中，有多少发生在模型本来会的 procedure 上？

---

## C2 Strict PPL Rate

\[
\boxed{
SPR=
\frac{
\#SamePriorPersist+\#SamePriorRecurred
}{
\#ValidC2Runs
}
}
\]

其中 denominator 仅包含：

```text
C1 capable
prefix verifiable
protocol compliant
```

的 runs。

---

## Ordinary Repair Failure Rate

\[
ORF=
P(OTHER\_REPAIR\_FAIL)
\]

必须和 PPL 分开。

---

## No-target-edit Rate

\[
NER=
P(NO\_TARGET\_EDIT)
\]

---

## Protocol Violation Rate

\[
PVR=
P(PROTOCOL\_VIOLATION)
\]

它可以反映 block-local repair instruction 本身对不同模型是否足够稳定。

---

# 36. C0 的额外统计

记录：

\[
ErrorDepth(t)
=
\#CompilerRevealedErrors
\]

以及：

\[
PriorDepth(t)
=
\#PriorCandidateEvents
\]

论文中必须称：

> compiler-revealed error sequence

不能把它解释成 compiler 在初始状态一次性发现的完整错误集合。

---

# 37. Repair-induced Error

因为所有修改被限制在一个 block 内，所以 repair-induced errors 可以更可靠地识别。

若新的错误首次出现在刚修改 block：

```text
REPAIR_INDUCED
```

可以额外研究：

\[
P(
NewPriorError
\mid
BlockRepair
)
\]

但不属于 Strict PPL 主定义。

---

# 38. Human Adjudication

大部分流程应自动化。

人工只处理：

```text
BLOCK_PARSE_FAILURE
NON_SELF_CONTAINED ambiguity
prior detector ambiguity
SAME_PRIOR vs OTHER_REPAIR_FAIL ambiguity
```

人工审核者尽量只看到：

```text
original block
repaired block
compiler error
procedure family
prefix compiler result
```

减少主观信息泄漏。

---

# 39. 实验禁止事项

### 禁止 1

```text
compile fail => PPL
```

错误。

---

### 禁止 2

C0 出现 LaTeX/Markdown 就直接叫 Strict PPL。

必须经过 C1+C2。

---

### 禁止 3

C1 提供正确 Typst syntax。

---

### 禁止 4

C2 告诉模型：

> 这是 LaTeX error。

---

### 禁止 5

C2 各 run 串联。

必须独立从原始错误 snapshot 开始。

---

### 禁止 6

模型修改 Repair Block 外代码却仍算合法 repair。

必须标：

```text
PROTOCOL_VIOLATION
```

---

### 禁止 7

把 `OTHER_REPAIR_FAIL` 算作 PPL。

---

### 禁止 8

把 `NO_TARGET_EDIT` 自动算成 PPL。

---

### 禁止 9

为了让 prefix 编译成功，在正式实验中临时人工修改被截断源码。

---

### 禁止 10

对于 `NON_SELF_CONTAINED` event 强行使用 prefix compile 判负。

---

### 禁止 11

根据正式结果重新修改 Strict-PPL 判定定义。

---

# 40. 开发阶段

## Phase 1：Block Parser + Compiler Harness

首先实现：

```text
Typst compile
compiler diagnostic parser
Repair Block locator
prefix generator
prefix compiler
```

这是新版实验最核心的基础设施。

先用人工构造样本测试：

- equation；
- matrix；
- heading；
- list；
- function；
- content/code block。

---

## Phase 2：Block-local Repair Harness

实现：

```text
LLM repair
block extraction
outside-block equality check
protocol violation detection
full-source reconstruction
```

确保：

\[
P,Q
\]

不会被模型修改。

---

## Phase 3：Serial C0

实现：

```text
Generate
→ Compile
→ Locate Block
→ Repair
→ Prefix Compile
→ Full Compile
→ Next Event
```

---

## Phase 4：Error Registry + Prior Detector

实现：

```text
error taxonomy
prior family
procedure family
origin
prior detector
```

---

## Phase 5：C1

实现：

```text
atomic capability task
3 runs
compiler
semantic checker
2/3 capability gate
```

---

## Phase 6：C2

实现：

```text
original snapshot recovery
original Repair Block recovery
3 independent repairs
outside-block validation
prefix compilation
outcome classification
PPLScore
```

---

# 41. Pilot

正式实验前选择：

\[
10\text{–}20
\]

个真实任务跑完整：

\[
C0\rightarrow C1\rightarrow C2
\]

Pilot 重点检查：

1. compiler error 能否稳定映射到 Repair Block；
2. block boundary 是否一致；
3. prefix compilation 是否适用于大多数 event；
4. `NON_SELF_CONTAINED` 比例；
5. 模型能否稳定遵守 block-only edit；
6. outside-block equality checker 是否可靠；
7. C1 checker 是否稳定；
8. C2 outcome 自动分类是否稳定。

---

# 42. Freeze 标准

至少满足：

```text
Repair Block 自动定位率足够高
prefix_verifiable 比例足够高
outside-block checker 稳定
prior detector 经人工验证
C1 checker 稳定
C2 outcome 分类稳定
UNKNOWN / NON_SELF_CONTAINED 比例可接受
```

然后冻结：

```text
experiment_protocol_version
git_commit
prompt_hash
block_parser_version
checker_version
model_config_hash
Typst_version
```

正式实验后不得无记录修改。

---

# 43. 最终论文逻辑

### C0

\[
\boxed{
\text{Models naturally execute competing procedures in realistic Typst tasks.}
}
\]

---

### C1

\[
\boxed{
\text{Many such failures occur despite demonstrated capability on the corresponding Typst procedure.}
}
\]

---

### C2

\[
\boxed{
\text{Even when the problem is reduced to one local syntactic block and the true compiler error is supplied, some models continue to execute the same competing procedure.}
}
\]

因此逐步排除：

```text
模型根本不会
↓
整篇任务太难
↓
不知道错误在哪里
↓
必须同时修很多问题
↓
后续错误干扰 compiler 判断
↓
普通 target-side repair failure
```

如果这些因素被控制后仍存在：

\[
\pi_{old}
\]

持续执行，则构成：

\[
\boxed{\textbf{Strict Procedural Prior Lock-in}}
\]

---

# 44. 实验最高原则

整个实现始终遵守：

\[
\boxed{
\text{错误不是 PPL；
旧 procedure 的持续执行才是 PPL。}
}
\]

以及：

\[
\boxed{
\text{修复失败不是 PPL；
模型会正确 procedure，却在局部 block 修复中继续执行 competing procedure，才是 PPL。}
}
\]

新版再增加第三条：

\[
\boxed{
\text{局部修复是否成功，优先由相同 document prefix 的实际编译结果决定。}
}
\]

这样 C0、C1、C2 的实验单位、修复单位和验证单位形成统一闭环：

\[
\boxed{
Error
\rightarrow
RepairBlock
\rightarrow
PrefixCompile
\rightarrow
Capability
\rightarrow
LocalPPLTest
}
\]