import logging
import time
from typing import List

from django.core.management import BaseCommand

from digest.scrappers import LGTScrapper, ScrappedItem
from utils.exceptions import StopProcessing

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import data from LGT web'

    def add_arguments(self, parser):
        parser.add_argument('--race_id', default=None, type=int, help='')
        parser.add_argument('--all', action='store_true', default=False)

    def handle(self, *args, **options):
        scrapper = LGTScrapper()

        assert options['race_id'] or options['all']

        if options['all']:
            i = 9  # 8 first IDs are test races
            empty_count = 0
            items: List[ScrappedItem] = []
            while True:
                if empty_count > 8:  # stops the scrapper when 8 races are empty in a row
                    break

                try:
                    items.extend(scrapper.scrap(race_id=i))
                except StopProcessing:
                    empty_count += 1
                else:
                    empty_count = 0
                    time.sleep(1)

                i += 1

            scrapper.save(items)

        if options['race_id']:
            scrapper.save(
                list(scrapper.scrap(race_id=options['race_id'])),
                file_name=f'{options["race_id"]}.csv',
            )
