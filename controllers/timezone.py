from collections import OrderedDict

from models.timezone import read_regions
from views.timezone import TimezoneView

class TimezoneController:
    def __init__(self, app):
        self._app = app
        self._all_regions = OrderedDict()
        for region in read_regions():
            self._all_regions[region.name] = region

        self.region = self.regions[0]
        self.city = self.cities_for_region(self.region)[0]

    @property
    def regions(self) -> list[str]:
        return [k for k in self._all_regions.keys()]

    def cities_for_region(self, region: str) -> list[str]:
        return self._all_regions[region].cities

    def make_ui(self):
        return TimezoneView(self, self.region, self.city)

    def done(self, region: str, city: str):
        self.region = region
        self.city = city
        self._app.next_screen()

    def cancel(self):
        self._app.prev_screen()
