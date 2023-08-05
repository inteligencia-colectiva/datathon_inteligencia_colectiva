import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.cloud import storage
from google.oauth2 import service_account
import numpy as np

st.title("Recommendation Engine")
st.markdown ('***')

#credencial_path = './azuredatathonic26723-0c14968ab1c8.json'
credencial_path = './datathon-intel-colectiva-30fea2af8c02.json'
client = storage.Client.from_service_account_json(credencial_path)
# Nombre del bucket y del archivo en GCS
bucket_name = 'ic_machine_learning'
archivo_nombre = 'recommendation_system/recommendation_system_category_matrix1000.csv'

# Descarga el archivo desde GCS
st.write("Loading category-product matrix....")
bucket = client.bucket(bucket_name)
blob = bucket.blob(archivo_nombre)
contenido = blob.download_as_text()

data = [line.split(',') for line in contenido.split('\n')]
column_names = data[0]
data = data[1:]

df_matrix_cat = pd.DataFrame(data, columns=column_names)
for col in df_matrix_cat.columns[1:]:
    df_matrix_cat[col] = df_matrix_cat[col].astype(float)
df_matrix_cat=df_matrix_cat.iloc[:-1]

credentials = service_account.Credentials.from_service_account_file(
    credencial_path)

client = bigquery.Client(credentials=credentials,
                         project="datathon-intel-colectiva")

st.write("Loading clients list....")

query = """
    SELECT asin,reviewerID,SAFE_CAST(overall AS FLOAT64) AS ranking
FROM `datathon-intel-colectiva.ml_data.reviews` WHERE asin in (SELECT asin FROM(SELECT COUNT(asin) as total, asin FROM `datathon-intel-colectiva.ml_data.reviews`
GROUP BY asin
ORDER by total DESC
LIMIT 1000)) AND
reviewerID in (SELECT reviewerID FROM(SELECT COUNT(reviewerID) as total, reviewerID FROM `datathon-intel-colectiva.ml_data.reviews`
GROUP BY reviewerID
ORDER by total DESC
LIMIT 1000))
"""

query_job = client.query(query)
df_most = query_job.to_dataframe()

# Lista de opciones para el menú desplegable
opciones = df_most["reviewerID"].to_list()

query2 = """
    SELECT asin, categoria FROM `datathon-intel-colectiva.ml_data.metadata_completa`,
UNNEST(category) AS categoria
WHERE asin in (SELECT DISTINCT asin FROM (SELECT asin,reviewerID,SAFE_CAST(overall AS FLOAT64) AS ranking
FROM `datathon-intel-colectiva.ml_data.reviews` WHERE asin in (SELECT asin FROM(SELECT COUNT(asin) as total, asin FROM `datathon-intel-colectiva.ml_data.reviews`
GROUP BY asin
ORDER by total DESC
LIMIT 1000)) AND
reviewerID in (SELECT reviewerID FROM(SELECT COUNT(reviewerID) as total, reviewerID FROM `datathon-intel-colectiva.ml_data.reviews`
GROUP BY reviewerID
ORDER by total DESC
LIMIT 1000))))
"""

query2_job = client.query(query2)
df_asinxcat = query2_job.to_dataframe()

df_categorias = df_asinxcat[["asin", "categoria"]]
categorias_unicas = list({cat for cat in df_categorias["categoria"]})
tupla_cat = [(j,cat) for j,cat in enumerate (categorias_unicas)]

# Widget selectbox para el menú desplegable
opcion_elegida = st.selectbox('Choose a Code Client:', opciones)
# Muestra la opción seleccionada
st.write('Chosen client :', opcion_elegida)
usuario = opcion_elegida

go=st.button("Recommend")

if go:

    st.write("Assembling client-product matrix....")

    df_usu= pd.DataFrame(df_matrix_cat["asin"])

    def see_stars(asin):
        if  (df_most[(df_most["asin"]==asin) & (df_most["reviewerID"]==usuario)].shape[0]) >0 :
            return pd.Series(df_most[(df_most["asin"]==asin) & (df_most["reviewerID"]==usuario)]["ranking"]).mean()
        else:
            return 0


    df_usu["ranking"]=df_usu["asin"].apply(lambda x : see_stars(x))

    st.write("Getting client vector profile....")

    user_profile = df_usu[["ranking"]].T.dot(df_matrix_cat[[str(j) for j,_ in tupla_cat]])
    if user_profile.iloc[0].sum() > 0:  
        user_profile.iloc[0]=user_profile.iloc[0]/user_profile.iloc[0].sum()
    else:
        pass

    #Recomendaciones
    st.write("Obtaining rankings....")
    asin_like = user_profile.dot(df_matrix_cat[[str(j) for j,_ in tupla_cat]].T)
    asin_like=asin_like.T
    def ubi_asin(index):
        return df_matrix_cat[["asin"]].iloc[index][0]

    asin_like["asin"]=asin_like.index.to_series().apply(lambda x : ubi_asin(x))
    asin_like["ranking"]=asin_like["ranking"].apply(lambda x : float(x))

    unknown = {asin for asin,user in zip(df_most["asin"],df_most["reviewerID"]) if user!= usuario }
    unknown = {asin for asin in unknown if asin in df_matrix_cat["asin"].to_list()}
    known = {asin for asin,user in zip(df_most["asin"],df_most["reviewerID"]) if user== usuario}
    unknown = {asin for asin in unknown if asin not in known}

    lis=[(asin,ranking) for asin,ranking in zip(asin_like["asin"],asin_like["ranking"]) if asin in unknown ]
    asin_like_=pd.DataFrame(lis,columns=["asin","ranking"])

    recomendation = asin_like_.nlargest(5, 'ranking')

    def desc(asin):
        query3 = "SELECT title,new_main_cat from `datathon-intel-colectiva.ml_data.metadata_completa` WHERE asin = '"
        query3 = query3 + asin + "'"
        query3_job = client.query(query3)
        lis_ = query3_job.to_dataframe()
        lis_ = lis_.values.tolist()
        title = lis_[0][0]
        main_cat = lis_[0][1]
        return title, main_cat

    recomendation["title"]=recomendation["asin"].apply(lambda x : desc(x)[0])
    recomendation["main_cat"]=recomendation["asin"].apply(lambda x : desc(x)[1])


    st.write(":heavy_minus_sign:" * 32)
    st.markdown("### Recommendation Results")
    st.write(recomendation)

    st.markdown("### Buyer History")
    bought=pd.DataFrame(known, columns=["asin"])
    bought["title"]=bought["asin"].apply(lambda x : desc(x)[0])
    bought["main_cat"]=bought["asin"].apply(lambda x : desc(x)[1])
    st.write(bought)
