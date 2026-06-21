import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from obsact import SemanticError, main, transpile_text


def compile_source(source):
    code, warnings = transpile_text(source)
    compile(code, "<codigo-gerado>", "exec")
    return code, warnings


def run_code(code):
    namespace = {"__name__": "teste"}
    output = io.StringIO()
    with redirect_stdout(output):
        exec(code, namespace)
        namespace["main"]()
    return output.getvalue()


class ObsActTests(unittest.TestCase):
    def test_todos_os_exemplos_compilam_e_executam(self):
        for path in sorted((ROOT / "tests").glob("exemplo*.obsact")):
            with self.subTest(path=path.name):
                code, warnings = compile_source(path.read_text(encoding="utf-8"))
                run_code(code)
                self.assertEqual(warnings, [])

    def test_atribuicao_repetida_gera_python_valido(self):
        source = """
dispositivo: {monitor, temperatura}
set temperatura = 1.
set temperatura = 2.
"""
        code, _ = compile_source(source)
        self.assertNotIn("global ", code)
        run_code(code)

    def test_leitura_antes_de_atribuicao_comeca_em_zero(self):
        source = """
dispositivo: {lampada, temperatura}
se temperatura == 0 entao ligar lampada.
set temperatura = 1.
"""
        code, _ = compile_source(source)
        self.assertIn("lampada ligado!", run_code(code))

    def test_nomes_reservados_sao_protegidos(self):
        source = """
dispositivo: {lampada, class}
dispositivo: {monitor, ligar}
dispositivo: {sensor, estados}
set class = 1.
set ligar = 2.
set estados = 3.
ligar lampada.
"""
        code, _ = compile_source(source)
        self.assertIn("obs_class", code)
        self.assertIn("lampada ligado!", run_code(code))

    def test_resultado_de_acao_pode_criar_variavel(self):
        source = """
dispositivo: {ventilador}
set estado_ventilador = verificar(ventilador).
se estado_ventilador == 0 entao ligar ventilador.
"""
        code, _ = compile_source(source)
        output = run_code(code)
        self.assertIn("ventilador ligado!", output)

    def test_bloco_senao_em_varias_linhas(self):
        source = """
dispositivo: {lampada, movimento}
se movimento == True entao
    ligar lampada.
senao
    desligar lampada.
.
"""
        code, _ = compile_source(source)
        self.assertIn("lampada desligado!", run_code(code))

    def test_condicao_composta_e_broadcast(self):
        source = """
dispositivo: {Termometro, temperatura}
dispositivo: {higrometro, umidade}
dispositivo: {monitor}
dispositivo: {celular}
set temperatura = 35.
set umidade = 40.
se temperatura > 30 && umidade < 50 entao
    enviar alerta ("Ambiente", temperatura) para todos: monitor, celular.
.
"""
        code, _ = compile_source(source)
        output = run_code(code)
        self.assertIn("monitor recebeu o alerta", output)
        self.assertIn("celular recebeu o alerta", output)

    def test_broadcast_multilinha_como_no_enunciado(self):
        source = """
dispositivo {monitor}
dispositivo: {celular}
dispositivo: {Termometro, temperatura}
se temperatura > 30 entao .
enviar alerta ("Temperatura em", temperatura) para todos:
    monitor, celular.
"""
        code, _ = compile_source(source)
        run_code(code)

    def test_prefixos_de_palavras_reservadas_sao_identificadores(self):
        source = """
dispositivo: {sensor, TrueValue}
dispositivo: {controle, ligarStatus}
dispositivo: {lampada}
set TrueValue = 1.
set ligarStatus = 1.
se TrueValue > 0 && ligarStatus > 0 entao ligar lampada.
"""
        code, _ = compile_source(source)
        self.assertIn("lampada ligado!", run_code(code))

    def test_dispositivo_simples_usado_como_observacao(self):
        source = """
dispositivo: {umidade}
dispositivo: {Monitor}
se umidade < 40 entao enviar alerta "Ar seco detectado" Monitor.
"""
        code, _ = compile_source(source)
        self.assertIn("Monitor recebeu o alerta", run_code(code))

    def test_erros_semanticos(self):
        invalid_sources = {
            "dispositivo com numero": "dispositivo: {lampada1}\nligar lampada1.",
            "dispositivo longo": (
                "dispositivo: {" + ("a" * 101) + "}\nligar " + ("a" * 101) + "."
            ),
            "dispositivo duplicado": (
                "dispositivo: {lampada}\ndispositivo: {lampada}\nligar lampada."
            ),
            "dispositivo nao declarado": "dispositivo: {lampada}\nligar ventilador.",
            "observacao nao declarada": (
                "dispositivo: {lampada}\n"
                "se temperatura > 0 entao ligar lampada."
            ),
            "observacao invalida": (
                "dispositivo: {lampada, _potencia}\nset _potencia = 1."
            ),
            "associacao incorreta": (
                "dispositivo: {lampada, potencia}\n"
                "dispositivo: {ventilador, velocidade}\n"
                "set {lampada, velocidade} = 1."
            ),
            "mensagem longa": (
                "dispositivo: {monitor}\n"
                + 'enviar alerta ("' + ("x" * 101) + '") monitor.'
            ),
            "mensagem vazia": (
                'dispositivo: {monitor}\nenviar alerta ("") monitor.'
            ),
        }
        for name, source in invalid_sources.items():
            with self.subTest(name=name):
                with self.assertRaises(SemanticError):
                    transpile_text(source)

    def test_cli_gera_arquivo(self):
        source_path = ROOT / "tests" / "exemplo1.obsact"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "saida.py"
            result = main([str(source_path), "-o", str(output_path)])
            self.assertEqual(result, 0)
            self.assertTrue(output_path.exists())
            compile(output_path.read_text(encoding="utf-8"), str(output_path), "exec")


if __name__ == "__main__":
    unittest.main()
