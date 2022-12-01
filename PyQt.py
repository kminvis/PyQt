import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
from pandas import Series, DataFrame
from fbprophet import Prophet
import yfinance as yf

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self):
        self.setGeometry(600, 200, 1200, 600)
        self.setWindowTitle("PyChart Viewer v0.1")
        self.setWindowIcon(QIcon('icon.png'))

        self.lineEdit = QLineEdit()
        self.pushButton = QPushButton("차트그리기")
        self.pushButton.clicked.connect(self.pushButtonClicked)

        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)

        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.canvas)

        # Right Layout
        rightLayout = QVBoxLayout()
        rightLayout.addWidget(self.lineEdit)
        rightLayout.addWidget(self.pushButton)
        rightLayout.addStretch(1)

        layout = QHBoxLayout()
        layout.addLayout(leftLayout)
        layout.addLayout(rightLayout)
        layout.setStretchFactor(leftLayout, 1)
        layout.setStretchFactor(rightLayout, 0)

        self.setLayout(layout)

    def pushButtonClicked(self):
        code = self.lineEdit.text()
        data = yf.download(code, start = '2020-01-01')

        data = data.rename(columns={'Close':'y'})
        data['ds'] = data.index 
        data = data[['ds', 'y']]

        m = Prophet(daily_seasonality = True)
        m.fit(data)

        future = m.make_future_dataframe(periods=365)
        prediction = m.predict(future)
        m.plot(prediction)

        ax = self.fig.add_subplot(111)
        ax.plot(data['ds'], data['y'], color="black")
        ax.plot(prediction['ds'], prediction['yhat'], color="red")
        ax.plot(prediction['ds'], prediction['yhat_lower'], color="red")
        ax.plot(prediction['ds'], prediction['yhat_upper'], color="red")

        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()