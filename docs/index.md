# IDAssist Documentation

Welcome to the IDAssist documentation. This guide covers installation, configuration, and usage of IDAssist — an AI-powered reverse engineering plugin for IDA Pro.

<!-- SCREENSHOT: IDAssist main interface with the Explain tab active -->
![Screenshot](/docs/screenshots/main_interface.png)

## What is IDAssist?

IDAssist is an IDA Pro plugin that brings LLM-powered analysis directly into your reverse engineering workflow. It provides AI-assisted function explanation, interactive querying, automated rename suggestions, a semantic knowledge graph, RAG-powered document search, and collaborative symbol sharing through SymGraph.

IDAssist runs as a dockable panel inside IDA Pro 9.0+ and connects to LLM providers (Anthropic, OpenAI, Ollama, LiteLLM) to analyze binary code. All data is stored locally in SQLite databases under `~/.idapro/idassist/`.

## Tabs Overview

IDAssist organizes its functionality into seven tabs:

| Tab | Description |
|-----|-------------|
| **[Explain](tabs/explain-tab.md)** | Generate function and line explanations with security analysis |
| **[Query](tabs/query-tab.md)** | Interactive chat with context macros, ReAct agent, and MCP tools |
| **[Actions](tabs/actions-tab.md)** | AI-powered rename and retype suggestions with confidence scores |
| **[Semantic Graph](tabs/semantic-graph-tab.md)** | Knowledge graph with visual explorer, search, and community detection |
| **[RAG](tabs/rag-tab.md)** | Upload reference documents for context-enriched analysis |
| **[SymGraph](tabs/symgraph-tab.md)** | Compare against SymGraph, import shared analysis, and publish your own revisions |
| **[Settings](tabs/settings-tab.md)** | Configure LLM providers, MCP servers, SymGraph credentials, system prompt, and database paths |

## Key Features

### MCP Tool Integration

IDAssist provides built-in internal tools — function lookup, disassembly, pseudocode, cross-references, renaming, and graph queries — that LLMs can invoke during reasoning via function calling. You can also connect to external MCP servers for additional tool capabilities, including URL-based and stdio-launched MCP servers.

### ReAct Agent

The Query tab supports an autonomous ReAct agent mode where the LLM plans an investigation, executes tools to gather information, reflects on findings, and synthesizes answers across multiple reasoning rounds.

### Extended Thinking

Control reasoning depth with four effort levels for supported Opus, Sonnet, GPT, and open-weight reasoning models. Availability depends on the selected model and provider:

| Level | Token Budget | Use Case |
|-------|-------------|----------|
| None | Disabled | Quick, simple questions |
| Low | ~2K tokens | Straightforward analysis |
| Medium | ~10K tokens | Moderate complexity |
| High | ~25K tokens | Deep analysis, complex functions |

### Semantic Graph

Build a searchable knowledge graph of the binary's functions, relationships, and security characteristics. Includes:
- Automatic function indexing via `idautils.Functions()`
- LLM-generated summaries for each function
- Security flag detection (buffer overflow, injection, format string, etc.)
- Network flow and taint analysis
- Community detection for module identification
- Visual graph rendering with Graphviz layout

## Supported LLM Providers

| Type | Auth | Streaming | Tool Calling |
|------|------|-----------|-------------|
| `anthropic_platform` | API Key | Yes | Yes |
| `anthropic_oauth` | OAuth | Yes | Yes |
| `anthropic_claude_cli` | Local CLI | Yes | Yes |
| `openai_platform` | API Key | Yes | Yes |
| `openai_oauth` | OAuth | Yes | Yes |
| `ollama` | None (local) | Yes | Model-dependent |
| `litellm` | Proxy URL | Yes | Provider-dependent |

### Recommended Models

- **Open-weight models**: Start with [GLM](https://github.com/zai-org), [Qwen](https://github.com/QwenLM), [DeepSeek](https://github.com/deepseek-ai), [Nemotron](https://www.nvidia.com/en-us/ai-data-science/foundation-models/nemotron/), [Gemma](https://deepmind.google/models/gemma/), or [Muse](https://research.meta.ai/blog/introducing-muse-glimmer-open-agentic-model). Choose a current instruction-tuned, coding, or reasoning model; for Muse, select an open-weight release.
- **Hosted frontier models**: Opus, Sonnet, and GPT are recommended for code analysis and complex investigations.
- **Agentic mode, MCP, and Actions**: Prioritize reliable native tool calling, structured arguments, and multi-step reasoning. Verify these capabilities with the selected model and serving backend before starting a long investigation.
- **Explain and semantic graph summaries**: Balance code understanding, instruction following, latency, and context capacity. Compare results on representative functions from your binaries.
- **Local/private analysis**: Run open weights through a supported local or self-hosted endpoint. Choose a model and quantization that fit available memory, leaving room for decompiled code, tool results, and conversation history. Check runtime support for the selected model; a hosted API serving open weights still sends data off-machine.

Recommendations use family names rather than fixed releases or parameter counts. The **Model** field still requires the exact model ID or installed tag exposed by your endpoint; family names are not necessarily valid IDs. Use `ollama list` for installed Ollama tags, or consult your provider's model catalog. For a proxy, use its configured model alias.

Reasoning ability does not guarantee support for the plugin's **Reasoning Effort** control. Enable it only when the model and provider support it; otherwise leave it at **None**.

## Architecture Overview

IDAssist uses an MVC architecture:

```
idassist_plugin.py          # IDA plugin entry point
src/
├── views/                  # PySide6 tab widgets (UI)
├── controllers/            # Signal handlers, state management
├── services/               # Business logic, DB access
│   ├── llm_providers/      # LLM provider implementations
│   ├── graphrag/           # Knowledge graph services
│   ├── streaming/          # Streaming response rendering
│   └── ...
└── mcp_server/             # Internal tool definitions and handlers
```

- **Views** emit Qt signals on user interaction
- **Controllers** connect signals to service methods
- **Services** handle LLM calls, database access, and graph analysis
- All IDA API calls run on the main thread via `execute_on_main_thread()`
- LLM responses stream incrementally to the UI

## Getting Started

New to IDAssist? Start with the [Getting Started Guide](getting-started.md) for installation, provider setup, and your first analysis.

## Workflows

Step-by-step guides for common tasks:

- [Explain Workflow](workflows/explain-workflow.md) — Analyze and document functions
- [Query Workflow](workflows/query-workflow.md) — Ask questions with context macros, MCP, and ReAct
- [Semantic Graph Workflow](workflows/semantic-graph-workflow.md) — Build and explore the binary knowledge graph

## Tab Reference

Detailed reference for each tab's UI elements and capabilities:

- [Explain Tab](tabs/explain-tab.md)
- [Query Tab](tabs/query-tab.md)
- [Actions Tab](tabs/actions-tab.md)
- [Semantic Graph Tab](tabs/semantic-graph-tab.md)
- [RAG Tab](tabs/rag-tab.md)
- [SymGraph Tab](tabs/symgraph-tab.md)
- [Settings Tab](tabs/settings-tab.md)
