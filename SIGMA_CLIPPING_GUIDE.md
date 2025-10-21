# Sigma Clipping Guide

## What Changed

Sigma clipping is now available for **all moment types** (M0, M1, M8, M9), with intelligent warnings to guide users toward best practices.

## How Sigma Clipping Works

**Clip σ slider** (range: 0.0 to 10.0)
- **Value = 0**: No clipping (default) - all pixels are included
- **Value > 0**: Excludes pixels below `value × RMS` from the calculation

Example:
- RMS = 0.005 Jy/beam
- Clip σ = 3.0
- Threshold = 3.0 × 0.005 = 0.015 Jy/beam
- All pixels < 0.015 Jy/beam are masked out

## Recommendations by Moment Type

### M0 (Integrated Intensity) - Clip σ = 0 ⭐ RECOMMENDED

**Why clip σ = 0:**
- M0 measures **total flux** from the source
- Faint, extended emission contributes to total flux
- Clipping excludes faint emission → underestimates flux
- User mask already defines the spatial region

**When to use clip σ > 0:**
- Only if you specifically want to exclude faint emission
- When studying compact, bright cores only
- Be aware you're measuring a **lower limit** on flux

**Warning System:**
- Orange warning appears if M0 is selected with clip σ > 0
- Reminds you that clipping underestimates total flux
- Suggestion to set clip σ to 0

### M1 (Velocity Centroid) - Clip σ = 3-5 ⭐ RECOMMENDED

**Why clip σ > 0:**
- M1 measures velocity-weighted centroid
- Noise can bias velocity measurements
- Clipping ensures only real emission contributes
- Prevents noisy pixels from skewing velocity

**Typical values:**
- Clip σ = 3.0: Conservative, includes most real emission
- Clip σ = 5.0: Strict, only bright emission
- Clip σ = 2.0: Very sensitive, may include some noise

### M8 (Peak Intensity) - Either is OK

**Clip σ = 0:**
- Measures maximum pixel value in each spectrum
- Already robust to noise (max operation)
- User mask defines region

**Clip σ > 0:**
- Can help if mask includes noisy regions
- Ensures peak is from real emission
- Useful if mask is generous

**Recommendation:** Use user mask + clip σ = 0 if mask is well-defined

### M9 (Linewidth) - Clip σ = 3-5 ⭐ RECOMMENDED

**Why clip σ > 0:**
- M9 measures spectral width
- Noise artificially broadens lines
- Clipping prevents noise from inflating linewidth
- Essential for accurate FWHM measurements

**Typical values:**
- Clip σ = 3.0: Standard for linewidth measurements
- Clip σ = 5.0: Very strict, only bright cores

## UI Features

### Help Text
Below the control sliders, you'll see:
> 💡 Clip σ: Set to 0 for no clipping (recommended for M0). Values > 0 exclude pixels below σ×RMS (useful for M1/M9).

### Warning for M0 + Clipping
If you select M0 with clip σ > 0, an orange warning appears:
> ⚠ Warning: Sigma clipping is enabled for M0. This is NOT recommended as it excludes faint emission and underestimates total flux. Set clip σ to 0 to disable clipping for M0.

### Default Value
- New default: **Clip σ = 0.0** (no clipping)
- Previously: 3.0 (always clipped)
- This aligns with best practices for flux measurements

## Examples

### Example 1: Total Flux Measurement (M0)

```python
from moment_explorer import create_interactive_explorer

explorer, ui = create_interactive_explorer('cube.fits', 'mask.fits')

# In UI:
# 1. Select Moment: M0
# 2. Set Clip σ: 0.0  ← No clipping
# 3. Enable "Use mask"
# 4. Click Apply
# → Measures total flux within mask
```

### Example 2: Velocity Map (M1)

```python
explorer, ui = create_interactive_explorer('cube.fits', 'mask.fits')

# In UI:
# 1. Select Moment: M1
# 2. Set Clip σ: 3.0  ← Exclude noise
# 3. Click Apply
# → Velocity only computed where S/N > 3
```

### Example 3: Comparing Clipped vs Unclipped M0

```python
from moment_explorer import MomentMapExplorer

explorer = MomentMapExplorer()
explorer.load_cube('cube.fits', 'mask.fits')

# Without clipping
M0_noclip, _ = explorer.generate('M0', 30, 70, clip_sigma=0.0, use_mask=True)
total_flux_noclip = np.nansum(M0_noclip)

# With clipping
M0_clip, _ = explorer.generate('M0', 30, 70, clip_sigma=3.0, use_mask=True)
total_flux_clip = np.nansum(M0_clip)

# Compare
flux_ratio = total_flux_clip / total_flux_noclip
print(f"Clipping excludes {(1-flux_ratio)*100:.1f}% of total flux")
# Typical result: "Clipping excludes 15-30% of total flux"
```

## Technical Details

### How Clipping is Applied

For **all moment types**, if clip σ > 0:

```python
# Create threshold mask
threshold_mask = data > (clip_sigma * RMS)

# Apply to data
if moment in ['M0', 'M8']:
    masked_data = data * channel_mask * user_mask * threshold_mask
else:  # M1, M9
    masked_data = data * channel_mask * threshold_mask
```

### Order of Operations

1. **Channel mask**: Select spectral range (first_channel to last_channel)
2. **User mask**: Apply spatial mask (if use_mask=True)
3. **Threshold mask**: Apply sigma clipping (if clip_sigma > 0)
4. **Collapse**: Compute moment map

### RMS Estimation

RMS is automatically estimated using `bettermoments.estimate_RMS()`:
- Samples outer edge channels (assumed line-free)
- Robust to outliers
- Typical values: 1e-3 to 1e-2 Jy/beam

You can check RMS value in the loading output:
```
Cube loaded: (100, 500, 500)
RMS: 3.878e-03  ← This is the RMS used for clipping
```

## Migration from Old Behavior

**Old behavior:**
- M0/M8: No clipping (only user mask)
- M1/M9: Always clipped at 3σ
- Default clip σ: 3.0

**New behavior:**
- M0/M1/M8/M9: All support clipping
- Default clip σ: 0.0 (no clipping)
- User chooses when to clip

**If you want old behavior:**
- M0/M8: Set clip σ = 0 (same as before)
- M1/M9: Set clip σ = 3.0 (same as before)

## Best Practices Summary

| Moment | Clip σ | Reason |
|--------|--------|--------|
| **M0** | **0** | Preserve total flux |
| **M1** | **3-5** | Exclude noisy velocities |
| **M8** | **0** | Max already robust; use mask |
| **M9** | **3-5** | Prevent noise broadening |

## FAQs

**Q: Why does the warning only appear for M0?**
A: M0 (total flux) is most commonly misused with clipping. M1/M9 usually benefit from clipping, so no warning is needed.

**Q: Can I disable the warning?**
A: The warning only appears when M0 + clip σ > 0. Set clip σ = 0 to remove it.

**Q: What if my mask is bad and includes noise?**
A: Fix your mask! Clipping is not a substitute for a good mask. Use the Cube Viewer to check mask coverage.

**Q: Should I use clip σ for masking instead of creating a mask file?**
A: No. Clipping is velocity-dependent (changes per channel), while masks are typically 3D. Use both: mask for spatial selection, clipping for S/N threshold.

**Q: How do I know what clip σ to use?**
A: Start with 3.0 (standard). If your data is noisy, try 5.0. If you need to include faint emission (for M1/M9), try 2.0.

## Related Documentation

- [README.md](README.md) - Main package documentation
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick reference guide
- [COMPARISON.md](COMPARISON.md) - Before/after refactoring comparison
