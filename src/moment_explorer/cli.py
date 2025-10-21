"""
Command-line interface for moment-explorer with interactive file browser.
"""
import os
import sys
import ipywidgets as widgets
from IPython.display import display, clear_output
from pathlib import Path


def browse_files(start_path=None, file_pattern='*.fits'):
    """
    Interactive file browser widget for selecting FITS files.

    Args:
        start_path (str): Starting directory. Defaults to current directory.
        file_pattern (str): Glob pattern for files to show.

    Returns:
        str: Selected file path or None if cancelled.
    """
    if start_path is None:
        start_path = os.getcwd()

    start_path = Path(start_path).expanduser().absolute()

    # Widgets
    current_path = widgets.HTML(value=f"<b>Current directory:</b> {start_path}")
    file_list = widgets.Select(options=[], description='Files:', rows=15, layout=widgets.Layout(width='600px'))
    selected_file = widgets.HTML(value="<i>No file selected</i>")

    # Buttons
    up_button = widgets.Button(description='↑ Parent Directory', button_style='info')
    select_button = widgets.Button(description='Select File', button_style='success')
    cancel_button = widgets.Button(description='Cancel', button_style='danger')

    output = widgets.Output()
    result = {'path': None, 'done': False}

    def update_file_list(path):
        """Update the file list for the given directory."""
        path = Path(path)
        items = []

        # Add directories first
        try:
            for item in sorted(path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    items.append(f"📁 {item.name}/")

            # Add matching files
            for item in sorted(path.glob(file_pattern)):
                if item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    items.append(f"📄 {item.name} ({size_mb:.1f} MB)")

            file_list.options = items if items else ['<empty directory>']
            current_path.value = f"<b>Current directory:</b> {path}"

        except PermissionError:
            file_list.options = ['<Permission denied>']

    def on_file_select(change):
        """Handle file/directory selection."""
        if not change['new']:
            return

        selection = change['new']
        current_dir = Path(current_path.value.split('</b> ')[1])

        if selection.startswith('📁'):
            # Navigate into directory
            dir_name = selection.replace('📁 ', '').rstrip('/')
            new_path = current_dir / dir_name
            update_file_list(new_path)
            selected_file.value = "<i>No file selected</i>"

        elif selection.startswith('📄'):
            # File selected
            file_name = selection.split(' ')[1]
            file_path = current_dir / file_name
            selected_file.value = f"<b>Selected:</b> {file_path}"

    def on_up_button(b):
        """Go to parent directory."""
        current_dir = Path(current_path.value.split('</b> ')[1])
        parent = current_dir.parent
        update_file_list(parent)
        selected_file.value = "<i>No file selected</i>"

    def on_select_button(b):
        """Confirm selection."""
        selection = file_list.value
        if selection and selection.startswith('📄'):
            current_dir = Path(current_path.value.split('</b> ')[1])
            file_name = selection.split(' ')[1]
            result['path'] = str(current_dir / file_name)
            result['done'] = True
            with output:
                clear_output()
                print(f"✓ Selected: {result['path']}")

    def on_cancel_button(b):
        """Cancel selection."""
        result['done'] = True
        with output:
            clear_output()
            print("✗ Cancelled")

    # Connect callbacks
    file_list.observe(on_file_select, names='value')
    up_button.on_click(on_up_button)
    select_button.on_click(on_select_button)
    cancel_button.on_click(on_cancel_button)

    # Initial file list
    update_file_list(start_path)

    # Layout
    buttons = widgets.HBox([up_button, select_button, cancel_button])
    browser_ui = widgets.VBox([
        current_path,
        file_list,
        selected_file,
        buttons,
        output
    ])

    display(browser_ui)

    return result


def launch_interactive_explorer():
    """
    Launch interactive file browser to select cube and mask, then start explorer.

    This function creates a Jupyter-based UI for file selection and launches
    the moment map explorer.
    """
    print("=" * 60)
    print("Moment Explorer - Interactive Launcher")
    print("=" * 60)

    # Step 1: Select cube file
    print("\n📂 Step 1: Select your FITS cube file")
    cube_result = browse_files(file_pattern='*.fits')

    # Wait for user interaction (in notebook, this is handled by widget callbacks)
    # For a real blocking implementation, you'd need a different approach

    print("\nNote: This function is designed for Jupyter notebooks.")
    print("For command-line use, please specify files directly:")
    print("\n  from moment_explorer import create_interactive_explorer")
    print("  explorer, ui = create_interactive_explorer('path/to/cube.fits', 'path/to/mask.fits')")


def create_launcher_ui():
    """
    Create a Jupyter UI for launching the explorer with file browser.

    Returns:
        VBox widget containing the launcher interface.
    """
    from .ui import create_interactive_explorer

    # Widgets
    cube_path_widget = widgets.Text(
        value='',
        placeholder='/path/to/cube.fits',
        description='Cube:',
        style={'description_width': '100px'},
        layout=widgets.Layout(width='500px')
    )

    mask_path_widget = widgets.Text(
        value='',
        placeholder='/path/to/mask.fits (optional)',
        description='Mask:',
        style={'description_width': '100px'},
        layout=widgets.Layout(width='500px')
    )

    browse_cube_button = widgets.Button(
        description='Browse...',
        button_style='info',
        icon='folder-open'
    )

    browse_mask_button = widgets.Button(
        description='Browse...',
        button_style='info',
        icon='folder-open'
    )

    prefix_sums_checkbox = widgets.Checkbox(
        value=True,
        description='Enable prefix-sum optimization',
        indent=False
    )

    launch_button = widgets.Button(
        description='Launch Explorer',
        button_style='success',
        icon='rocket'
    )

    output = widgets.Output()

    # Callbacks
    def on_browse_cube(b):
        with output:
            clear_output()
            print("Browse for cube file:")
            result = browse_files()

    def on_browse_mask(b):
        with output:
            clear_output()
            print("Browse for mask file:")
            result = browse_files()

    def on_launch(b):
        cube_path = cube_path_widget.value.strip()
        mask_path = mask_path_widget.value.strip() or None

        if not cube_path:
            with output:
                clear_output()
                print("❌ Error: Please specify a cube file path")
            return

        if not os.path.exists(cube_path):
            with output:
                clear_output()
                print(f"❌ Error: Cube file not found: {cube_path}")
            return

        if mask_path and not os.path.exists(mask_path):
            with output:
                clear_output()
                print(f"❌ Error: Mask file not found: {mask_path}")
            return

        with output:
            clear_output()
            print("🚀 Launching explorer...")
            try:
                explorer, ui = create_interactive_explorer(
                    cube_path=cube_path,
                    mask_path=mask_path,
                    enable_prefix_sums=prefix_sums_checkbox.value
                )
                print("✓ Explorer launched successfully!")
            except Exception as e:
                print(f"❌ Error launching explorer: {e}")

    browse_cube_button.on_click(on_browse_cube)
    browse_mask_button.on_click(on_browse_mask)
    launch_button.on_click(on_launch)

    # Layout
    cube_row = widgets.HBox([cube_path_widget, browse_cube_button])
    mask_row = widgets.HBox([mask_path_widget, browse_mask_button])

    launcher_ui = widgets.VBox([
        widgets.HTML("<h2>🔭 Moment Explorer Launcher</h2>"),
        widgets.HTML("<p>Select your FITS cube and optional mask file to begin:</p>"),
        cube_row,
        mask_row,
        prefix_sums_checkbox,
        launch_button,
        output
    ])

    return launcher_ui


def main():
    """
    Main entry point for command-line usage.
    """
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(
        description='Moment Explorer - Interactive FITS cube moment map tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch Jupyter Lab with example notebook
  moment-explorer notebook

  # Open example notebook in current directory
  moment-explorer notebook --here

  # Display help
  moment-explorer --help

For interactive use in Python/Jupyter:
  from moment_explorer import create_multi_cube_explorer
  explorer, ui, selector = create_multi_cube_explorer(available_cubes)
        """
    )

    parser.add_argument(
        'command',
        nargs='?',
        choices=['notebook', 'help'],
        default='help',
        help='Command to run'
    )

    parser.add_argument(
        '--here',
        action='store_true',
        help='Copy example notebook to current directory'
    )

    args = parser.parse_args()

    if args.command == 'help' or args.command is None:
        parser.print_help()
        print("\n" + "="*60)
        print("Moment Explorer Quick Start")
        print("="*60)
        print("\nThis tool requires Jupyter Notebook/Lab to run interactively.")
        print("\nRecommended workflow:")
        print("  1. Run: moment-explorer notebook")
        print("  2. This opens the example notebook in Jupyter Lab")
        print("  3. Follow the notebook instructions to explore your data")
        print("\nOr use in a Python script/notebook:")
        print("  from moment_explorer import create_interactive_explorer")
        print("  explorer, ui = create_interactive_explorer('cube.fits', 'mask.fits')")
        return 0

    elif args.command == 'notebook':
        # Find the example notebook
        import os
        pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        example_nb = os.path.join(pkg_dir, 'examples', 'interactive_moment_maker.ipynb')

        if not os.path.exists(example_nb):
            print(f"❌ Error: Example notebook not found at {example_nb}")
            return 1

        if args.here:
            # Copy to current directory
            import shutil
            dest = os.path.join(os.getcwd(), 'interactive_moment_maker.ipynb')
            if os.path.exists(dest):
                response = input(f"File {dest} already exists. Overwrite? [y/N]: ")
                if response.lower() != 'y':
                    print("Cancelled.")
                    return 0
            shutil.copy(example_nb, dest)
            print(f"✓ Copied notebook to {dest}")
            notebook_path = dest
        else:
            notebook_path = example_nb

        # Try to launch Jupyter Lab, fall back to classic notebook
        print("🚀 Launching Jupyter Lab...")
        try:
            subprocess.run(['jupyter', 'lab', notebook_path], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Jupyter Lab not found, trying classic Jupyter Notebook...")
            try:
                subprocess.run(['jupyter', 'notebook', notebook_path], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("\n❌ Error: Jupyter is not installed.")
                print("\nPlease install Jupyter:")
                print("  pip install jupyterlab")
                print("\nOr:")
                print("  pip install jupyter")
                return 1

        return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
