import pytest

from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions
from .utils import (
    checkout_create,
    checkout_delivery_method_update,
    raw_checkout_complete,
)


@pytest.mark.e2e
def test_should_not_be_able_to_make_purchase_with_no_payment_CORE_0113(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    warehouse_id, channel_id, channel_slug, shipping_method_id = prepare_shop(
        e2e_staff_api_client
    )

    product_variant_id = prepare_product(e2e_staff_api_client, warehouse_id, channel_id)

    # Step 1 - Create checkout.
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["deliveryMethod"] is None
    assert checkout_data["shippingMethod"] is None
    shipping_method_id = checkout_data["shippingMethods"][0]["id"]

    # Step 2 - Set shipping address and DeliveryMethod for checkout

    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 3 - Unable to complete checkout without payment
    order_data = raw_checkout_complete(e2e_not_logged_api_client, checkout_id)
    assert order_data["order"] is None
    errors = order_data["errors"]
    assert errors == [
        {
            "code": "CHECKOUT_NOT_FULLY_PAID",
            "field": None,
            "message": (
                "Provided payment methods can not cover the checkout's total amount"
            ),
        }
    ]
