# dependencies
from flask import Flask, render_template, jsonify
import pandas as pd
from sqlalchemy import create_engine

# establishing DB connection 
database_path = "Resources/NJ_CPS.sqlite"
engine = create_engine(f"sqlite:///{database_path}", echo=True)

# table names

school = "NJ_school_rating"
poverty = "NJ_poverty"
crime = "NJ_crime"
population = "NJ_population"

# --- create an instance of the Flask class ---
app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/d3')
def d3():
    return render_template("d3.html")

@app.route('/api/d3_data')
def d3_data():
    sqlite_connection = engine.connect()
      
    query = '''SELECT POV.county_name, POV.median_hh_income, POV.poverty_rate, POV.county_fips,
               CRM.total AS total_offense, ROUND(CRM2.total,2) AS rate_per_100k, CRM3.total AS total_arrest,
               POP.population, SCH.school_rank
               FROM NJ_poverty AS POV 
               INNER JOIN NJ_crime AS CRM ON POV.county_name = CRM.county_name AND CRM.report_type = 'Number of Offenses'
               INNER JOIN NJ_crime AS CRM2 ON POV.county_name = CRM2.county_name AND CRM2.report_type = 'Rate Per 100,000'
               INNER JOIN NJ_crime AS CRM3 ON POV.county_name = CRM3.county_name AND CRM3.report_type = 'Number of Arrests'
               INNER JOIN (SELECT county_name, SUM(population) AS population FROM NJ_population GROUP BY county_name) AS POP ON POV.county_name = POP.county_name
               INNER JOIN (SELECT county_name, ROUND(AVG(summativescore),2) AS school_rank FROM NJ_school_rating GROUP BY county_name) AS SCH ON POV.county_name = SCH.county_name'''
    df = pd.read_sql(query, sqlite_connection)

    data_csv = df.to_csv(encoding='utf-8')
    sqlite_connection.close()
    
    print("Data retrieval successfull")
    
    return data_csv

@app.route('/plotly')
def plotly():
    return render_template("plotly.html")

@app.route('/api/plotly_data')
def plotly_data():
    sqlite_connection = engine.connect()
    
    metadata_df = pd.read_sql_query("SELECT T1.*, T2.population FROM (SELECT county_name,median_hh_income,poverty_rate FROM NJ_poverty) AS T1 \
                                INNER JOIN (SELECT county_name, sum(population) as population FROM NJ_population GROUP BY county_name) AS T2\
                                ON T1.county_name = T2.county_name", sqlite_connection)
    metadata_dict = metadata_df.to_dict(orient='records')
    
    school_df = pd.read_sql_query("SELECT county_name,district_code||school_code as school_id, school_name,summativescore FROM NJ_school_rating ORDER BY county_name, summativescore DESC", sqlite_connection)
    school_dict = school_df.to_dict(orient='records')
    
    crime_df = pd.read_sql_query("SELECT county_name, murder,rape, robbery, assault, burglary, larceny, auto_theft, total FROM NJ_crime WHERE report_type = 'Number of Offenses'", sqlite_connection)
    crime_dict = crime_df.to_dict(orient='records')
    
    sqlite_connection.close()
    
    data_json= {}
    data_json["metadata"] = metadata_dict
    data_json["school"] = school_dict
    data_json["crime"] = crime_dict
    
    print("Data retrieval successfull")
    
    return jsonify(data_json)

@app.route('/api/sunburst1_data')
def sunburst_data():
    sqlite_connection = engine.connect()
      
    query1 = '''SELECT DISTINCT "NJ-"||county_name AS id , county_name AS label,  '' AS parent, SUM(count) AS value FROM 
            (SELECT county_name, 'murder' AS crime_type, murder AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'rape' AS crime_type, rape AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'robbery' AS crime_type, robbery AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'assault' AS crime_type, assault AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'burglary' AS crime_type, burglary AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'larceny' AS crime_type, larceny AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'auto_theft' AS crime_type, auto_theft AS count FROM NJ_crime WHERE report_type = 'Number of Offenses')
        GROUP BY 1,2,3'''
    df1 = pd.read_sql(query1, sqlite_connection)

    query2 = '''SELECT DISTINCT county_name||"-"||crime_type AS id ,crime_type AS label,  "NJ-"||county_name AS parent, SUM(count) AS value FROM 
            (SELECT county_name, 'murder' AS crime_type, murder AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'rape' AS crime_type, rape AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'robbery' AS crime_type, robbery AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'assault' AS crime_type, assault AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'burglary' AS crime_type, burglary AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'larceny' AS crime_type, larceny AS count FROM NJ_crime WHERE report_type = 'Number of Offenses'
        UNION ALL SELECT county_name, 'auto_theft' AS crime_type, auto_theft AS count FROM NJ_crime WHERE report_type = 'Number of Offenses')
        GROUP BY 1,2,3'''
    df2 = pd.read_sql(query2, sqlite_connection)
    
    df = pd.concat([df1, df2])
    data_csv = df.to_csv(encoding='utf-8')
    sqlite_connection.close()
    
    print("Data retrieval successfull")
    
    return data_csv

