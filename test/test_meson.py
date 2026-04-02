from pathlib import Path

from eutaxis.workers.meson.lark_clean import lark_clean_code, lark_parser


base_path = Path(__file__).parent


def test_meson() -> None:
    lark = lark_parser()

    meson = (base_path / "meson.build").read_text(encoding="utf-8")
    formatted = lark_clean_code(
        lark,
        meson,
        config=base_path / "muon-fmt.ini",
        format=True,
    )
    assert meson == formatted
