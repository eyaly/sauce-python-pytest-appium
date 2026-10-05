"""pytest wiring: device parametrization, the Sauce Labs driver fixture, and result reporting."""

import base64
import copy
import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options

from config import settings
from config.capabilities import CAPABILITIES
from config.test_data import PASSWORD, VALID_USER
from pages.login_page import LoginPage

log = logging.getLogger("sauce")


def pytest_addoption(parser):
    parser.addoption(
        "--devices",
        default=os.getenv("DEVICES", ""),
        help="Comma-separated device ids from config/capabilities.py (default: all). Env: DEVICES",
    )


def pytest_configure(config):
    # Fix the build name once in the main process so every xdist worker
    # (they inherit the environment) reports into the same Sauce Labs build.
    if not hasattr(config, "workerinput"):
        os.environ.setdefault("SAUCE_BUILD_NAME", settings.default_build_name())


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Before any Appium driver is created, make sure every selected device has a free phone.

    Runs once in the main process (before xdist starts its workers), so a missing device
    stops the whole run cleanly instead of failing each test.
    """
    config = session.config
    if hasattr(config, "workerinput") or config.option.collectonly:
        return
    if not (settings.SAUCE_USERNAME and settings.SAUCE_ACCESS_KEY):
        return  # the driver fixture reports the missing credentials
    say = config.pluginmanager.get_plugin("terminalreporter").write_line
    for device in _selected_devices(config):
        _wait_for_available_device(device, CAPABILITIES[device]["appium:deviceName"], say)


def _wait_for_available_device(device: str, device_name: str, say) -> None:
    """Poll the Sauce Labs device status API until a device matching `device_name` is AVAILABLE.

    Exits the pytest run if none frees up within settings.DEVICE_WAIT_TIMEOUT seconds.
    """
    deadline = time.monotonic() + settings.DEVICE_WAIT_TIMEOUT
    while True:
        available = _available_devices(device_name)
        if available:
            say(f"[{device}] available device(s) for '{device_name}': {', '.join(available[:5])}")
            return
        if time.monotonic() >= deadline:
            message = (f"[{device}] no available Sauce Labs device matching '{device_name}' "
                       f"after waiting {settings.DEVICE_WAIT_TIMEOUT}s - stopping the test run")
            log.error(message)
            pytest.exit(message, returncode=3)
        say(f"[{device}] no available device for '{device_name}' yet, "
            f"checking again in {settings.DEVICE_POLL_INTERVAL}s")
        time.sleep(settings.DEVICE_POLL_INTERVAL)


def _available_devices(device_name: str) -> list[str]:
    """Descriptors of devices matching `device_name` (regex) whose state is AVAILABLE.

    API: GET /rdc/v2/devices/status
    https://docs.saucelabs.com/dev/api/real-device-access/#tag/device-catalog/GET/devices/status
    """
    query = urllib.parse.urlencode({"deviceName": device_name, "state": "AVAILABLE"})
    token = base64.b64encode(f"{settings.SAUCE_USERNAME}:{settings.SAUCE_ACCESS_KEY}".encode()).decode()
    request = urllib.request.Request(f"{settings.RDC_API_URL}/devices/status?{query}",
                                     headers={"Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            devices = json.load(response).get("devices", [])
    except OSError as exc:  # network/HTTP error: treat as "not available yet" and keep polling
        log.warning("Device status API call failed: %s", exc)
        return []
    return [d["descriptor"] for d in devices if d.get("state") == "AVAILABLE"]


def _selected_devices(config) -> list[str]:
    wanted = [d.strip() for d in config.getoption("--devices").split(",") if d.strip()]
    if not wanted:
        return list(CAPABILITIES)
    unknown = [d for d in wanted if d not in CAPABILITIES]
    if unknown:
        raise pytest.UsageError(f"Unknown device id(s) {unknown}. Known: {list(CAPABILITIES)}")
    return wanted


def pytest_generate_tests(metafunc):
    """Run every test that uses `driver` once per device: test_x[pixel], test_x[samsung], ..."""
    if "device" in metafunc.fixturenames:
        devices = _selected_devices(metafunc.config)
        metafunc.parametrize("device", devices, ids=devices)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    # Keep each phase's report on the test item so the driver fixture can see
    # whether the test body passed when it tears down.
    report = yield
    setattr(item, f"rep_{report.when}", report)
    return report


@pytest.fixture
def driver(request, device):
    """A fresh Appium session on a Sauce Labs real device, closed after the test."""
    if not (settings.SAUCE_USERNAME and settings.SAUCE_ACCESS_KEY):
        pytest.fail("Set SAUCE_USERNAME and SAUCE_ACCESS_KEY environment variables")

    caps = copy.deepcopy(CAPABILITIES[device])
    caps["sauce:options"].update({
        "username": settings.SAUCE_USERNAME,
        "accessKey": settings.SAUCE_ACCESS_KEY,
        "build": settings.build_name(),
        "name": request.node.originalname,  # e.g. test_valid_user_can_log_in
    })
    drv = webdriver.Remote(settings.HUB_URL, options=UiAutomator2Options().load_capabilities(caps))
    job_url = settings.dashboard_url(drv.session_id)
    log.info("Sauce Labs job: %s", job_url)
    request.node.user_properties.append(("sauce_job_url", job_url))

    yield drv

    call_report = getattr(request.node, "rep_call", None)
    passed = call_report is not None and call_report.passed
    try:
        if not passed:
            _save_failure_artifacts(drv, request.node)
        drv.execute_script(f"sauce:job-result={'passed' if passed else 'failed'}")
    finally:
        drv.quit()


def _save_failure_artifacts(drv, node):
    """Screenshot + UI tree of the failing screen, kept in reports/failures/ (published by the CI)."""
    out_dir = Path("reports/failures")
    out_dir.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^\w.-]+", "_", node.name)
    try:
        drv.get_screenshot_as_file(str(out_dir / f"{name}.png"))
        (out_dir / f"{name}.xml").write_text(drv.page_source, encoding="utf-8")
    except Exception as exc:  # never hide the real test failure
        log.warning("Could not save failure artifacts: %s", exc)


@pytest.fixture
def login_page(driver) -> LoginPage:
    return LoginPage(driver).wait_until_loaded()


@pytest.fixture
def shop_page(login_page):
    """Start the test already logged in as the valid demo user."""
    return login_page.login(VALID_USER, PASSWORD)