@app.route('/api/sunburst2_data')
def sunburst2_data():
    sqlite_connection = engine.connect()

    query1 = '''SELECT DISTINCT "NJ-"||county_name AS id , county_name AS label,  '' AS parent, AVG(summativescore) AS value FROM 
            (SELECT county_name,district_name,gradespan,school_name,summativescore
            FROM 
              ( SELECT county_name,district_name,gradespan,school_name, summativescore,
                       ROW_NUMBER() OVER (PARTITION BY county_name
                                          ORDER BY summativescore DESC) AS rn
                FROM NJ_school_rating) AS tmp 
            WHERE rn <= 3
            ORDER BY county_name) GROUP BY 1,2,3'''
    df1 = pd.read_sql(query1, sqlite_connection)
      
    # query2 = '''SELECT DISTINCT county_name||"-"||school_name AS id ,school_name AS label,  "NJ-"||county_name AS parent, AVG(summativescore) AS value FROM 
    #         NJ_school_rating GROUP BY 1,2,3'''
    # df2 = pd.read_sql(query2, sqlite_connection)
    
    query2 = '''SELECT DISTINCT county_name||"-"||gradespan AS id ,gradespan AS label,  "NJ-"||county_name AS parent, AVG(summativescore) AS value FROM 
            (SELECT county_name,district_name,gradespan,school_name,summativescore
            FROM 
              ( SELECT county_name,district_name,gradespan,school_name, summativescore,
                       ROW_NUMBER() OVER (PARTITION BY county_name
                                          ORDER BY summativescore DESC) AS rn
                FROM NJ_school_rating) AS tmp 
            WHERE rn <= 3
            ORDER BY county_name) GROUP BY 1,2,3'''
    df2 = pd.read_sql(query2, sqlite_connection)

    # query2 = '''SELECT DISTINCT county_name||"-"||district_name AS id ,district_name AS label,  "NJ-"||county_name AS parent, AVG(summativescore) AS value FROM 
    #         NJ_school_rating GROUP BY 1,2,3'''
    # df2 = pd.read_sql(query2, sqlite_connection)
    
    query3 = '''SELECT DISTINCT gradespan||"-"||district_name AS id ,district_name AS label,  county_name||"-"||gradespan AS parent, AVG(summativescore) AS value FROM 
            (SELECT county_name,district_name,gradespan,school_name,summativescore
            FROM 
              ( SELECT county_name,district_name,gradespan,school_name, summativescore,
                       ROW_NUMBER() OVER (PARTITION BY county_name
                                          ORDER BY summativescore DESC) AS rn
                FROM NJ_school_rating) AS tmp 
            WHERE rn <= 3
            ORDER BY county_name) GROUP BY 1,2,3'''
    df3 = pd.read_sql(query3, sqlite_connection)
    
    # query3 = '''SELECT DISTINCT district_name||"-"||gradespan AS id ,gradespan AS label,  county_name||"-"||district_name AS parent, AVG(summativescore) AS value FROM 
    #         NJ_school_rating GROUP BY 1,2,3'''
    # df3 = pd.read_sql(query3, sqlite_connection)
    
    # query3 = '''SELECT DISTINCT district_name||"-"||school_name AS id ,school_name AS label,  county_name||"-"||district_name AS parent, AVG(summativescore) AS value FROM 
    #     NJ_school_rating GROUP BY 1,2,3'''
    # df3 = pd.read_sql(query3, sqlite_connection)
    
    query4 = '''SELECT DISTINCT district_name||"-"||school_name AS id ,school_name AS label,  gradespan||"-"||district_name AS parent, AVG(summativescore) AS value FROM 
        (SELECT county_name,district_name,gradespan,school_name,summativescore
        FROM 
            ( SELECT county_name,district_name,gradespan,school_name, summativescore,
                    ROW_NUMBER() OVER (PARTITION BY county_name
                                        ORDER BY summativescore DESC) AS rn
            FROM NJ_school_rating) AS tmp 
        WHERE rn <= 3
        ORDER BY county_name) GROUP BY 1,2,3'''
    df4 = pd.read_sql(query4, sqlite_connection)
    
    # df = pd.concat([df1, df2])
    
    # df = pd.concat([df1, df2, df3])
    
    df = pd.concat([df1, df2, df3, df4])
    
    data_csv = df.to_csv(encoding='utf-8')
    sqlite_connection.close()
    
    print("Data retrieval successfull")
    
    return data_csv

