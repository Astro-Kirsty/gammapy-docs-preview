"""
Estimation of time variability in a lightcurve
==============================================
Compute a series of time variability significance estimators for a lightcurve.

Prerequisites
-------------

Understanding the light curve estimator, please refer to the :doc:`light curve notebook </tutorials/analysis-time/light_curve`.
For more in-depth explanation on the creation of smaller observations for exploring time variability, refer to :doc:`light curve notebook </tutorials/analysis-time/light_curve_flare`

Context
-------
Frequently, after computing a lightcurve, we need to quantify its variability in the time domain, for example in the case of a flare, burst, decaying light curve in GRBs or heightened activity in general.

There are many ways to define the significance of the variability.

**Objective: Estimate the level time variability in a lightcurve through different methods.**

Proposed approach
-------------
We will start by reading the pre-computed light curve for PKS 2155-304 that is stored in `$GAMMAPY_DATA` 
To learn how to compute such an object, see the :doc:`light curve tutorial </tutorials/analysis-time/light_curve_flare`

This tutorial will demonstrate how to compute different estimates which measure the significance of variability. These estimators range from basic ones that calculate the peak-to-trough variation, to more complex ones like fractional excess and point-to-point fractional variance, which consider the entire light curve. We also show an approach which utilises the change points inn Bayesian blocks as indicators of variability.
"""
######################################################################
# Setup
# -----
# As usual, we’ll start with some general imports…


import numpy as np
from astropy.stats import bayesian_blocks
import matplotlib.pyplot as plt
from gammapy.estimators import FluxPoints
from gammapy.estimators.utils import (
    compute_lightcurve_doublingtime,
    compute_lightcurve_fpp,
    compute_lightcurve_fvar,
)

######################################################################
# Load the light curve for the PKS 2155-304 flare directly from “$GAMMAPY_DATA/estimators”

lc_1d = FluxPoints.read(
    "$GAMMAPY_DATA/estimators/pks2155_hess_lc/pks2155_hess_lc.fits", format="lightcurve"
)

plt.figure(figsize=(8, 6))
lc_1d.plot(marker="o")
plt.show()

######################################################################
# Methods to characterize variability
# -----------------------------------
#  Amplitude maximum variation, relative variability amplitude and variability amplitude
#
# The amplitude maximum variation is the simplest method to define variability (as described in
# [Boller et al., 2016](https://ui.adsabs.harvard.edu/abs/2016A&A...588A.103B/abstract)) as it just computes
# the level of tension between the lowest and highest measured fluxes in the lightcurve.
# This estimator requires fully Gaussian errors.

flux = lc_1d.flux.quantity
flux_err = lc_1d.flux_err.quantity

f_mean = np.mean(flux)
f_mean_err = np.mean(flux_err)

f_max = flux.max()
f_max_err = flux_err[flux.argmax()]
f_min = flux.min()
f_min_err = flux_err[flux.argmin()]

amplitude_maximum_variation = (f_max - f_max_err) - (f_min + f_min_err)

amplitude_maximum_significance = amplitude_maximum_variation / np.sqrt(
    f_max_err**2 + f_min_err**2
)

print(amplitude_maximum_significance)

######################################################################
# There are other methods based on the peak-to-trough difference to assess the variability in a lightcurve.
# Here we present as example the relative variability amplitude as presented in [Kovalev et al., 2004]
# (https://iopscience.iop.org/article/10.1086/497430):

relative_variability_amplitude = (f_max - f_min) / (f_max + f_min)

relative_variability_error = (
    2
    * np.sqrt((f_max * f_min_err) ** 2 + (f_min * f_max_err) ** 2)
    / (f_max + f_min) ** 2
)

relative_variability_significance = (
    relative_variability_amplitude / relative_variability_error
)

print(relative_variability_significance)

######################################################################
# And the variability amplitude as presented in [Heidt & Wagner, 1996](https://ui.adsabs.harvard.edu/abs/1996A%26A...305...42H/abstract):

variability_amplitude = np.sqrt((f_max - f_min) ** 2 - 2 * f_mean_err**2)

variability_amplitude_100 = 100 * variability_amplitude / f_mean

