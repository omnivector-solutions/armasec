import pytest

from cli.cache import (
    _get_token_paths,
    load_tokens_from_cache,
    save_tokens_to_cache,
    clear_token_cache,
    init_cache,
)
from cli.exceptions import Abort
from cli.schemas import TokenSet


@pytest.mark.usefixtures("override_cache_dir")
def test_load_tokens_from_cache__success(make_token):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 22:30:00",
    )
    refresh_token = "dummy-refresh-token"
    (access_token_path, refresh_token_path) = _get_token_paths()
    access_token_path.write_text(access_token)
    refresh_token_path.write_text(refresh_token)

    token_set = load_tokens_from_cache()

    assert token_set.access_token == access_token
    assert token_set.refresh_token == refresh_token


@pytest.mark.usefixtures("override_cache_dir")
def test_load_tokens_from_cache__omits_refresh_token_if_it_is_not_found(make_token):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 22:30:00",
    )
    (access_token_path, _) = _get_token_paths()
    access_token_path.write_text(access_token)

    token_set = load_tokens_from_cache()

    assert token_set.access_token == access_token
    assert token_set.refresh_token is None


@pytest.mark.usefixtures("override_cache_dir")
def test_save_tokens_to_cache__success(make_token):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 22:30:00",
    )
    refresh_token = "dummy-refresh-token"
    (access_token_path, refresh_token_path) = _get_token_paths()
    token_set = TokenSet(
        access_token=access_token,
        refresh_token=refresh_token,
    )

    save_tokens_to_cache(token_set)

    assert access_token_path.exists()
    assert access_token_path.read_text() == access_token
    assert access_token_path.stat().st_mode & 0o777 == 0o600

    assert refresh_token_path.exists()
    assert refresh_token_path.read_text() == refresh_token
    assert access_token_path.stat().st_mode & 0o777 == 0o600


@pytest.mark.usefixtures("override_cache_dir")
def test_save_tokens_to_cache__only_saves_access_token_if_refresh_token_is_not_defined(
    make_token,
):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 22:30:00",
    )
    (access_token_path, refresh_token_path) = _get_token_paths()
    token_set = TokenSet(
        access_token=access_token,
    )

    save_tokens_to_cache(token_set)

    assert access_token_path.exists()
    assert access_token_path.read_text() == access_token

    assert not refresh_token_path.exists()


@pytest.mark.usefixtures("override_cache_dir")
def test_clear_token_cache__success(make_token):
    access_token = make_token(
        azp="dummy-client",
        email="good@email.com",
        expires="2022-02-16 22:30:00",
    )
    refresh_token = "dummy-refresh-token"
    (access_token_path, refresh_token_path) = _get_token_paths()
    access_token_path.write_text(access_token)
    refresh_token_path.write_text(refresh_token)

    assert access_token_path.exists()
    assert refresh_token_path.exists()

    clear_token_cache()

    assert not access_token_path.exists()


@pytest.mark.usefixtures("override_cache_dir")
def test_clear_token_cache__does_not_fail_if_no_tokens_are_in_cache():
    (access_token_path, refresh_token_path) = _get_token_paths()

    assert not access_token_path.exists()
    assert not refresh_token_path.exists()

    clear_token_cache()


@pytest.mark.usefixtures("override_cache_dir")
def test_init_cache__success(tmp_path, mocker):
    new_cache_dir = tmp_path / "cache"
    with mocker.patch("cli.cache.cache_dir", new=new_cache_dir):
        @init_cache
        def _helper():
            assert new_cache_dir.exists()
            token_path = new_cache_dir / "token"
            assert token_path.exists()
            info_file_path = new_cache_dir / "info.txt"
            assert info_file_path.exists()
            assert "cache" in info_file_path.read_text()

        _helper()


@pytest.mark.usefixtures("override_cache_dir")
def test_init_cache__raises_Abort_if_cache_dir_is_not_usable(tmp_path):
    info_file_path = tmp_path / "info.txt"
    info_file_path.write_text("blah")
    info_file_path.chmod(0o000)

    @init_cache
    def _helper():
        pass

    with pytest.raises(Abort, match="check your home directory permissions"):
        _helper()
