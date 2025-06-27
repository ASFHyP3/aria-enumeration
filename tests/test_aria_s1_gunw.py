import re
from datetime import date

import pytest
import shapely

from asf_enumeration import aria_s1_gunw


def test_get_frames():
    wkt = 'POLYGON((-128.0401 57.1054,-127.7544 57.1054,-127.7544 57.2034,-128.0401 57.2034,-128.0401 57.1054))'
    search_polygon = shapely.from_wkt(wkt)

    frames = aria_s1_gunw.get_frames()
    assert len(frames) == 27398

    frames = aria_s1_gunw.get_frames(geometry=search_polygon)
    assert len(frames) == 8

    ascending = aria_s1_gunw.get_frames(geometry=search_polygon, flight_direction='ASCENDING')
    assert len(ascending) == 4

    all_filters = aria_s1_gunw.get_frames(geometry=search_polygon, flight_direction='ASCENDING', path=35)
    assert len(all_filters) == 2


def test_get_frames_by_path():
    frames = aria_s1_gunw.get_frames(path=100)

    assert all(frame.path == 100 for frame in frames)


def test_get_frames_by_flight_direction():
    ascending = aria_s1_gunw.get_frames(flight_direction='ASCENDING')
    assert all(frame.flight_direction == 'ASCENDING' for frame in ascending)

    descending = aria_s1_gunw.get_frames(flight_direction='DESCENDING')
    assert all(frame.flight_direction == 'DESCENDING' for frame in descending)

    with pytest.raises(
        aria_s1_gunw.AriaEnumerationError, match='Invalid flight direction, must be either "ASCENDING" or "DESCENDING"'
    ):
        aria_s1_gunw.get_frames(flight_direction='foo')  # type: ignore


def test_aria_s1_gunw_frame():
    frame = aria_s1_gunw.get_frame(100)

    assert frame.id == 100

    with pytest.raises(
        aria_s1_gunw.AriaEnumerationError, match=re.escape('Frame ID is out of range [0, 27397] given 27398')
    ):
        aria_s1_gunw.get_frame(27398)

    with pytest.raises(
        aria_s1_gunw.AriaEnumerationError, match=re.escape('Frame ID is out of range [0, 27397] given -1')
    ):
        aria_s1_gunw.get_frame(-1)


@pytest.mark.network
def test_get_acquisitions():
    frame = aria_s1_gunw.get_frame(200)

    acquisitions = aria_s1_gunw.get_acquisitions(frame)

    assert all(
        [
            frame_version.date == id_version.date
            for (frame_version, id_version) in zip(acquisitions, aria_s1_gunw.get_acquisitions(200))
        ]
    )
    assert all(acquisition.frame.id == 200 for acquisition in acquisitions)
    assert all(len(acquisition.products) <= 3 for acquisition in acquisitions)

    # TODO: Better acquisition testing


@pytest.mark.network
def test_get_acquisition():
    frame = aria_s1_gunw.get_frame(200)
    acquisition = aria_s1_gunw.get_acquisition(frame, date(2025, 5, 28))

    assert acquisition.date == aria_s1_gunw.get_acquisition(200, date(2025, 5, 28)).date
    assert acquisition.frame.id == 200
    assert all(aria_s1_gunw._date_from_granule(product) == date(2025, 5, 28) for product in acquisition.products)


@pytest.mark.network
def test_acquisition_from_standard_products():
    # S1-GUNW-A-R-064-tops-20241216_20241204-015158-00120W_00038N-PP-6e8f-v3_0_1
    frame_id = 9852
    ref_acquisition = aria_s1_gunw.get_acquisition(frame_id, date(2024, 12, 16))
    sec_acquisition = aria_s1_gunw.get_acquisition(frame_id, date(2024, 12, 4))

    assert set(product.properties['sceneName'] for product in ref_acquisition.products) == {
        'S1A_IW_SLC__1SDV_20241216T015132_20241216T015159_057011_070161_9D6A',
        'S1A_IW_SLC__1SDV_20241216T015157_20241216T015224_057011_070161_F3FE',
    }

    assert set(product.properties['sceneName'] for product in sec_acquisition.products) == {
        'S1A_IW_SLC__1SDV_20241204T015133_20241204T015200_056836_06FA75_6070',
        'S1A_IW_SLC__1SDV_20241204T015158_20241204T015225_056836_06FA75_BB7D',
    }

    # S1-GUNW-A-R-005-tops-20231124_20231112-004542-00103W_00035N-PP-a548-v3_0_1
    frame_id = 657
    ref_acquisition = aria_s1_gunw.get_acquisition(frame_id, date(2023, 11, 24))
    sec_acquisition = aria_s1_gunw.get_acquisition(frame_id, date(2023, 11, 12))

    assert set(product.properties['sceneName'] for product in ref_acquisition.products) == {
        'S1A_IW_SLC__1SDV_20231124T004516_20231124T004543_051352_063249_3723',
        'S1A_IW_SLC__1SDV_20231124T004541_20231124T004608_051352_063249_4B9E',
    }

    assert set(product.properties['sceneName'] for product in sec_acquisition.products) == {
        'S1A_IW_SLC__1SDV_20231112T004516_20231112T004544_051177_062C3E_C095',
        'S1A_IW_SLC__1SDV_20231112T004541_20231112T004608_051177_062C3E_2A0E',
    }


@pytest.mark.network
def test_product_exists():
    frame = aria_s1_gunw.get_frame(25388)
    # 'S1-GUNW-D-R-163-tops-20250527_20250503-212910-00121E_00010S-PP-07c7-v3_0_1'
    assert aria_s1_gunw.product_exists(frame, date(2025, 5, 27), date(2025, 5, 3))
    assert aria_s1_gunw.product_exists(frame.id, date(2025, 5, 27), date(2025, 5, 3))

    assert not aria_s1_gunw.product_exists(25388, date(2025, 5, 26), date(2025, 5, 3))


def test_gunw_dates_match():
    assert aria_s1_gunw._gunw_dates_match(
        'S1-GUNW-D-R-163-tops-20250527_20250503-212910-00121E_00010S-PP-07c7-v3_0_1',
        date(2025, 5, 27),
        date(2025, 5, 3),
    )

    assert not aria_s1_gunw._gunw_dates_match(
        'S1-GUNW-D-R-163-tops-20250527_20250503-212910-00121E_00010S-PP-07c7-v3_0_1',
        date(2024, 5, 27),
        date(2024, 5, 3),
    )
