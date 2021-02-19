"""Streams metadata."""
# -*- coding: utf-8 -*-
from types import MappingProxyType

# Streams metadata
STREAMS: MappingProxyType = MappingProxyType({
    'paypal_transactions': {
        'key_properties': ['transaction_info', 'transaction_id'],
        'replication_method': 'INCREMENTAL',
        'replication_key': 'transaction_info.transaction_updated_date',
        'bookmark': 'start_date',
    },
})
