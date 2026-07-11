#!/bin/bash

# 配图功能整合验证脚本
# 用途：快速检查 wechat-nostalgia-music 技能的配图功能是否正确整合

echo "=================================="
echo "配图功能整合验证"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
PASS=0
FAIL=0

# 检查函数
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $1 (缺失)"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

check_content() {
    if grep -q "$2" "$1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $1 包含 '$3'"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $1 缺少 '$3'"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

echo "1. 检查核心文件..."
echo "-----------------------------------"
check_file "SKILL.md"
check_file "README.md"
check_file "scripts/generate-image.js"
check_file "references/illustration-guide.md"
check_file "evals/evals.json"
check_file "evals/test-article.md"
echo ""

echo "2. 检查脚本可执行性..."
echo "-----------------------------------"
if [ -x "scripts/generate-image.js" ]; then
    echo -e "${GREEN}✓${NC} scripts/generate-image.js 可执行"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} scripts/generate-image.js 不可执行"
    FAIL=$((FAIL + 1))
fi

if node scripts/generate-image.js --help > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} scripts/generate-image.js 可运行"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} scripts/generate-image.js 无法运行"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "3. 检查 SKILL.md 更新..."
echo "-----------------------------------"
check_content "SKILL.md" "配图或加图片" "任务路由表包含配图"
check_content "SKILL.md" "## 配图功能" "配图功能章节"
check_content "SKILL.md" "年代符号" "年代符号参考"
check_content "SKILL.md" "版权注意事项" "版权保护说明"
echo ""

echo "4. 检查配图指南..."
echo "-----------------------------------"
check_content "references/illustration-guide.md" "70 年代" "70年代符号库"
check_content "references/illustration-guide.md" "80 年代" "80年代符号库"
check_content "references/illustration-guide.md" "90 年代" "90年代符号库"
check_content "references/illustration-guide.md" "00 年代" "00年代符号库"
check_content "references/illustration-guide.md" "PROMPT:" "提示词模板"
echo ""

echo "5. 检查测试用例..."
echo "-----------------------------------"
if grep -q '"id": 7' evals/evals.json 2>/dev/null; then
    echo -e "${GREEN}✓${NC} evals.json 包含配图测试用例 #7"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} evals.json 缺少配图测试用例 #7"
    FAIL=$((FAIL + 1))
fi

if grep -q '"id": 8' evals/evals.json 2>/dev/null; then
    echo -e "${GREEN}✓${NC} evals.json 包含配图测试用例 #8"
    PASS=$((PASS + 1))
else
    echo -e "${RED}✗${NC} evals.json 缺少配图测试用例 #8"
    FAIL=$((FAIL + 1))
fi
echo ""

echo "6. 检查依赖..."
echo "-----------------------------------"
if command -v node > /dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js 已安装: $NODE_VERSION"
    PASS=$((PASS + 1))
else
    echo -e "${YELLOW}⚠${NC} Node.js 未安装（配图功能需要）"
fi

if command -v codex > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} codex-cli 已安装"
    PASS=$((PASS + 1))
elif command -v agy > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} agy (Gemini) 已安装"
    PASS=$((PASS + 1))
else
    echo -e "${YELLOW}⚠${NC} 未检测到图片生成后端（codex-cli 或 agy）"
    echo -e "   内容创作功能可正常使用，配图功能需要安装后端"
fi
echo ""

echo "=================================="
echo "验证结果"
echo "=================================="
echo -e "通过: ${GREEN}$PASS${NC}"
echo -e "失败: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！配图功能已成功整合。${NC}"
    echo ""
    echo "下一步："
    echo "  1. 测试内容创作功能（无需图片生成后端）"
    echo "  2. 如需测试配图功能，请安装 codex-cli 或 agy"
    echo "  3. 运行测试用例 #7 和 #8"
    exit 0
else
    echo -e "${RED}✗ 发现 $FAIL 个问题，请检查上述失败项。${NC}"
    exit 1
fi
