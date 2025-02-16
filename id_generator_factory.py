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

class BranchSeqIdGenerator:
    """
    Branch sequence-based ID generation primarily used by NYSE and CBOE.
    
    NYSE: Not supported yet in this class.
    
    Needs to be configured in session with the following parameters:
      - fixVariant: CBOE
      - toVenueClordIdPrefixRange: A-G  # Provides the range between A to G
    """
    def __init__(self, branch_range: str, generator_type: str):
        parts = branch_range.split("-")
        if len(parts) == 1:
            parts.append("ZZZ")
        
        self.branch_start = self._format_branch(parts[0])
        self.branch_end = self._format_branch(parts[1])
        self.today_date = datetime.now().strftime("%Y%m%d")
        
        start_str = self.branch_start + "0001"
        end_str = self.branch_end + "9999"
        
        self.start = self._decode(start_str) - 1
        self.end = self._decode(end_str)
        self.type = generator_type
    
    def _format_branch(self, branch: str) -> str:
        branch = branch.strip().upper().ljust(3, 'A')
        return branch[:3]
    
    def _decode(self, encoded: str) -> int:
        if len(encoded) < 7:
            return -1
        
        branch_part = encoded[:3]
        seq_part = encoded[3:]
        
        if not branch_part.isalpha() or not seq_part.isdigit():
            return -1
        
        branch_value = 0
        for c in branch_part:
            branch_value = branch_value * 26 + (ord(c) - ord('A'))
        
        return branch_value * 10000 + int(seq_part)
    
    def get_mapped_seq_no(self, in_seq_no: int) -> int:
        num_skips = (in_seq_no - 1) // 9999
        return num_skips + in_seq_no + self.start
    
    def encode(self, to_be_encoded: int) -> str:
        if to_be_encoded <= 0:
            raise ValueError("Encoded ID should be > 0")
        
        mapped_seq_no = self.get_mapped_seq_no(to_be_encoded)
        if mapped_seq_no > self.end:
            raise ValueError("ID generator allocation ended")
        
        seq_part = str(mapped_seq_no % 10000).zfill(4)
        mapped_seq_no //= 10000
        
        branch_code = ""
        for _ in range(3):
            branch_code = chr(mapped_seq_no % 26 + ord('A')) + branch_code
            mapped_seq_no //= 26
        
        if self.type == "CBOE":
            return f"{branch_code}{seq_part}-{self.today_date}"
        return ""
    
    def decode(self, encoded_str: str) -> int:
        return self._decode(encoded_str)

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

class NumericClOrdIdGenerator:
    TRAITS = {
        10: {"max_clordid": 10_000_000, "endpoint_modulo": 100, "time_divisor": 28800},
        11: {"max_clordid": 10_000_000, "endpoint_modulo": 1000, "time_divisor": 9600},
        12: {"max_clordid": 10_000_000, "endpoint_modulo": 10000, "time_divisor": 9600},
        13: {"max_clordid": 100_000_000, "endpoint_modulo": 10000, "time_divisor": 9600},
        14: {"max_clordid": 1_000_000_000, "endpoint_modulo": 10000, "time_divisor": 9600},
    }
    
    def __init__(self, eid: int, length: int = 10, seed: bool = True):
        if length not in self.TRAITS:
            raise ValueError("Unsupported ClOrdID length")
        
        self.length = length
        self.seed = seed
        self.uid = self._init_uid(eid)
    
    def _init_uid(self, eid: int) -> int:
        traits = self.TRAITS[self.length]
        uid = eid % traits["endpoint_modulo"]
        
        segment = 1
        if self.seed:
            segment = int(time.time()) % 86400 // traits["time_divisor"] + 1
            if segment == 5:
                segment += 1
        
        uid += segment * traits["endpoint_modulo"]
        uid *= traits["max_clordid"]
        return uid
    
    def encode(self, to_be_encoded: int) -> str:
        if to_be_encoded >= self.TRAITS[self.length]["max_clordid"]:
            raise ValueError("Max ClOrdID exceeded")
        return str(self.uid + to_be_encoded)
    
    def decode(self, to_be_decoded: str) -> int:
        return int(to_be_decoded) - self.uid

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
