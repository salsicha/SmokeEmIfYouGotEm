"""Read-only observation insertion for an exported Mantaflow liquid-step body."""
import ast


class Instrument(ast.NodeTransformer):
    def __init__(self, identifier):
        self.function = f'liquid_step_{identifier}'
        self.labels = []

    def visit_FunctionDef(self, node):
        if node.name != self.function:
            return node
        body = [ast.parse("capture('before_liquid_step')").body[0]]
        for index, statement in enumerate(node.body):
            body.append(statement)
            # Observe only top-level operations; do not change branches/calls.
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                text = ast.unparse(statement.value)
                if text.startswith('mantaMsg('):
                    continue
                label = f'{index:02d}: {text}'
                self.labels.append(label)
                body.append(ast.parse(f'capture({label!r})').body[0])
        node.body = body
        return node
