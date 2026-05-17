# anthropic-claude-starter

**阅读语言:** [English](README.md) · [Español](README.es.md) · **中文**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/dc-holdings-spa/anthropic-claude-starter?style=flat)](https://github.com/dc-holdings-spa/anthropic-claude-starter/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/dc-holdings-spa/anthropic-claude-starter?style=flat)](https://github.com/dc-holdings-spa/anthropic-claude-starter/network/members)
[![Last commit](https://img.shields.io/github/last-commit/dc-holdings-spa/anthropic-claude-starter/main?style=flat)](https://github.com/dc-holdings-spa/anthropic-claude-starter/commits/main)
[![Repo size](https://img.shields.io/github/repo-size/dc-holdings-spa/anthropic-claude-starter?style=flat)](https://github.com/dc-holdings-spa/anthropic-claude-starter)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg?style=flat)](https://github.com/astral-sh/ruff)
[![Built with Claude](https://img.shields.io/badge/built%20with-Claude-D97757?style=flat)](https://www.anthropic.com/claude)
[![Anthropic SDK](https://img.shields.io/pypi/v/anthropic?label=anthropic&style=flat)](https://pypi.org/project/anthropic/)
[![MCP SDK](https://img.shields.io/pypi/v/mcp?label=mcp&style=flat)](https://pypi.org/project/mcp/)

基于 Anthropic Claude API、Model Context Protocol (MCP)、Skills、Subagents 和 Hooks 构建应用的生产级启动模板。

**状态:** v0.1.0 — 生产级,已审计。

## 为什么存在

提炼自 Anthropic Skilljar 官方课程(约 10 小时,约 86 道测验全部 100% 通过)以及生产环境中构建 agentic 系统的实战经验。目标是一个干净的基线,从第零天起就交付真正重要的模式,没有以后需要删除的脚手架。

---

## 目录

- [概览](#概览)
- [功能](#功能)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [结构](#结构)
- [模式](#模式)
- [成本模型](#成本模型)
- [理念](#理念)
- [贡献](#贡献)
- [许可证](#许可证)

---

## 概览

为基于 Claude 的应用打造的有主见的基础设施。将 Claude API 客户端与自动 prompt caching、MCP 服务器脚手架、确定性 eval 流水线、混合检索、基于 hook 的护栏、可复用的 skills 和 subagents,以及双层测试框架连接在一起。专为那些想构建 agentic 系统而不必在三个 sprint 后重新发现相同模式的团队设计。

## 功能

| 组件 | 描述 |
|---|---|
| `CachedClient` | Anthropic API 封装器,自动注入 `cache_control`。缓存输入 token 最高享 90% 折扣。 |
| MCP 服务器脚手架 | FastMCP 服务器模板,包含 Tool、模板化 Resource 和 Prompt 示例。 |
| Eval 流水线 | LLM-as-judge,带结构化输出(分数、优势、劣势、推理)。 |
| 混合 RAG | Voyage embeddings + BM25 词法检索,通过 Reciprocal Rank Fusion 融合。不使用纯向量。 |
| Hooks | `PreToolUse` 阻止 `.env` 访问。`PostToolUse` 写入时类型检查。 |
| Skills | `commit-style`、`pr-review`、`code-audit` 脚手架,可直接扩展。 |
| Subagents | `researcher`、`reviewer`、`eval-grader`,带结构化输出契约。 |
| `CLAUDE.md` | 内置十条 LLM-first 设计的北极星规则。 |
| `anatomist-lint` | 反模式 linter,作为 pre-commit hook 和 CI 闸门。 |
| 成本计量器 | 按 engagement 追踪和报告预算。 |
| 双层 eval | `tier1` 确定性(零 token)。`tier2` 燃烧 token 的回归测试。 |
| External Validator 模式 | Doble Filo 双 LLM 审计协议,已文档化,随时可调用。 |

## 技术栈

| 依赖 | 角色 |
|---|---|
| [`anthropic`](https://pypi.org/project/anthropic/) | Claude API SDK |
| [`mcp`](https://pypi.org/project/mcp/) | Model Context Protocol SDK |
| [`voyageai`](https://pypi.org/project/voyageai/) | 混合检索的 embedding 模型 |
| [`rank-bm25`](https://pypi.org/project/rank-bm25/) | 词法检索组件 |
| [`fastapi`](https://pypi.org/project/fastapi/) | API 脚手架的 HTTP 接口 |
| [`pytest`](https://pypi.org/project/pytest/) | tier1 和 tier2 的测试运行器 |
| [`ruff`](https://pypi.org/project/ruff/) | Linter 和格式化器 |

## 快速开始

```bash
git clone https://github.com/dc-holdings-spa/anthropic-claude-starter my-app
cd my-app
cp .env.example .env
# 编辑 .env:设置 ANTHROPIC_API_KEY。VOYAGE_API_KEY 是可选的(仅 RAG 需要)。

# 初始化 Claude 设置(将 $PWD 解析到 .claude/settings.local.json)。
bash scripts/init-claude.sh

# 安装并运行确定性 tier。
pip install -e .
pytest tests/tier1     # 零 token
```

运行燃烧 token 的回归测试套件:

```bash
pytest tests/tier2     # 消耗 token;由 CI label 控制
```

## 结构

```
.claude/
├── settings.json            已提交的 hooks,与团队共享
├── settings.local.json      gitignored,由 init-claude.sh 生成
├── skills/                  共享 skills
├── agents/                  自定义 subagents
└── commands/                slash 命令

src/
├── api/                     FastAPI 服务器脚手架
├── prompts/                 版本化的 prompts,关联到 evals
├── tools/                   自定义 tool 函数
├── mcp_servers/             FastMCP 服务器
├── eval/                    eval 流水线框架
├── rag/                     混合检索 (vector + BM25 + RRF)
└── caching.py               带 cache_control 自动注入的 Claude 客户端

tests/
├── tier1/                   确定性,零 token,make e2e
└── tier2/                   燃烧 token,make e2e-full

scripts/
├── init-claude.sh           $PWD 解析器
└── anatomist-lint.py        反模式检查

docs/
├── PATTERNS.md              决策树和速查表
├── DECISIONS.md             workflow vs agent 决策
├── COST_MODEL.md            估算框架
├── BEST_PRACTICES.md        跨课程综合
└── EXTERNAL_VALIDATOR.md    Doble Filo 协议

.github/workflows/
├── anatomist-lint.yml       反模式 CI 闸门
└── eval-pipeline.yml        每个 PR 运行 evals
```

## 模式

选择正确 Claude 原语的决策树。

| 需求 | 使用 | 参考 |
|---|---|---|
| 始终相关的知识 | `CLAUDE.md` | [docs/PATTERNS.md](docs/PATTERNS.md) |
| 任务特定的知识 | Skill | [.claude/skills/](.claude/skills/) |
| 自动响应事件 | Hook | [.claude/settings.json](.claude/settings.json) |
| 需要隔离上下文的任务 | Subagent | [.claude/agents/](.claude/agents/) |
| 外部服务或数据源 | MCP 服务器 | [src/mcp_servers/](src/mcp_servers/) |
| 程序化 Claude Code | `@anthropic-ai/claude-agent-sdk` | [docs/PATTERNS.md](docs/PATTERNS.md) |

## 成本模型

典型工作负载的数量级目标。

| 工作负载 | 目标成本 |
|---|---|
| 单次 API 请求(基础 prompt) | $0.002 – $0.01 |
| 带 eval 流水线和缓存的 engagement | $0.10 – $0.50 |
| 端到端客户 POC | $5 – $15 |

完整方法论见 [docs/COST_MODEL.md](docs/COST_MODEL.md)。

## 理念

1. 先可靠地解决问题,再设计优雅的架构。
2. 确定性胜过希望。关键路径用 hooks 而不是 prompts。
3. 上下文窗口是有限的。用 subagents 保护它用于探索。
4. 默认无状态。有状态只在成本明确且可衡量时使用。
5. 结构化输出胜过措辞优美的 prompts。
6. Tool 描述做两件事:何时调用,以及如何调用。
7. Tools 采用最小权限。每个 agent 都用 allow-list。
8. 验证比信任成本低。`PreToolUse` hooks 和引用都很便宜。

## 贡献

欢迎 issues 和 pull requests。提交 PR 前:

1. 运行 `ruff format` 和 `ruff check`。
2. 运行 `pytest tests/tier1`。必须以零 token 通过。
3. 运行 `python scripts/anatomist-lint.py`。必须通过。
4. 如果改动了 prompts 或 eval 逻辑,运行 `pytest tests/tier2` 并附上报告。

## 许可证

MIT。见 [LICENSE](LICENSE)。