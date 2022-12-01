import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from fbprophet import Prophet
import yfinance as yf

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("chart.ui", self)
        self.setupUI()

    def setupUI(self):
        self.fig1 = plt.Figure()
        self.prediction_canvas = FigureCanvas(self.fig1)
        self.prediction_verticalLayout.addWidget(self.prediction_canvas)

        self.pushButton.clicked.connect(self.pushButtonClicked)
    def pushButtonClicked(self):
        code = self.lineEdit.text()
        date = self.dateEdit.text()
        data = yf.download(code, start = date)

        data = data.rename(columns={'Close':'y'})
        data['ds'] = data.index 
        data = data[['ds', 'y']]

        m = Prophet(daily_seasonality = True)
        m.fit(data)

        future = m.make_future_dataframe(periods=365)
        prediction = m.predict(future)
        m.plot(prediction)

        ax = self.fig1.add_subplot(111)
        ax.plot(data['ds'], data['y'], color="black")
        ax.plot(prediction['ds'], prediction['yhat'], color="red")
        ax.plot(prediction['ds'], prediction['yhat_lower'], color="red")
        ax.plot(prediction['ds'], prediction['yhat_upper'], color="red")

        self.prediction_canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()