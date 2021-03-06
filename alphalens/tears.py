#
# Copyright 2016 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pandas as pd

from . import plotting
from . import performance as perf
from . import utils


# it makes life easier with grid plots
class GridFigure(object):
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.fig = plt.figure(figsize=(14, rows * 7))
        self.gs = gridspec.GridSpec(rows, cols, wspace=0.4, hspace=0.3)
        self.curr_row = 0
        self.curr_col = 0

    def next_row(self):
        if self.curr_col != 0:
            self.curr_row += 1
            self.curr_col = 0
        subplt = plt.subplot(self.gs[self.curr_row, :])
        self.curr_row += 1
        return subplt

    def next_cell(self):
        if self.curr_col >= self.cols:
            self.curr_row += 1
            self.curr_col = 0
        subplt = plt.subplot(self.gs[self.curr_row, self.curr_col])
        self.curr_col += 1
        return subplt


@plotting.customize
def create_summary_tear_sheet(factor_data, long_short=True):
    """
    Creates a small summary tear sheet with returns, information, and turnover
    analysis.

    Parameters
    ----------
    factor_data : pd.DataFrame - MultiIndex
        A MultiIndex DataFrame indexed by date (level 0) and asset (level 1),
        containing the values for a single alpha factor, forward returns for each period,
        The factor quantile/bin that factor value belongs too, and (optionally) the group the
        asset belongs to.
    long_short : bool
        Should this computation happen on a long short portfolio? if so, then factor values
        will be demeaned across the factor universe when factor weighting the portfolio. 
        Additionally, mean quantile returns will be demeaned across the factor universe.
    """


    # Returns Analysis
    factor_returns = perf.factor_returns(factor_data, long_short)

    mean_ret_quantile, std_quantile = perf.mean_return_by_quantile(factor_data,
                                                                   by_group=False,
                                                                   demeaned=long_short)

    mean_compret_quantile = mean_ret_quantile.apply(utils.rate_of_return, axis=0)

    mean_ret_quant_daily, std_quant_daily = perf.mean_return_by_quantile(factor_data,
                                                                         by_date=True,
                                                                         by_group=False,
                                                                         demeaned=long_short)

    mean_compret_quant_daily = mean_ret_quant_daily.apply(utils.rate_of_return,
                                                          axis=0)
    compstd_quant_daily = std_quant_daily.apply(utils.std_conversion, axis=0)

    alpha_beta = perf.factor_alpha_beta(factor_data, long_short)

    mean_ret_spread_quant, std_spread_quant = perf.compute_mean_returns_spread(
        mean_compret_quant_daily,
        factor_data['factor_quantile'].max(),
        factor_data['factor_quantile'].min(),
        std_err=compstd_quant_daily)

    fr_cols = len(factor_returns.columns)
    vertical_sections = 2 + fr_cols * 3
    gf = GridFigure(rows=vertical_sections, cols=1)


    plotting.plot_quantile_statistics_table(factor_data)

    plotting.plot_returns_table(alpha_beta, mean_compret_quantile, mean_ret_spread_quant)

    plotting.plot_quantile_returns_bar(mean_compret_quantile,
                                       by_group=False,
                                       ylim_percentiles=None,
                                       ax=gf.next_row())

    # Information Analysis
    ic = perf.factor_information_coefficient(factor_data)
    plotting.plot_information_table(ic)

    # Turnover Analysis
    turnover_periods = utils.get_forward_returns_columns(factor_data.columns)
    quantile_factor = factor_data['factor_quantile']

    quantile_turnover = {p: pd.concat([perf.quantile_turnover(
        quantile_factor, q, p) for q in range(1, int(quantile_factor.max()) + 1)],
                                           axis=1)
                              for p in turnover_periods}

    autocorrelation = pd.concat(
        [perf.factor_rank_autocorrelation(factor_data, period) for period in
         turnover_periods], axis=1)

    plotting.plot_turnover_table(autocorrelation, quantile_turnover)


