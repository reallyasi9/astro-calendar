#!/usr/bin/env python3

import click
import skyfield.api as sf
from skyfield import almanac
import yaml
import sys
import pytz
from datetime import datetime


@click.command()
@click.argument("config_file", type=click.Path(dir_okay=False))
@click.argument(
    "output_file", type=click.Path(dir_okay=False, writable=True, allow_dash=True)
)
def astro_calendar(config_file, output_file):
    config = read_config_file(config_file)
    output = open_output_file(output_file)

    ts = sf.load.timescale()
    eph = sf.load("de435.bsp")

    timezone = pytz.timezone(config["timezone"])
    t0 = ts.utc(datetime(2018, 12, 21, tzinfo=timezone))
    t1 = ts.utc(datetime(2019, 6, 21, tzinfo=timezone))

    times, idx = almanac.find_discrete(t0, t1, almanac.seasons(eph))
    for i, time in zip(idx, times):
        print(i, almanac.SEASON_EVENTS[i], time.utc_iso(" "))

    sun = eph["sun"]
    earth = eph["earth"]
    boston = earth + sf.Topos(
        latitude_degrees=config["location"]["lat"],
        longitude_degrees=config["location"]["lon"],
        elevation_m=config["location"]["alt"],
    )
    # heliocentric = sun.at(t0).observe(boston)
    # Note:  in this frame, the winter solstace is roughly +y, the spring equinox is roughly -x
    print(sun.at(t0).observe(boston).position.au)
    print(sun.at(t1).observe(boston).position.au)

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


if __name__ == "__main__":
    astro_calendar()
