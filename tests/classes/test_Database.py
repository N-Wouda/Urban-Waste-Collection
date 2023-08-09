from numpy.testing import assert_raises

from waste.classes import Database


def test_existing_res_db_raises_unless_explicitly_allowed(tmp_path):
    src_db = str(tmp_path / "src.db")
    res_db = str(tmp_path / "res.db")

    # Create res db. This is not OK unless explicitly allowed by setting
    # exists_ok.
    (tmp_path / "res.db").touch()
    with assert_raises(FileExistsError):
        Database(src_db, res_db)

    Database(src_db, res_db, exists_ok=True)
