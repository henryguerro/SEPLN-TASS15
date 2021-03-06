import xmlreader as xml
import utils as ut
import numpy as np
import BagOfWords as bow
import classifiers as clf
import sklearn.cross_validation as cv
import pandas as pd
import matplotlib.pyplot as plt
import classify_diagnosis as diagnose
import itertools


def printResults(accuracy, precision, recall, f_measure, name="Unknown"):
    print "Result of " + name + ":"
    print "Accuracy: ", sum(accuracy) / float(len(accuracy))
    print "Precision: ", sum(precision) / float(len(precision))
    print "Recall: ", sum(recall) / float(len(recall))
    print "F1-measure: ", sum(f_measure) / float(len(f_measure))


if __name__ == "__main__":

    xmlTrainFile = '../DATA/general-tweets-train-tagged.xml'
    tweets = xml.readXML(xmlTrainFile)

    tokenized_tweets = []
    for tweet in tweets:
        tokenized_tweets.append(ut.tokenize(tweet.content, tweet.polarity))

    tweets = []
    labels = []
    for tweet in tokenized_tweets:
        tweets.append(tweet['clean'])
        labels.append(tweet['class'])

    tweets = np.array(tweets)
    labels = np.array(labels)

    train_tweets, test_tweets, train_labels, test_labels = ut.crossValidation2(tweets, labels, 3)


    # train_tweets = np.hstack(train_tweets)
    dictionary, tweets_features, vectorizer = bow.bow(train_tweets, vec="tfidf")
    # dictionary, tweets_features, vectorizer = bow.bow(train_tweets, vec="count")
    '''
    Training different classifiers.
    '''
    print '\nTraining Classifiers:\n'
    # forest_cls, svm_cls, rbf_cls, ada_cls, lr_cls = clf.train_classifiers(tweets_features,train_labels)
    forest_cls, svm_cls, lr_cls, ada_cls = clf.train_classifiers(tweets_features, train_labels)
    '''
    Create results dataset from classifiers. Where each attribute is a classifier and each row corresponds to the
    classification of a tweet according to each classifier.
    '''

    print '\nCreating Train set for super classifier ... '
    test_tweet_trans = vectorizer.transform(test_tweets)
    test_tweet_trans = test_tweet_trans.toarray()

    # classifiers = (forest_cls, svm_cls, rbf_cls, ada_cls, lr_cls)
    classifiers = (forest_cls, svm_cls, lr_cls, ada_cls)
    train_results = clf.test_classifiers(test_tweet_trans, test_labels, classifiers)

    '''
    Train the super classifier on the test set
    '''

    xmlTestFile = '../DATA/general-tweets-test1k.xml'
    tweets = xml.readXMLTest(xmlTestFile)

    tokenized_tweets = []
    tweetids = []
    for tweet in tweets:
        tokenized_tweets.append(ut.tokenize(tweet.content, tweet.polarity))
        tweetids.append(tweet.id)

    tweets = []
    labels = []
    for tweet in tokenized_tweets:
        tweets.append(tweet['clean'])
        # labels.append(tweet['class'])

    tweets_SEPLN = np.array(tweets)
    # labels_SEPLN = np.array(labels)

    print '\nCreating Test set for super classifier ... '
    val_tweet_trans = vectorizer.transform(tweets_SEPLN)
    val_tweet_trans = val_tweet_trans.toarray()

    SEPLN_results = clf.test_classifiers(val_tweet_trans, 0, classifiers)

    '''
    Now we have a train_results and test_results. Lets train and test a super classifier
    '''
    print '\nTraining super classifier ... '
    super_clf = clf.rbf_classifier(train_results, test_labels)

    print '\nEvaluating Super classifier ... '
    rbf_results = super_clf.predict(SEPLN_results)
    # rbf_results, _, _, _, _ = clf.evaluateResults(super_clf, train_results, test_labels)
    # validation_labels,
    # estimator_name='Supper Classifier')
    import classify_diagnosis as cd

    lambdas = cd.weighted_voting_getlambdas(train_results, test_labels)
    w_results = cd.weighted_voting(SEPLN_results, lambdas)

    v_results = diagnose.voting(SEPLN_results)

    # polarity = np.array(['NONE', 'N+', 'N', 'NEU', 'P', 'P+'])
    polarity = np.array(['NONE', 'N', 'NEU', 'P'])
    w_results = polarity[w_results]
    df = np.vstack([tweetids, w_results])
    df = pd.DataFrame(df.T)

    df.to_csv('../output/results/1k/partition2_3/weighted_results_tf-idf.txt', sep='\t', index=False, header=False)


    # polarity = np.array(['NONE', 'N+', 'N', 'NEU', 'P', 'P+'])
    polarity = np.array(['NONE', 'N', 'NEU', 'P'])

    v_results = polarity[v_results]
    df = np.vstack([tweetids, v_results])
    df = pd.DataFrame(df.T)

    df.to_csv('../output/results/1k/partition2_3/voted_results_tf-idf.txt', sep='\t', index=False, header=False)

    # polarity = np.array(['NONE', 'N+', 'N', 'NEU', 'P', 'P+'])
    polarity = np.array(['NONE', 'N', 'NEU', 'P'])

    rbf_results = polarity[rbf_results]
    df = np.vstack([tweetids, rbf_results])
    df = pd.DataFrame(df.T)

    df.to_csv('../output/results/1k/partition2_3/rbf_results_tf-idf.txt', sep='\t', index=False, header=False)

