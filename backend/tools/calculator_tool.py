from tools.base_tool import BaseTool
import ast
import operator

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluates basic math expressions safely. Provide expression as a string. Good for exact arithmetic."
    parameters = {
        "expression": "Math expression string to evaluate, e.g. '2 + 2 * 4'"
    }

    def execute(self, expression: str = "", **kwargs) -> str:
        try:
            allowed_operators = {
                ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                ast.Div: operator.truediv, ast.Pow: operator.pow, ast.BitXor: operator.xor,
                ast.USub: operator.neg
            }
            def eval_expr(node):
                if isinstance(node, ast.Num): return node.n
                elif isinstance(node, ast.BinOp):
                    return allowed_operators[type(node.op)](eval_expr(node.left), eval_expr(node.right))
                elif isinstance(node, ast.UnaryOp):
                    return allowed_operators[type(node.op)](eval_expr(node.operand))
                else:
                    raise TypeError(node)
            result = eval_expr(ast.parse(expression, mode='eval').body)
            return str(result)
        except Exception as e:
            return f"Calculator error: {e}"
