#!/usr/bin/env bash
# Kyvra self-host setup script
# Usage: bash setup.sh

set -e

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║        Kyvra Self-Host Setup         ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════╝${RESET}"
echo ""

# ── Check Docker ────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo -e "${RED}✗ Docker not found.${RESET}"
  echo "  Install Docker Desktop: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker compose version &>/dev/null; then
  echo -e "${RED}✗ Docker Compose not found.${RESET}"
  echo "  Docker Compose comes with Docker Desktop — make sure it's up to date."
  exit 1
fi

echo -e "${GREEN}✓ Docker found${RESET}"

# ── Create .env from example ─────────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${GREEN}✓ Created .env from .env.example${RESET}"
else
  echo -e "${YELLOW}⚠ .env already exists — skipping copy${RESET}"
fi

echo ""
echo -e "${BOLD}Now fill in your .env file:${RESET}"
echo ""
echo "  Required:"
echo "    TELEGRAM_BOT_TOKEN  — from @BotFather on Telegram"
echo "    REPORT_CHAT_IDS     — your Telegram chat ID (@userinfobot to find it)"
echo "    DEEPSEEK_API_KEY    — from https://platform.deepseek.com (free tier works)"
echo ""
echo "  Optional but recommended:"
echo "    X_BEARER_TOKEN      — Twitter API key for better crypto/tech signal"
echo ""

COMPOSE_FILE="docker-compose.yml"

# ── Open .env for editing ────────────────────────────────────────────────────
echo ""
read -rp "Open .env in your editor now? [Y/n]: " open_env
open_env=${open_env:-Y}

if [[ "$open_env" =~ ^[Yy]$ ]]; then
  ${EDITOR:-nano} .env
fi

# ── Validate required vars ───────────────────────────────────────────────────
echo ""
echo "Checking .env..."

missing=0
for var in TELEGRAM_BOT_TOKEN REPORT_CHAT_IDS; do
  val=$(grep -E "^${var}=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
  if [ -z "$val" ] || [[ "$val" == *"your_"* ]]; then
    echo -e "${RED}  ✗ $var is not set${RESET}"
    missing=1
  else
    echo -e "${GREEN}  ✓ $var${RESET}"
  fi
done

if [ "$missing" = "1" ]; then
  echo ""
  echo -e "${RED}Please fill in the missing values in .env and re-run this script.${RESET}"
  exit 1
fi



# ── Start ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Starting Kyvra...${RESET}"
docker compose -f "$COMPOSE_FILE" up -d --build

echo ""
echo -e "${GREEN}${BOLD}✓ Kyvra is running!${RESET}"
echo ""
echo "  Your bot is live. Open Telegram and send /start to your bot."
echo ""
echo "  Useful commands:"
echo "    docker compose logs -f kyvra     — view live logs"
echo "    docker compose restart kyvra     — restart the bot"
echo "    docker compose down              — stop everything"
echo ""
echo "  If you find Kyvra useful, consider supporting the project:"
echo "  → https://github.com/kyvra-tech/kyvra-agentic"
echo ""
