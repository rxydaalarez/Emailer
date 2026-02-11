# Investment Update Email Workflow

This project monitors an inbox for investment-specific updates (e.g., `bert`), then automatically:

1. Pulls historical opinion/research files from a OneDrive folder.
2. Uses a premium multimodal LLM workflow to summarize the new update in context.
3. Generates a graph artifact from historical scoring signals (if present).
4. Sends a formatted outbound email to a configured recipient list.

## Features

- Keyword-triggered email monitoring (IMAP polling)
- OneDrive ingestion via Microsoft Graph API
- Context assembly from historical files
- LLM-driven summarization + email drafting
- Graph generation (`PNG`) from extracted historical score data
- SMTP notification to configurable distribution list

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
python -m emailer_bot.main --config config.yaml
```

## Configuration

See `config.example.yaml` for required fields.

### Recipient format

Recipients are defined as a list of objects:

```yaml
recipients:
  - name: "Alice Analyst"
    email: "alice@example.com"
  - name: "Bob PM"
    email: "bob@example.com"
```

## Notes

- You must provide credentials/tokens for IMAP, Microsoft Graph, SMTP, and OpenAI APIs.
- The default LLM model is configurable and should be set to your top-tier multimodal model offering.
- Historical files can be `txt`, `md`, `json`, or `csv`.
