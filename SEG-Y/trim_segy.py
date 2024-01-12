# pick out first reflection
# first_reflections = np.where(f.trace.raw[100:-100] > 0.01)
# first_reflection = np.min(first_reflections[1])

import segyio
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import sys
from time import time
import datetime


def trim_segy(
    segy_file: Path, start_time, end_time, destination: Path, overwrite=False
):
    export_filename = destination / (segy_file.stem + "_TRIM.sgy")
    # Skip if file already exists
    if export_filename.exists() and not overwrite:
        print(f"File {export_filename.stem} already exists")
        return
    try:
        tic = time()
        with segyio.open(segy_file, ignore_geometry=True) as src:
            spec = segyio.tools.metadata(src)
            samples = src.samples
            first_idx = np.where(samples > start_time)[0][0]
            last_idx = np.where(samples > end_time)[0][0]
            samples = samples[first_idx:last_idx]
            spec.samples = samples
            tracecount = src.tracecount

            with segyio.create(export_filename, spec) as dst:
                dst.text[0] = src.text[0]
                print("Copying binary header")
                dst.bin = src.bin
                dst.bin[segyio.BinField.Samples] = len(samples)

                # print("Setting up empty trace array")
                # dst.trace = np.zeros((tracecount, len(samples)), dtype=np.float32)
                # print('Trace shape', np.shape(dst.trace))
                # Copy headers and set new sample count

                print(f"Copying {len(src.trace)} traces")
                for i in range(tracecount):
                    # Print progress
                    sys.stdout.write("\rTrimming traces: %d%%" % (i / tracecount * 100))
                    sys.stdout.flush()

                    dst.header[i] = src.header[i]
                    # dst.header[i][segyio.TraceField.LagTimeA] = samples[0]
                    dst.header[i][segyio.TraceField.TRACE_SAMPLE_COUNT] = samples.size
                    dst.header[i][segyio.TraceField.DelayRecordingTime] = round(
                        samples[0]
                    )

                    dst.trace[i] = src.trace[i][first_idx:last_idx]


                # # dst.header = src.header
                # for i, header in enumerate(dst.header):
                #     sys.stdout.write(
                #         "\rUpdating headers: %d%%" % (i / tracecount * 100)
                #     )
                #     sys.stdout.flush()
                    
            del src, dst, spec
            return (time() - tic) / tracecount

    except Exception as e:
        print(f"\n\nError in file {Path(segy_file).stem}: {e}\n\n")
        return 0


def trim_segy_files(
    segy_files,
    start_time,
    end_time,
    destination=None,
    overwrite=False,
    tpt=0.0015,
    total_traces=0,
    amount_of_files=0,
):
    # Create destination folder if it doesn't exist
    if destination is None:
        destination = Path().cwd() / "TRIM"
    if not destination.exists():
        destination.mkdir()

    time_per_trace = tpt
    if not total_traces and not amount_of_files:
        print("Counting total number of traces")
        total_traces = 0
        amount_of_files = 0
        tracecounts = {}
        for segy_file in segy_files:
            try:
                with segyio.open(segy_file, ignore_geometry=True) as src:
                    total_traces += src.tracecount
                    tracecounts[Path(segy_file).stem] = src.tracecount
                    amount_of_files += 1
            except Exception as e:
                print(f"Error in file {Path(segy_file).stem}: {e}")

    print(f"Total traces: {total_traces}")
    print(f"Total files: {amount_of_files}")
    print("Initiating file trimming")
    remaining = total_traces
    for i, segy_file in enumerate(segy_files):
        if time_per_trace is None:
            time_per_trace = tpt
        remaining -= i * total_traces / amount_of_files
        print(f"\n\nProcessing file: {Path(segy_file).stem}")
        print(
            f"Trimming files: {i / amount_of_files * 100:.2f}% ETA: {datetime.timedelta(seconds=(time_per_trace * remaining))}"
        )
        time_per_trace = trim_segy(
            segy_file, start_time, end_time, destination, overwrite
        )


if __name__ == "__main__":
    # import os
    # folder = Path(
    #     r"P:\2023\02\20230203\Background-Others\BP_EnBW_AzureStorageExplorer\Morven_SEGY_UHR_twt"
    # )
    folder = Path.cwd() / Path('..', '..', '..') / 'Background-Others/BP_EnBW_AzureStorageExplorer/Morven_SEGY_UHR_twt'
    # Check if operating system is linux or windows
    # if os.name == "posix":
    #     folder = Path(
    #         r"/home/sjb/P/2023/02/20230203/Background-Others/BP_EnBW_AzureStorageExplorer/Morven_SEGY_UHR_twt"
    #     )

    destination = folder / "TRIM" / "test"

    segy_files = folder.glob("*.sgy")

    start_time = 82 - 2  # ms
    end_time = start_time + 88  # ms
    # for num in [
    #             # '037',
    #             '038',
    #             '050']:

    #     trim_segy(
    #         Path(
    #             fr"P:\2023\02\20230203\Background-Others\BP_EnBW_AzureStorageExplorer\Morven_SEGY_UHR_twt\BP22MVNUHR01-{num}_FULL_WVELSTATIC.sgy"
    #         ),
    #         start_time,
    #         end_time,
    #         destination,
    #         overwrite=True,
    #     )
    trim_segy_files(
        segy_files,
        start_time,
        end_time,
        destination,
        overwrite=True,
        total_traces=4412031,
        amount_of_files=180
    )
