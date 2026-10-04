from pages.base_page import BasePage, by_tag


class LoginPage(BasePage):
    USERNAME = by_tag("login_username")
    PASSWORD = by_tag("login_password")
    LOGIN_BUTTON = by_tag("login_button")
    ERROR = by_tag("login_error")

    def wait_until_loaded(self) -> "LoginPage":
        self.find(self.LOGIN_BUTTON)
        return self

    def submit(self, username: str, password: str) -> "LoginPage":
        """Fill in the form and tap Log in, without assuming the outcome."""
        self.type(self.USERNAME, username)
        self.type(self.PASSWORD, password)
        self.hide_keyboard()
        self.tap(self.LOGIN_BUTTON)
        return self

    def login(self, username: str, password: str):
        """Log in successfully and land on the shop."""
        from pages.shop_page import ShopPage

        self.submit(username, password)
        return ShopPage(self.driver).wait_until_loaded()

    def error_message(self) -> str:
        return self.text_of(self.ERROR)
