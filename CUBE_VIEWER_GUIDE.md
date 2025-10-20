# Cube Viewer Guide

The `CubeMaskViewer` provides an interactive interface for exploring individual channels of your FITS cube with mask contours overlaid.

## Features

- **Channel slider** - Navigate through all channels of your cube
- **Intensity scaling** - Manual vmin/vmax controls or auto-scaling
- **Mask overlay** - Display mask as red contours
- **Colormap selection** - Choose from 7 different colormaps
- **Interactive zoom/pan** - Explore spatial details with Plotly
- **WCS support** - Automatic coordinate display

## Quick Start

### Option 1: Direct Usage

```python
from moment_explorer import create_cube_viewer

# Create the viewer
viewer = create_cube_viewer(
    cube_path='/path/to/cube.fits',
    mask_path='/path/to/mask.fits'  # optional
)
```

### Option 2: Programmatic Control

```python
from moment_explorer import CubeMaskViewer

# Create viewer instance
viewer = CubeMaskViewer()
viewer.load_cube('cube.fits', 'mask.fits')

# Create and display UI
ui = viewer.create_viewer()
from IPython.display import display
display(ui)
```

### Option 3: Interactive Launcher UI

```python
from moment_explorer import create_launcher_ui
from IPython.display import display

# Display file browser launcher
display(create_launcher_ui())
```

## Controls

### Channel Slider
- **Range**: 0 to N-1 (where N = number of channels)
- **Behavior**: Updates display when released (not continuous)
- **Shows**: Current velocity in plot title

### Intensity Scaling

**vmin/vmax text boxes:**
- Manually set the display range
- Use scientific notation (e.g., `1.5e-3`)

**Auto-scale checkbox:**
- When enabled: Automatically sets vmin/vmax to 1st and 99th percentiles
- When disabled: Uses manual vmin/vmax values
- Updates on channel change if enabled

### Colorscale Dropdown
Choose from:
- **Viridis** (default) - Perceptually uniform, good for most data
- **Cividis** - Colorblind-friendly alternative to Viridis
- **Magma** - High contrast
- **Plasma** - Bright colors
- **Greys** - Black and white
- **RdBu_r** - Diverging (red-blue reversed)
- **Jet** - Rainbow (not recommended for scientific use, but included)

### Mask Overlay

**Show mask contour checkbox:**
- When enabled: Displays mask as red contour lines
- Contour level: 0.5 (shows mask boundary)
- Automatically disabled if no mask loaded

### Buttons

**Apply**
- Manually refresh the display with current settings
- Useful when auto-scale is disabled

**Reset View**
- Restore default zoom/pan state
- Doesn't affect channel or intensity settings

## Status Bar

Shows:
- Cube shape (nchan × ny × nx)
- Current channel number
- Current velocity (km/s)
- Current vmin/vmax range

## Example Workflows

### Workflow 1: Quick Channel Exploration

```python
from moment_explorer import create_cube_viewer

# Load and view
viewer = create_cube_viewer('cube.fits', 'mask.fits')

# Now use the UI:
# 1. Enable "Auto-scale intensity"
# 2. Move the channel slider to explore
# 3. Channels auto-scale as you move
```

### Workflow 2: Finding Optimal vmin/vmax

```python
from moment_explorer import create_cube_viewer

viewer = create_cube_viewer('cube.fits')

# In UI:
# 1. Go to a representative channel
# 2. Enable "Auto-scale"
# 3. Note the vmin/vmax values shown
# 4. Disable "Auto-scale"
# 5. Fine-tune vmin/vmax manually
# 6. Navigate through channels with fixed scaling
```

### Workflow 3: Mask Verification

```python
from moment_explorer import create_cube_viewer

viewer = create_cube_viewer('cube.fits', 'mask.fits')

# In UI:
# 1. Enable "Show mask contour"
# 2. Slide through channels to check mask coverage
# 3. Look for channels where mask doesn't match emission
# 4. Use zoom to inspect spatial details
```

### Workflow 4: Multi-Cube Comparison

