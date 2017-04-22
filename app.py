from flask import Flask, render_template, request, redirect, send_from_directory
import dill

from bokeh.plotting import figure, Figure
from bokeh.charts import Histogram, Bar, Scatter, Line
from bokeh.embed import components
from bokeh.models.widgets import Panel, Tabs, Select
from bokeh.models import Span, CustomJS, ColumnDataSource, Slider, Range1d

#for gmaps
from bokeh.models import GMapPlot, GMapOptions, ColumnDataSource, Circle, DataRange1d, PanTool, WheelZoomTool, BoxZoomTool,ResetTool

#from bokeh.models.sources import ColumnDataSource
from bokeh.layouts import gridplot, column, row

from bokeh.models import *

import cPickle as pickle
import re

import numpy as np
import pandas as pd

#app setup
app = Flask(__name__)
app.vars = {}

#read pickled dictionaries of user ratings and tag ratings
tagByUser = pickle.load( open("tag_count_by_user.pickle", "rb" ) )
histPerTag = pickle.load( open("hist_per_tag.pickle","rb") )

### read tag rating data
trans = dill.load(open('dv_trans.dill','rb'))
feat = list(dill.load(open('dv_feat.dill','rb')))


###selected features for plotting
selectedFeat = ['python','python-3.x','azure','c','c#','c++','docker','numpy','ios','java','r','pandas']
selectedFeat.sort()
selectedFeatIdx = [feat.index(ft) for ft in selectedFeat]

'''
#geolocation stuff
loc_dict = pickle.load(open( "loc_dict.pickle", "rb" ) )
lat_long_dict_a = pickle.load(open( "lat_long_dict_a.pickle", "rb" ) ) #tech string in lat_long bin
lat_long_dict_b = pickle.load(open( "lat_long_dict_b.pickle", "rb" ) ) #userid in each lat_long bin
'''

@app.route('/')
def main():
    return redirect('/index')

@app.route('/index',methods=['GET','POST'])
def index():
    return render_template('index.html')

@app.route('/viz1')
def viz1():

    data = {}
    for i in range(len(selectedFeat)):
        sf = selectedFeat[i]
        arr = trans.getcol(selectedFeatIdx[i]).toarray()
        arg = np.where(arr==0)[0]
        arr[arg] = -99
        data[sf] = arr

    data['x'] = data['python']
    data['y'] = data['c']

    print 'keys', data.keys()

    source = ColumnDataSource(data=data)

    plot = Figure(plot_width=600, plot_height=600, title='StackOverflow.com Skill Tag Correlations')
    plot.x_range = Range1d(0,200)
    plot.y_range = Range1d(0,200)
    plot.scatter('x', 'y', source=source)
    plot.xaxis.axis_label = "Skill 1 Tag Score"
    plot.yaxis.axis_label = "Skill 2 Tag Score"
    print 'got plot'

    callbackX = CustomJS(args=dict(source=source), code="""
        var data = source.data;
        var f = cb_obj.value
        source.data['x'] = data[f]
        source.trigger('change');
    """)

    callbackY = CustomJS(args=dict(source=source), code="""
        var data = source.data;
        var f = cb_obj.value
        source.data['y'] = data[f]
        source.trigger('change');
    """)

    selectX = Select(title="Skill 1:", value='python', options=selectedFeat)
    selectX.js_on_change('value', callbackX)
    selectY = Select(title="Skill 2:", value='r', options=selectedFeat)
    selectY.js_on_change('value', callbackY)
    print 'select'

    c1 = column(selectX,selectY)
    c2 = column(plot)
    layout = row([c1,c2])
    print 'layout'

    script, div = components(layout) #works for single plot
    print 'script, div'

    #kwargs
    kwargs = {}
    kwargs['script'] = script
    kwargs['div'] = div

    print 'kwargs'


    return render_template('viz.html',**kwargs)

