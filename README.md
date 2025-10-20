# Moment Explorer

Interactive Plotly-based moment map visualization tool for FITS spectral cubes, powered by [bettermoments](https://github.com/richteague/bettermoments).

**New to moment-explorer?** See [GETTING_STARTED.md](GETTING_STARTED.md) for a 5-minute quick start guide.
**Need help finding docs?** Check [INDEX.md](INDEX.md) for a complete navigation guide.
**Migrating from the old notebook?** Read [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md).

## Features

- **Smooth, responsive UI** using Plotly's FigureWidget with persistent zoom/pan
- **Debounced updates** (~200ms) for smooth slider interactions
- **Multiple moment types**: M0 (integrated intensity), M1 (velocity), M8 (peak intensity), M9 (linewidth)
- **Performance optimizations**: Optional prefix-sum acceleration for M0/M1 computation
- **WCS support**: Automatic coordinate display when FITS headers are available
- **Interactive controls**: ipywidgets for channel range, clipping, masking, and color scales
- **One-click FITS export**: Save moment maps directly from the UI

## Installation

### From source (development)

```bash
git clone https://github.com/yourusername/moment-explorer.git
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

## Quick Start

### Interactive UI

```python
from moment_explorer import create_interactive_explorer

# Load a cube and create the interactive UI
explorer, ui = create_interactive_explorer(
    cube_path='path/to/your/cube.fits',
    mask_path='path/to/your/mask.fits',  # optional
    enable_prefix_sums=True  # faster M0/M1 computation
)
```

The UI will display automatically with:
- Dropdown for moment type selection (M0, M1, M8, M9)
- Sliders for channel range and clipping threshold
- Checkbox for mask application
- Color scale selector
- Auto-apply toggle with debouncing
- Apply, Save FITS, and Reset View buttons

### Programmatic Usage

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
    clip_sigma=3.0,
    use_mask=True
)

print(f"Computed in {compute_time*1000:.1f} ms")

# Save to FITS
output_path = explorer.save()
print(f"Saved to {output_path}")
```

## API Reference

### `MomentMapExplorer`

Core class for moment map computation.

#### Methods

- **`load_cube(cube_path, mask_path=None)`**: Load FITS cube and optional mask
  - Returns: Dictionary with cube info (shape, velocity range, RMS, etc.)

- **`generate(moment, first, last, clip_sigma, use_mask)`**: Compute a moment map
  - `moment`: 'M0', 'M1', 'M8', or 'M9'
  - `first`, `last`: Channel range (inclusive)
  - `clip_sigma`: Clipping threshold in units of RMS
  - `use_mask`: Boolean to apply user mask
  - Returns: (moment_map, compute_time)

- **`enable_prefix_sums(flag=True)`**: Enable/disable prefix-sum optimization for M0/M1
  - Speeds up M0/M1 by ~2-5x
  - Uses additional memory for cumulative sums

- **`save(path=None)`**: Save current moment map to FITS
  - If `path` is None, auto-generates filename based on cube path
  - Returns: Path to saved file

- **`get_wcs_extent()`**: Get WCS extent for plotting
  - Returns: (xmin, xmax, ymin, ymax) in arcsec offsets, or None

### `create_interactive_explorer`

Convenience function to create and display the full interactive UI.

```python
explorer, ui = create_interactive_explorer(
    cube_path,
    mask_path=None,
    enable_prefix_sums=True
)
```

Returns:
- `explorer`: MomentMapExplorer instance
- `ui`: MomentMapUI instance

## Performance

### Prefix-Sum Optimization

For M0 and M1 moment maps, the package supports an optional prefix-sum optimization:

```python
S0 = np.cumsum(data * mask, axis=0)
S1 = np.cumsum(velax[:,None,None] * data * mask, axis=0)
M0 = S0[j] - S0[i-1]
M1 = (S1[j]-S1[i-1]) / (M0 + 1e-9)
```

This allows computing moment maps over arbitrary channel ranges in O(1) time after O(N) preprocessing.

**Trade-offs:**
- Speedup: 2-5x for typical cubes
- Memory: +2x cube size for cached cumulative sums
- Best for: Interactive exploration with frequent channel range changes

### Debouncing

The UI uses a 200ms debounce timer when "Auto-apply" is enabled. This prevents excessive recomputation during slider dragging while maintaining responsiveness.

## Examples

See [`examples/interactive_moment_maker.ipynb`](examples/interactive_moment_maker.ipynb) for a complete Jupyter notebook demo.

### Batch Processing

```python
from moment_explorer import MomentMapExplorer

cubes = ['cube1.fits', 'cube2.fits', 'cube3.fits']
masks = ['mask1.fits', 'mask2.fits', 'mask3.fits']

for cube, mask in zip(cubes, masks):
    explorer = MomentMapExplorer()
    explorer.load_cube(cube, mask)

    # Generate all moment types
    for moment in ['M0', 'M1', 'M8', 'M9']:
        explorer.generate(moment, 30, 70, 3.0, True)
        explorer.save()
```

## Plotly Features

### Persistent View State

The Plotly figure uses `uirevision="moment_explorer_v1"` to preserve zoom/pan state across updates.

### In-Place Updates

Updates are performed in-place using `fig.batch_update()` and direct assignment:

```python
with fig.batch_update():
    fig.data[0].z = new_map
    fig.layout.coloraxis.cmin = vmin
    fig.layout.coloraxis.cmax = vmax
```

This avoids recreating the entire figure and ensures smooth performance.

### Color Scales

Available color scales:
- **Viridis** (default for M0, M8)
- **Cividis**
- **Magma**
- **Plasma**
- **RdBu_r** (default for M1, diverging)
- **Jet**

## Development

### Running Tests

```bash
pytest
```

### Building Documentation

```bash
# Coming soon
```

## Troubleshooting

**Issue**: Slow updates even with prefix sums enabled

**Solution**: Ensure you're using `Heatmapgl` instead of `Heatmap`. The UI automatically selects `Heatmapgl` for WebGL-accelerated rendering.

---

**Issue**: Color scale doesn't update automatically

**Solution**: The color scale dropdown updates the figure immediately. For moment-dependent scales (e.g., RdBu_r for M1), change the moment type dropdown.

---

**Issue**: "No cube loaded" error

**Solution**: Ensure `load_cube()` is called before `generate()` or creating the UI.

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
