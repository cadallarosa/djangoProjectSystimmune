from pyopenms import *
import numpy as np

# Load the mzML file
exp = MSExperiment()
MzMLFile().load("RN1.mzML", exp)

# Extract the (only) spectrum
spectra_data = []
for spectrum in exp.getSpectra():
    mz_array, intensity_array = spectrum.get_peaks()
    rt = spectrum.getRT() / 60.0  # Convert seconds to minutes
    ms_level = spectrum.getMSLevel()

    # Calculate base peak and TIC
    if len(intensity_array) > 0:
        max_idx = np.argmax(intensity_array)
        base_peak_mz = mz_array[max_idx]
        base_peak_intensity = intensity_array[max_idx]
        total_ion_current = np.sum(intensity_array)
    else:
        base_peak_mz = None
        base_peak_intensity = None
        total_ion_current = 0

    spectra_data.append({
        "rt": rt,
        "ms_level": ms_level,
        "mz_array": mz_array,
        "intensity_array": intensity_array,
        "base_peak_mz": base_peak_mz,
        "base_peak_intensity": base_peak_intensity,
        "total_ion_current": total_ion_current
    })

# Show summary for first (and only) spectrum
spec = spectra_data[0]
print(f"RT: {spec['rt']:.2f} min")
print(f"MS Level: {spec['ms_level']}")
print(f"Base Peak m/z: {spec['base_peak_mz']}")
print(f"Total Ion Current: {spec['total_ion_current']:.1f}")

# Show first 10 m/z-intensity pairs
print("First 10 m/z and intensities:")
for m, i in zip(spec["mz_array"][:10], spec["intensity_array"][:10]):
    print(f"  m/z: {m:.4f}, Intensity: {i:.2f}")

# Show m/z range and top 20 most intense peaks
mz_array = spec["mz_array"]
intensity_array = spec["intensity_array"]
print(f"\nObserved m/z range: {mz_array.min():.2f} - {mz_array.max():.2f}")

top_peaks = sorted(zip(mz_array, intensity_array), key=lambda x: -x[1])[:20]
print("\nTop 20 intense peaks:")
for mz, intensity in top_peaks:
    print(f"  m/z: {mz:.4f}, Intensity: {intensity:.2f}")

# --------------------------
# Glycan Matching (m/z only)
# --------------------------

# Sample glycan list (neutral masses in Da)
glycans = {
    "M3": 894.32,
    "F(6)M3": 1050.37,
    "A2G(4)2": 1460.53,
    "F(6)A2G(4)2": 1616.59,
    "M5": 1256.42,
}

# Common adducts
adducts = {
    "[M+H]+": 1.0073,
    "[M+Na]+": 22.9898,
    "[M+K]+": 38.9637,
}

# Tolerance
ppm_tolerance = 10

def ppm_error(observed, theoretical):
    return 1e6 * abs(observed - theoretical) / theoretical

# Match observed m/z to theoretical m/z
matches = []
for glycan_name, neutral_mass in glycans.items():
    for adduct_name, adduct_mass in adducts.items():
        theo_mz = neutral_mass + adduct_mass
        for mz, intensity in zip(mz_array, intensity_array):
            error = ppm_error(mz, theo_mz)
            if error <= ppm_tolerance:
                matches.append({
                    "glycan": glycan_name,
                    "adduct": adduct_name,
                    "theoretical_mz": theo_mz,
                    "observed_mz": mz,
                    "ppm_error": round(error, 2),
                    "intensity": round(intensity, 2)
                })

# Sort matches by intensity
matches = sorted(matches, key=lambda x: -x["intensity"])

print("\nMatched Glycans (±10 ppm):")
if matches:
    for match in matches:
        print(f"{match['glycan']} {match['adduct']}: "
              f"Observed m/z = {match['observed_mz']:.4f}, "
              f"Theoretical m/z = {match['theoretical_mz']:.4f}, "
              f"ppm error = {match['ppm_error']}, "
              f"Intensity = {match['intensity']}")
else:
    print("No matches found.")
