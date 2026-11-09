---
id: 01M70WCKTD9X5YKK02BBYC3RQ3
module: infra.Tests
entity: AtlasRevealProxyBypass
kind: conclusion
status: active
supersedes: []
anchors:
- tests/test_atlas_all_images.py
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: atlas reveal HTTP 测须 ProxyHandler 空代理直连环回
verify: python3 -m unittest tests.test_atlas_all_images.AtlasAllImagesTests.test_reveal_serves_workbench_html_over_http
  -q
applies: 本机 getproxies 指向本地代理时跑 test_atlas_all_images reveal HTTP
---
根因：urllib.getproxies 把 http 指到本地代理，默认 urlopen RemoteDisconnected。测例用 build_opener(ProxyHandler({})) 直连环回。
