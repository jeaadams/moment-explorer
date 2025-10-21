# Moment Explorer

Interactive Plotly-based moment map visualization tool for FITS spectral cubes, powered by [bettermoments](https://github.com/richteague/bettermoments).

## Features

- **Multiple moment types**: M0 (integrated intensity), M1 (velocity), M8 (peak intensity), M9 (linewidth)
- **Multi-cube explorer**: Dropdown selector to switch between multiple cubes
- **Cube viewer**: Channel-by-channel visualization with mask overlay
- **Interactive launcher**: File browser UI for easy cube/mask selection
- **WCS support**: Automatic coordinate display when FITS headers are available
- **Interactive controls**: ipywidgets for channel range, clipping, masking, and color scales
- **One-click FITS export**: Save moment maps (and uncertainties) directly from the UI
- **Smart sigma clipping**: Works for all moment types with intelligent warnings

## Installation

### From source (development)

```bash
git clone https://github.com/jeaadams/moment-explorer.git
cd moment-explorer
pip install -e .
```

### Dependencies

- Python >= 3.8
- numpy >= 1.20
- astropy >= 5.0
- bettermoments >= 1.0
- plotly >= 5.0
- ipywidgets >= 8.0

## Command-Line Usage

After installation, the `moment-explorer` command is available:

```bash
# Launch Jupyter Lab with the example notebook
moment-explorer notebook

# Copy the example notebook to the current directory
moment-explorer notebook --here

# Display help
moment-explorer --help
```

The `moment-explorer notebook` command automatically opens Jupyter Lab with the example notebook.

## Quick Start

### Option 1: Multi-Cube Explorer (Recommended)

Easily switch between multiple cubes with a dropdown selector:

```python
from moment_explorer import create_multi_cube_explorer
import os

# Define your cubes
available_cubes = {
    'N2H+': {
        'cube': 'path/to/N2H+_cube.fits',
        'mask': 'path/to/N2H+_mask.fits',
    },
    'HCN': {
        'cube': 'path/to/HCN_cube.fits',
        'mask': 'path/to/HCN_mask.fits',
    }
}

# Create explorer with cube selector
explorer, ui, selector = create_multi_cube_explorer(available_cubes)
```

### Option 2: Cube Viewer (Channel Explorer)

Explore individual channels with mask overlay:

```python
from moment_explorer import create_cube_viewer

# Create channel-by-channel viewer
viewer = create_cube_viewer(
    cube_path='path/to/cube.fits',
    mask_path='path/to/mask.fits'  # optional
)
```

All UI options display automatically with:
- Dropdown for moment type selection (M0, M1, M8, M9)
- Sliders for channel range and clipping threshold
- Checkbox for mask application
- Color scale selector
- Auto-apply toggle with debouncing
- Apply, Save FITS, and Reset View buttons

## Usage Guide

### Interactive Controls

**Moment Dropdown**
- Select M0 (integrated intensity), M1 (velocity), M8 (peak), or M9 (linewidth)
- Switching moment types triggers immediate update
- Colorscale automatically adjusts for M1 (velocity maps use RdBu_r)

**Channel Sliders**
- Set first and last channel for moment map computation
- Range automatically adjusts when switching cubes

**Clip σ Slider** (range: 0.0 to 10.0)
- **0.0**: No clipping (recommended for M0)
- **>0**: Excludes pixels below σ × RMS from the calculation
- Smart warnings appear when using inappropriate clipping (e.g., M0 with clipping)

**Auto-Apply Checkbox**
- When enabled: Updates automatically after 200ms of inactivity
- When disabled: Use "Apply" button for manual control
- Recommended: Enable for exploration, disable for precise control

**Buttons**
- **Apply**: Manually update the plot with current settings
- **Save FITS**: Save both moment map and uncertainty (dM0, dM1, etc.) to FITS files
- **Reset View**: Restore default zoom/pan state

### Sigma Clipping Best Practices

| Moment | Recommended Clip σ | Reason |
|--------|-------------------|--------|
| **M0** | **0** | Preserves total flux; faint emission contributes to integrated intensity |
| **M1** | **3-5** | Excludes noise from velocity measurements |
| **M8** | **0** | Peak is already robust; use mask for spatial selection |
| **M9** | **3-5** | Prevents noise from artificially broadening lines |

**Warning System**: Orange warning appears if you use M0 with clipping enabled, reminding you this underestimates total flux.

### Cube Viewer Controls

**Channel Slider**
- Navigate through all channels of your cube
- Updates velocity display in plot title

**Intensity Scaling**
- Manual vmin/vmax controls or auto-scaling (1st to 99th percentile)
- Auto-scale checkbox updates scaling on each channel change

**Mask Overlay**
- Toggle red contour overlay showing mask boundaries
- Useful for verifying mask coverage across channels

**Use Cases**
- Find emission channels before creating moment maps
- Verify mask coverage across velocity range
- Check for artifacts or bad channels
- Explore velocity structure channel-by-channel

### Saving Moment Maps

When you click "Save FITS", the following files are saved:

```
# Moment map
/path/to/cube_M0.fits

# Uncertainty map
/path/to/cube_dM0.fits
```

Files are saved in the same directory as your input cube with automatic naming:
- `{cube_name}_M0.fits`, `{cube_name}_dM0.fits` (integrated intensity + uncertainty)
- `{cube_name}_M1.fits`, `{cube_name}_dM1.fits` (velocity + uncertainty)
- `{cube_name}_M8.fits`, `{cube_name}_dM8.fits` (peak + uncertainty)
- `{cube_name}_M9.fits`, `{cube_name}_dM9.fits` (linewidth + uncertainty)

FITS headers include metadata:
- Moment type and parameters used
- Channel range
- Clipping threshold
- Proper WCS coordinates (2D projection of cube WCS)
- Correct BUNIT (Jy/beam km/s for M0, km/s for M1/M9, etc.)

## Programmatic Usage

```python
from moment_explorer import MomentMapExplorer

# Create explorer and load cube
explorer = MomentMapExplorer()
explorer.load_cube('path/to/cube.fits', 'path/to/mask.fits')

# Generate a moment map
moment_map, compute_time = explorer.generate(
    moment='M0',
    first=30,
    last=70,
    clip_sigma=0.0,  # No clipping for M0
    use_mask=True
)

print(f"Computed in {compute_time*1000:.1f} ms")

# Save to FITS (returns list of paths: [moment_map, uncertainty_map])
output_paths = explorer.save()
for path in output_paths:
    print(f"Saved to {path}")
```

### Batch Processing Example

```python
from moment_explorer import MomentMapExplorer

cubes = ['cube1.fits', 'cube2.fits', 'cube3.fits']
masks = ['mask1.fits', 'mask2.fits', 'mask3.fits']

for cube, mask in zip(cubes, masks):
    explorer = MomentMapExplorer()
    explorer.load_cube(cube, mask)

    # Generate all moment types
    for moment in ['M0', 'M1', 'M8', 'M9']:
        clip_sigma = 0.0 if moment in ['M0', 'M8'] else 3.0
        explorer.generate(moment, 30, 70, clip_sigma, True)
        paths = explorer.save()
        print(f"{moment}: {paths[0]}")
```

## API Reference

### `MomentMapExplorer`

Core class for moment map computation.

**Methods:**

- **`load_cube(cube_path, mask_path=None)`**
  - Load FITS cube and optional mask
  - Returns: Dictionary with cube info (shape, velocity range, RMS, etc.)

- **`generate(moment, first, last, clip_sigma, use_mask)`**
  - Compute a moment map
  - `moment`: 'M0', 'M1', 'M8', or 'M9'
  - `first`, `last`: Channel range (inclusive)
  - `clip_sigma`: Clipping threshold in units of RMS (0 = no clipping)
  - `use_mask`: Boolean to apply user mask
  - Returns: `(moment_map, compute_time)`

- **`save(path=None)`**
  - Save current moment map and uncertainty to FITS
  - If `path` is None, auto-generates filename based on cube path
  - Returns: List of paths `[moment_path, uncertainty_path]`

- **`get_wcs_extent()`**
  - Get WCS extent for plotting
  - Returns: `(xmin, xmax, ymin, ymax)` in arcsec offsets, or None

### `create_multi_cube_explorer`

Create an explorer with dropdown selector for multiple cubes.

```python
explorer, ui, selector = create_multi_cube_explorer(
    available_cubes,
    default_cube=None  # Optional: cube key to load first
)
```

Returns:
- `explorer`: MomentMapExplorer instance
- `ui`: MomentMapUI instance
- `selector`: Dropdown widget for cube selection

### `create_cube_viewer`

Create a channel-by-channel viewer with mask overlay.

```python
viewer = create_cube_viewer(
    cube_path,
    mask_path=None
)
```

Returns:
- `viewer`: CubeMaskViewer instance with UI displayed

## Examples

See [`examples/interactive_moment_maker.ipynb`](examples/interactive_moment_maker.ipynb) for a complete Jupyter notebook demo including:
- Multi-cube explorer with dropdown
- Single-cube explorer
- Cube viewer for channel exploration
- Launcher UI for file selection
- Programmatic usage examples
- Batch processing workflows

## Troubleshooting

**Issue**: Moment dropdown doesn't update the plot

**Solution**: This is now fixed - moment dropdown always triggers immediate update. Restart your Jupyter kernel if using an old version.

---

**Issue**: Error "Use `clip=None` to not use a threshold mask"

**Solution**: This is fixed in the latest version. Set clip σ = 0 for no clipping. Restart your kernel after updating.

---

**Issue**: Can't find saved FITS files

**Solution**: Files are saved in the same directory as your input cube. Check the console output after clicking "Save FITS" for the full absolute path.

---

**Issue**: Widgets not displaying

**Solution**:
```bash
# For JupyterLab
jupyter labextension install @jupyter-widgets/jupyterlab-manager

# For classic Jupyter
jupyter nbextension enable --py widgetsnbextension

# Restart Jupyter
```

---

**Issue**: Plotly figure not rendering

**Solution**:
```bash
pip install plotly>=5.0 kaleido
pip install "jupyterlab>=3" "ipywidgets>=7.6"

# Restart Jupyter
```

---

**Issue**: Slow updates

**Solution**:
- Disable auto-apply for large cubes
- Use the Apply button for manual control
- Close other notebook cells/viewers

## Performance Notes

### In-Place Updates

The Plotly figure uses in-place updates for smooth performance:

```python
with fig.batch_update():
    fig.data[0].z = new_map
    fig.layout.coloraxis.cmin = vmin
    fig.layout.coloraxis.cmax = vmax
```

This avoids recreating the entire figure and preserves zoom/pan state via `uirevision="moment_explorer_v1"`.

### Debouncing

When "Auto-apply" is enabled, a 200ms debounce timer prevents excessive recomputation during slider dragging.

### WebGL Acceleration

The UI automatically tries to use `Heatmapgl` (WebGL-accelerated) but falls back to standard `Heatmap` if not available. For best performance, use Plotly >= 5.0.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use this package in your research, please cite:

- [bettermoments](https://github.com/richteague/bettermoments) (Teague & Foreman-Mackey 2018)
- This package (citation coming soon)

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

## Acknowledgments

Built on top of the excellent [bettermoments](https://github.com/richteague/bettermoments) package by Richard Teague.
