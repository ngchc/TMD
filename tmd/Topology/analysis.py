'''
tmd Topology analysis algorithms implementation
'''

import numpy as np


def collapse(ph_list):
    '''Collapses a list of ph diagrams
       into a single instance for plotting.
    '''
    ph_tr = []
    for p in ph_list:
        for pi in p:
            ph_tr.append(list(pi))
    return ph_tr


def sort_ph(ph, reverse=True):
    """
    Sorts barcode according to decreasing length of bars.
    """
    ph_sort = []

    for p in ph:
        ph_sort.append([p[0], p[1], np.abs(p[0] - p[1])])

    ph_sort.sort(key=lambda x: x[2], reverse=reverse)

    return ph_sort


def load_file(filename, delimiter=' '):
    """Load PH file in a np.array
    """
    f = open(filename, 'r')

    ph = []

    for line in f:

        line = np.array(line.split(delimiter), dtype=np.float)
        ph.append(line)

    f.close()

    return np.array(ph)


def define_limits(phs_list):
    '''Returns the x-y coordinates limits (min, max)
    for a list of persistence diagrams
    '''
    ph = collapse(phs_list)
    xlims = [min(np.transpose(ph)[0]), max(np.transpose(ph)[0])]
    ylims = [min(np.transpose(ph)[1]), max(np.transpose(ph)[1])]

    return xlims, ylims


def persistence_image_data(ph, norm_factor=None, xlims=None, ylims=None):
    '''Create the data for the generation of the persistence image.
    If norm_factor is provided the data will be normalized based on this,
    otherwise they will be normalized to 1.
    If xlims, ylims are provided the data will be scaled accordingly.   
    '''
    from scipy import stats

    if xlims is None:
        xlims = [min(np.transpose(ph)[0]), max(np.transpose(ph)[0])]
    if ylims is None:
        ylims = [min(np.transpose(ph)[1]), max(np.transpose(ph)[1])]

    X, Y = np.mgrid[xlims[0]:xlims[1]:100j, ylims[0]:ylims[1]:100j]

    values = np.transpose(ph)
    kernel = stats.gaussian_kde(values)
    positions = np.vstack([X.ravel(), Y.ravel()])
    Z = np.reshape(kernel(positions).T, X.shape)

    if norm_factor is None:
        norm_factor = np.max(Z)

    return Z / norm_factor


def img_diff_data(Z1, Z2, norm=True):
    """Takes as input two images
       as exported from the gaussian kernel
       plotting function, and returns
       their absolute difference:
       diff(abs(Z1 - Z2))
    """
    if norm:
        Z1 = Z1 / Z1.max()
        Z2 = Z2 / Z2.max()

    return Z1 - Z2


def horizontal_hist(ph1, num_bins=100, min_bin=None, max_bin=None):
    """Calculate how many barcode lines are found in each bin.
    """
    import math

    if min_bin is None:
        min_bin = np.min(ph1)
    if max_bin is None:
        max_bin = np.max(ph1)

    bins = np.linspace(min_bin, max_bin, num_bins, dtype=float)

    binsize = (max_bin - min_bin) / (num_bins - 1.)

    results = np.zeros(num_bins - 1)

    for ph in ph1:

        ph_decompose = np.linspace(np.min(ph), np.max(ph),
                                   math.ceil((np.max(ph) - np.min(ph)) / binsize),
                                   dtype=float)

        bin_ph = np.histogram(ph_decompose,
                              bins=bins)[0]

        results = np.add(results, bin_ph)

    return bins, results


def step_hist(ph1):
    '''Calculate step distance of ph data'''
    from itertools import chain

    bins = np.unique(list(chain(*ph1)))

    results = np.zeros(len(bins) - 1)

    for ph in ph1:
        for it, _ in enumerate(bins[:-1]):
            if min(ph) <= bins[it + 1] and max(ph) > bins[it]:
                results[it] = results[it] + 1

    return bins, results


