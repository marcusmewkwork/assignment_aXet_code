import pytest

from logscope.cli import main


def test_help_is_available(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--help"])

    assert error.value.code == 0
    assert "usage: logscope" in capsys.readouterr().out
