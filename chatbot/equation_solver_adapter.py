from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement

from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application
)
import matplotlib
matplotlib.use('Agg')

from sympy.plotting import plot
from sympy.printing.latex import latex
import re
import io
import base64

class EquationSolverAdapter(LogicAdapter):
    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)
        self.transformations = standard_transformations + (implicit_multiplication_application,)

    def can_process(self, statement):
        text = statement.text.lower().strip()
        return '=' in text or re.match(r'^\s*\d+\s*[\+\-\*/]\s*\d+\s*$', text)

    def process(self, statement, additional_response_selection_parameters=None):
        from sympy import symbols, Eq, solve, pretty, simplify, sin, cos, tan, ln, sqrt, exp, factor, expand
        text = statement.text.lower()
        text = text.replace("solve", "").strip()
        text = text.replace('^', '**')

        try:
            if re.match(r'^\s*\d+\s*[\+\-\*/]\s*\d+\s*$', text):
                result = eval(text, {"__builtins__": {}})
                response_text = f"The result is {result}."
                confidence = 0.95
            else:
                if '=' not in text:
                    return Statement(text="Please provide an equation with an equals sign, e.g., '2x + 3 = 7'.")

                left, right = [s.strip() for s in text.split('=', 1)]
                if not left or not right:
                    return Statement(text="Invalid equation format. Try '2x + 3 = 7'.")

                variables = sorted(set(re.findall(r'[a-zA-Z]', text)))
                sympy_vars = symbols(variables)
                local_dict = {str(v): v for v in sympy_vars}
                local_dict.update({'sin': sin, 'cos': cos, 'tan': tan, 'ln': ln, 'sqrt': sqrt, 'exp': exp})

                left_expr = parse_expr(left, local_dict=local_dict, transformations=self.transformations)
                right_expr = parse_expr(right, local_dict=local_dict, transformations=self.transformations)
                equation = Eq(left_expr, right_expr)

                steps = []
                steps_latex = []

                steps.append(f"Original equation:\n{pretty(equation)}")
                steps_latex.append(f"Original equation: $$ {latex(equation)} $$")

                # Move all terms to one side: lhs - rhs = 0
                moved_expr = simplify(left_expr - right_expr)
                moved_eq = Eq(moved_expr, 0)
                steps.append(f"Rewrite to zero on one side:\n{pretty(moved_eq)}")
                steps_latex.append(f"Rewrite to zero: $$ {latex(moved_eq)} $$")

                # Expand expression if needed
                expanded_expr = expand(moved_expr)
                if expanded_expr != moved_expr:
                    steps.append(f"Expand expression:\n{pretty(expanded_expr)} = 0")
                    steps_latex.append(f"Expand: $$ {latex(expanded_expr)} = 0 $$")

                # Try to factor
                factored_expr = factor(expanded_expr)
                if factored_expr != expanded_expr:
                    steps.append(f"Factor expression:\n{pretty(factored_expr)} = 0")
                    steps_latex.append(f"Factor: $$ {latex(factored_expr)} = 0 $$")

                # Solve equation
                solution = solve(equation, sympy_vars)

                if solution:
                    if isinstance(solution, list):
                        if isinstance(solution[0], dict):
                            solution_str = ', '.join(f"{k} = {pretty(v)}" for d in solution for k, v in d.items())
                            solution_latex = ', '.join(f"{k} = {latex(v)}" for d in solution for k, v in d.items())
                        else:
                            solution_str = ', '.join(f"{sympy_vars[0]} = {pretty(s)}" for s in solution)
                            solution_latex = ', '.join(f"{sympy_vars[0]} = {latex(s)}" for s in solution)
                    else:
                        solution_str = str(solution)
                        solution_latex = latex(solution)

                    steps.append(f"Solution:\n{solution_str}")
                    steps_latex.append(f"Solution: $$ {solution_latex} $$")
                    confidence = 0.95
                else:
                    steps.append("I couldn't solve this equation.")
                    steps_latex.append("I couldn't solve this equation.")
                    confidence = 0.1

                response_text = "\n\n".join(steps)
                # Include LaTeX in a separate key or as part of response for frontend rendering
                response_text += "\n\n---\nLaTeX format (for rendering):\n" + "\n".join(steps_latex)

                # Plot graph if single variable and solution found
                if len(sympy_vars) == 1 and solution and confidence > 0.5:
                    try:
                        x = sympy_vars[0]
                        f = left_expr - right_expr
                        p = plot(f, (x, -10, 10), show=False, ylabel="f(x) = LHS - RHS")
                        buf = io.BytesIO()
                        p.save(buf)
                        buf.seek(0)
                        encoded_plot = base64.b64encode(buf.read()).decode('utf-8')
                        response_text += "\n\n🖼️ Graph available (base64 encoded)."
                    except Exception:
                        response_text += "\n(Graphing failed)"

        except Exception as e:
            response_text = f"Sorry, I couldn't solve that equation due to an error: {str(e)}. Try a simpler one like '2x + 3 = 7'."
            confidence = 0.1

        response = Statement(text=response_text)
        response.confidence = confidence
        return response
