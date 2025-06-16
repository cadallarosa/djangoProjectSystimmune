from pyteomics import mzml
import pandas as pd

ms1_data = []

# Ensure we're starting from the top of the file
with mzml.MzML("FB1387_fixed.mzML") as reader:
    for spectrum in reader:
        if spectrum.get('ms level') == 1:
            rt = spectrum.get('scanList', {}).get('scan', [{}])[0].get('scan start time')
            mz = spectrum.get('base peak m/z')
            intensity = spectrum.get('base peak intensity')
            if rt and mz and intensity:
                ms1_data.append({
                    'retention_time_min': float(rt),
                    'base_peak_mz': float(mz),
                    'base_peak_intensity': float(intensity)
                })

# Convert and save
df = pd.DataFrame(ms1_data)
df.sort_values("retention_time_min", inplace=True)
print(df.head())  # Optional preview
df.to_csv("base_peak_chromatogram.csv", index=False)


from pyteomics import mzml
from collections import Counter

ms_levels = []

with mzml.MzML("FB1387_fixed.mzML") as reader:
    for spectrum in reader:
        level = spectrum.get("ms level")
        ms_levels.append(level)

level_counts = Counter(ms_levels)
print("MS Level Counts:", level_counts)
