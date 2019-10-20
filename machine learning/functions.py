import pandas as pd
import geopandas as gpd
import folium
import os, shutil
from glob import glob
import numpy as np
import pyproj
from shapely import geometry
import matplotlib.pyplot as plt
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import cv2
from datetime import datetime
import rasterio


def get_s3_scenes():
    SCENE_LIST_PATH = "./data/external/Landsat8/scene_list.gz"
    s3_scenes = pd.read_csv(SCENE_LIST_PATH, compression='gzip')
    to_datetime = lambda x: datetime.strptime(x.split(".")[0], '%Y-%m-%d %H:%M:%S')
    s3_scenes['acquisitionDate'] = s3_scenes['acquisitionDate'].apply(to_datetime)
    return s3_scenes


def get_image(coords, date_time, band, s3_scenes):
    coords = [geometry.Point(y, x) for x, y in coords]
    multipoints = geometry.MultiPoint(coords)
    bounds = multipoints.envelope
    
    WRS_PATH = './data/external/Landsat8/WRS2_descending_0.zip'
    LANDSAT_PATH = os.path.dirname(WRS_PATH)
    wrs = gpd.GeoDataFrame.from_file('./data/external/Landsat8/wrs2/WRS2_descending.shp')
    wrs_intersection = wrs[wrs.intersects(bounds)]

    paths, rows = wrs_intersection['PATH'].values, wrs_intersection['ROW'].values
    
#     print(len(wrs_intersection))
    
    bulk_list = []

    # Iterate through paths and rows
    for path, row in zip(paths, rows):
        scenes = s3_scenes[(s3_scenes.path == path) & (s3_scenes.row == row) & 
                           (s3_scenes.cloudCover <= 5) & 
                           (s3_scenes.acquisitionDate <= date_time) & 
                           (~s3_scenes.productId.str.contains('_T2')) &
                           (~s3_scenes.productId.str.contains('_RT'))]

        if len(scenes):
            scene = scenes.sort_values('acquisitionDate').iloc[-1]

        # Add the selected scene to the bulk download list.
        bulk_list.append(scene)
        
    files = []
    file_coords = []
    
    bulk_frame = pd.concat(bulk_list, 1).T
        
    for i, row in bulk_frame.iterrows():

        # Print some the product ID
#         print('\n', 'EntityId:', row.productId, '\n')
#         print(' Checking content: ', '\n')

        # Request the html text of the download_url from the amazon server. 
        # download_url example: https://landsat-pds.s3.amazonaws.com/c1/L8/139/045/LC08_L1TP_139045_20170304_20170316_01_T1/index.html
        response = requests.get(row.download_url)

        # If the response status code is fine (200)
        if response.status_code == 200:

            # Import the html to beautiful soup
            html = BeautifulSoup(response.content, 'html.parser')

            # Create the dir where we will put this image files.
            entity_dir = os.path.join(LANDSAT_PATH, row.productId)
            os.makedirs(entity_dir, exist_ok=True)

            # Second loop: for each band of this image that we find using the html <li> tag
            for li in html.find_all('li'):

                # Get the href tag
                file = li.find_next('a').get('href')
                
                if not file.endswith("B" + str(band) + ".TIF"):
                    continue
                
                files.append(Path(entity_dir) / file)
                file_coords.append([row.min_lon, row.max_lon, row.min_lat, row.max_lat])

#                 print('  Downloading: {}'.format(file))
                if file in os.listdir(entity_dir):
                    continue

                # Download the files
                # code from: https://stackoverflow.com/a/18043472/5361345

                response = requests.get(row.download_url.replace('index.html', file), stream=True)

                with open(os.path.join(entity_dir, file), 'wb') as output:
                    shutil.copyfileobj(response.raw, output)
                del response
    
    extent_all = [[], [], [], []]

    height_mod = 1
    width_mod = 1
    
    lat_mod = 1
    lon_mod = 1

    for image_path, file_coord in zip(files, file_coords):
        image_path = str(image_path)

        with rasterio.open(image_path) as src_raster:
            extent = [src_raster.bounds[i] for i in [0, 2, 1, 3]]
            for i, ex in enumerate(extent):
                extent_all[i].append(extent[i])
            height_mod = src_raster.read(1).shape[0] / (extent[3] - extent[2])
            width_mod = src_raster.read(1).shape[1] / (extent[1] - extent[0])
            lat_mod = src_raster.read(1).shape[0] / (file_coord[3] - file_coord[2])
            lon_mod = src_raster.read(1).shape[1] / (file_coord[1] - file_coord[0])

    extent_all[0] = np.min(extent_all[0])
    extent_all[1] = np.max(extent_all[1])
    extent_all[2] = np.min(extent_all[2])
    extent_all[3] = np.max(extent_all[3])
    
    coords_all = [0, 0, 0, 0]
    
    coords_all[0] = np.min([coord[0] for coord in file_coords])
    coords_all[1] = np.max([coord[1] for coord in file_coords])
    coords_all[2] = np.min([coord[2] for coord in file_coords])
    coords_all[3] = np.max([coord[3] for coord in file_coords])
    
    bounds = bounds.bounds
    bounds = [bounds[i] for i in [0, 2, 1, 3]]
