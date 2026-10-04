import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_configure(config):
    config.addinivalue_line("markers", "sitl: needs an ArduCopter SITL binary (robotics box)")
    config.addinivalue_line("markers", "gz: needs Gazebo / gz-transport (robotics box)")
    config.addinivalue_line("markers", "slow: takes more than ~10 s")


@pytest.fixture
def cfg():
    from skyscan.config import load_config
    return load_config()
