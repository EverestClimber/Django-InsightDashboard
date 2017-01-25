from mixer.backend.django import mixer
import pytest

from django.test import TestCase

from survey.models import Option
from ..models import OptionDict

pytestmark = pytest.mark.django_db


class TestOptionDict(TestCase):

    def setUp(self):
        OptionDict.clear()

    def test_load(self):
        mixer.blend(Option, value='Qq')
        mixer.blend(Option, value='Ww')
        mixer.blend(Option, value='Ee')

        od1 = mixer.blend(OptionDict, lower='qq', original='Qq')
        od2 = mixer.blend(OptionDict, lower='ww', original='W')

        assert OptionDict.get('qq') == 'Qq'
        assert OptionDict.get('mm') == 'mm'

        assert OptionDict.data['qq'] == od1
        assert OptionDict.data['ww'] == od2
        assert OptionDict.data['ww'].original == 'Ww'
        assert OptionDict.data['ee'].original == 'Ee'

        OptionDict.register('mm', 'Mm')
        assert OptionDict.get('mm') == 'Mm'
        assert OptionDict.objects.get(lower='mm')


        assert OptionDict.get('xx') == 'xx'

