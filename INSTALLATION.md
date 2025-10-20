# Installation Guide

## Prerequisites

Ensure you have Python 3.8 or later installed.

## Step 1: Install Dependencies

The package requires the following dependencies:

```bash
pip install numpy astropy bettermoments plotly ipywidgets
```

For Jupyter notebook support:

```bash
pip install jupyter jupyterlab
```

## Step 2: Install moment-explorer

### Development Installation (Recommended)

From the `moment-explorer` directory:

```bash
pip install -e .
```

This installs the package in "editable" mode, allowing you to modify the source code without reinstalling.

### Standard Installation

```bash
pip install .
```

## Step 3: Verify Installation

Run the test script:

```bash
python test_package.py
```

Expected output:
```
============================================================
Moment Explorer Package Test Suite
============================================================
Testing imports...
✓ All imports successful

Testing MomentMapExplorer initialization...
✓ MomentMapExplorer initialized successfully

Testing API methods...
✓ All 5 API methods present

Testing with dummy data...
✓ Dummy data tests passed

============================================================
Results: 4/4 tests passed
============================================================

✓ All tests passed! Package is ready to use.
```

## Step 4: Enable Jupyter Widgets

For JupyterLab:

```bash
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

For classic Jupyter Notebook:

```bash
jupyter nbextension enable --py widgetsnbextension
```

## Step 5: Launch the Example Notebook

```bash
cd examples
jupyter lab interactive_moment_maker.ipynb
```

Or with classic notebook:

```bash
cd examples
jupyter notebook interactive_moment_maker.ipynb
```

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'bettermoments'`

**Solution**: Install bettermoments:

```bash
pip install bettermoments
```

If not available via pip, install from source:

```bash
git clone https://github.com/richteague/bettermoments.git
cd bettermoments
pip install -e .
```

### Issue: Widgets not displaying in Jupyter

**Solution**: Ensure ipywidgets extension is enabled:

```bash
# For JupyterLab 3.x
pip install jupyterlab_widgets

# For older versions
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

Then restart JupyterLab.

### Issue: Plotly figures not rendering

**Solution**: Install plotly renderer support:

```bash
pip install plotly>=5.0 kaleido
```

For JupyterLab:

```bash
pip install "jupyterlab>=3" "ipywidgets>=7.6"
```

## Quick Start After Installation

```python
from moment_explorer import create_interactive_explorer

# Create interactive UI
explorer, ui = create_interactive_explorer(
    cube_path='path/to/cube.fits',
    mask_path='path/to/mask.fits'
)
```

See [README.md](README.md) for more usage examples.
