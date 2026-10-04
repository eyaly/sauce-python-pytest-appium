"""Shared helpers for all page objects: locating, waiting, tapping, typing, scrolling."""

import re

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings


def by_tag(tag: str) -> tuple[str, str]:
    """Locator for a Jetpack Compose testTag.

    The app enables `testTagsAsResourceId`, so each testTag is exposed as an Android
    resource-id without a package prefix. UiSelector matches it exactly; a plain
    `AppiumBy.ID` would prepend the app package ("com.pawknits.demo:id/...") and miss.
    """
    return AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().resourceId("{tag}")'


def parse_price(text: str) -> int:
    """'$55.00' or 'Charged $55.00 (demo)' -> 55"""
    match = re.search(r"\$(\d+)", text)
    if not match:
        raise ValueError(f"No price in {text!r}")
    return int(match.group(1))


class BasePage:
    def __init__(self, driver, timeout: int = settings.DEFAULT_TIMEOUT):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def find(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def tap(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def type(self, locator, text: str):
        """Replace the field's text. On Compose fields `clear()` is a no-op and
        `send_keys()` appends, so use UiAutomator2's replace command instead."""
        element = self.find(locator)
        self.driver.execute_script("mobile: replaceElementValue", {"elementId": element.id, "text": text})

    def text_of(self, locator) -> str:
        return self.find(locator).text

    def is_displayed(self, locator, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def is_gone(self, locator, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def scroll_to(self, tag: str, max_swipes: int = 12):
        """Scroll down until the element with this testTag is comfortably on screen.

        Uses the `mobile: scrollGesture` command, which works reliably with Compose lazy
        lists (UiScrollable.scrollIntoView does not). The element must end up in the upper
        80% of the scrollable area so bottom overlays (snackbars) don't cover it.
        """
        target = by_tag(tag)
        for _ in range(max_swipes + 1):
            container = self._scrollable()
            if container is None:
                return  # nothing to scroll: the element is either visible or absent
            box = container.rect
            comfort_line = box["y"] + box["height"] * 0.8
            elements = self.driver.find_elements(*target)
            if elements and elements[0].is_displayed():
                el_box = elements[0].rect
                if el_box["y"] + el_box["height"] <= comfort_line:
                    return
            percent = 0.3 if elements else 0.7  # nudge if already partly visible
            before = self.driver.page_source
            # The gesture's return value is unreliable here (a collapsing top app bar
            # absorbs the first swipe and it reports "end of list"), so detect the end
            # by checking whether the screen actually changed.
            self.driver.execute_script("mobile: scrollGesture", {
                "elementId": container.id, "direction": "down", "percent": percent,
                "speed": 1500,  # slow enough not to fling past the target
            })
            if self.driver.page_source == before:
                return  # reached the end of the list
        raise NoSuchElementException(f"Could not scroll to '{tag}' after {max_swipes} swipes")

    def _scrollable(self):
        found = self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().scrollable(true)")
        return found[0] if found else None

    def hide_keyboard(self):
        # Guarded: on Android, hide_keyboard() without a keyboard can act as a Back press.
        if self.driver.is_keyboard_shown():
            self.driver.hide_keyboard()
