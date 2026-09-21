# v0.3 修订记录

用户修正：当前错误可能源自先前定义，应允许修改当前 block 和全部前文；不同模型采用各自 API 配置；可使用 dsh + step-5-preview 自动审核。

## 编辑范围与指标

- Target Block 继续作为错误定位单元，Editable Prefix `[0,target_block_end)` 作为真正的编辑范围。
- 只冻结后文 Q，前文 P 修改不再判 PROTOCOL_VIOLATION。
- 修复后使用不变 Q 恢复新前缀，而不是用原 block_start 推算新 block。
- 仅改先前依赖是有效目标修改；“目标 block 文本未改”不再直接等同 NO_TARGET_EDIT。
- 判 SAME_PRIOR_PERSIST / RECURRED 时要求因果关联，不能把无关前文的新错误或字符串命中算为 PPL。
- FIXED 要保留目标及受影响前文语义；完整文件继续编译，记录上游改动可能引起的后文错误。
- 旧 block-only 条件保留为显式对照；新旧条件不能合并主指标。源文件末尾的目标意味着允许编辑全文，单独记录覆盖比例。

## 凭据与路由实测

读取用户本地 `apikey.config`，不打印或复制密钥至公共报告；独立环境变量可覆盖。

- Qwen：配置的新地址返回 HTTP 200，报告 model 为 qwen3.8-flash，结束原因 stop。
- GLM：星渡返回 HTTP 200，报告 model 为 glm-5.3-flash；64-token 探针触及 length，仅作为连通证据。
- DeepSeek：原星渡凭据返回 HTTP 401。用户文件明确列出 qwen 标签也支持 deepseek-v4.1-flash；在其配套接口验证得到 HTTP 200、正确 reported_model、stop，已将该显式连接设为当前路由，保留失败连接记录。
- 所有探针是基础设施检查，不纳入 C0/C1/C2 数据。网关返回的 reported_model 不能独立证明底层快照身份，仍需保存 provider/version 信息。

原始证据位于 runs/model-connectivity-001.json 和 runs/deepseek-alternative-connectivity-001.json。

## 外部 reviewer

桥接入口 scripts/review_with_dsh.py 使用 dsh headless + step-5-preview，输出结构化且带证据的建议。
不准 reviewer 用想象代替编译结果，也不把审核意见传回被测模型；建议默认不自动写入最终标签。
旧 docs/review.md 是 v0.2 历史审阅，本记录与 v0.3 协议覆盖其旧范围/统一密钥说明。

## 本轮验证状态

23 项离线测试通过，包含：前置定义修改、目标 block 不变、后文越界、Unicode 与前缀变长、文末目标、删除前缀仍须语义核验、独立凭据/地址解析，以及审核输入/输出字段校验。
另用本机 Typst 0.15.1 做开发案例：把先前 denominator 定义从字符串改为数值，目标除法表达式不改；真实前缀编译由失败变为成功。此结果只验证开发案例，不计入固定 0.12.0 的正式实验。

外部大范围协议审核第一次超时；缩小到协议关键段和两道题后，第二次进程退出但没有结构化最终回答。两次均标 PENDING_REVIEW，不视为通过，保留 runs/reviewer-step5-001 和 runs/reviewer-step5-002。还需验证小案例链路及正式数据上的审核一致率，再考虑批量自动裁决。
本轮未据不完整的外部意见修改 dataset；沿用已优化的 10 道 C0 题及 2–5 页政策。

小案例审核已完成：dsh 0.1.5-rc.1 + step-5-preview 返回有效 JSON，review_status=PASS、confidence=0.93、findings=[]。原始证据见 runs/reviewer-step5-smoke；这是连通及结构化输出验证，不证明所有自动审核结论可靠。后续默认按单个错误事件提交，不把协议和完整数据集放进同一次审核。
