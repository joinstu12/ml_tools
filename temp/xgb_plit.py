import numpy as np
import pandas as pd
from sklearn import svm,grid_search
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.optimizers import Adadelta
from keras.layers.normalization import BatchNormalization
import xgboost as xgb
import ml_metrics as metrics
class NN:
    #I made a small wrapper for the Keras model to make it more scikit-learn like
    #I think they have something like this built in already, oh well
    #See http://keras.io/ for parameter options
    def __init__(self, inputShape, layers, dropout = [], activation = 'relu', init = 'uniform', loss = 'rmse', optimizer = 'adadelta', nb_epochs = 50, batch_size = 32, verbose = 1):

        model = Sequential()
        for i in range(len(layers)):
            if i == 0:
                print ("Input shape: " + str(inputShape))
                print ("Adding Layer " + str(i) + ": " + str(layers[i]))
                model.add(Dense(layers[i], input_dim = inputShape, init = init))
            else:
                print ("Adding Layer " + str(i) + ": " + str(layers[i]))
                model.add(Dense(layers[i], init = init))
            print ("Adding " + activation + " layer")
            model.add(Activation(activation))
            model.add(BatchNormalization())
            if len(dropout) > i:
                print ("Adding " + str(dropout[i]) + " dropout")
                model.add(Dropout(dropout[i]))
        model.add(Dense(1, init = init)) #End in a single output node for regression style output
        model.compile(loss=loss, optimizer=optimizer)
        
        self.model = model
        self.nb_epochs = nb_epochs
        self.batch_size = batch_size
        self.verbose = verbose

    def fit(self, X, y): 
        self.model.fit(X.values, y.values, nb_epoch=self.nb_epochs, batch_size=self.batch_size, verbose = self.verbose)
        
    def predict(self, X, batch_size = 128, verbose = 1):
        return self.model.predict(X.values, batch_size = batch_size, verbose = verbose)

class pdStandardScaler:
    #Applies the sklearn StandardScaler to pandas dataframes
    def __init__(self):
        from sklearn.preprocessing import StandardScaler
        self.StandardScaler = StandardScaler()
    def fit(self, df):
        self.StandardScaler.fit(df)
    def transform(self, df):
        df = pd.DataFrame(self.StandardScaler.transform(df), columns=df.columns)
        return df
    def fit_transform(self, df):
        df = pd.DataFrame(self.StandardScaler.fit_transform(df), columns=df.columns)
        return df
        
def getDummiesInplace(columnList, train, test = None):
    #Takes in a list of column names and one or two pandas dataframes
    #One-hot encodes all indicated columns inplace
    columns = []
    
    if test is not None:
        df = pd.concat([train,test], axis= 0)
    else:
        df = train
        
    for columnName in df.columns:
        index = df.columns.get_loc(columnName)
        if columnName in columnList:
            dummies = pd.get_dummies(df.ix[:,index], prefix = columnName, prefix_sep = ".")
            columns.append(dummies)
        else:
			print columnName+"\n"
			#print df.ix[:,index]
			columns.append(df.ix[:,index].to_frame())
    #print columns[0]
    df = pd.concat(columns, axis = 1)
    
    if test is not None:
        train = df[:train.shape[0]]
        test = df[train.shape[0]:]
        return train, test
    else:
        train = df
        return train
        
def pdFillNAN(df, strategy = "mean"):
    #Fills empty values with either the mean value of each feature, or an indicated number
    if strategy == "mean":
        return df.fillna(df.mean())
    elif type(strategy) == int:
        return df.fillna(strategy)
        