@plotting.customize
def create_returns_tear_sheet(factor_data, long_short=True, by_group=False):
    """
    Creates a tear sheet for returns analysis of a factor.

    Parameters
    ----------
    factor_data : pd.DataFrame - MultiIndex
        A MultiIndex DataFrame indexed by date (level 0) and asset (level 1),
        containing the values for a single alpha factor, forward returns for each period,
        The factor quantile/bin that factor value belongs too, and (optionally) the group the
        asset belongs to.
    long_short : bool
        Should this computation happen on a long short portfolio? if so, then factor values
        will be demeaned across the factor universe when factor weighting the portfolio. 
        Additionally, mean quantile returns will be demeaned across the factor universe.
    by_group : bool
        If True, perform calcuations, and display graphs separately for
        each group.
    """

    factor_returns = perf.factor_returns(factor_data, long_short)

    mean_ret_quantile, std_quantile = perf.mean_return_by_quantile(factor_data,
                                                                   by_group=False,
                                                                   demeaned=long_short)

    mean_compret_quantile = mean_ret_quantile.apply(utils.rate_of_return, axis=0)

    mean_ret_quant_daily, std_quant_daily = perf.mean_return_by_quantile(factor_data,
                                                                         by_date=True,
                                                                         by_group=False,
                                                                         demeaned=long_short)

    mean_compret_quant_daily = mean_ret_quant_daily.apply(utils.rate_of_return, axis=0)
    compstd_quant_daily = std_quant_daily.apply(utils.std_conversion, axis=0)

    alpha_beta = perf.factor_alpha_beta(factor_data, long_short)

    mean_ret_spread_quant, std_spread_quant = perf.compute_mean_returns_spread(
        mean_compret_quant_daily,
        factor_data['factor_quantile'].max(),
        factor_data['factor_quantile'].min(),
        std_err=compstd_quant_daily)

    fr_cols = len(factor_returns.columns)
    vertical_sections = 2 + fr_cols * 3
    gf = GridFigure(rows=vertical_sections, cols=1)

    plotting.plot_returns_table(alpha_beta, mean_compret_quantile, mean_ret_spread_quant)

    plotting.plot_quantile_returns_bar(mean_compret_quantile,
                                       by_group=False,
                                       ylim_percentiles=None,
                                       ax=gf.next_row())

    plotting.plot_quantile_returns_violin(mean_compret_quant_daily,
                                          ylim_percentiles=(1, 99),
                                          ax=gf.next_row())

    for p in factor_returns:

        plotting.plot_cumulative_returns(factor_returns[p],
                                         period=p,
                                         ax=gf.next_row())

        plotting.plot_cumulative_returns_by_quantile(mean_ret_quant_daily[p],
                                                     period=p,
                                                     ax=gf.next_row())

    ax_mean_quantile_returns_spread_ts = [ gf.next_row() for x in range(fr_cols) ]
    plotting.plot_mean_quantile_returns_spread_time_series(mean_ret_spread_quant,
                                                           std_err=std_spread_quant,
                                                           bandwidth=0.5,
                                                           ax=ax_mean_quantile_returns_spread_ts)

    if by_group:
        mean_return_quantile_group, mean_return_quantile_group_std_err = perf.mean_return_by_quantile(factor_data,
                                                                                                      by_date=False,
                                                                                                      by_group=by_group,
                                                                                                      demeaned=True)

        mean_compret_quantile_group = mean_return_quantile_group.apply(utils.rate_of_return, axis=0)

        num_groups = len(mean_compret_quantile_group.index.get_level_values('group').unique())
        vertical_sections = 1 + (((num_groups - 1) // 2) + 1)
        gf = GridFigure(rows=vertical_sections, cols=2)

        ax_quantile_returns_bar_by_group = [gf.next_cell() for _ in range(num_groups)]
        plotting.plot_quantile_returns_bar(mean_compret_quantile_group,
                                           by_group=True,
                                           ylim_percentiles=(5, 95),
                                           ax=ax_quantile_returns_bar_by_group)


@plotting.customize
def create_information_tear_sheet(factor_data,
                                  group_adjust=False,
                                  by_group=False):
    """
    Creates a tear sheet for information analysis of a factor.

    Parameters
    ----------
    factor_data : pd.DataFrame - MultiIndex
        A MultiIndex DataFrame indexed by date (level 0) and asset (level 1),
        containing the values for a single alpha factor, forward returns for each period,
        The factor quantile/bin that factor value belongs too, and (optionally) the group the
        asset belongs to.
    group_adjust : bool
        Demean forward returns by group before computing IC.
    by_group : bool
        If True, perform calcuations, and display graphs separately for
        each group.
    """


    ic = perf.factor_information_coefficient(factor_data, group_adjust)

    plotting.plot_information_table(ic)

    columns_wide = 2
    fr_cols = len(ic.columns)
    rows_when_wide = (((fr_cols - 1) // columns_wide) + 1)
    vertical_sections = fr_cols + 3 * rows_when_wide + 2 * fr_cols
    gf = GridFigure(rows=vertical_sections, cols=columns_wide)

    ax_ic_ts = [gf.next_row() for _ in range(fr_cols)]
    plotting.plot_ic_ts(ic, ax=ax_ic_ts)

    ax_ic_hqq = [gf.next_cell() for _ in range(fr_cols * 2)]
    plotting.plot_ic_hist(ic, ax=ax_ic_hqq[::2])
    plotting.plot_ic_qq(ic, ax=ax_ic_hqq[1::2])

    if not by_group:

        mean_monthly_ic = perf.mean_information_coefficient(factor_data,
                                                            group_adjust,
                                                            by_group,
                                                            "M")
        ax_monthly_ic_heatmap = [gf.next_cell() for x in range(fr_cols)]
        plotting.plot_monthly_ic_heatmap(mean_monthly_ic, ax=ax_monthly_ic_heatmap)

    if by_group:
        mean_group_ic = perf.mean_information_coefficient(factor_data,
                                                          by_group=True)

        plotting.plot_ic_by_group(mean_group_ic, ax=gf.next_row())


@plotting.customize
def create_turnover_tear_sheet(factor_data):
    """
    Creates a tear sheet for analyzing the turnover properties of a factor.

    Parameters
    ----------
    factor_data : pd.DataFrame - MultiIndex
        A MultiIndex DataFrame indexed by date (level 0) and asset (level 1),
        containing the values for a single alpha factor, forward returns for each period,
        The factor quantile/bin that factor value belongs too, and (optionally) the group the
        asset belongs to.
    """

    turnover_periods = utils.get_forward_returns_columns(factor_data.columns)
    quantile_factor = factor_data['factor_quantile']

    quantile_turnover = {p: pd.concat([perf.quantile_turnover(
        quantile_factor, q, p) for q in range(1, int(quantile_factor.max()) + 1)],
                                           axis=1)
                              for p in turnover_periods}

    autocorrelation = pd.concat(
        [perf.factor_rank_autocorrelation(factor_data, period) for period in
         turnover_periods], axis=1)

    plotting.plot_turnover_table(autocorrelation, quantile_turnover)

    fr_cols = len(turnover_periods)
    columns_wide = 1
    rows_when_wide = (((fr_cols - 1) // 1) + 1)
    vertical_sections = fr_cols + 3 * rows_when_wide + 2 * fr_cols
    gf = GridFigure(rows=vertical_sections, cols=columns_wide)

    for period in sorted(quantile_turnover.keys()):
        plotting.plot_top_bottom_quantile_turnover(quantile_turnover[period],
                                                   period=period,
                                                   ax=gf.next_row())

    for period in autocorrelation:
        plotting.plot_factor_rank_auto_correlation(autocorrelation[period],
                                                   period=period,
                                                   ax=gf.next_row())


@plotting.customize
def create_full_tear_sheet(factor_data,
                           long_short=True,
                           group_adjust=False,
                           by_group=False):
    """
    Creates a full tear sheet for analysis and evaluating single
    return predicting (alpha) factor.

    Parameters
    ----------
    factor_data : pd.DataFrame - MultiIndex
        A MultiIndex DataFrame indexed by date (level 0) and asset (level 1),
        containing the values for a single alpha factor, forward returns for each period,
        The factor quantile/bin that factor value belongs too, and (optionally) the group the
        asset belongs to.
    group_adjust : bool
        Demean forward returns by group before computing IC.
    by_group : bool
        If True, perform calcuations, and display graphs separately for
        each group.
    long_short : bool
        Should this computation happen on a long short portfolio? if so, then factor values
        will be demeaned across the factor universe when factor weighting the portfolio. 
        Additionally, mean quantile returns will be demeaned across the factor universe.
    """

    plotting.plot_quantile_statistics_table(factor_data)
    create_returns_tear_sheet(factor_data, long_short, by_group, set_context=False)
    create_information_tear_sheet(factor_data, group_adjust, by_group, set_context=False)
    create_turnover_tear_sheet(factor_data, set_context=False)


@plotting.customize
def create_event_returns_tear_sheet(factor_data,
                                    prices,
                                    avgretplot=(5, 15),
                                    long_short=True,
                                    by_group=False):
        """
            Creates a tear sheet to view the average cumulative returns for a
            factor within a window (pre and post event).

            Parameters
            ----------
            factor_data : pd.DataFrame - MultiIndex
                A MultiIndex Series indexed by date (level 0) and asset (level 1),
                containing the values for a single alpha factor, forward returns for each period,
                The factor quantile/bin that factor value belongs too, and (optionally) the group the
                asset belongs to.
            prices : pd.DataFrame
                A wide form Pandas DataFrame indexed by date with assets
                in the columns. Pricing data should span the factor
                analysis time period plus/minus an additional buffer window
                corresponding to periods_after/periods_before parameters.
            avgretplot: tuple (int, int) - (before, after)
                If not None, plot quantile average cumulative returns
            long_short : bool
                Should this computation happen on a long short portfolio? if so then factor returns
                will be demeaned across the factor universe
            by_group : bool
                If True, view the average cumulative returns for each group.
        """

        before, after = avgretplot
        after = max(after, max(utils.get_forward_returns_columns(factor_data.columns)) + 1)

        avg_cumulative_returns = perf.average_cumulative_return_by_quantile(factor_data['factor_quantile'],
                                                                            prices,
                                                                            periods_before=before,
                                                                            periods_after=after,
                                                                            demeaned=long_short)

        num_quantiles = int(factor_data['factor_quantile'].max())

        vertical_sections = 1 + (((num_quantiles - 1) // 2) + 1)
        cols = 2 if num_quantiles != 1 else 1
        gf = GridFigure(rows=vertical_sections, cols=cols)
        plotting.plot_quantile_average_cumulative_return(avg_cumulative_returns, by_quantile=False,
                                                         std_bar=False, ax=gf.next_row())

        ax_avg_cumulative_returns_by_q = [gf.next_cell() for _ in range(num_quantiles)]
        plotting.plot_quantile_average_cumulative_return(avg_cumulative_returns, by_quantile=True,
                                                         std_bar=True, ax=ax_avg_cumulative_returns_by_q)

        if by_group:
            num_groups = len(factor_data['group'].unique())
            vertical_sections = ((num_groups - 1) // 2) + 1
            gf = GridFigure(rows=vertical_sections, cols=2)

            for group, g_factor in factor_data.groupby('group'):
                avg_cumulative_returns = perf.average_cumulative_return_by_quantile(g_factor['factor_quantile'],
                                                                                    prices,
                                                                                    periods_before=before,
                                                                                    periods_after=after,
                                                                                    demeaned=long_short)


                plotting.plot_quantile_average_cumulative_return(avg_cumulative_returns, by_quantile=False,
                                                                 std_bar=False, title=group, ax=gf.next_cell())


@plotting.customize
def create_event_study_tear_sheet(factor_data, prices, avgretplot=(5, 15)):
    """
    Creates an event study tear sheet for analysis of a specific event.

    Parameters
    ----------
    factor_data : pd.DataFrame - MultiIndex
        A MultiIndex DataFrame indexed by date (level 0) and asset (level 1),
        containing the values for a single event, forward returns for each period,
        The factor quantile/bin that factor value belongs too, and (optionally) the group the
        asset belongs to.
    prices : pd.DataFrame
        A wide form Pandas DataFrame indexed by date with assets
        in the columns. Pricing data should span the factor
        analysis time period plus/minus an additional buffer window
        corresponding to periods_after/periods_before parameters.
        if 'avgretplot' is None this can be None too
    avgretplot: tuple (int, int) - (before, after)
        If not None, plot quantile average cumulative returns
    """

    long_short = False # no return demeaning

    plotting.plot_quantile_statistics_table(factor_data)

    gf = GridFigure(rows=1, cols=1)
    plotting.plot_events_distribution(events=factor_data['factor'],
                                      ax=gf.next_row())

    create_event_returns_tear_sheet(factor_data=factor_data,
                                    prices=prices,
                                    avgretplot=avgretplot,
                                    long_short=long_short,
                                    by_group=False)

    mean_ret_quantile, std_quantile = perf.mean_return_by_quantile(factor_data,
                                                                   by_group=False,
                                                                   demeaned=long_short)

    mean_ret_quant_daily, std_quant_daily = perf.mean_return_by_quantile(factor_data,
                                                                         by_date=True,
                                                                         by_group=False,
                                                                         demeaned=long_short)

    fr_cols = len(mean_ret_quantile.columns)
    vertical_sections = 2 + fr_cols * 3
    gf = GridFigure(rows=vertical_sections, cols=1)

    plotting.plot_quantile_returns_bar(mean_ret_quantile,
                                       by_group=False,
                                       ylim_percentiles=None,
                                       ax=gf.next_row())

    plotting.plot_quantile_returns_violin(mean_ret_quant_daily,
                                          ylim_percentiles=(1, 99),
                                          ax=gf.next_row())

    for c in mean_ret_quant_daily:

        plotting.plot_cumulative_returns_by_quantile(mean_ret_quant_daily[c],
                                                     period=c,
                                                     ax=gf.next_row())
