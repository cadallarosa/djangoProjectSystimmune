import gzip
import shutil

with gzip.open('example.mzXML.gz', 'rb') as f_in:
    with open('example.mzXML', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)


from pyteomics import mzxml

# Open the mzXML file
with mzxml.read('example.mzXML') as reader:
    for spectrum in reader:
        # Access spectrum metadata
        scan_num = spectrum['num']
        ms_level = spectrum['msLevel']
        retention_time = spectrum['retentionTime']

        # Access m/z and intensity arrays
        mz_array = spectrum['m/z array']
        intensity_array = spectrum['intensity array']

        # Process the data as needed
        print(f'Scan: {scan_num}, MS Level: {ms_level}, RT: {retention_time}')
        print(f'm/z array: {mz_array[:5]}')  # Print first 5 m/z values
        print(f'Intensity array: {intensity_array[:5]}')  # Print first 5 intensity values
        break  # Remove this break to process all spectra



import matplotlib.pyplot as plt
from pyteomics import mzxml

times = []
tics = []

with mzxml.read("example.mzXML") as reader:
    for spectrum in reader:
        if spectrum['msLevel'] == 1:  # TIC is usually from MS1
            rt = spectrum['retentionTime']
            tic = sum(spectrum['intensity array'])

            # Convert RT from seconds (e.g. PT8.001083S) to float if needed
            times.append(float(rt))
            tics.append(tic)

plt.plot(times, tics)
plt.title("Total Ion Chromatogram")
plt.xlabel("Retention Time (s)")
plt.ylabel("Total Intensity")
plt.grid(True)
plt.tight_layout()
plt.show()


target_mz = 500.0
tolerance = 0.5  # Da

xic_times = []
xic_intensities = []

with mzxml.read("example.mzXML") as reader:
    for spectrum in reader:
        mzs = spectrum['m/z array']
        intensities = spectrum['intensity array']
        rt = float(spectrum['retentionTime'])

        mask = (mzs >= target_mz - tolerance) & (mzs <= target_mz + tolerance)
        intensity = intensities[mask].sum() if mask.any() else 0

        xic_times.append(rt)
        xic_intensities.append(intensity)

plt.plot(xic_times, xic_intensities)
plt.title(f"XIC for m/z ≈ {target_mz}")
plt.xlabel("Retention Time (s)")
plt.ylabel("Intensity")
plt.grid(True)
plt.tight_layout()
plt.show()
