from __future__ import annotations

import argparse
import logging
import threading
import time

from .auth import MicrosoftAuth
from .config import load_config
from .email_monitor import EmailMonitor
from .llm_client import LLMClient
from .notifier import Notifier
from .onedrive_client import OneDriveClient
from .workflow import InvestmentWorkflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Investment-triggered email workflow")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    return parser.parse_args()


def run_monitor(config_path: str, stop_event: threading.Event | None = None) -> None:
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    config = load_config(config_path)

    monitor = EmailMonitor(config.imap)
    onedrive_client = OneDriveClient(config.onedrive)
    workflow = InvestmentWorkflow(
        onedrive=onedrive_client,
        llm=LLMClient(config.openai),
    )
    notifier = Notifier(config.smtp)

    # Auth setup
    auth_client = None
    current_refresh_token = config.refresh_token
    last_refresh_time = 0

    if getattr(config.imap, "auth_method", "password") == "oauth" or getattr(config.onedrive, "auth_method", "password") == "oauth":
        try:
            auth_client = MicrosoftAuth(client_id=config.client_id)
        except Exception as e:
            logging.error(f"Failed to init auth client: {e}")

    logging.info("Starting monitor for keyword '%s'", config.investment_keyword)

    while True:
        # Token Refresh Logic
        if auth_client and current_refresh_token:
            # Refresh if > 45 mins since last refresh (token usually valid for 60m)
            # or if it's the first iteration (last_refresh_time=0) to ensure freshness
            if time.time() - last_refresh_time > 2700:
                try:
                    logging.info("Refreshing access token...")
                    result = auth_client.refresh_access_token(current_refresh_token)
                    new_token = result.get("access_token")
                    new_refresh = result.get("refresh_token")

                    if new_token:
                        monitor.update_token(new_token)
                        notifier.update_token(new_token)
                        onedrive_client.update_token(new_token)
                        last_refresh_time = time.time()
                        logging.info("Token refreshed successfully.")

                    if new_refresh:
                        current_refresh_token = new_refresh
                except Exception as e:
                    logging.error(f"Token refresh failed: {e}")

        if stop_event and stop_event.is_set():
            logging.info("Stopping monitor...")
            break

        try:
            unseen = monitor.fetch_unseen()
            logging.info("Fetched %d unseen email(s)", len(unseen))
        except Exception:
            logging.exception("Error fetching emails")
            if stop_event:
                if stop_event.wait(config.poll_interval_seconds):
                    break
            else:
                time.sleep(config.poll_interval_seconds)
            continue

        for incoming in unseen:
            if stop_event and stop_event.is_set():
                break

            try:
                if monitor.has_keyword(incoming, config.investment_keyword):
                    logging.info("Keyword '%s' detected in UID %s", config.investment_keyword, incoming.uid)
                    output = workflow.run(config.investment_keyword, incoming)
                    notifier.send(
                        recipients=config.recipients,
                        subject=output.subject,
                        body=output.body,
                        graph_path=output.graph_path,
                    )
                    logging.info("Notification sent for UID %s", incoming.uid)

                monitor.mark_as_read(incoming.uid)
            except Exception:
                logging.exception("Error processing email UID %s", incoming.uid)

        if stop_event:
            if stop_event.wait(config.poll_interval_seconds):
                logging.info("Stopping monitor during sleep...")
                break
        else:
            time.sleep(config.poll_interval_seconds)


def main() -> None:
    args = parse_args()
    run_monitor(args.config)


if __name__ == "__main__":
    main()
