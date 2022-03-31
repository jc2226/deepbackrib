# -*- coding: utf-8 -*-
"""DeepBackRib_for_all_readmit_df

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FQJyChDQ_nmnToawCfcTjrra-rL_gGaS
"""

import tensorflow as tf
tf.compat.v1.disable_v2_behavior() # <-- make sure to include this line if using tensorflow version >2.4
import tensorflow.keras.backend as K
import pandas as pd
import os
import random
import numpy as np
from numpy.random import seed
import math 
from datetime import datetime
from packaging import version
from tensorflow import keras
import time
from keras.callbacks import TensorBoard
from keras.models import Sequential
from keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.constraints import max_norm, unit_norm
from sklearn.model_selection import train_test_split
from sklearn.utils import class_weight
from tensorflow.keras.regularizers import l2

#access to google drive files
from google.colab import drive
drive.mount('/content/drive')

print(tf.__version__)

#Set seeds for reproducible results
seed(1)
tf.random.set_seed(2)

#specify path, upload file 
ROOT = '/content/drive/MyDrive/DeepBackRib/'
df = pd.read_csv(os.path.join(ROOT, 'dl_highvar_march7.csv'))
#print(df.index.size) #13443

#drop bottom and top 5th percentile of LOS and ISS before min max transform 
small_exclude = df.nsmallest(math.ceil(len(df.index)*0.025), 'LOS_atindex') 
large_exclude = df.nlargest(math.ceil(len(df.index)*0.025), 'LOS_atindex') 
df = df.drop(small_exclude.index)
df = df.drop(large_exclude.index)
small_exclude = df.nsmallest(math.ceil(len(df.index)*0.025), 'riss') 
large_exclude = df.nlargest(math.ceil(len(df.index)*0.025), 'riss') 
df = df.drop(small_exclude.index)
df = df.drop(large_exclude.index)

from sklearn.preprocessing import MinMaxScaler
#min max transform numeric variables
scaler = MinMaxScaler()
df[['AGE']]=scaler.fit_transform(df[["AGE"]])
df[['LOS_atindex']]=scaler.fit_transform(df[["LOS_atindex"]])
df[['riss']]=scaler.fit_transform(df[["riss"]])
df.head()

#check distribution of min max transformed numeric variables 
#df.hist(column="LOS_atindex") 
#df.hist(column="AGE")
df.hist(column="riss")

#one hot encode some variables 
df= pd.get_dummies(data = df, columns = ['PAY1', 'HOSP_BEDSIZE', 'HOSP_UR_TEACH']) #one_hot_encode 
df.index.size #10792

#PROPORTION OF OUTOUTCOME
df["any_ribfx_related_readmit"].value_counts() #~10% unweighted

def split_stratified_into_train_val_test(df_input, outcome='y',
                                         frac_train=0.6, frac_val=0.20, frac_test=0.20,
                                         random_state=5):
    '''
    Splits a Pandas dataframe into three subsets (train, val, and test)
    following fractional ratios provided by the user, where each subset is
    stratified by the values in a specific column (that is, each subset has
    the same relative frequency of the values in the column). It performs this
    splitting by running train_test_split() twice.

    Parameters
    ----------
    df_input : Pandas dataframe
        Input dataframe to be split.
    outcome : str
        The name of the column that will be used for stratification. Usually
        this column would be for the label.
    frac_train : float
    frac_val   : float
    frac_test  : float
        The ratios with which the dataframe will be split into train, val, and
        test data. The values should be expressed as float fractions and should
        sum to 1.0.
    random_state : int, None, or RandomStateInstance
        Value to be passed to train_test_split().

    Returns
    -------
    df_train, df_val, df_test :
        Dataframes containing the three splits.
    y_train, y_val, y_test:
        outcomes for train val and test sets
    '''

    if frac_train + frac_val + frac_test != 1.0:
        raise ValueError('fractions %f, %f, %f do not add up to 1.0' % \
                         (frac_train, frac_val, frac_test))

    if outcome not in df_input.columns:
        raise ValueError('%s is not a column in the dataframe' % (outcome))

    X = df_input.drop(outcome,axis=1) # drop outcome
    y = df_input[[outcome]] # Dataframe of just the column on which to stratify.

    # Split original dataframe into train and temp dataframes.
    df_train, df_temp, y_train, y_temp = train_test_split(X,
                                                          y,
                                                          stratify=y,
                                                          test_size=(1.0 - frac_train),
                                                          random_state=random_state)

    # Split the temp dataframe into val and test dataframes.
    relative_frac_test = frac_test / (frac_val + frac_test)
    df_val, df_test, y_val, y_test = train_test_split(df_temp,
                                                      y_temp,
                                                      stratify=y_temp,
                                                      test_size=relative_frac_test,
                                                      random_state=random_state)

    y_train=y_train.values
    y_train=y_train.flatten()
    
    y_val=y_val.values
    y_val=y_val.flatten()
    
    y_test=y_test.values
    y_test=y_test.flatten()
    
    assert len(df_input) == len(df_train) + len(df_val) + len(df_test)


    return df_train, df_val, df_test, y_train, y_val, y_test

