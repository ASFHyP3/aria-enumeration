# ASF Enumeration

Enumeration code for [ARIA S1 GUNW](https://hyp3-docs.asf.alaska.edu/guides/gunw_product_guide/) products

```python
>>> from aria_enumeration import s1_gunw

>>> frames = s1_gunw.get_frames(flight_direction='ASCENDING', path=175)
>>> frames[0]
AriaFrame(id=27236, path=175, flight_direction='ASCENDING', polygon=<POLYGON ((30.157 1.767...>)))

>>> acquisitions = s1_gunw.get_acquisitions(frames[0])
>>> acquisitions[0]
Sentinel1Acquisition(date=datetime.date(2014, 10, 17), frame=AriaFrame(...), products=[<asf_search.ASFProduct>])
```

## Installation

In order to easily manage dependencies, we recommend using dedicated project
environments via [Anaconda/Miniconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
or [Python virtual environments](https://docs.python.org/3/tutorial/venv.html).

`aria_enumeration` can be installed into a conda environment with:

```
conda install -c conda-forge aria_enumeration
```

or into a virtual environment with:

```
python -m pip install aria_enumeration
```

## Usage

TODO

## Development

1. Install [git](https://git-scm.com/) and [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html).
1. Clone the repository.
   ```
   git clone git@github.com:ASFHyP3/aria-enumeration.git
   cd aria-enumeration
   ```
1. Create and activate the conda environment.
   ```
   conda env create -f environment.yml
   conda activate aria-enumeration
   ```
1. Run the tests.
   ```
   pytest
   ```
