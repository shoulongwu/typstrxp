# 单题试点 001

日期：2026-09-22。任务：`C0_01`。被测模型：`qwen3.8-flash`。性质：协议开发试点，不进入正式统计。本试点未运行 C1/C2，不产生 PPL 判定。

## Generation 与初始编译

Qwen 返回完整正文，HTTP 200，`finish_reason=stop`，耗时 82.08 秒。输入、输出和总 token 分别为 583、5,877、6,460，其中 reasoning token 为 299；正文 13,856 个 Unicode code point。

Typst 0.12.0 初次编译失败，共返回 15 条 raw diagnostics。根据共同 target block 和因果关系，开发盘点将其合并为 5 个候选错误事件：

| 事件 | target | raw diagnostics | 历史 DSH candidate | 独立审核 |
| --- | --- | ---: | --- | --- |
| E01 | page header/footer setup | 2 | 1 轮 prefix 通过 | PASS，0.94 |
| E02 | `def-block` definition | 4 | 1 轮 prefix 通过 | PASS，0.95 |
| E03 | `thm-block` definition | 4 | 第 2 轮 prefix 通过 | 有争议；确认 target 诊断消失，但要求人工复核 |
| E04 | `rem-block` definition | 2 | 1 轮 prefix 通过 | PENDING_REVIEW，未取得有效结构输出 |
| E05 | Practice Problems callout | 3 | 无候选 | 不适用 |

15 条 diagnostic 不等于 15 个独立错误。当前可复核的开发口径是 5 个候选因果事件，且由于 E03/E04 的语义晋升尚未全部完成，这个数不得当作已冻结的正式 C0 统计。

## 前四个事件

E01 删除 footer `context` 代码模式中两个非法 `#`，保留居中页码。E02–E04 分别修正三个 callout 定义的 content/code 边界。四个 candidate 均通过 immutable-suffix locality 和 Typst 0.12.0 prefix compiler，且无 tool call。各次完整编译只在后续未修改区域继续报错。

E01 和 E02 获得独立结构化 PASS。E03 的独立 reviewer 确认当前 target diagnostics 已消失，同时因完整文档仍有后续错误而要求人工复核；这与“当前事件只看 prefix 和冻结后文”的串行规则存在解读争议。E04 审核未取得合法 JSON，保持 `PENDING_REVIEW`。因此“前四个 prefix compiler 通过”不能改写为“前四个正式 FIXED”。

## E05 与 DSH repair 停用

E05 是文档最后的 Practice Problems block，冻结区间为 `[12699,13894)`，包含两条 `invalid number suffix: b61a8` 和一条 `unclosed delimiter` diagnostic。它的 editable prefix 即几乎整份文档。

完整 prefix 返回模式多次超时。稀疏 `edits` 模式最初暴露了一个运行器提示冲突：同时要求返回完整 prefix 和 edits。修正该冲突并禁用全部模型工具后，Step 仍然在一轮内用尽 4,096 tokens 而无正文；放宽到 16,384 tokens 时产生约 57,000 个推理字符，仍无 repair JSON。这些运行没有 candidate，不是“候选编译失败”，也不应通过重复请求伪造多轮进展。

根据 v0.6 决定，DSH repair 停用；E05 保持未修复，轨迹在此截尾。当前完整源码仍有 E05 的 3 条 raw diagnostics，没有编译通过的最终 PDF。

## 结论边界

本试点验证了 generation、事件 packet、Unicode 坐标、suffix locality、prefix compiler 和独立 reviewer 的基础管道，也证明 DSH repair 在长前缀上不足以作为可冻结 backend。v0.6 保留 provider 无关的 [repair 接口](repair-interface.md)，但在新 backend 通过审阅前不继续串行 C0。

本试点的 C0 正式错误统计、C1 和 C2 均未完成；`strict_ppl = null`。
