#!/usr/bin/env python3
# SPDX-License-Identifier: MIT-0
"""Run one synthetic fixture without AWS credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from finding_processor.config import Settings
from finding_processor.handler import process_event


class PrintingSNS:
    def publish(self, **kwargs: Any) -> dict[str, Any]:
        print(f"sanitized_notification={kwargs['Message']}")
        return {"MessageId": "local-demo"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--mode", choices=("ocsf", "asff", "dual"), required=True)
    args = parser.parse_args()
    event = json.loads(args.fixture.read_text(encoding="utf-8"))
    settings = Settings(
        finding_schema_mode=args.mode,
        local_demo=True,
        notification_topic_arn="arn:aws:sns:us-east-1:000000000000:local-demo",
        policy_path=str(Path(__file__).parents[1] / "config/triage-policy.json"),
    )
    print(json.dumps(process_event(event, settings=settings, sns_client=PrintingSNS()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
