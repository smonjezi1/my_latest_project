import dill
import pickle
import pandas as pd
import io
import requests
from datetime import date
from flask import Flask, render_template, request, redirect
from bokeh.plotting import figure, show, output_notebook
from bokeh.embed import components
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, Range1d
app = Flask(__name__)

#car models to search
df_top = dill.load(open('df_top.pkd', 'rb'))
#model discontinuation check file
df_top2 = dill.load(open('df_top2.pkd', 'rb'))
#estimator
car_est3 = pickle.load(open('car_est3.sav', 'rb'))
#mlp

# maintenance calculation
def cost_calc3(year,make,model,span,annual_mileage):
    cond=(df_top2['make0']==make)&(df_top2['model0']==model)
    current_price=car_est3.predict([[year,make,model,(2019-year)*15000]])
    future_price=car_est3.predict([[year-span,make,model,(2019-year)*15000+span*annual_mileage]])
    price_drop=current_price[0]-future_price[0]
    maintnc_cost=0
    for i in range(span):
        maintnc_cost=list(df_top2['cost'][cond&(df_top2['year0']==year-i)])[0]+maintnc_cost
    return int(price_drop+maintnc_cost)

#car recommendation model
def car_recom(years_to_keep,budget,annual_mileage,tol):
    possible_cars3=pd.DataFrame(columns=['year','make','model','predicted price (USD)','estimated total loss after '+str(years_to_keep)+' years (USD)'])
    s=0
    for i in range(len(df_top)):
        make,model=df_top.loc[i,['make0','model0']]
        for j in range(len(df_top2[['cost']][(df_top2['make0']==make)&(df_top2['model0']==model)])-years_to_keep):        
            year=max(df_top2[['year0']][(df_top2['make0']==make)&(df_top2['model0']==model)].values)[0]-j
    #        if (year-min(df_top2[['year0']][(df_top2['make0']==make)&(df_top2['model0']==model)].values)[0])+1<=years_to_keep: continue
            est_price=int(car_est3.predict([[year,make,model,(2019-year)*15000]])[0])
            if (est_price>budget-tol)&(est_price<budget+tol):
                possible_cars3.loc[s] = [year,make,model,est_price,cost_calc3(year,make,model,years_to_keep,annual_mileage)]
                s+=1
    return possible_cars3.sort_values(['estimated total loss after '+str(years_to_keep)+' years (USD)'], ascending=[1]).reset_index(drop=True)


@app.route('/')
def main():
    return redirect('/index')

@app.route('/index', methods=['GET','POST'])
def index():
    err_msg = '<div class="error">\n  <p style="font-size: 25px;text-align:center;color:red;font-family:verdana;">Unexpected or out of range values!!! Try again.</p>\n</div>\n'
    if request.method == 'GET':
        return render_template('index.html', script_1="", script_2="")
    else:
        try:
            years_to_keep=int(request.form['input_years'])
            budget=int(request.form['input_budget'])
            annual_mileage=int(request.form['input_miles'])
            tol=int(request.form['input_tol'])
            df_table = car_recom(years_to_keep,budget,annual_mileage,tol)
            if budget-tol<1500 or budget+tol>70000:
                return render_template('index.html', script_1="", script_2=err_msg)                
        except:
            return render_template('index.html', script_1="", script_2=err_msg)
        if df_table.empty:
            return render_template('index.html', script_1="", script_2=err_msg)
        table_script=df_table.to_html(classes='df',index=False)
        table_script=table_script.replace('<table border="1" class="dataframe df">','<table border="1" class="sortable" class="dataframe df">')    
        return render_template(
            'index.html',
            script_1="",
            script_2=table_script)

if __name__ == '__main__':
    
    app.debug = True
    app.run(host='127.0.0.1',use_reloader=True)
