# v0.6 修订：停用 DSH repair，保留通用接口

日期：2026-09-22。

单题开发试点表明，DSH + step-5-preview 可在前四个目标事件上提出通过 prefix compiler 的修复，但在最后一个 13,894 code-point 前缀上出现不可接受的稳定性问题：完整前缀模式多次超时；稀疏 edits 模式在修正相互冲突的提示后，仍把 4,096 和 16,384 tokens 全部用于内部推理而无正文。这些 run 没有 repair candidate，不能记为编译修复失败，也不能靠重复请求改善结果。

从 v0.6 起，DSH 不再是启用的 C0 repair backend。`scripts/repair_with_dsh.py` 保留为历史、可选、禁用状态的适配器，用于复现已有冒烟记录和保持测试覆盖。配置将 C0 oracle 标为 `interface_only_no_active_backend`；在新 backend 被审阅、版本化和冻结之前，完整串行 C0 轨迹不可运行。

修复接口与 provider 解耦。新增 packet 和 response JSON Schema，固定 Unicode code-point 坐标、`prefix_after` / sparse `edits` 响应、suffix 不变、prefix compiler-first 和独立语义晋升顺序。运输失败、空响应和输出耗尽与真正的 candidate compile failure 分开记录。

DSH 仍可作为错误事件初筛和独立结构化审阅器。它只产生建议，不执行 repair，不直接写入错误计数或 PPL 标签。错误统计继续以冻结事件、Typst 编译证据和人工复核为准。
