# Bk2MapCreator
Simple Python script for creating Blitzkrieg2 binary map files (so far only square maps are supported).

This script allows to overcome Blitzkrieg 2 Editor limitations and create maps larger than 20x20, it should be noted maps larger than 22x22 may suffer from Blitzkrieg2 culling system and not display properly. This can be in part mitigated by changing camera limits, and zooming out more than usually allowed. 

## Requirements
- Python3 

## Installing

Example installation with `pipenv`.

```bash
pip install virtualenv
pip install pipenv
python -m venv venv
python -m pipenv install opencv-python
python -m pipenv shell
python -m pipenv run main.py
```

`pipenv` is not a requirement, PyCharm works out of the box as well.

## Running with pipenv

```bash
python -m pipenv run main.py
```

## Changing map size

Make sure that the [input/map.b2m](input/map.b2m) exists and is the only file in the input folder.

In [main.py](main.py) there's two changes that have to be done.
- Set the current map size by changing `14` in `MAP_FILE_N = 14` on line 21 to the current map size.
- Set the desired map size by changing `20` in `map_creator.n = 20` on line 542 to the desired map size.

## Creating a map from a height image and texture image
Paste the heightmap into [input/map.png](input/map.png).
Paste the texturemap into [input/map2.png](input/map2.png).

In [main.py](main.py) there's two changes that have to be done.
- Set `b2m` in `IMPORT_FROM_FILES = b2m` on line 23 to 'png'
- Set the desired map size by changing `20` in `map_creator.n = 20` on line 542 to the desired map size.
 
If you want to use only a heightmap or only a texture image keep only `input/map.png` or `input/map2.png` respectively.

### Converting rgb to textures

Set the current map season and rgb values for textures starting on line 27. 

### Setting map height

Set `MAX_HEIGHT` on line 23 to determine the in game height for the highest point on the heightmap.
