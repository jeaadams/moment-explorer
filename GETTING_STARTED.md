# Getting Started with moment-explorer

A 5-minute guide to get up and running with the moment-explorer package.

## Prerequisites

- Python 3.8 or later
- Jupyter Notebook or JupyterLab
- A FITS spectral cube file
- (Optional) A mask FITS file

## Step 1: Install Dependencies 

```bash
# Install core dependencies
pip install numpy astropy bettermoments plotly ipywidgets

# Install Jupyter (if not already installed)
pip install jupyter jupyterlab

# Enable widget extension for JupyterLab
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

## Step 2: Install the Package 

```bash
# Navigate to the package directory
cd /Users/jea/AATau/moment-explorer

# Install in development mode
pip install -e .
```

## Step 3: Verify Installation

```bash
# Run the test script
python test_package.py
```

Expected output:
```
============================================================
Moment Explorer Package Test Suite
============================================================
Testing imports...
✓ All imports successful
...
Results: 4/4 tests passed
✓ All tests passed! Package is ready to use.
```

## Step 4: Launch Jupyter 

```bash
cd examples
jupyter lab interactive_moment_maker.ipynb
```

Or with classic Jupyter:
```bash
jupyter notebook interactive_moment_maker.ipynb
```

## Step 5: Run Your First Interactive Explorer 

In a Jupyter cell:

```python
from moment_explorer import create_interactive_explorer

# Replace with your FITS file paths
cube_path = '/path/to/your/cube.fits'
mask_path = '/path/to/your/mask.fits'  # Optional

# Create the interactive UI (one line!)
explorer, ui = create_interactive_explorer(
    cube_path=cube_path,
    mask_path=mask_path,
    enable_prefix_sums=True
)
```

That's it! You should see an interactive Plotly plot with controls.

## Quick Tutorial: Exploring Your Data

### 1. Basic Controls

- **Moment dropdown**: Select M0, M1, M8, or M9
- **Channel sliders**: Adjust first and last channel
- **Clip σ slider**: Set the clipping threshold
- **Use mask checkbox**: Toggle mask on/off
- **Colorscale dropdown**: Change the color map

### 2. Update Modes

#### Auto-Apply (Recommended for Exploration)

1. Check the "Auto-apply (debounced)" checkbox
2. Move sliders smoothly - updates happen after ~200ms
3. Great for quick exploration

#### Manual Apply (Recommended for Precision)

1. Uncheck "Auto-apply"
2. Adjust all parameters to desired values
3. Click "Apply" button to compute
4. Best for final publication-quality maps

### 3. Interacting with the Plot

- **Click + drag**: Pan the view
- **Scroll**: Zoom in/out
- **Double-click**: Reset view
- **Hover**: See pixel values

Your zoom and pan are **preserved** when you update parameters!

### 4. Saving Your Work

1. Adjust parameters until satisfied
2. Click "Save FITS" button
3. See confirmation message with output path
4. File saved automatically to cube directory

## Example Workflows

### Workflow 1: Quick Exploration

```python
# 1. Create explorer
from moment_explorer import create_interactive_explorer

explorer, ui = create_interactive_explorer('cube.fits', 'mask.fits')

# 2. Enable auto-apply and explore
#    - Check "Auto-apply" checkbox in UI
#    - Move sliders to explore different channel ranges
#    - Zoom into interesting regions
#    - Switch moment types to see different views

# 3. Save when satisfied
#    - Click "Save FITS" button
```

### Workflow 2: Precise Publication Map

```python
# 1. Create explorer
from moment_explorer import create_interactive_explorer

explorer, ui = create_interactive_explorer('cube.fits', 'mask.fits')

# 2. Disable auto-apply for precise control
#    - Uncheck "Auto-apply" checkbox
#    - Set moment type: M0
#    - Set first channel: 35
#    - Set last channel: 65
#    - Set clip σ: 3.5
#    - Click "Apply"

# 3. Fine-tune visualization
#    - Zoom to region of interest
#    - Change colorscale to "Viridis"
#    - Verify data range in status label

# 4. Save final map
#    - Click "Save FITS"
```

### Workflow 3: Programmatic Batch Processing

```python
from moment_explorer import MomentMapExplorer

# Define your cubes
cubes = [
    {'cube': 'cube1.fits', 'mask': 'mask1.fits', 'name': 'Source1'},
    {'cube': 'cube2.fits', 'mask': 'mask2.fits', 'name': 'Source2'},
]

