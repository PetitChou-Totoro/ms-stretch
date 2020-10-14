"""
This plot shows the final output of MSNoise.


.. include:: clickhelp/msnoise-plot-dvv.rst


Example:

``msnoise plot dvv`` will plot all defaults:

.. image:: .static/dvv.png

"""

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

from matplotlib.dates import DateFormatter
from matplotlib.dates import MonthLocator

from msnoise.api import *
from ..datautilities import get_dvv, get_filter_info, nicen_up_pairs


def main(mov_stack=10, components='ZZ', filterid='1', pairs=None,
         forcing='prec', ask=False, type='points', show=True, outfile=None):

    db = connect()

    start, end, datelist = build_movstack_datelist(db)

    filterids, lows, highs, minlags, endlags = get_filter_info(filterid)
    pairs, nice_pairs = nicen_up_pairs(pairs)

    if components.count(","):
        components = components.split(",")
    else:
        components = [components, ]

    #Plot only one move_stack with precipitation data
    gs = gridspec.GridSpec(2, 1)
    fig = plt.figure(figsize=(12, 9))
    plt.subplots_adjust(bottom=0.06, hspace=0.3)
    first_plot = True
    filter_len = len(filterids)
    for i, filterid in enumerate(filterids):
        dflist = []
        for pair in pairs:
            dvv_data = get_dvv(mov_stack=mov_stack, comps=comps,
                               filterid=filterid, pairs=pair)
            dflist.append(dvv_data)

        # Plot dvv mean and median or multiple dvv
        if first_plot:
            ax = plt.subplot(gs[0])
            first_plot = False

        # TODO: Maybe check for same filter, so that label can be shortened
        if "all" in pairs and filter_len == 1:
            tmp = dflist[0]["mean"]
            plt.plot(tmp.index, tmp.values, ".", markersize=11, label="mean")
            tmp = dflist[0]["median"]
            plt.plot(tmp.index, tmp.values, ".", markersize=11, label="median")
        elif "all" in pairs and filter_len > 1:
            # TODO: Maybe add option to choose mean or median
            tmp = dflist[0]["mean"]
            label = "Filter %i, %i-%is" % (int(filter), minlags[i], endlags[i])
            plt.plot(tmp.index, tmp.values, ".", markersize=11, label=label)
        elif "all" not in pairs and filter_len == 1:
            max_len = 0
            for df, pair in zip(dflist, nice_pairs):
                tmp = df["mean"]
                #Find out longest time series to plot
                if len(tmp) > max_len:
                    max_len = len(tmp)
                    id = tmp.index
                plt.plot(tmp.index, tmp, label=pair)
        else:
            max_len = 0
            for df, pair in zip(dflist, nice_pairs):
                tmp = df["mean"]
                #Find out longest time series to plot
                if len(tmp) > max_len:
                    max_len = len(tmp)
                    id = tmp.index
                label = ("Filter %i, %i-%is, %s" %
                        (int(filter), minlags[i], endlags[i], pair))
                plt.plot(tmp.index, tmp, label=pair)

    # Coordinate labels and grids
    left, right = id[0], id[-1]
    plt.xlim(left, right)
    plt.ylabel('dv/v (%)')
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(DateFormatter("%Y-%m-%d %H:%M"))
    fig.autofmt_xdate()
    # Title and legend
    if mov_stack == 1:
        plt.title('1 Day Smoothing')
    else:
        plt.title('%i Days Smoothing' % mov_stack)
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=4,
               ncol=2, borderaxespad=0.)


    # Plot forcing
    plt.subplot(gs[1], sharex=ax)

    # load forcing default values
    defaults = pd.read_csv("defaults.csv", header=1, index_col=1)
    dir = defaults.at[forcing, 'folder_name']
    name = defaults.at[forcing, 'forcing']
    unit = defaults.at[forcing, 'unit']

    if ask:
        stas = ask_stations(dir)
    else:
        stas = [defaults.at[forcing, 'default_station']]

    if forcing == 'PGV':
        data = get_pgv()
    else:
        data = get_data(dir, stas)

    # Plot configurations
    if type == 'points':
        plt.plot(data.index, data, ".", markersize=8)
    elif type == 'bars':
        plt.bar(data.index, data)
    elif type == 'cumsum':
        plt.bar(data.index, data.cumsum())
        name = "Cumulative " + name.lower()
    elif type == 'errorbars':
        # TODO: Maybe find more elegant way? For now, data in first, errors
        # in second column
        data_err = data.iloc[2]
        plt.errorbar(data.index, data.iloc[1], yerr=data_err, fmt='o')
    else:
        print("Unknown type parameter, using default.")
        plt.plot(data.index, data, ".", markersize=8)

    plt.ylabel(name, unit)
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(DateFormatter("%Y-%m-%d %H:%M"))
    fig.autofmt_xdate()
    plt.legend()
    # Station list without the brackets
    stas_string = str(stas)[1:-1]
    if "all" in stas:
        plt.title("%s data for all the stations" % name)
    elif len(stas) == 1:
        plt.title("%s data for station: %s" % (name, stas_string))
    else:
        plt.title("%s data for stations: %s" % (name, stas_string))

    # Prepare plot title
    title = 'Stretching, %s \n' % ",".join(components)
    for i, filterid in enumerate(filterids):
        title += ('Filter %d (%.2f - %.2f Hz), Lag time window %.1f - %.1fs \n' % (
                  int(filterid[0:2]), lows[i], highs[i], minlags[i], endlags[i]))
    if "all" in pairs:
        title += "Average over all pairs"
    else:
        title += "Pairs: %s" % str(nice_pairs)[1:-1]

    # Save plot output if true
    if outfile:
        if outfile.startswith("?"):
            if len(mov_stacks) == 1:
                outfile = outfile.replace('?', '%s-f%i-m%i-M%s' % (components,
                                                                   filterid,
                                                                   mov_stack,
                                                                   dttname))
            else:
                outfile = outfile.replace('?', '%s-f%i-M%s' % (components,
                                                               filterid,
                                                               dttname))
        outfile = "dvv_" + outfile
        print("output to:", outfile)
        plt.savefig(outfile)
    if show:
        plt.show()


if __name__ == "__main__":
    main()
