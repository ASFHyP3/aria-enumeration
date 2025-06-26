"""Module for enumerating inputs for ARIA S1 GUNW products."""

import datetime
import importlib.resources
import json
from collections import defaultdict
from dataclasses import dataclass

import asf_search as asf
import shapely


@dataclass(frozen=True)
class AriaFrame:
    """Class for representing an aria frame.

    Args:
        frame_id: aria frame id
        path: path the frame is on
        flight direction

    """

    id: int
    path: int
    flight_direction: str
    polygon: shapely.Polygon

    def does_intersect(self, geometry: shapely.Geometry) -> bool:
        """Check if geometry intersects aria frame.

        Args:
            geometry: shapely geometry to check frames against

        Returns:
            does_intersect: if the frame instersects the geometry
        """
        return shapely.intersects(self.polygon, geometry)

    @property
    def wkt(self) -> str:
        """Get the wkt of the frames polygon.

        Returns:
            wkt: The wkt of the aria frame
        """
        return shapely.to_wkt(self.polygon)


@dataclass(frozen=True)
class Sentinel1Acquisition:
    """Class respresenting a Sentinel 1 acquisition overa given aria frame.

    Args:
         date: the date of the acquisition
         frame: aria frame the the acquisition covers
         products: list of SLC's from the acquisition

    """

    date: datetime.date
    frame: AriaFrame
    products: list[asf.ASFProduct]


class InvalidFrameIdError(Exception):
    """Exception for Frame ID being out of range."""

    pass


def _validate_frame_id(frame_id: int) -> None:
    if frame_id not in FRAMES_BY_ID:
        raise InvalidFrameIdError(f'Frame ID is out of range [0, 27397] given {frame_id}')


def _load_aria_frames_by_id() -> dict[int, AriaFrame]:
    frames_by_id = {}

    with importlib.resources.path('aria_enumeration.aria_frames', 'frames.geojson') as frame_file:
        frames = json.loads(frame_file.read_text())

    for frame in frames['features']:
        props = frame['properties']

        aria_frame = AriaFrame(
            id=props['id'],
            path=props['path'],
            flight_direction=props['dir'],
            polygon=shapely.Polygon(frame['geometry']['coordinates'][0]),
        )

        frames_by_id[aria_frame.id] = aria_frame

    return frames_by_id


FRAMES_BY_ID = _load_aria_frames_by_id()


def get_frames(
    geometry: shapely.Geometry | None = None, flight_direction: str | None = None, path: int | None = None
) -> list[AriaFrame]:
    """Get all aria frames that match filter parameters.

    Args:
        geometry: get all frames intersecting polygon
        flight_direction: filter by either 'ASCENDING' or 'DESCENDING'
        path: path to filter frames

    Returns:
        aria_frames: list of aria frames
    """
    aria_frames = []

    for frame in FRAMES_BY_ID.values():
        if flight_direction and flight_direction.upper() != frame.flight_direction:
            continue

        if path and path != frame.path:
            continue

        if geometry and not frame.does_intersect(geometry):
            continue

        aria_frames.append(frame)

    return aria_frames


def get_frame(frame_id: int) -> AriaFrame:
    """Get a single aria frame by it's frame ID .

    Returns:
        aria_frame: the aria frame with the given ID
    """
    _validate_frame_id(frame_id)
    return FRAMES_BY_ID[frame_id]


def get_acquisitions(frame_id: int) -> list[Sentinel1Acquisition]:
    """Get all the possible Sentinel 1 aquisitions over a given frame ID.

    Args:
        frame_id: the aria frame to get the aquisitions from

    Returns:
        aquisitions: All the Sentinel 1 acquisitions for a given frame
    """
    frame = get_frame(frame_id)
    granules = _get_granules_for(frame)
    aquisitions = _get_acquisitions_from(granules, frame)
    aquisitions.sort(key=lambda group: group.date)

    return aquisitions


def _get_granules_for(frame: AriaFrame, date: datetime.date | None = None) -> asf.ASFSearchResults:
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


def _get_acquisitions_from(granules: asf.ASFSearchResults, frame: AriaFrame) -> list[Sentinel1Acquisition]:
    groups = defaultdict(list)
    for granule in granules:
        props = granule.properties
        group_id = f'{props["platform"]}_{props["orbit"]}'
        groups[group_id].append(granule)

    def get_date_from_group(group: list[asf.ASFProduct]) -> datetime.date:
        return min(_date_from_granule(granule) for granule in group)

    s1_acquisitions = [
        Sentinel1Acquisition(date=get_date_from_group(group), frame=frame, products=[product for product in group])
        for group in groups.values()
    ]

    return s1_acquisitions


def get_acquisition(frame_id: int, date: datetime.date) -> Sentinel1Acquisition:
    """Get a Sentinel 1 acquisition for a given frame and date.

    Args:
        frame_id: aria frame ID
        date: date of the acquisition

    Returns:
        acquisition: Sentiel 1 acquisition

    """
    frame = get_frame(frame_id)
    products = _get_granules_for(frame, date)
    acquisition = Sentinel1Acquisition(date=date, frame=frame, products=products)

    return acquisition


def product_exists(frame_id: int, reference_date: datetime.date, secondary_date: datetime.date) -> bool:
    """Check if aria product already exists.

    Args:
        frame_id: aria frame ID
        reference_date: Reference date of the product
        secondary_date: Secondary date of the product

    Returns:
        exists_in_archive: whether the product already exists in ASF's archive

    """
    _validate_frame_id(frame_id)
    date_buffer = datetime.timedelta(days=1)
    params = {
        'dataset': asf.constants.DATASET.ARIA_S1_GUNW,
        'frame': frame_id,
        'start': (reference_date - date_buffer),
        'end': (reference_date + date_buffer),
    }

    results = asf.search(**params)
    exists_in_archive = any(
        [_dates_match(result.properties['sceneName'], reference_date, secondary_date) for result in results]
    )

    return exists_in_archive


def _dates_match(granule: str, reference: datetime.date, secondary: datetime.date) -> bool:
    date_strs = granule.split('-')[6].split('_')
    granule_reference, granule_secondary = [
        datetime.datetime.strptime(date_str, '%Y%m%d').date() for date_str in date_strs
    ]

    return granule_reference == reference and granule_secondary == secondary


def _date_from_granule(granule: asf.ASFProduct) -> datetime.date:
    start_time = granule.properties['startTime']
    return datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S%z').date()
