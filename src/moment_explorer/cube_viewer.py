"""
Interactive cube viewer with mask contour overlay.
"""
import numpy as np
import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display
import bettermoments as bm
from astropy.io import fits


class CubeMaskViewer:
    """
    Interactive viewer for exploring spectral cube channels with mask overlay.

    Displays individual channels of a FITS cube with the mask shown as contours.
    Provides controls for channel selection, intensity scaling, and colormap.
    """

    def __init__(self):
        """Initialize an empty CubeMaskViewer."""
        self.data = None
        self.velax = None
        self.mask = None
        self.header = None
        self.cube_path = None
        self.mask_path = None
        self.fig = None
        self.widgets = {}

    def load_cube(self, cube_path, mask_path=None):
        """
        Load a FITS spectral cube and optional mask.

        Args:
            cube_path (str): Path to the FITS cube.
            mask_path (str): Path to the mask FITS file (optional).

        Returns:
            dict: Summary information about the loaded cube.
        """
        self.cube_path = cube_path
        self.mask_path = mask_path

        # Load data
        self.data, self.velax = bm.load_cube(cube_path)

        # Load mask
        if mask_path:
            self.mask = bm.get_user_mask(data=self.data, user_mask_path=mask_path)
        else:
            self.mask = None

        # Cache header for WCS
        self.header = fits.getheader(cube_path)

        return {
            'shape': self.data.shape,
            'vel_range': (float(self.velax[0]), float(self.velax[-1])),
            'n_channels': len(self.velax)
        }

    def get_wcs_extent(self):
        """Get the WCS extent for plotting."""
        if self.header is None:
            return None

        try:
            ra_offset = 3600. * self.header['CDELT1'] * (
                np.arange(self.header['NAXIS1']) - (self.header['CRPIX1'] - 1)
            )
            dec_offset = 3600. * self.header['CDELT2'] * (
                np.arange(self.header['NAXIS2']) - (self.header['CRPIX2'] - 1)
            )
            return (np.max(ra_offset), np.min(ra_offset),
                    np.min(dec_offset), np.max(dec_offset))
        except KeyError:
            return None

    def create_viewer(self):
        """
        Create the interactive viewer UI.

        Returns:
            VBox widget containing the viewer interface.
        """
        if self.data is None:
            raise RuntimeError("No cube loaded. Call load_cube() first.")

        n_channels = len(self.velax)
        initial_channel = n_channels // 2

        # Get initial channel data
        channel_data = self.data[initial_channel, :, :]

        # Get extent
        extent = self.get_wcs_extent()
        if extent:
            x_min, x_max, y_min, y_max = extent
            x = np.linspace(x_max, x_min, channel_data.shape[1])
            y = np.linspace(y_min, y_max, channel_data.shape[0])
        else:
            x = np.arange(channel_data.shape[1])
            y = np.arange(channel_data.shape[0])

        # Compute initial vmin/vmax
        vmin_init, vmax_init = np.nanpercentile(channel_data, [1, 99])

        # Create figure with heatmap
        try:
            heatmap_trace = go.Heatmapgl(
                z=channel_data,
                x=x,
                y=y,
                coloraxis="coloraxis",
                hovertemplate='x: %{x:.2f}<br>y: %{y:.2f}<br>value: %{z:.3e}<extra></extra>'
            )
        except (AttributeError, ImportError):
            heatmap_trace = go.Heatmap(
                z=channel_data,
                x=x,
                y=y,
                coloraxis="coloraxis",
                hovertemplate='x: %{x:.2f}<br>y: %{y:.2f}<br>value: %{z:.3e}<extra></extra>'
            )

        self.fig = go.FigureWidget(
            data=[heatmap_trace],
            layout=dict(
                coloraxis=dict(
                    colorscale="Viridis",
                    cmin=vmin_init,
                    cmax=vmax_init,
                    colorbar=dict(
                        title=dict(text="Intensity [Jy/beam]")
                    )
                ),
                uirevision="cube_viewer_v1",
                xaxis=dict(
                    title="ΔRA [arcsec]" if extent else "X [pixels]",
                    scaleanchor="y",
                    scaleratio=1
                ),
                yaxis=dict(
                    title="ΔDEC [arcsec]" if extent else "Y [pixels]",
                    autorange=True
                ),
                width=800,
                height=700,
                title=f"Channel {initial_channel} (v = {self.velax[initial_channel]:.2f} km/s)"
            )
        )

        # Add mask contour if available
        if self.mask is not None:
            mask_channel = self.mask[initial_channel, :, :]
            if np.any(mask_channel > 0):
                contour_trace = go.Contour(
                    z=mask_channel,
                    x=x,
                    y=y,
                    contours=dict(
                        start=0.5,
                        end=0.5,
                        size=1,
                        coloring='lines'
                    ),
                    line=dict(color='red', width=2),
                    showscale=False,
                    hoverinfo='skip',
                    name='Mask'
                )
                self.fig.add_trace(contour_trace)

        # Create widgets
        self._create_widgets(n_channels, initial_channel, vmin_init, vmax_init)

        # Layout
        controls_left = widgets.VBox([
            self.widgets['channel'],
            self.widgets['vmin'],
            self.widgets['vmax'],
        ])

        controls_right = widgets.VBox([
            self.widgets['colorscale'],
            self.widgets['show_mask'],
            self.widgets['auto_scale'],
        ])

        controls = widgets.HBox([controls_left, controls_right])

        buttons = widgets.HBox([
            self.widgets['apply_button'],
            self.widgets['reset_button']
        ])

        status = self.widgets['status_label']

        viewer_ui = widgets.VBox([
            controls,
            buttons,
            status,
            self.fig
        ])

        return viewer_ui

    def _create_widgets(self, n_channels, initial_channel, vmin_init, vmax_init):
        """Create UI widgets."""
        # Channel slider
        self.widgets['channel'] = widgets.IntSlider(
            value=initial_channel,
            min=0,
            max=n_channels - 1,
            step=1,
            description='Channel:',
            continuous_update=False,
            style={'description_width': '100px'},
            layout=widgets.Layout(width='400px')
        )

        # vmin slider
        self.widgets['vmin'] = widgets.FloatText(
            value=vmin_init,
            description='vmin:',
            style={'description_width': '100px'},
            layout=widgets.Layout(width='200px')
        )

        # vmax slider
        self.widgets['vmax'] = widgets.FloatText(
            value=vmax_init,
            description='vmax:',
            style={'description_width': '100px'},
            layout=widgets.Layout(width='200px')
        )

        # Colorscale dropdown
        self.widgets['colorscale'] = widgets.Dropdown(
            options=['Viridis', 'Cividis', 'Magma', 'Plasma', 'Greys', 'RdBu_r', 'Jet'],
            value='Viridis',
            description='Colorscale:',
            style={'description_width': '100px'}
        )

        # Show mask checkbox
        self.widgets['show_mask'] = widgets.Checkbox(
            value=True if self.mask is not None else False,
            description='Show mask contour',
            disabled=self.mask is None,
            indent=False
        )

        # Auto-scale checkbox
        self.widgets['auto_scale'] = widgets.Checkbox(
            value=True,
            description='Auto-scale intensity',
            indent=False
        )

        # Buttons
        self.widgets['apply_button'] = widgets.Button(
            description='Apply',
            button_style='primary',
            icon='refresh'
        )

        self.widgets['reset_button'] = widgets.Button(
            description='Reset View',
            button_style='warning',
            icon='home'
        )

        # Status label
        self.widgets['status_label'] = widgets.HTML(
            value=f"<b>Cube shape:</b> {self.data.shape} | <b>Channel:</b> {initial_channel}"
        )

        # Connect callbacks
        self.widgets['channel'].observe(self._on_channel_change, names='value')
        self.widgets['colorscale'].observe(self._on_colorscale_change, names='value')
        self.widgets['show_mask'].observe(self._on_show_mask_change, names='value')
        self.widgets['apply_button'].on_click(lambda b: self._update_display())
        self.widgets['reset_button'].on_click(lambda b: self._reset_view())

    def _on_channel_change(self, change):
        """Handle channel slider change."""
        self._update_display()

    def _on_colorscale_change(self, change):
        """Handle colorscale dropdown change."""
        with self.fig.batch_update():
            self.fig.layout.coloraxis.colorscale = change['new']

    def _on_show_mask_change(self, change):
        """Handle show mask checkbox change."""
        self._update_display()

    def _update_display(self):
        """Update the display with current channel and settings."""
        channel = self.widgets['channel'].value

        # Get channel data
        channel_data = self.data[channel, :, :]

        # Auto-scale if enabled
        if self.widgets['auto_scale'].value:
            vmin, vmax = np.nanpercentile(channel_data, [1, 99])
            self.widgets['vmin'].value = vmin
            self.widgets['vmax'].value = vmax
        else:
            vmin = self.widgets['vmin'].value
            vmax = self.widgets['vmax'].value

        # Update heatmap
        with self.fig.batch_update():
            self.fig.data[0].z = channel_data
            self.fig.layout.coloraxis.cmin = vmin
            self.fig.layout.coloraxis.cmax = vmax
            self.fig.layout.title = f"Channel {channel} (v = {self.velax[channel]:.2f} km/s)"

            # Update or remove mask contour
            if self.mask is not None and self.widgets['show_mask'].value:
                mask_channel = self.mask[channel, :, :]

                # Update existing contour or add new one
                if len(self.fig.data) > 1:
                    # Update existing contour
                    self.fig.data[1].z = mask_channel
                else:
                    # Add new contour
                    extent = self.get_wcs_extent()
                    if extent:
                        x_min, x_max, y_min, y_max = extent
                        x = np.linspace(x_max, x_min, channel_data.shape[1])
                        y = np.linspace(y_min, y_max, channel_data.shape[0])
                    else:
                        x = np.arange(channel_data.shape[1])
                        y = np.arange(channel_data.shape[0])

                    contour_trace = go.Contour(
                        z=mask_channel,
                        x=x,
                        y=y,
                        contours=dict(
                            start=0.5,
                            end=0.5,
                            size=1,
                            coloring='lines'
                        ),
                        line=dict(color='red', width=2),
                        showscale=False,
                        hoverinfo='skip',
                        name='Mask'
                    )
                    self.fig.add_trace(contour_trace)
            else:
                # Remove contour if exists
                if len(self.fig.data) > 1:
                    self.fig.data = [self.fig.data[0]]

        # Update status
        self.widgets['status_label'].value = (
            f"<b>Cube shape:</b> {self.data.shape} | "
            f"<b>Channel:</b> {channel} | "
            f"<b>Velocity:</b> {self.velax[channel]:.2f} km/s | "
            f"<b>Range:</b> [{vmin:.3e}, {vmax:.3e}]"
        )

    def _reset_view(self):
        """Reset the plot view to default."""
        extent = self.get_wcs_extent()
        if extent:
            x_min, x_max, y_min, y_max = extent
            with self.fig.batch_update():
                self.fig.layout.xaxis.range = [x_max, x_min]
                self.fig.layout.yaxis.range = [y_min, y_max]
        else:
            with self.fig.batch_update():
                self.fig.layout.xaxis.autorange = True
                self.fig.layout.yaxis.autorange = True


def create_cube_viewer(cube_path, mask_path=None):
    """
    Create and display an interactive cube viewer.

    Args:
        cube_path (str): Path to the FITS cube.
        mask_path (str): Path to the mask FITS file (optional).

    Returns:
        CubeMaskViewer: The viewer instance.

    Example:
        >>> viewer = create_cube_viewer('cube.fits', 'mask.fits')
    """
    viewer = CubeMaskViewer()
    info = viewer.load_cube(cube_path, mask_path)

    print(f"Cube loaded: {info['shape']}")
    print(f"Velocity range: {info['vel_range'][0]:.2f} to {info['vel_range'][1]:.2f} km/s")
    print(f"Number of channels: {info['n_channels']}")

    ui = viewer.create_viewer()
    display(ui)

    return viewer