def step_dist(ph1, ph2, order=1):
    '''Calculate step distance difference between two ph'''
    from itertools import chain
    from numpy.linalg import norm

    bins1 = np.unique(list(chain(*ph1)))
    bins2 = np.unique(list(chain(*ph2)))

    bins = np.unique(np.append(bins1, bins2))

    results1 = np.zeros(len(bins) - 1)
    results2 = np.zeros(len(bins) - 1)

    for ph in ph1:
        for it, _ in enumerate(bins[:-1]):
            if min(ph) <= bins[it + 1] and max(ph) > bins[it]:
                results1[it] = results1[it] + 1

    for ph in ph2:
        for it, _ in enumerate(bins[:-1]):
            if min(ph) <= bins[it + 1] and max(ph) > bins[it]:
                results2[it] = results2[it] + 1

    return norm(np.abs(np.subtract(results1, results2)) * (bins[1:] + bins[:-1]) / 2, order)


def hist_distance(ph1, ph2, norm=1, bins=100):
    """Calculate distance between two ph diagrams.
       Distance definition:
    """
    _, data_1 = horizontal_hist(ph1, num_bins=bins)
    _, data_2 = horizontal_hist(ph2, num_bins=bins)

    return np.linalg.norm(np.abs(np.subtract(data_1, data_2)), norm)


def hist_distance_un(ph1, ph2, norm=1, bins=100):
    """Calculate unnormed distance between two ph diagrams.
    """
    maxb = np.max([np.max(ph1), np.max(ph2)])

    minb = np.min([np.min(ph1), np.min(ph2)])

    _, results1 = horizontal_hist(ph1, num_bins=bins, min_bin=minb,
                                  max_bin=maxb)

    _, results2 = horizontal_hist(ph2, num_bins=bins, min_bin=minb,
                                  max_bin=maxb)

    return np.linalg.norm(np.abs(np.subtract(results1, results2)), norm)


def get_total_length(ph):
    """Calculates the total length of a barcode
       by summing the length of each bar. This should
       be equivalent to the total length of the tree
       if the barcode represents path distances.
    """
    return sum([np.abs(p[1] - p[0]) for p in ph])


def get_image_diff(Z1, Z2):
    """Takes as input two images
       as exported from the gaussian kernel
       plotting function, and returns
       their absolute difference:
       diff(abs(Z1 - Z2))
    """
    img1 = Z1[0] / Z1[0].max()
    img2 = Z2[0] / Z2[0].max()

    diff = np.sum(np.abs(img2 - img1))

    # Normalize the difference to % of #pixels
    diff = diff / np.prod(np.shape(img1))

    return diff


def get_image_max_diff(Z1, Z2):
    """Takes as input two images
       as exported from the gaussian kernel
       plotting function, and returns
       their absolute difference:
       diff(abs(Z1 - Z2))
    """
    img1 = Z1[0] / Z1[0].max()
    img2 = Z2[0] / Z2[0].max()

    diff = np.max(np.abs(img2 - img1))

    return diff


def transform_to_length(ph, keep_side='end'):
    '''Transforms a persistence diagram into a
    (start_point, length) equivalent diagram or a
    (end, length) diagram depending on keep_side option.
    Note: the direction of the diagram will be lost!
    '''
    if keep_side == 'start':
        # keeps the start point and the length of the bar
        return [[min(i), np.abs(i[1] - i[0])] for i in ph]
    else:
        # keeps the end point and the length of the bar
        return [[max(i), np.abs(i[1] - i[0])] for i in ph]


def transform_from_length(ph, keep_side='end'):
    '''Transforms a persistence diagram into a
    (start_point, length) equivalent diagram or a
    (end, length) diagram depending on keep_side option.
    Note: the direction of the diagram will be lost!
    '''
    if keep_side == 'start':
        # keeps the start point and the length of the bar
        return [[i[0], i[1] - i[0]] for i in ph]
    else:
        # keeps the end point and the length of the bar
        return [[i[0] - i[1], i[0]] for i in ph]


