import pandas as pnd
import matplotlib.pyplot as plt
from pygam import LinearGAM, s
import tkinter as tk
from tkinter import filedialog


#SRC_DATASET_1="D:\\DivaGisData\\CongoBrazza_Fleur\\POUR_LISSAGE\\makou_sud_altitude_100m.txt"
SRC_DATASET_1="D:\\DivaGisData\\CongoBrazza_Fleur\\POUR_LISSAGE\\makou_sud_altitude_100m_end.xlsx"
FIELD_ALT_1="Z"
FIELD_ALT_1_END="Z_END"
FIELD_LENGTH_1="longueur_m"

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
    
def go():
    print("test")
    #df1=pnd.read_csv(SRC_DATASET_1, sep="\t", header=0)
    df1=pnd.read_excel(SRC_DATASET_1)
    merged_1=handle_frame(df1,FIELD_LENGTH_1,  FIELD_ALT_1, FIELD_ALT_1_END, CUM_FIELD, True, "begin", False )
    file_path1 = filedialog.asksaveasfilename(defaultextension=".xslx", filetypes=[("Excel files", "*.xslx"), ("All files", "*.*")])
    merged_1.to_excel(file_path1)
    
go()
