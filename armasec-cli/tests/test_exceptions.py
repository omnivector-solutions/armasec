import pytest

from armasec_cli.exceptions import Abort


def test_Abort_handle_errors():
    original_error = RuntimeError("Boom!")
    with pytest.raises(Abort) as err_info:
        with Abort.handle_errors("Something went wrong"):
            raise original_error

    assert err_info.value.original_error is original_error
    assert "Boom!" in str(err_info.value)
    assert "Something went wrong" in str(err_info.value)
