import unittest
from unittest.mock import patch, Mock
from casos_criminais import CASOS, extrair_interrogatorio, anonimizar, obter_interrogatorio

class BlindCasesTests(unittest.TestCase):
    def test_cases_have_neutral_context(self):
        self.assertGreaterEqual(len(CASOS),2)
        for c in CASOS:
            self.assertIn("contexto", c.__dataclass_fields__)
            self.assertNotIn("sentença",c.contexto.lower())
            self.assertNotIn("condenad",c.contexto.lower())
            self.assertTrue(c.fonte.startswith("https://www2.tjal.jus.br/"))

    def test_extract_only_interrogation(self):
        questions = " ".join(
            f"PERGUNTADO: {q}? RESPONDEU: Que esteve no local durante a tarde e que explicou o que aconteceu. Informou detalhes adicionais sobre o trajeto e os horários que recordava."
            for q in ["se é verdadeira a acusação","onde estava na data","se conhece as provas",
                      "se conhece as testemunhas","se conhece o instrumento","outros fatos",
                      "se tem algo mais a alegar"])
        page = "<html><body>CONDENAÇÃO NÃO PODE APARECER. "+questions+\
               " Nada mais sendo dito, o juiz encerrou a oitiva. SENTENÇA FORA DO REGISTRO.</body></html>"
        result=extrair_interrogatorio(page)
        self.assertTrue(result.startswith("PERGUNTADO:"))
        self.assertNotIn("SENTENÇA FORA",result)
        self.assertNotIn("CONDENAÇÃO NÃO",result)
        self.assertGreaterEqual(result.count("RESPONDEU:"),5)

    def test_anonymize_subject_and_places(self):
        c=CASOS[0]
        result=anonimizar("Josedi Luiz da Penha falou com Rosangela em Valparaíso.",c)
        self.assertNotIn("Josedi",result)
        self.assertNotIn("Rosangela",result)
        self.assertNotIn("Valparaíso",result)
        self.assertIn("INTERROGADO",result)
        self.assertIn("Pessoa A",result)
        self.assertIn("Local A",result)

    def test_invalid_web_host(self):
        from dataclasses import replace
        c=replace(CASOS[0],fonte="https://malicious.example/test")
        with self.assertRaises(ValueError):
            obter_interrogatorio(c)

if __name__=="__main__":
    unittest.main()
