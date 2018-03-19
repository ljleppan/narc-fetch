# Copyright 2018, Leo Leppänen <leppanen.leo@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation 
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and 
# to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO 
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, 
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from bs4 import BeautifulSoup
import requests
import re
import time
import os
import argparse
import logging


SERIE_URL_PREFIX = 'http://www.narc.fi:8080/VakkaWWW/Selaus.action?kuvailuTaso=SARJA&avain='
SERIE_ITEM_URL_PREFIX = 'http://digi.narc.fi/digi/hae_ay.ka?ay='
ITEM_URL_PREFIX = 'http://digi.narc.fi/digi/slistaus.ka?ay='
IMAGE_URL_PREFIX = 'http://digi.narc.fi/digi/fetch_hqjpg.ka?kuid='

ITEM_LINK_REGEXP = re.compile('Selaus\.action;jsessionid=\w+\?kuvailuTaso=AY&avain=([\w\.]+)')
SECTION_LINK_REGEXP = re.compile('view\.ka\?kuid=(\d+)')

def fetch_item_identifiers(serie_identifier):
    serie_url = SERIE_URL_PREFIX + serie_identifier
    print('Fetching serie {} from url {}'.format(serie_identifier, serie_url))

    req = requests.get(serie_url)

    if req.status_code != 200:
        print('ERROR: Failed to fetch serie index, unexpected status code {}'.format(req.status_code))
        return

    html = BeautifulSoup(req.text, 'html.parser')
    item_links = html.find_all('a', href=ITEM_LINK_REGEXP)
    item_identifiers = [match.group(1) for match in (ITEM_LINK_REGEXP.match(link['href']) for link in item_links) if match]
    print('Found {} items'.format(len(item_identifiers)))
    return item_identifiers


def fetch_section_identifiers(item_identifier):
    if '.' in item_identifier:
        # This is a item identifier fetched from a serie listing, we need to resolve it to a fully numeric format
        item_url = SERIE_ITEM_URL_PREFIX + item_identifier
    else:
        item_url = ITEM_URL_PREFIX + item_identifier
    print('Fetching item {} from url {}'.format(item_identifier, item_url))

    req = requests.get(item_url)

    if req.status_code != 200:
        print('ERROR: Failed to fetch item index, unexpected status code {}'.format(req.status_code))
        return

    html = BeautifulSoup(req.text, 'html.parser')
    section_links = html.find_all(href=SECTION_LINK_REGEXP)
    section_identifiers = [match.group(1) for match in (SECTION_LINK_REGEXP.match(link['href']) for link in section_links) if match]
    print('Found {} sections'.format(len(section_identifiers)))
    return section_identifiers


def download_and_store_section_as_image(section_identifier, directory, filename=None, overwrite=False):
    if not filename:
        filename = section_identifier + '.jpg'
    else:
        filename = str(filename) + '.jpg'
    target_file = os.path.join(directory, filename)

    # Don't bother downloading if file exists and we are not allowed to overwrite
    if os.path.exists(target_file) and not overwrite:
        print('Skipping existing file {}'.format(target_file))
        return False

    url = IMAGE_URL_PREFIX + section_identifier
    req = requests.get(url)
    if req.status_code != 200:
        print('ERROR: Failed to fetch section {}, unexpected status code {}'.format(section_identifier, req.status_code))

    
    mode = 'wb' if overwrite else 'xb'
    with open(target_file, mode) as target_file_handle:
        try:
            target_file_handle.write(req.content)
            print('Stored section {} as {}'.format(section_identifier, target_file))
        except Exception as ex:
            print('ERROR: Failed to store section {} on disk as {}'.format(section_identifier, target_file))
    return True


def identifier_as_path(identifier):
    return identifier.replace('.', '')


