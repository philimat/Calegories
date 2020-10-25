import sys
import time
import datetime
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
        self.current_date = pd.to_datetime("today")
        self.reference_date = self.current_date.replace(
            hour=0, minute=0, second=0, microsecond=0)
        self.ui.nextWeekButton.clicked.connect(self.show_next_week)
        self.ui.prevWeekButton.clicked.connect(self.show_prev_week)
        self.ui.currentWeekButton.clicked.connect(self.show_current_week)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionLoad_ics.triggered.connect(self.load_ics)
        menu = self.menuBar()
        menu.setNativeMenuBar(False)
        self.ics_iso_fmt = "%Y%m%dT%H%M%S"
        self.events_df = None
        self.displayed_week = []
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
            categories = pd.unique(df['category'])
            model = self.ui.weekTableView.model()
            columns = model._df.columns
            categories_df_dict = {}
            for i, column in enumerate(columns):
                if i == 0:
                    categories_df_dict[column] = categories
                else:
                    categories_df_dict[column] = len(categories) * [0.0]

            categories_df = pd.DataFrame(categories_df_dict)
            category_day_df = df.groupby(['category', 'day_name']).sum()
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
        if filename is not None:
            df_dict = {'title': [], 'category': [],
                       'start': [], 'end': [], 'day_name': []}
            with open(filename, 'r', encoding='utf8') as f:
                in_event = False
                for line in f:
                    line = line.lstrip().rstrip()
                    if line.startswith('BEGIN:VEVENT'):
                        in_event = True
                        category = None
                        dt_start = None
                        dt_end = None
                        recurrence_data = {}
                        title = ''
                        excluded_dates = []
                    elif in_event:
                        if line.startswith('RRULE:'):
                            stripped_line = ''.join(
                                line.split(':')[1:]).split(';')
                            for pair in stripped_line:
                                split_line = pair.split('=')
                                recurrence_data[split_line[0]] = split_line[1]
                        elif line.startswith('CATEGORIES:'):
                            category = ''.join(line.split(':')[1:])
                        elif line.startswith('SUMMARY:'):
                            title = ''.join(line.split(':')[1:])
                        elif line.startswith('DTSTART;'):
                            iso_start = ''.join(line.split(':')[1:])
                            try:
                                dt_start = pd.Timestamp(datetime.datetime.strptime(
                                    iso_start, self.ics_iso_fmt))
                            except:
                                continue
                        elif line.startswith('DTEND;'):
                            iso_end = ''.join(line.split(':')[1:])
                            try:
                                dt_end = pd.Timestamp(datetime.datetime.strptime(
                                    iso_end, self.ics_iso_fmt))
                            except:
                                continue
                        elif line.startswith('EXDATE;'):
                            ex_dates = line.split(':')[-1].split(',')
                            for ex_date in ex_dates:
                                try:
                                    excluded_dates.append(pd.Timestamp(datetime.datetime.strptime(
                                        ex_date, self.ics_iso_fmt)))
                                except:
                                    continue
                        elif line.startswith('END:VEVENT'):
                            if dt_start is not None and dt_end is not None and category is not None:
                                df_dict['title'].append(title)
                                df_dict['category'].append(category)
                                df_dict['start'].append(dt_start)
                                df_dict['end'].append(dt_end)
                                day_name = dt_end.day_name()
                                df_dict['day_name'].append(day_name)
                                if recurrence_data:
                                    weekday_abbr = {
                                        'MO': 'Monday',
                                        'TU': 'Tuesday',
                                        'WE': 'Wednesday',
                                        'TH': 'Thursday',
                                        'FR': 'Friday',
                                        'SA': 'Saturday',
                                        'SU': 'Sunday',
                                    }
                                    interval = int(
                                        recurrence_data.get('INTERVAL', 1))
                                    count = recurrence_data.get('COUNT', None)
                                    if count is None:
                                        # Only support events that have counts at this time
                                        break
                                    else:
                                        count = int(count)
                                    # check frequency
                                    if recurrence_data['FREQ'] == 'DAILY':
                                        i = 0
                                        while i < (count - 1):
                                            dt_start += pd.Timedelta(
                                                days=interval)
                                            dt_end += pd.Timedelta(days=interval)
                                            if dt_start in excluded_dates:
                                                i += 1
                                                continue
                                            df_dict['title'].append(title)
                                            df_dict['category'].append(category)
                                            df_dict['start'].append(dt_start)
                                            df_dict['end'].append(dt_end)
                                            day_name = dt_end.day_name()
                                            df_dict['day_name'].append(day_name)
                                            i += 1

                                    elif recurrence_data['FREQ'] == 'WEEKLY':
                                        repeat_days_abbr = recurrence_data.get(
                                            'BYDAY', []).split(',')
                                        repeat_days = [weekday_abbr[day]
                                                       for day in repeat_days_abbr]
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
                                            interval = min(day_distances)

                                            dt_start += pd.Timedelta(
                                                days=interval)
                                            dt_end += pd.Timedelta(days=interval)
                                            if dt_start in excluded_dates:
                                                i += 1
                                                continue
                                            df_dict['title'].append(title)
                                            df_dict['category'].append(category)
                                            df_dict['start'].append(dt_start)
                                            df_dict['end'].append(dt_end)
                                            day_name = dt_end.day_name()
                                            df_dict['day_name'].append(day_name)
                                            i += 1

                                    elif recurrence_data['FREQ'] == 'MONTHLY':
                                        pass

                                    elif recurrence_data['FREQ'] == 'YEARLY':
                                        pass
                            in_event = False

                df = pd.DataFrame(df_dict)
                df['duration'] = (df['end'] - df['start']) / \
                    pd.Timedelta(hours=1)
                if self.events_df is None:
                    self.events_df = df
                else:
                    self.events_df = self.events_df.append(
                        df, ignore_index=True)
        self.update_week_df()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
