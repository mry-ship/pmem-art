---
id: 01M6RGE4TC3MPZMF18E9EMYE2H
module: infra.Cli
entity: Install
kind: feature
status: active
supersedes:
- 01M6QY7V8ESGC9XV2NBWKD6JTR
anchors:
- .cursor/hooks.json
- .cursor/mcp.json
- .memory/bin/pmem-hook
revision: git:6a2d5af
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 本机 pmem 已升到 0.6.5（GitHub dbfdab48）
verify: pmem --version 与 pmemw --version 均为 0.6.5；direct_url.json 的 commit_id 为 dbfdab4895187df1271bcbc48bb220b435aebffd；pmem
  doctor 的 Hooks 已接入
applies: 本机用 uv tool 安装的 pmem 升级时
---
需求来源：用户要求跟上 GitHub 上的 pmem 更新。
必须保持：有 pmem serve 占用 ~/.local/bin/pmem.exe 时，禁止 uv tool install --force。
就地升级用 uv pip install，解释器指向 %APPDATA%\uv\tools\pmem\Scripts 下的解释器，包地址为 git+https://github.com/mry-ship/pmem.git 的 pmem[embed]。
升级后若 ~/.local/bin 缺 pmemw.exe，从同目录 Scripts 手工拷贝；pmem.exe 被占用拷不过去时，旧启动器仍能读到新包，不要杀正在跑的 serve。
升级后必须在项目根执行 pmem init --agents auto --hooks auto。
MCP 仍用 command=pmem，Hook 用 pmemw。
当前：源为 GitHub master commit dbfdab4895187df1271bcbc48bb220b435aebffd，命令版号 0.6.5；项目 doctor 通过。
入口：uv tools 环境 + 项目 pmem init。
