import argparse
import os
import sys
import numpy as np
import struct

from swc import Skeleton
from scipy.spatial import KDTree

# add parent directory
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from utilities import dataIO, seg2gold



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('segmentation', type=str, help='filename for segmentation dataset')
    parser.add_argument('gold', type=str, help='filename for gold dataset')
    parser.add_argument('max_distance', type=int, help='maximum distance between two considered endpoints in nanometers')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='print progress (default: False)')

    args = parser.parse_args()

    # open the segmentation and gold files
    segmentation = dataIO.ReadH5File(args.segmentation, 'main')
    gold = dataIO.ReadH5File(args.gold, 'stack')

    # get filename prefix
    prefix = args.segmentation.split('/')[1].split('_')[0]

    # read in the meta data
    (zres, yres, xres) = segmentation.shape
    assert (segmentation.shape == gold.shape)
    (zsamp, ysamp, xsamp) = dataIO.ReadMeta(prefix)

    # create an array for all of the skeletons
    skeletons = []

    # read in all skeletons
    nendpoints = 0
    for label in np.unique(segmentation):
        skeleton_filename = 'skeletons/' + prefix + '/' + 'tree_' + str(label) + '.swc'

        # see if this skeleton exists
        if not os.path.isfile(skeleton_filename):
            continue

        # read the skeletons
        skeleton = Skeleton(prefix, label)
        nendpoints += len(skeleton.endpoints)

        # add to the list of skeletons
        skeletons.append(skeleton)

    # create a data array for the kdtree and mapping from endpoint to label
    data = np.zeros((nendpoints, 3), dtype=np.float32)
    endpoint_labels = np.zeros(nendpoints, dtype=np.uint64)

    index = 0
    for skeleton in skeletons:
        for endpoint in skeleton.endpoints:

            # set the x, y, and z coordinates for the skeleton
            data[index,0] = xsamp * endpoint.x
            data[index,1] = ysamp * endpoint.y
            data[index,2] = zsamp * endpoint.z

            # update the label mapping
            endpoint_labels[index] = skeleton.label

            index += 1

    # create a KDTree
    kdtree = KDTree(data)

    # find all pairs of neighbors within max_distance
    close_pairs = kdtree.query_ball_tree(kdtree, args.max_distance)


    # create an array of all boundary examples
    potential_merges = []

    # get all pairs of endpoints that should be considered
    for index_one, pairs in enumerate(close_pairs):
        for index_two in pairs:
            if (index_one > index_two): continue
            if endpoint_labels[index_one] == endpoint_labels[index_two]: continue

            potential_merges.append((index_one, index_two))

    seg2gold_mapping = seg2gold.seg2gold(segmentation, gold)

    output_filename = 'skeletons/' + prefix + '_merge_candidates.merge'

    with open(output_filename, 'wb') as fd:
        # write the number of potential merges
        fd.write(struct.pack('Q', len(potential_merges)))

        # find the center for all of the boundary examples
        for pair in potential_merges:
            index_one = pair[0]
            index_two = pair[1]

            # get the location for the two skeleton endpoints
            position_one = data[index_one,:]
            position_two = data[index_two,:]

            # find the middle point for this merge
            mid_point = (position_one + position_two) / 2

            # get the downsampled x, y, and z location
            xpoint = mid_point[0] / xsamp
            ypoint = mid_point[1] / ysamp
            zpoint = mid_point[2] / zsamp

            # get the label values
            label_one = endpoint_labels[index_one]
            label_two = endpoint_labels[index_two]

            # should these two segments merge
            ground_truth = (seg2gold_mapping[label_one] == seg2gold_mapping[label_two])

            # make sure the bounding box is contained within the global volume
            xradius = args.max_distance / xsamp
            yradius = args.max_distance / ysamp
            zradius = args.max_distance / zsamp

            # skip points whose bounding boxes extend too far
            if (xpoint - xradius < 0 or ypoint - yradius < 0 or zpoint - zradius < 0): continue
            if (xpoint + xradius > xres - 1 or ypoint + yradius > yres - 1 or zpoint + zradius > zres - 1): continue

            # create a string of relevant information
            fd.write(struct.pack('QQQQdddB', index_one, index_two, label_one, label_two, xpoint, ypoint, zpoint, ground_truth))


if __name__ == '__main__':
    main()    
