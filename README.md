A python script to fetch images from Digital Archive of the Finnish National Archive. Supports downloading of both individual images and larger collections.

## Requirements
- Python 3.5+
- [Requests](http://docs.python-requests.org/en/master/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

## Usage

```
usage: narc-fetch.py [-h] [-x ID] [-i ID] [-s ID] [-q]
                     [--identifiers-as-names] [-d DIR] [-o] [-w SECONDS]

Download image data from the Digital Archive of the Finnish National Archive.

optional arguments:
  -h, --help            show this help message and exit

Download resources:
  Use these flags to control what resources are downloaded. At least one
  must be present.

  -x ID, --section ID   Specify a section to download. Can be repeated and
                        combined with other flags to download multiple
                        resources.
  -i ID, --item ID      Specify an item to download. Can be repeated and
                        combined with other flags to download multiple
                        resources.
  -s ID, --serie ID     Specify a serie to download. Can be repeated and
                        combined with other flags to download multiple
                        resources.

Additional flags:
  Used to excert fine-grained control over program behavior.

  -q, --quiet           Supress all output.
  --identifiers-as-names
                        Use section identifiers rather than running numbers
                        (i.e. page numbers) as file names. Only usable if type
                        is serie or item.
  -d DIR, --output-dir DIR
                        Defines the parent directory to which the image files
                        should be downloaded. Defaults to current working
                        directory.
  -o, --overwrite       Overwrite existing files.
  -w SECONDS, --wait SECONDS
                        How many seconds to wait between downloads.
```

## Finding the ID

The online archive can be browsed via two interfaces. The ID of the resource you are browsing can always be found from the URL.

### Sections (individual images)

For <http://digi.narc.fi/digi/view.ka?kuid=59216869> the ID is `59216869`.

### Items (collections of sections)

For <http://digi.narc.fi/digi/slistaus.ka?ay=365406> the ID is `365406`.

For <http://www.narc.fi:8080/VakkaWWW/Selaus.action?kuvailuTaso=AY&avain=3737306.KA> the ID is `3737306.KA`

### Series (collections of items)

For <http://digi.narc.fi/digi/dosearch.ka?sartun=392763.KA> the ID is `392763.KA`.

For <http://www.narc.fi:8080/VakkaWWW/Selaus.action?kuvailuTaso=SARJA&avain=392763.KA> the ID is `392763.KA`

