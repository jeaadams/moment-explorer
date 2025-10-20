"""
Plotly + ipywidgets UI for interactive moment map exploration.
"""
import time
import numpy as np
import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display
from threading import Timer


class MomentMapUI:
    """
    Interactive Plotly-based UI for moment map exploration.

    Attributes:
        explorer: MomentMapExplorer instance.
        fig: Plotly FigureWidget.
        widgets: Dictionary of UI widgets.
        debounce_timer: Timer for debounced updates.
    """

    def __init__(self, explorer):
        """
        Initialize the UI with a MomentMapExplorer instance.

        Args:
            explorer: MomentMapExplorer instance with a loaded cube.
        """
        self.explorer = explorer
        self.fig = None
        self.widgets = {}
        self.debounce_timer = None
        self._status_label = None
        self._last_update = 0
        self._debounce_delay = 0.2  # 200ms

        # Initialize the UI
        self._create_figure()
        self._create_widgets()

    def _create_figure(self):
        """Create the initial Plotly FigureWidget."""
        # Generate an initial moment map (M0 with defaults)
        if self.explorer.data is None:
            raise RuntimeError("Explorer has no loaded cube.")

        # Default parameters
        n_channels = len(self.explorer.velax)
        first = max(0, n_channels // 4)
        last = min(n_channels - 1, 3 * n_channels // 4)

        initial_map, _ = self.explorer.generate(
            moment='M0',
            first=first,
            last=last,
            clip_sigma=3.0,
            use_mask=True
        )

        # Get extent for WCS
        extent = self.explorer.get_wcs_extent()

        # Compute initial color limits
        vmin, vmax = np.nanpercentile(initial_map, [50, 99.99])

        # Create the figure
        if extent:
            x_min, x_max, y_min, y_max = extent
            x = np.linspace(x_max, x_min, initial_map.shape[1])
            y = np.linspace(y_min, y_max, initial_map.shape[0])
        else:
            x = np.arange(initial_map.shape[1])
            y = np.arange(initial_map.shape[0])

        # Try Heatmapgl first (WebGL accelerated), fallback to Heatmap
        try:
            heatmap_trace = go.Heatmapgl(
                z=initial_map,
                x=x,
                y=y,
                coloraxis="coloraxis",
                hovertemplate='x: %{x:.2f}<br>y: %{y:.2f}<br>value: %{z:.3e}<extra></extra>'
            )
            self._using_webgl = True
        except (AttributeError, ImportError):
            # Heatmapgl not available, use standard Heatmap
            heatmap_trace = go.Heatmap(
                z=initial_map,
                x=x,
                y=y,
                coloraxis="coloraxis",
                hovertemplate='x: %{x:.2f}<br>y: %{y:.2f}<br>value: %{z:.3e}<extra></extra>'
            )
            self._using_webgl = False
            print("Note: Using standard Heatmap (Heatmapgl not available). Performance may be slower for large maps.")

        self.fig = go.FigureWidget(
            data=[heatmap_trace],
            layout=dict(
                coloraxis=dict(
                    colorscale="Viridis",
                    cmin=vmin,
                    cmax=vmax,
                    colorbar=dict(
                        title="Integrated Intensity",
                        titleside="right"
                    )
                ),
                uirevision="moment_explorer_v1",  # Persist zoom/pan
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
                title="Moment Map Explorer"
            )
        )

    def _create_widgets(self):
        """Create all UI widgets."""
        n_channels = len(self.explorer.velax)

        # Moment type dropdown
        self.widgets['moment'] = widgets.Dropdown(
            options=['M0', 'M1', 'M8', 'M9'],
            value='M0',
            description='Moment:',
            style={'description_width': '100px'}
        )

        # Channel sliders
        self.widgets['first_channel'] = widgets.IntSlider(
            value=max(0, n_channels // 4),
            min=0,
            max=n_channels - 1,
            step=1,
            description='First Ch:',
            continuous_update=False,
            style={'description_width': '100px'}
        )

        self.widgets['last_channel'] = widgets.IntSlider(
            value=min(n_channels - 1, 3 * n_channels // 4),
            min=0,
            max=n_channels - 1,
            step=1,
            description='Last Ch:',
            continuous_update=False,
            style={'description_width': '100px'}
        )

        # Clip sigma slider
        self.widgets['clip_sigma'] = widgets.FloatSlider(
            value=3.0,
            min=1.0,
            max=10.0,
            step=0.5,
            description='Clip σ:',
            continuous_update=False,
            style={'description_width': '100px'}
        )

        # Use mask checkbox
        self.widgets['use_mask'] = widgets.Checkbox(
            value=True,
            description='Use mask',
            indent=False
        )

        # Color scale dropdown
        self.widgets['colorscale'] = widgets.Dropdown(
            options=['Viridis', 'Cividis', 'Magma', 'Plasma', 'RdBu_r', 'Jet'],
            value='Viridis',
            description='Colorscale:',
            style={'description_width': '100px'}
        )

        # Auto-apply checkbox
        self.widgets['auto_apply'] = widgets.Checkbox(
            value=False,
            description='Auto-apply (debounced)',
            indent=False
        )

        # Buttons
        self.widgets['apply_button'] = widgets.Button(
            description='Apply',
            button_style='primary',
            icon='refresh'
        )

        self.widgets['save_button'] = widgets.Button(
            description='Save FITS',
            button_style='success',
            icon='save'
        )

        self.widgets['reset_button'] = widgets.Button(
            description='Reset View',
            button_style='warning',
            icon='home'
        )

        # Status label
        self._status_label = widgets.HTML(
            value=f"<b>Cube shape:</b> {self.explorer.data.shape} | <b>Last compute:</b> -- ms"
        )

        # Save output
        self._save_output = widgets.Output()

        # Connect callbacks
        self.widgets['apply_button'].on_click(lambda b: self._on_apply())
        self.widgets['save_button'].on_click(lambda b: self._on_save())
        self.widgets['reset_button'].on_click(lambda b: self._on_reset_view())

        # Connect auto-apply
        for key in ['moment', 'first_channel', 'last_channel', 'clip_sigma', 'use_mask']:
            self.widgets[key].observe(self._on_param_change, names='value')

        # Connect colorscale change
        self.widgets['colorscale'].observe(self._on_colorscale_change, names='value')

    def _on_param_change(self, change):
        """Handle parameter changes for auto-apply."""
        if self.widgets['auto_apply'].value:
            # Cancel existing timer
            if self.debounce_timer is not None:
                self.debounce_timer.cancel()

            # Start new debounce timer
            self.debounce_timer = Timer(self._debounce_delay, self._on_apply)
            self.debounce_timer.start()

    def _on_colorscale_change(self, change):
        """Handle colorscale dropdown changes."""
        with self.fig.batch_update():
            self.fig.layout.coloraxis.colorscale = change['new']

    def _on_apply(self):
        """Apply current parameters and update the plot."""
        # Get current parameters
        moment = self.widgets['moment'].value
        first = self.widgets['first_channel'].value
        last = self.widgets['last_channel'].value
        clip_sigma = self.widgets['clip_sigma'].value
        use_mask = self.widgets['use_mask'].value

        # Validate channel range
        if first > last:
            first, last = last, first
            self.widgets['first_channel'].value = first
            self.widgets['last_channel'].value = last

        # Generate moment map
        try:
            moment_map, compute_time = self.explorer.generate(
                moment=moment,
                first=first,
                last=last,
                clip_sigma=clip_sigma,
                use_mask=use_mask
            )

            # Update the plot
            self._update_plot(moment_map, moment)

            # Update status
            self._status_label.value = (
                f"<b>Cube shape:</b> {self.explorer.data.shape} | "
                f"<b>Last compute:</b> {compute_time*1000:.1f} ms | "
                f"<b>Data range:</b> [{np.nanmin(moment_map):.2e}, {np.nanmax(moment_map):.2e}]"
            )

        except Exception as e:
            self._status_label.value = f"<b style='color:red;'>Error:</b> {str(e)}"

    def _update_plot(self, moment_map, moment_type):
        """Update the Plotly figure with new data."""
        # Compute new color limits
        if moment_type in ['M0', 'M8']:
            vmin, vmax = np.nanpercentile(moment_map, [50, 99.99])
        elif moment_type == 'M1':
            vmin, vmax = np.nanpercentile(moment_map, [2, 98])
        else:  # M9
            vmin, vmax = np.nanpercentile(moment_map, [5, 95])

        # Update colorbar label
        colorbar_labels = {
            'M0': 'Integrated Intensity',
            'M1': 'Velocity [km/s]',
            'M8': 'Peak Intensity',
            'M9': 'Linewidth [km/s]'
        }

        # Update figure in place
        with self.fig.batch_update():
            self.fig.data[0].z = moment_map
            self.fig.layout.coloraxis.cmin = vmin
            self.fig.layout.coloraxis.cmax = vmax
            self.fig.layout.coloraxis.colorbar.title = colorbar_labels.get(
                moment_type, 'Intensity'
            )

            # Use RdBu_r for velocity (M1)
            if moment_type == 'M1':
                if self.widgets['colorscale'].value not in ['RdBu_r']:
                    self.widgets['colorscale'].value = 'RdBu_r'

    def _on_save(self):
        """Save the current moment map to FITS."""
        with self._save_output:
            self._save_output.clear_output()
            try:
                path = self.explorer.save()
                print(f"✓ Moment map saved to: {path}")
            except Exception as e:
                print(f"✗ Error saving: {str(e)}")

    def _on_reset_view(self):
        """Reset the plot view to default."""
        extent = self.explorer.get_wcs_extent()
        if extent:
            x_min, x_max, y_min, y_max = extent
            with self.fig.batch_update():
                self.fig.layout.xaxis.range = [x_max, x_min]
                self.fig.layout.yaxis.range = [y_min, y_max]
        else:
            with self.fig.batch_update():
                self.fig.layout.xaxis.autorange = True
                self.fig.layout.yaxis.autorange = True

    def display(self):
        """Display the complete UI."""
        # Layout widgets
        controls_left = widgets.VBox([
            self.widgets['moment'],
            self.widgets['first_channel'],
            self.widgets['last_channel'],
            self.widgets['clip_sigma'],
        ])

        controls_right = widgets.VBox([
            self.widgets['use_mask'],
            self.widgets['colorscale'],
            self.widgets['auto_apply'],
        ])

        controls = widgets.HBox([controls_left, controls_right])

        buttons = widgets.HBox([
            self.widgets['apply_button'],
            self.widgets['save_button'],
            self.widgets['reset_button']
        ])

        ui = widgets.VBox([
            controls,
            buttons,
            self._status_label,
            self.fig,
            self._save_output
        ])

        display(ui)


def create_interactive_explorer(cube_path, mask_path=None, enable_prefix_sums=True):
    """
    Convenience function to create and display an interactive moment map explorer.

    Args:
        cube_path (str): Path to the FITS cube.
        mask_path (str): Path to the mask FITS file (optional).
        enable_prefix_sums (bool): Enable prefix-sum optimization for M0/M1.

    Returns:
        tuple: (MomentMapExplorer, MomentMapUI)
    """
    from .explorer import MomentMapExplorer

    # Create explorer and load cube
    explorer = MomentMapExplorer()
    info = explorer.load_cube(cube_path, mask_path)

    print(f"Cube loaded: {info['shape']}")
    print(f"Velocity range: {info['vel_range'][0]:.2f} to {info['vel_range'][1]:.2f} km/s")
    print(f"RMS: {info['rms']:.3e}")

    # Enable prefix sums if requested
    if enable_prefix_sums:
        explorer.enable_prefix_sums(True)
        print("Prefix-sum optimization enabled for M0/M1")

    # Create and display UI
    ui = MomentMapUI(explorer)
    ui.display()

    return explorer, ui
