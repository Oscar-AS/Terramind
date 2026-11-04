"""Tests de la préparation du texte wolof avant synthèse vocale.

Lancer depuis la racine : python3 -m unittest discover engine/tests
Les nombres attendus suivent les exemples des sources du lexique
(jangawolof.org) ; ils restent à valider par un locuteur. Les phrases wolof
des tests ne servent qu'à exercer le code : ce ne sont pas des contenus.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app" / "responses" / "voix"))
import normalisation as nz  # noqa: E402

LEX = nz.charger_lexique()
CH, BA = LEX[0], LEX[1]


class Nombres(unittest.TestCase):
    def test_exemples_des_sources(self):
        cas = {
            7: "juróom-ñaar",
            11: "fukk ak benn",
            21: "ñaar fukk ak benn",
            34: "ñett fukk ak ñeent",
            101: "téeméer ak benn",
            200: "ñaari téeméer",
            2000: "ñaari junni",
            1945: "junni ak juróom-ñeenti téeméer ak ñeent fukk ak juróom",
        }
        for n, attendu in cas.items():
            self.assertEqual(nz.nombre_en_wolof(n, CH, BA), attendu, n)

    def test_hors_plage(self):
        with self.assertRaises(ValueError):
            nz.nombre_en_wolof(1_000_000, CH, BA)


class Preparation(unittest.TestCase):
    def test_retire_sources_et_ecrit_les_nombres(self):
        r = nz.preparer("Dafay jël 110 bés. [Guide 1987, p. 119]", LEX)
        self.assertEqual(r.morceaux, ["Dafay jël téeméer ak fukk bés."])
        self.assertTrue(r.synthetisable)

    def test_signale_decimales_symboles_et_mots_a_remplir(self):
        r = nz.preparer("Tomate bi: 2,5 ha, 30 %.", LEX)
        self.assertFalse(r.synthetisable)
        texte = " ".join(r.problemes)
        self.assertIn("décimal", texte)
        self.assertIn("« ha »", texte)  # « ha » reste à remplir dans le lexique
        self.assertIn("tomate", texte)

    def test_signale_le_francais(self):
        r = nz.preparer("Arrose les feuilles le matin.", LEX)
        self.assertTrue(any("français" in p for p in r.problemes))

    def test_decoupage_court_et_ponctue(self):
        long = "Ab baat bu gudd, " * 20 + "jeex na"
        for m in nz.decouper(long):
            self.assertLessEqual(len(m), nz.TAILLE_MAX + 1)
            self.assertIn(m[-1], ".!?")


if __name__ == "__main__":
    unittest.main()
