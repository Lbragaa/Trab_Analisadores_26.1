import sys
from parser import parser
from lexer import lexer
from codegen import generate
from semantic import SemanticError, validate

def main():
    if len(sys.argv) != 3:
        print("Uso: python obsact.py <entrada.obsact> <saida.py>")
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8-sig') as f:
        src = f.read()
    lexer.lineno = 1
    lexer.errors = []
    ast = parser.parse(src, lexer=lexer)
    if lexer.errors or ast is None:
        print("Falha na analise.")
        sys.exit(1)
    try:
        symbols = validate(ast)
    except SemanticError as exc:
        print(exc)
        sys.exit(1)
    code = generate(ast, symbols)
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"Gerado: {sys.argv[2]}")

if __name__ == '__main__':
    main()
