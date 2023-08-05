import streamlit as st

st.title("Recommendation Engine")
st.markdown ('***')

st.markdown (''' The content-based recommendation algorithm is a method
              rooted in suggesting items to customers based on the similarity
              between those items and those valued by the customer on a star 
             rating scale. A higher star rating signifies a more favorable 
             evaluation, leading to stronger recommendations. The initial 
             step involves constructing the customer's profile through a 
             multidimensional vector. Subsequently, items are encoded, with 
             item categories serving as sets of features. Further, unrated 
             items are encoded to determine the most recommended items. 
             This determination is achieved through a dot product multiplication
              between the user's profile vector and the matrix of candidate 
             items.''')


st.markdown('''For this case, only the top 1000 customers who provide the most
          opinions have been considered, along with the 1000 most highly rated
          items. This approach aims to accommodate the limitations of the 
         Streamlit platform, which has a specific threshold.''')

