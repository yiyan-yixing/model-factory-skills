#!/bin/bash
# 模型工厂 Agent 体系一键安装脚本
# 用法: bash install.sh /path/to/project
# 或者: bash install.sh /path/to/project --skip-init
#
# 本地仓库安装（已 clone model-factory-skills 到本地）:
#   bash install.sh /path/to/project
# 远程安装（发布到 Git 后）:
#   curl -fsSL https://example.com/model-factory-skills/install.sh | bash

set -e

# 仓库地址（发布后替换为真实地址；本地安装时自动检测使用本地文件）
REPO_URL="https://github.com/your-org/model-factory-skills.git"
CLONE_DIR=$(mktemp -d)
TARGET_DIR="."
SKIP_INIT=""

# ─── 解析参数 ───
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-init) SKIP_INIT="1"; shift ;;
    --init) SKIP_INIT=""; shift ;;
    -*) echo "未知参数: $1"; shift ;;
    *) TARGET_DIR="$1"; shift ;;
  esac
done

echo "🏭 模型工厂 Agent 体系安装"
echo "============================"
echo ""

# ─── Step 1: 定位源仓库 ───
echo "📦 [1/5] 定位源仓库..."
# 优先使用本地仓库（脚本所在目录的上一级或同级）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/README.md" ] && [ -d "$SCRIPT_DIR/agents" ]; then
  CLONE_DIR="$SCRIPT_DIR"
  echo "   使用本地仓库: $CLONE_DIR"
else
  echo "   本地未找到完整仓库，尝试克隆远程..."
  git clone --depth 1 "$REPO_URL" "$CLONE_DIR" --quiet
  echo "   克隆完成"
fi

# ─── Step 2: 安装 Skills ───
echo "🎯 [2/5] 安装 Skills 到 .claude/skills/..."
cd "$TARGET_DIR"
mkdir -p .claude/skills
if [ -d "$CLONE_DIR/skills" ]; then
  cp -r "$CLONE_DIR"/skills/* .claude/skills/ 2>/dev/null || true
  echo "   ✅ 16 个 Skills"
fi

# ─── Step 3: 安装 Agents ───
echo "👥 [3/5] 安装 Agents 到 .claude/agents/..."
mkdir -p .claude/agents
for agent_file in "$CLONE_DIR"/agents/*.md; do
  if [ -f "$agent_file" ]; then
    cp "$agent_file" .claude/agents/
  fi
done
echo "   ✅ 15 个 Agent + WORKFLOW + 质疑协议"

# ─── Step 4: 安装记忆系统 + 白板 + 评估 + CLAUDE.md ───
echo "🧠 [4/5] 安装记忆系统 + 白板 + 评估体系..."

# 记忆系统
mkdir -p .claude/memory/core .claude/memory/archival/decisions .claude/memory/archival/lessons .claude/memory/archival/user-research .claude/memory/recall/sessions
if [ -d "$CLONE_DIR/memory/core" ]; then
  cp "$CLONE_DIR"/memory/core/* .claude/memory/core/ 2>/dev/null || true
  cp "$CLONE_DIR"/memory/archival/decisions/* .claude/memory/archival/decisions/ 2>/dev/null || true
  cp "$CLONE_DIR"/memory/archival/lessons/* .claude/memory/archival/lessons/ 2>/dev/null || true
  cp "$CLONE_DIR"/memory/archival/user-research/* .claude/memory/archival/user-research/ 2>/dev/null || true
  echo "   ✅ 记忆系统 (core + archival + recall)"
fi

# 共享白板
mkdir -p .claude/blackboard
if [ -d "$CLONE_DIR/blackboard" ]; then
  cp "$CLONE_DIR"/blackboard/* .claude/blackboard/ 2>/dev/null || true
  echo "   ✅ 共享白板 (4 个文件)"
fi

# 评估体系
mkdir -p .claude/evals
if [ -d "$CLONE_DIR/evals" ]; then
  cp "$CLONE_DIR"/evals/* .claude/evals/ 2>/dev/null || true
  echo "   ✅ 评估体系"
fi

# 垂直落地配置（参考）
if [ -d "$CLONE_DIR/profiles" ]; then
  mkdir -p .claude/profiles
  cp -r "$CLONE_DIR"/profiles/* .claude/profiles/ 2>/dev/null || true
  echo "   ✅ 垂直 profile（参考配置）"
fi

# CLAUDE.md
if [ -f "$CLONE_DIR/CLAUDE.md.template" ]; then
  cp "$CLONE_DIR"/CLAUDE.md.template .claude/CLAUDE.md
  echo "   ✅ CLAUDE.md (记忆入口)"
fi

# ─── Step 5: 安装 init.sh ───
echo "🚀 [5/5] 安装初始化脚本..."
if [ -f "$CLONE_DIR/init.sh" ]; then
  cp "$CLONE_DIR"/init.sh .claude/init.sh
  chmod +x .claude/init.sh
  echo "   ✅ init.sh (交互式初始化)"
fi

# 清理临时目录（本地仓库不删）
if [ "$CLONE_DIR" != "$SCRIPT_DIR" ] && [ -d "$CLONE_DIR" ]; then
  rm -rf "$CLONE_DIR"
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "已安装内容："
echo "  .claude/skills/        — 16 个 Skills"
echo "  .claude/agents/        — 15 个 Agent + WORKFLOW + 质疑协议"
echo "  .claude/memory/        — 三层记忆系统 (core + archival + recall)"
echo "  .claude/blackboard/    — 共享白板 (4 个文件)"
echo "  .claude/evals/         — 效果评估体系"
echo "  .claude/CLAUDE.md      — 记忆入口 (@import core)"
echo "  .claude/init.sh        — 交互式初始化脚本"
echo ""

# ─── Step 6: 自动初始化（非 --skip-init 时） ───
if [ -z "$SKIP_INIT" ] && [ -f ".claude/init.sh" ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⚡ 现在运行初始化，设置你的模型公司信息"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  bash .claude/init.sh
else
  echo "下一步："
  echo "  1. 运行 bash .claude/init.sh 初始化你的模型公司信息"
  echo "  2. 启动 Claude Code，输入 @ceo 定垂直场景和模型路线"
fi
