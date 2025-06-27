# ASF Enumeration

Enumeration code for [ARIA S1 GUNW](https://hyp3-docs.asf.alaska.edu/guides/gunw_product_guide/) products

```python
>>> from asf_enumeration import aria_s1_gunw

>>> frames = aria_s1_gunw.get_frames(flight_direction='ASCENDING', path=175)
>>> frames[0]
AriaFrame(id=27236, path=175, flight_direction='ASCENDING', polygon=<POLYGON ((30.157 1.767...>)))

>>> acquisitions = aria_s1_gunw.get_acquisitions(frames[0])
>>> acquisitions[0]
Sentinel1Acquisition(date=datetime.date(2014, 10, 17), frame=AriaFrame(...), products=[<asf_search.ASFProduct>])
```

## Installation

In order to easily manage dependencies, we recommend using dedicated project
environments via [Anaconda/Miniconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
or [Python virtual environments](https://docs.python.org/3/tutorial/venv.html).

`asf_enumeration` can be installed into a conda environment with:

```
conda install -c conda-forge asf_enumeration
```

or into a virtual environment with:

```
python -m pip install asf_enumeration
```

## Usage

These are the main data classes used by the `asf_enumeration.aria_s1_gunw` module
   - `AriaFrame` which represents all metadata associated with a ARIA frame (id, path, flight direction and it's polygon)
   - `Sentinel1Acquisition` which represents all available Sentinel-1 SLC's over an ARIA frame on a specific date (products, date, frame)

The `asf_enumeration.aria_s1_gunw` module exposes these functions
   - `get_frames` get all ARIA frames based on filter critiria (geometry, flight direction, path)
   - `get_frame` get a single ARIA frame based on it's ID
   - `get_acquisitions` get all Sentinel-1 acquisitions for a given ARIA frame
   - `get_acquisition` get a Sentinel-1 acquisition for a given ARIA frame and date
   - `product_exists` check if an ARIA product exists in the ASF archive given an ARIA frame, reference date and secondary date

### Getting Frames

`aria_s1_gunw.get_frames` allows for filtering based on any `shapely.Geometry`, as well as `flight_direction` and `path`

```python
frames_over_point = aria_s1_gunw.get_frames(geometry=shapely.Point(122.78, -8.55))
frames_filtered  = aria_s1_gunw.get_frames(flight_direction='DESCENDING', path=2)
```

A single frame can be looked up using `aria_s1_gunw.get_frame`

```python
frame = aria_s1_gunw.get_frame(100)
```

### Getting Acquisitions

`aria_s1_gunw.get_acquisitions` returns all the Sentinel-1 acqusitions over a ARIA frame. It takes either the ARIA frame ID or an `AriaFrame` object as input.

```python
acquisitions_frame_id = aria_s1_gunw.get_acquisitions(9852)
frame = aria_s1_gunw.get_frame(9852)
acquisitions_frame_obj = aria_s1_gunw.get_acquisitions(frame)
```

An acquisition for a specific date can be found using `aria_s1_gunw.get_acquisition`

```python
single_acquisition = aria_s1_gunw.get_acquisition(frame=9852, date=datetime.date(2014, 11, 3))
```

### Checking if a Product Exists

`aria_s1_gunw.product_exists` checks if an ARIA product already exists in the ASF archive

```python
    # S1-GUNW-D-R-163-tops-20250527_20250503-212910-00121E_00010S-PP-07c7-v3_0_1
    aria_s1_gunw.product_exists(25388, datetime.date(2025, 5, 27), datetime.date(2025, 5, 3))
```


## Development

1. Install [git](https://git-scm.com/) and [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).
1. Clone the repository.
   ```
   git clone git@github.com:ASFHyP3/asf-enumeration.git
   cd asf-enumeration
   ```
1. Create and activate the conda environment.
   ```
   conda env create -f environment.yml
   conda activate asf-enumeration
   ```
1. Run the tests.
   ```
   pytest
   ```
