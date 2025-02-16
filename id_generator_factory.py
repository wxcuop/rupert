import logging
import re
from datetime import datetime


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

class CHIXBranchSeqGenerator:
    def __init__(self, prefix: str):
        if not prefix or len(prefix) > 5:
            raise ValueError("CHIXBranchSeqGenerator: Prefix length should be 5 or less")
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

class ESPSeqGenerator:
    def __init__(self, s: str):
        if not s or len(s) > 5:
            raise ValueError("ESPSeqGenerator: Invalid parameter")
        self.id_prefix = s.ljust(5, '0')
    
    def encode(self, to_be_encoded: int) -> str:
        return f"{self.id_prefix}{to_be_encoded:010d}"
    
    def decode(self, to_be_decoded: str) -> int:
        if not to_be_decoded or len(to_be_decoded) != 15:
            return -1
        num_part = to_be_decoded[5:]
        if not num_part.isdigit():
            return -1
        return int(num_part)

class KSESeqGenerator:
    def __init__(self, s: str):
        if not s or len(s) > 5:
            raise ValueError("KSESeqGenerator: Invalid parameter")
        self.id_prefix = s.ljust(5, '0')
    
    def encode(self, to_be_encoded: int) -> str:
        return f"{self.id_prefix}{to_be_encoded:010d}"
    
    def decode(self, to_be_decoded: str) -> int:
        if not to_be_decoded or len(to_be_decoded) != 15:
            return -1
        num_part = to_be_decoded[5:]
        if not num_part.isdigit():
            return -1
        return int(num_part)
	    
class MonthClOrdIdGenerator:
    def __init__(self, eid: int, seed: bool = True):
        self.uid = eid
        self.day_index = self._init_day_index()
    
    def _init_day_index(self) -> str:
        mday = datetime.now().day
        if mday < 26:
            return chr(ord('A') + mday)
        else:
            return chr(ord('a') + mday - 26)
    
    def encode(self, to_be_encoded: int) -> str:
        max_clordid = 2**31
        if to_be_encoded >= max_clordid:
            raise ValueError("Max ClOrdID exceeded")
        return f"{self.day_index}{self.uid + to_be_encoded}"
    
    def decode(self, to_be_decoded: str) -> int:
        if not to_be_decoded or len(to_be_decoded) < 2:
            return -1
        return int(to_be_decoded[1:])

class NyseBranchSeqGenerator:
    RESERVED_BRANCH_CODES = {"HMQ", "QQQ", "RRR", "TTT", "YYY", "ZYX", "ZYY", "ZYZ", "ZZZ"}
    
    def __init__(self, branch_range: str):
        parts = branch_range.split('-')
        if len(parts) != 2:
            raise ValueError(f"Invalid branch range: {branch_range}")
        
        self.min_branch = self._get_branch_value(parts[0])
        self.max_branch = self._get_branch_value(parts[1])
        
        if self.min_branch is None or self.max_branch is None or self.min_branch > self.max_branch:
            raise ValueError(f"Invalid branch range: {branch_range}")
        
        if any(self.min_branch * 10000 == self._get_branch_value(code) * 10000 for code in self.RESERVED_BRANCH_CODES):
            raise ValueError(f"Starting branch code is reserved: {branch_range}")
        
        self.min_branch *= 10000
        self.max_branch = self.max_branch * 10000 + 9999
        self.available_ids = self.max_branch - self.min_branch
    
    def _get_branch_value(self, code: str) -> int:
        if len(code) > 3 or not code.isalpha() or any(c < 'A' or c > 'Z' for c in code):
            return None
        
        value = 0
        for c in code:
            value = value * 26 + (ord(c) - ord('A'))
        return value
    
    def get_nth_id(self, seq_no: int) -> int:
        if seq_no > self.available_ids:
            return -1
        return self.min_branch + seq_no
    
    def encode(self, to_be_encoded: int) -> str:
        if to_be_encoded > self.available_ids:
            return ""
        
        encoded_value = self.get_nth_id(to_be_encoded)
        branch_code = "".join(chr((encoded_value // (26**i)) % 26 + ord('A')) for i in range(2, -1, -1))
        num_code = str(encoded_value % 10000).zfill(4)
        return f"{branch_code} {num_code}/{datetime.now().strftime('%m%d%Y')}"
    
    def decode(self, to_be_decoded: str) -> int:
        try:
            branch_code, num_code = to_be_decoded[:3], to_be_decoded[4:8]
            branch_value = self._get_branch_value(branch_code)
            if branch_value is None:
                return -1
            return branch_value * 10000 + int(num_code)
        except Exception:
            return -1


class NumericClOrdIdGenerator13Digits:
    def __init__(self, s: str):
        if not s or len(s) > 3:
            raise ValueError("NumericClOrdIdGenerator13Digits: Invalid parameter")
        self.id_prefix = s.ljust(3, '0')
    
    def encode(self, to_be_encoded: int) -> str:
        return f"{self.id_prefix}{to_be_encoded:010d}"
    
    def decode(self, to_be_decoded: str) -> int:
        if not to_be_decoded or len(to_be_decoded) != 13:
            return -1
        num_part = to_be_decoded[3:]
        if not num_part.isdigit():
            return -1
        return int(num_part)
		
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
		
class CompSubIDPrefixGenerator:
    def __init__(self, prop: str, config=None):
        self.prop = prop
        self.config = config
    
    def encode(self, to_be_encoded: int) -> str:
        return f"{self.prop}{to_be_encoded:010d}"
    
    def decode(self, to_be_decoded: str) -> int:
        if not to_be_decoded or len(to_be_decoded) <= len(self.prop):
            return -1
        num_part = to_be_decoded[len(self.prop):]
        if not num_part.isdigit():
            return -1
        return int(num_part)

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
                "Numeric13": NumericClOrdIdGenerator13Digits,
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
