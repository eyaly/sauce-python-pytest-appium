"""Appium capabilities for each Sauce Labs real device. Every test runs once per entry.

The key ("pixel", ...) is the id used with --devices. `appium:deviceName` is a regex:
Sauce Labs picks any free phone that matches (dynamic allocation).

Only per-run values are added at runtime by the `driver` fixture in conftest.py:
sauce:options.username / accessKey (never hard-code credentials), build, and name (the test name).
"""

CAPABILITIES = {
    "pixel": {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": "Google.*",
        "appium:platformVersion": "17",
        "appium:app": "storage:filename=PawKnits.apk",
        "sauce:options": {
            "appiumVersion": "latest",
            "phoneOnly": True,
            "tags": ["python", "pytest", "pawknits"],
        },
    },
    "samsung": {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": "Samsung.*",
        "appium:platformVersion": "16",
        "appium:app": "storage:filename=PawKnits.apk",
        "sauce:options": {
            "appiumVersion": "latest",
            "phoneOnly": True,
            "tags": ["python", "pytest", "pawknits"],
        },
    },
    "android-14": {
        "platformName": "Android",
        "appium:automationName": "UiAutomator2",
        "appium:deviceName": ".*",
        "appium:platformVersion": "14",
        "appium:app": "storage:filename=PawKnits.apk",
        "sauce:options": {
            "appiumVersion": "latest",
            "phoneOnly": True,
            "tags": ["python", "pytest", "pawknits"],
        },
    },
}