def make_dataset(useDummies = True, fillNANStrategy = "mean", useNormalization = True):
    data_dir = "input/"
    train = pd.read_csv(data_dir + 'train.csv')
    test = pd.read_csv(data_dir + 'test.csv')
    train.reindex(np.random.permutation(train.index))
    labels = train["Response"]
    train.drop(labels = "Id", axis = 1, inplace = True)
    train.drop(labels = "Response", axis = 1, inplace = True)
    test.drop(labels = "Id", axis = 1, inplace = True)
    
    categoricalVariables = ["Product_Info_1", "Product_Info_2", "Product_Info_3", "Product_Info_5", "Product_Info_6", "Product_Info_7", "Employment_Info_2", "Employment_Info_3", "Employment_Info_5", "InsuredInfo_1", "InsuredInfo_2", "InsuredInfo_3", "InsuredInfo_4", "InsuredInfo_5", "InsuredInfo_6", "InsuredInfo_7", "Insurance_History_1", "Insurance_History_2", "Insurance_History_3", "Insurance_History_4", "Insurance_History_7", "Insurance_History_8", "Insurance_History_9", "Family_Hist_1", "Medical_History_2", "Medical_History_3", "Medical_History_4", "Medical_History_5", "Medical_History_6", "Medical_History_7", "Medical_History_8", "Medical_History_9", "Medical_History_10", "Medical_History_11", "Medical_History_12", "Medical_History_13", "Medical_History_14", "Medical_History_16", "Medical_History_17", "Medical_History_18", "Medical_History_19", "Medical_History_20", "Medical_History_21", "Medical_History_22", "Medical_History_23", "Medical_History_25", "Medical_History_26", "Medical_History_27", "Medical_History_28", "Medical_History_29", "Medical_History_30", "Medical_History_31", "Medical_History_33", "Medical_History_34", "Medical_History_35", "Medical_History_36", "Medical_History_37", "Medical_History_38", "Medical_History_39", "Medical_History_40", "Medical_History_41"]

    if useDummies == True:
        print ("Generating dummies...")
        train, test = getDummiesInplace(categoricalVariables, train, test)
    valid = train[43000:]
    train = train[0:43000]
    valid_labels = labels[43000:]
    labels = labels[0:43000]
    if fillNANStrategy is not None:
        print ("Filling in missing values...")
        train = pdFillNAN(train, fillNANStrategy)
        valid = pdFillNAN(valid,fillNANStrategy)
        test = pdFillNAN(test, fillNANStrategy)

    if useNormalization == True:
        print ("Scaling...")
        scaler = pdStandardScaler()
        train = scaler.fit_transform(train)
        valid = scaler.transform(valid)
        test = scaler.transform(test)
    
    return train, test, labels , valid , valid_labels
def ensemble(train,test,labels,numModel):
	prediction = None
	for i in range(numModel):
		clf = NN(inputShape=train.shape[1],layers=[128],dropout=[0.5],loss='mae',optimizer='adadelta',init='glorot_normal',nb_epochs=10)
		clf.fit(train,labels)
		if i == 0:
			prediction = clf.predict(test)
		else:
			pred = clf.predict(test)
			for j in range(len(pred)):
				prediction[j] += pred[j]
	for i in range(len(prediction)):
		prediction[i] = prediction[i]/numModel
	return prediction
		
print ("Creating dataset...") 
train, test, labels , valid,valid_labels = make_dataset(useDummies = True, fillNANStrategy = "mean", useNormalization = True)

train_data = train.as_matrix()
test_data = test.as_matrix()
labels_data = labels.as_matrix()    
valid_data = valid.as_matrix()
valid_label = valid_labels.as_matrix()
dtrain = xgb.DMatrix(train_data,label=labels_data,missing=-999.0)
dtest = xgb.DMatrix(test_data)
dvalid = xgb.DMatrix(valid_data,label=valid_label)
param = {'bst:max_depth':6,'bst:eta':1,'silent':1,'objective':'reg:linear'}
param['nthread'] = 4
evallist = [(dvalid,'eval'),(dtrain,'train')]
plst = param.items()
bst = xgb.train(plst,dtrain,500,evallist,early_stopping_rounds=10)
#bst.train(plst,dtrain,1,evallist)
pred = bst.predict(dtest)

#clf = NN(inputShape = train.shape[1], layers = [128], dropout = [0.5], loss='mae', optimizer = 'adadelta', init = 'glorot_normal', nb_epochs = 1)
'''
#parameters = {'kernel':('linear','rbf'),'C':[1,10]}
#svr = svm.SVC()
#clf_svr = grid_search.GridSearchCV(svr,parameters)
print ("Training model...")
clf.fit(train, labels)
#clf_svr.fit(train,labels)

print ("Making predictions...")
pred = clf.predict(test)
'''
#score = 0.00001
#for i in range(15):
#    clf.fit(train,labels)
valid_pred = bst.predict(dvalid)
print "valid:"
#    score_last = score
print metrics.quadratic_weighted_kappa(valid_labels,valid_pred)
#    print score
#    if score/score_last < 1.011:
#        break
#pred = clf.predict(test)
#pred = ensemble(train,test,labels,5)
predClipped = np.clip(np.round(pred), 1, 8).astype(int) #Make the submissions within the accepted range

submission = pd.read_csv('input/sample_submission.csv')
submission["Response"] = predClipped
submission.to_csv('xgboost.csv', index=False)
