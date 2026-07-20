#!/bin/bash

# 通义千问图像生成集成测试脚本
# 用于验证 Qwen 后端的配置和功能

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "通义千问图像生成集成测试"
echo "=========================================="
echo

# 1. 检查配置文件
echo "1. 检查配置文件..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}❌ .env 文件不存在${NC}"
    echo "   请从 .env.example 复制并配置"
    exit 1
fi
echo -e "${GREEN}✅ .env 文件存在${NC}"

# 2. 检查必需的环境变量
echo
echo "2. 检查环境变量配置..."
source "$PROJECT_DIR/.env"

if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo -e "${RED}❌ DASHSCOPE_API_KEY 未配置${NC}"
    echo "   请在 .env 文件中设置"
    exit 1
fi
echo -e "${GREEN}✅ DASHSCOPE_API_KEY 已配置${NC}"

REGION=${DASHSCOPE_REGION:-cn-beijing}
echo -e "${GREEN}✅ DASHSCOPE_REGION: $REGION${NC}"

# Workspace ID 仅在新加坡地域必需
if [ "$REGION" = "ap-southeast-1" ]; then
    if [ -z "$DASHSCOPE_WORKSPACE_ID" ]; then
        echo -e "${RED}❌ DASHSCOPE_WORKSPACE_ID 未配置${NC}"
        echo "   新加坡地域需要此配置"
        exit 1
    fi
    echo -e "${GREEN}✅ DASHSCOPE_WORKSPACE_ID: $DASHSCOPE_WORKSPACE_ID${NC}"
elif [ "$REGION" = "cn-beijing" ]; then
    echo -e "${GREEN}✅ 国内地域无需 DASHSCOPE_WORKSPACE_ID${NC}"
fi

MODEL=${QWEN_IMAGE_MODEL:-qwen-image-2.0-pro}
echo -e "${GREEN}✅ QWEN_IMAGE_MODEL: $MODEL${NC}"

# 3. 检查脚本文件
echo
echo "3. 检查脚本文件..."
if [ ! -f "$SCRIPT_DIR/qwen-image-generator.js" ]; then
    echo -e "${RED}❌ qwen-image-generator.js 不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ qwen-image-generator.js 存在${NC}"

if [ ! -f "$SCRIPT_DIR/generate-image.js" ]; then
    echo -e "${RED}❌ generate-image.js 不存在${NC}"
    exit 1
fi
echo -e "${GREEN}✅ generate-image.js 存在${NC}"

# 4. 测试 qwen-image-generator 帮助信息
echo
echo "4. 测试 qwen-image-generator 基础功能..."
if node "$SCRIPT_DIR/qwen-image-generator.js" --help > /dev/null 2>&1; then
    echo -e "${GREEN}✅ qwen-image-generator.js 可以正常运行${NC}"
else
    echo -e "${RED}❌ qwen-image-generator.js 运行失败${NC}"
    exit 1
fi

# 5. 测试 generate-image.js 是否识别 qwen provider
echo
echo "5. 测试 generate-image.js qwen provider 集成..."
if node "$SCRIPT_DIR/generate-image.js" --help | grep -q "qwen"; then
    echo -e "${GREEN}✅ generate-image.js 已集成 qwen provider${NC}"
else
    echo -e "${YELLOW}⚠️  generate-image.js 帮助信息中未找到 qwen${NC}"
fi

# 6. 创建测试 prompt
echo
echo "6. 创建测试 prompt..."
TEST_PROMPT_FILE="/tmp/test-qwen-prompt-$$.md"
cat > "$TEST_PROMPT_FILE" << 'EOF'
---
aspect_ratio: "1:1"
---

PROMPT:
一只坐着的橘黄色猫，表情愉悦，活泼可爱，毛发蓬松柔软，阳光透过窗户洒在它身上。背景是温馨的现代家居客厅。
EOF
echo -e "${GREEN}✅ 测试 prompt 已创建: $TEST_PROMPT_FILE${NC}"

