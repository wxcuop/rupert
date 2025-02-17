import re
import json
from typing import List, Dict, Any, Union
from collections import deque

class ReadYAML:
    def __init__(self, source: Union[str, Any], is_file: bool = True):
        """
        Read yaml from a given stream or file and translate it to a property tree.

        :param source: Path to the file or stream from which to read the property tree.
        :param is_file: Flag to indicate if the source is a file path or stream.
        """
        if is_file:
            with open(source, 'r') as f:
                content = f.read()
        else:
            content = source
        
        self.root = self.yaml_to_dict(content)
        self._type_stack = deque()
        self._node_stack = deque()
        self._key_stack = deque()
        self._seq_arr = {}

    @staticmethod
    def yaml_to_dict(yaml_str: str) -> dict:
        # Convert YAML string to a JSON-compatible dictionary
        yaml_str = re.sub(r'(\n|\A)(\s*-\s+)', r'\1- ', yaml_str)
        yaml_str = re.sub(r':\s+(\d+)', r': "\1"', yaml_str)
        yaml_str = re.sub(r'(?<!\n)\n(?!\n)', r',\n', yaml_str)
        yaml_str = re.sub(r'(\w+):\s*', r'"\1": ', yaml_str)
        yaml_str = re.sub(r'- ', r'"-', yaml_str)
        yaml_str = re.sub(r'(\n\s*)- ', r'\1"', yaml_str)
        yaml_str = '{' + yaml_str + '}'
        return json.loads(yaml_str)

    @staticmethod
    def load(pt: Dict[str, Any], key: str, strings: List[str]) -> None:
        """
        Iterate over tree at specified path and store all found children.

        :param pt: Property tree
        :param key: Path
        :param strings: The found children.
        """
        strings.clear()
        keys = key.split('.')
        current = pt
        for k in keys:
            current = current.get(k, {})
        strings.extend(current.keys() if isinstance(current, dict) else current)

    @staticmethod
    def save(pt: Dict[str, Any], key: str, strings: List[str]) -> None:
        """
        Adds children at the given path.

        :param pt: Property tree
        :param key: Path
        :param strings: Vector of values.
        """
        keys = key.split('.')
        current = pt
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        if len(strings) > 1:
            current[keys[-1]] = strings
        elif strings:
            current[keys[-1]] = strings[0]

    def traverse(self, node: Any, depth: int = 0) -> None:
        """
        Traverse the YAML node and populate the property tree.

        :param node: YAML node
        :param depth: Current depth of the traversal
        """
        if isinstance(node, dict):
            self._type_stack.append('mapping')
            for key, value in node.items():
                self._key_stack.append(key)
                self.traverse(value, depth + 1)
                self._key_stack.pop()
            self._type_stack.pop()
        elif isinstance(node, list):
            self._type_stack.append('sequence')
            for item in node:
                self.traverse(item, depth + 1)
            self._type_stack.pop()
        else:
            self._type_stack.append('scalar')
            key = self._key_stack[-1] if self._key_stack else None
            if key:
                current = self._node_stack[-1] if self._node_stack else self._seq_arr
                current[key] = node
            self._type_stack.pop()

    def init(self) -> Dict[str, Any]:
        """
        Initialize the parsing process and return the property tree.

        :return: The property tree.
        """
        self.traverse(self.root)
        return self._seq_arr


# Example usage
if __name__ == "__main__":
    filepath = "example.yaml"
    reader = ReadYAML(filepath)
    pt = reader.init()
    print(pt)

    children = []
    ReadYAML.load(pt, 'some.path', children)
    print(children)

    new_children = ['child1', 'child2']
    ReadYAML.save(pt, 'some.path', new_children)
    print(pt)
``` ▋
