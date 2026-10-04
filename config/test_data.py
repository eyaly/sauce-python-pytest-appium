"""Demo data hard-coded in the PawKnits app."""

from dataclasses import dataclass

VALID_USER = "doglover"
LOCKED_USER = "locked"
PASSWORD = "woof1234"

APPROVED_CARD = "4242 4242 4242 4242"
DECLINED_CARD = "4000 0000 0000 0002"


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    price: int


ORANGE_SWEATER = Product(1, "Orange sweater", 1)
GREY_BLANKET = Product(2, "Grey blanket", 89)
US_SCARF = Product(3, "US scarf", 79)
GREY_SWEATER = Product(4, "Grey sweater", 94)
YELLOW_SWEATER = Product(5, "Yellow sweater", 99)
GREEN_SWEATER = Product(6, "Green sweater", 65)
XMAS_SWEATER = Product(7, "Xmas sweater", 54)
GREY_RED_SWEATER = Product(8, "Grey-Red sweater", 83)
