import unittest
from unittest.mock import patch, Mock
from engine import analyze, compare, times, normalize, fragments
from fontes import extrair_html, obter_texto, hash_documento, catalogo

class EngineTests(unittest.TestCase):
    def test_pt_br_markers(self):
        rows=analyze("Eu acho que a reunião ocorreu às 10h30. Na verdade, foi depois.", "A")
        self.assertTrue(rows)
        joined=" ".join(x["Categorias"] for x in rows)
        self.assertIn("Incerteza",joined)
        self.assertIn("Reformulação",joined)
        self.assertIn("Referência temporal",joined)

    def test_cross_statement_numeric_and_negation(self):
        a="Eu vi o carro azul estacionado no portão às 10h30, tinha 3 pessoas."
        b="Eu não vi o carro azul estacionado no portão às 11h30, tinha 4 pessoas."
        rows=compare(a,b,.15)
        self.assertTrue(rows)
        signs=rows[0]["Sinais"]
        self.assertIn("Negação divergente",signs)
        self.assertIn("Horários diferentes",signs)
        self.assertIn("Números diferentes",signs)

    def test_time_reference(self):
        t=times("Eu estava no posto às 09h15 e voltei 11:20.","A")
        self.assertEqual(len(t),2)

    def test_empty_and_normalize(self):
        self.assertEqual(compare("","nada"),[])
        self.assertEqual(normalize("NÃO"),"nao")

class SourceTests(unittest.TestCase):
    def test_official_catalog_is_portuguese(self):
        entries=catalogo()
        self.assertGreaterEqual(len(entries),5)
        self.assertTrue(all(x["idioma"]=="pt-BR" for x in entries))
        self.assertTrue(all("www25.senado.leg.br" in x["url"] for x in entries))

    def test_extract_timestamped_turns(self):
        turn="O SR. DEPOENTE - Eu compareci à reunião e respondi às perguntas da comissão com a maior clareza possível. " * 5
        html="<html><body><table><tr><th>Horário</th><th>Texto com revisão</th></tr>"+\
             "".join(f"<tr><td>10:0{i}</td><td>{turn}</td></tr>" for i in range(3))+"</table></body></html>"
        text=extrair_html(html)
        self.assertIn("10:00 | O SR.",text)
        self.assertIn("10:02 | O SR.",text)
        self.assertNotIn("<table>",text)

    def test_reject_unapproved_url(self):
        with self.assertRaises(ValueError):
            obter_texto({"url":"https://example.com/test"})

if __name__=="__main__":
    unittest.main()
