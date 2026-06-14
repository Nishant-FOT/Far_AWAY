import sys
import os
from starlette.testclient import TestClient

# Ensure backend app package is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.main import app, read_root


def test_root():
    res = read_root()
    assert isinstance(res, dict)
    assert 'Disaster' in res.get('message', '')
