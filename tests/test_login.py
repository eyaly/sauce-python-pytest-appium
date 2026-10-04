import pytest

from config.test_data import LOCKED_USER, PASSWORD, VALID_USER


@pytest.mark.smoke
def test_valid_user_can_log_in(login_page):
    shop = login_page.login(VALID_USER, PASSWORD)

    assert shop.cart_count() == 0


def test_locked_out_user_sees_error(login_page):
    login_page.submit(LOCKED_USER, PASSWORD)

    assert login_page.error_message() == "Sorry, this account has been locked out."


def test_wrong_password_is_rejected(login_page):
    login_page.submit(VALID_USER, "wrong-password")

    assert login_page.error_message() == "Username and password do not match any user"
