#!/usr/bin/env python3

import click
import skyfield.api as sf
from skyfield import almanac
import yaml
import sys
import pytz
from datetime import datetime, timedelta
import math
import numpy as np


@click.command()
@click.argument("config_file", type=click.Path(dir_okay=False))
@click.argument(
    "output_file", type=click.Path(dir_okay=False, writable=True, allow_dash=True)
)
def astro_calendar(config_file, output_file):
    config = read_config_file(config_file)
    output = open_output_file(output_file)

    ts = sf.load.timescale()
    eph = sf.load(config["ephemeris"])
    tz = pytz.timezone(config["timezone"])
    year = config["year"]

    offset = sf.Topos(
        latitude_degrees=config["location"]["lat"],
        longitude_degrees=config["location"]["lon"],
        elevation_m=config["location"]["alt"],
    )
    sun = eph["sun"]
    observed = eph["earth"] + offset

    # # Note:  in this frame, the winter solstace is roughly +y, the spring equinox is roughly -x
    day_radials = calculate_day_radials(ts, sun, observed, tz, year)
    sunrises, sunsets = calculate_sunrises_sunsets(eph, ts, offset, tz, year)

    print(sunrises.utc_iso())
    print(sunsets.utc_iso())


    # times, idx = almanac.find_discrete(t0, t1, almanac.seasons(eph))
    # for i, time in zip(idx, times):
    #     print(i, almanac.SEASON_EVENTS[i], time.utc_iso(" "))
    
    output.close()


def read_config_file(config_file):
    config = {}
    with open(config_file) as f:
        config = yaml.safe_load(f)
    check_config(config)
    return config


def check_config(config):
    pass


def open_output_file(output_file):
    if output_file == "-":
        return sys.stdout
    else:
        return open(output_file, "w")


def _t_generator(ts, t, delta_t):
    start_year = t.year
    while t.year == start_year:
        yield ts.utc(t)
        t += delta_t


def calculate_day_radials(ts, observer, observed, tz, year):
    t = datetime(year, 1, 1, tzinfo=tz)
    delta_t = timedelta(days=1)
    return np.vstack([day_radial(observer, observed, t_utc) for t_utc in _t_generator(ts, t, delta_t)])


def day_radial(observer, observed, t_utc):
    pos = observer.at(t_utc).observe(observed).position.au
    return np.array([np.linalg.norm(pos), math.atan2(pos[1], pos[0])])


def calculate_sunrises_sunsets(eph, ts, offset, tz, year):
    start_day = ts.utc(datetime(year, 1, 1, tzinfo=tz))
    end_day_excl = ts.utc(datetime(year+1, 1, 1, tzinfo=tz))
    sunrise_sunset, is_sunrise = almanac.find_discrete(start_day, end_day_excl, almanac.sunrise_sunset(eph, offset))
    sunrises = sunrise_sunset[is_sunrise]
    sunsets = sunrise_sunset[~is_sunrise]
    return sunrises, sunsets


if __name__ == "__main__":
    astro_calendar()
