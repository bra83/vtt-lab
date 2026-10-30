"""Fluxo de ponta a ponta: biblioteca criminal -> A -> resultado automático."""
import unittest
from streamlit.testing.v1 import AppTest
from casos_criminais import CASOS, somente_respostas

FIXTURE = (
    "PERGUNTADO: onde estava? RESPONDEU: Eu estava na praça às 10h30 e vi três carros "
    "em frente ao mercado, mas não falei com ninguém. "
    "PERGUNTADO: quem estava presente? RESPONDEU: Acho que havia dois homens no local "
    "e depois fui para casa, sem conversar com as testemunhas. "
    "PERGUNTADO: o que aconteceu? RESPONDEU: Na verdade, retifico o horário, "
    "pode ter sido às 11h40, porque meu relógio estava adiantado."
)

class IntegratedLibraryTests(unittest.TestCase):
    def test_criminal_library_feeds_analysis_without_second_upload(self):
        app=AppTest.from_file("app.py",default_timeout=50)
        app.session_state["criminal_text_CR-01"]=FIXTURE
        app.session_state["criminal_answers_CR-01"]=somente_respostas(FIXTURE)
        app.run(timeout=50)
        self.assertFalse(app.exception, [str(x.message) for x in app.exception])
        self.assertTrue(any("Biblioteca de transcrições" in x.label for x in app.tabs))
        self.assertTrue(any("Análise comparativa" in x.label for x in app.tabs))
        app.button(key="carregar_crime_a").click().run(timeout=50)
        self.assertFalse(app.exception,[str(x.message) for x in app.exception])
        self.assertIn("Resposta 01",app.session_state["text_A"])
        self.assertNotIn("PERGUNTADO:",app.session_state["text_A"])
        self.assertTrue(app.session_state["result"]["notes"])
        self.assertEqual(app.session_state["result"]["proveniencia"]["A"]["id_caso"],"CR-01")

    def test_only_responses_exclude_judicial_questions(self):
        s=somente_respostas(FIXTURE)
        self.assertNotIn("PERGUNTADO:",s)
        self.assertNotIn("onde estava?",s)
        self.assertIn("às 10h30",s)
        self.assertIn("às 11h40",s)
        self.assertEqual(s.count("Resposta 0"),3)

if __name__=="__main__":
    unittest.main()
