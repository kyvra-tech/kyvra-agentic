# Web API interface — Phase 2
#
# Will use FastAPI to expose the pipeline over HTTP:
#   GET  /report          → supervisor.generate_report()
#   GET  /update          → supervisor.quick_scan()
#   GET  /breaking        → supervisor.quick_scan() + spike filter
#   GET  /topic?q={kw}    → supervisor.generate_report_for_topic(kw)
#   POST /chat            → chat_with_llm(message, history)
#
# Enables: frontends, n8n / Make / Zapier webhooks, CLI scripts,
#          and any other HTTP client.
#
# Required dependency (add to requirements.txt when implementing):
#   fastapi
#   uvicorn