#split dataset 
x_train, x_val, x_test, y_train, y_val, y_test= split_stratified_into_train_val_test(df,outcome="any_ribfx_related_readmit",frac_train=0.6, frac_val=0.2, frac_test=0.2, random_state=5)

print(f"X_train shape {x_train.shape}")
print(f"y_train shape {y_train.shape}")
print(f"X_val shape {x_val.shape}")
print(f"y_val shape {y_val.shape}")
print(f"X_test shape {x_test.shape}")
print(f"y_test shape {y_test.shape}")

from google.colab import files
#save NRD_VISITLINK of train, val, test sets 
train_nrd_visitlink=x_train["NRD_VISITLINK"]
train_nrd_visitlink.to_csv("train_nrd_visitlink.csv")
files.download("train_nrd_visitlink.csv")

val_nrd_visitlink=x_val["NRD_VISITLINK"]
val_nrd_visitlink.to_csv("val_nrd_visitlink.csv")
files.download("val_nrd_visitlink.csv")

test_nrd_visitlink=x_test["NRD_VISITLINK"]
test_nrd_visitlink.to_csv("test_nrd_visitlink.csv")
files.download("test_nrd_visitlink.csv")

#drop unwanted variables
x_train = x_train.drop(["Unnamed: 0", "NRD_VISITLINK"],axis=1)
x_val = x_val.drop(["Unnamed: 0", "NRD_VISITLINK"],axis=1)
x_test = x_test.drop(["Unnamed: 0", "NRD_VISITLINK"],axis=1)

#confirm no NA values
x_train.isnull().values.any()
x_val.isnull().values.any()
x_test.isnull().values.any()

#Tally 0 and 1 values. Double check good distribution across datasets
print("ADVERSE EVENT","|","NON_ADVERSE_EVENT")
print((y_train==1).sum(),"|",(y_train==0).sum())
print((y_val==1).sum(),"|",(y_val==0).sum())
print((y_test==1).sum(),"|",(y_test==0).sum())

x_test.head

#define class weights
class_weights = class_weight.compute_class_weight(class_weight='balanced',
                                                 classes=np.unique(y_train),
                                                 y=y_train)

class_weights = dict(zip(np.unique(y_train), class_weights))
class_weights
# class_weights {0: 0.5620659722222222, 1: 4.527972027972028}


NAME="model-{}".format(int(time.time()))

#callback object
tensorboard=TensorBoard(log_dir='logs/{}'.format(NAME))

model = Sequential()
model.add(Dense(16, activation='relu',kernel_regularizer=l2(0.001)))
model.add(Dropout(0.5))
model.add(BatchNormalization())
model.add(Dense(4, activation='relu',kernel_regularizer=l2(0.001)))
model.add(Dropout(0.5)) #don't make smaller 
model.add(BatchNormalization())
model.add(Dense(1, activation='sigmoid'))

# Define the Keras TensorBoard callback.
logdir="logs/fit/" + datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = keras.callbacks.TensorBoard(log_dir=logdir)

#optional: include early stopping if no improvement in validation loss after 10 epochs 
es = tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=10)

