"""
Core MomentMapExplorer class for computing and caching moment maps.
"""
import time
import numpy as np
import bettermoments as bm
from astropy.io import fits


class MomentMapExplorer:
    """
    High-performance moment map generator for FITS spectral cubes.

    Attributes:
        data (np.ndarray): The spectral cube data (nchan, ny, nx).
        velax (np.ndarray): The velocity axis (nchan,).
        mask (np.ndarray): The user mask (nchan, ny, nx).
        rms (float): Estimated RMS noise.
        header (fits.Header): FITS header for WCS information.
        cube_path (str): Path to the loaded cube.
        mask_path (str): Path to the loaded mask (if any).
        current_moment (np.ndarray): The most recently computed moment map.
        current_uncertainty (np.ndarray): The uncertainty map for the current moment.
    """

    def __init__(self):
        """Initialize an empty MomentMapExplorer."""
        self.data = None
        self.velax = None
        self.mask = None
        self.rms = None
        self.header = None
        self.cube_path = None
        self.mask_path = None
        self.current_moment = None
        self.current_uncertainty = None
        self.current_params = {}

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

        # Load data using bettermoments
        self.data, self.velax = bm.load_cube(cube_path)

        # Load mask
        if mask_path:
            self.mask = bm.get_user_mask(data=self.data, user_mask_path=mask_path)
        else:
            self.mask = np.ones_like(self.data)

        # Estimate RMS
        self.rms = bm.estimate_RMS(data=self.data, N=5)

        # Cache header for WCS
        self.header = fits.getheader(cube_path)

        return {
            'shape': self.data.shape,
            'vel_range': (float(self.velax[0]), float(self.velax[-1])),
            'rms': float(self.rms),
            'n_channels': len(self.velax)
        }

    def _compute_moment_standard(self, moment, first, last, clip_sigma, use_mask):
        """
        Compute moment maps using standard bettermoments functions.

        Args:
            moment (str): Moment type ('M0', 'M1', 'M8', 'M9').
            first (int): First channel index.
            last (int): Last channel index.
            clip_sigma (float): Clipping threshold in sigma.
            use_mask (bool): Whether to apply the user mask.

        Returns:
            np.ndarray: The computed moment map.
        """
        # Create channel mask
        channel_mask = bm.get_channel_mask(
            data=self.data,
            firstchannel=first,
            lastchannel=last
        )

        # Create threshold mask only if clipping is requested
        # bettermoments expects None (not 0.0) when no clipping is desired
        if clip_sigma > 0:
            threshold_mask = bm.get_threshold_mask(
                data=self.data,
                clip=clip_sigma,
                smooth_threshold_mask=0.0
            )
        else:
            threshold_mask = None

        # Apply masks based on moment type
        if moment in ['M0', 'M8']:
            # M0 and M8: use clipping only if explicitly requested
            if use_mask:
                masked_data = self.data * channel_mask * self.mask
                if threshold_mask is not None:
                    masked_data = masked_data * threshold_mask
            else:
                masked_data = self.data * channel_mask
                if threshold_mask is not None:
                    masked_data = masked_data * threshold_mask
        else:  # M1 or M9
            # M1 and M9: always use threshold mask if provided
            if threshold_mask is not None:
                masked_data = self.data * threshold_mask * channel_mask
            else:
                # If no clipping requested, use a minimal threshold (3 sigma)
                threshold_mask = bm.get_threshold_mask(
                    data=self.data,
                    clip=3.0,
                    smooth_threshold_mask=0.0
                )
                masked_data = self.data * threshold_mask * channel_mask

        # Compute the moment (returns tuple: moment_map, uncertainty)
        if moment == 'M0':
            moment_map, uncertainty = bm.collapse_zeroth(
                velax=self.velax,
                data=masked_data,
                rms=self.rms
            )
        elif moment == 'M1':
            moment_map, uncertainty = bm.collapse_first(
                velax=self.velax,
                data=masked_data,
                rms=self.rms
            )
        elif moment == 'M8':
            moment_map, uncertainty = bm.collapse_eighth(
                velax=self.velax,
                data=masked_data,
                rms=self.rms
            )
        elif moment == 'M9':
            moment_map, uncertainty = bm.collapse_ninth(
                velax=self.velax,
                data=masked_data,
                rms=self.rms
            )
        else:
            raise ValueError(f"Unknown moment type: {moment}")

        return moment_map, uncertainty

    def generate(self, moment, first, last, clip_sigma, use_mask):
        """
        Generate a moment map with the specified parameters.

        Args:
            moment (str): Moment type ('M0', 'M1', 'M8', 'M9').
            first (int): First channel index.
            last (int): Last channel index.
            clip_sigma (float): Clipping threshold in sigma.
            use_mask (bool): Whether to apply the user mask.

        Returns:
            tuple: (moment_map, compute_time_seconds)
        """
        if self.data is None:
            raise RuntimeError("No cube loaded. Call load_cube() first.")

        # Validate inputs
        first = max(0, min(first, len(self.velax) - 1))
        last = max(first, min(last, len(self.velax) - 1))

        start_time = time.time()

        # Compute moment map using bettermoments
        self.current_moment, self.current_uncertainty = self._compute_moment_standard(
            moment, first, last, clip_sigma, use_mask
        )

        compute_time = time.time() - start_time

        # Cache parameters
        self.current_params = {
            'moment': moment,
            'first': first,
            'last': last,
            'clip_sigma': clip_sigma,
            'use_mask': use_mask
        }

        return self.current_moment, compute_time

    def save(self, path=None):
        """
        Save the current moment map to a FITS file.

        Args:
            path (str): Optional output path. If None, derives from cube_path.

        Returns:
            str: The path to the saved FITS file.
        """
        if self.current_moment is None:
            raise RuntimeError("No moment map to save. Call generate() first.")

        # Determine output path
        if path is None:
            # Auto-generate path from cube path
            output_path = self.cube_path.replace('.fits', f'_{self.current_params["moment"]}.fits')
        else:
            output_path = path

        # Create a 2D header from the 3D cube header
        header_2d = self.header.copy()

        # Remove all axis-3 and higher keywords
        keys_to_remove = []
        for key in header_2d.keys():
            if any(key.endswith(str(i)) for i in range(3, 10)):  # Remove axis 3-9
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del header_2d[key]

        # Update NAXIS to 2
        header_2d['NAXIS'] = 2

        # Add metadata about the moment map
        moment_type = self.current_params['moment']
        header_2d['COMMENT'] = f'Moment {moment_type} map'
        header_2d['COMMENT'] = f'Generated with moment-explorer'
        header_2d['COMMENT'] = f'Channels: {self.current_params["first"]}-{self.current_params["last"]}'
        header_2d['COMMENT'] = f'Clip sigma: {self.current_params["clip_sigma"]}'

        # Set appropriate BUNIT
        if moment_type in ['M0', 'M8']:
            header_2d['BUNIT'] = 'Jy/beam km/s' if moment_type == 'M0' else 'Jy/beam'
        else:  # M1, M9
            header_2d['BUNIT'] = 'km/s'

        # Save moment map
        hdu = fits.PrimaryHDU(self.current_moment.astype(np.float32), header=header_2d)
        hdu.writeto(output_path, overwrite=True)

        # Save uncertainty map if available
        saved_paths = [output_path]
        if self.current_uncertainty is not None:
            uncertainty_path = output_path.replace(f'_{moment_type}.fits', f'_d{moment_type}.fits')

            # Update header for uncertainty
            header_uncertainty = header_2d.copy()
            header_uncertainty['COMMENT'] = f'Uncertainty for {moment_type} map'
            header_uncertainty['COMMENT'] = f'Generated with moment-explorer'

            # Save uncertainty
            hdu_uncertainty = fits.PrimaryHDU(self.current_uncertainty.astype(np.float32), header_uncertainty)
            hdu_uncertainty.writeto(uncertainty_path, overwrite=True)
            saved_paths.append(uncertainty_path)

        return saved_paths

    def get_wcs_extent(self):
        """
        Get the WCS extent for plotting.

        Returns:
            tuple or None: (xmin, xmax, ymin, ymax) in arcsec offsets, or None if no header.
        """
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
