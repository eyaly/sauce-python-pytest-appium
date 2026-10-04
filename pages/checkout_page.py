from pages.base_page import BasePage, by_tag, parse_price


class CheckoutPage(BasePage):
    SCREEN = by_tag("checkout_screen")
    TOTAL = by_tag("checkout_total")
    NAME = by_tag("checkout_name")
    ADDRESS = by_tag("checkout_address")
    CARD_NUMBER = by_tag("checkout_card_number")
    EXPIRY = by_tag("checkout_expiry")
    CVV = by_tag("checkout_cvv")
    PAY_BUTTON = by_tag("pay_button")
    PAYMENT_ERROR = by_tag("payment_error")

    def wait_until_loaded(self) -> "CheckoutPage":
        self.find(self.SCREEN)
        return self

    def total(self) -> int:
        return parse_price(self.text_of(self.TOTAL))

    def fill_shipping(self, name: str, address: str) -> "CheckoutPage":
        self.scroll_to("checkout_name")
        self.type(self.NAME, name)
        self.type(self.ADDRESS, address)
        self.hide_keyboard()
        return self

    def enter_card(self, number: str, expiry: str = "12/30", cvv: str = "123") -> "CheckoutPage":
        """The form is prefilled with the approved demo card; overwrite it."""
        self.scroll_to("checkout_card_number")
        self.type(self.CARD_NUMBER, number)
        self.type(self.EXPIRY, expiry)
        self.type(self.CVV, cvv)
        self.hide_keyboard()
        return self

    def pay(self) -> "CheckoutPage":
        self.hide_keyboard()
        self.scroll_to("pay_button")
        self.tap(self.PAY_BUTTON)
        return self

    def place_order(self):
        """Pay and wait for the confirmation screen (the demo gateway takes ~1.5s)."""
        from pages.order_complete_page import OrderCompletePage

        self.pay()
        return OrderCompletePage(self.driver).wait_until_loaded()

    def payment_error(self) -> str:
        """Appears just above the Pay button once the demo gateway answers (~1.5s)."""
        return self.text_of(self.PAYMENT_ERROR)
