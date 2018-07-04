# Install the plaidml backend
#import plaidml.keras
#plaidml.keras.install_backend()

from library.utils import Utils
from library.ml import ML, column_or_1d
from sklearn.utils.validation import column_or_1d
import pandas as pd
import numpy as np
import time
import os
import pickle
import dill
from sklearn import tree
from keras.wrappers.scikit_learn import KerasClassifier
from sklearn.preprocessing import label_binarize


pd.set_option('max_colwidth', 64)

#
# Script actions
#
# Assemble the preprocessed data
assemble_preprocessed_data = False
# Build a classifier
build_classifier = True
classifier_type = 'dt'
feature_type = 'rwe'

#
# Calculate features
#
source_dir = '/Volumes/JONES/Focused Set May 2018/Binaries'

datapoints = 1024
windowsize = 256
number_of_jobs = 50
if feature_type == 'rwe':
    datadir = '/Volumes/JONES/Focused Set May 2018/RWE'
elif feature_type == 'gist':
    datadir = '/Volumes/JONES/Focused Set May 2018/GIST'
arguments = ['-w', str(windowsize), '-d', str(datapoints), '-j', str(number_of_jobs), source_dir, datadir]

# Neural Network params
batch_size = 100
epochs = 1
n_categories = 6

# Cross fold validation variables
cross_fold_validation = True
cfv_groups = 5
n_jobs = 10

# ROC Curves - only works for SciKit Learn models right now
generate_roc_curves = False

# Grid search params
gridsearch_type = 'ann'
gridsearch_params = {'epochs': [1, 2], 'batch_size': [100, 200]}
gridsearch_njobs = -1

# KNN params
knn_neighbors = 1
knn_weights = 'distance'

# Centroid params
shrink_threshold = 0.2

# Adaboost params
n_estimators = 200
base_estimator = ML.build_svm_static(kernel='rbf')

# OneVRest params
ovr_base_estimator = ML.build_svm_static(kernel='rbf')

# Set this to the percentage for test size,
# 0 makes the train and test set be the whole data set
test_percent = 0.9
# Make the whole data set for training if we are doing cross fold validation
# if cross_fold_validation is True or classifier_type.lower() == 'gridsearch':
#     test_percent = 0

# Put the data together and save hashes used for training
if assemble_preprocessed_data:
    # Load data
    all_data, raw_data, classifications = Utils.load_features(datadir, feature_type, windowsize=windowsize, datapoints=datapoints)

    # Pick 60k samples, 10k from each classification
    trimmed_data = all_data.groupby('classification').head(10000)
    # trimmed_data.to_csv(os.path.join(datadir, 'data.csv'))
    pd.DataFrame(trimmed_data.index).to_csv(os.path.join(datadir, 'hashes_60k.txt'), header=False, index=False)

    # Pull the hashes we care about
    hashes = pd.read_csv(os.path.join(datadir, 'hashes_60k.txt'), header=None).values[:,0]
    data = Utils.filter_hashes(all_data, hashes)
    data.to_csv(os.path.join(datadir, 'data.csv'))

