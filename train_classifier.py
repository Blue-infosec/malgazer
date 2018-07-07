import sys
import argparse
import time
import os
import pandas as pd
import json
from library.utils import Utils
from library.ml import ML
from keras.wrappers.scikit_learn import KerasClassifier


pd.set_option('max_colwidth', 64)


def get_estimator_static(classifier_type, *args, **kwargs):
    """
    Returns a static estimator based on classifier type.

    :param classifier_type:  A valid classifier type.
    :param args:  Args to be passed to base constructor.
    :param kwargs:  Kwargs to be passed to the base constructor.
    :return:  The classifier
    """
    if classifier_type.lower() == 'svm':
        return ML.build_svm_static(*args, **kwargs)
    elif classifier_type.lower() == 'dt':
        return ML.build_dt_static(*args, **kwargs)
    elif classifier_type.lower() == 'nb':
        return ML.build_nb_static(*args, **kwargs)
    elif classifier_type.lower() == 'rf':
        return ML.build_rf_static(*args, **kwargs)
    elif classifier_type.lower() == 'knn':
        return ML.build_knn_static(*args, **kwargs)
    elif classifier_type.lower() == 'nc':
        return ML.build_nc_static(*args, **kwargs)
    elif classifier_type.lower() == 'adaboost':
        return ML.build_adaboost_static(*args, **kwargs)
    elif classifier_type.lower() == 'ovr':
        return ML.build_ovr_static(*args, **kwargs)
    elif classifier_type.lower() == 'ann':
        def create_model():
            return ML.build_ann_static(*args, **kwargs)
        return KerasClassifier(build_fn=create_model)
    elif classifier_type.lower() == 'cnn':
        def create_model():
            return ML.build_cnn_static(*args, **kwargs)
        return KerasClassifier(build_fn=create_model)
    else:
        return None


def get_estimator(classifier_type, ml, *args, **kwargs):
    """
    Returns an estimator based on classifier type.

    :param classifier_type:  A valid classifier type.
    :param ml:  The ml object to create an estimator.
    :param args:  Args to be passed to base constructor.
    :param kwargs:  Kwargs to be passed to the base constructor.
    :return:  The classifier
    """
    if classifier_type.lower() == 'svm':
        return ml.build_svm(*args, **kwargs)
    elif classifier_type.lower() == 'dt':
        return ml.build_dt(*args, **kwargs)
    elif classifier_type.lower() == 'nb':
        return ml.build_nb(*args, **kwargs)
    elif classifier_type.lower() == 'rf':
        return ml.build_rf(*args, **kwargs)
    elif classifier_type.lower() == 'knn':
        return ml.build_knn(*args, **kwargs)
    elif classifier_type.lower() == 'nc':
        return ml.build_nc(*args, **kwargs)
    elif classifier_type.lower() == 'adaboost':
        return ml.build_adaboost(*args, **kwargs)
    elif classifier_type.lower() == 'ovr':
        return ml.build_ovr(*args, **kwargs)
    elif classifier_type.lower() == 'ann':
        return ml.build_ann(*args, **kwargs)
    elif classifier_type.lower() == 'cnn':
        return ml.build_cnn(*args, **kwargs)
    else:
        return None


