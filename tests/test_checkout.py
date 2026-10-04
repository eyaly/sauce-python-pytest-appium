import re

import pytest

from config.test_data import DECLINED_CARD, GREY_BLANKET, ORANGE_SWEATER, XMAS_SWEATER


@pytest.mark.smoke
def test_successful_checkout(shop_page):
    expected_total = ORANGE_SWEATER.price + XMAS_SWEATER.price

    cart = shop_page.add_to_cart(ORANGE_SWEATER.id).add_to_cart(XMAS_SWEATER.id).open_cart()
    checkout = cart.checkout()
    assert checkout.total() == expected_total

    confirmation = checkout.fill_shipping("Rex the Dog", "1 Bark Street, Dogtown").place_order()

    assert confirmation.title() == "Payment successful!"
    assert re.fullmatch(r"PK-\d{6}", confirmation.order_number())
    assert confirmation.amount() == expected_total

    shop = confirmation.continue_shopping()
    assert shop.cart_count() == 0


def test_declined_card_shows_error(shop_page):
    checkout = shop_page.add_to_cart(GREY_BLANKET.id).open_cart().checkout()

    checkout.fill_shipping("Rex the Dog", "1 Bark Street, Dogtown").enter_card(DECLINED_CARD).pay()

    assert "Your card was declined" in checkout.payment_error()
