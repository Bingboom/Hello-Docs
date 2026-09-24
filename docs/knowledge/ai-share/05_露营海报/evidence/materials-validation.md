# 素材与稿件验收记录

> 历史阶段记录：以下内容记录最初保留原六章时的验收，不代表当前稿件结构或最新钉钉状态。当前稿件已按“鹈鹕作品—海报工作—延伸场景”重排；三张 PNG 和三份 PDF 已完成一次上传，钉钉持续自动同步仍未接通。最新稿件与链接以重新运行 `validate_materials.py` 的结果为准。

- 主稿按原始六章和原有三个小标题扩充示例，原标题及顺序保持一致；新教程只追加在末尾附录。
- `python3 -m unittest -v test_demo`：14 项通过。
- `python3 demo.py build`：现有输入无变化，跳过重建；三份 PDF 哈希仍符合 acceptance.json。
- `python3 -m ruff check demo.py test_demo.py verify_acceptance.py render_materials.py package_materials.py validate_materials.py`：通过。
- `python3 validate_materials.py`：Markdown 与 HTML 主体严格一致；原始标题结构检查通过；5 个页面、69 个本地公开素材链接通过。
- 仓库 `python3 tools/check_doc_link_integrity.py`：227 个文档、2037 个链接，0 断链。该检查的范围与案例局部检查不同，不以它代替案例检查。
- 浏览器验证：原六章与附录目录实际可跳转；主稿截图及素材入口四张图片均加载；最终附录 390 px 宽度下页面 scrollWidth = clientWidth = 390。临时视口已恢复。
- 打印检查边界：已保留原打印样式并检查代码；内置浏览器点击打印没有提供可检查的系统打印预览。本次未核验整篇分享稿的实际打印分页，不将此项标为通过。三张海报 PDF 的单页 A5 检查与视觉验收已完成。
- `git diff --check`：通过；全部修改仅位于 docs/knowledge 内。未提交、未合入、未发布 Read the Docs。
- 钉钉：三张 PNG 在对应记录的海报预览字段回读到非空附件 resourceId，名称、大小和远端 SHA-256 与本地冻结 PNG 一致。PDF 和钉钉自动更新未接入。工作区地址和原始回执仅本地私有保存。
- ZIP 使用公开文件筛选规则排除运行目录、旧原型截图、钉钉私有绑定；完整性检查通过。
