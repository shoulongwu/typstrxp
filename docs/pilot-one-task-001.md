# 单题试点 001

日期：2026-09-22。任务：`C0_01`。被测模型：`qwen3.8-flash`。性质：协议 v0.5 的一题一次开发试点，不进入正式统计，未运行 C1/C2，因而不产生 PPL 判定。

## Generation

Qwen 返回完整正文，HTTP 200，`finish_reason=stop`，耗时 82.08 秒。输入、输出和总 token 分别为 583、5,877、6,460，其中 reasoning token 为 299；正文 13,856 个 Unicode 字符。

Typst 0.12.0 编译失败。首个事件冻结为文件开头的完整 `#set page(...)`，原始 code-point 范围 `[0, 321)`。同一 target block 内有两条真实诊断：footer `context` 代码模式中的 `#set` 与 `#align` 使用了非法 `#`。

## DSH repair

无工具 DSH SDK session 使用 `step-5-preview`、low reasoning。第 1 轮只删除 footer context 内两个非法 code-mode `#`：

```diff
-  #set text(size: 8pt)
-  #align(center)[#counter(page).display("1")]
+  set text(size: 8pt)
+  align(center)[#counter(page).display("1")]
```

候选满足 immutable-suffix locality，editable prefix 用 Typst 0.12.0 编译成功，`tool_calls=[]`。完整文件随后在未修改的第 25 行暴露下一组错误；这些诊断没有反馈给当前 repair session。

## 独立审核

最初的完整文档审核包和默认推理配置两次未产生结构化结果，均保留为 `PENDING_REVIEW`，没有伪装成通过。审核器随后修正为 low reasoning、禁用模型工具，并使用当前事件所需的完整 editable prefix、diff 与编译证据。

最终独立结构化审核为 `PASS`，置信度 0.94，`requires_human_review=false`。审核确认修改命中因果 target、保持 A4/header/footer 语义，完整编译的后续错误位于冻结后文。

本试点证明“一次 subject generation → 冻结首事件 → 无工具 DSH repair → prefix compiler gate → 独立语义审核 → 揭示下一错误”的最小链路可运行。当前只完成首事件，不继续修复第 25 行后续事件；正式 C0 计数、C1 和 C2 仍未运行。
