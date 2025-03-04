# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved

from __future__ import annotations

import copy
from typing import Any, Optional, Tuple, Union

import numpy as np
import numpy.typing as npt
from scipy.signal import butter

from acconeer.exptool import a121


ENVELOPE_FWHM_M = {
    a121.Profile.PROFILE_1: 0.04,
    a121.Profile.PROFILE_2: 0.07,
    a121.Profile.PROFILE_3: 0.14,
    a121.Profile.PROFILE_4: 0.19,
    a121.Profile.PROFILE_5: 0.32,
}
APPROX_BASE_STEP_LENGTH_M = 2.5e-3
# Parameter of signal temperature model.
SIGNAL_TEMPERATURE_MODEL_PARAMETER = {
    a121.Profile.PROFILE_1: 67.0,
    a121.Profile.PROFILE_2: 85.0,
    a121.Profile.PROFILE_3: 86.0,
    a121.Profile.PROFILE_4: 99.0,
    a121.Profile.PROFILE_5: 104.0,
}
# Largest measurable distance per PRF.
MAX_MEASURABLE_DIST_M = {prf: prf.mmd for prf in set(a121.PRF)}
# Slope and interception of linear noise temperature model.
NOISE_TEMPERATURE_MODEL_PARAMETER = [-0.00275, 0.98536]

SPEED_OF_LIGHT = 299792458
RADIO_FREQUENCY = 60.5e9
WAVELENGTH = SPEED_OF_LIGHT / RADIO_FREQUENCY
PERCEIVED_WAVELENGTH = WAVELENGTH / 2

MEAN_ABS_DEV_OUTLIER_TH = 5


def get_distances_m(
    config: Union[a121.SensorConfig, a121.SubsweepConfig], metadata: a121.Metadata
) -> Tuple[npt.NDArray[np.float_], float]:
    points = np.arange(config.num_points) * config.step_length + config.start_point
    distances_m = points * metadata.base_step_length_m
    step_length_m = config.step_length * metadata.base_step_length_m
    return distances_m, step_length_m


def get_approx_fft_vels(
    metadata: a121.Metadata, config: a121.SensorConfig
) -> Tuple[npt.NDArray[np.float_], float]:
    if config.sweep_rate is not None:
        sweep_rate = config.sweep_rate
    else:
        sweep_rate = metadata.max_sweep_rate

    spf = config.sweeps_per_frame
    f_res = 1 / spf
    freqs = np.fft.fftshift(np.fft.fftfreq(spf))
    f_to_v = 2.5e-3 * sweep_rate
    return freqs * f_to_v, f_res * f_to_v


def interpolate_peaks(
    abs_sweep: npt.NDArray[np.float_],
    peak_idxs: list[int],
    start_point: int,
    step_length: int,
    step_length_m: float,
) -> Tuple[list[float], list[float]]:
    """Quadratic interpolation around a peak using the amplitudes of the peak and its two
    neghbouring points.

    Derivation:
    https://math.stackexchange.com/questions/680646/get-polynomial-function-from-3-points

    :param abs_sweep: Absolute value of mean sweep.
    :param peak_idxs: List containing indexes of identified peaks.
    :param start_point: Start point.
    :param step_length: Step length in points.
    :param step_length_m: Step length in meters.
    """
    estimated_distances = []
    estimated_amplitudes = []
    for peak_idx in peak_idxs:
        x = np.arange(peak_idx - 1, peak_idx + 2, 1)
        y = abs_sweep[peak_idx - 1 : peak_idx + 2]
        a = (x[0] * (y[2] - y[1]) + x[1] * (y[0] - y[2]) + x[2] * (y[1] - y[0])) / (
            (x[0] - x[1]) * (x[0] - x[2]) * (x[1] - x[2])
        )
        b = (y[1] - y[0]) / (x[1] - x[0]) - a * (x[0] + x[1])
        c = y[0] - a * x[0] ** 2 - b * x[0]
        peak_loc = -b / (2 * a)
        estimated_distances.append((start_point + peak_loc * step_length) * step_length_m)
        estimated_amplitudes.append(a * peak_loc**2 + b * peak_loc + c)
    return estimated_distances, estimated_amplitudes


