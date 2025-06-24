import datetime
import importlib.resources
import json
from collections import defaultdict
from dataclasses import dataclass

import asf_search as asf
import shapely


@dataclass(frozen=True)
class AriaFrame:
    """Class for representing an aria frame."""
    frame_id: int
    path: int
    flight_direction: str
    polygon: shapely.Polygon

    def does_intersect(self, polygon: shapely.Polygon) -> bool:
        return shapely.intersects(self.polygon, polygon)

    @property
    def wkt(self) -> str:
        return shapely.to_wkt(self.polygon)


@dataclass(frozen=True)
class AriaProductGroup:
    """Class respresenting a valid date and list of SLC products for processing."""
    date: datetime.date
    products: list[asf.ASFProduct]


def _load_aria_frames_by_id() -> dict[int, AriaFrame]:
    frames_by_id = {}

    with importlib.resources.path('aria_enumeration.aria_frames', 'frames.geojson') as frame_file:
        frames = json.loads(frame_file.read_text())

    for frame in frames['features']:
        props = frame['properties']

        aria_frame = AriaFrame(
            frame_id=props['id'],
            path=props['path'],
            flight_direction=props['dir'],
            polygon=shapely.Polygon(frame['geometry']['coordinates'][0]),
        )

        frames_by_id[aria_frame.frame_id] = aria_frame

    return frames_by_id


FRAMES_BY_ID = _load_aria_frames_by_id()


def get_frames(
    polygon: shapely.Polygon | None = None, flight_direction: str | None = None, path: int | None = None
) -> list[AriaFrame]:
    """Get all aria frames that match filter parameters.

    Args:
        polygon: get all frames intersecting polygon
        flight_direction: filter by either 'ASCENDING' or 'DESCENDING'
        path: path to filter by

    Returns:
        aria_frames: list of aria frames
    """
    aria_frames = []

    for frame in FRAMES_BY_ID.values():
        if flight_direction and flight_direction.upper() != frame.flight_direction:
            continue

        if path and path != frame.path:
            continue

        if polygon and not frame.does_intersect(polygon):
            continue

        aria_frames.append(frame)

    return aria_frames


def get_frame(frame_id: int) -> AriaFrame:
    return FRAMES_BY_ID[frame_id]


def get_stack(frame_id: int) -> list[AriaProductGroup]:
    granules = _get_granules_for_frame(frame_id)
    stack = _get_stack_from(granules)
    stack.sort(key=lambda group: group.date)
    return stack


def _get_granules_for_frame(frame_id: int, date: datetime.date = None) -> list[asf.ASFSearchResults]:
    frame = get_frame(frame_id)

    search_params = {
        'dataset': asf.constants.DATASET.SENTINEL1,
        'platform': ['SA', 'SB'],
        'processingLevel': asf.constants.PRODUCT_TYPE.SLC,
        'beamMode': asf.constants.BEAMMODE.IW,
        'polarization': [asf.constants.POLARIZATION.VV, asf.constants.POLARIZATION.VV_VH],
        'flightDirection': frame.flight_direction,
        'relativeOrbit': frame.path,
        'intersectsWith': frame.wkt,
    }

    if date:
        date_as_datetime = datetime.datetime(year=date.year, month=date.month, day=date.day)
        search_params['start'] = date_as_datetime - datetime.timedelta(minutes=5)
        search_params['end'] = date_as_datetime + datetime.timedelta(days=1, minutes=5)

    results = asf.search(**search_params)

    return results


def _get_stack_from(granules: asf.ASFSearchResults) -> list[AriaProductGroup]:
    groups = defaultdict(list)
    for granule in granules:
        props = granule.properties
        group_id = f'{props["platform"]}_{props["orbit"]}'
        groups[group_id].append(granule)

    def _get_date_from_group(group: str) -> datetime.date:
        return min(datetime.datetime.fromisoformat(granule.properties['startTime']).date() for granule in group)

    aria_groups = [
        AriaProductGroup(date=_get_date_from_group(group), products=[product for product in group])
        for group in groups.values()
    ]

    return aria_groups


def get_slcs(frame_id: int, date: datetime.date) -> list[asf.ASFProduct]:
    slcs = _get_granules_for_frame(frame_id, date)

    return slcs


def does_product_exist(frame_id: int, reference_date: datetime.date, secondary_date: datetime.date) -> bool:
    date_buffer = datetime.timedelta(days=1)
    params = {
        'dataset': asf.constants.DATASET.ARIA_S1_GUNW,
        'frame': frame_id,
        'start': (reference_date - date_buffer),
        'end': (reference_date + date_buffer),
    }

    results = asf.search(**params)

    return any([_dates_match(result.properties['sceneName'], reference_date, secondary_date) for result in results])


def _dates_match(granule: str, reference: datetime.date, secondary: datetime.date) -> bool:
    date_strs = granule.split('-')[6].split('_')
    granule_reference, granule_secondary = [
        datetime.datetime.strptime(date_str, '%Y%m%d').date() for date_str in date_strs
    ]

    return granule_reference == reference and granule_secondary == secondary
