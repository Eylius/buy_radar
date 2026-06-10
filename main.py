import sys

from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from scraper import CATEGORIES, load_category_data, scrape_category


class BuyRadarWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Buy Radar")
        self.resize(1100, 650)
        self.current_rows = []
        self.active_text_filter = None

        self.category_box = QComboBox()
        self.category_box.addItems(CATEGORIES.keys())
        self.category_box.currentTextChanged.connect(self.load_selected_data)

        self.load_button = QPushButton("Gespeicherte Daten laden")
        self.load_button.clicked.connect(self.load_selected_data)

        self.scrape_button = QPushButton("Neu scrapen")
        self.scrape_button.clicked.connect(self.scrape_selected_data)

        self.filter_mode_box = QComboBox()
        self.filter_mode_box.addItems(["Alle", "Above", "Below"])
        self.filter_mode_box.currentTextChanged.connect(self.update_filter_values)

        self.filter_value_box = QComboBox()
        self.filter_value_box.currentTextChanged.connect(self.apply_filter)

        self.status_label = QLabel("Keine Daten geladen.")

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellClicked.connect(self.handle_table_click)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Kategorie:"))
        top_layout.addWidget(self.category_box)
        top_layout.addWidget(self.load_button)
        top_layout.addWidget(self.scrape_button)
        top_layout.addWidget(QLabel("DeltaOwn:"))
        top_layout.addWidget(self.filter_mode_box)
        top_layout.addWidget(self.filter_value_box)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self.update_filter_values()
        self.load_selected_data()

    def selected_category(self):
        return self.category_box.currentText()

    def load_selected_data(self):
        category_name = self.selected_category()
        self.current_rows = load_category_data(category_name)
        self.active_text_filter = None
        self.apply_filter()

        if self.current_rows:
            self.status_label.setText(f"{len(self.current_rows)} gespeicherte Einträge für '{category_name}' geladen.")
        else:
            self.status_label.setText(f"Keine gespeicherten Daten für '{category_name}' gefunden.")

    def scrape_selected_data(self):
        category_name = self.selected_category()
        self.set_controls_enabled(False)
        self.status_label.setText(f"Scraping läuft: {category_name}")
        QApplication.processEvents()

        try:
            self.current_rows = scrape_category(category_name)
            self.active_text_filter = None
        except Exception as error:
            QMessageBox.critical(self, "Fehler", str(error))
            self.status_label.setText(f"Fehler beim Scraping von '{category_name}'.")
        else:
            self.apply_filter()
            self.status_label.setText(
                f"{len(self.current_rows)} Einträge für '{category_name}' gescrapt und gespeichert."
            )
        finally:
            self.set_controls_enabled(True)

    def set_controls_enabled(self, enabled):
        self.category_box.setEnabled(enabled)
        self.load_button.setEnabled(enabled)
        self.scrape_button.setEnabled(enabled)
        self.filter_mode_box.setEnabled(enabled)
        self.filter_value_box.setEnabled(enabled)

    def update_filter_values(self):
        mode = self.filter_mode_box.currentText()
        current_value = self.filter_value_box.currentText()

        if mode == "Below":
            values = ["0%"] + [f"{value}%" for value in range(-10, -101, -10)]
        else:
            values = [f"{value}%" for value in range(0, 101, 10)]

        self.filter_value_box.blockSignals(True)
        self.filter_value_box.clear()
        self.filter_value_box.addItems(values)

        if current_value in values:
            self.filter_value_box.setCurrentText(current_value)

        self.filter_value_box.blockSignals(False)
        self.apply_filter()

    def apply_filter(self):
        rows = self.current_rows
        mode = self.filter_mode_box.currentText()
        threshold = int(self.filter_value_box.currentText().removesuffix("%"))

        if mode != "Alle":
            rows = [row for row in rows if self.matches_delta_own_filter(row, mode, threshold)]

        if self.active_text_filter is not None:
            filter_key, filter_value = self.active_text_filter
            rows = [row for row in rows if row.get(filter_key, "") == filter_value]

        self.show_rows(rows)

        if self.current_rows:
            status_text = f"{len(rows)} von {len(self.current_rows)} Einträgen angezeigt."
            if self.active_text_filter is not None:
                _, filter_value = self.active_text_filter
                status_text += f" Filter: {filter_value}"
            self.status_label.setText(status_text)

    def matches_delta_own_filter(self, row, mode, threshold):
        value = self.parse_percent(self.get_delta_own_text(row))
        if value is None:
            return False
        if mode == "Above":
            return value >= threshold
        return value <= threshold

    def get_delta_own_text(self, row):
        for key, value in row.items():
            normalized_key = key.lower().replace("Â", "").replace("Î", "")
            if "own" in normalized_key and "owned" not in normalized_key:
                return value
        return ""

    def parse_percent(self, text):
        cleaned_text = text.replace("%", "").replace(",", "").replace("+", "").strip()
        if not cleaned_text:
            return None

        try:
            return float(cleaned_text)
        except ValueError:
            return None

    def handle_table_click(self, row_index, column_index):
        header_item = self.table.horizontalHeaderItem(column_index)
        cell_item = self.table.item(row_index, column_index)

        if header_item is None or cell_item is None:
            return

        header_text = header_item.text().lower()
        if "company" not in header_text and "insider" not in header_text:
            return

        filter_key = header_item.text()
        filter_value = cell_item.text()

        if self.active_text_filter == (filter_key, filter_value):
            self.active_text_filter = None
        else:
            self.active_text_filter = (filter_key, filter_value)

        self.apply_filter()

    def show_rows(self, rows):
        self.table.clear()

        if not rows:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        headers = list(rows[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, header in enumerate(headers):
                self.table.setItem(row_index, column_index, QTableWidgetItem(row.get(header, "")))

        self.table.resizeColumnsToContents()


def main():
    app = QApplication(sys.argv)
    window = BuyRadarWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