def find_peaks(abs_sweep: npt.NDArray[np.float_], threshold: npt.NDArray[np.float_]) -> list[int]:
    """Identifies peaks above threshold.

    A peak is defined as a point with greater value than its two neighbouring points and all
    three points are above the threshold.

    :param abs_sweep: Absolute value of mean sweep.
    :param threshold: Array of values, defining the threshold throughout the sweep.
    """
    if threshold is None:
        raise ValueError
    found_peaks = []
    d = 1
    N = len(abs_sweep)
    while d < (N - 1):
        if np.isnan(threshold[d - 1]):
            d += 1
            continue
        if np.isnan(threshold[d + 1]):
            break
        if abs_sweep[d] <= threshold[d]:
            d += 2
            continue
        if abs_sweep[d - 1] <= threshold[d - 1]:
            d += 1
            continue
        if abs_sweep[d - 1] >= abs_sweep[d]:
            d += 1
            continue
        d_upper = d + 1
        while True:
            if (d_upper) >= (N - 1):
                break
            if np.isnan(threshold[d_upper]):
                break
            if abs_sweep[d_upper] <= threshold[d_upper]:
                break
            if abs_sweep[d_upper] > abs_sweep[d]:
                break
            elif abs_sweep[d_upper] < abs_sweep[d]:
                found_peaks.append(int(np.argmax(abs_sweep[d:d_upper]) + d))
                break
            else:
                d_upper += 1
        d = d_upper
    return found_peaks


def get_temperature_adjustment_factors(
    temperature_diff: int, profile: a121.Profile
) -> Tuple[float, float]:
    """Calculate temperature compensation for mean sweep and background noise(tx off) standard
    deviation.

    The signal adjustment model is follows 2 ** (temperature_diff / model_parameter), where
    model_parameter reflects the temperature difference relative the reference temperature,
    required for the amplitude to double/halve.

    The noise adjustment is a linear function of the temperature difference, calibrated using
    noise-normalized data, generalizing to different sensor configurations.
    """
    signal_adjustment_factor = 2 ** (
        temperature_diff / SIGNAL_TEMPERATURE_MODEL_PARAMETER[profile]
    )
    noise_adjustment_factor = (
        NOISE_TEMPERATURE_MODEL_PARAMETER[0] * temperature_diff
        + NOISE_TEMPERATURE_MODEL_PARAMETER[1]
    )
    return (signal_adjustment_factor, noise_adjustment_factor)


def get_distance_filter_coeffs(profile: a121.Profile, step_length: int) -> Any:
    """Calculates the iir coefficients corresponding to a matched filter, based on the profile and
    the step length.
    """
    wnc = APPROX_BASE_STEP_LENGTH_M * step_length / (ENVELOPE_FWHM_M[profile])
    return butter(N=2, Wn=wnc)


def get_distance_filter_edge_margin(profile: a121.Profile, step_length: int) -> int:
    """Calculates the number of points required for filter initialization when performing
    distance filtering, using the filter coefficients supplied by the function
    get_distance_filter_coeffs.
    """
    return int(_safe_ceil(ENVELOPE_FWHM_M[profile] / (APPROX_BASE_STEP_LENGTH_M * step_length)))