model.compile(optimizer= tf.keras.optimizers.Adam(), loss='binary_crossentropy', metrics=[tf.keras.metrics.Recall(thresholds=0.4), tf.keras.metrics.Precision(thresholds=0.4),"accuracy",tf.keras.metrics.AUC(),tf.keras.metrics.AUC(curve='PR')])
history=model.fit(x=np.array(x_train), y=np.array(y_train), validation_data=(np.array(x_val), np.array(y_val)), epochs=50,
                  class_weight=class_weights,callbacks=[es,tensorboard_callback])  #make sure to callback tensorboard

# Commented out IPython magic to ensure Python compatibility.
##TENSORBOARD VISUALIZATION ##
# %load_ext tensorboard
# %tensorboard --logdir logs

#CHOOSE DECISION THRESHOLD USING GHOST: https://pubs.acs.org/doi/10.1021/acs.jcim.1c00160
!pip install ghostml
import ghostml
from sklearn import metrics

# extract the positive prediction probabilities for the training set from the trained  model
train_probs = model.predict(x_train).flatten()

# Get prediction probabilities for the val set
val_probs = model.predict(x_val).flatten()


# optmize the threshold 
thresholds = np.round(np.arange(0.05,0.5,0.01),2)
threshold1 = ghostml.optimize_threshold_from_predictions(y_val, val_probs, thresholds, ThOpt_metrics = 'ROC')

threshold1

model.summary()
#PREDICT ON TEST DATASET.
y_score = model.predict(x_test)

#save great models
model.save("/content/drive/MyDrive/DeepBackRib/march_7_all_model")
#from keras.models import load_model

#model.save('model_all_readmit.h5')

# run reconstructed model 
#reconstructed_model = load_model("/content/drive/MyDrive/DeepBackRib/nov_18_all_model")

#
#reconstructed_model.fit(x=np.array(x_train), y=np.array(y_train), validation_data=(np.array(x_val), np.array(y_val)), epochs=50,
                #  class_weight=class_weights,callbacks=[es])

###PLOT PERFORMANCE##
import matplotlib.pyplot as plt 
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

#plot recall performance 
plt.plot(history.history['recall'])
plt.plot(history.history['val_recall'])
plt.title('model recall')
plt.ylabel('recall')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

from sklearn.metrics import roc_curve, average_precision_score, precision_recall_curve, auc, plot_precision_recall_curve
#precision recall curve
precision,recall,thresholds=precision_recall_curve(y_test, y_score)
auc_precision_recall=auc(recall,precision)
print(auc_precision_recall)
print(thresholds)

plt.plot(recall,precision)
plt.show()

def plot_precision_recall_vs_threshold(precisions, recalls, thresholds):
    """
    Modified from:
    Hands-On Machine learning with Scikit-Learn
    and TensorFlow; p.89
    """
    plt.figure(figsize=(8, 8))
    plt.title("Precision and Recall Scores as a function of the decision threshold")
    plt.plot(thresholds, precisions[:-1], "b--", label="Precision")
    plt.plot(thresholds, recalls[:-1], "g-", label="Recall")
    plt.ylabel("Score")
    plt.xlabel("Decision Threshold")
    plt.legend(loc='best')



plot_precision_recall_vs_threshold(precision,recall,thresholds)

result = result = model.evaluate(x_test, y_test, batch_size=320)
dict(zip(model.metrics_names, result))

"""MODEL INTERPRETABILITY"""

!pip install shap

import shap
#initialize js methods for visualization
shap.initjs()

shap.explainers._deep.deep_tf.op_handlers["AddV2"] = shap.explainers._deep.deep_tf.passthrough

# create an instance of the DeepSHAP which is called DeepExplainer

explainer_shap = shap.DeepExplainer(model=model,data=x_train)

#alternative for efficiency if want to look at sample of dataset
#background = x_train[np.random.choice(x_train.shape[0], 1000, replace=False)]
#explainer_shap = shap.DeepExplainer(model=model,data=background)

shap_values = explainer_shap.shap_values(X=np.array(x_train))

# get the ovearall mean contribution of each feature variable
shap.summary_plot(shap_values[0], x_train, feature_names=x_train.columns,max_display=15)

#global dependence plot
shap.dependence_plot("AGE", shap_values[0], x_train)
