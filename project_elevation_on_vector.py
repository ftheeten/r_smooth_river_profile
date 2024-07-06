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
import traceback

os.environ["PROJ_LIB"]="C:\\OSGeo4W\\share\\proj"
#os.environ["GEOS_INCLUDE_PATH"]="C:\\OSGeo4W64\\include"
#os.environ["GEOS_LIBRARY_PATH"]="C:\\OSGeo4W64\\lib"



#ORIGINAL_FILE="D:\\DivaGisData\\CongoBrazza_Fleur\\affluent_intermediaire_sud.gpkg"
ORIGINAL_FILE_1="C:\\DEV\\CongoBrazza_Fleur\\passage_est_affluent_ndoue.gpkg"
ORIGINAL_FILE_2="C:\\DEV\\CongoBrazza_Fleur\\passage_fleur_no_3.gpkg"
ORIGINAL_FILE_3="C:\\DEV\\CongoBrazza_Fleur\\fleur_passage_no3_affluent_nord.gpkg"
RASTER="C:\\DEV\\CongoBrazza_Fleur\\fusion_s03E014s04e014_lefini_kouilou.tif"
CRS=32733
LEN_SEG=100

FIELD_ALT_1="Z"
FIELD_ALT_1_END="Z_END"
FIELD_LENGTH_1="length"
FIELD_NAME="NAME"
NAME_1="Affluent Ndoue"
NAME_2="Crestline"
NAME_3="Affluent Lefini"
CUM_FIELD='DIST_SURF'
TITLE="Profile line c"


def handle_frame(p_df, z_field_start, cum_field_name, field_name, name, smooth=True, color='DarkBlue', mode="begin"):
    merged=None
    first=p_df.iloc[0]
    first_z=first[z_field_start]
    print("first_z="+str(first_z))
    last= p_df.iloc[-1]
    last_z=last[z_field_start]
    print("last_z="+str(last_z))
    
    len_cum=p_df[cum_field_name].max()
    

    if smooth and first_z>last_z:
        print("REVERSE")
        #
        print(len_cum)
        p_df[cum_field_name]=abs(p_df[cum_field_name]-len_cum)
        p_df=p_df.iloc[::-1]    
    
    p_df["ORIGINAL_Z"]= p_df[z_field_start]
    if smooth:
        X= p_df[cum_field_name]
        y= p_df[z_field_start]
        gam1 = LinearGAM(s(0, constraints='monotonic_inc')).fit(X, y)
        smoothed=gam1.predict(X)
        
        #ax1.plot(X, smoothed, label='monotonic fit', c='red')
        #merged=pnd.DataFrame({cum_field_name: X.to_list(), "Z":smoothed })
        #merged=p_df
        #print(merged)
        p_df[z_field_start]=smoothed
        print(p_df)
    first=p_df.iloc[0]
    first_z=first[z_field_start]
    print("first_z="+str(first_z))
    last= p_df.iloc[-1]
    last_z=last[z_field_start]
    len_cum=p_df[cum_field_name].max()
    if (mode=="begin" and first_z>last_z) or (mode=="end" and first_z<last_z):
        p_df[cum_field_name]=abs(p_df[cum_field_name]-len_cum)
        p_df=p_df.iloc[::-1]
    p_df[cum_field_name]=p_df[cum_field_name]
    #if smooth:
    #    p_df = p_df.sort_values(by=[z_field_start], ascending=True)
    #else:
    p_df = p_df.sort_values(by=[cum_field_name], ascending=True)
    p_df[field_name]=name        
    ax1 = p_df.plot.scatter(x=cum_field_name, y="ORIGINAL_Z", c="black")
    ax1.plot(p_df[cum_field_name], p_df[z_field_start], label='monotonic fit', c=color)
    plt.show()
    return p_df

def pairs(lst):
    for i in range(1, len(lst)):
        yield lst[i-1], lst[i]
        
def line_merge(geom):
    try:
        tmp = ops.linemerge(geom)
        geom=tmp
    except Exception:
        print(traceback.format_exc())
    finally:
        return geom
        
