import sys
import time
import datetime
import icalendar
import pandas as pd
import numpy as np
from PySide2 import QtWidgets, QtCore
from resources.ui.main_window_ui import Ui_MainWindow
from time_sheet_table_model import TimeSheetTableModel


class MainWindow(QtWidgets.QMainWindow):
    """ Main Window of Calegories """

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.tz = 'US/Central'
        self.current_date = pd.to_datetime("today").tz_localize(tz=self.tz)
        self.reference_date = self.current_date.replace(
            hour=0, minute=0, second=0, microsecond=0)
        self.ui.nextWeekButton.clicked.connect(self.show_next_week)
        self.ui.prevWeekButton.clicked.connect(self.show_prev_week)
        self.ui.currentWeekButton.clicked.connect(self.show_current_week)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionLoad_ics.triggered.connect(self.load_ics)
        menu = self.menuBar()
        menu.setNativeMenuBar(False)
        self.events_df = None
        self.displayed_week = []
        self.weekday_abbr = {
            'MO': 'Monday',
            'TU': 'Tuesday',
            'WE': 'Wednesday',
            'TH': 'Thursday',
            'FR': 'Friday',
            'SA': 'Saturday',
            'SU': 'Sunday',
        }
        self.init_week_df()

    def find_day_name_index(self, day_name):
        for i, day in enumerate(self.weekdays):
            if day_name == day:
                idx = i
                return idx

    def format_table_view(self):
        table_view = self.ui.weekTableView
        num_cols = table_view.model().columnCount()
        for col in range(1, num_cols - 1):
            table_view.setItemDelegateForColumn(
                col, table_view._delegates['PositiveDoubleDelegate'])
        self.ui.weekTableView.model().dataChanged.connect(self.update_totals)

    def init_week_df(self):
        week_start_day = 0
        pd_weekdays = ['Monday', 'Tuesday', 'Wednesday',
                       'Thursday', 'Friday', 'Saturday', 'Sunday']
        num_weekdays = len(pd_weekdays)
        self.weekdays = [pd_weekdays[i] for i in range(week_start_day, num_weekdays)] + [pd_weekdays[i] for i in range(
            0, week_start_day)]
        current_day = self.reference_date.day_name()
        idx = self.find_day_name_index(current_day)
        self.displayed_week = [self.reference_date + pd.Timedelta(i - idx, unit='d')
                               for i in range(num_weekdays)]
        strf_dates = [date_obj.strftime("%m/%d/%y")
                      for date_obj in self.displayed_week]

        last_column = ['Week Total']
        first_column = 'Category'
        middle_columns = [
            f'{self.weekdays[i]}\n{strf_dates[i]}' for i in range(num_weekdays)]
        df_dict = {}
        df_dict[first_column] = 'Day Total'
        for key in middle_columns + last_column:
            df_dict[key] = [0.0]
        week_df = pd.DataFrame(df_dict)
        week_df.set_index(first_column)
        model = TimeSheetTableModel(week_df)
        self.ui.weekTableView.setModel(model)
        self.ui.weekTableView.horizontalHeader().setSectionResizeMode(0,
                                                                      QtWidgets.QHeaderView.Stretch)
        self.ui.weekTableView.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents)
        self.format_table_view()

    def update_week_df(self):
        self.init_week_df()
        if self.events_df is not None:
            start_date = self.displayed_week[0].replace(
                hour=0, minute=0, second=0, microsecond=0)
            end_date = self.displayed_week[-1].replace(
                hour=0, minute=0, second=0, microsecond=0) + pd.Timedelta(days=1)
            filter1 = self.events_df['start'] >= start_date
            filter2 = self.events_df['start'] <= end_date
            df = self.events_df.where(filter1 & filter2).dropna()
            categories = pd.unique(df['categories'])
            model = self.ui.weekTableView.model()
            columns = model._df.columns
            categories_df_dict = {}
            for i, column in enumerate(columns):
                if i == 0:
                    categories_df_dict[column] = categories
                else:
                    categories_df_dict[column] = len(categories) * [0.0]

            categories_df = pd.DataFrame(categories_df_dict)
            category_day_df = df.groupby(['categories', 'day_name']).sum()
            for i in range(category_day_df.shape[0]):
                day_name = category_day_df.index[i][-1]
                category_name = category_day_df.index[i][0]
                k = np.argwhere(category_name == categories).flatten()[0]
                j = self.find_day_name_index(day_name)
                num = category_day_df['duration'].iloc[i]
                categories_df.iat[k, j + 1] = num
            # TODO: switch to join instead of append
            full_df = categories_df.append(model._df, ignore_index=True)
            model = TimeSheetTableModel(full_df)
            self.ui.weekTableView.setModel(model)
            self.update_totals()
            self.format_table_view()

    def update_totals(self):
        df = self.ui.weekTableView.model()._df
        week_totals = df.drop(df.columns[-1], axis=1).sum(axis=1)
        df[df.columns[-1]] = week_totals
        day_totals = df.drop(df.shape[0] - 1, axis=0).sum(axis=0)
        for j in range(1, df.shape[1]):
            df.iat[df.shape[0] - 1, j] = day_totals[j]

    def show_current_week(self):
        self.reference_date = self.current_date
        self.update_week_df()

    def show_next_week(self):
        self.reference_date += datetime.timedelta(weeks=1)
        self.update_week_df()

    def show_prev_week(self):
        self.reference_date -= datetime.timedelta(weeks=1)
        self.update_week_df()

    def load_ics(self):
        options = QtWidgets.QFileDialog.Options()
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open", "", " ICS (*.ics)", options=options)
        if filename is None:
            return
        df_dict = {'title': [], 'categories': [],
                   'start': [], 'end': [], 'day_name': []}
        with open(filename, 'r', encoding='utf8') as f:
            calendar = icalendar.Calendar.from_ical(f.read())
        for component in calendar.walk():
            if component.name == "VEVENT":
                categories = component.get('CATEGORIES', None)
                if categories is not None:

                    title = str(component.get('SUMMARY', ''))
                    categories = ''.join(
                        [str(cat) for cat in categories.cats])
                    dt_start = pd.Timestamp(
                        component.get('DTSTART', None).dt).tz_convert(tz=self.tz)
                    dt_end = pd.Timestamp(
                        component.get('DTEND', None).dt).tz_convert(tz=self.tz)
                    day_name = dt_start.day_name()

                    df_dict['title'].append(title)
                    df_dict['categories'].append(categories)
                    df_dict['start'].append(dt_start)
                    df_dict['end'].append(dt_end)
                    df_dict['day_name'].append(day_name)

                    recurrence_data = component.get('RRULE', {})
                    if recurrence_data:
                        excluded_dates = component.get('EXDATE', [])
                        if excluded_dates:
                            excluded_dates = [pd.Timestamp(
                                ex_date.dt) for ex_date in excluded_dates.dts]
                        interval = recurrence_data.get('INTERVAL', [1])[0]
                        count = recurrence_data.get('COUNT', [None])[0]
                        by_day = recurrence_data.get(
                            'BYDAY', [])
                        by_month_day = recurrence_data.get(
                            'BYMONTHDAY', [None])[0]
                        by_month = recurrence_data.get(
                            'BYMONTH', [None])[0]
                        if count is None:
                            # Only support events that have counts at this time
                            break
                        # check frequency
                        if recurrence_data['FREQ'][0] == 'DAILY':
                            i = 0
                            while i < (count - 1):
                                dt_start += pd.Timedelta(
                                    days=interval)
                                dt_end += pd.Timedelta(days=interval)
                                if dt_start in excluded_dates:
                                    i += 1
                                    continue
                                df_dict['title'].append(title)
                                df_dict['categories'].append(categories)
                                df_dict['start'].append(dt_start)
                                df_dict['end'].append(dt_end)
                                day_name = dt_end.day_name()
                                df_dict['day_name'].append(day_name)
                                i += 1

                        elif recurrence_data['FREQ'][0] == 'WEEKLY':
                            repeat_days = [self.weekday_abbr[day]
                                           for day in by_day]
                            i = 0
                            while i < (count - 1):
                                possible_days = repeat_days.copy()
                                current_day_name = dt_start.day_name()
                                current_day_idx = self.find_day_name_index(
                                    current_day_name)
                                possible_days_indices = [self.find_day_name_index(
                                    day) for day in possible_days]
                                day_distances = [
                                    (possible_day_idx - current_day_idx) for possible_day_idx in possible_days_indices]
                                for j, distance in enumerate(day_distances):
                                    if distance <= 0:
                                        day_distances[j] += 7
                                day_interval = min(day_distances)
                                shift = interval * day_interval

                                dt_start += pd.Timedelta(
                                    days=shift)
                                dt_end += pd.Timedelta(days=shift)
                                if dt_start in excluded_dates:
                                    i += 1
                                    continue
                                df_dict['title'].append(title)
                                df_dict['categories'].append(categories)
                                df_dict['start'].append(dt_start)
                                df_dict['end'].append(dt_end)
                                day_name = dt_end.day_name()
                                df_dict['day_name'].append(day_name)
                                i += 1

                        elif recurrence_data['FREQ'][0] == 'MONTHLY':
                            if by_month_day is not None:
                                i = 0
                                while i < (count - 1):
                                    if by_month_day:
                                        month_shift = pd.DateOffset(
                                            months=interval)
                                        day_shift = pd.Timedelta(
                                            days=(dt_start.day - by_month_day))
                                        dt_start += month_shift
                                        dt_start += day_shift
                                        dt_end += month_shift
                                        dt_end += day_shift
                                        if dt_start in excluded_dates:
                                            i += 1
                                            continue
                                        df_dict['title'].append(title)
                                        df_dict['categories'].append(categories)
                                        df_dict['start'].append(dt_start)
                                        df_dict['end'].append(dt_end)
                                        day_name = dt_end.day_name()
                                        df_dict['day_name'].append(day_name)
                                        i += 1
                            else:
                                repeat_days = []
                                day_instances = []
                                for day in by_day:
                                    if len(day) > 3:
                                        day_instances.append(int(day[:2]))
                                        repeat_days.append(
                                            self.weekday_abbr[day[2:]])
                                    else:
                                        day_instances.append(int(day[0]))
                                        repeat_days.append(
                                            self.weekday_abbr[day[1:]])
                                repeat_days = dict(
                                    zip(repeat_days, day_instances))
                                repeat_day_timestamps = self.get_repeat_day_timestamps(
                                    dt_start, repeat_days)
                                first_day_of_month = dt_start - \
                                    pd.Timedelta(days=dt_start.day - 1)

                                i = 0
                                while i < (count - 1):
                                    for repeat_day in repeat_day_timestamps:
                                        if repeat_day > dt_start:
                                            shift = repeat_day.dayofyear - dt_start.dayofyear
                                            dt_start += pd.Timedelta(
                                                days=shift)
                                            dt_end += pd.Timedelta(days=shift)
                                            if dt_start in excluded_dates:
                                                i += 1
                                                continue
                                            df_dict['title'].append(title)
                                            df_dict['categories'].append(
                                                categories)
                                            df_dict['start'].append(dt_start)
                                            df_dict['end'].append(dt_end)
                                            day_name = dt_end.day_name()
                                            df_dict['day_name'].append(day_name)
                                            i += 1
                                    repeat_day_timestamps = self.get_repeat_day_timestamps(first_day_of_month + pd.DateOffset(
                                        months=interval), repeat_days)

                        elif recurrence_data['FREQ'][0] == 'YEARLY':
                            pass

        df = pd.DataFrame(df_dict)
        df['duration'] = (df['end'] - df['start']) / \
            pd.Timedelta(hours=1)
        if self.events_df is None:
            self.events_df = df
        else:
            self.events_df = self.events_df.append(
                df, ignore_index=True)
        self.update_week_df()

    def get_repeat_day_timestamps(self, reference_date, repeat_day_dict):
        day_occurances = dict(
            zip(self.weekdays, [0] * len(self.weekdays)))
        repeat_day_timestamps = []
        first_day_of_month = reference_date - \
            pd.Timedelta(days=reference_date.day - 1)
        i = 0
        scan_date = first_day_of_month
        days_in_month = first_day_of_month.days_in_month
        while i < days_in_month:
            scan_day = scan_date.day_name()
            day_occurances[scan_day] += 1
            if scan_day in repeat_day_dict.keys() and repeat_day_dict[scan_day] == day_occurances[scan_day]:
                repeat_day_timestamps.append(
                    scan_date)
            elif scan_day in repeat_day_dict.keys() and (days_in_month - i) <= len(self.weekdays) and repeat_day_dict[scan_day] == -1:
                repeat_day_timestamps.append(
                    scan_date)
            scan_date = scan_date + pd.Timedelta(days=1)
            i += 1
        repeat_day_timestamps.sort()
        return repeat_day_timestamps


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
