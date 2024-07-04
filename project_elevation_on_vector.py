import geopandas as gpd
import pygeos
from shapely import LineString, Polygon, Point, segmentize, distance, ops
import rioxarray as rxr
#from rasterio.plot import plotting_extent
from pyproj import Proj, transform, CRS, Transformer
import os
import pandas as pnd
import pandas as pnd
import matplotlib.pyplot as plt
from pygam import LinearGAM, s

os.environ["PROJ_LIB"]="C:\\OSGeo4W64\\share\\proj"
os.environ["GEOS_INCLUDE_PATH"]="C:\\OSGeo4W64\\include"
os.environ["GEOS_LIBRARY_PATH"]="C:\\OSGeo4W64\\lib"



#ORIGINAL_FILE="D:\\DivaGisData\\CongoBrazza_Fleur\\affluent_intermediaire_sud.gpkg"
ORIGINAL_FILE="D:\\DivaGisData\\CongoBrazza_Fleur\\makou_sud_dissolved.gpkg"
RASTER="D:\\DivaGisData\\CongoBrazza_Fleur\\fusion_s03E014s04e014_lefini_kouilou.tif"
CRS=32733
LEN_SEG=100

FIELD_ALT_1="Z"
FIELD_ALT_1_END="Z_END"
FIELD_LENGTH_1="length"

CUM_FIELD='DIST_SURF'

def handle_frame(p_df, x_field, y_field_start, y_field_end, cum_field_name, smooth=True, mode="begin", reverse_result=False):
    merged=None
    p_df = p_df[[ x_field, y_field_start, y_field_end]]
    if(len(p_df)>0):
        first=p_df.iloc[-1]
        first_z=first[y_field_start]
        last= p_df.iloc[-1]
        print(last[y_field_end])
        last_z=last[y_field_end]
        last_x=last[x_field]
        p_df.loc[len(p_df)] = [last_x, last_z, last_z]
        if (mode=="begin" and first_z<last_x) or (mode=="end" and first_z>last_x) :
            p_df=p_df.iloc[::-1]
    p_df[cum_field_name]=p_df[x_field].cumsum()
    print(p_df)
    ax1 = p_df.plot.scatter(x=CUM_FIELD, y=y_field_start, c='DarkBlue')
    if smooth:
        X= p_df[cum_field_name]
        y= p_df[y_field_start]
        gam1 = LinearGAM(s(0, constraints='monotonic_inc')).fit(X, y)
        smoothed=gam1.predict(X)
        print("X=")
        print(X.to_list())
        print(type(X))
        print("SMOOTH=")
        print(smoothed)
        print(len(X.to_list()))
        print(len(smoothed))
        ax1.plot(X, smoothed, label='monotonic fit', c='red')
        merged=pnd.DataFrame({cum_field_name: X.to_list(), "Z":smoothed })
        print(merged)
    plt.show()
    return merged

def pairs(lst):
    for i in range(1, len(lst)):
        yield lst[i-1], lst[i]
        
def handle_river(river_file, crs, len_seg, fp):
    data = gpd.read_file(river_file)
    raster_data = rxr.open_rasterio(fp, masked=True).rio.reproject("epsg:"+str(CRS))
    #data = data.explode()
    data["DISS"]=0
    dissolved = data.dissolve(by='DISS')
    dissolved=dissolved.to_crs(crs)
    print(dissolved.head())
    
    length = dissolved['geometry'].length
    print(length)
    geom = dissolved.loc[0, 'geometry']
    print(geom)
    try:
        merged_line = ops.linemerge(geom)
    finally:
        merged_line=geom
    print(merged_line)
    print(merged_line.length)
    geom_seg=segmentize(merged_line, max_segment_length=len_seg)
    print(raster_data)
    gen_x=[]
    gen_y=[]
    gen_z=[]
    
    gen_x_end=[]
    gen_y_end=[]
    gen_z_end=[]
    
    gen_length=[]
    for segment in pairs(list(geom_seg.coords)):
        #print(segment)
        dist=distance(Point(segment[0]), Point(segment[1]))
        x_list=[]
        y_list=[]
        x_list.append(segment[0][0])
        y_list.append(segment[0][1])
        gen_x.append(segment[0][0])
        gen_y.append(segment[0][1])
        #print(dist)
        
        
        x_end_list=[]
        y_end_list=[]
        x_end_list.append(segment[1][0])
        y_end_list.append(segment[1][1])
        gen_x_end.append(segment[1][0])
        gen_y_end.append(segment[1][1])
        #print(tmp)
        tmp=raster_data.sel(x=x_list, y=y_list, method="nearest")
        alt=tmp.to_numpy()[0][0][0]
        gen_z.append(alt)
        
        tmp_end=raster_data.sel(x=x_end_list, y=y_end_list, method="nearest")
        alt_end=tmp_end.to_numpy()[0][0][0]
        #print(alt)
        
        gen_z_end.append(alt_end)
        
        gen_length.append(dist)
    returned=pnd.DataFrame({"x": gen_x,"y": gen_y, "Z":gen_z,"Z_END":gen_z_end,  "length":gen_length })
    print(returned)
    return returned
    """
    print(tmp)
    print(tmp["x"])
    print(tmp["y"])
    print(tmp["band"])
    
    """
    
    #print(raster_data.sel(x=x_list, y=y_list, method="nearest").to_dataframe("river profile"))
    
def go():
    df1=handle_river(ORIGINAL_FILE, CRS, LEN_SEG, RASTER)
    merged_1=handle_frame(df1,FIELD_LENGTH_1,  FIELD_ALT_1, FIELD_ALT_1_END, CUM_FIELD, True, "begin", False )
go()