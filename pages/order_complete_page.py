from pages.base_page import BasePage, by_tag, parse_price


class OrderCompletePage(BasePage):
    SCREEN = by_tag("order_complete_screen")
    TITLE = by_tag("order_complete_title")
    ORDER_NUMBER = by_tag("order_number")
    AMOUNT = by_tag("order_amount")
    CONTINUE_BUTTON = by_tag("continue_shopping_button")

    def wait_until_loaded(self) -> "OrderCompletePage":
        self.find(self.SCREEN)
        return self

    def title(self) -> str:
        return self.text_of(self.TITLE)

    def order_number(self) -> str:
        """'Order PK-123456' -> 'PK-123456'"""
        return self.text_of(self.ORDER_NUMBER).removeprefix("Order ").strip()

    def amount(self) -> int:
        return parse_price(self.text_of(self.AMOUNT))

    def continue_shopping(self):
        from pages.shop_page import ShopPage

        self.tap(self.CONTINUE_BUTTON)
        return ShopPage(self.driver).wait_until_loaded()
