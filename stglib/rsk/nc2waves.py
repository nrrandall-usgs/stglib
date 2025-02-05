from __future__ import division, print_function

from ..core import utils, waves


def nc_to_waves(nc_filename):

    ds = utils.open_time_2d_dataset(nc_filename)  # this will deal with a cf file, too

    if utils.is_cf(ds):
        pass
    else:
        ds = utils.epic_to_cf_time(ds)

        ds = utils.create_epic_times(ds)

    spec = waves.make_waves_ds(ds)

    for k in ["wp_peak", "wh_4061", "wp_4060", "pspec"]:
        ds[k] = spec[k]

    # ds = utils.create_water_depth(ds)

    ds = utils.create_water_depth_var(ds)

    for k in ["P_1", "P_1ac", "sample", "T_28"]:
        if k in ds:
            ds = ds.drop_vars(k)

    ds = utils.trim_max_wp(ds)

    ds = utils.trim_min_wh(ds)

    ds = utils.trim_max_wh(ds)

    ds = utils.trim_wp_ratio(ds)

    # Add attrs
    ds = utils.ds_add_attrs(ds)

    # Reshape and associate dimensions with lat/lon
    if not utils.is_cf:
        for var in ["wp_peak", "wh_4061", "wp_4060", "pspec", "water_depth"]:
            if var in ds:
                ds = utils.add_lat_lon(ds, var)

    # assign min/max (need to do this after trimming):
    ds = utils.add_min_max(ds)

    nc_filename = ds.attrs["filename"] + "s-a.nc"

    ds = utils.rename_time(ds)

    for var in ds.data_vars:
        if "time" not in var:
            # cast as float32
            ds = utils.set_var_dtype(ds, var)

    ds.to_netcdf(nc_filename, unlimited_dims=["time"])

    return ds
