from peak_acl import parse, dumps, AclMessage
import pytest

RAW_SIMPLE = '(inform :sender a :receiver b :content "hi")'
RAW_NESTED = '(proxy :sender a :receiver b :content (request :sender a :content "turn_on"))'

@pytest.mark.parametrize("raw", [RAW_SIMPLE, RAW_NESTED])
def test_round_trip(raw):
    msg = parse(raw)
    again = dumps(msg)
    assert again == raw

def test_missing_content_raises():
    with pytest.raises(ValueError):
        parse('(inform :sender a)')
