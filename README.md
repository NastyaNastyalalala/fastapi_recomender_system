# 🚀 Recommender system

This repository contains research and FastAPI service implementation of a recommendation system for posts on a social network.

## DATA Review
 
**Table**: `user_data`

Contains information about all users of the social network

| Field name | Overview |
| ------ | ------ |
| age |	User age (in profile) |
| city | User's city (in profile) |
| country |	User country (in profile) |
| exp_group | Experimental group: some encrypted category |
| gender |	User gender |
| user_id |	Unique user ID |
| os | Operating system of the device from which the social network is used |
| source | Did the user come to the app from organic traffic or from advertising? |

___

**Table**: `post_text_df`

Contains information about posts and a unique ID of each unit with its corresponding text and topic

| Field name | Overview |
| ------ | ------ |
| id | 	Unique post ID | 
| text | Text content of the post | 
| topic | Main topics | 
 
___

**Table**: `feed_data`

Contains a history of posts viewed for each user during the period under study.
Attention: The table is SOOO large. It is recommended not to load it completely, otherwise everything will fall

| Field name | Overview |
| ------ | ------ |
| timestamp | Time when the view was made | 
| user_id | ID of the user who viewed it | 
| post_id | id of the viewed post | 
| action | Action type: view or like | 
| target | 1 for views if a like was made almost immediately after viewing, otherwise 0. Like actions have a missing value.| 

## Brief Overview of the Files
### 1. requirements.txt
Before running code locally please install dependancies from requirements.txt

### 2. service/app.py
This endpoint should return the top limit posts by number of likes. 
More formally: you need to count the number of likes for each post, sort in descending order and display 
the first limit of post records (their id, text and topic).

### 3. service/schema.py
This script helps with data validation based on BaseModel from pydantic

### 4. service/catboost_model
Models are not retrained when using services. The code will import the already trained model and apply it

### 5. research/model_training_CB.ipynb
Training the model on Jupyter Hub and assessing its quality on the validation set

### 6. How to run the script

```sh
python ch.py
```
using this script we can check recommendations for any of the users


### Metrics: Hitrate@5 
It takes the value 1 if, among the 5 proposed recommendations, at least 1 
received a like from the user. Even if all 5 proposed posts are eventually rated by the user, the hitrate will still 
be equal to 1. The metric is binary! Otherwise, if none of the suggested posts were rated by the user, hitrate takes 
the value 0. This is the metric we want to maximize.

**!The set of users is fixed and no new ones will appear**

###Pipeline:
1. Loading data from the database into Jupyter Hub, reviewing the data.
2. Creation of features and training set.
3. Training the model on Jupyter Hub and assessing its quality on the validation set
4. Saving the model ->catboost_model
5. loading model -> 
   getting features for a model by user_id -> 
   predicting posts that will be liked -> 
   return response. 
