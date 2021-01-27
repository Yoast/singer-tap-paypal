"""PayPal tap."""
# -*- coding: utf-8 -*-
import logging
from argparse import Namespace

import singer
from singer import utils
from singer.catalog import Catalog
from tap_paypal.discover import discover
from tap_paypal.sync import sync
from tap_paypal.paypal import PayPal


LOGGER: logging.RootLogger = singer.get_logger()
REQUIRED_CONFIG_KEYS: tuple = ('start_date', 'client_id', 'secret')


@utils.handle_top_exception(LOGGER)
def main() -> None:
    """Run tap."""
    # Parse command line arguments
    args: Namespace = utils.parse_args(REQUIRED_CONFIG_KEYS)

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
    )

    sync(paypal, args.state, catalog, args.config['start_date'])


if __name__ == '__main__':
    main()
