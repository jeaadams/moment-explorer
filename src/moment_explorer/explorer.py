"""
Core MomentMapExplorer class for computing and caching moment maps.
"""
import time
import numpy as np
import bettermoments as bm
from astropy.io import fits


class MomentMapExplorer:
    """
    High-performance moment map generator with caching and optional prefix-sum optimization.

    Attributes:
        data (np.ndarray): The spectral cube data (nchan, ny, nx).
        velax (np.ndarray): The velocity axis (nchan,).
        mask (np.ndarray): The user mask (nchan, ny, nx).
        rms (float): Estimated RMS noise.
        header (fits.Header): FITS header for WCS information.
        cube_path (str): Path to the loaded cube.
        mask_path (str): Path to the loaded mask (if any).
        current_moment (np.ndarray): The most recently computed moment map.
        use_prefix_sums (bool): Whether to use prefix-sum optimization for M0/M1.
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
        self.current_params = {}

        # Prefix-sum caching
        self.use_prefix_sums = False
        self._S0 = None  # Cumulative sum for M0
        self._S1 = None  # Cumulative sum for M1
        self._prefix_mask = None  # Mask used for prefix sums

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

        # Clear prefix sums (will be recomputed if needed)
        self._S0 = None
        self._S1 = None
        self._prefix_mask = None

        return {
            'shape': self.data.shape,
            'vel_range': (float(self.velax[0]), float(self.velax[-1])),
            'rms': float(self.rms),
            'n_channels': len(self.velax)
        }

    def enable_prefix_sums(self, flag=True):
        """
        Enable or disable prefix-sum optimization for M0/M1 computation.

        Args:
            flag (bool): Whether to enable prefix sums.
        """
        self.use_prefix_sums = flag
        if not flag:
            # Clear cached prefix sums
            self._S0 = None
            self._S1 = None
            self._prefix_mask = None

    def _compute_prefix_sums(self, channel_mask, use_mask):
        """
        Compute and cache prefix sums for M0/M1 optimization.

        Args:
            channel_mask (np.ndarray): Channel selection mask.
            use_mask (bool): Whether to apply the user mask.
        """
        # Build the effective mask
        if use_mask:
            effective_mask = channel_mask * self.mask
        else:
            effective_mask = channel_mask

        # Check if we need to recompute
        if self._S0 is not None and np.array_equal(effective_mask, self._prefix_mask):
            return  # Already computed

        # Compute prefix sums
        masked_data = self.data * effective_mask
        self._S0 = np.cumsum(masked_data, axis=0)

        # For M1: cumulative sum of velocity * intensity
        vel_broadcasted = self.velax[:, None, None]
        self._S1 = np.cumsum(vel_broadcasted * masked_data, axis=0)

        # Cache the mask used
        self._prefix_mask = effective_mask.copy()

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
        # Create masks
        channel_mask = bm.get_channel_mask(
            data=self.data,
            firstchannel=first,
            lastchannel=last
        )
        threshold_mask = bm.get_threshold_mask(
            data=self.data,
            clip=clip_sigma,
            smooth_threshold_mask=0.0
        )

        # Apply masks based on moment type
        if moment in ['M0', 'M8']:
            if use_mask:
                masked_data = self.data * channel_mask * self.mask
            else:
                masked_data = self.data * channel_mask
        else:  # M1 or M9
            masked_data = self.data * threshold_mask * channel_mask

        # Compute the moment
        if moment == 'M0':
            result = bm.collapse_zeroth(
                velax=self.velax,
                data=masked_data,
                rms=self.rms
            )[0]
        elif moment == 'M1':
            result = bm.collapse_first(
                velax=self.velax,
                data=masked_data,
                rms=self.rms
            )[0]
        elif moment == 'M8':
            result = bm.collapse_eighth(
                velax=self.velax,
                data=masked_data,
                rms=self.rms
            )[0]
        elif moment == 'M9':
            result = bm.collapse_ninth(
                velax=self.velax,
                data=masked_data,
                rms=self.rms
            )[0]
        else:
            raise ValueError(f"Unknown moment type: {moment}")

        return result

    def _compute_moment_prefix(self, moment, first, last, use_mask):
        """
        Compute M0 or M1 using prefix-sum optimization.

        Args:
            moment (str): Moment type ('M0' or 'M1').
            first (int): First channel index.
            last (int): Last channel index.
            use_mask (bool): Whether to apply the user mask.

        Returns:
            np.ndarray: The computed moment map.
        """
        # Create channel mask for prefix sum computation
        channel_mask = np.zeros_like(self.data)
        channel_mask[first:last+1, :, :] = 1.0

        # Ensure prefix sums are computed
        self._compute_prefix_sums(channel_mask, use_mask)

        # Extract the range using prefix sums
        if first == 0:
            M0 = self._S0[last, :, :]
            if moment == 'M1':
                M1_numerator = self._S1[last, :, :]
        else:
            M0 = self._S0[last, :, :] - self._S0[first - 1, :, :]
            if moment == 'M1':
                M1_numerator = self._S1[last, :, :] - self._S1[first - 1, :, :]

        if moment == 'M0':
            # Convert to integrated intensity (multiply by channel width)
            dv = np.abs(self.velax[1] - self.velax[0])
            return M0 * dv
        elif moment == 'M1':
            # Compute velocity centroid
            M1 = M1_numerator / (M0 + 1e-12)
            # Mask out regions with no signal
            M1[M0 < 3 * self.rms] = np.nan
            return M1

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

        # Use prefix sums for M0/M1 if enabled
        if self.use_prefix_sums and moment in ['M0', 'M1']:
            self.current_moment = self._compute_moment_prefix(moment, first, last, use_mask)
        else:
            self.current_moment = self._compute_moment_standard(
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

        # bettermoments.save_to_FITS expects moments as a tuple/list for some methods
        # Wrap the moment map to ensure compatibility
        moment_data = self.current_moment

        # Determine output path and method
        method_map = {'M0': 'zeroth', 'M1': 'first', 'M8': 'eighth', 'M9': 'ninth'}
        method = method_map[self.current_params['moment']]

        if path is None:
            # Auto-generate path from cube path
            output_path = self.cube_path.replace('.fits', f'_{self.current_params["moment"]}.fits')
        else:
            output_path = path

        # Save using bettermoments
        try:
            bm.save_to_FITS(moments=moment_data, method=method, path=self.cube_path)
            # bettermoments saves to cube_path with method suffix, find the actual file
            return self.cube_path.replace('.fits', f'_{self.current_params["moment"]}.fits')
        except (ValueError, TypeError, AttributeError) as e:
            # If bettermoments fails, save manually with astropy
            from astropy.io import fits

            # Create a 2D header from the 3D cube header
            header_2d = self.header.copy()

            # Remove spectral axis keywords
            keys_to_remove = ['NAXIS3', 'CTYPE3', 'CRVAL3', 'CDELT3', 'CRPIX3', 'CUNIT3']
            for key in keys_to_remove:
                if key in header_2d:
                    del header_2d[key]

            # Update NAXIS to 2
            header_2d['NAXIS'] = 2

            # Add comment about the moment map
            header_2d['COMMENT'] = f'Moment {self.current_params["moment"]} map'
            header_2d['COMMENT'] = f'Generated with moment-explorer'
            header_2d['BUNIT'] = 'Jy/beam' if method in ['zeroth', 'eighth'] else 'km/s'

            # Create HDU and save
            hdu = fits.PrimaryHDU(moment_data, header=header_2d)
            hdu.writeto(output_path, overwrite=True)

            return output_path

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
