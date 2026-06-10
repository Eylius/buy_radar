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

        self.category_box = QComboBox()
        self.category_box.addItems(CATEGORIES.keys())
        self.category_box.currentTextChanged.connect(self.load_selected_data)

        self.load_button = QPushButton("Gespeicherte Daten laden")
        self.load_button.clicked.connect(self.load_selected_data)

        self.scrape_button = QPushButton("Neu scrapen")
        self.scrape_button.clicked.connect(self.scrape_selected_data)

        self.status_label = QLabel("Keine Daten geladen.")

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Kategorie:"))
        top_layout.addWidget(self.category_box)
        top_layout.addWidget(self.load_button)
        top_layout.addWidget(self.scrape_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        self.load_selected_data()

    def selected_category(self):
        return self.category_box.currentText()

    def load_selected_data(self):
        category_name = self.selected_category()
        rows = load_category_data(category_name)
        self.show_rows(rows)

        if rows:
            self.status_label.setText(f"{len(rows)} gespeicherte Einträge für '{category_name}' geladen.")
        else:
            self.status_label.setText(f"Keine gespeicherten Daten für '{category_name}' gefunden.")

    def scrape_selected_data(self):
        category_name = self.selected_category()
        self.set_controls_enabled(False)
        self.status_label.setText(f"Scraping läuft: {category_name}")
        QApplication.processEvents()

        try:
            rows = scrape_category(category_name)
        except Exception as error:
            QMessageBox.critical(self, "Fehler", str(error))
            self.status_label.setText(f"Fehler beim Scraping von '{category_name}'.")
        else:
            self.show_rows(rows)
            self.status_label.setText(f"{len(rows)} Einträge für '{category_name}' gescrapt und gespeichert.")
        finally:
            self.set_controls_enabled(True)

    def set_controls_enabled(self, enabled):
        self.category_box.setEnabled(enabled)
        self.load_button.setEnabled(enabled)
        self.scrape_button.setEnabled(enabled)

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
