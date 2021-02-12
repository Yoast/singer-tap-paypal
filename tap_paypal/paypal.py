"""PayPal API Client."""
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Generator, Optional

import dateutil.parser
import dateutil.rrule
import httpx
import singer

API_SCHEME: str = 'https://'
API_BASE_URL: str = 'api-m.paypal.com'
API_VERSION: str = 'v1'

API_PATH_OAUTH: str = 'oauth2/token'
API_PATH_TRANSACTIONS: str = 'reporting/transactions'

HEADERS: MappingProxyType = MappingProxyType({  # Frozen dictionary
    'Content-Type': 'application/json',
    'Authorization': 'Bearer :accesstoken:',
})


class PayPal(object):
    """PayPal API Client."""

    def __init__(self, client_id: str, secret: str) -> None:
        """Initialize client.

        Arguments:
            client_id {str} -- PayPal client id
            secret {str} -- PayPal secret
        """
        self.client_id: str = client_id
        self.secret: str = secret
        self.logger = singer.get_logger()

        self.token: Optional[str] = None
        self.token_expires: Optional[datetime] = None

        # Perform authentication during initialising
        self._authenticate()

    def _authenticate(self) -> None:
        """Generate a bearer access token."""
        url: str = (
            f'{API_SCHEME}{API_BASE_URL}/'
            f'{API_VERSION}/{API_PATH_OAUTH}'
        )
        headers: dict = {
            'Accept': 'application/json',
            'Accept-Language': 'en_US',
        }
        post_data: dict = {'grant_type': 'client_credentials'}

        now: datetime = datetime.utcnow()
        response: httpx._models.Response = httpx.post(  # noqa: WPS437
            url,
            headers=headers,
            data=post_data,
            auth=(self.client_id, self.secret)
        )

        # Raise error on 4xx and 5xxx
        response.raise_for_status()

        response_data: dict = response.json()

        # Save the token
        self.token = response_data.get('access_token')

        # Set experation date for token
        expires_in: int = response_data.get('expires_in', 0)
        self.token_expires = now + timedelta(expires_in)

        # Set up headers to use in API requests
        self._create_headers()

        self.logger.info(
            f"Authentication succesfull (appid: {response_data.get('app_id')})"
        )

    def paypal_transactions(
        self,
        **kwargs: dict,
    ) -> Generator[dict, None, None]:
        """PayPal transaction history.

        Raises:
            ValueError: When the parameter start_date is missing

        Yields:
            Generator[dict] -- Yields PayPal transactions
        """
        self.logger.info('Stream PayPal transactions')

        # Validate the start_date value exists
        start_date_input: str = str(kwargs.get('start_date', ''))

        if not start_date_input:
            raise ValueError('The parameter start_date is required.')

        # Set start date and end date
        start_date: datetime = dateutil.parser.isoparse(start_date_input)
        end_date: datetime = datetime.now(timezone.utc).replace(microsecond=0)

        self.logger.info(
            f'Retrieving transactions from {start_date} to {end_date}'
        )
        # Extra kwargs will be converted to parameters in the API requests
        # start_date is parsed into batches, thus we remove it from the kwargs
        kwargs.pop('start_date', None)

        # The difference between start_date and end_date can max be 31 days
        # Split up the requests into weekly batches
        batches: dateutil.rrule.rrule = dateutil.rrule.rrule(
            dateutil.rrule.WEEKLY,
            dtstart=start_date,
            until=end_date,
        )

        total_batches: int = len(list(batches))
        self.logger.info(f'Total weekly batches: {total_batches}')

        current_batch: int = 0

        # Batches contain all start_dates, the end_date is 6 days 23:59 later
        # E.g. 2021-01-01T00:00:00+0000 <--> 2021-01-07T23:59:59+0000
        for start_date_batch in batches:
            # Determine the end_date
            end_date_batch: datetime = (
                start_date_batch + timedelta(days=7, seconds=-1)
            )

            # Prevent the end_date from going into the future
            if end_date_batch > end_date:
                end_date_batch = end_date

            # Convert the datetimes to datetime formats the api expects
            start_date_str: str = self._date_to_paypal_format(start_date_batch)
            end_date_str: str = self._date_to_paypal_format(end_date_batch)

            current_batch += 1

            self.logger.info(
                f'Parsing batch {current_batch}: {start_date_str} <--> '
                f'{end_date_str}')

            # Default initial parameters send with each request
            fixed_params: dict = {
                'fields': 'all',
                'page_size': 100,
                'page': 1,  # Is updated in further requests
                'start_date': start_date_str,
                'end_date': end_date_str,
            }
            # Kwargs can be used to add aditional parameters to each requests
            params: dict = fixed_params | kwargs

            # Start of pagination
            page: int = 0
            total_pages: int = 1
            url: str = (
                f'{API_SCHEME}{API_BASE_URL}/'
                f'{API_VERSION}/{API_PATH_TRANSACTIONS}'
            )

            # Request more pages if there are available
            while page < total_pages:
                # Update current page
                page += 1
                params['page'] = page

                # Request data from the API
                response: httpx._models.Response = httpx.get(  # noqa: WPS437
                    url,
                    headers=self.headers,
                    params=params,
                )
                # Raise error on 4xx and 5xxx
                response.raise_for_status()

                response_data: dict = response.json()

                # Retrieve the current page details
                page = response_data.get('page', 1)
                total_pages = response_data.get('total_pages', 0)

                percentage_page: float = round((page / total_pages) * 100, 2)
                percentage_batch: float = round(
                    (current_batch / total_batches) * 100, 2,
                )

                self.logger.info(
                    f'Batch: {current_batch} of {total_batches} '
                    f'({percentage_batch}%), page: {page} of {total_pages} '
                    f'({percentage_page}%)'
                )

                # Yield every transaction in the response
                transactions: list = response_data.get(
                    'transaction_details',
                    [],
                )
                for transaction in transactions:
                    yield self._paypal_transactions_parse(transaction)

        self.logger.info('Finished: paypal_transactions')

    def _create_headers(self) -> None:
        """Create authenticationn headers for requests."""
        headers: dict = dict(HEADERS)
        headers['Authorization'] = headers['Authorization'].replace(
            ':accesstoken:',
            self.token,
        )
        self.headers = headers

    def _date_to_paypal_format(self, input_datetime: datetime) -> str:
        """Convert a datetime to the format that the PayPal api expects.

        Arguments:
            input_datetime {datetime} -- Input e.g. 2021-01-01 00:00:00+00:00

        Returns:
            str -- Converted datetime: 2021-01-01T00:00:00+0000
        """
        return ''.join(input_datetime.isoformat().rsplit(':', 1))

    def _paypal_transactions_parse(self, row: dict) -> dict:
        """Parse a row of transaction data and clean it.

        Arguments:
            row {dict} -- Input row

        Returns:
            dict -- Cleaned row
        """
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
        return row