def main(arguments=None):
    # Argument parsing
    parser = argparse.ArgumentParser(
        description='Trains a malware classifier.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('ClassifierType',
                        help='The classifier type.  Valid values: '
                        'ann - Artifical Neural Network, cnn - Convolutional Neural Network, '
                        'dt - Decision Tree, svm - State Vector Machine, nb - Naive Bayes, '
                        'rf - Random Forest, knn - k-Nearest Neighbors, nc - Nearest Centroid, '
                        'adaboost - Adaboost (requires a base estimator), '
                        'ovr - OneVRest (requires a base estimator), '
                        'gridsearch - Grid search (requires a base estimator and does not save classifier)')
    parser.add_argument('FeatureType',
                        help='The feature type. Valid values: '
                        'rwe - Running Window Entropy, gist - GIST image features')
    parser.add_argument('DataDirectory',
                        help='The directory containing the feature files.')
    parser.add_argument("-t", "--test",
                        help="The percentage of samples used for testing (not valid for gridsearch or cross validation)."
                             "", type=float, default=0.1)
    parser.add_argument("-c", "--crossval",
                        help="The number of groups for cross validation.  Set to zero to disable cross validation.  "
                             "Cross validation will use all the samples if enabled.  "
                             "Not available for gridsearch.", type=int, default=0)
    parser.add_argument("-n", "--numclasses",
                        help="The number of classes in the training data."
                             "", type=int, default=6)
    parser.add_argument("-roc", "--roccurves", action='store_true',
                        help="Plot the ROC curves."
                             "", required=False)
    parser.add_argument("-rwew", "--rwewindowsize",
                        help="The window size of RWE to use as features."
                             "", type=int, default=256)
    parser.add_argument("-rwed", "--rwedatapoints",
                        help="The number of datapoints of RWE to use as features."
                             "", type=int, default=1024)
    parser.add_argument("-nnb", "--nnbatchsize",
                        help="The batch size used for training neural networks."
                             "", type=int, default=100)
    parser.add_argument("-nne", "--nnepochs",
                        help="The epochs used for training neural networks."
                             "", type=int, default=10)
    parser.add_argument("-ncs", "--ncshrink",
                        help="The nc shrink threshold."
                             "", type=float, default=0.2)
    parser.add_argument("-gt", "--gridsearchtype",
                        help="The type of the base estimator for gridsearch."
                             "", type=str, default='dt')
    parser.add_argument("-gp", "--gridsearchparams",
                        help="The params for the gridsearch.  This is a JSON string that will be accepted by "
                            "the GridsearchCV in scikit learn."
                             "", type=str, default='{}')
    parser.add_argument("-gj", "--gridsearchjobs",
                        help="The number of jobs for the gridsearch."
                             "", type=int, default=-1)
    parser.add_argument("-gc", "--gridsearchcv",
                        help="The number of cross validation groups for the gridsearch."
                             "", type=int, default=-1)
    parser.add_argument("-at", "--adaboosttype",
                        help="The type of the base estimator for adaboost."
                             "", type=str, default='dt')
    parser.add_argument("-an", "--adaboostnumestimators",
                        help="The number of estimators for adaboost."
                             "", type=int, default=20)
    parser.add_argument("-kn", "--knnneighbors",
                        help="The number of neighbors for knn."
                             "", type=int, default=1)
    parser.add_argument("-kj", "--knnjobs",
                        help="The number of jobs for knn."
                             "", type=int, default=-1)
    parser.add_argument("-ot", "--ovrtype",
                        help="The type of the base estimator for ovr."
                             "", type=str, default='dt')
    if isinstance(arguments, list):
        args = parser.parse_args(arguments)
    else:
        args = parser.parse_args()

    datadir = args.DataDirectory
    feature_type = args.FeatureType.lower()
    classifier_type = args.ClassifierType.lower()
    cross_fold_validation = args.crossval > 0
    cfv_groups = args.crossval
    generate_roc_curves = args.roccurves
    test_percent = args.test
    windowsize = args.rwewindowsize
    datapoints = args.rwedatapoints
    n_categories = args.numclasses
    batch_size = args.nnbatchsize
    epochs = args.nnepochs
    gridsearch_type = args.gridsearchtype.lower()
    gridsearch_params = json.loads(args.gridsearchparams)
    gridsearch_njobs = args.gridsearchjobs
    gridsearch_cv = args.gridsearchcv
    adaboost_type = args.adaboosttype
    adaboost_n_estimators = args.adaboostnumestimators
    adaboost_base_estimator = get_estimator_static(adaboost_type)
    knn_weights = 'distance'
    knn_neighbors = args.knnneighbors
    knn_n_jobs = args.knnjobs
    ovr_type = args.ovrtype.lower()
    ovr_base_estimator = get_estimator_static(ovr_type)
    nc_shrink_threshold = args.ncshrink

    if cross_fold_validation or classifier_type == 'gridsearch':
        test_percent = 0

    print("Loading data...")

    # Load data
    all_data, raw_data, classifications = Utils.load_features(datadir, feature_type, filterhashes=True,
                                                              windowsize=windowsize, datapoints=datapoints)
    print("\n")
    print("Testing: {0}%".format(test_percent*100))
    print("\n")

    # Assemble the final training data
    X = all_data.drop('classification', axis=1).values.copy()
    y = pd.DataFrame(all_data['classification']).values.copy()

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

    # List the data...
    ytr = ml.decode_classifications(y_train.tolist())
    yte = ml.decode_classifications(y_test.tolist())
    print("\n")
    print("======")
    print("Training Class Count: \n{0}".format(pd.DataFrame(ytr)[0].value_counts()))
    print("======")
    print("Testing Class Count: \n{0}".format(pd.DataFrame(yte)[0].value_counts()))
    print("======")
    print("\n")

    print("Begin training...")
    print("\n")
    if classifier_type.lower() == 'cnn':
        if cross_fold_validation is False:
            # Create the CNN
            classifier = ml.build_cnn(X_train, y_train)

            # Train the CNN
            start_time = time.time()
            classifier = ml.train(X_train, y_train, batch_size=batch_size, epochs=epochs, tensorboard=False)
            print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))
            print("\n")

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
            print("\n")

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
        Xt = X_train
        yt = y_train

        if gridsearch_type.lower() == 'ann':
            classifier = get_estimator_static(gridsearch_type.lower(), Xt, yt)
        elif gridsearch_type.lower() == 'cnn':
            classifier = get_estimator_static(gridsearch_type.lower(), Xt, yt)
        else:
            classifier = get_estimator_static(gridsearch_type.lower())

        classifier = ml.build_gridsearch(gridsearch_type=gridsearch_type, estimator=classifier,
                                         param_grid=gridsearch_params,
                                         cv=gridsearch_cv, n_jobs=gridsearch_njobs)
        start_time = time.time()

        classifier = ml.train(Xt, yt)
        print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))
        print("\n")

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
            classifier = get_estimator(classifier_type.lower(), ml, kernel='rbf')
        elif classifier_type.lower() == 'dt':
            classifier = get_estimator(classifier_type.lower(), ml, criterion='entropy')
        elif classifier_type.lower() == 'nb':
            classifier = get_estimator(classifier_type.lower(), ml)
        elif classifier_type.lower() == 'rf':
            classifier = get_estimator(classifier_type.lower(), ml, n_estimators=10, criterion='entropy')
        elif classifier_type.lower() == 'knn':
            classifier = get_estimator(classifier_type.lower(), ml, n_neighbors=knn_neighbors, weights=knn_weights, n_jobs=knn_n_jobs)
        elif classifier_type.lower() == 'nc':
            classifier = get_estimator(classifier_type.lower(), ml, shrink_threshold=nc_shrink_threshold)
        elif classifier_type.lower() == 'adaboost':
            classifier = get_estimator(classifier_type.lower(), ml, adaboost_type=adaboost_type, n_estimators=adaboost_n_estimators, base_estimator=adaboost_base_estimator, algorithm='SAMME')
        elif classifier_type.lower() == 'ovr':
            classifier = get_estimator(classifier_type.lower(), ml, ovr_type=ovr_type, estimator=ovr_base_estimator)

        start_time = time.time()
        if cross_fold_validation is False:
            classifier = ml.train(X_train, y_train)
            print("Training time {0:.6f} seconds".format(round(time.time() - start_time, 6)))
            print("\n")
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
    print("\n")
    if feature_type == 'rwe':
        path = os.path.join(datadir,
                            "classifiers_rwe_{0}_window_{1}_datapoints".format(windowsize, datapoints),
                            classifier_type.lower())
    else:
        path = os.path.join(datadir, "classifiers", classifier_type.lower())

    try:
        os.stat(path)
    except:
        os.makedirs(path)
    if classifier_type.lower() != 'gridsearch':
        print("Saving the classifier...")
        ml.save_classifier(path)
        print("Classifier saved to: {0}".format(path))
        print("\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)