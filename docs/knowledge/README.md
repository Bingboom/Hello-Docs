# 知识资料

这里由 Hello-Docs 独立维护，存放分享稿、配图、示例及参考资料。

- `ai-share/index.html`：AI 使用知识分享主稿。
- `ai-share/practical.html`：从工作需求切入的独立版本；主稿保持不变，鹈鹕动画放在文末彩蛋。
- `ai-share/05_露营海报/`：当前分享主线；两张 CSV、三种共享样式的 LaTeX 海报、本地自动更新程序和真实操作素材。
- `ai-share/配图/`：当前页面使用的 Q 版配图（`*-q版.png`）与保留的原图。
- `ai-share/阅读样式.css`：主稿、参考阅读页及学生情况卡共用的样式；提示框采用浅灰底、细灰线，链接保留下划线。
- `ai-share/04_参考资料/`：按需阅读的参考页。
- 其余例子目录：可独立使用的练习文件。

整个文件夹一起维护，保留相对路径；修改后检查图片和页面跳转。
发布构建将 `ai-share/` 复制到网站同名路径，知识库入口为 `/workspace/`。
原有说明书仍由 `docs/publish/` 管理。

## 直接在 Hello-Docs 修改

`docs/knowledge/**` 是 Hello-Docs 业务内容的直接编辑区，也是单向工程镜像规则的
明确例外。分享内容不需要复制到 auto-manual，也不需要等待工程仓库先同步；
auto-manual 的同步会完整保留这里已经合入 `Hello-Docs/main` 的内容。

修改流程：

1. 从最新的 `Hello-Docs/main` 建立 `docs/knowledge-<主题>` 内容分支。
2. 主稿文字改动先修改 `ai-share/分享稿.md`，工作实践版修改
   `ai-share/实用版分享稿.md`；运行素材渲染脚本生成对应的 `index.html` 或
   `practical.html`。样式、图片和示例则修改同目录对应文件。
3. 只提交 `docs/knowledge/**` 下的文件。本次内容 PR 不夹带模板、构建代码、
   `docs/publish/**` 或产品说明书评审文件。
4. 本地打开 `ai-share/index.html`，检查目录跳转、参考链接、图片、窄屏
   布局和打印效果。
5. 向 `Hello-Docs/main` 提交内容 PR。合入后，Read the Docs 从该 main commit
   重新构建 `/ai-share/`。

更细的 Agent 操作边界和验收项见同目录 [`AGENTS.md`](AGENTS.md)。

分享内容通过 Hello-Docs 的内容 PR 更新；页面模板和构建代码通过
auto-manual 工程 PR 更新。不要把分享内容复制回工程仓库。