@app.route('/api/d3_zoom_sunburst')
def d3_zoom_sunburst():
    sqlite_connection = engine.connect()

    query = '''SELECT county_name,district_name,gradespan,school_name,summativescore FROM NJ_school_rating ORDER BY county_name,district_name,gradespan,school_name;'''
    test = pd.read_sql_query(query, sqlite_connection)
    
    sqlite_connection.close()
    
    data_json = {}
    data_json["name"] = "flare"
    data_json["description"] = "flare"
    
    counties = list(test['county_name'].unique())
    
    children = []
    for i in range(len(counties)):
        child1 = {}
        child1["name"] = counties[i]
        child1["description"] = counties[i]
        district = list(test['district_name'].loc[test['county_name']==counties[i]].unique())
        child2_list = []
        for k in range(len(district)):
            child2 = {}
            child2["name"] = district[k]
            child2["description"] = district[k]
            child3_list = []
            gradespan = list(test['gradespan'].loc[(test['county_name']==counties[i]) & (test['district_name'] == district[k])].unique())
            for j in range(len(gradespan)):
                child3 = {}
                child3["name"] = gradespan[j]
                child3["description"] = gradespan[j]
                child4_list = []
                for index,row in test.loc[(test['county_name']==counties[i]) & (test['district_name'] == district[k]) & (test['gradespan'] == gradespan[j])].iterrows():
                    child4 = {}
                    child4["name"] = row["school_name"]
                    child4["description"] = row["school_name"]
                    child4["size"] = row["summativescore"]
                    child4_list.append(child4)
                child3["children"] = child4_list
                child3_list.append(child3)
            child2["children"] = child3_list
            child2_list.append(child2)
        child1["children"] = child2_list
        children.append(child1)
        
    data_json["children"] = children
    print("Data retrieval successfull")

    return jsonify(data_json)

@app.route('/leaflet')
def leaflet():
    return render_template("leaflet.html")

@app.route('/bonus')
def bonus():
    return render_template("bonus.html")

@app.route("/data_pop")
def data_pop():
    sqlite_connection = engine.connect()
    table = "NJ_population"
    query = "SELECT * from NJ_population"
    df = pd.read_sql(query, sqlite_connection)
    sqlite_connection.close()
    html_table = df.to_html(index=False, header=True, border=1, justify = 'left',classes="bg-light table table-striped table-bordered")
    results = html_table
    print("Data retrieval successfull")
    return render_template("data.html", info = results, table = table)

@app.route("/data_crime")
def data_crime():
    sqlite_connection = engine.connect()
    table = "NJ_crime"
    query = "SELECT * from NJ_crime"
    df = pd.read_sql(query, sqlite_connection)
    sqlite_connection.close()
    html_table = df.to_html(index=False, header=True, border=1, justify = 'left',classes="bg-light table table-striped table-bordered")
    results = html_table
    print("Data retrieval successfull")
    return render_template("data.html", info = results, table = table)

@app.route("/data_poverty")
def data_poverty():
    sqlite_connection = engine.connect()
    table = "NJ_poverty"
    query = "SELECT * from NJ_poverty"
    df = pd.read_sql(query, sqlite_connection)
    sqlite_connection.close()
    html_table = df.to_html(index=False, header=True, border=1, justify = 'left',classes="bg-light table table-striped table-bordered")
    results = html_table
    print("Data retrieval successfull")
    return render_template("data.html", info = results, table = table)

@app.route("/data_school")
def data_school():
    sqlite_connection = engine.connect()
    table = "NJ_school_rating"
    query = "SELECT * from NJ_school_rating"
    df = pd.read_sql(query, sqlite_connection)
    sqlite_connection.close()
    html_table = df.to_html(index=False, header=True, border=1, justify = 'left',classes="bg-light table table-striped table-bordered")
    results = html_table
    print("Data retrieval successfull")
    return render_template("data.html", info = results, table = table)

@app.route("/data_crime_detail")
def data_crime_detail():
    sqlite_connection = engine.connect()
    table = "NJ_crime_detail"
    query = "SELECT * from NJ_crime_detail"
    df = pd.read_sql(query, sqlite_connection)
    sqlite_connection.close()
    html_table = df.to_html(index=False, header=True, border=1, justify = 'left',classes="bg-light table table-striped table-bordered")
    results = html_table
    print("Data retrieval successfull")
    return render_template("data.html", info = results, table = table)

if __name__ == "__main__":
    app.run(debug = True)
