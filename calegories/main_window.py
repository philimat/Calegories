from PySide2.QtWidgets import QMainWindow, QHeaderView, QAction, QFileDialog, QTableWidgetItem
from PySide2.QtCore import Qt
from resources.ui.main_window_ui import Ui_MainWindow
import datetime
import pandas as pd
import numpy as np


class MainWindow(QMainWindow):
    """ Main Window of Calegories """

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.current_date = pd.to_datetime("today")
        self.reference_date = self.current_date
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
        self.create_week_table_widget()
        self.ui.weekTableWidget.itemChanged.connect(self.handle_item_changed)

    def handle_item_changed(self, item):
        table = self.ui.weekTableWidget
        index = table.indexFromItem(item)
        row = index.row()
        col = index.column()
        day_total = 0
        week_total = 0
        num_rows = table.rowCount()
        num_cols = table.columnCount()
        flags = Qt.ItemFlags()
        flags != Qt.ItemIsEditable

        if row != num_rows - 1:
            for i in range(num_rows - 1):
                item = table.item(i, col)
                if item is None:
                    break
                else:
                    update = float(item.text())
                    day_total += update

            new_item = QTableWidgetItem(f'{day_total}')
            new_item.setFlags(flags)
            table.setItem(num_rows - 1, col, new_item)

        if col != num_cols - 1:
            for j in range(num_cols - 1):
                item = table.item(row, j)
                if item is None:
                    break
                else:
                    update = float(item.text())
                    week_total += update

            new_item = QTableWidgetItem(f'{week_total}')
            new_item.setFlags(flags)
            table.setItem(row, num_cols - 1, new_item)

    def create_week_table_widget(self):
        # self.ui.weekTableWidget.setItemDelegate(TimeSheetDelegate())
        self.set_column_headers()
        self.update_table_content()

    def find_day_name_index(self, day_name):
        for i, day in enumerate(self.weekdays):
            if day_name == day:
                idx = i
                return idx

    def set_column_headers(self):
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
        first_columns = [
            f'{self.weekdays[i]}\n{strf_dates[i]}' for i in range(num_weekdays)]
        columns = first_columns + last_column
        self.ui.weekTableWidget.setColumnCount(len(columns))
        self.ui.weekTableWidget.setHorizontalHeaderLabels(columns)
        self.ui.weekTableWidget.horizontalHeader().setSectionResizeMode(0,
                                                                        QHeaderView.Stretch)
        self.ui.weekTableWidget.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)

    def refresh_table_cells(self):
        table = self.ui.weekTableWidget
        num_cols = table.columnCount()
        num_rows = table.rowCount()
        for col in range(num_cols):
            for row in range(num_rows):
                item = QTableWidgetItem(f'{0.0}')
                if row == (num_rows - 1) or col == (num_cols - 1):
                    flags = Qt.ItemFlags()
                    flags != Qt.ItemIsEditable
                    item.setFlags(flags)
                table.setItem(row, col, item)

    def update_table_content(self):
        if self.events_df is not None:
            start_date = self.displayed_week[0]
            end_date = self.displayed_week[-1]
            filter1 = self.events_df['start'] >= start_date
            filter2 = self.events_df['start'] <= end_date
            df = self.events_df.where(filter1 & filter2).dropna()
            rows = pd.unique(df['category'])
            self.ui.weekTableWidget.setRowCount(len(rows) + 1)
            self.ui.weekTableWidget.setVerticalHeaderLabels(
                list(rows) + ['Total'])
            self.refresh_table_cells()
            category_day_df = df.groupby(['category', 'day_name']).sum()
            for i in range(category_day_df.shape[0]):
                day_name = category_day_df.index[i][-1]
                category_name = category_day_df.index[i][0]
                k = np.argwhere(category_name == rows).flatten()[0]
                j = self.find_day_name_index(day_name)
                num = category_day_df['duration'].iloc[i]
                item = QTableWidgetItem(f'{num}')
                self.ui.weekTableWidget.setItem(k, j, item)
        else:
            self.ui.weekTableWidget.setRowCount(1)
            self.ui.weekTableWidget.setVerticalHeaderLabels(['Day Total'])
            self.refresh_table_cells()

    def show_current_week(self):
        self.reference_date = self.current_date
        self.set_column_headers()
        self.update_table_content()

    def show_next_week(self):
        self.reference_date += datetime.timedelta(weeks=1)
        self.set_column_headers()
        self.update_table_content()

    def show_prev_week(self):
        self.reference_date -= datetime.timedelta(weeks=1)
        self.set_column_headers()
        self.update_table_content()

    def load_ics(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open", "", " ICS (*.ics)", options=options)
        if filename is not None:
            df_dict = {'title': [], 'category': [],
                       'start': [], 'end': [], 'day_name': []}
            with open(filename, 'r') as f:
                for line in f:
                    line = line.lstrip().rstrip()
                    if line.startswith('BEGIN:VEVENT'):
                        category = None
                        dt_start = None
                        dt_end = None
                        title = ''
                    elif line.startswith('CATEGORIES:'):
                        category = ''.join(line.split(':')[1:])
                    elif line.startswith('SUMMARY:'):
                        title = ''.join(line.split(':')[1:])
                    elif line.startswith('DTSTART;'):
                        iso_start = ''.join(line.split(':')[1:])
                        dt_start = pd.Timestamp(datetime.datetime.strptime(
                            iso_start, self.ics_iso_fmt))
                    elif line.startswith('DTEND;'):
                        iso_end = ''.join(line.split(':')[1:])
                        dt_end = pd.Timestamp(datetime.datetime.strptime(
                            iso_end, self.ics_iso_fmt))
                    if line.startswith('END:VEVENT'):
                        if dt_start is not None and dt_end is not None and category is not None:
                            df_dict['title'].append(title)
                            df_dict['category'].append(category)
                            df_dict['start'].append(dt_start)
                            df_dict['end'].append(dt_end)
                            day_name = dt_end.day_name()
                            df_dict['day_name'].append(day_name)
                df = pd.DataFrame(df_dict)
                df['duration'] = (df['end'] - df['start']) / \
                    pd.Timedelta(hours=1)
                if self.events_df is None:
                    self.events_df = df
                else:
                    self.events_df = self.events_df.append(
                        df, ignore_index=True)
        self.update_table_content()