def ensure_path_exists(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception:
            print('ERROR: Failed to create directory {}'.format(path))


def run():
    parser = argparse.ArgumentParser(description='Download image data from the Digital Archive of the Finnish National Archive.')
    download = parser.add_argument_group('Download resources', 'Use these flags to control what resources are downloaded. At least one must be present.')
    download.add_argument(
        '-x', '--section',
        dest = 'sections',
        action = 'append',
        metavar = 'ID',
        help = 'Specify a section to download. Can be repeated and combined with other flags to download multiple resources.'
    )
    download.add_argument(
        '-i', '--item',
        dest = 'items',
        action = 'append',
        metavar = 'ID',
        help = 'Specify an item to download. Can be repeated and combined with other flags to download multiple resources.'
    )
    download.add_argument(
        '-s', '--serie',
        dest = 'series',
        action = 'append',
        metavar = 'ID',
        help = 'Specify a serie to download. Can be repeated and combined with other flags to download multiple resources.'
    )
    additional = parser.add_argument_group('Additional flags', 'Used to excert fine-grained control over program behavior.')
    additional.add_argument(
        '-q', '--quiet',
        action = 'store_true',
        help = 'Supress all output.'
    )
    additional.add_argument(
        '--identifiers-as-names',
        action = 'store_true',
        help = 'Use section identifiers rather than running numbers (i.e. page numbers) as file names. Only usable if type is serie or item.'
    )
    additional.add_argument(
        '-d', '--output-dir',
        metavar = 'DIR',
        default = os.getcwd(),
        help = 'Defines the parent directory to which the image files should be downloaded. Defaults to current working directory.'
    )
    additional.add_argument(
        '-o', '--overwrite',
        action = 'store_true',
        help = 'Overwrite existing files.' 
    )
    additional.add_argument(
        '-w', '--wait',
        type = float,
        metavar = 'SECONDS',
        default = 0.5,
        help = 'How many seconds to wait between downloads.'
    )
    args = parser.parse_args()


    # Disable printing if -q or --quiet is set
    global print
    print = logging.info
    logging.basicConfig(level=logging.WARNING if args.quiet else logging.INFO,format="%(message)s")

    if not args.sections and not args.items and not args.series:
        print('ERROR: Must specify at least one section, item or serie. See run with --help to see help.')
        exit(1)

    if args.series:
        for serie_identifier in args.series:
            item_identifiers = fetch_item_identifiers(serie_identifier)
            for item_identifier in item_identifiers:
                section_identifiers = fetch_section_identifiers(item_identifier)
                path = os.path.join(
                    os.path.abspath(args.output_dir), 
                    identifier_as_path(serie_identifier), 
                    identifier_as_path(item_identifier), 
                    ''
                )
                ensure_path_exists(path)
                for n, section_identifier in enumerate(section_identifiers):
                    filename = section_identifier if args.identifiers_as_names else str(n + 1).zfill(len(str(len(section_identifiers))))
                    downloaded_something = download_and_store_section_as_image(section_identifier, path, filename, overwrite=args.overwrite)
                    if downloaded_something: 
                        time.sleep(args.wait)

    if args.items:
        for item_identifier in args.items:
            section_identifiers = fetch_section_identifiers(item_identifier)
            path = os.path.join(
                os.path.abspath(args.output_dir),
                identifier_as_path(item_identifier), 
                ''
            )
            ensure_path_exists(path)
            for n, section_identifier in enumerate(section_identifiers):
                filename = section_identifier if args.identifiers_as_names else str(n + 1).zfill(len(str(len(section_identifiers))))
                downloaded_something = download_and_store_section_as_image(section_identifier, path, filename, overwrite=args.overwrite)
                if downloaded_something:
                    time.sleep(args.wait)

    if args.sections:
        for section_identifier in args.sections:
            path = os.path.abspath(args.output_dir)
            ensure_path_exists(path)
            downloaded_something = download_and_store_section_as_image(section_identifier, path, section_identifier, overwrite=args.overwrite)
            if downloaded_something:
                time.sleep(args.wait)

if __name__ == "__main__":
    run()