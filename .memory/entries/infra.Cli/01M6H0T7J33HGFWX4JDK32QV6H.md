---
id: 01M6H0T7J33HGFWX4JDK32QV6H
module: infra.Cli
entity: McpLaunch
kind: exclusion
status: active
supersedes: []
anchors: []
revision: git:91abe1f
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 用户级 MCP 禁止 pythonw 子进程转接，须 exec 直连 pmem
scope: project
verify: 向 pmem-mcp-serve.py 发 initialize 能返回 result；Cursor 重开 pmem MCP 后 list_modules
  可用
applies: Cursor 用户级 ~/.cursor/mcp.json 接入 pmem 时（Windows）
aliases:
- Connection closed
- MCP未连通
- user-pmem失败
---
现象：Cursor 里 user-pmem 工具发现失败 Connection closed，但命令行 pmem doctor / pmem search 正常，直接 pmemw serve 的 initialize 握手也正常。
原因：~/.cursor/mcp.json 曾用 pythonw.exe 跑 pmem-mcp-serve.py，启动器再用 subprocess.call(pmemw, CREATE_NO_WINDOW) 转一层。
Windows 上 pythonw/无窗口子进程常把 MCP 所需的 stdin/stdout 掐断，宿主侧就 Connection closed。
排除：继续用 pythonw 启动 MCP；或在启动器里 CREATE_NO_WINDOW 子进程转 pmemw。
正确：用户级用 python.exe -u pmem-mcp-serve.py；
启动器用 os.execv 顶替当前进程直连 pmem.exe serve（保留按 WORKSPACE_FOLDER_PATHS 选 root）；
项目级 .cursor/mcp.json 可用 pmemw serve。
