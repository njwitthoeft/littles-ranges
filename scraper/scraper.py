from bs4 import BeautifulSoup

import requests
import zipfile
import io
import geopandas as gpd
from tqdm import tqdm

root = "https://www.fs.fed.us/nrs/atlas/littlefia/"

# use beautiful soup to get a list of files to download with species names
page = BeautifulSoup(requests.get(root + "species_table.html").text, "html.parser")
rows = page.find("div", id = "cns").table.find_all("tr")[1:]

specieslist = list()


#make a list of downloads to grab
for row in rows:
    species_entry = row.find_all("td")
    species_suffix = species_entry[0].find_all("a")[-1].get("href")
    shape_url = root + species_suffix
    binomial = species_entry[2].a.text
    specieslist.append((binomial, shape_url))

## these are in a arcgis defined arbitrary projection, but this proj4 string can fix this
little_proj = "+proj=aea +lat_0=40 +lon_0=-82 +lat_1=38 +lat_2=42 +x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"

# iterate through shapefiles, downloading to a temporary file, then finally saving as a well-named geojson
for i in tqdm(range(0,len(specieslist)), 'Downloading', unit = ' Shapefiles'):
  url = specieslist[i][1]
  name = "".join(i if i.isalnum() else '_' for i in specieslist[i][0])
  local_path = 'tmp/'
  r = requests.get(url)
  try:
    z = zipfile.ZipFile(io.BytesIO(r.content))
  except Exception:
    pass
  try:
    z.extractall(path=local_path) # extract to folder
  except Exception:
    pass
  filenames = [y for y in sorted(z.namelist()) for ending in ['dbf', 'prj', 'shp', 'shx'] if y.endswith(ending)] 
  dbf, shp, shx = [filename for filename in filenames]
  gpd.read_file(local_path + shp).set_crs(little_proj).to_crs(epsg = 4326).to_file(f"../data/{name}.geojson", driver = 'GeoJSON')