import numpy as np
from ..io import rows_to_bytes


def export_plane(zone, fname=None):

    num_x, num_y = zone.geometry.num_x, zone.geometry.num_y  # tmp

    values = zone.get_values()
    if values is None:
        vals = [[-1] * num_y for _ in range(num_x)]
    elif values.shape == (num_x, num_y):
        vals = values
    elif hasattr(zone.geometry, "values_to_grid"):
        # Non-rectangular (polygon) zone: values only cover in-polygon
        # points. Map them onto the full grid, filling outside-polygon
        # points with NaN (matches the plotting code's convention).
        vals = zone.geometry.values_to_grid(values)
    else:
        vals = [[-1] * num_y for _ in range(num_x)]

    # Use the full (unmasked) coordinate grid for axis labels / z-values --
    # zone.geometry.coords only contains in-polygon points for non-rectangular
    # zones, which doesn't reshape to (num_x, num_y).
    coords = getattr(zone.geometry, "full_coords", zone.geometry.coords)
    zvals = coords.T[2].reshape(num_x, num_y).T[::-1]

    xpoints = coords.T[0].reshape(num_x, num_y).T[0].tolist()
    ypoints = coords.T[1].reshape(num_x, num_y)[0].tolist()

    if len(np.unique(xpoints)) == 1 and len(np.unique(ypoints)) == 1:
        xpoints = coords.T[0].reshape(num_x, num_y)[0].tolist()
        ypoints = coords.T[1].reshape(num_x, num_y).T[0].tolist()
        vals = np.array(vals).T.tolist()
        zvals = zvals.T.tolist()

    rows = [[""] + xpoints]

    rows += np.concatenate(([np.flip(ypoints)], vals)).T.tolist()
    rows += [""]
    # zvals

    rows += [[""] + list(line) for line in zvals]
    return to_csv(rows=rows, fname=fname)


def export_volume(zone, fname=None):

    header = """Data format notes:
        
    Data consists of numZ horizontal grids of fluence rate values; each grid contains numX by numY points.

    numX; numY; numZ are given on the first line of data.
    The next line contains numX values; indicating the X-coordinate of each grid column.
    The next line contains numY values; indicating the Y-coordinate of each grid row.
    The next line contains numZ values; indicating the Z-coordinate of each horizontal grid.
    A blank line separates the position data from the first horizontal grid of fluence rate values.
    A blank line separates each subsequent horizontal grid of fluence rate values.

    fluence rate values are given in uW/cm2
    """

    lines = header.split("\n")
    rows = [[line] for line in lines]
    rows += [zone.geometry.num_points]
    rows += [np.unique(zone.geometry.coords.T[0])]
    rows += [np.unique(zone.geometry.coords.T[1])]
    rows += [np.unique(zone.geometry.coords.T[2])]
    values = zone.get_values()
    for i in range(zone.geometry.num_z):
        rows += [""]
        if values is None:
            rows += [[""] * zone.geometry.num_x for _ in range(zone.geometry.num_y)]
        elif values.shape != (
            zone.geometry.num_x,
            zone.geometry.num_y,
            zone.geometry.num_z,
        ):
            rows += [[""] * zone.geometry.num_x for _ in range(zone.geometry.num_y)]
        else:
            rows += values.T[i].tolist()

    return to_csv(rows=rows, fname=fname)


def export_point(zone, fname=None):
    pos = zone.geometry.position
    aim = zone.geometry.aim_point
    normal = zone.geometry.normal_direction
    values = zone.get_values()
    val = "" if values is None else values.flat[0]
    rows = [
        ["Zone ID", zone.zone_id],
        ["Name", zone.name],
        ["Position", *pos],
        ["Aim Point", *aim],
        ["Normal", *normal],
        ["Value", val],
        ["Units", zone.value_units],
    ]
    return to_csv(rows=rows, fname=fname)


def to_csv(rows, fname=None):

    # rows = zone._write_rows()  # implemented in subclass
    csv_bytes = rows_to_bytes(rows)

    if fname is not None:
        with open(fname, "wb") as csvfile:
            csvfile.write(csv_bytes)
    return csv_bytes