def double_buffering_frame_filter(_frame: npt.NDArray[Any]) -> Optional[npt.NDArray[np.complex_]]:
    """
    Detects and removes outliers in data that appear when the double buffering mode is enabled,
    and returns the filtered frame.

    The filter is applied only when there are 32 or more sweeps per frame.

    The disturbance caused by enabling the double buffering mode can appear in multiple sweeps
    but, according to observations, is limited to a maximum of two consecutive sweeps.

    Outliers are detected along the sweep dimension using the second order difference and removed
    by interpolating between the sample before and the sample two positions ahead.
    """

    (n_s, n_d) = _frame.shape
    min_num_sweeps = 32

    if n_s < min_num_sweeps:
        return None

    frame_real = _frame["real"]
    frame_imag = _frame["imag"]

    # Second order difference along sweeps
    frame_diff_real = np.zeros((n_s, n_d), dtype=np.int16)
    frame_diff_imag = np.zeros((n_s, n_d), dtype=np.int16)
    frame_diff_real[1:-1, :] = np.diff(frame_real, axis=0, n=2)
    frame_diff_imag[1:-1, :] = np.diff(frame_imag, axis=0, n=2)

    # Estimating magnitude using: abs(real) + abs(imag)
    frame_diff_abs = np.abs(frame_diff_real) + np.abs(frame_diff_imag)

    # Mean absolute deviation
    frame_diff_mad = np.sum(frame_diff_abs, axis=0) // (n_s - 2)

    # Detect outliers
    threshold = MEAN_ABS_DEV_OUTLIER_TH * frame_diff_mad
    outliers = frame_diff_abs > threshold

    # Perform filtering at each distance to remove outliers
    filtered_frame_real = frame_real.copy()
    filtered_frame_imag = frame_imag.copy()
    for d in range(n_d):
        if np.any(outliers[:, d]):
            args = np.where(outliers[:, d])[0]
            for idx in args:
                if idx <= 1:
                    # Median filtering for the first two and the last two sweeps
                    filtered_frame_real[idx, d] = np.median(filtered_frame_real[idx : idx + 4, d])
                    filtered_frame_imag[idx, d] = np.median(filtered_frame_imag[idx : idx + 4, d])
                elif idx >= n_s - 2:
                    filtered_frame_real[idx, d] = np.median(filtered_frame_real[idx - 3 : idx, d])
                    filtered_frame_imag[idx, d] = np.median(filtered_frame_imag[idx - 3 : idx, d])
                else:
                    # Interpolation for the remaining sweeps
                    filtered_frame_real[idx, d] = int(
                        (
                            2 * filtered_frame_real[max(idx - 1, 0), d]
                            + filtered_frame_real[min(idx + 2, n_s - 1), d]
                        )
                        / 3
                    )
                    filtered_frame_imag[idx, d] = int(
                        (
                            2 * filtered_frame_imag[max(idx - 1, 0), d]
                            + filtered_frame_imag[min(idx + 2, n_s - 1), d]
                        )
                        / 3
                    )

    filtered_frame = np.empty((n_s, n_d), dtype=np.complex_)
    filtered_frame.real = filtered_frame_real
    filtered_frame.imag = filtered_frame_imag

    return filtered_frame


def select_prf(breakpoint: int, profile: a121.Profile) -> a121.PRF:
    """Calculates the highest possible PRF for the given breakpoint.

    :param breakpoint: Distance in the unit of points.
    :param profile: Profile.
    """
    max_meas_dist_m = copy.copy(MAX_MEASURABLE_DIST_M)

    if a121.PRF.PRF_19_5_MHz in max_meas_dist_m and profile != a121.Profile.PROFILE_1:
        del max_meas_dist_m[a121.PRF.PRF_19_5_MHz]

    breakpoint_m = breakpoint * APPROX_BASE_STEP_LENGTH_M
    viable_prfs = [prf for prf, max_dist_m in max_meas_dist_m.items() if breakpoint_m < max_dist_m]
    return sorted(viable_prfs, key=lambda prf: prf.frequency)[-1]


def estimate_frame_rate(client: a121.Client, session_config: a121.SessionConfig) -> float:
    """
    Performs a measurement of the actual frame rate obtained by the configuration.
    This is hardware dependent. Hence the solution using a measurement.

    If a recorder is attached to the client,
    this call will result in a new session being run and recorded!
    """

    delta_times = np.full(2, np.nan)

    client.setup_session(session_config)
    client.start_session()

    for i in range(4):
        result = client.get_next()
        assert isinstance(result, a121.Result)

        if i < 2:
            # Ignore first read, it is sometimes inaccurate
            last_time = result.tick_time
            continue

        time = result.tick_time
        delta = time - last_time
        last_time = time
        delta_times = np.roll(delta_times, -1)
        delta_times[-1] = delta

    client.stop_session()

    return float(1.0 / np.nanmean(delta_times))


def exponential_smoothing_coefficient(fs: float, time_constant: float) -> float:
    """Calculate the exponential smoothing coefficient.

    Typical usage:

    y = y * coeff + x * (1 - coeff)

    :param fs: Sampling frequency.
    :param time_constant: Time constant.
    """
    dt = 1 / fs
    return float(np.exp(-dt / time_constant))


def _safe_ceil(x: float) -> float:
    """Perform safe ceil.

    Implementation of ceil function, compatible with float representation in C.
    """
    return float(f"{x:.16g}")