# Build a classifier
if build_classifier:
    print("Loading data...")

    # Load data
    all_data, raw_data, classifications = Utils.load_features(datadir, feature_type, windowsize=windowsize, datapoints=datapoints)

    # Pull the hashes we care about
    hashes = pd.read_csv(os.path.join(datadir, 'hashes_60k.txt'), header=None).values[:, 0]
    data = Utils.filter_hashes(all_data, hashes)

    print("Test percent: {0}".format(test_percent))

    # Assemble the final training data
    X = data.drop('classification', axis=1).values.copy()
    y = pd.DataFrame(data['classification']).values.copy()

    # Make the classifier
    ml = ML(feature_type=feature_type, classifier_type=classifier_type, n_classes=n_categories, rwe_windowsize=windowsize, datapoints=datapoints)
    X, y = ml.preprocess_data(X, y)
    if test_percent > 0:
        X_train, X_test, y_train, y_test = ml.train_test_split(X, y, test_percent=test_percent)
    else:
        X_train = X
        y_train = y
        X_test = X
        y_test = y

    ytr = ml.decode_classifications(y_train.tolist())
    yte = ml.decode_classifications(y_test.tolist())

    print("Training Class Count: \n{0}".format(pd.DataFrame(ytr)[0].value_counts()))
    print("Testing Class Count: \n{0}".format(pd.DataFrame(yte)[0].value_counts()))

    print("Beginning training...")

    if classifier_type.lower() == 'cnn':
        if cross_fold_validation is False:
            # Create the CNN
            classifier = ml.build_cnn(X_train, y_train)

            # Train the CNN
            start_time = time.time()
            classifier = ml.train(X_train, y_train, batch_size=batch_size, epochs=epochs, tensorboard=False)
            print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))

            # Predict the results
            y_pred = ml.predict(X_test)

            # Making the Confusion Matrix
            accuracy, cm = ml.confusion_matrix(y_test, y_pred)

            print("Confusion Matrix:")
            print(cm)
            print("Accuracy:")
            print(accuracy)

            if generate_roc_curves:
                ml.plot_roc_curves(y_test, y_pred, n_categories)
        else:
            # Cross Fold Validation
            start_time = time.time()
            mean, variance, classifiers = ml.cross_fold_validation(X_train, y_train,
                                                                   batch_size=batch_size,
                                                                   epochs=epochs,
                                                                   cv=cfv_groups)
            print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))
            print("CFV Mean: {0}".format(mean))
            print("CFV Var: {0}".format(variance))

            if generate_roc_curves:
                for fold in range(cfv_groups):
                    ml.set_classifier_by_fold(fold+1)
                    y_test = ml.classifiers[fold+1]['y_test']
                    y_pred = ml.classifiers[fold+1]['y_pred']
                    ml.plot_roc_curves(y_test, y_pred, n_categories, fold+1)

    elif classifier_type.lower() == 'ann':
        if cross_fold_validation is False:
            # Create the ANN
            classifier = ml.build_ann(X_train, y_train)

            # Train the NN
            start_time = time.time()
            classifier = ml.train(X_train, y_train, batch_size=batch_size, epochs=epochs, tensorboard=False)
            print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))

            # Predict the results
            y_pred = ml.predict(X_test)

            # Making the Confusion Matrix
            accuracy, cm = ml.confusion_matrix(y_test, y_pred)

            print("Confusion Matrix:")
            print(cm)
            print("Accuracy:")
            print(accuracy)

            if generate_roc_curves:
                ml.plot_roc_curves(y_test, y_pred, n_categories)
        else:
            # Cross Fold Validation
            start_time = time.time()
            mean, variance, classifiers = ml.cross_fold_validation(X_train, y_train,
                                                                   batch_size=batch_size,
                                                                   epochs=epochs,
                                                                   cv=cfv_groups)
            print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))
            print("CFV Mean: {0}".format(mean))
            print("CFV Var: {0}".format(variance))

            if generate_roc_curves:
                for fold in range(cfv_groups):
                    ml.set_classifier_by_fold(fold+1)
                    y_test = ml.classifiers[fold+1]['y_test']
                    y_pred = ml.classifiers[fold+1]['y_pred']
                    ml.plot_roc_curves(y_test, y_pred, n_categories, fold+1)
    elif classifier_type.lower() == 'gridsearch':
        if gridsearch_type.lower() == 'ann':
            Xt = X_train
            yt = label_binarize(y_train.tolist(), classes=range(n_categories))
            def create_model():
                return ML.build_ann_static(Xt, yt)
            classifier = KerasClassifier(build_fn=create_model)
        elif gridsearch_type.lower() == 'cnn':
            Xt = np.expand_dims(X_train, axis=2)
            yt = label_binarize(y_train.tolist(), classes=range(n_categories))
            def create_model():
                return ML.build_cnn_static(Xt, yt)
            classifier = KerasClassifier(build_fn=create_model)
        elif gridsearch_type.lower() == 'dt':
            classifier = ml.build_dt()
            Xt = X_train
            yt = y_train
        elif gridsearch_type.lower() == 'svm':
            classifier = ml.build_svm()
            Xt = X_train
            yt = y_train
        elif gridsearch_type.lower() == 'nb':
            classifier = ml.build_nb()
            Xt = X_train
            yt = y_train
        elif gridsearch_type.lower() == 'rf':
            classifier = ml.build_rf()
            Xt = X_train
            yt = y_train
        elif gridsearch_type.lower() == 'knn':
            classifier = ml.build_knn()
            Xt = X_train
            yt = y_train
        elif gridsearch_type.lower() == 'nc':
            classifier = ml.build_nc()
            Xt = X_train
            yt = y_train
        elif gridsearch_type.lower() == 'adaboost':
            classifier = ml.build_adaboost()
            Xt = X_train
            yt = y_train
        elif gridsearch_type.lower() == 'ovr':
            classifier = ml.build_ovr()
            Xt = X_train
            yt = y_train

        classifier = ml.build_gridsearch(estimator=classifier,
                                         param_grid=gridsearch_params,
                                         cv=cfv_groups, n_jobs=gridsearch_njobs)
        start_time = time.time()

        classifier = ml.train(Xt, yt)
        print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))

        print("Best Score: {0}".format(classifier.best_score_))
        print("CV Results: {0}".format(classifier.cv_results_))
        print("Params: {0}".format(classifier.cv_results_['params']))
        print("Mean Test Score: {0}".format(classifier.cv_results_['mean_test_score']))
        print("Best Estimator: {0}".format(classifier.best_estimator_))
        best_param = classifier.cv_results_['params'][(classifier.cv_results_['mean_test_score'] == classifier.best_score_).argmax()]
        print("Best Params: {0}".format(best_param))
    else:
        # This area is for scikit learn models
        if classifier_type.lower() == 'svm':
            classifier = ml.build_svm(kernel='rbf')
        elif classifier_type.lower() == 'dt':
            classifier = ml.build_dt(criterion='entropy')
        elif classifier_type.lower() == 'nb':
            classifier = ml.build_nb()
        elif classifier_type.lower() == 'rf':
            classifier = ml.build_rf(n_estimators=10, criterion='entropy')
        elif classifier_type.lower() == 'knn':
            classifier = ml.build_knn(n_neighbors=knn_neighbors, weights=knn_weights, n_jobs=n_jobs)
        elif classifier_type.lower() == 'nc':
            classifier = ml.build_nc(shrink_threshold=shrink_threshold)
        elif classifier_type.lower() == 'adaboost':
            classifier = ml.build_adaboost(n_estimators=n_estimators, base_estimator=base_estimator, algorithm='SAMME')
        elif classifier_type.lower() == 'ovr':
            classifier = ml.build_ovr(ovr_base_estimator)

        start_time = time.time()
        if cross_fold_validation is False:
            classifier = ml.train(X_train, y_train)
            print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))
            y_pred = ml.predict(X_test)
            # probas = ml.classifier.predict_proba(X_test)

            # Making the Confusion Matrix
            accuracy, cm = ml.confusion_matrix(y_test, y_pred)

            print("Confusion Matrix:")
            print(cm)
            print("Accuracy:")
            print(accuracy)

            if generate_roc_curves:
                ml.plot_roc_curves(y_test, y_pred, n_categories)
        else:
            # Cross Fold Validation
            mean, variance, classifiers = ml.cross_fold_validation(X_train, y_train,
                                                                   cv=cfv_groups)
            print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))
            print("CFV Mean: {0}".format(mean))
            print("CFV Var: {0}".format(variance))

            if generate_roc_curves:
                for fold in range(cfv_groups):
                    ml.set_classifier_by_fold(fold+1)
                    y_test = ml.classifiers[fold+1]['y_test']
                    y_pred = ml.classifiers[fold+1]['y_pred']
                    ml.plot_roc_curves(y_test, y_pred, n_categories, fold+1)

    # Save the classifier
    if cross_fold_validation is False and classifier_type.lower() != 'gridsearch':
        print("Saving the classifier...")
        if feature_type == 'rwe':
            path = os.path.join(datadir,
                                 '{0}_window_{1}_datapoints'.format(windowsize, datapoints),
                                 classifier_type.lower())
        elif feature_type == 'gist':
            path = os.path.join(datadir, 'gist', classifier_type.lower())

        try:
            os.stat(path)
        except:
            os.makedirs(path)
        ml.save_classifier(path, "classifier")
        if classifier_type.lower() == 'dt':
            tree.export_graphviz(classifier, out_file=os.path.join(path, 'tree.dot'))
        if classifier_type.lower() != 'ann' and classifier_type.lower() != 'cnn':
            pickle.dump(ml, open(os.path.join(path, 'ml.pickle'), 'wb'))
            dill.dump(ml, open(os.path.join(path, 'ml.dill'), 'wb'))
