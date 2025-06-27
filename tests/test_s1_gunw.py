import re
from datetime import date

import pytest
import shapely

from aria_enumeration import s1_gunw


def test_get_frames():
    wkt = 'POLYGON((-128.0401 57.1054,-127.7544 57.1054,-127.7544 57.2034,-128.0401 57.2034,-128.0401 57.1054))'
    search_polygon = shapely.from_wkt(wkt)

    frames = s1_gunw.get_frames()
    assert len(frames) == 27398

    frames = s1_gunw.get_frames(geometry=search_polygon)
    assert len(frames) == 8

    ascending = s1_gunw.get_frames(geometry=search_polygon, flight_direction='ASCENDING')
    assert len(ascending) == 4

    all_filters = s1_gunw.get_frames(geometry=search_polygon, flight_direction='ASCENDING', path=35)
    assert len(all_filters) == 2


def test_get_frames_by_path():
    frames = s1_gunw.get_frames(path=100)

    assert all(frame.path == 100 for frame in frames)


def test_get_frames_by_flight_direction():
    ascending = s1_gunw.get_frames(flight_direction='ASCENDING')
    assert all(frame.flight_direction == 'ASCENDING' for frame in ascending)

    descending = s1_gunw.get_frames(flight_direction='DESCENDING')
    assert all(frame.flight_direction == 'DESCENDING' for frame in descending)

    with pytest.raises(s1_gunw.AriaEnumerationError, match='Invalid flight direction, must be either "ASCENDING" or "DESCENDING"'):
        s1_gunw.get_frames(flight_direction='foo')  # type: ignore


def test_s1_gunw_frame():
    frame = s1_gunw.get_frame(100)

    assert frame.id == 100

    with pytest.raises(s1_gunw.AriaEnumerationError, match=re.escape('Frame ID is out of range [0, 27397] given 27398')):
        s1_gunw.get_frame(27398)

    with pytest.raises(s1_gunw.AriaEnumerationError, match=re.escape('Frame ID is out of range [0, 27397] given -1')):
        s1_gunw.get_frame(-1)


@pytest.mark.network
def test_get_acquisitions():
    frame = s1_gunw.get_frame(200)

    acquisitions = s1_gunw.get_acquisitions(frame)

    assert all(
        [
            frame_version.date == id_version.date
            for (frame_version, id_version) in zip(acquisitions, s1_gunw.get_acquisitions(200))
        ]
    )
    assert all(acquisition.frame.id == 200 for acquisition in acquisitions)
    assert all(len(acquisition.products) <= 3 for acquisition in acquisitions)

    # TODO: Better acquisition testing


@pytest.mark.network
def test_get_acquisition():
    frame = s1_gunw.get_frame(200)
    acquisition = s1_gunw.get_acquisition(frame, date(2025, 5, 28))

    assert acquisition.date == s1_gunw.get_acquisition(200, date(2025, 5, 28)).date
    assert acquisition.frame.id == 200
    assert all(s1_gunw._date_from_granule(product) == date(2025, 5, 28) for product in acquisition.products)


@pytest.mark.network
def test_product_exists():
    frame = s1_gunw.get_frame(25388)
    # 'S1-GUNW-D-R-163-tops-20250527_20250503-212910-00121E_00010S-PP-07c7-v3_0_1'
    assert s1_gunw.product_exists(frame, date(2025, 5, 27), date(2025, 5, 3))
    assert s1_gunw.product_exists(frame.id, date(2025, 5, 27), date(2025, 5, 3))

    assert not s1_gunw.product_exists(25388, date(2025, 5, 26), date(2025, 5, 3))


def test_dates_match():
    assert s1_gunw._dates_match(
        'S1-GUNW-D-R-163-tops-20250527_20250503-212910-00121E_00010S-PP-07c7-v3_0_1',
        date(2025, 5, 27),
        date(2025, 5, 3),
    )

    assert not s1_gunw._dates_match(
        'S1-GUNW-D-R-163-tops-20250527_20250503-212910-00121E_00010S-PP-07c7-v3_0_1',
        date(2024, 5, 27),
        date(2024, 5, 3),
    )
