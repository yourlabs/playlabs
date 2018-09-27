from playlabs.main import nostrict


def test_nostrict():
    result = nostrict([])
    assert len(result) == 2
    assert result[0] == '--ssh-extra-args'
    assert 'StrictHostKeyChecking=no' in result[1]
