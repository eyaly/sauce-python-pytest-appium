from pages.base_page import BasePage, by_tag, parse_price


class CartPage(BasePage):
    SCREEN = by_tag("cart_screen")
    TOTAL = by_tag("cart_total")
    CHECKOUT_BUTTON = by_tag("checkout_button")
    EMPTY_MESSAGE = by_tag("cart_empty")
    BACK_BUTTON = by_tag("back_button")

    def wait_until_loaded(self) -> "CartPage":
        self.find(self.SCREEN)
        return self

    def has_item(self, product_id: int) -> bool:
        return self.is_displayed(by_tag(f"cart_item_{product_id}"), timeout=2)

    def item_removed(self, product_id: int) -> bool:
        return self.is_gone(by_tag(f"cart_item_{product_id}"))

    def quantity(self, product_id: int) -> int:
        return int(self.text_of(by_tag(f"cart_quantity_{product_id}")))

    def increment(self, product_id: int) -> "CartPage":
        self.tap(by_tag(f"cart_increment_{product_id}"))
        return self

    def decrement(self, product_id: int) -> "CartPage":
        self.tap(by_tag(f"cart_decrement_{product_id}"))
        return self

    def remove(self, product_id: int) -> "CartPage":
        self.tap(by_tag(f"cart_remove_{product_id}"))
        return self

    def total(self) -> int:
        return parse_price(self.text_of(self.TOTAL))

    def is_empty(self) -> bool:
        return self.is_displayed(self.EMPTY_MESSAGE)

    def checkout(self):
        from pages.checkout_page import CheckoutPage

        self.tap(self.CHECKOUT_BUTTON)
        return CheckoutPage(self.driver).wait_until_loaded()

    def back_to_shop(self):
        from pages.shop_page import ShopPage

        self.tap(self.BACK_BUTTON)
        return ShopPage(self.driver).wait_until_loaded()
