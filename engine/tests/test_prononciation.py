"""Table de prononciation de la voix wolof : seule la graphie envoyée à Octopus change."""

from unittest import mock

from engine.app.responses.voix import prononciation as pr


def _avec(lignes, tmp_path):
    t = tmp_path / "p.csv"
    t.write_text(
        "ecrit,dit_a_la_voix,raison\n" + "".join(f"{e},{d},essai\n" for e, d in lignes),
        encoding="utf-8",
    )
    pr._table.cache_clear()
    return mock.patch.object(pr, "TABLE", t)


def test_mot_entier_et_majuscule(tmp_path):
    with _avec([("tool", "tol"), ("jërëjëf", "jerejef")], tmp_path):
        assert (
            pr.pour_la_voix("Jërëjëf, dégg na fi sa tool nekk.")
            == "Jerejef, dégg na fi sa tol nekk."
        )
        assert pr.pour_la_voix("tooli") == "tooli"  # pas au milieu d'un autre mot
    pr._table.cache_clear()


def test_table_vide_rien_ne_change(tmp_path):
    with _avec([], tmp_path):
        assert pr.pour_la_voix("sa tool") == "sa tool"
    pr._table.cache_clear()
