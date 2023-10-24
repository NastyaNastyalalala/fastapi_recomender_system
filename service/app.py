import os
import pandas as pd
from typing import List
from catboost import CatBoostClassifier
from fastapi import FastAPI
from service.schema import PostGet
from datetime import datetime
from sqlalchemy import create_engine
from loguru import logger


CHUNKSIZE = 200000
PG_URL = os.getenviron("PG_URL")
PG_PORT = os.getenviron("PG_PORT")
PG_SCHEMA = os.getenviron("PG_SCHEMA")
PG_LOGIN = os.getenviron("PG_LOGIN")
PG_PASSWORD = os.getenviron("PG_PASSWORD")


def batch_load_sql(query: str):

    engine = create_engine(
        f"postgresql://{PG_LOGIN}:{PG_PASSWORD}",
        f"{PG_URL}:{PG_PORT}/{PG_SCHEMA}"
    )
    conn = engine.connect().execution_options(stream_results=True)
    chunks = []
    for chunk_dataframe in pd.read_sql(query, conn, chunksize=CHUNKSIZE):
        chunks.append(chunk_dataframe)
    conn.close()
    return pd.concat(chunks, ignore_index=True)


def get_model_path(path: str) -> str:
    # correct path to load the model
    if os.environ.get("IS_LMS") == "1":  # We check where the code is executed in the LMS, or locally. A little magic
        MODEL_PATH = '/workdir/user_input/model'
    else:
        MODEL_PATH = path
    return MODEL_PATH


def load_features():
    # Unique records post_id, user_id where the like was made
    logger.info("loading liked posts")
    liked_posts_query = """
        SELECT distinct post_id, user_id
        FROM public.feed_data
        where action ='like'"""
    liked_posts = batch_load_sql(liked_posts_query)

    # Features by post based on tf-idf
    logger.info("loading posts features")
    posts_features = pd.read_sql(
        """SELECT * FROM public.posts_info_features""",

        con=f"postgresql://{PG_LOGIN}:{PG_PASSWORD}"
            f"{PG_URL}:{PG_PORT}/{PG_SCHEMA}"
    )

    # Features by user
    logger.info("loading user features")
    user_features = pd.read_sql(
        """SELECT * FROM public.user_data""",

        con=f"postgresql://{PG_LOGIN}:{PG_PASSWORD}"
            f"{PG_URL}:{PG_PORT}/{PG_SCHEMA}"
    )

    return [liked_posts, posts_features, user_features]


def load_models():
    # Catboost loading
    model_path = get_model_path("catboost_model")
    loaded_model = CatBoostClassifier()
    loaded_model.load_model(model_path)
    return loaded_model


def get_recommended_feed(id: int, time: datetime, limit: int):
    # Load features by user
    logger.info(f"user_id: {id}")
    logger.info("reading features")
    user_features = features[2].loc[features[2].user_id == id]
    user_features = user_features.drop('user_id', axis=1)

    # Load features by post
    logger.info("dropping columns")
    posts_features = features[1].drop(['index', 'text'], axis=1)
    content = features[1][['post_id', 'text', 'topic']]

    # Let's combine these features
    logger.info("zipping everything")
    add_user_features = dict(zip(user_features.columns, user_features.values[0]))
    logger.info("assigning everything")
    user_posts_features = posts_features.assign(**add_user_features)
    user_posts_features = user_posts_features.set_index('post_id')

    # Let's add information about the date of recommendations
    logger.info("add time info")
    user_posts_features['hour'] = time.hour
    user_posts_features['month'] = time.month

    # Let's generate predictions of the likelihood of liking a post for all posts
    logger.info('predicting')
    predicts = model.predict_proba(user_posts_features)[:, 1]
    user_posts_features["predicts"] = predicts

    # We will remove posts where the user has previously liked
    logger.info('deleting liked posts')
    liked_posts = features[0]
    liked_posts = liked_posts[liked_posts.user_id == id].post_id.values
    filtered_ = user_posts_features[~user_posts_features.index.isin(liked_posts)]

    recommended_posts = filtered_.sort_values('predicts')[-limit:].index  # Top 5 recommendation by likelihood of posts

    return [
        PostGet(**{
            "id": i,
            "text": content[content.post_id == i].text.values[0],
            "topic": content[content.post_id == i].topic.values[0]
        }) for i in recommended_posts
    ]


# When raising the service, put the model and features into the variables model, features
logger.info("loading model")
model = load_models()
logger.info("loading features")
features = load_features()
logger.info("service is up and running")

app = FastAPI() #create an instance of the class

@app.get("/post/recommendations/", response_model=List[PostGet])
def recommended_posts(id: int, 
                      time: datetime,
                      limit: int = 10) -> List[PostGet]:
    return get_recommended_feed(id, time, limit)













































