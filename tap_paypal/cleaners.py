"""Cleaner functions."""
# -*- coding: utf-8 -*-
from decimal import Decimal

from dateutil.parser import parse as parse_d


def clean_paypal_transactions(row: dict) -> dict:  # noqa: WPS 210,WPS231
    """Parse a row of transaction data and clean it.

    Arguments:
        row {dict} -- Input row

    Returns:
        dict -- Cleaned row
    """
    # Primary key must be top-level
    row['transaction_id'] = row.get('transaction_info', {}).get(
        'transaction_id',
    )

    # Transaction info
    t_info: dict = row.get('transaction_info', {})

    if t_info:
        # transaction_info.available_balance.value
        if t_info.get('available_balance', {}).get('value'):
            t_info['available_balance']['value'] = Decimal(
                t_info['available_balance']['value'],
            )

        # transaction_info.ending_balance.value
        if t_info.get('ending_balance', {}).get('value'):
            t_info['ending_balance']['value'] = Decimal(
                t_info['ending_balance']['value'],
            )

        # transaction_info.transaction_amount.value
        if t_info.get('transaction_amount', {}).get('value'):
            t_info['transaction_amount']['value'] = Decimal(
                t_info['transaction_amount']['value'],
            )

        # transaction_info.fee_amount.value
        if t_info.get('fee_amount', {}).get('value'):
            t_info['fee_amount']['value'] = Decimal(
                t_info['fee_amount']['value'],
            )

        # transaction_info.insurance_amount.value
        if t_info.get('insurance_amount', {}).get('value'):
            t_info['insurance_amount']['value'] = Decimal(
                t_info['insurance_amount']['value'],
            )

        # transaction_info.shipping_amount.value
        if t_info.get('shipping_amount', {}).get('value'):
            t_info['shipping_amount']['value'] = Decimal(
                t_info['shipping_amount']['value'],
            )

        # transaction_info.sales_tax_amount.value
        if t_info.get('sales_tax_amount', {}).get('value'):
            t_info['sales_tax_amount']['value'] = Decimal(
                t_info['sales_tax_amount']['value'],
            )

        # transaction_info.shipping_discount_amount.value
        if t_info.get('shipping_discount_amount', {}).get('value'):
            t_info['shipping_discount_amount']['value'] = Decimal(
                t_info['shipping_discount_amount']['value'],
            )

        # transaction_info.transaction_initiation_date
        if t_info.get('transaction_initiation_date'):
            t_info['transaction_initiation_date'] = parse_d(
                t_info['transaction_initiation_date'],
            ).isoformat()

        # transaction_info.transaction_updated_date
        if t_info.get('transaction_updated_date'):
            t_info['transaction_updated_date'] = parse_d(
                t_info['transaction_updated_date'],
            ).isoformat()

    # Cart info
    c_info: dict = row.get('cart_info', {})
    cart_all: list = c_info.get('item_details', [])

    for cart in cart_all:
        # cart_info.item_details.item_unit_price.value
        if cart.get('item_unit_price', {}).get('value'):
            cart['item_unit_price']['value'] = Decimal(
                cart['item_unit_price']['value'],
            )

        # cart_info.item_details.tax_amounts
        tax_amounts: list = cart.get('tax_amounts', [])

        for tax in tax_amounts:
            #  cart_info.item_details.tax_amounts.tax_amount.value
            if tax.get('tax_amount', {}).get('value'):
                tax['tax_amount']['value'] = Decimal(
                    tax['tax_amount']['value'],
                )

        # cart_info.item_details.item_amount.value
        if cart.get('item_amount', {}).get('value'):
            cart['item_amount']['value'] = Decimal(
                cart['item_amount']['value'],
            )

        # cart_info.item_details.total_item_amount.value
        if cart.get('total_item_amount', {}).get('value'):
            cart['total_item_amount']['value'] = Decimal(
                cart['total_item_amount']['value'],
            )

        # cart_info.item_details.tax_percentage
        if cart.get('tax_percentage'):
            cart['tax_percentage'] = Decimal(cart['tax_percentage'])

        # cart_info.item_details.item_quantity
        if cart.get('item_quantity'):
            cart['item_quantity'] = Decimal(cart['item_quantity'])

    # Incentive info
    i_info: dict = row.get('incentive_info', {})
    i_all: list = i_info.get('incentive_details', [])

    for inc in i_all:

        # incentive_info.incentive_details.incentive_amount.value
        if inc.get('incentive_amount', {}).get('value'):
            inc['incentive_amount']['value'] = Decimal(
                inc['incentive_amount']['value'],
            )

    # last_refreshed_datetime
    if row.get('last_refreshed_datetime'):
        row['last_refreshed_datetime'] = parse_d(
            row['last_refreshed_datetime'],
        ).isoformat()

    # These keys can be added to the schema, however it is currently
    # unknown which fields are available from the API.
    row.pop('store_info', None)
    row.pop('auction_info', None)
    return row
