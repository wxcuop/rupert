import os
import re
from typing import Optional, Callable, Dict, List, Any

class TextOStream:
    def __init__(self, os):
        self.os = os
        self.tabs = ""

    def __lshift__(self, other):
        if isinstance(other, str):
            self.os.write(other)
        else:
            self.os.write(str(other))
        return self

    def indent(self):
        self.tabs += "    "

    def outdent(self):
        if len(self.tabs) >= 4:
            self.tabs = self.tabs[:-4]

    def tab(self):
        return self.tabs

class Node:
    def __init__(self, name: str, parent: Optional['Node'] = None):
        self.name = name
        self.parent = parent
        self.children: Dict[str, 'Node'] = {}
        self.index: List[str] = []
        self.valid = True

    @staticmethod
    def create_from_file(filename: str) -> 'Node':
        with open(filename, 'r') as file:
            content = file.read()
        return Node.create_from_string(content)

    @staticmethod
    def create_from_string(content: str) -> 'Node':
        content = content.replace("@", "_")
        parsed_yaml = Node.yaml_to_dict(content)
        root_node = Node("<root>")
        root_node.traverse(parsed_yaml)
        return root_node

    @staticmethod
    def yaml_to_dict(yaml_str: str) -> dict:
        # Basic YAML to dict conversion using the JSON parser
        # Note: This is a simplistic approach and may not handle all YAML features
        yaml_str = re.sub(r'(\n|\A)(\s*-\s+)', r'\1- ', yaml_str)
        yaml_str = re.sub(r':\s+(\d+)', r': "\1"', yaml_str)
        yaml_str = re.sub(r'(?<!\n)\n(?!\n)', r',\n', yaml_str)
        yaml_str = re.sub(r'(\w+):\s*', r'"\1": ', yaml_str)
        yaml_str = re.sub(r'- ', r'"-', yaml_str)
        yaml_str = re.sub(r'(\n\s*)- ', r'\1"', yaml_str)
        yaml_str = '{' + yaml_str + '}'
        return json.loads(yaml_str)

    def traverse(self, node: Any):
        if isinstance(node, dict):
            for key, value in node.items():
                child = self.add_child(key)
                child.traverse(value)
        elif isinstance(node, list):
            for item in node:
                self.traverse(item)

    def name(self) -> str:
        return self.name

    def for_each_child(self, func: Callable[['Node'], None]):
        for child in self.children.values():
            func(child)

    def for_each_child_in_order(self, func: Callable[['Node'], None]):
        for name in self.index:
            func(self.children[name])

    def add_child(self, name: str) -> 'Node':
        if name not in self.children:
            self.children[name] = Node(name, self)
            self.index.append(name)
        return self.children[name]

    def get_child(self, name: str) -> 'Node':
        if name in self.children:
            return self.children[name]
        if "<any>" in self.children:
            return self.children["<any>"]
        raise KeyError("Child not found")

    def get_pathname(self) -> str:
        path = []
        node = self
        while node.parent:
            path.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(path))

    def get_parent(self) -> Optional['Node']:
        return self.parent

    def get_depth(self) -> int:
        depth = 0
        node = self.parent
        while node:
            depth += 1
            node = node.parent
        return depth

    def validate(self, node: 'Node') -> 'Report':
        report = Report()
        if self.name == "<any>":
            return report
        node.for_each_child(lambda child: self._validate_child(child, report))
        return report

    def _validate_child(self, child: 'Node', report: 'Report'):
        try:
            master_child = self.get_child(child.name)
            report += master_child.validate(child)
        except KeyError:
            child.set_invalid()
            report.add_violation(child.get_pathname())

    def set_invalid(self):
        self.valid = False

    def is_valid(self) -> bool:
        return self.valid

    def __str__(self):
        return self._to_string(TextOStream(self.os))

    def _to_string(self, os: TextOStream) -> str:
        os << ("[ ]" if self.is_valid() else "[!]") << os.tab() << self.name << '\n'
        os.indent()
        self.for_each_child_in_order(lambda child: os << child._to_string(os))
        os.outdent()
        return os.os.getvalue()

class Report:
    def __init__(self, exception: str = ""):
        self.violations = []
        self.exception = exception

    def add_violation(self, path: str):
        self.violations.append(path)

    def for_each_violation(self, func: Callable[[str], None]):
        for violation in self.violations:
            func(violation)

    def ok(self) -> bool:
        return not self.violations and not self.exception

    def is_exception(self) -> bool:
        return bool(self.exception)

    def release_exception_if_present(self):
        if self.exception:
            raise RuntimeError(self.exception)

    def is_path_ok(self, path: List[str]) -> bool:
        path_str = "/" + "/".join(path)
        return path_str not in self.violations

    def get_violations_count(self) -> int:
        return len(self.violations)

    def get_exception(self) -> str:
        return self.exception

    def __iadd__(self, other: 'Report'):
        self.violations.extend(other.violations)
        return self

def check(filename: str) -> Report:
    try:
        node = Node.create_from_file(filename)
        reference_yaml = """
            # Add your reference YAML here
        """
        master = Node.create_from_string(reference_yaml)
        return master.validate(node)
    except Exception as ex:
        return Report(str(ex))

# Example usage
if __name__ == "__main__":
    report = check("example.yaml")
    print(report)
