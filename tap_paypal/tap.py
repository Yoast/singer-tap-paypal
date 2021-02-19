"""PayPal tap."""
# -*- coding: utf-8 -*-
import logging
from argparse import Namespace

import pkg_resources
from singer import get_logger, utils
from singer.catalog import Catalog

from tap_paypal.discover import discover
from tap_paypal.paypal import PayPal
from tap_paypal.sync import sync

VERSION: str = pkg_resources.get_distribution('tap-paypal').version
LOGGER: logging.RootLogger = get_logger()
REQUIRED_CONFIG_KEYS: tuple = ('start_date', 'client_id', 'secret')


@utils.handle_top_exception(LOGGER)
def main() -> None:
    """Run tap."""
    # Parse command line arguments
    args: Namespace = utils.parse_args(REQUIRED_CONFIG_KEYS)

    LOGGER.info(f'>>> Running tap-paypal v{VERSION}')

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog: Catalog = discover()
        catalog.dump()
        return

    # Otherwise run in sync mode
    if args.catalog:
        # Load command line catalog
        catalog = args.catalog
    else:
        # Loadt the  catalog
        catalog = discover()

    # Initialize PayPal client
    paypal: PayPal = PayPal(
        args.config['client_id'],
        args.config['secret'],
        args.config.get('sandbox', False),
    )

    sync(paypal, args.state, catalog, args.config['start_date'])


if __name__ == '__main__':
    main()
