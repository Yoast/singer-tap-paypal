"""PayPal API Client."""
# -*- coding: utf-8 -*-

from typing import Optional
from datetime import datetime, timedelta, timezone
import httpx
from pprint import pprint
from types import MappingProxyType
import singer
import dateutil.parser
import dateutil.rrule


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

        self.token = response_data.get('access_token')

        # Set experation date for tokenn
        expires_in: int = response_data.get('expires_in', 0)
        self.token_expires = now + timedelta(expires_in)

        self._create_headers()

        self.logger.info(
            f"Authentication succesfull (appid: {response_data.get('app_id')})"
        )

    def paypal_transactions(self, **kwargs: dict) -> list:
        if 'start_date' not in kwargs:
            raise ValueError('start_date required')

        # Set input date and output date
        start_date: datetime = dateutil.parser.isoparse(kwargs['start_date'])
        end_date: datetime = datetime.now(timezone.utc).replace(microsecond=0)

        # Extra kwargs will be converted to parameters in the API requests
        # start_date is parsed into batches, thus we remove it from the kwargs
        kwargs.pop('start_date', None)

        # The difference between start_date and end_date can max be 31 days
        # Split up the requests in weekly batches
        batches = dateutil.rrule.rrule(
            dateutil.rrule.WEEKLY, 
            dtstart=start_date,
            until=end_date,
        )

        total_batches: int = len(list(batches))
        self.logger.info(f'Total weekly batches: {total_batches}')

        current_batch: int = 0

        # Batches contains all start_dates, the end_date is 6 days 23:59 later
        for start_date_batch in batches:
            end_date_batch = start_date_batch + timedelta(days=7, seconds=-1)

            # Prevent the end_date from going into the future
            if end_date_batch > end_date:
                end_date_batch = end_date

            # Convert the datetimes to date formats the api expects
            start_date_str: str = self._date_to_paypal_format(start_date_batch)
            end_date_str: str = self._date_to_paypal_format(end_date_batch)

            current_batch += 1

            self.logger.info(
                f'Parsing batch {current_batch}: {start_date_str} <--> '
                f'{end_date_str}')
 

            # Default parameters send with each request
            fixed_params: dict = {
                'fields': 'all',
                'page_size': 100,
                'page': 1,
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

            # Request more pages when there are available
            while page < total_pages:
                # Update current page
                page += 1
                params['page'] = page

                response: httpx._models.Response = httpx.get(  # noqa: WPS437
                    url,
                    headers=self.headers,
                    params=params,
                )
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
                transactions: list = response_data.get('transactions_details', [])
                for transaction in transactions:
                    yield transactions

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
