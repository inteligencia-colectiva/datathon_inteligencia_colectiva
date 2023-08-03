import streamlit as st
from transformers import pipeline
import base64
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
import matplotlib.pyplot as plt
from matplotlib import style
from wordcloud import WordCloud
import numpy as np
import pandas as pd

st.title("Stars & Sentiment Analisys")
st.markdown ('***')

choice=st.radio("Make a choice :", ("Prediction of a text", "Prediction of a file"))

if choice=="Prediction of a text" :
    text = st.text_input("Enter your text here")
    st.write("Texto ingresado:", text)
    if text =="" or len(text)<2 or text.isdigit():
        st.error("The text must be unless a word of two letters",icon="🚨")
    else:
        pipe = pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")
        results = pipe(text)
        print(results[0]["label"])
        if results[0]["label"]== '5 stars' or results[0]["label"]== '4 stars':
            sentiment = "Positive"
        else:
            if results[0]["label"]== '1 star' or results[0]["label"]== '2 stars':
                sentiment = "Negative"
            else:
                sentiment = "Neutral"

        st.write("Label : ",results[0]["label"], " - ",sentiment)
        st.write("Score : ",results[0]["score"])
        
else:
    
    uploaded_file = st.file_uploader("Choose your csv of comments")
    st.write( "Do not forget to call 'text' on the column to analyze.")
    
    if uploaded_file is not None:
        if uploaded_file.name[-4:]==".csv":
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
            exist_text=[col.lower() for col in df.columns if col.lower()=="text"]
            if len(exist_text)>0 :
                go=st.button("Predict")
                down = st.checkbox("Download Predictions")
                if go:
                    tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
                    model = AutoModelForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
                    
                    def translate_sentiment(star):
                        if star>=4:
                            return "Positive"
                        else:
                            if star==3:
                                return "Neutral"
                            else:
                                if star <3:
                                    return "Negative"
                                else:
                                    pass
                                        
                    def predict_stars(text):

                        encoded_input = tokenizer(text, return_tensors='pt')
                        output = model(**encoded_input)
                        scores = output[0][0].detach().numpy()
                        scores = softmax(scores)
                        winner= max(scores)
                        if scores[0]==winner:
                            return 1
                        else:
                            if scores[1]==winner:
                                return 2
                            else:
                                if scores[2]==winner:
                                    return 3
                                else:
                                    if scores[3]==winner:
                                        return 4
                                    else:
                                        return 5
                    
                    try:
                        st.spinner(text="In progress...")
                        df["Prediction_stars"]=df["text"].apply(lambda x :predict_stars(x))
                        df["Prediction_sentiment"]=df["Prediction_stars"].apply(lambda x : translate_sentiment(x))
                    
                        st.write(":heavy_minus_sign:" * 32)
                        st.markdown("### Prediction Results")

                        fig, (ax2,ax3) = plt.subplots(1,2,figsize=(15,5))
                        colors=("yellowgreen","red","gold")
                        wp={"linewidth":2,"edgecolor":"black"}
                        tags= df["Prediction_sentiment"].value_counts()
                        orden=tags.index
                        if len(df["Prediction_sentiment"].unique())==2:
                            explode = (0.1,0.1)
                        else:
                            explode = (0.1,0.1,0.1)

                        ax2.pie(x=tags,explode=explode,colors=colors,labels=tags.index,
                                    autopct='%1.1f%%',shadow=True,startangle=90,wedgeprops= wp)
                        ax2.set_title("Distribution of Sentiments based in Stars")

                        negative=df[df["Prediction_sentiment"]=="Negative"]
                        text_neg= " ".join ([word for word in negative["text"]])
                        wordcloud= WordCloud(max_words=500,width=1600,height=800).generate(text_neg)
                        ax3.imshow(wordcloud,interpolation="bilinear")
                        ax3.axis("off")
                        ax3.set_title("Negative Comments", fontsize=19)

                        st.pyplot(fig)
                        data=df[["text","Prediction_stars","Prediction_sentiment"]]
                        st.write(data)

                                        
                        if down:
                            
                            csv = data.to_csv(index=False)
                            b64 = base64.b64encode(csv.encode()).decode()  # encode CSV file as base64
                            href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">Download CSV file</a>'
                            st.markdown(href, unsafe_allow_html=True)
                        else:
                            pass
                    
                    except Exception as e:
                        st.error("Token indices sequence length is longer than the specified maximum sequence length for this model (must be less than 512)",icon="🚨")
                        print(f"Error al procesar : {e}")
                    
                                        
                else:
                    pass

            else:
                st.error ("Column named 'text' does not exist",icon="🚨")
        else:
            st.error("File must be a CSV",icon="🚨")

    else:
        pass