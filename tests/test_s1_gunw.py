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


def test_s1_gunw_frame_wkt():
    wkt = s1_gunw.get_frame(100).wkt

    assert 'POLYGON' in wkt


def test_get_frames_by_path():
    frames = s1_gunw.get_frames(path=100)

    assert all([frame.path == 100 for frame in frames])


def test_get_frames_by_flight_direction():
    ascending = s1_gunw.get_frames(flight_direction='ASCENDING')
    assert all([frame.flight_direction == 'ASCENDING' for frame in ascending])

    descending = s1_gunw.get_frames(flight_direction='DESCENDING')
    assert all([frame.flight_direction == 'DESCENDING' for frame in descending])


@pytest.mark.network
def test_get_stack():
    stack = s1_gunw.get_acquisitions(200)
    assert len(stack) > 0


@pytest.mark.network
def test_get_slcs():
    slcs = s1_gunw.get_slcs(200, date(2025, 5, 28))

    assert slcs


@pytest.mark.network
def test_product_exists():
    # 'S1-GUNW-D-R-163-tops-20250527_20250503-212910-00121E_00010S-PP-07c7-v3_0_1'
    assert s1_gunw.product_exists(25388, date(2025, 5, 27), date(2025, 5, 3))

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
