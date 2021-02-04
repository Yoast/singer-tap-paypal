"""PayPal API Client."""
# -*- coding: utf-8 -*-

from typing import Optional
from datetime import datetime, timedelta
import httpx
from pprint import pprint
from types import MappingProxyType
import singer


API_SCHEME: str = 'https://'
API_BASE_URL: str = 'api-m.sandbox.paypal.com'
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

        # Initial params
        FIXED_PARAMS: MappingProxyType = MappingProxyType({
            'fields': 'all',
            'page_size': 100,
            'page': 1,
        })

        # Merge fixed params with input params
        params = dict(FIXED_PARAMS) | kwargs

        page: int = 0
        total_pages: int = 1
        url: str = (
            f'{API_SCHEME}{API_BASE_URL}/'
            f'{API_VERSION}/{API_PATH_TRANSACTIONS}'
        )

        # Pagination
        while page < total_pages:
            page += 1
            params['page'] = page

            response: httpx._models.Response = httpx.get(  # noqa: WPS437
                url,
                headers=self.headers,
                params=params,
            )

            response.raise_for_status()

            response_data: dict = response.json()

            pprint(response_data)

            page = response_data.get('page', 1)
            total_pages = response_data.get('total_pages', 0)

            transactions: list = response_data.get('transactions_details', [])
            for transaction in transactions:
                yield transactions

    def _create_headers(self) -> None:
        """Create authenticationn headers for requests."""
        headers: dict = dict(HEADERS)
        headers['Authorization'] = headers['Authorization'].replace(
            ':accesstoken:',
            self.token,
        )
        self.headers = headers