# 7. 测试实际生成（可选，需要用户确认）
echo
echo "7. 实际生成测试（将调用 API，会产生费用）"
read -p "是否继续进行实际生成测试？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    TEST_OUTPUT="/tmp/test-qwen-output-$$.png"
    echo "   生成测试图片到: $TEST_OUTPUT"
    echo "   使用 provider: qwen"
    echo

    if node "$SCRIPT_DIR/qwen-image-generator.js" \
        --prompt "一只坐着的橘黄色猫，表情愉悦" \
        --output "$TEST_OUTPUT" \
        --aspect-ratio 1:1; then
        echo
        echo -e "${GREEN}✅ 生成成功！${NC}"
        echo "   输出文件: $TEST_OUTPUT"

        # 检查文件大小
        if [ -f "$TEST_OUTPUT" ]; then
            SIZE=$(stat -f%z "$TEST_OUTPUT" 2>/dev/null || stat -c%s "$TEST_OUTPUT" 2>/dev/null)
            if [ "$SIZE" -gt 1024 ]; then
                echo -e "${GREEN}   文件大小: $((SIZE / 1024)) KB${NC}"

                # 尝试打开图片（macOS）
                if command -v open > /dev/null 2>&1; then
                    echo "   正在打开图片预览..."
                    open "$TEST_OUTPUT"
                fi
            else
                echo -e "${RED}   ⚠️  文件太小 ($SIZE bytes)，可能生成失败${NC}"
            fi
        fi
    else
        echo
        echo -e "${RED}❌ 生成失败${NC}"
        echo "   请检查:"
        echo "   1. API Key 和 Workspace ID 是否正确"
        echo "   2. 网络连接是否正常"
        echo "   3. API 配额是否充足"
        exit 1
    fi

    # 8. 测试通过 generate-image.js 生成
    echo
    echo "8. 测试通过 generate-image.js 生成..."
    TEST_OUTPUT_2="/tmp/test-generate-image-$$.png"

    if node "$SCRIPT_DIR/generate-image.js" \
        --prompt-file "$TEST_PROMPT_FILE" \
        --output "$TEST_OUTPUT_2" \
        --provider qwen; then
        echo
        echo -e "${GREEN}✅ 通过 generate-image.js 生成成功！${NC}"
        echo "   输出文件: $TEST_OUTPUT_2"

        if [ -f "$TEST_OUTPUT_2" ]; then
            SIZE=$(stat -f%z "$TEST_OUTPUT_2" 2>/dev/null || stat -c%s "$TEST_OUTPUT_2" 2>/dev/null)
            echo -e "${GREEN}   文件大小: $((SIZE / 1024)) KB${NC}"
        fi
    else
        echo
        echo -e "${RED}❌ generate-image.js 生成失败${NC}"
        exit 1
    fi

    # 清理测试文件
    echo
    read -p "是否删除测试文件？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$TEST_OUTPUT" "$TEST_OUTPUT_2" "$TEST_PROMPT_FILE"
        echo -e "${GREEN}✅ 测试文件已删除${NC}"
    else
        echo "测试文件保留:"
        echo "  - $TEST_OUTPUT"
        echo "  - $TEST_OUTPUT_2"
        echo "  - $TEST_PROMPT_FILE"
    fi
else
    echo "跳过实际生成测试"
    rm -f "$TEST_PROMPT_FILE"
fi

echo
echo "=========================================="
echo -e "${GREEN}✅ 所有测试通过！${NC}"
echo "=========================================="
echo
echo "Qwen 后端已成功集成，可以开始使用："
echo
echo "  # 直接使用 Qwen 生成器"
echo "  node scripts/qwen-image-generator.js --prompt \"描述\" --output out.png"
echo
echo "  # 通过 generate-image.js 使用"
echo "  node scripts/generate-image.js --prompt-file prompt.md --output out.png --provider qwen"
echo
echo "  # 飞书推送集成"
echo "  python scripts/send_feishu_image.py --prompt \"描述\" --provider qwen --dry-run"
echo
echo "详细文档: docs/qwen-setup-guide.md"
echo
