from __future__ import division, print_function

from ..core import utils
from . import aqdutils


def cdf_to_nc(
    cdf_filename, atmpres=False, writefile=True
):  # , format="NETCDF3_64BIT"): # don't think we need to fall back to netcdf3 any more

    # Load raw .cdf data
    ds = aqdutils.load_cdf(cdf_filename, atmpres=atmpres)

    # Clip data to in/out water times or via good_ens
    ds = utils.clip_ds(ds, wvs=True)

    # Create water_depth variables
    # ds = utils.create_water_depth(ds)
    ds = utils.create_nominal_instrument_depth(ds)

    # Create depth variable depending on orientation
    ds, T, T_orig = aqdutils.set_orientation(ds, ds["TransMatrix"].values)

    # Transform coordinates from ENU to BEAM if necessary
    if "wave_coord_output" in ds.attrs:
        histtext = "Converting from {} to {} at user request. ".format(
            ds.attrs["AQDCoordinateSystem"], ds.attrs["wave_coord_output"]
        )
        print(histtext)
        ds = utils.insert_history(ds, histtext)
        u, v, w = aqdutils.coord_transform(
            ds["VEL1"].values,
            ds["VEL2"].values,
            ds["VEL3"].values,
            ds["Heading"].values,
            ds["Pitch"].values,
            ds["Roll"].values,
            T,
            T_orig,
            ds.attrs["AQDCoordinateSystem"],
            out=ds.attrs["wave_coord_output"],
        )
        ds["VEL1"].values = u
        ds["VEL2"].values = v
        ds["VEL3"].values = w

    # Make bin_depth variable
    ds = aqdutils.make_bin_depth(ds, waves=True)

    # Swap dimensions from bindist to depth
    ds = aqdutils.swap_bindist_to_depth(ds)
    # Rename DataArrays within Dataset for EPIC compliance
    # and append depth coord to velocities and amplitudes
    ds = aqdutils.ds_rename(ds, waves=True)

    # add EPIC and CMG attributes, set _FillValue
    ds = aqdutils.ds_add_attrs(ds, waves=True)

    # Add DELTA_T for EPIC compliance
    ds = aqdutils.add_delta_t(ds, waves=True)

    # Add minimum and maximum attributes
    ds = utils.add_min_max(ds)

    # Cast vars as float32
    for var in ds.variables:
        if (var not in ds.coords) and ("time" not in var):
            # cast as float32
            ds = utils.set_var_dtype(ds, var)

    # Need to add lat lon to certain variables
    for var in ["Hdg_1215", "Ptch_1216", "Roll_1217"]:
        ds = utils.add_lat_lon(ds, var)

    # Ensure no _FillValue is assigned to coordinates
    ds = utils.ds_coord_no_fillvalue(ds)

    if writefile:
        nc_filename = ds.attrs["filename"] + "wvsb-cal.nc"
        ds.to_netcdf(nc_filename)
        # Rename time variables for EPIC compliance, keeping a time_cf
        # coorindate.
        utils.rename_time_2d(nc_filename, ds)

        print("Done writing netCDF file", nc_filename)

    return ds
