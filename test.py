
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
from sklearn.preprocessing import StandardScaler

user_data = pd.read_csv('user.csv')
artist_data = pd.read_csv('artist.csv')

temp_user = user_data.drop(columns=['id','song_name','Unnamed: 0'])
temp_artist = artist_data.drop(columns=['id','song_name','image','Unnamed: 0'])

scaler = StandardScaler()


df_user_norm = pd.DataFrame(scaler.fit_transform(temp_user),columns=temp_user.columns)
df_artist_norm = pd.DataFrame(scaler.fit_transform(temp_artist),columns=temp_artist.columns)


kmeans = KMeans(n_clusters=4)
kmeans.fit(df_user_norm)

centers = kmeans.cluster_centers_

cosine_similarities = []
for index,row in df_artist_norm.iterrows():
    row_vector = row.values
    cos_sim = max(cosine_similarity([row_vector],[center])[0][0] for center in centers)
    cosine_similarities.append(np.round((cos_sim+1)*50,0))
    

print(cosine_similarities)
    