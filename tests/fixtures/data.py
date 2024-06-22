from tests.utils import get_content

PACK = {"height": 8, "length": 10, "weight_packed": 100, "width": 5}
PRICE = {"price_with_discount": 99.99, "price_without_discount": 119.99, "vat": "20%"}
MANUALLY_FILLED_SPEC = {
    "custom_properties": {"характеристика 1": "Состав: 92% Хлопок 8% Эластан"},
    "description": "Лучшее платье",
    "height": 100,
    "length": 100,
    "type": "Платье трикотажкое",
    "weight": 100,
    "width": 100,
}
IMAGE = {"order_num": 0, "image": get_content()}
DOCUMENT = {"name": "document_name", "document": get_content()}
