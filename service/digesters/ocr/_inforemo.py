import logging
import os
import re
from datetime import date, datetime
from typing import List, Optional, Tuple

import cv2
import numpy as np
from pandas import DataFrame
from pytesseract import pytesseract

from ai_django.ai_core.utils.strings import whitespaces_clean, remove_symbols
from apps.entities.models import LEAGUE_GENDER_MALE, LEAGUE_GENDER_FEMALE
from apps.races.models import RACE_VETERANS, RACE_TRAINERA
from digesters import ScrappedItem
from digesters.ocr.image import ImageOCR, IMAGE_INFOREMO

logger = logging.getLogger(__name__)


class ImageOCRInforemo(ImageOCR, source=IMAGE_INFOREMO):
    DATASOURCE = IMAGE_INFOREMO

    _GENDERS = {
        LEAGUE_GENDER_MALE: ['MASCULINO', 'ABSOLUTO', 'VETERANO'],
        LEAGUE_GENDER_FEMALE: ['FEMENINO', 'VETERANA'],
    }

    def digest(self, path: str) -> List[ScrappedItem]:
        logger.info(f'processing {path}')

        self.prepare_image(path)
        name, t_date, town = self.parse_header()
        if not name or not t_date:
            logger.error(f'unable to process: {path}')
            return []

        df = self.prepare_dataframe()

        if self.allow_plot:
            logger.info(df)

        trophy_name = self.normalized_name(name)
        race_lanes = self.get_race_lanes(df)
        race_laps = self.get_race_laps(df)
        for itx, row in df.iterrows():
            club_name = self.get_club_name(row)
            yield ScrappedItem(
                name=name,
                trophy_name=trophy_name,
                edition=self.get_edition(),
                day=self.get_day(),
                t_date=t_date,
                town=town,
                gender=self.get_gender(row),
                modality=self.get_modality(row),
                league=self.get_league(),
                organizer=self.get_organizer(),
                club_name=club_name,
                participant=self.normalized_club_name(club_name),
                series=self.get_series(row),
                lane=self.get_lane(row),
                laps=self.get_laps(row),
                race_id=os.path.basename(path),
                url=None,
                datasource=self.DATASOURCE,
                race_laps=race_laps,
                race_lanes=race_lanes
            )

    ####################################################
    #                 IMAGE PROCESSING                 #
    ####################################################

    def prepare_image(self, path: str, **kwargs):
        img = cv2.imread(path, 0)
        self.plot(img)

        thresh, img_bin = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)  # thresholding the image to a binary image
        img_bin = 255 - img_bin  # inverting the image
        self.plot(img_bin)

        img_vh = self.get_vh_lines(img_bin)  # find vertical and horizontal lines
        self.plot(img_vh)

        # Eroding and thesholding the image
        bitxor = cv2.bitwise_xor(img, img_vh)
        bitnot = cv2.bitwise_not(bitxor)
        self.plot(bitnot)  # find vertical and horizontal lines

        # can't be done directly
        self.img, self.img_vh, self.img_bin, self.bitnot = img, img_vh, img_bin, bitnot

    def parse_header(self, **kwargs) -> Tuple[str, date, Optional[str]]:
        # TODO: improve name detection
        header = self.get_image_header(self.img_bin)
        self.plot(header)

        # https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html#page-segmentation-method
        out = pytesseract.image_to_string(header, config='--psm 3')
        return self.get_name(out), self.get_date(out), self.get_town(out)

    ####################################################
    #              DATAFRAME PROCESSING                #
    ####################################################

    def prepare_dataframe(self, **kwargs) -> DataFrame:
        final_boxes, (count_col, count_row) = self.get_boxes(self.img_vh)

        # from every single image-based cell/box the strings are extracted via pytesseract and stored in a list
        outer = []
        for i in range(len(final_boxes)):
            for j in range(len(final_boxes[i])):
                inner = ''
                if len(final_boxes[i][j]) == 0:
                    outer.append(' ')
                    continue

                for k in range(len(final_boxes[i][j])):
                    y, x, w, h = final_boxes[i][j][k][0], final_boxes[i][j][k][1], final_boxes[i][j][k][2], final_boxes[i][j][k][3]
                    finalimg = self.bitnot[x:x + h, y:y + w]
                    border = cv2.copyMakeBorder(finalimg, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=[255, 255])

                    out = pytesseract.image_to_string(border, config='--psm 4')
                    if len(out) == 0:
                        out = pytesseract.image_to_string(border, config='--psm 10')
                    inner = inner + " " + out
                outer.append(inner)

        # Creating a dataframe of the generated OCR list
        arr = np.array(outer)
        return self.clean_dataframe(DataFrame(arr.reshape(count_row, count_col)))

    def clean_dataframe(self, df: DataFrame) -> DataFrame:
        df = df.applymap(whitespaces_clean)
        df.drop(df.columns[[0, len(df.columns) - 1]], axis=1, inplace=True)

        remove = []
        # remove rows without any content
        for index, row in df.iterrows():
            col_with_content = 0
            for _, col in row.items():
                content = whitespaces_clean(col)
                if content and len(content) > 5:
                    col_with_content += 1
            if col_with_content < 2:  # check we at least have (maybe) name and final time
                remove.append(index)
        df.drop(remove, inplace=True)

        return df

    ####################################################
    #                      GETTERS                     #
    ####################################################

    def get_name(self, image: str, **kwargs) -> str:
        for line in image.split('\n'):
            if any(w in line for w in ['@', 'inforemo']):
                continue

            match = re.match(r'^[a-zA-ZñÑ ]+$', whitespaces_clean(remove_symbols(line)))
            if match and len(match.group(0)) > 5:
                return match.group(0)

    def get_date(self, image: str, **kwargs) -> date:
        for line in image.split('\n'):
            match = re.findall(r'\d{1,2} [a-zA-ZñÑ]+ 20\d{2}', whitespaces_clean(line))
            if not len(match):
                continue

            try:
                return datetime.strptime(match[0], '%d %B %Y')
            except ValueError:
                continue

    def get_town(self, image: str, **kwargs) -> Optional[str]:
        name = self.get_name(image)
        for line in image.split('\n'):
            if any(w in line for w in ['@', 'inforemo']):
                continue
            line = whitespaces_clean(remove_symbols(line))
            if line == name:
                continue
            match = re.match(r'^[a-zA-ZñÑ \-0]+$', line)
            if match and len(match.group(0)) > 4:
                return match.group(0)

    def get_gender(self, data, **kwargs) -> str:
        gender = data[2]
        for k, v in self._GENDERS.items():
            if gender in v or any(part in gender for part in v):
                gender = k
                break
        return gender

    def get_modality(self, data, **kwargs) -> str:
        modality = data[2]
        if 'VETERANO' in modality:
            return RACE_VETERANS
        return RACE_TRAINERA

    def get_club_name(self, data, **kwargs) -> str:
        return data[1]

    def get_lane(self, data, **kwargs) -> int:
        try:
            # if : means we are in a TIME_TRIAL image so all the boats will be in the same lane
            return 1 if ':' in data[4] else int(data[4])
        except ValueError:
            return 1

    def get_series(self, data, **kwargs) -> int:
        try:
            return int(data[3])
        except ValueError:
            return 1

    @staticmethod
    def clean_lap(maybe_tyme: str) -> str:
        # clean normal OCR errors
        maybe_tyme = maybe_tyme.replace('"a', '4:').replace('T', '').replace('_', '')
        maybe_tyme = maybe_tyme.replace('::', ':')

        return whitespaces_clean(maybe_tyme)

    def get_laps(self, data, **kwargs) -> List[str]:
        idx = 3 if ':' in data[4] else 4
        return [t.isoformat() for t in [self.normalize_time(self.clean_lap(t)) for t in data.iloc[idx:]] if t]

    def get_race_lanes(self, df: DataFrame, **kwargs) -> int:
        lanes = max(row[4] for _, row in df.iterrows())
        try:
            lanes = int(lanes)
            return lanes if lanes < 7 else 1
        except ValueError:
            return 1

    def get_race_laps(self, df: DataFrame, **kwargs) -> int:
        return len(df.columns) - 4

    def normalized_club_name(self, name: str, **kwargs) -> str:
        new_name = super(ImageOCRInforemo, self).normalized_club_name(name)
        new_name = remove_symbols(new_name, ignore_quotes=True)
        new_name = new_name.replace('\'', '"')  # normalize quotes

        return new_name

    ####################################################
    #                 DEFAULT VALUES                   #
    ####################################################

    @staticmethod
    def get_edition(**kwargs) -> int:
        return 1

    def get_league(self, **kwargs) -> Optional[str]:
        return None

    def get_day(self, **kwargs) -> int:
        return 1

    def get_organizer(self, **kwargs) -> Optional[str]:
        return None