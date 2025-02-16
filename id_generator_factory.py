import logging
from rupert.id_generator import (
    NyseBranchSeqGenerator, CHIXBranchSeqGenerator, ESPSeqGenerator,
    OSESeqGenerator, ClientOrderIdGenerator, BranchSeqIdGenerator,
    NumericClOrdIdGenerator13Digits, MonthClOrdIdGenerator,
    YMDClOrdIdGenerator, PSESeqGenerator, KSESeqGenerator,
    CompSubIDPrefixGenerator
)

class IdGeneratorFactory:
    @staticmethod
    def create_client_order_id_generator(protocol_var: str, prop: str, config=None):
        try:
            generator_map = {
                "NYSE": NyseBranchSeqGenerator,
                "CHIX": CHIXBranchSeqGenerator,
                "ESP": ESPSeqGenerator,
                "PSE": PSESeqGenerator,
                "POWERBASE": KSESeqGenerator,
                "ORION": KSESeqGenerator,  # same as KSE
                "CBOE": BranchSeqIdGenerator,
                "OSE": OSESeqGenerator,
                "INT32": NumericClOrdIdGenerator13Digits,
                "Numeric13": NumericClOrdIdGenerator13Digits,
                "Monthly": MonthClOrdIdGenerator,
                "YMD": YMDClOrdIdGenerator,
                "Numeric14": NumericClOrdIdGenerator13Digits,
                "CompIDSubID": lambda prop, config: CompSubIDPrefixGenerator(prop, config),
            }

            generator_class = generator_map.get(protocol_var)
            if generator_class:
                return generator_class(prop) if protocol_var != "CompIDSubID" else generator_class(prop, config)
            
        except Exception as ex:
            logging.fatal(f"IdGeneratorFactory.create_client_order_id_generator({protocol_var}, {prop}): returns None due to exception {ex}")
        
        return None
