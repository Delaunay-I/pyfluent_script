import joblib
import numpy as np
import pandas as pd


def data_cleanser(data_df):
    dmd_df_new = data_df.copy()

    # Adding new features
    sig_list = np.array(['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'])
    num = np.arange(0,8)

    for i in num:
        col_name = sig_list[i+1] + '_' + sig_list[i]
        dmd_df_new.insert(loc=int(i+1), 
                         column=col_name,
                         value=dmd_df_new[sig_list[i+1]]/dmd_df_new[sig_list[i]])
        
    # Scaling DMD mode residuals based on the first singular value
    res_list = np.array(['res1', 'res2', 'res3', 'res4', 'res5', 'res6', 'res7', 'res8', 'res9'])
    # replace infs with a large positive number
    dmd_df_new.replace([np.inf, -np.inf], 1e+200, inplace=True)
    for item in res_list:
        # log-scale the residaul values
        dmd_df_new[item] = dmd_df_new[item] + 1e-200
        dmd_df_new[item] = np.log(dmd_df_new[item])
        dmd_df_new[item] = dmd_df_new[item]/dmd_df_new['s1']

    # Removing unnecessary features    
    dmd_df_new = dmd_df_new.drop(sig_list[1:], axis=1)
    
    return dmd_df_new


def ML_proba(list):

    column_names = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9',
                    'amp1', 'amp2', 'amp3', 'amp4', 'amp5', 'amp6', 'amp7', 'amp8', 'amp9',
                    'eig1', 'eig2', 'eig3', 'eig4', 'eig5', 'eig6', 'eig7', 'eig8', 'eig9',
                    'eng1', 'eng2', 'eng3', 'eng4', 'eng5', 'eng6', 'eng7', 'eng8', 'eng9',
                    'res1', 'res2', 'res3', 'res4', 'res5', 'res6', 'res7', 'res8', 'res9']

    df = pd.DataFrame(data = [list],
                      columns = column_names)
    df = data_cleanser(df)
    print(df.shape)

    # Loading the trained RandomForest model
    # clf = joblib.load("DMD_ML_v02.joblib")
    clf = joblib.load("./ML_xgb.joblib")
    # Getting the number of features required for this model
    # n_input_feats = clf.named_steps['randomforestclassifier'].n_features_in_
    n_input_feats = clf.named_steps['xgbclassifier'].n_features_in_


    # Proccessing data
    X = df.values

    assert X.shape == (1, n_input_feats), f"number of input variables/input formatting is not correct. {X.shape}"
    prediction = clf.predict_proba(X)

    # In the predicted probability, the first element is probability of effective update,
    # The second one is the probability of non-effective update
    # We are returning the effectiveness probability
    return prediction[0,0]


