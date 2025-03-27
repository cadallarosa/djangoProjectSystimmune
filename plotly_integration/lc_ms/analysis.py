import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyteomics import mzxml

# Load mzXML data
reader = mzxml.read('example.mzXML')

# Containers for TIC and XIC
tic_times = []
tic_intensities = []

xic_target_mz = 500.0
xic_tolerance = 0.5
xic_times = []
xic_intensities = []

ms1_spectra = []

# Read and collect data
for spectrum in reader:
    rt = float(spectrum['retentionTime'])  # seconds
    mz_array = spectrum['m/z array']
    intensity_array = spectrum['intensity array']

    # TIC: total intensity per scan
    total_intensity = np.sum(intensity_array)
    tic_times.append(rt)
    tic_intensities.append(total_intensity)

    # XIC: intensity of ions near target m/z
    mask = (mz_array >= xic_target_mz - xic_tolerance) & (mz_array <= xic_target_mz + xic_tolerance)
    xic_intensity = np.sum(intensity_array[mask]) if mask.any() else 0
    xic_times.append(rt)
    xic_intensities.append(xic_intensity)

    # Save MS1 spectrum
    if spectrum['msLevel'] == 1 and len(ms1_spectra) < 3:
        ms1_spectra.append((rt, mz_array, intensity_array))

# Plot TIC with top peaks annotated
plt.figure(figsize=(10, 4))
plt.plot(tic_times, tic_intensities, label='TIC', color='navy')
top_tic_idxs = np.argsort(tic_intensities)[-5:]
for i in top_tic_idxs:
    plt.annotate(f"{tic_times[i]:.1f}s\n{int(tic_intensities[i])}", (tic_times[i], tic_intensities[i]),
                 xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8,
                 arrowprops=dict(arrowstyle='->', lw=0.5))
plt.title("Total Ion Chromatogram (TIC)")
plt.xlabel("Retention Time (s)")
plt.ylabel("Total Intensity")
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot XIC for a specific m/z
plt.figure(figsize=(10, 4))
plt.plot(xic_times, xic_intensities, label=f"XIC @ {xic_target_mz}±{xic_tolerance}", color='darkgreen')
top_xic_idxs = np.argsort(xic_intensities)[-5:]
for i in top_xic_idxs:
    plt.annotate(f"{xic_times[i]:.1f}s\n{int(xic_intensities[i])}", (xic_times[i], xic_intensities[i]),
                 xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8,
                 arrowprops=dict(arrowstyle='->', lw=0.5))
plt.title("Extracted Ion Chromatogram (XIC)")
plt.xlabel("Retention Time (s)")
plt.ylabel("Intensity")
plt.grid(True)
plt.tight_layout()
plt.show()

# Plot overlaid MS1 spectra
plt.figure(figsize=(10, 5))
colors = ['blue', 'red', 'green']
for i, (rt, mzs, intensities) in enumerate(ms1_spectra):
    plt.plot(mzs, intensities, label=f"RT: {rt:.1f}s", alpha=0.7, color=colors[i])
plt.title("Overlay of 3 MS1 Spectra")
plt.xlabel("m/z")
plt.ylabel("Intensity")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
