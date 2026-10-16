"""Shared helpers for all page objects: locating, waiting, tapping, typing, scrolling.

The same page objects drive Android and iOS: both apps use the same element ids
(Compose testTags on Android, accessibilityIdentifiers on iOS).
"""

import re

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings


TAG = "tag"  # placeholder strategy, turned into a real locator by BasePage.locator()


def by_tag(tag: str) -> tuple[str, str]:
    """Locator for an element id that both apps share, e.g. by_tag("login_button").

    Page objects are platform-neutral, so the real strategy is picked when the locator
    is used, by BasePage.locator().
    """
    return TAG, tag


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
        self.ios = driver.capabilities.get("platformName", "").lower() == "ios"

    def locator(self, locator) -> tuple[str, str]:
        """Turn by_tag("x") into a real locator for this platform. Other locators pass through.

        Android: the app enables `testTagsAsResourceId`, so each testTag is a resource-id
        without a package prefix. UiSelector matches it exactly; a plain `AppiumBy.ID` would
        prepend the app package ("com.pawknits.demo:id/...") and miss.
        iOS: the tag is the element's accessibilityIdentifier, i.e. its accessibility id.
        """
        by, value = locator
        if by != TAG:
            return locator
        if self.ios:
            return AppiumBy.ACCESSIBILITY_ID, value
        return AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().resourceId("{value}")'

    def find(self, locator):
        return self.wait.until(EC.visibility_of_element_located(self.locator(locator)))

    def find_all(self, locator) -> list:
        """All matching elements right now, without waiting (empty list if none)."""
        return self.driver.find_elements(*self.locator(locator))

    def tap(self, locator):
        self.wait.until(EC.element_to_be_clickable(self.locator(locator))).click()

    def type(self, locator, text: str):
        """Replace the field's text."""
        element = self.find(locator)
        if self.ios:
            element.clear()
            element.send_keys(text)
            # The keyboard's "Done" toolbar covers the next field, so close it after each field.
            self._tap_keyboard_done()
        else:
            # On Compose fields `clear()` is a no-op and `send_keys()` appends,
            # so use UiAutomator2's replace command instead.
            self.driver.execute_script("mobile: replaceElementValue", {"elementId": element.id, "text": text})

    def text_of(self, locator) -> str:
        return self.find(locator).text

    def is_displayed(self, locator, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(self.locator(locator)))
            return True
        except TimeoutException:
            return False

    def is_gone(self, locator, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located(self.locator(locator)))
            return True
        except TimeoutException:
            return False

    def scroll_to(self, tag: str, max_swipes: int = 12):
        """Scroll down until the element with this testTag is comfortably on screen.

        Swipes and checks after each swipe, because lazy lists (Compose LazyColumn, SwiftUI
        LazyVGrid) only create items once they're near the screen. The element must end up
        in the upper 80% of the scrollable area so bottom overlays (snackbars) don't cover it.
        """
        target = by_tag(tag)
        for _ in range(max_swipes + 1):
            container = self._scrollable()
            if container is None:
                return  # nothing to scroll: the element is either visible or absent
            box = container.rect
            comfort_line = box["y"] + box["height"] * 0.8
            elements = self.find_all(target)
            if elements and elements[0].is_displayed():
                el_box = elements[0].rect
                if el_box["y"] + el_box["height"] <= comfort_line:
                    return
            percent = 0.3 if elements else 0.7  # nudge if already partly visible
            before = self.driver.page_source
            # The gesture's return value is unreliable here (a collapsing top app bar
            # absorbs the first swipe and it reports "end of list"), so detect the end
            # by checking whether the screen actually changed.
            self._swipe_up(container, percent)
            if self.driver.page_source == before:
                return  # reached the end of the list
        raise NoSuchElementException(f"Could not scroll to '{tag}' after {max_swipes} swipes")

    def _swipe_up(self, container, percent: float):
        """Scroll the content down by `percent` of the container's height."""
        if self.ios:
            # A slow drag inside the scroll view: scrolls without flinging past the target.
            box = container.rect
            x = box["x"] + box["width"] // 2
            start_y = box["y"] + int(box["height"] * 0.8)
            self.driver.swipe(x, start_y, x, start_y - int(box["height"] * percent), 800)
        else:
            # `mobile: scrollGesture` works reliably with Compose lazy lists
            # (UiScrollable.scrollIntoView does not).
            self.driver.execute_script("mobile: scrollGesture", {
                "elementId": container.id, "direction": "down", "percent": percent,
                "speed": 1500,  # slow enough not to fling past the target
            })

    def _scrollable(self):
        if self.ios:
            found = self.driver.find_elements(AppiumBy.CLASS_NAME, "XCUIElementTypeScrollView")
        else:
            found = self.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().scrollable(true)")
        return found[0] if found else None

    def hide_keyboard(self):
        # Guarded: on Android, hide_keyboard() without a keyboard can act as a Back press.
        if not self.driver.is_keyboard_shown():
            return
        if self.ios:
            # iOS number pads have no Return key; the app adds a "Done" button above the keyboard.
            self._tap_keyboard_done()
        else:
            self.driver.hide_keyboard()

    def _tap_keyboard_done(self):
        """iOS: tap the app's "Done" button above the keyboard, if this screen has one."""
        done = self.find_all(by_tag("keyboard_done"))
        if done and done[0].is_displayed():
            done[0].click()
