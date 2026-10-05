"""Run settings, read from environment variables so the same code runs locally and in CI."""

import os
from datetime import datetime

SAUCE_USERNAME = os.getenv("SAUCE_USERNAME")
SAUCE_ACCESS_KEY = os.getenv("SAUCE_ACCESS_KEY")

# Sauce Labs EU data center, where the PawKnits APK is uploaded.
HUB_URL = "https://ondemand.eu-central-1.saucelabs.com/wd/hub"

# Real Device Access API in the same data center, used to check device availability.
RDC_API_URL = "https://api.eu-central-1.saucelabs.com/rdc/v2"

# How long to wait for a free device before giving up, and how often to re-check (seconds).
DEVICE_WAIT_TIMEOUT = int(os.getenv("DEVICE_WAIT_TIMEOUT", "300"))
DEVICE_POLL_INTERVAL = int(os.getenv("DEVICE_POLL_INTERVAL", "15"))

# Seconds a page object waits for an element before failing.
DEFAULT_TIMEOUT = int(os.getenv("ELEMENT_TIMEOUT", "20"))


def default_build_name() -> str:
    """Groups all tests of one run under a single Sauce Labs build.

    Uses the Azure DevOps build number when running in a pipeline, a timestamp otherwise.
    """
    if os.getenv("BUILD_BUILDNUMBER"):
        pipeline = os.getenv("BUILD_DEFINITIONNAME", "PawKnits")
        return f"{pipeline} #{os.environ['BUILD_BUILDNUMBER']}"
    return f"PawKnits Python - local - {datetime.now():%Y-%m-%d %H:%M:%S}"


def build_name() -> str:
    return os.getenv("SAUCE_BUILD_NAME") or default_build_name()


def dashboard_url(session_id: str) -> str:
    return f"https://app.eu-central-1.saucelabs.com/tests/{session_id}"
