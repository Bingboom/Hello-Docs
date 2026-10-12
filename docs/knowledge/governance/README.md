# 知识发现台账

`findings.json` 是欧规说明书知识问题的台账（机读 Phase 3）。每个条目写明哪些版本与参照原文不一致、
证据、各版本的发布路径，以及人工结论、修改与核验结果。字段与规则见
[知识治理方案](../../../code-as-doc/dev/machine_readable_knowledge_governance.md) §6.1。
台账不发布到网站。

## 更新方式

1. 从最新的 `Hello-Docs/main` 建 `docs/knowledge-<主题>` 分支，只改本目录。
2. 给结论时，在条目的 `decisions` 末尾追加一条（`status`、`by`、`role`、`date`，需要时加 `note`），
   并把条目的 `status` 改成同一个值；已有的决定不改写。
   - `role`：`content_owner`（内容负责人）、`certification_owner`（产品 / 认证负责人）、
     `operator`（操作者）。
   - `rejected`、`not_applicable`、`superseded` 必须在 `note` 里写理由。`not_applicable` 以及合规类
     条目（`category` 为 `compliance`）的确认或否决由认证负责人给出；修改范围与措辞由操作者批准
     （`change_approved`）。
3. 批准的措辞写入 TM-B，`changes` 里只引用记录（`tm:<记录 ID>`），不写原文。
4. 修改发布后，在 `changes` 里补上权威源 PR 与新的 `manual_variant_id`，状态改为 `applied`；
   重新观察核验到差异消失后才改为 `closed`。
5. 提交前运行 `python -m tools.manual_knowledge.findings check`，结果为 `"status": "valid"`。
   Manual Validation 的单元测试也会校验本文件。

机器只登记 `candidate` 并写核验字段；`finding_id` 登记后不变。
