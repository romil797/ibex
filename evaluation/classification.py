import numpy as np
from numba import jit

## TODO add compilation
#@jit(nopython=True)
def prob2pred(probabilities):
    # get the number of entries and the number of classes
    nentries = probabilities.shape[0]
    predictions = np.zeros(nentries, dtype=np.uint8)

    # iterate through every entry and every 
    for ie in range(nentries):
        if probabilities[ie] > 0.5:
            predictions[ie] = 1
        else: 
            predictions[ie] = 0

    return predictions

#@jit(nopython=True)
def PrecisionAndRecall(ground_truth, predictions):
    # make sure there are an equal number of elements
    assert (ground_truth.shape == predictions.shape)

    # make sure that the data is binary
    assert (np.amax(ground_truth) <= 1 and np.amax(predictions) <= 1)
    assert (np.amin(ground_truth) >= 0 and np.amax(predictions) >= 0)

    # set all of the counters to zero
    (TP, FP, FN, TN) = (0, 0, 0, 0)

    # iterate through every entry
    for ie in range(predictions.size):
        truth = ground_truth[ie]
        prediction = predictions[ie]

        if truth and prediction:
            TP += 1
        elif not truth and prediction:
            FP += 1
        elif truth and not prediction:
            FN += 1
        else:
            TN += 1

    print
    print 'Positive Examples: ' + str(TP + FN)
    print 'Negative Examples: ' + str(FP + TN)
    print
    print '+--------------+----------------+'
    print '|%14s|%13s%3s|' % ('', 'Prediction', '')
    print '+--------------+----------------+'
    print '|%14s|%7s%7s  |' % ('', 'Merge', 'Split')
    print '|%8s%5s |%7d%7d  |' % ('', 'Merge', TP, FN)
    print '| %-13s|%7s%7s  |' % ('Truth', '', '')
    print '|%8s%5s |%7d%7d  |' % ('', 'Split', FP, TN) 
    print '+--------------+----------------+'
    print

    if not TP + FP == 0:
        print 'Precision: ' + str(float(TP) / float(TP + FP))
    else: 
        print 'Precision: N/A'
    if not TP + FN == 0:
        print 'Recall: ' + str(float(TP) / float(TP + FN))
    else:
        print 'Recall: N/A'
    print 'Accuracy: ' + str(float(TP + TN) / float(TP + FP + FN + TN))
    print
