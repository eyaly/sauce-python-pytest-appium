from config.test_data import GREY_BLANKET, ORANGE_SWEATER, XMAS_SWEATER


def test_adding_products_updates_badge_and_total(shop_page):
    shop_page.add_to_cart(ORANGE_SWEATER.id).add_to_cart(XMAS_SWEATER.id)

    assert shop_page.wait_for_cart_count(2)

    cart = shop_page.open_cart()
    assert cart.has_item(ORANGE_SWEATER.id)
    assert cart.has_item(XMAS_SWEATER.id)
    assert cart.total() == ORANGE_SWEATER.price + XMAS_SWEATER.price


def test_change_quantity_and_remove_items(shop_page):
    cart = shop_page.add_to_cart(GREY_BLANKET.id).open_cart()

    cart.increment(GREY_BLANKET.id).increment(GREY_BLANKET.id)
    assert cart.quantity(GREY_BLANKET.id) == 3
    assert cart.total() == 3 * GREY_BLANKET.price

    cart.decrement(GREY_BLANKET.id)
    assert cart.quantity(GREY_BLANKET.id) == 2

    cart.remove(GREY_BLANKET.id)
    assert cart.item_removed(GREY_BLANKET.id)
    assert cart.is_empty()