@app.route('/viz2')
def viz2():
    print 'in viz2'
    data = {}
    for i in range(len(selectedFeat)):
        sf = selectedFeat[i]
        xkey = sf+'-x'
        ykey = sf+'-y'
        data[xkey] = np.log10(histPerTag[sf][0][:-1]) #all but last bin edge
        data[ykey] = np.log10(histPerTag[sf][1])

    data['x'] = data['python-x']
    data['y'] = data['python-y']

    print 'keys', data.keys()

    source = ColumnDataSource(data=data)

    plot = Figure(plot_width=600, plot_height=600, title='Number of People With a Given Tag Score')

    print 'got figure'

    plot.scatter('x', 'y',source=source, size=6)
    plot.line('x', 'y', source=source, line_width=3)

    plot.xaxis.axis_label = "log10(Tag Score)"
    plot.yaxis.axis_label = "log10(Number)"

    print 'got plot'

    callback = CustomJS(args=dict(source=source), code="""
        var data = source.data;
        var f = cb_obj.value
        source.data['x'] = data[f+'-x']
        source.data['y'] = data[f+'-y']
        source.trigger('change');
    """)

    select = Select(title="Tag", value='python', options=selectedFeat)
    select.js_on_change('value', callback)
    print 'select'

    c1 = column(select)
    c2 = column(plot)
    layout = row([c1,c2])
    print 'layout'

    script, div = components(layout) #works for single plot
    print 'script, div'

    #kwargs
    kwargs = {}
    kwargs['script'] = script
    kwargs['div'] = div

    print 'kwargs'

    return render_template('viz.html',**kwargs)

@app.route('/viz3')
def viz3():

    print 'in viz 3'
    X2008  = pd.read_csv('flat_2008-01312009.csv')
    X2009  = pd.read_csv('flat_01022009-2009.csv')
    X2010  = pd.read_csv('flat_2010.csv')
    X2011  = pd.read_csv('flat_2011.csv')
    X2012  = pd.read_csv('flat_2012.csv')
    X2013  = pd.read_csv('flat_2013.csv')
    X2014  = pd.read_csv('flat_2014.csv')

    data = {}
    print 'data collation'
    #for df,yr in zip([X2008,X2009],['2008','2009']):
    for df,yr in zip([X2008,X2009,X2010,X2011,X2012,X2013,X2014],['2008','2009','2010','2011','2012','2013','2014']):

        uid_subset = []
        tcount = []
        rep_subset = []
        #for i in range(len(df['user_id'])):
        for i in np.random.randint(0,len(df),5000): #random subset of data
            uid = str(df['user_id'].loc[i])
            if tagByUser.has_key(uid):
                tcount.append(tagByUser[uid])
                rep_subset.append(df['reputation'].loc[i])
         
        data[yr+'-x'] = tcount
        data[yr+'-y'] = rep_subset

    print 'post data collation'

    data['x'] = data['2008-x']
    data['y'] = data['2008-y']

    print 'keys', data.keys()

    source = ColumnDataSource(data=data)

    plot = Figure(plot_width=600, plot_height=600, title='Reputation vs Tag Count')
    plot.x_range = Range1d(0,1000)
    plot.y_range = Range1d(0,40000)

    print 'got figure'

    plot.scatter('x', 'y',source=source, size=3)

    plot.xaxis.axis_label = "User Tag Count"
    plot.yaxis.axis_label = "Reputation"

    print 'got plot'

    callback = CustomJS(args=dict(source=source), code="""
        var data = source.data;
        var f = cb_obj.value
        source.data['x'] = data[f+'-x']
        source.data['y'] = data[f+'-y']
        source.trigger('change');
    """)

    select = Select(title="Year Joined StackOverflow", value='2008', options=['2008','2009','2010','2011','2012','2013','2014'])
    select.js_on_change('value', callback)
    print 'select'

    c1 = column(select)
    c2 = column(plot)
    layout = row([c1,c2])
    print 'layout'

    script, div = components(layout) #works for single plot
    print 'script, div'

    #kwargs
    kwargs = {}
    kwargs['script'] = script
    kwargs['div'] = div

    return render_template('viz.html',**kwargs)

if __name__ == '__main__':
  app.run(host='0.0.0.0',port=33507)
