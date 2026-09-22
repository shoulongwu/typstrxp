# C0 repair 接口

状态：`interface-only`。当前没有启用的自动 C0 repair backend；本文定义未来手工、脚本或模型适配器必须满足的与 provider 无关接口。DSH 仅保留为已禁用的实验适配器，不是 v0.6 的 C0 repair 实现。

## 1. 输入 packet

Schema：[`schemas/c0-repair-packet.schema.json`](../schemas/c0-repair-packet.schema.json)。

必填字段：

- `event_id`：冻结事件 ID。
- `original_task`：原始生成任务。
- `source_before`：事件冻结时的完整 Typst 源码。
- `target_start` / `target_end`：0-based Unicode code-point 半开区间。
- `target_block`：必须等于 `source_before[target_start:target_end]`。
- `selected_diagnostic`：当前 primary compiler diagnostic。
- `target_diagnostics`：只包含 span 位于同一 target block 内的共位诊断，并且必须包含 primary diagnostic。

`dependency_spans` 可选，用于记录已冻结的前文依赖及证据。packet 不得包含被测模型身份、C1/C2 结果、密钥、统计结论或后续事件的诊断。

Schema 只校验结构。坐标与文本一致性、primary diagnostic 成员关系和 diagnostic span 归属必须由运行器另行校验。

## 2. 响应

Schema：[`schemas/c0-repair-response.schema.json`](../schemas/c0-repair-response.schema.json)。一次调用只能选择一种响应模式。

`prefix_after` 模式返回从文档开头到修复后 target 结束位置的完整可编辑前缀：

```json
{"prefix_after":"#set page(...)\n..."}
```

`edits` 模式返回不重叠稀疏编辑：

```json
{
  "edits": [
    {"start": 42, "end": 45, "replacement": "replacement text"}
  ]
}
```

edits 使用冻结 `source_before` 的 Unicode code-point 坐标，满足 `0 <= start < end <= target_end`，不重叠，最多 32 项。运行器按坐标逆序应用 edits，防止早先编辑使后续坐标偏移。两种响应都只能修改 `[0,target_end)`；稀疏模式不缩小“当前 target 及全部前文”的可编辑范围。

## 3. 确定性验收顺序

1. 验证 packet 结构、冻结坐标、target 文本和 diagnostic 归属。
2. 从响应组装 candidate prefix，再拼回原始不可变 suffix `source_before[target_end:]`。
3. locality 门确认该 suffix 逐字符不变。
4. 用固定 Typst 0.12.0 编译 candidate prefix。失败时只能将这个 prefix 的原始 compiler feedback 交给同一 repair attempt。
5. prefix 成功后才编译完整 candidate。后文首次显现的诊断属于新事件，不能回传到当前 attempt。
6. 独立语义审核检查目标和受影响前文。编译成功的候选仍是 `PENDING_REVIEW`，不能自动晋升。

多轮只在已收到可解析 candidate，且 prefix compiler 产生新反馈时继续。纯运输错误、空正文或 `OUTPUT_EXHAUSTED` 不伪装成一次 repair 轮，也不进入 C0 错误计数。

## 4. 状态语义

| 状态 | 含义 | 是否有 repair candidate |
| --- | --- | --- |
| `INVALID_PACKET` | 冻结输入不满足接口 | 否 |
| `PROVIDER_RUNTIME_FAILURE` | 运输、认证、进程或超时失败 | 否 |
| `INVALID_RESPONSE` | 响应不符合 schema | 否 |
| `OUTPUT_EXHAUSTED` | 用尽输出预算仍无正文 | 否 |
| `PROTOCOL_VIOLATION` | 越界访问、禁用工具或泄漏信息 | 可能，但不可接受 |
| `LOCALITY_VIOLATION` | 修改了冻结 suffix | 是，但不可接受 |
| `PREFIX_COMPILE_FAIL` | 有效候选未通过 prefix compiler | 是 |
| `NO_PROGRESS` | 连续候选与诊断签名相同 | 是 |
| `ROUND_LIMIT` | 用尽预注册的反馈轮数 | 可能 |
| `CANDIDATE_PENDING_REVIEW` | locality 和 prefix compiler 通过 | 是 |
| `FIXED` | 独立语义审核通过，可晋升为下一快照 | 是 |

## 5. 适配器要求

新 backend 在启用前必须：

- 声明精确 provider/model/version/推理和 token 参数，不依赖隐式全局默认值。
- 持久化原始请求、原始输出、用量、耗时、停止原因和所有 compiler artifacts。
- 不读取工作区、网络、C1/C2 结果或冻结 packet 之外的实验数据。
- 通过至少包含 Unicode 坐标、变长编辑、重叠 edits 拒绝、suffix 不变和多轮隔离的回归测试。
- 完成一个不进入正式统计的留出冒烟测试，经审阅后再在新协议版本中启用。

`scripts/repair_with_dsh.py` 保留用于复现历史开发记录和测试接口。它不得用于 v0.6 正式 C0 trajectory，除非未来协议另行冻结该 backend。
