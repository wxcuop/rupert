import logging

class CompSubIDPrefixGenerator:
    def __init__(self, prefix: str, config, length: int = 12):
        self.length = length
        self.uid = 0
        self.max_clord_id = 0
        self.init_(prefix, config)

    def init_(self, endpoint_id: str, config):
        sender_comp_id = config.get("senderCompID", "")
        sender_sub_id = config.get("senderSubID", "")
        combined_id = f"{sender_comp_id}{sender_sub_id}"

        try:
            self.uid = int(combined_id)
        except ValueError:
            logging.error(f"Couldn't convert {combined_id} to an integer")
            raise RuntimeError("Failed to initialize ID generator")

        prefix_digits = len(combined_id)
        self.max_clord_id = 10 ** (self.length - prefix_digits)
        self.uid *= self.max_clord_id

        logging.debug(f"Initialized numeric ClOrdID generator with UID prefix = [{self.uid}] max ClOrdID {self.max_clord_id}")

    def encode(self, to_be_encoded: int) -> str:
        if to_be_encoded >= self.max_clord_id:
            raise RuntimeError("Max ClOrdID exceeded")

        return str(self.uid + to_be_encoded)

    def decode(self, to_be_decoded: str) -> int:
        return int(to_be_decoded) - self.uid
