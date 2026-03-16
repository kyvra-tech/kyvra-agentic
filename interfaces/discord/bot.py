# Discord interface — Phase 2
#
# Will use discord.py to mirror the Telegram command set:
#   /report   → supervisor.generate_report()
#   /update   → supervisor.quick_scan()
#   /breaking → supervisor.quick_scan() + spike filter
#   /topic    → supervisor.generate_report_for_topic(topic)
#   /chat     → chat_with_llm()
#
# All pipeline calls are identical to the Telegram interface —
# only the message delivery layer differs.
#
# Required env vars (to add in config.py):
#   DISCORD_BOT_TOKEN
