# 通义千问（Qwen）图像生成 - 快速参考卡

## 一分钟上手

### 1️⃣ 配置（只需一次）

编辑 `.env` 文件：

```bash
DASHSCOPE_API_KEY=sk-your-key-here
DASHSCOPE_WORKSPACE_ID=ws-your-workspace-here
```

获取方式：https://help.aliyun.com/zh/model-studio/get-api-key

### 2️⃣ 测试

```bash
./scripts/test-qwen-integration.sh
```

### 3️⃣ 使用

```bash
# 最简单
node scripts/qwen-image-generator.js \
  --prompt "一只橘猫" \
  --output cat.png

# 推荐方式（集成到现有流程）
node scripts/generate-image.js \
  --prompt-file prompt.md \
  --output result.png \
  --provider qwen
```

---

## 常用命令

### 基础生成

```bash
# 单张图片
node scripts/qwen-image-generator.js \
  --prompt "描述" \
  --output output.png

# 指定宽高比
node scripts/qwen-image-generator.js \
  --prompt "描述" \
  --output output.png \
  --aspect-ratio 16:9

# 指定模型
node scripts/qwen-image-generator.js \
  --prompt "描述" \
  --output output.png \
  --model qwen-image-2.0-pro
```

### 批量生成

```bash
# 生成 3 张不同的图（qwen-image-2.0 系列）
node scripts/qwen-image-generator.js \
  --prompt "手绘架构图" \
  --output arch.png \
  --count 3
# 输出：arch-1.png, arch-2.png, arch-3.png
```

### 精确控制

```bash
# 使用负面提示词
node scripts/qwen-image-generator.js \
  --prompt "风景画" \
  --negative-prompt "模糊,低分辨率,扭曲" \
  --output landscape.png

# 关闭智能改写（更精确）
node scripts/qwen-image-generator.js \
  --prompt "详细的描述..." \
  --output output.png \
  --no-prompt-extend
```

### 集成到工作流

```bash
# 飞书推送
python scripts/send_feishu_image.py \
  --prompt "描述" \
  --provider qwen \
  --user-ids "ou_xxx"

# 小红书发布
node scripts/publish_xiaohongshu.js \
  --prompt "描述" \
  --provider qwen \
  --aspect-ratio 3:4

# 抖音发布
node scripts/publish_douyin.js \
  --prompt "描述" \
  --provider qwen
```

---

## 配置速查

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DASHSCOPE_API_KEY` | API Key（必需） | - |
| `DASHSCOPE_WORKSPACE_ID` | Workspace ID（必需） | - |
| `DASHSCOPE_REGION` | 地域 | `cn-beijing` |
| `QWEN_IMAGE_MODEL` | 模型 | `qwen-image-2.0-pro` |
| `QWEN_PROMPT_EXTEND` | 智能改写 | `true` |
| `QWEN_WATERMARK` | 水印 | `false` |

### 模型选择

| 模型 | 速度 | 质量 | 价格 | 适用场景 |
|------|------|------|------|---------|
| `qwen-image-2.0-pro` ⭐ | 快 | 最高 | 高 | 正式产出 |
| `qwen-image-2.0` | 最快 | 高 | 中 | 日常使用 |
| `qwen-image-max` | 中 | 最高 | 高 | 写实风格 |
| `qwen-image-plus` | 快 | 中 | 低 | 测试/试验 |

### 宽高比

| 比例 | qwen-image-2.0 | max/plus | 适用 |
|------|----------------|----------|------|
| `16:9` | 2688×1536 | 1664×928 | 横版 |
| `9:16` | 1536×2688 | 928×1664 | 竖版 |
| `1:1` | 2048×2048 | 1328×1328 | 方形 |
| `4:3` | 2368×1728 | 1472×1104 | 传统横 |
| `3:4` | 1728×2368 | 1104×1472 | 传统竖 |

---

## Provider 对比

| 特性 | Qwen | Codex | Gemini |
|------|------|-------|--------|
| **速度** | 10-30s | 30-120s | 20-60s |
| **稳定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **文字渲染** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **中文支持** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **批量生成** | ✅ | ❌ | ❌ |
| **负面提示词** | ✅ | ❌ | ❌ |
| **自定义分辨率** | ✅ | ❌ | ❌ |
| **依赖** | API Key | codex-cli | agy |

---

## 常见问题

### Q: 如何获取 API Key？
**A:** 访问 https://help.aliyun.com/zh/model-studio/get-api-key

### Q: 生成失败怎么办？
**A:** 检查：
1. API Key 和 Workspace ID 是否正确
2. 地域设置是否匹配（北京 vs 新加坡）
3. API 配额是否充足
4. 网络连接是否正常

### Q: 如何降低成本？
**A:** 
- 日常用 `qwen-image-2.0` 或 `qwen-image-plus`
- 正式产出用 `qwen-image-2.0-pro`
- 使用负面提示词提高首次成功率
- 利用批量生成减少重复调用

### Q: 如何切换 provider？
**A:**
```bash
# 显式指定
--provider qwen

# 自动选择（优先级：qwen > codex > gemini）
--provider auto
```

### Q: 与 codex/gemini 共存吗？
**A:** ✅ 完全共存，互不影响

---

## 文档链接

- 📖 [完整配置指南](qwen-setup-guide.md)
- 📋 [API 文档参考](../../docs/qwen_api.md)
- 📝 [变更日志](../CHANGELOG-qwen.md)

---

## 支持

遇到问题？
1. 查看 [故障排查](qwen-setup-guide.md#故障排查)
2. 运行 `./scripts/test-qwen-integration.sh`
3. 查看 [错误码文档](https://help.aliyun.com/zh/model-studio/error-code)

---

**版本：** 2026-07-20
**作者：** Kiro Assistant
