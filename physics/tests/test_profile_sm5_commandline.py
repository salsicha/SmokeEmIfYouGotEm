"""Token-boundary regression for the owned SM5 profiler process check."""
from pathlib import Path
import re

import pytest


@pytest.mark.parametrize('command,expected', [
    ('editor -sm5 -Unattended', True), ('editor "-sm5" -Unattended', True),
    ('-sm5', True), ('"-SM5"', True),
    ('editor -sm50', False), ('editor -sm6', False),
    ('editor prefix-sm5', False), ('editor "-sm5suffix"', False),
    ('editor "-sm5', False), ('editor -sm5"', False),
])
def test_exact_sm5_token_accepts_balanced_quotes_only(command, expected):
    source = (Path(__file__).resolve().parents[2] /
              'unreal/Scripts/profile_south_fork_current_map.ps1').read_text()
    pattern = re.search(r"\$actual\.CommandLine -notmatch '([^']+)'", source).group(1)
    assert bool(re.search(pattern, command)) is expected
