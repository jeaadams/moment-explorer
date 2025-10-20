# Multi-Cube Explorer Example

The `create_multi_cube_explorer` function allows you to easily switch between multiple cubes using a dropdown selector.

## Usage in Jupyter Notebook

```python
from moment_explorer import create_multi_cube_explorer
import os

# Define your base path
base_path = '/Users/jea/AATau/cleaning_data/'

# Define available cubes
available_cubes = {
    'N2H+ (2013SG2)': {
        'cube': os.path.join(base_path, 'fits_2013SG2/AATau_N2H+_clean1_contsub.fits'),
        'mask': os.path.join(base_path, 'fits_2013SG2/AATau_N2H+_clean0_contsub.mask.fits'),
        'name': 'N$_2$H$^+$'
    },
    'HCN (2013SG1)': {
        'cube': os.path.join(base_path, 'fits_2013SG1/AATau_HCN_clean1_contsub.fits'),
        'mask': os.path.join(base_path, 'fits_2013SG1/AATau_HCN_clean0_contsub.mask.fits'),
        'name': 'HCN'
    },
    'HCO+ (2013SG1)': {
        'cube': os.path.join(base_path, 'fits_2013SG1/AATau_HCO+_clean1_contsub.fits'),
        'mask': os.path.join(base_path, 'fits_2013SG1/AATau_HCO+_clean0_contsub.mask.fits'),
        'name': 'HCO$^{+}$'
    },
    '13CO (2015)': {
        'cube': os.path.join(base_path, 'fits_2015/AATau_13CO_clean1_contsub.fits'),
        'mask': os.path.join(base_path, 'fits_2015/AATau_13CO_clean0_contsub.mask.fits'),
        'name': '$^{13}$CO'
    },
    'C18O (2015)': {
        'cube': os.path.join(base_path, 'fits_2015/AATau_C18O_clean1_contsub.fits'),
        'mask': os.path.join(base_path, 'fits_2015/AATau_C18O_clean0_contsub.mask.fits'),
        'name': 'C$^{18}$O'
    },
    'CN SPW1 (2015)': {
        'cube': os.path.join(base_path, 'fits_2015/AATau_CN_SPW1_clean1_contsub.fits'),
        'mask': os.path.join(base_path, 'fits_2015/AATau_CN_SPW1_clean0_contsub.mask.fits'),
        'name': 'CN J=7/2-5/2'
    },
    'CN SPW3 (2015)': {
        'cube': os.path.join(base_path, 'fits_2015/AATau_CN_SPW3_clean1_contsub.fits'),
        'mask': os.path.join(base_path, 'fits_2015/AATau_CN_SPW3_clean0_contsub.mask.fits'),
        'name': 'CN J=5/2-3/2'
    }
}

# Create the multi-cube explorer
explorer, ui, selector = create_multi_cube_explorer(
    available_cubes,
    enable_prefix_sums=True,
    default_cube='N2H+ (2013SG2)'  # Optional: specify which cube to load first
)
```

## Features

- **Dropdown selector** at the top of the UI to switch between cubes
- **Automatic slider updates** - channel ranges adjust based on the selected cube
- **Live reloading** - switching cubes automatically regenerates the moment map
- **All standard controls** - moment type, channels, clipping, colorscale, etc.

## How It Works

1. **Select a cube** from the dropdown at the top
2. The cube is automatically loaded and a moment map is generated
3. The channel sliders update to match the new cube's channel count
4. Adjust parameters as needed and explore your data
5. Switch to another cube anytime - your UI settings persist where applicable

## Return Values

- `explorer`: The MomentMapExplorer instance (shared across all cubes)
- `ui`: The MomentMapUI instance
- `selector`: The cube selector dropdown widget (in case you want to manipulate it)

## Tips

- The explorer reuses the same instance, so switching cubes is fast
- Prefix-sum optimization is maintained across cube switches
- Your zoom/pan state resets when switching cubes (this is intentional)
- Use the "Save FITS" button to save moment maps for each cube

## Minimal Example

```python
from moment_explorer import create_multi_cube_explorer

# Minimal configuration
cubes = {
    'Cube 1': {'cube': 'path/to/cube1.fits'},
    'Cube 2': {'cube': 'path/to/cube2.fits', 'mask': 'path/to/mask2.fits'}
}

explorer, ui, selector = create_multi_cube_explorer(cubes)
```

That's it! The multi-cube explorer provides all the functionality of the single-cube explorer, plus easy switching between your datasets.