def average_image(ph_list, xlims=None, ylims=None, norm_factor=None, **kwargs):
    '''Plots the gaussian kernel of a population of cells
       as an average of the ph diagrams that are given.
    '''
    imgs_list = [persistence_image_data(p, norm_factor=norm_factor,
                                        xlims=xlims, ylims=ylims)
                for p in ph_list]

    average_imgs = imgs_list[0]

    for im in imgs_list[1:]:
        average_imgs = np.add(average_imgs, im)

    average_imgs = average_imgs / len(imgs_list)

    return average_imgs


def _marriage_problem(women_preferences, men_preferences):
    '''Matches N women to M men so that max(M, N)
    are coupled to their preferred choice that is available
    See https://en.wikipedia.org/wiki/Stable_marriage_problem
    '''
    N = len(women_preferences)
    M = len(men_preferences)

    swapped = False

    if M > N:
        swap = women_preferences
        women_preferences = men_preferences
        men_preferences = swap
        N = len(women_preferences)
        M = len(men_preferences)
        swapped = True

    free_women = range(N)
    free_men = range(M)

    couples = {x: None for x in xrange(N)} # woman first, then current husband

    count = 0

    while len(free_men) > 0:
        m = free_men.pop()
        choice = men_preferences[m].pop(0)

        if choice in free_women:
            couples[choice] = m
            free_women.remove(choice)
        else:
            current = np.where(np.array(women_preferences)[choice] == couples[choice])[0][0]
            tobe = np.where(np.array(women_preferences)[choice] == m)[0][0]
            if  current < tobe:
                free_men.append(couples[choice])
                couples[choice] = m
            else:
                free_men.append(m)

    if swapped:
        return {couples[k]: k for k in couples}

    return couples


def symmetric(p):
    '''Returns the symmetric point of a PD point on the diagonal
    '''
    return [(p[0] + p[1]) / 2., (p[0] + p[1]) / 2]

def match_diagrams_marriage_probl(p1, p2, plot=False):
    '''Returns a list of matching components
    '''
    from scipy.spatial.distance import cdist
    if plot:
        import view
        fig, ax = view.common.get_figure(new_fig=True, subplot=111)

    p1_enhanced = p1 + [symmetric(i) for i in p2]
    p2_enhanced = p2 + [symmetric(i) for i in p1]

    D = cdist(p1_enhanced, p2_enhanced)

    first_distances = cdist(p1_enhanced, p2_enhanced)
    second_distances = cdist(p2_enhanced, p1_enhanced)

    first_pref = [np.argsort(k).tolist() for k in first_distances]
    second_pref = [np.argsort(k).tolist() for k in second_distances]

    indices = _marriage_problem(first_pref, second_pref)

    pairs = []

    for c in church:
        pair = [p1_enhanced[c], p2_enhanced[church[c]]]
        if plot:
            view.common.plt.scatter(pair[0][0], pair[0][1], color='r')
            view.common.plt.scatter(pair[1][0], pair[1][1], color='b')
            view.common.plt.plot(np.array(pair)[:,0], np.array(pair)[:,1], color='black')
        pairs.append(pair)

    total_length = np.sum([np.linalg.norm([i[0][0]-i[1][0], i[0][1]-i[1][1]]) for i in pairs])

    return pairs, total_length


def matching_munkres(p1, p2, plot=False):
    '''finds a matching based on munkress module.
    '''
    from scipy.spatial.distance import cdist
    import munkres
    import pylab as plt

    p1_enh = p1 + [symmetric(i) for i in p2]
    p2_enh = p2 + [symmetric(i) for i in p1]

    D = cdist(p1_enh, p2_enh)

    m = munkres.Munkres()
    indices = m.compute(D)

    if plot:
        fig = plt.figure()
        for i,j in indices:
           plt.plot((p1_enh[i][0], p2_enh[j][0]), (p1_enh[i][1], p2_enh[j][1]), color='black')
           plt.scatter(p1_enh[i][0], p1_enh[i][1], c='r')
           plt.scatter(p2_enh[j][0], p2_enh[j][1], c='b')

    D = cdist(p1_enh, p2_enh)
    ssum = 0
    for i,j in indices:
        ssum = ssum + D[i][j]

    return indices, ssum


