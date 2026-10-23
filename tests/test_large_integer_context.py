import copy
import json
from unittest.mock import patch

import pytest

import rollbar
from rollbar.lib import transforms
from rollbar.lib.transforms.serializable import SerializableTransform


@pytest.mark.parametrize('value', [10**400, -(10**400)], ids=['positive', 'negative'])
def test_serializable_transform_preserves_large_integer(value):
    result = transforms.transform(
        {'counter': value, 'neighbor': 'retained'}, SerializableTransform()
    )

    assert result == {'counter': value, 'neighbor': 'retained'}


@pytest.mark.parametrize('batch_transforms', [False, True])
@pytest.mark.parametrize(('value', 'expected'), [
    (10**400, 10**400),
    (-(10**400), -(10**400)),
    (0, 0),
    (42, 42),
    (3.14, 3.14),
    (True, True),
    (float('nan'), '<NaN>'),
    (float('inf'), '<Infinity>'),
    (float('-inf'), '<NegativeInfinity>'),
], ids=[
    'large-positive', 'large-negative', 'zero', 'int', 'float',
    'bool', 'nan', 'infinity', 'negative-infinity',
])
def test_report_message_preserves_numeric_context(monkeypatch, batch_transforms, value, expected):
    for name in ('SETTINGS', '_initialized', '_transforms', '_serialize_transform', '_threads'):
        monkeypatch.setattr(rollbar, name, getattr(rollbar, name, None), raising=False)
    rollbar.SETTINGS = copy.deepcopy(rollbar.SETTINGS)
    rollbar._initialized = False
    rollbar.init('local-test', handler='blocking', batch_transforms=batch_transforms)

    with patch('rollbar.send_payload') as send:
        rollbar.report_message(
            'numeric context', extra_data={'counter': value, 'neighbor': 'retained'}
        )

    send.assert_called_once()
    payload = json.loads(json.dumps(send.call_args[0][0], allow_nan=False))
    assert payload['data']['custom'] == {'counter': expected, 'neighbor': 'retained'}
