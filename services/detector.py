import easyocr

from models.region import Region


class TextDetector:

    def __init__(self):

        self.reader = easyocr.Reader(
            ['en'],
            gpu=False
        )

    def detect(self, image_path):

        results = self.reader.readtext(
            image_path
        )

        regions = []

        for idx, item in enumerate(results):

            regions.append(
                Region(
                    id=idx,
                    polygon=item[0],
                    text=item[1]
                )
            )

        return regions