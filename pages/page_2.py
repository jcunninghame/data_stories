import datetime

import streamlit as st
import plost
import pandas as pd
import snowflake.connector as sn
from dotenv import load_dotenv
import os

st.markdown("# A Further Look")
st.sidebar.markdown("# Drilldown")

con = sn.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse=os.getenv('SNOWFLAKE_WH'),
    role=os.getenv('SNOWFLAKE_ROLE')
)
cs = con.cursor()
cs.execute("""SELECT PT.*, PB.MEMBER_COUNT, PB.PHARMACY_SPEND FROM TUVA_PROJECT_DEMO.PMPM.PMPM_TRENDS PT
              LEFT JOIN (SELECT CONCAT(LEFT(YEAR_MONTH, 4), '-', RIGHT(YEAR_MONTH, 2)) AS YEAR_MONTH, 
                         COUNT(*) AS MEMBER_COUNT,
                         SUM(PHARMACY_PAID) AS PHARMACY_SPEND 
                         FROM TUVA_PROJECT_DEMO.PMPM.PMPM_BUILDER
                         GROUP BY YEAR_MONTH) AS PB
              ON PT.YEAR_MONTH = PB.YEAR_MONTH;""")

pmpm_data = cs.fetch_pandas_all()
pmpm_data['YEAR_MONTH'] = pd.to_datetime(pmpm_data['YEAR_MONTH'], format='%Y-%m').dt.date
pmpm_data['PHARMACY_SPEND'] = pmpm_data['PHARMACY_SPEND'].astype(float)

cs.execute("""SELECT
                CONCAT(date_part(year, FIRST_DIAGNOSIS_DATE), '-', lpad(date_part(month, FIRST_DIAGNOSIS_DATE), 2, 0)) AS DIAGNOSIS_YEAR_MONTH,
                CONDITION,
                COUNT(*) AS CONDITION_CASES,
                AVG(LAST_DIAGNOSIS_DATE + 1 - FIRST_DIAGNOSIS_DATE) AS DIAGNOSIS_DURATION
              FROM TUVA_PROJECT_DEMO.CHRONIC_CONDITIONS.TUVA_CHRONIC_CONDITIONS_LONG
              GROUP BY 1,2
              ORDER BY 3 DESC;""")

cond_data = cs.fetch_pandas_all()
#cond_data['DIAGNOSIS_YEAR_MONTH'] = pd.to_datetime(cond_data['DIAGNOSIS_YEAR_MONTH'], format='%Y-%m').dt.date

cs.execute("""SELECT * FROM CLAIMS_DATA_PROFILING.DATES.DATE_SUMMARY
              WHERE YEAR_MONTH >= '201601' AND YEAR_MONTH <> 'Duplicate';""")
quality_data = cs.fetch_pandas_all()
quality_data['YEAR_MONTH'] = pd.to_datetime(quality_data['YEAR_MONTH'],
                                            format='%Y%m').dt.date + datetime.timedelta(days=1)
quality_data.dropna(axis=1, how='all', inplace=True)

st.markdown("### Date Summary")
sum_col1, sum_col2 = st.columns([1, 3])
with sum_col1:
    metric_options = [x for x in quality_data.columns if x != 'YEAR_MONTH']
    sum_metric = st.radio(label='Select Mertic for Summary Display',
                             options=metric_options)
with sum_col2:
    plost.time_hist(data=quality_data, date='YEAR_MONTH', x_unit='month', y_unit='year',
                    color=dict(field=sum_metric, type='quantitative'), aggregate='sum',
                    height=400, use_container_width=True)

st.divider()
st.markdown("### PMPM Breakdown and Pharmacy Spend Trends")
start_date, end_date = st.select_slider("Select date range for claims summary",
                                        options=pmpm_data['YEAR_MONTH'].sort_values(),
                                        value=(pmpm_data['YEAR_MONTH'].min(), pmpm_data['YEAR_MONTH'].max()))

filtered_pmpm_data = pmpm_data.loc[(pmpm_data['YEAR_MONTH'] >= start_date) & (pmpm_data['YEAR_MONTH'] <= end_date), :]
filtered_pmpm_data['Metric'] = 'Average PMPM'

pmpm_cats = ['INPATIENT_PMPM', 'OUTPATIENT_PMPM', 'OFFICE_VISIT_PMPM', 'ANCILLARY_PMPM', 'OTHER_PMPM']
grouped_pmpm = filtered_pmpm_data.groupby(by='Metric', as_index=False)[pmpm_cats].mean()

st.divider()
plost.bar_chart(data=grouped_pmpm, bar='Metric', value=pmpm_cats, stack='normalize',
                direction='horizontal', legend='top', title='Average PMPM Broken out by Category',
                height=200)
st.markdown("**Total Pharmacy Spend Over Claim Period**")
st.line_chart(data=filtered_pmpm_data, x='YEAR_MONTH', y='PHARMACY_SPEND')

st.divider()

st.markdown("**Top 5 Condition Diagnoses Over Claim Period**")
msk = (cond_data['DIAGNOSIS_YEAR_MONTH'] >= str(start_date)) & (cond_data['DIAGNOSIS_YEAR_MONTH'] <= str(end_date))
filtered_cond_data = cond_data.loc[msk, :]
top5_conditions = filtered_cond_data.groupby('CONDITION')['CONDITION_CASES'].sum().nlargest(5)
msk = filtered_cond_data['CONDITION'].isin(top5_conditions.index)
top5_filtered_cond = filtered_cond_data.loc[msk, :]

plost.line_chart(data=top5_filtered_cond,
                 x='DIAGNOSIS_YEAR_MONTH',
                 y='CONDITION_CASES',
                 color='CONDITION',
                 pan_zoom=None,
                 height=400)

con.close()
