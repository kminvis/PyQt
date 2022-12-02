import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from fbprophet import Prophet
import yfinance as yf

MainForm = uic.loadUiType("main.ui")[0]
ChartForm = uic.loadUiType("chart.ui")[0]
TradeForm = uic.loadUiType("trade.ui")[0]

class MyWindow(QMainWindow, MainForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.predictionButton.clicked.connect(self.prediction)
        self.tradeButton.clicked.connect(self.trade)

    def prediction(self):
        if self.status.text() != "차트예측":
            for i in range(self.Layout.count()):
                self.Layout.itemAt(i).widget().deleteLater()
            self.Layout.addWidget(predictionWindow())
            self.status.setText("차트예측")

    def trade(self):
        if self.status.text() != "매매":
            for i in range(self.Layout.count()):
                self.Layout.itemAt(i).widget().deleteLater()
            self.Layout.addWidget(tradeWindow())
            self.status.setText("매매")


class predictionWindow(QWidget, ChartForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.fig = plt.Figure()
        self.prediction_canvas = FigureCanvas(self.fig)
        self.prediction_verticalLayout.addWidget(self.prediction_canvas)
        
        self.predictionButton.clicked.connect(self.chart)

    def chart(self):
        self.label_3.clear()
        self.label_5.clear()
        self.label_4.setText("로딩중")
        try:
            self.progressBar.setValue(5)
            code = self.lineEdit.text()
            code = code.upper()
            periods = self.spinBox.value()
            date = self.dateEdit.text()
            data = yf.download(code, start = date)

            data = data.rename(columns={'Close':'y'})
            data['ds'] = data.index 
            data = data[['ds', 'y']]

            m = Prophet(daily_seasonality = True)
            self.progressBar.setValue(20)
            m.fit(data)

            future = m.make_future_dataframe(periods=periods)
            self.progressBar.setValue(70)
            prediction = m.predict(future)
            m.plot(prediction)

            ax = self.fig.add_subplot(111)
            ax.plot(data['ds'], data['y'], label='price', color="black")
            ax.plot(prediction['ds'], prediction['yhat'], label='prediction', color="red")
            ax.plot(prediction['ds'], prediction['yhat_lower'], color="red")
            ax.plot(prediction['ds'], prediction['yhat_upper'], color="red")
            ax.legend(loc='upper right')
            ax.grid()

            self.prediction_canvas.draw()
            self.label_5.setText(code)
            self.label_4.setText("완료")
            self.progressBar.setValue(100)
        except:
            self.progressBar.setValue(0)
            self.label_5.clear()
            self.label_4.clear()
            self.label_3.setText("티커명 재확인 필요")

class tradeWindow(QWidget, TradeForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()