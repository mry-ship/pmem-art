---
id: 01M86ZE0NF3FDV4PHY51ZA6V3P
module: infra.Scripts
entity: Packaging
kind: decision
status: active
supersedes: []
anchors:
- scripts/pack_pmem_art.py#tracked_rel_paths
- scripts/pack_pmem_art.py#should_skip
revision: git:c92cbb7
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 用户 zip 只打 git 已跟踪文件，再去掉 pmem
scope: project
verify: python -m unittest tests.test_pack_pmem_art -v；zip 条目都在 git ls-files 里，且没有
  /.memory/
applies: 打画师用户包时
source:
  conversation: ba9d4a3d-e1c3-47a2-8066-198c30709ef1
---
用户包不再扫整个工作区。scripts/pack_pmem_art.py 只收 git ls-files 里的文件，然后仍按原规则去掉 .memory、pmem hook、pmem MCP、AGENTS/CLAUDE 里的 pmem 段。
本机未提交的会话图、探针文件、竞品参考图不会进 zip。
开发仓 GitHub 仍然带 .memory。不要把打包改回整盘 rglob，也不要为了用户包干净而从仓库里删掉 pmem。
