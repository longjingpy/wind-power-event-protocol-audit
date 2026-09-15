# Review action register v16

更新：2026-09-15。本文档把当前审稿意见转换为可验收的工作项。`DONE` 只表示已有当前文件和命令输出直接证明；`RUNNING` 表示实验进程仍在运行；`BLOCKED` 表示缺少外部证据或用户参与，不能用已有结果替代。

| ID | 审稿要求 | 状态 | 验收证据 / 下一动作 |
|---|---|---|---|
| R1 | 经济实验覆盖 10%/2 h、容量和价格条件，并给出事件加权适用条件 | RUNNING | `outputs/storage_policy_v15/capacity_price_surface.csv`、`conditional_advantage.csv` 已生成；补充表 S23/S26 已接入。当前网格中 14/360 单元均值有利，固定 10%/2 h 仅 Yandun TCN 高尾部惩罚情景有利。下一动作：补充真实结算/偏差价格后重算；当前不能称真实利润。 |
| R2 | 简单规则与 TimesNet、KAN-AD、TCN-AE、Transformer-AE 公平比较、超参和计算成本 | DONE（受控合成任务） | 3 组 hidden/latent/lr 配置已完成；验证集选择、测试集冻结。KAN-AD held-out F1=0.795，mean rule=0.741，TimesNet=0.631；计算成本与参数量见 S27–S28。该结果是合成定位证据，真实 SCADA 迁移仍需独立实验。 |
| R3 | 报告匹配覆盖率及匹配/未匹配事件组成 | DONE（主分析） | S14/S16 含 weighted NMI/ARI、left/right coverage 和 IoU 敏感性；正文唯一范围句保留一次。下一动作：若需要更强机制证据，补充未匹配事件的幅度、持续时间、方向和功率分布对照。 |
| R4 | 天气结果使用 association / exploratory 语言并修正 Fig.1 | DONE | 正文、Fig.1、Fig.6 和 S19 均使用 observational association / exploratory 表述；未将 logistic 风险差写作因果效应。若要因果结论，需独立天气观测、处理前混杂和可交换性证据。 |
| R5 | 多评审者标注、平衡抽样、kappa/alpha 和公开界面 | BLOCKED（等待真实独立响应） | v15 网页和离线包已公开，200 窗口四站点平衡抽样、JSON 合并与统计代码已测试。当前没有第二位及以上真实评审者导出文件，因此没有经验 kappa/alpha。下一动作：收集独立响应后运行 `script/merge_multirater_v15.py`；在此之前不写多评审者一致性结论。 |
| R6 | 数据许可、去标识化、代码/模型/中间结果和环境复现 | PARTIAL / BLOCKED | 用户已授权全部研究数据公开，`DATA_LICENSE.md` 已记录 MIT 计划；公开 release v0.2.0 已有数据资产和脚本。当前仍需逐项核对提供方原始条款、同 tag 代码、模型权重、中间目录、容器或锁文件。下一动作：生成许可矩阵和可执行环境锁定；未完成前不称“完全可复现”。 |
| R7 | 明确创新性及 Applied Energy 运行影响 | DONE（文本层） | 摘要与结论已将 protocol-aware measurement layer、catalogue reach、representation 和 storage objective 的联结写成正向贡献；经济条件化结论已进入正文。下一动作：用 HPO 和真实价格结果更新定量句。 |
| R8 | Fig.5/8、DOI、拼写、表注、成本单位、权重依据、时间边界 | PARTIAL | Fig.5/8 已重新导出为可读矢量 PDF；43 引用/38 篇论文、S1–S27 结构检查通过；分页和日志检查通过。下一动作：完成新 HPO 后再做终稿全文扫；容器与模型发布状态仍未关闭。 |

## 当前明确阻塞项

1. **R5：真实独立标注响应。** 这是数据收集门槛，不通过时只能报告“接口和统计方法已准备”，不能报告多评审者一致性。
2. **R6：真实价格与可执行复现环境。** 当前经济表使用声明的价格情景，尚未使用场站结算或偏差价格；模型权重、完整中间产物和容器锁定也未全部归档。

## 本轮关闭标准

- HPO 所有候选均完成，验证集选择记录可追溯，独立测试汇总已写入 S28；
- 经济结果同时报告普通价格和高尾部惩罚条件，并明确适用域；
- 全文每个主张标注 measurement、association 或 causal 证据等级；
- R5 收到真实多评审者文件后，kappa/alpha、缺失率和类别分布可复算；
- R6 的许可、环境、权重、事件目录和结果清单均有当前文件证据；
- 最终 PDF、图件和表格重新编译并通过文本、结构和视觉检查。