#     print(bounds)
#     bounds = [np.min(bounds[1::2]), np.max(bounds[1::2]), np.min(bounds[::2]), np.max(bounds[::2])]

    dst = np.zeros((int((extent_all[3] - extent_all[2]) * height_mod * 1.1),
                    int((extent_all[1] - extent_all[0]) * width_mod * 1.1)), np.uint16)

    for image_path, f_coords in zip(files, file_coords):
        image_path = str(image_path)

        with rasterio.open(image_path) as src_raster:
            extent = [src_raster.bounds[i] for i in [0, 2, 1, 3]]

            src = src_raster.read(1)

            startx = dst.shape[0] - int((extent[2] - extent_all[2]) * height_mod) - src.shape[0]
            starty = int((extent[0] - extent_all[0]) * width_mod)
            
            dst[startx:startx+src.shape[0], starty:starty+src.shape[1]] = \
                    src + dst[startx:startx+src.shape[0], starty:starty+src.shape[1]] * (src == 0)
    
    boxx0 = dst.shape[0] - int((bounds[3] - coords_all[2]) * lat_mod)
    boxy0 = int((bounds[0] - coords_all[0]) * lon_mod)

    boxx1 = dst.shape[0] - int((bounds[2] - coords_all[2]) * lat_mod)
    boxy1 = int((bounds[1] - coords_all[0]) * lon_mod)

    return dst[boxx0:boxx1, boxy0:boxy1]


def get_df(days):
    df = None
    for day in days:
        modis_df = pd.read_csv("data/FIRMS/c6/Global/MODIS_C6_Global_MCD14DL_NRT_2019" + str(day) + ".txt")
        viirs_df = pd.read_csv("data/FIRMS/viirs/Global/VIIRS_I_Global_VNP14IMGTDL_NRT_2019" + str(day) + ".txt")
        viirs_df['confidence'] = viirs_df['confidence'].apply(lambda x: {"low": 30, "nominal": 60, "high": 90}[x])
        viirs_df = viirs_df.drop(columns=['bright_ti4', 'scan', 'track', 'satellite', 'version', 'bright_ti5', 'daynight'])
        modis_df = modis_df.drop(columns=['brightness', 'scan', 'track', 'satellite', 'version', 'bright_t31', 'daynight'])
        if df is None:
            df = pd.concat([viirs_df, modis_df])
        else:
            df = pd.concat([df, viirs_df, modis_df])
    
#     print(len(df))
    
    date_to_day = lambda x: (datetime.strptime(x['acq_date'] + " " + x['acq_time'], '%Y-%m-%d %H:%M') -
                         datetime(1970,1,1)).total_seconds() / (3600 * 24)
    df['day'] = df.apply(date_to_day, axis=1)
    
    return df


def get_points(spacial_delta, temporal_delta, df):
    point_s = df.iloc[np.random.randint(0, len(df) - 1)]
    near_points = df[(point_s.latitude - spacial_delta <= df.latitude) &
                     (df.latitude <= point_s.latitude + spacial_delta) &
                     (point_s.longitude - spacial_delta <= df.longitude) &
                     (df.longitude <= point_s.longitude + spacial_delta) &
                     (point_s.day - temporal_delta <= df.day) &
                     (df.day <= point_s.day + temporal_delta)]
    return near_points


def get_map(points, s3_scenes):
    points.sort_values(by=['day'])
    date_time = datetime.strptime(points.iloc[0]['acq_date'] + " " + points.iloc[0]['acq_time'], '%Y-%m-%d %H:%M')
    lats = points["latitude"].values
    lons = points["longitude"].values
    
    coords = []
    coords.append([np.min(lats) - 0.001, np.min(lons) - 0.001])
    coords.append([np.max(lats) + 0.001, np.max(lons) + 0.001])
    
    b5 = get_image(coords, date_time, 5, s3_scenes)
#     b3 = get_image(coords, date_time, 3, s3_scenes)
    b4 = get_image(coords, date_time, 4, s3_scenes)
    
#     print(np.min(b3), np.average(b3), np.max(b3))
#     print(np.min(b4), np.average(b4), np.max(b4))
#     print(np.min(b5), np.average(b5), np.max(b5))
    
    false_col = np.stack(((b4 - np.min(b4)) / (np.max(b4) - np.min(b4)), 
                          (b5 - np.min(b5)) / (np.max(b5) - np.min(b5)),
                          np.zeros(b5.shape, b5.dtype)), axis=2)
    return coords, false_col


def coords_to_pos(coords, bounds, shape):
    x = (bounds[1][0] - coords[0]) / (bounds[1][0] - bounds[0][0]) * shape[0]
    y = (coords[1] - bounds[0][1]) / (bounds[1][1] - bounds[0][1]) * shape[1]
#     print(type(x), type(y), x, y)
    return int(y), int(x)


class SeriesGenerator(object):
    def __init__(self):
        self.s3_scenes = get_s3_scenes()
        start = np.random.randint(232, 283)
        self.df = get_df(list(range(start, start + 10)))
        
    def get_series(self):
        points = []
        while len(points) < 10:
            points = get_points(0.09, 10, self.df)
        bounds, false_col_map = get_map(points, self.s3_scenes)
        
        days = list(range(18100, 18200))
        
        masks = []

        for day in days:
            fil_points = points[(day <= points.day) & (points.day < day + 1)]
            if len(fil_points) == 0:
                continue
            mask = np.zeros(false_col_map.shape[:2], false_col_map.dtype)
            for p in fil_points.index:
                overlay = np.zeros(mask.shape, mask.dtype)
                cv2.circle(overlay, coords_to_pos((fil_points.loc[p].latitude, fil_points.loc[p].longitude),
                                                             bounds, false_col_map.shape), 12, 1, -1)
                alpha = fil_points.loc[p].confidence / 100
                mask += alpha * overlay
                mask = np.clip(mask, 0, 1)
            masks.append(mask)
        return false_col_map, masks
        
    def get_series_threaded(self, results):
        res = self.get_series()
        results[0] = res[0]
        results[1] = res[1]
