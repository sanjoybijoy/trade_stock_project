"""
Copyright (C) 2019 Interactive Brokers LLC. All rights reserved. This code is subject to the terms
and conditions of the IB API Non-Commercial License or the IB API Commercial License, as applicable.
"""

#from ibapi.enum_impl import Enum

"""
TickTypeEnum Implementation for IBKR API
"""

class Enum:
    def __init__(self, *sequential):
        self.enum_dict = {name: idx for idx, name in enumerate(sequential)}
        self.reverse_dict = {idx: name for idx, name in enumerate(sequential)}

    def to_str(self, value):
        return self.reverse_dict.get(value, "Unknown")

    def __getitem__(self, key):
        return self.enum_dict[key]

    def __contains__(self, key):
        return key in self.enum_dict

    def __iter__(self):
        return iter(self.enum_dict)

# TickType
TickTypeEnum = Enum(
    "BID",
    "BID_SIZE",
    "ASK",
    "ASK_SIZE",
    "LAST",
    "LAST_SIZE",
    "HIGH",
    "LOW",
    "VOLUME",
    "CLOSE",
    "BID_OPTION_COMPUTATION",
    "ASK_OPTION_COMPUTATION",
    "LAST_OPTION_COMPUTATION",
    "MODEL_OPTION",
    "OPEN",
    "LOW_13_WEEK",
    "HIGH_13_WEEK",
    "LOW_26_WEEK",
    "HIGH_26_WEEK",
    "LOW_52_WEEK",
    "HIGH_52_WEEK",
    "AVG_VOLUME",
    "OPEN_INTEREST",
    "OPTION_HISTORICAL_VOL",
    "OPTION_IMPLIED_VOL",
    "OPTION_BID_EXCH",
    "OPTION_ASK_EXCH",
    "OPTION_CALL_OPEN_INTEREST",
    "OPTION_PUT_OPEN_INTEREST",
    "OPTION_CALL_VOLUME",
    "OPTION_PUT_VOLUME"
)