# Process all cubes
for cube_info in cubes:
    print(f"Processing {cube_info['name']}...")

    # Create explorer
    explorer = MomentMapExplorer()
    explorer.load_cube(cube_info['cube'], cube_info['mask'])
    explorer.enable_prefix_sums(True)

    # Generate all moment types
    for moment in ['M0', 'M1', 'M8', 'M9']:
        print(f"  Computing {moment}...")
        explorer.generate(
            moment=moment,
            first=30,
            last=70,
            clip_sigma=3.0,
            use_mask=True
        )
        path = explorer.save()
        print(f"  Saved to {path}")
```

### Workflow 4: Custom Matplotlib Export

```python
import matplotlib.pyplot as plt
from moment_explorer import MomentMapExplorer

# Load and compute
explorer = MomentMapExplorer()
explorer.load_cube('cube.fits', 'mask.fits')
moment_map, compute_time = explorer.generate('M0', 30, 70, 3.0, True)

print(f"Computed in {compute_time*1000:.1f} ms")

# Get WCS extent for proper coordinates
extent = explorer.get_wcs_extent()

# Create publication-quality plot with matplotlib
fig, ax = plt.subplots(figsize=(8, 7), dpi=150)
im = ax.imshow(moment_map, origin='lower', cmap='viridis', extent=extent)

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Integrated Intensity [Jy/beam km/s]', rotation=270, labelpad=20)

# Labels and title
ax.set_xlabel('ΔRA [arcsec]')
ax.set_ylabel('ΔDEC [arcsec]')
ax.set_title('Moment 0 Map')

# Save as PNG
plt.savefig('moment0_publication.png', dpi=300, bbox_inches='tight')
plt.show()
```

## Tips for Best Performance

### 1. Enable Prefix-Sum Optimization

For interactive exploration where you'll change channel ranges frequently:

```python
explorer.enable_prefix_sums(True)
```

This pre-computes cumulative sums, making M0/M1 computation 2-5x faster.

**Trade-off**: Uses 2x cube size in memory.

### 2. Use Heatmapgl (Automatic)

The UI automatically uses `go.Heatmapgl` for WebGL acceleration. No action needed.

### 3. Debounce Slider Updates

Already built-in when "Auto-apply" is enabled. The 200ms debounce prevents excessive recomputation during slider dragging.

### 4. Disable Auto-Apply for Large Cubes

If computation is slow (>1 second), disable "Auto-apply" and use the "Apply" button for manual control.

## Common Issues & Solutions

### Issue 1: Widgets Not Displaying

**Symptoms**: See widget code instead of interactive controls

**Solution**:
```bash
# For JupyterLab
jupyter labextension install @jupyter-widgets/jupyterlab-manager

# For classic Jupyter
jupyter nbextension enable --py widgetsnbextension

# Restart Jupyter
```

### Issue 2: Plotly Figure Not Rendering

**Symptoms**: Blank space where plot should be

**Solution**:
```bash
pip install plotly>=5.0 kaleido
pip install "jupyterlab>=3" "ipywidgets>=7.6"

# Restart Jupyter
```

### Issue 3: ModuleNotFoundError: bettermoments

**Symptoms**: Import error when loading package

**Solution**:
```bash
pip install bettermoments

# If not on PyPI, install from source:
git clone https://github.com/richteague/bettermoments.git
cd bettermoments
pip install -e .
```

### Issue 4: Slow Updates Even With Optimization

**Symptoms**: Updates take >500ms

**Check**:
1. Is prefix-sum enabled? `explorer.enable_prefix_sums(True)`
2. Is auto-apply disabled for large cubes?
3. Is WebGL working? Check browser console for errors

**Solution**: Disable auto-apply, use manual "Apply" button

### Issue 5: Out of Memory Error

**Symptoms**: Kernel crashes when loading large cube

**Solution**: Disable prefix-sum optimization
```python
explorer.enable_prefix_sums(False)
```

This reduces memory usage by 2x.

## Next Steps

Now that you're up and running:

1. **Explore your data** with the interactive UI
2. **Read the full documentation** in [README.md](README.md)
3. **Check the quick reference** in [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
4. **See the comparison** with the old notebook in [COMPARISON.md](COMPARISON.md)
5. **Migrate existing workflows** using [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

## Getting Help

- **Documentation**: See [README.md](README.md)
- **API Reference**: See docstrings in source code
- **Examples**: Check [examples/interactive_moment_maker.ipynb](examples/interactive_moment_maker.ipynb)
- **Issues**: Report bugs or request features on GitHub

## Useful Links

- [bettermoments documentation](https://github.com/richteague/bettermoments)
- [Plotly documentation](https://plotly.com/python/)
- [ipywidgets documentation](https://ipywidgets.readthedocs.io/)

---

**Estimated time to first interactive plot**: ~5 minutes

Enjoy exploring your moment maps!