variability_amplitude_error = (
    100
    * ((f_max - f_min) / (f_mean * variability_amplitude_100 / 100))
    * np.sqrt(
        (f_max_err / f_mean) ** 2
        + (f_min_err / f_mean) ** 2
        + ((np.std(flux, ddof=1) / np.sqrt(len(flux))) / (f_max - f_mean)) ** 2
        * (variability_amplitude_100 / 100) ** 4
    )
)

variability_amplitude_significance = (
    variability_amplitude_100 / variability_amplitude_error
)

print(variability_amplitude_significance)

######################################################################
#  Fractional excess variance, point-to-point fractional variance and doubling/halving time
# -----------------------------------------------------------------------------------------
# The fractional excess variance as presented by
# [Vaughan et al., 2003](https://ui.adsabs.harvard.edu/abs/2003MNRAS.345.1271V/abstract)) is a simple but effective
# method to assess the significance of a time variability feature in an object, for example an AGN flare.
# It is important to note that it requires Gaussian errors to be applicable.
# The excess variance computation is implemented in `~gammapy.estimators.utils`.

fvar_table = compute_lightcurve_fvar(lc_1d)
print(fvar_table)

######################################################################
# A similar estimator is the point-to-point fractional variance, as defined by
# [Edelson et al., 2002](https://ui.adsabs.harvard.edu/abs/2002ApJ...568..610E/abstract)
# which samples the lightcurve on smaller time granularity.
# In general, the point-to-point fractional variance being higher than the fractional excess variance is indicative
# of the presence of very short timescale variability.

fpp_table = compute_lightcurve_fpp(lc_1d)
print(fpp_table)

######################################################################
# The characteristic doubling and halving time, as introduced by
# [Brown, 2013](https://durham-repository.worktribe.com/output/1478453/) of the light curve can also be computed.
# This provides information on the shape of the variability feature, in particular how quickly it rises and falls.

dtime_table = compute_lightcurve_doublingtime(lc_1d, flux_quantity="flux")
print(dtime_table)

######################################################################
# Bayesian blocks
# ---------------
# The presence of temporal variability in a lightcurve can be assessed by using bayesian blocks ([reference
# paper](https://ui.adsabs.harvard.edu/abs/2013ApJ...764..167S/abstract)). A good and simple-to-use implementation of the algorithm is found in `astropy.stats`([documentation](https://docs.astropy.org/en/stable/api/astropy.stats.bayesian_blocks.html)). This implementation uses Gaussian statistics, as opposed to the [first introductory paper](https://iopscience.iop.org/article/10.1086/306064) which was based on Poissonian statistics.
#
# By passing the flux and error on the flux as `measures` to the method we can obtain the list of optimal bin edges defined by the bayesian blocks algorithm.

time = lc_1d.geom.axes["time"].time_mid.mjd

bayesian_edges = bayesian_blocks(
    t=time, x=flux.flatten(), sigma=flux_err.flatten(), fitness="measures"
)

######################################################################
# We can visualize the difference between the original lightcurve and the rebin with bayesian blocks

bayesian_flux = []
for tmin, tmax in zip(bayesian_edges[:-1], bayesian_edges[1:]):
    mask = (time >= tmin) & (time <= tmax)
    bayesian_flux.append(
        np.average(
            flux.flatten()[mask], weights=1 / (flux_err.flatten()[mask] ** 2)
        ).value
    )

xerr = np.diff(bayesian_edges) / 2
bayesian_x = bayesian_edges[:-1] + xerr

fig, ax = plt.subplots(
    figsize=(8, 6),
    gridspec_kw={"left": 0.16, "bottom": 0.2, "top": 0.98, "right": 0.98},
)
plt.plot(time, flux.flatten(), marker="+", linestyle="", color="teal")
plt.errorbar(
    bayesian_x,
    bayesian_flux,
    xerr=np.diff(bayesian_edges) / 2,
    linestyle="",
    color="orange",
)
plt.ylim(bottom=0)
plt.show()

######################################################################
# The result giving a significance estimation for variability in the lightcurve is the number of *change points*, i.e. the number of internal bin edges: if at least one change point is identified by the algorithm, there is significant variability.

ncp = len(bayesian_edges) - 2
print(ncp)
