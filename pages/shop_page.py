from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage, by_tag


class ShopPage(BasePage):
    SCREEN = by_tag("shop_screen")
    CART_BUTTON = by_tag("cart_button")
    CART_BADGE = by_tag("cart_badge")
    LOGOUT_BUTTON = by_tag("logout_button")

    def wait_until_loaded(self) -> "ShopPage":
        self.find(self.SCREEN)
        return self

    def add_to_cart(self, product_id: int) -> "ShopPage":
        tag = f"add_to_cart_{product_id}"
        self.scroll_to(tag)  # products 5-8 are below the fold on most phones
        self.tap(by_tag(tag))
        return self

    def product_name(self, product_id: int) -> str:
        tag = f"product_name_{product_id}"
        self.scroll_to(tag)
        return self.text_of(by_tag(tag))

    def cart_count(self) -> int:
        """The badge is only rendered when the cart has items."""
        badges = self.driver.find_elements(*self.CART_BADGE)
        return int(badges[0].text) if badges else 0

    def wait_for_cart_count(self, expected: int, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(lambda _: self.cart_count() == expected)
            return True
        except TimeoutException:
            return False

    def open_cart(self):
        from pages.cart_page import CartPage

        self.tap(self.CART_BUTTON)
        return CartPage(self.driver).wait_until_loaded()

    def logout(self):
        from pages.login_page import LoginPage

        self.tap(self.LOGOUT_BUTTON)
        return LoginPage(self.driver).wait_until_loaded()