```python
from moment_explorer import create_cube_viewer

# Create two viewers in separate cells
# Cell 1:
viewer1 = create_cube_viewer('cube1.fits', 'mask1.fits')

# Cell 2:
viewer2 = create_cube_viewer('cube2.fits', 'mask2.fits')

# Now you can compare side-by-side
```

## Tips & Tricks

### Tip 1: Keyboard Navigation
While the slider is focused, use arrow keys to move one channel at a time.

### Tip 2: Finding Emission Channels
1. Enable auto-scale
2. Move slider through channels
3. Look for when the plot suddenly shows structure
4. Note those channel numbers for your moment map range

### Tip 3: Zooming to a Specific Region
1. Click and drag to draw a box
2. The view zooms to that box
3. Double-click to reset zoom
4. Click "Reset View" button to restore defaults

### Tip 4: Checking Noise Levels
1. Go to a line-free channel (edge of cube)
2. Enable auto-scale
3. Note the vmax value - this is roughly your noise level
4. Compare to channels with emission

### Tip 5: Exporting Channel Images
The Plotly figure has a built-in camera icon (top-right):
- Click to download as PNG
- Useful for presentations or papers

## Technical Details

### Mask Contour
- Displayed at level = 0.5 (mask boundary)
- Color: Red (#FF0000)
- Line width: 2 pixels
- Updates automatically when changing channels

### Performance
- Uses Plotly WebGL acceleration when available
- Falls back to standard Plotly if WebGL unavailable
- Updates are fast even for large cubes (500×500 spatial)
- Only loads one channel at a time (memory efficient)

### WCS Coordinates
If FITS header contains WCS information:
- Axes show ΔRA and ΔDEC in arcseconds
- Origin is at reference pixel (CRPIX)
- Aspect ratio is preserved (1:1 spatial)

## Comparison with Moment Map Explorer

| Feature | Cube Viewer | Moment Map Explorer |
|---------|-------------|---------------------|
| **View Type** | Single channels | Collapsed moment maps |
| **Channel Control** | Slider (one channel) | Range selector (first/last) |
| **Mask Display** | Contour overlay | Applied during collapse |
| **Use Case** | Inspect data quality | Generate science products |
| **Output** | Visual inspection | FITS moment maps |
| **Velocity Info** | Per channel | Weighted average (M1) |

**Use Cube Viewer when:**
- Checking data quality
- Finding line channels
- Verifying mask coverage
- Looking for artifacts
- Exploring spatial structure at specific velocities

**Use Moment Map Explorer when:**
- Creating publication figures
- Measuring integrated intensity
- Mapping velocity structure
- Generating science products
- Batch processing multiple cubes

## Troubleshooting

**Issue**: Contour doesn't appear

**Solution**:
- Check that mask file was loaded
- Enable "Show mask contour" checkbox
- Try a different channel (mask might be 0 in current channel)

---

**Issue**: Can't see any emission

**Solution**:
- Enable "Auto-scale intensity"
- Try different channels
- Check that vmin/vmax aren't too restrictive

---

**Issue**: Slow updates

**Solution**:
- Disable "Auto-scale" if you don't need it
- Close other notebook cells/viewers
- Consider using a smaller spatial region

---

**Issue**: Coordinates show pixels instead of arcsec

**Solution**: Your FITS file doesn't have complete WCS information. This is normal for some data, viewer still works fine with pixel coordinates.

## Related Functions

- `create_interactive_explorer()` - For moment map generation
- `create_multi_cube_explorer()` - For switching between multiple cubes
- `create_launcher_ui()` - For file browser interface

## Example: Complete Analysis Workflow

```python
from moment_explorer import create_cube_viewer, create_interactive_explorer

# Step 1: Explore channels to find emission range
viewer = create_cube_viewer('cube.fits', 'mask.fits')
# Use UI to find: emission from channel 30-70

# Step 2: Generate moment map with found range
explorer, ui = create_interactive_explorer('cube.fits', 'mask.fits')
# Set first_channel=30, last_channel=70
# Generate M0, M1, M8, M9 maps
# Save to FITS

# Step 3: Go back to cube viewer to verify specific features
# Use viewer to check individual channels for artifacts
```

This workflow combines both tools for complete analysis!
