"""Cleaner functions."""


def clean_paypal_transactions(row: dict) -> dict:
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

    # transaction_info.available_balance.value
    if row.get('transaction_info', {}).get('available_balance', {}).get(
        'value',
    ):
        row['transaction_info']['available_balance']['value'] = (
            float(row['transaction_info']['available_balance']['value'])
        )
    # transaction_info.ending_balance.value
    if row.get('transaction_info', {}).get('ending_balance', {}).get(
        'value',
    ):
        row['transaction_info']['ending_balance']['value'] = (
            float(row['transaction_info']['ending_balance']['value'])
        )
    # transaction_info.transaction_amount.value
    if row.get('transaction_info', {}).get('transaction_amount', {}).get(
        'value',
    ):
        row['transaction_info']['transaction_amount']['value'] = (
            float(row['transaction_info']['transaction_amount']['value'])
        )
    # transaction_info.fee_amount.value
    if row.get('transaction_info', {}).get('fee_amount', {}).get(
        'value',
    ):
        row['transaction_info']['fee_amount']['value'] = (
            float(row['transaction_info']['fee_amount']['value'])
        )
    # transaction_info.insurance_amount.value
    if row.get('transaction_info', {}).get('insurance_amount', {}).get(
        'value',
    ):
        row['transaction_info']['insurance_amount']['value'] = (
            float(row['transaction_info']['insurance_amount']['value'])
        )
    # transaction_info.shipping_amount.value
    if row.get('transaction_info', {}).get('shipping_amount', {}).get(
        'value',
    ):
        row['transaction_info']['shipping_amount']['value'] = (
            float(row['transaction_info']['shipping_amount']['value'])
        )
    # transaction_info.sales_tax_amount.value
    if row.get('transaction_info', {}).get('sales_tax_amount', {}).get(
        'value',
    ):
        row['transaction_info']['sales_tax_amount']['value'] = (
            float(row['transaction_info']['sales_tax_amount']['value'])
        )
    # transaction_info.shipping_discount_amount.value
    if row.get('transaction_info', {}).get(
        'shipping_discount_amount', {}).get(
        'value',
    ):
        row['transaction_info']['shipping_discount_amount']['value'] = (
            float(
                row['transaction_info']['shipping_discount_amount']['value']
            )
        )

    # cart_info.item_unit_price.value
    if row.get('cart_info', {}).get('item_unit_price', {}).get(
        'value',
    ):
        row['cart_info']['item_unit_price']['value'] = (
            float(row['cart_info']['item_unit_price']['value'])
        )

    # tax_cart_info.amounts.item_unit_price.value
    if row.get('cart_info', {}).get('tax_amounts', {}).get(
        'value',
    ):
        row['cart_info']['tax_amounts']['value'] = (
            float(row['cart_info']['tax_amounts']['value'])
        )
    # cart_info.item_unit_price.value
    if row.get('cart_info', {}).get('total_item_amount', {}).get(
        'value',
    ):
        row['cart_info']['total_item_amount']['value'] = (
            float(row['cart_info']['total_item_amount']['value'])
        )

    for details in row.get('cart_info', {}).get('item_details', []):
        # cart_info.item_details[item_quantity]
        if details.get('item_quantity'):
            details['item_quantity'] = float(details['item_quantity'])
        # cart_info.item_details[item_unit_price.value]
        if details.get('item_unit_price', {}).get('value'):
            details['item_unit_price']['value'] = float(
                details['item_unit_price']['value']
            )
        # cart_info.item_details[item_amount.value]
        if details.get('item_amount', {}).get('value'):
            details['item_amount']['value'] = float(
                details['item_amount']['value']
            )
        # cart_info.item_details[total_item_amount.value]
        if details.get('total_item_amount', {}).get('value'):
            details['total_item_amount']['value'] = float(
                details['total_item_amount']['value']
            )
        # cart_info.item_details[tax_amounts[tax_amount.value]]
        for tax in details.get('tax_amounts', []):
            if tax.get('tax_amount', {}).get('value'):
                tax['tax_amount']['value'] = float(
                    tax['tax_amount']['value']
                )
        # cart_info.item_details[tax_percentage]
        if details.get('tax_percentage'):
            details['tax_percentage'] = float(details['tax_percentage'])

    for incentive in row.get('incentive_info', {}).get(
        'incentive_details',
        [],
    ):
        # incentive_details.incentive_amount.value
        if incentive.get('incentive_amount', {}).get('value'):
            incentive['incentive_amount']['value'] = float(
                incentive['incentive_amount']['value']
            )

    # These keys can be added to the schema, however it is currently
    # unknown which fields are available from the API.
    row.pop('store_info', None)
    row.pop('auction_info', None)
    return row
