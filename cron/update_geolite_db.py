#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import sys
import os
from configlib import getConfig, OptionParser

import urllib.request
import urllib.error
import urllib.parse
import tempfile
import tarfile

from mozdef_util.geo_ip import GeoIP
from mozdef_util.utilities.logger import logger, initLogger


def fetch_db_data(db_download_location):
    logger.debug('Fetching db data from ' + db_download_location)
    response = urllib.request.urlopen(db_download_location)
    db_raw_data = response.read()
    with tempfile.NamedTemporaryFile(mode='wb') as temp:
        logger.debug('Writing compressed gzip to temp file: ' + temp.name)
        temp.write(db_raw_data)
        temp.flush()
        logger.debug('Extracting gzip data from ' + temp.name)
        tar = tarfile.open(temp.name)
        for tarinfo in tar:
            if tarinfo.name.endswith('GeoLite2-City.mmdb'):
                extracted_file = tar.extractfile(tarinfo.name)
                return extracted_file.read()


def save_db_data(save_path, db_data):
    temp_save_path = save_path + ".tmp"
    logger.debug("Saving db data to " + temp_save_path)
    with open(temp_save_path, "wb+") as text_file:
        text_file.write(db_data)
    logger.debug("Testing temp geolite db file")
    geo_ip = GeoIP(temp_save_path)
    # Do a generic lookup to verify we don't get any errors (malformed data)
    geo_ip.lookup_ip('8.8.8.8')
    logger.debug("Moving temp file to " + save_path)
    os.rename(temp_save_path, save_path)


def main():
    logger.debug('Starting')
    logger.debug(options)
    db_data = fetch_db_data(options.db_download_location)
    save_db_data(options.db_location, db_data)


def initConfig():
    # output our log to stdout or syslog
    options.output = getConfig('output', 'stdout', options.configfile)
    options.sysloghostname = getConfig('sysloghostname', 'localhost', options.configfile)
    options.syslogport = getConfig('syslogport', 514, options.configfile)

    options.db_download_location = getConfig('db_download_location', '', options.configfile)
    options.db_location = getConfig('db_location', '', options.configfile)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option(
        "-c",
        dest='configfile',
        default=sys.argv[0].replace('.py', '.conf'),
        help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    initLogger(options)
    main()
