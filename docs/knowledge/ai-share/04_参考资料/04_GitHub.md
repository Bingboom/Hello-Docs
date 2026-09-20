# 去 GitHub 找现成项目

### GitHub 是什么，为什么去那里找

[GitHub](https://github.com/) 是存放和分享代码项目的网站。可以把它想成一个项目展架：有人展示做好的程序，也把做法、使用说明和示例放在旁边。一个项目通常叫一个“仓库”，先把它理解成装着这些文件的文件夹就行。

比如你想批量整理文件、从资料生成文档，可能已经有人做过接近的功能。先看看别人的项目，就能知道已有的做法是什么、效果怎样，再让 Agent 帮忙试用和修改。有时不需要直接采用整个项目，看懂它怎么解决问题，也能给自己的尝试带来启发。

### 包内就有一个 Notebook 例子

GitHub 上有些项目用 Jupyter Notebook 展示做法。它像一本能动手试的笔记：一段说明、一段代码，下面就是运行结果。先看结果，再改一个条件、运行一次，就能看看变化。

这次分享包里准备了两份：

- [中文例子：整理家长反馈](../02_Notebook例子/阅读版.html)：为本次分享编写，使用虚构资料。先看“作业安排”有几条反馈，再把条件改成“阅读习惯”，看结果怎么变。
- [GitHub 原例：读取自行车计数资料](../03_GitHub原例/阅读版.html)：来自 [Pandas Cookbook](https://github.com/jvns/pandas-cookbook)，展示读取数据、选一列、画图的过程。英文原始 Notebook、配套数据和来源许可也一起放在包里。

先打开“阅读版”就能看说明、代码和已经生成的结果，不用安装软件。想修改并重新运行时，再把对应文件夹交给 Agent：

> 帮我准备运行这份 Notebook 所需的环境，先让我看到原来的结果。然后带我改一个条件，再运行一次。每次只解释当前这一步用到的知识。

阅读版展示的是保存下来的运行结果；重新执行 Python 代码，需要 Python 和 Jupyter 环境。具体准备方法见例子文件夹里的使用说明。

### 按自己要做的事去找

打开 GitHub，在搜索框输入想做的功能。比如 `batch rename`（批量改名）、`document generation`（生成文档）。搜索词可以先让 Agent 帮你想，也可以把需求直接交给能联网的 Agent：

> 我想把成绩、课堂表现和家访记录合在一起，批量生成每个学生的情况卡。帮我在 GitHub 找几个功能接近的项目，给我实际找到的链接。用简单的话说清楚：各自能做什么、有没有效果示例、在我的电脑上试用需要准备什么。

打开项目后，先看页面上的介绍、效果图或演示，再看 `README`，也就是它的使用说明。重点看它能解决什么问题、怎么使用，不用一开始就逐个读代码文件。拿不准时，把链接交给 Agent，让它结合你的需求解释。

找到接近的项目后，再决定是否下载试用。准备采用或修改其中的代码时，查看 `LICENSE` 里允许怎样使用。[GitHub 许可证说明](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)

### 把项目下载到电脑上

**建议初学者用 GitHub Desktop 操作**，下载项目、查看改动、保存版本都可以通过按钮完成，不用先记 Git 命令。Git 负责保存版本，GitHub Desktop 提供相应的按钮；GitHub 是网站，另外两个是电脑上的软件。

**先准备 Git 和 GitHub Desktop。**

**Windows：** 从 [Git 官方下载页](https://git-scm.com/install/windows)下载安装程序，按向导完成安装，再重新打开 PowerShell。

安装完成后，在 PowerShell 中输入下面的命令。显示版本号，就说明 Git 已经安装好。

```powershell
git --version
```

然后到 [GitHub 注册账号](https://github.com/signup)，验证邮箱；从 [官网下载 GitHub Desktop](https://desktop.github.com/)，安装后登录，按引导设置姓名和邮箱。[安装说明](https://docs.github.com/en/desktop/installing-and-authenticating-to-github-desktop/installing-github-desktop)

**再下载选好的项目。**

1. 在仓库页面点击 **Fork → Create fork**，得到自己账号下的一份副本，复制它的网址。
2. 打开 GitHub Desktop，选择 **File → Clone Repository → URL**，粘贴网址，选好保存位置，点击 **Clone**。
3. 用 Codex 或 Claude Code 打开下载得到的整个文件夹，把下面这段话发给 Agent。

这里的 Fork 是把副本放进自己的 GitHub 账号，Clone 是把仓库下载到电脑。也可以直接 Clone 原仓库；上面采用先 Fork 的方式，方便以后保存自己的修改。[Fork 说明](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/fork-a-repo) · [Clone 说明](https://docs.github.com/en/desktop/adding-and-cloning-repositories/cloning-and-forking-repositories-from-github-desktop)

### 让 Agent 陪着读，先把它跑起来

先请 Agent 帮忙说明项目用途，再运行它：

```text
先读一下这个项目的说明，告诉我它能做什么，再帮我运行起来。
需要装什么软件、点哪里、输入什么命令，请一步步告诉我。
如果出错了，帮我看看原因。

先看看原来的功能能不能用，
再看看要改成“按学生汇总资料、生成情况卡”，需要调整哪里。
先改一个能看见结果的部分，让我试用。
做好后，把下次怎么打开和使用也记进 README。
```

项目运行后，可以再问：“我刚才点的这个功能，对应哪些文件？如果想改输出内容，要改哪里？”带着已经看见的结果读代码，会更容易把文件和功能对应起来。

有的项目还需要安装 Python、Node.js 等软件。遇到这些提示，不需要先把它们全部学会，可以把项目说明和报错交给 Agent，让它一步步协助安装和运行。下载好仓库，只是先拿到了文件。

### 一个人做东西，为什么也值得用 Git？

情况卡原来能正常打印。你让 Agent 加一个搜索框，搜索做好了，打印却乱了。这时最想知道的是：**刚才改了哪里？原来能用的那版还在吗？**

Git 就像给项目留“存档点”。确认能用时存一版，再继续改。对自己做工具的人，它有三个很实际的用处：

- **改坏了，有以前的版本可找。** 原来能用的内容如果已经存进 Git，就可以取出来比较，必要时恢复。
- **想查问题，有改动记录可看。** 能看到这次哪些文件、哪些内容变了，也可以让 Agent 对照记录排查，不用全凭回忆。
- **做了一半，下次容易接着做。** “能生成情况卡”“增加搜索”“调整打印”各留一版、写句说明，过一阵子回来，还知道自己做到了哪里。

比如打印出了问题，可以直接告诉 Agent：

> 上一个版本打印正常，这次加搜索后排版乱了。帮我对比这次的改动，看看哪里影响了打印，保留搜索功能，把打印修好。

**每做好一个能用的部分，就留一个存档点，再继续尝试。** 这样比较有底气让 Agent 帮你改，也不用复制出一堆“最终版、最终版2、真的最终版”。Git 能找回的是已经存过的内容，所以这个习惯比记住命令更重要。

### 先学会在本地存一版

**先在自己的电脑上存版本就行，不用急着上传 GitHub。** 日常可以先记住两个动作：

- **add：选好这次要存的改动。** 像拍合照前，先确定这次谁入镜。
- **commit：正式拍下一张快照，再写一句说明。** 这就是一个留在电脑里的版本。下次继续改，不会自动覆盖这次存档。

文件本身还是照常编辑和保存。add、commit 是把选好的改动记入版本历史；Git 不会自动记录每次打字。[Git 的 add 说明](https://git-scm.com/docs/git-add) · [commit 说明](https://git-scm.com/docs/git-commit)

### 用 GitHub Desktop，就按这几步做

1. 改好文件并保存，试一下功能是否正常。
2. 在 **Changes** 里查看差异，勾选这次要存的文件。这对应“选好这次的改动”，不用另找一个 add 按钮。
3. 写一句说明，比如“增加按学生搜索”，点击 **Commit**。以后在 **History** 里查看这些存档。[Desktop 提交说明](https://docs.github.com/en/desktop/making-changes-in-a-branch/committing-and-reviewing-changes-to-your-project-in-github-desktop)

从 GitHub Clone 下来的项目，已经是 Git 仓库。自己新建的文件夹，可以先请 Agent 帮你建立 Git 仓库，并设置提交用的姓名和邮箱。准备好后，就可以反复“修改 → 选好改动 → 存一版”。

<details>
<summary>想试命令时，再看 add 和 commit 怎么写</summary>

在已经建立 Git 仓库的项目文件夹里，例如只保存这次对 `index.html` 的修改：

```bash
git status
git add index.html
git commit -m "增加按学生搜索"
```

第一行先看看哪些文件改了；第二行选中 `index.html` 当前的改动；第三行存成一个版本。文件名要换成你实际修改的文件。add 之后如果又改了文件，想把新改动一起存进去，就再 add 一次。

</details>

### 要同步到 GitHub 时，再用 Push

**Commit 存在自己的电脑里；Push 才是上传到 GitHub。** 在 Desktop 中点击 **Push origin**，就把本地的新存档同步上去；新建项目首次上传时通常显示 **Publish repository**。

上传前确认仓库是公开还是私有，不要上传密码或未经授权的业务资料。[可见范围说明](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories) · [创建和发布仓库说明](https://docs.github.com/en/desktop/overview/creating-your-first-repository-using-github-desktop)

代码上传到 GitHub，也不等于网页已经上线。
