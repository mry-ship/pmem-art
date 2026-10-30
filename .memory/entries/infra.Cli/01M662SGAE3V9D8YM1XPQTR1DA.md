---
id: 01M662SGAE3V9D8YM1XPQTR1DA
module: infra.Cli
entity: McpRoot
kind: correction
status: active
supersedes:
- 01M64DAZ4050A00D2V2BAGRJV0
anchors:
- .cursor/mcp.json
revision: git:959a507
author: 1002378395@qq.com
note_date: '2026-10-30'
summary: Windows用户级pmem须用launcher选root，禁止裸workspaceFolder
scope: project
verify: user-pmem list_modules 返回 ok 且 project_root 指向本仓；无「还没有接入 pmem」
applies: Cursor 用户级 mcp.json 使用 --root 时（Windows 与多根工作区均中招）
aliases:
- MCP未接入
- workspaceFolder未展开
- 还没有接入pmem
---
Windows 上用户级 ~/.cursor/mcp.json 写 pmem serve --root ${workspaceFolder} 时，Cursor 经常不展开变量。
实测进程命令行是字面量 --root ${workspaceFolder}，cwd=Temp，resolve_root 跳过 ${...} 后找不到 .memory，MCP 一律返回「当前工作区还没有接入 pmem」。
CLI 在项目目录仍正常。
本机多根工作区 WORKSPACE_FOLDER_PATHS 为逗号分隔。
修法：用户级改走 C:\Users\ZhengLangPC\.local\bin\pmem-mcp-serve.py（按 WORKSPACE_FOLDER_PATHS 里最近改过 .memory 的目录选 root）；
项目 .cursor/mcp.json 的 pmem --root 写本仓绝对路径；
pmem-art 的 command 用 python（WindowsApps 的 python3 是商店占位）。
改完需重载 MCP。
本机另把 Python312\python.exe 复制为 ~/.local/bin/python3.exe，避免其它 python3 入口再踩商店占位。
