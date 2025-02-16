import logging
import re
from datetime import datetime
from rupert.id_generator import (
    NyseBranchSeqGenerator, CHIXBranchSeqGenerator, ESPSeqGenerator,
    OSESeqGenerator, ClientOrderIdGenerator, BranchSeqIdGenerator,
    NumericClOrdIdGenerator13Digits, MonthClOrdIdGenerator,
    YMDClOrdIdGenerator, PSESeqGenerator, KSESeqGenerator,
    CompSubIDPrefixGenerator
)

class BMESeqGenerator:
    def __init__(self, s: str):
        if not s:
            raise ValueError("BMESeqGenerator: Invalid parameter")
        if len(s) > 20:
            raise ValueError("BMESeqGenerator: Prefix length should be less than or equal to 20")
        
        self.id_prefix = s.ljust(20, '0')
    
    def encode(self, to_be_encoded: int) -> str:
        return f"{self.id_prefix}{to_be_encoded:010d}"
    
    def decode(self, to_be_decoded: str) -> int:
        if not to_be_decoded or len(to_be_decoded) != 30:
            return -1
        
        num_part = to_be_decoded[20:]
        if not num_part.isdigit():
            return -1
        
        return int(num_part)

class NyseBranchSeqGenerator:
    def __init__(self, prefix: str):
        if not prefix or len(prefix) > 5:
            raise ValueError("NyseBranchSeqGenerator: Prefix length should be 5 or less")
        self.prefix = prefix.ljust(5, '0')
    
    def encode(self, sequence: int) -> str:
        return f"{self.prefix}{sequence:010d}"
    
    def decode(self, encoded: str) -> int:
        if not encoded or len(encoded) != 15:
            return -1
        sequence_part = encoded[5:]
        if not sequence_part.isdigit():
            return -1
        return int(sequence_part)

class OSESeqGenerator:
    def __init__(self, s: str):
        if not s:
            raise ValueError("OSESeqGenerator: Invalid parameter")
        if len(s) > 10:
            raise ValueError("OSESeqGenerator: Prefix length should be less than 10")

        self.id_prefix = s.ljust(10, '0')

    def encode(self, to_be_encoded: int) -> str:
        return f"{self.id_prefix}{to_be_encoded:010d}"

    def decode(self, to_be_decoded: str) -> int:
        if not to_be_decoded or len(to_be_decoded) != 20:
            return -1

        num_part = to_be_decoded[10:]
        if not num_part.isdigit():
            return -1

        return int(num_part)

class PSESeqGenerator:
    def __init__(self, s: str):
        if not s:
            raise ValueError("PSESeqGenerator: Invalid parameter")
        if len(s) > 2:
            raise ValueError("PSESeqGenerator: Prefix length should be less than or equal to 2")
        
        self.id_prefix = s.ljust(2, '0')
    
    def encode(self, to_be_encoded: int) -> str:
        return f"{self.id_prefix}{to_be_encoded:014d}"
    
    def decode(self, to_be_decoded: str) -> int:
        if not to_be_decoded or len(to_be_decoded) != 16:
            return -1
        
        num_part = to_be_decoded[2:]
        if not num_part.isdigit():
            return -1
        
        return int(num_part)

class YMDClOrdIdGenerator:
    def __init__(self, prop: str, seed: bool = True):
        self.uid = int(prop) if prop.isdigit() else 0
        self.seed = seed
        self.ymd_prefix = self._generate_ymd_prefix()
    
    def _generate_ymd_prefix(self) -> str:
        convert = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        today = datetime.utcnow()
        return f"{convert[today.year % 36]}{convert[today.month]}{convert[today.day]}-"
    
    def encode(self, to_be_encoded: int) -> str:
        if to_be_encoded >= 10**10:
            raise ValueError("Max ClOrdID exceeded")
        return f"{self.ymd_prefix}{self.uid + to_be_encoded}"
    
    def decode(self, to_be_decoded: str) -> int:
        return int(to_be_decoded[4:]) - self.uid

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
                "INT32": NumericClOrdIdGenerator,
                "Numeric13": NumericClOrdIdGenerator,
                "Monthly": MonthClOrdIdGenerator,
                "YMD": YMDClOrdIdGenerator,
                "Numeric14": NumericClOrdIdGenerator,
                "CompIDSubID": lambda prop, config: CompSubIDPrefixGenerator(prop, config),
                "BME": BMESeqGenerator,
            }

            generator_class = generator_map.get(protocol_var)
            if generator_class:
                return generator_class(prop) if protocol_var != "CompIDSubID" else generator_class(prop, config)
            
        except Exception as ex:
            logging.fatal(f"IdGeneratorFactory.create_client_order_id_generator({protocol_var}, {prop}): returns None due to exception {ex}")
        
        return None
