import urllib       # to download the data set
import pandas as pd

import plotly
import plotly.plotly as py
import plotly.figure_factory as ff
from plotly.graph_objs import layout
import plotly.graph_objs as go

# download the file online
file = urllib.request.urlopen("https://uofi.box.com/shared/static/bba3968d7c3397c024ec.dta")

# read the stata file to a pandas dataframe
df_dd = pd.read_stata(file)

# add a column "edate_end"
df_dd["edate_end"] = ""

# delete all rows where edate is empty
df_dd = df_dd[df_dd.edate != ""]

# reset the index and delete previous index column
df_dd = df_dd.reset_index()
df_dd.drop('index', axis=1, inplace=True)

# fix typos in the edate column
for index, row in df_dd.iterrows():
    date = row["edate"].split(".")

    # check if the date has 3 parts [MM.DD.YY]
    if len(date) != 3:
        date = input("The date doesn't seem to be in this style: [MM.DD.YY] Please enter the right date format: "+row["edate"]).split(".")

    # format the month
    if len(date[0]) == 2:
        if date[0] == "00":
            date[0] = "01"
    elif len(date[0]) == 1:
        if date[0] == "0":
            date[0] = "1"
        date[0] = "0"+date[0]
    else:
        date[0] = input("Insert the right month: "+date[0])

    # format the day
    if len(date[1]) == 2:
        if date[1] == "00":
            date[1] = "01"
    elif len(date[1]) == 1:
        if date[1] == "0":
            date[1] = "1"
        date[1] = "0"+date[1]
    else:
        date[1] = input("Insert the right day: "+date[1])

    # format the year
    if len(date[2]) == 2:
        if row["year"] <= 1999:
            date[2] = "19"+date[2]
        else:
            date[2] = str(row["year"])
    elif len(date[2]) == 1:
        if date[2] == "0":
            date[2] = "1"
        date[2] = "0"+date[2]
    else:
        date[2] = input("Pick the right year: "+date[2])

    # Make a string from the list
    date = ".".join(date)
    # Exchange the old date with the new
    df_dd.at[index,"edate"] = date

    # Use the date of the next regime as "edate_end"
    if df_dd.iloc[index-1]["ctryname"] == row["ctryname"]:
        df_dd.at[index-1,"edate_end"] = date
    else:
        df_dd.at[index-1,"edate_end"] = "12.31."+str(int(df_dd.iloc[index-1]["exity"]))

# fixing the last row
df_dd.edate_end.iloc[-2] = "12.31.2008"
df_dd = df_dd.drop(df_dd.index[-1])

# change to DateTime format
df_dd["edate"] = pd.to_datetime(df_dd["edate"], format="%m.%d.%Y")
df_dd["edate_end"] = pd.to_datetime(df_dd["edate_end"], format="%m.%d.%Y")

# change float to integer
df_dd["regime"] = df_dd["regime"].astype(int)
df_dd["year"] = df_dd["year"].astype(int)
df_dd["exity"] = df_dd["exity"].astype(int)

df_work = df_dd#.loc[0:200]
df_work["duration"] = df_work["edate_end"]-df_work["edate"]
df_work["duration_str"] = ""

# get a clear text instead of timedelta
for index, row in df_work.iterrows():
    time = row["duration"]
    years = int(str(int(str(time).split(" ")[0]) / 365).split(".")[0])
    months = int(str((int(str(time).split(" ")[0]) / 365 - years) * 12).split(".")[0])
    days = int(str((((int(str(time).split(" ")[0]) / 365 - years) * 12) - months) * 30).split(".")[0])
    output = str(years)+" Years "+str(months)+" Months "+str(days)+" Days"
    df_work.at[index,"duration_str"] = output

data = []
for row in df_work.itertuples():
    data.append(dict(Task=str(row.ctryname), Start=str(row.edate), Finish=str(row.edate_end), Resource=int(row.regime)))

# define the colors of the different regime types in the diagram
colors = {0:  "#003bb7", 1: '#0657ff', 2: '#8fb4ff', 3: '#ffda8f', 4: "#ffad06", 5: '#ff6f06'} # shing the groups individually
#colors = {0:"#003bb7",1:'#003bb7',2:'#003bb7',3:'#ffad06',4:"#ffad06",5:'#ffad06'} # distiguish only between dictatorships and democracies
#colors = {0:"#FFFFFF",1:'#FFFFFF',2:'#FFFFFF',3:'#000000',4:"#000000",5:'#000000'} # only dictatorships in black

fig = ff.create_gantt(data,
                      colors=colors,
                      index_col='Resource',
                      show_colorbar=False,
                      title='Regimes in history worldwide',
                      showgrid_x=True,
                      group_tasks=True)

resource_type = {0 : "Parliamentary democracy",
                 1 : "Mixed (semi-presidential) democracy",
                 2 : "Presidential democracy",
                 3 : "Civilian dictatorship",
                 4 : "Military dictatorship",
                 5 : "Royal dictatorship"}

# improved hover
for i in range(len(fig["data"]) - 2):
    text = "Country: {}<br>Leader: {}<br>Regime type: {}<br>Duration: {}".format(df_work["ctryname"].loc[i], df_work["ehead"].loc[i], resource_type[df_work["regime"].loc[i]], df_work["duration_str"].loc[i])
    fig["data"][i].update(text=text, hoverinfo="text")

fig["layout"].update(autosize=True, margin=dict(l=200), height=6000, width=1800)

plotly.offline.plot(fig, filename='./regimes.html')
