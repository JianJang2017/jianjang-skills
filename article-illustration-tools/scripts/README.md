# Image Generation Tool

Simple image generation script supporting codex-cli and gemini (agy) backends.

## Prerequisites

### Required
- **Node.js 14+**: To run the JavaScript script
  - Check: `node --version`
  - Install: See [INSTALLATION.md](../INSTALLATION.md)

### Image Generation Backend (at least one required)

#### Option 1: Codex CLI (Recommended)
- **Command**: `codex`
- **Provider**: OpenAI Codex
- **Website**: https://openai.com/zh-Hans-CN/codex
- **Features**: High-quality image generation, multiple styles
- **Installation**: 
  - Visit https://openai.com/zh-Hans-CN/codex
  - Or: `npm install -g codex-cli`
- **Verification**: `codex --version`
- **Configuration**: Remove `service_tier` from `~/.codex/config.toml` if present
- **Test**: `codex exec "generate a test image"`

#### Option 2: Antigravity CLI
- **Command**: `agy`
- **Provider**: Google Gemini
- **Website**: https://antigravity.google/docs/cli-getting-started
- **Features**: Fast, uses `generate_image` tool
- **Installation**: Follow Antigravity CLI documentation
- **Verification**: `agy --version`
- **Test**: `agy -p "generate a test image"`

## Installation

No installation needed for the script itself - just ensure you have Node.js and one of the backends.

## Usage

```bash
node scripts/generate-image.js --prompt-file <prompt.md> --output <image.png>
```

### Options

- `--provider, -p <name>` - Provider: auto, codex, gemini (default: auto)
- `--prompt-file <path>` - Path to prompt markdown file (required)
- `--output, -o <path>` - Output image path (required)
- `--aspect-ratio, --ar <ar>` - Aspect ratio (default: 16:9)
- `--model, -m <model>` - Model name (optional)
- `--help, -h` - Show help

### Examples

Auto-detect provider:
```bash
node scripts/generate-image.js --prompt-file prompts/01-architecture.md --output imgs/01-architecture.png
```

Use codex-cli:
```bash
node scripts/generate-image.js -p codex --prompt prompts/01-architecture.md -o imgs/01-architecture.png
```

Use gemini (agy):
```bash
node scripts/generate-image.js -p gemini --prompt prompts/01-architecture.md -o imgs/01-architecture.png
```

## Prompt File Format

The script expects a markdown file with a `PROMPT:` section:

```markdown
---
image_number: 1
title: System Architecture
type: infographic
style: infographic
aspect_ratio: "16:9"
---

# Image Prompt: System Architecture

## Main Content
[Description of the image]

PROMPT:
Create a professional infographic showing a microservices architecture...
```

## Backend Details

### Codex-CLI
Uses `codex exec` to generate images via Codex's imagegen skill.

### Gemini (agy)
Uses `agy -p` with the `generate_image` tool. Images are saved to the artifacts directory.

## Integration with article-illustration-tools

This script is called by the main skill in Step 5 (Generate Images).
