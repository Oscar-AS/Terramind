"""Gemini oublie parfois les apostrophes (« C est l alternariose », 18 nov 2026) : on les remet."""

from engine.app.modules.rag.reponse import remettre_apostrophes


def test_elisions_remises():
    assert remettre_apostrophes("C est l alternariose. Retire d abord.") == (
        "C'est l'alternariose. Retire d'abord."
    )
    assert remettre_apostrophes("Qu il pleuve, jusqu au matin.") == "Qu'il pleuve, jusqu'au matin."


def test_texte_correct_inchange():
    for texte in (
        "C'est déjà correct.",
        "Il y a une tache et la tomate a des cercles.",
        "Mets 2 l à l'hectare, 1 m entre les plants.",
    ):
        assert remettre_apostrophes(texte) == texte
