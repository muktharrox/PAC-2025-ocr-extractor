from app.classification import classifier
from tools.generate_synthetic_docs import document_lines


def test_classifica_pj():
    texto = "\n".join(document_lines("pj"))
    tipo, conf = classifier.classify(texto)
    assert tipo == "RGP_PJ"
    assert conf > 60


def test_classifica_pf():
    texto = "\n".join(document_lines("pf"))
    tipo, _conf = classifier.classify(texto)
    assert tipo == "RGP_PF"


def test_classifica_vazio():
    tipo, conf = classifier.classify("")
    assert tipo == "NAO_IDENTIFICADO"
    assert conf == 0.0
