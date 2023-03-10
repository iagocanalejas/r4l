import os.path

from django.conf import settings
from django.test import TestCase

from apps.races.models import Flag, Trophy
from apps.races.services import FlagService, TrophyService


class SearchQueryTest(TestCase):
    fixtures = [os.path.join(settings.BASE_DIR, 'fixtures', 'test-db.yaml')]

    def test_search_teresa_herrera(self):
        trophy = Trophy.objects.get(pk=25)
        flag = Flag.objects.get(pk=39)

        query = 'ELIMINATORIA TROFEO TERESA HERRERA'
        self.assertEqual(trophy, TrophyService.get_closest_by_name(query))
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        query = 'ELIMINATORIA BANDERA TERESA HERRERA'
        self.assertEqual(flag, FlagService.get_closest_by_name(query))
        self.assertEqual(trophy, TrophyService.get_closest_by_name(query))

    def test_search_deputacion(self):
        flag = Flag.objects.get(pk=133)

        query = 'BANDEIRA DEPUTACIÓN DA CORUÑA'
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        query = 'BANDEIRA DEPUTACION DA CORUNA'
        self.assertEqual(flag, FlagService.get_closest_by_name(query))

        query = 'BANDEIRA DEPUTACION DA CORUNA DE TRAINERAS'
        self.assertEqual(flag, FlagService.get_closest_by_name(query))