def handle_river(river_file, crs, len_seg, x_field, y_field_start, y_field_end, cum_field_name, fp):
    data = gpd.read_file(river_file)
    raster_data = rxr.open_rasterio(fp, masked=True).rio.reproject("epsg:"+str(CRS))
    #data = data.explode()
    data["DISS"]=0
    dissolved = data.dissolve(by='DISS')
    dissolved=dissolved.to_crs(crs)
    #print(dissolved.head())
    
    length = dissolved['geometry'].length
    #print(length)
    geom = dissolved.loc[0, 'geometry']
    #print(geom)
    merged_line=line_merge(geom)
    #print(merged_line)
    #print(merged_line.length)
    geom_seg=segmentize(merged_line, max_segment_length=len_seg)
    #print(raster_data)
    gen_x=[]
    gen_y=[]
    gen_z=[]
    
    gen_x_end=[]
    gen_y_end=[]
    gen_z_end=[]
    
    gen_length=[]
    
    gen_x_begin_4326=[]
    gen_y_begin_4326=[]
    gen_x_end_4326=[]
    gen_y_end_4326=[]
    if crs!=4326:
        p_transformer =Transformer.from_crs(crs, 4326, always_xy=True)
    
    #print(geom_seg.coords)
    #print(list(geom_seg.coords))
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
        if crs!=4326:
            begin_4326=ops.transform(p_transformer.transform, Point(segment[0][0], segment[0][1]))
            end_4326=ops.transform(p_transformer.transform, Point(segment[1][0], segment[1][1]))
        else:
            begin_4326=Point(segment[0][0], segment[0][1])
            end_4326=Point(segment[1][0], segment[1][1])
        gen_x_begin_4326.append(begin_4326.x)
        gen_y_begin_4326.append(begin_4326.y)
        gen_x_end_4326.append(end_4326.x)
        gen_y_end_4326.append(end_4326.y)
    returned=pnd.DataFrame({"x": gen_x_begin_4326,"y": gen_y_begin_4326, "x_end": gen_x_end_4326,"y_end": gen_y_end_4326, "Z":gen_z,"Z_END":gen_z_end,  "length":gen_length })
    
    if(len(returned)>0):
        first=returned.iloc[0]
        first_z=first[y_field_start]
        first_x=first[x_field]
        last= returned.iloc[-1]
        #print(last[y_field_end])
        #last_z=last[y_field_end]
        #last_x=last[x_field]
        last_x=last["x_end"]
        #last_y=last["y_end"]
        last_z=last["Z_END"]
        #print('first x:'+str(first_x))
        #print('last x:'+str(last_x))
        #returned.loc[len(returned)] = [last_x, last_y, None, None, last_z, None, 0]
        if first_z<last_z: #(mode=="begin" and first_z<last_z) or (mode=="end" and first_z>last_z) :
            returned=returned.iloc[::-1]
            
        returned[cum_field_name]=returned[x_field].cumsum()-first_x
    #print(returned)
    return returned
    """
    print(tmp)
    print(tmp["x"])
    print(tmp["y"])
    print(tmp["band"])
    
    """
    
    #print(raster_data.sel(x=x_list, y=y_list, method="nearest").to_dataframe("river profile"))
 
def get_offset(p_pnd, p_dist_field):
    returned=0
    if len(p_pnd)>0:
        last= p_pnd.iloc[-1]
        returned=last[p_dist_field]
    return returned

def concatenate_df(df_1, df_2,  cum_field, field_length, name_field, align_alt=False, z_field=""):    
    last=df_1.iloc[-1]
    first=df_2.iloc[0]
    last[name_field]=first[name_field]
    offset=last[cum_field]+last[field_length]
    df_2[cum_field]=df_2[cum_field]+offset
    
    df_2.iloc[-1]=last
    if align_alt:
        df_2.loc[df_2[z_field]<last[z_field], z_field]=last[z_field]
    df_2.index = df_2.index + 1  # shifting index
    tmp=pnd.concat([df_1, df_2], axis=0, ignore_index=True)
    tmp=tmp.sort_values(by=[cum_field], ascending=True)
    return tmp
    
def go():
    df1=handle_river(ORIGINAL_FILE_1, CRS, LEN_SEG, FIELD_LENGTH_1,  FIELD_ALT_1, FIELD_ALT_1_END, CUM_FIELD, RASTER)
    merged_1=handle_frame(df1, FIELD_ALT_1,  CUM_FIELD, FIELD_NAME, NAME_1, True, 'DarkBlue', "begin")
    #print(merged_1)
    #offset_1=get_offset(merged_1, CUM_FIELD)
    #print("offset1")
    #print(offset_1)
    df2=handle_river(ORIGINAL_FILE_2, CRS, LEN_SEG, FIELD_LENGTH_1,  FIELD_ALT_1, FIELD_ALT_1_END, CUM_FIELD, RASTER)
    merged_2=handle_frame(df2,  FIELD_ALT_1,  CUM_FIELD, FIELD_NAME, NAME_2, False, 'Black', "begin")
    merged_2=concatenate_df(merged_1, merged_2, CUM_FIELD, FIELD_LENGTH_1, FIELD_NAME, True, FIELD_ALT_1)
    #offset_2=get_offset(merged_2, CUM_FIELD)
    #print("offset2")
    #print(offset_2)
    df3=handle_river(ORIGINAL_FILE_3, CRS, LEN_SEG, FIELD_LENGTH_1,  FIELD_ALT_1, FIELD_ALT_1_END, CUM_FIELD, RASTER)
    merged_3=handle_frame(df3, FIELD_ALT_1,  CUM_FIELD, FIELD_NAME, NAME_3, True, 'Red',  "end")
    df_final=concatenate_df(merged_2, merged_3, CUM_FIELD, FIELD_LENGTH_1, FIELD_NAME)
    print(df_final)
    first=df_final[df_final[FIELD_NAME]==NAME_1]
    second=df_final[df_final[FIELD_NAME]==NAME_2]
    third=df_final[df_final[FIELD_NAME]==NAME_3]
    
    fig_final, ax_final = plt.subplots()
    ax_final.plot(first[CUM_FIELD], first[FIELD_ALT_1], label=NAME_1, c="DarkBlue")
    ax_final.plot(second[CUM_FIELD], second[FIELD_ALT_1], label=NAME_2, c="Black", linestyle="dashed")
    ax_final.plot(third[CUM_FIELD], third[FIELD_ALT_1], label=NAME_3, c="Red")
    plt.xlabel("Distance on map (m)")
    plt.ylabel("Elevation (m)")
    plt.legend(loc="best")
    plt.title(TITLE)
    first_x=round(df_final.iloc[0]["x"],4)
    first_y=round(df_final.iloc[0]["y"],4)
    last_x=round(df_final.iloc[-1]["x_end"],4)
    last_y=round(df_final.iloc[-1]["y_end"],4)
    plt.figtext(0.5, 0.01, "Begin : lat "+str(first_x)+" lon"+str(first_y)+" "+"End : lat "+str(last_x)+" lon"+str(last_y), ha="center")
    plt.show()
go()