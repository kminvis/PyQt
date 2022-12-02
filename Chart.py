import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from fbprophet import Prophet
import yfinance as yf
import pandas as pd
import datetime
import time
import requests
import json
from pytz import timezone
now = datetime.datetime.now()

MainForm = uic.loadUiType("main.ui")[0]
ChartForm = uic.loadUiType("chart.ui")[0]
TradeForm = uic.loadUiType("trade.ui")[0]

class MyWindow(QMainWindow, MainForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.predictionButton.clicked.connect(self.prediction)
        self.tradeButton.clicked.connect(self.trade)

    def layoutClear(self):
        for i in range(self.Layout.count()):
            self.Layout.itemAt(i).widget().deleteLater()

    def prediction(self):
        if self.status.text() != "차트예측":
            self.layoutClear()
            self.Layout.addWidget(predictionWindow())
            self.status.setText("차트예측")

    def trade(self):
        if self.status.text() != "자동매매":
            self.layoutClear()
            self.Layout.addWidget(tradeWindow())
            self.status.setText("자동매매")


class predictionWindow(QWidget, ChartForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.predictionButton.clicked.connect(self.chart)

    def chart(self):
        self.label_3.clear()
        self.label_5.clear()
        for i in range(self.prediction_verticalLayout.count()):
            self.prediction_verticalLayout.itemAt(i).widget().deleteLater()
        
        self.fig = plt.Figure()
        self.prediction_canvas = FigureCanvas(self.fig)
        self.prediction_verticalLayout.addWidget(self.prediction_canvas)

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
        self.start.clicked.connect(self.start_clicked)

    def start_clicked(self):
        a = Thread1(self)
        a.start()

class Thread1(QThread):
    #parent = MainWidget을 상속 받음.
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.power = True
        self.parent.stop.clicked.connect(self.stop_clicked)

    def stop_clicked(self):
        self.power = False
        self.quit()
        self.wait(3000)
        self.parent.textBrowser.append(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 자동매매 종료")

    def run(self):
        APP_KEY = self.parent.APP_KEY.text()
        APP_SECRET = self.parent.APP_SECRET.text()
        ACCESS_TOKEN = ""
        CANO = self.parent.CANO.text()
        ACNT_PRDT_CD = self.parent.ACNT_PRDT_CD.text()
        URL_BASE = "https://openapi.koreainvestment.com:9443"

        def send_message(msg):
            """디스코드 메세지 전송"""
            message = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}"
            self.parent.textBrowser.append(str(message))
            print(message)

        def get_access_token():
            """토큰 발급"""
            headers = {"content-type":"application/json"}
            body = {"grant_type":"client_credentials",
            "appkey":APP_KEY, 
            "appsecret":APP_SECRET}
            PATH = "oauth2/tokenP"
            URL = f"{URL_BASE}/{PATH}"
            res = requests.post(URL, headers=headers, data=json.dumps(body))
            ACCESS_TOKEN = res.json()["access_token"]
            return ACCESS_TOKEN
            
        def hashkey(datas):
            """암호화"""
            PATH = "uapi/hashkey"
            URL = f"{URL_BASE}/{PATH}"
            headers = {
            'content-Type' : 'application/json',
            'appKey' : APP_KEY,
            'appSecret' : APP_SECRET,
            }
            res = requests.post(URL, headers=headers, data=json.dumps(datas))
            hashkey = res.json()["HASH"]
            return hashkey

        def get_current_price(market="NAS", code="AAPL"):
            """현재가 조회"""
            PATH = "uapi/overseas-price/v1/quotations/price"
            URL = f"{URL_BASE}/{PATH}"
            headers = {"Content-Type":"application/json", 
                    "authorization": f"Bearer {ACCESS_TOKEN}",
                    "appKey":APP_KEY,
                    "appSecret":APP_SECRET,
                    "tr_id":"HHDFS00000300"}
            params = {
                "AUTH": "",
                "EXCD":market,
                "SYMB":code,
            }
            res = requests.get(URL, headers=headers, params=params)
            return float(res.json()['output']['last'])

        def get_target_price(market="NAS", code="AAPL"):
            """변동성 돌파 전략으로 매수 목표가 조회"""
            PATH = "uapi/overseas-price/v1/quotations/dailyprice"
            URL = f"{URL_BASE}/{PATH}"
            headers = {"Content-Type":"application/json", 
                "authorization": f"Bearer {ACCESS_TOKEN}",
                "appKey":APP_KEY,
                "appSecret":APP_SECRET,
                "tr_id":"HHDFS76240000"}
            params = {
                "AUTH":"",
                "EXCD":market,
                "SYMB":code,
                "GUBN":"0",
                "BYMD":"",
                "MODP":"0"
            }
            res = requests.get(URL, headers=headers, params=params)
            stck_oprc = float(res.json()['output2'][0]['open']) #오늘 시가
            stck_hgpr = float(res.json()['output2'][1]['high']) #전일 고가
            stck_lwpr = float(res.json()['output2'][1]['low']) #전일 저가
            target_price = stck_oprc + (stck_hgpr - stck_lwpr) * 0.5
            return target_price

        def get_movingaverage5(market="NAS", code="AAPL"):
            """5일 이동평균선 조회"""
            PATH = "uapi/overseas-price/v1/quotations/dailyprice"
            URL = f"{URL_BASE}/{PATH}"
            headers = {"Content-Type":"application/json", 
                "authorization": f"Bearer {ACCESS_TOKEN}",
                "appKey":APP_KEY,
                "appSecret":APP_SECRET,
                "tr_id":"HHDFS76240000"}
            params = {
                "AUTH":"",
                "EXCD":market,
                "SYMB":code,
                "GUBN":"0",
                "BYMD":"",
                "MODP":"0"
            }
            res = requests.get(URL, headers=headers, params=params)
            stck_clpr1 = float(res.json()['output2'][1]['clos']) #전일 종가
            stck_clpr2 = float(res.json()['output2'][2]['clos']) #2일전 종가
            stck_clpr3 = float(res.json()['output2'][3]['clos']) #3일전 종가
            stck_clpr4 = float(res.json()['output2'][4]['clos']) #4일전 종가
            stck_clpr5 = float(res.json()['output2'][5]['clos']) #5일전 종가
            movingaverage5 = (stck_clpr1 + stck_clpr2 + stck_clpr3 + stck_clpr4 + stck_clpr5)
            return movingaverage5

        def get_movingaverage20(market="NAS", code="AAPL"):
            """20일 이동평균선 조회"""
            PATH = "uapi/overseas-price/v1/quotations/dailyprice"
            URL = f"{URL_BASE}/{PATH}"
            headers = {"Content-Type":"application/json", 
                "authorization": f"Bearer {ACCESS_TOKEN}",
                "appKey":APP_KEY,
                "appSecret":APP_SECRET,
                "tr_id":"HHDFS76240000"}
            params = {
                "AUTH":"",
                "EXCD":market,
                "SYMB":code,
                "GUBN":"0",
                "BYMD":"",
                "MODP":"0"
            }
            res = requests.get(URL, headers=headers, params=params)
            stck_clpr1 = float(res.json()['output2'][1]['clos']) #전일 종가
            stck_clpr2 = float(res.json()['output2'][2]['clos']) #2일전 종가
            stck_clpr3 = float(res.json()['output2'][3]['clos']) #3일전 종가
            stck_clpr4 = float(res.json()['output2'][4]['clos']) #4일전 종가
            stck_clpr5 = float(res.json()['output2'][5]['clos']) #5일전 종가
            stck_clpr6 = float(res.json()['output2'][6]['clos']) 
            stck_clpr7 = float(res.json()['output2'][7]['clos']) 
            stck_clpr8 = float(res.json()['output2'][8]['clos']) 
            stck_clpr9 = float(res.json()['output2'][9]['clos']) 
            stck_clpr10 = float(res.json()['output2'][10]['clos']) 
            stck_clpr11 = float(res.json()['output2'][11]['clos'])
            stck_clpr12 = float(res.json()['output2'][12]['clos']) 
            stck_clpr13 = float(res.json()['output2'][13]['clos']) 
            stck_clpr14 = float(res.json()['output2'][14]['clos']) 
            stck_clpr15 = float(res.json()['output2'][15]['clos']) 
            stck_clpr16 = float(res.json()['output2'][16]['clos']) 
            stck_clpr17 = float(res.json()['output2'][17]['clos']) 
            stck_clpr18 = float(res.json()['output2'][18]['clos']) 
            stck_clpr19 = float(res.json()['output2'][19]['clos']) 
            stck_clpr20 = float(res.json()['output2'][20]['clos']) 
            movingaverage20 = (stck_clpr1 + stck_clpr2 + stck_clpr3 + stck_clpr4 + stck_clpr5 + stck_clpr6 + stck_clpr7 + stck_clpr8 + stck_clpr9 + stck_clpr10 + \
            stck_clpr11 + stck_clpr12 + stck_clpr13 + stck_clpr14 + stck_clpr15 + stck_clpr16 + stck_clpr17 + stck_clpr18 + stck_clpr19 + stck_clpr20) / 20
            return movingaverage20

        def get_noiseratio(market="NAS", code="AAPL"):
            """노이즈비율 조회"""
            PATH = "uapi/overseas-price/v1/quotations/dailyprice"
            URL = f"{URL_BASE}/{PATH}"
            headers = {"Content-Type":"application/json", 
                "authorization": f"Bearer {ACCESS_TOKEN}",
                "appKey":APP_KEY,
                "appSecret":APP_SECRET,
                "tr_id":"HHDFS76240000"}
            params = {
                "AUTH":"",
                "EXCD":market,
                "SYMB":code,
                "GUBN":"0",
                "BYMD":"",
                "MODP":"0"
            }
            res = requests.get(URL, headers=headers, params=params)
            stck_oprc1 = float(res.json()['output2'][1]['open']) #전일 시가
            stck_clpr1 = float(res.json()['output2'][1]['clos']) #전일 종가
            stck_hgpr1 = float(res.json()['output2'][1]['high']) #전일 고가
            stck_lwpr1 = float(res.json()['output2'][1]['low']) #전일 저가
            stck_oprc2 = float(res.json()['output2'][2]['open']) 
            stck_clpr2 = float(res.json()['output2'][2]['clos']) 
            stck_hgpr2 = float(res.json()['output2'][2]['high']) 
            stck_lwpr2 = float(res.json()['output2'][2]['low']) 
            stck_oprc3 = float(res.json()['output2'][3]['open']) 
            stck_clpr3 = float(res.json()['output2'][3]['clos']) 
            stck_hgpr3 = float(res.json()['output2'][3]['high']) 
            stck_lwpr3 = float(res.json()['output2'][3]['low']) 
            stck_oprc4 = float(res.json()['output2'][4]['open']) 
            stck_clpr4 = float(res.json()['output2'][4]['clos']) 
            stck_hgpr4 = float(res.json()['output2'][4]['high']) 
            stck_lwpr4 = float(res.json()['output2'][4]['low']) 
            stck_oprc5 = float(res.json()['output2'][5]['open']) 
            stck_clpr5 = float(res.json()['output2'][5]['clos']) 
            stck_hgpr5 = float(res.json()['output2'][5]['high']) 
            stck_lwpr5 = float(res.json()['output2'][5]['low']) 
            stck_oprc6 = float(res.json()['output2'][6]['open']) 
            stck_clpr6 = float(res.json()['output2'][6]['clos']) 
            stck_hgpr6 = float(res.json()['output2'][6]['high']) 
            stck_lwpr6 = float(res.json()['output2'][6]['low']) 
            stck_oprc7 = float(res.json()['output2'][7]['open']) 
            stck_clpr7 = float(res.json()['output2'][7]['clos']) 
            stck_hgpr7 = float(res.json()['output2'][7]['high']) 
            stck_lwpr7 = float(res.json()['output2'][7]['low']) 
            stck_oprc8 = float(res.json()['output2'][8]['open']) 
            stck_clpr8 = float(res.json()['output2'][8]['clos']) 
            stck_hgpr8 = float(res.json()['output2'][8]['high']) 
            stck_lwpr8 = float(res.json()['output2'][8]['low']) 
            stck_oprc9 = float(res.json()['output2'][9]['open']) 
            stck_clpr9 = float(res.json()['output2'][9]['clos']) 
            stck_hgpr9 = float(res.json()['output2'][9]['high']) 
            stck_lwpr9 = float(res.json()['output2'][9]['low']) 
            stck_oprc10 = float(res.json()['output2'][10]['open']) 
            stck_clpr10 = float(res.json()['output2'][10]['clos']) 
            stck_hgpr10 = float(res.json()['output2'][10]['high']) 
            stck_lwpr10 = float(res.json()['output2'][10]['low']) 
            stck_oprc11 = float(res.json()['output2'][11]['open']) 
            stck_clpr11 = float(res.json()['output2'][11]['clos']) 
            stck_hgpr11 = float(res.json()['output2'][11]['high']) 
            stck_lwpr11 = float(res.json()['output2'][11]['low']) 
            stck_oprc12 = float(res.json()['output2'][12]['open']) 
            stck_clpr12 = float(res.json()['output2'][12]['clos']) 
            stck_hgpr12 = float(res.json()['output2'][12]['high']) 
            stck_lwpr12 = float(res.json()['output2'][12]['low']) 
            stck_oprc13 = float(res.json()['output2'][13]['open']) 
            stck_clpr13 = float(res.json()['output2'][13]['clos']) 
            stck_hgpr13 = float(res.json()['output2'][13]['high']) 
            stck_lwpr13 = float(res.json()['output2'][13]['low']) 
            stck_oprc14 = float(res.json()['output2'][14]['open']) 
            stck_clpr14 = float(res.json()['output2'][14]['clos']) 
            stck_hgpr14 = float(res.json()['output2'][14]['high']) 
            stck_lwpr14 = float(res.json()['output2'][14]['low']) 
            stck_oprc15 = float(res.json()['output2'][15]['open']) 
            stck_clpr15 = float(res.json()['output2'][15]['clos']) 
            stck_hgpr15 = float(res.json()['output2'][15]['high']) 
            stck_lwpr15 = float(res.json()['output2'][15]['low']) 
            stck_oprc16 = float(res.json()['output2'][16]['open']) 
            stck_clpr16 = float(res.json()['output2'][16]['clos']) 
            stck_hgpr16 = float(res.json()['output2'][16]['high']) 
            stck_lwpr16 = float(res.json()['output2'][16]['low']) 
            stck_oprc17 = float(res.json()['output2'][17]['open']) 
            stck_clpr17 = float(res.json()['output2'][17]['clos']) 
            stck_hgpr17 = float(res.json()['output2'][17]['high']) 
            stck_lwpr17 = float(res.json()['output2'][17]['low']) 
            stck_oprc18 = float(res.json()['output2'][18]['open']) 
            stck_clpr18 = float(res.json()['output2'][18]['clos']) 
            stck_hgpr18 = float(res.json()['output2'][18]['high']) 
            stck_lwpr18 = float(res.json()['output2'][18]['low']) 
            stck_oprc19 = float(res.json()['output2'][19]['open']) 
            stck_clpr19 = float(res.json()['output2'][19]['clos']) 
            stck_hgpr19 = float(res.json()['output2'][19]['high']) 
            stck_lwpr19 = float(res.json()['output2'][19]['low'])
            stck_oprc20 = float(res.json()['output2'][20]['open']) 
            stck_clpr20 = float(res.json()['output2'][20]['clos']) 
            stck_hgpr20 = float(res.json()['output2'][20]['high']) 
            stck_lwpr20 = float(res.json()['output2'][20]['low'])
            noiseratio = 1 - (abs(stck_oprc1-stck_clpr1) / (stck_hgpr1-stck_lwpr1) + abs(stck_oprc2-stck_clpr2) / (stck_hgpr2-stck_lwpr2) + abs(stck_oprc3-stck_clpr3) / (stck_hgpr3-stck_lwpr3) + \
            abs(stck_oprc4-stck_clpr4) / (stck_hgpr4-stck_lwpr4) + abs(stck_oprc5-stck_clpr5) / (stck_hgpr5-stck_lwpr5) + abs(stck_oprc6-stck_clpr6) / (stck_hgpr6-stck_lwpr6) + \
            abs(stck_oprc7-stck_clpr7) / (stck_hgpr7-stck_lwpr7) + abs(stck_oprc8-stck_clpr8) / (stck_hgpr8-stck_lwpr8) + abs(stck_oprc9-stck_clpr9) / (stck_hgpr9-stck_lwpr9) + \
            abs(stck_oprc10-stck_clpr10) / (stck_hgpr10-stck_lwpr10) + abs(stck_oprc11-stck_clpr11) / (stck_hgpr11-stck_lwpr11) + abs(stck_oprc12-stck_clpr12) / (stck_hgpr12-stck_lwpr12) + \
            abs(stck_oprc13-stck_clpr13) / (stck_hgpr13-stck_lwpr13) + abs(stck_oprc14-stck_clpr14) / (stck_hgpr14-stck_lwpr14) + abs(stck_oprc15-stck_clpr15) / (stck_hgpr15-stck_lwpr15) + \
            abs(stck_oprc16-stck_clpr16) / (stck_hgpr16-stck_lwpr16) + abs(stck_oprc17-stck_clpr17) / (stck_hgpr17-stck_lwpr17) + abs(stck_oprc18-stck_clpr18) / (stck_hgpr18-stck_lwpr18) + \
            abs(stck_oprc19-stck_clpr19) / (stck_hgpr19-stck_lwpr19) + abs(stck_oprc20-stck_clpr20) / (stck_hgpr20-stck_lwpr20)) / 20
            return noiseratio

        def get_stock_balance():
            """주식 잔고조회"""
            PATH = "uapi/overseas-stock/v1/trading/inquire-balance"
            URL = f"{URL_BASE}/{PATH}"
            headers = {"Content-Type":"application/json", 
                "authorization":f"Bearer {ACCESS_TOKEN}",
                "appKey":APP_KEY,
                "appSecret":APP_SECRET,
                "tr_id":"JTTT3012R",
                "custtype":"P"
            }
            params = {
                "CANO": CANO,
                "ACNT_PRDT_CD": ACNT_PRDT_CD,
                "OVRS_EXCG_CD": "NASD",
                "TR_CRCY_CD": "USD",
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": ""
            }
            res = requests.get(URL, headers=headers, params=params)
            stock_list = res.json()['output1']
            evaluation = res.json()['output2']
            stock_dict = {}
            send_message(f"====주식 보유잔고====")
            for stock in stock_list:
                if int(stock['ovrs_cblc_qty']) > 0:
                    stock_dict[stock['ovrs_pdno']] = stock['ovrs_cblc_qty']
                    send_message(f"{stock['ovrs_item_name']}({stock['ovrs_pdno']}): {stock['ovrs_cblc_qty']}주")
                    time.sleep(0.1)
            send_message(f"주식 평가 금액: ${evaluation['tot_evlu_pfls_amt']}")
            time.sleep(0.1)
            send_message(f"평가 손익 합계: ${evaluation['ovrs_tot_pfls']}")
            time.sleep(0.1)
            send_message(f"=================")
            return stock_dict

        def get_balance():
            """현금 잔고조회"""
            PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
            URL = f"{URL_BASE}/{PATH}"
            headers = {"Content-Type":"application/json", 
                "authorization":f"Bearer {ACCESS_TOKEN}",
                "appKey":APP_KEY,
                "appSecret":APP_SECRET,
                "tr_id":"TTTC8908R",
                "custtype":"P",
            }
            params = {
                "CANO": CANO,
                "ACNT_PRDT_CD": ACNT_PRDT_CD,
                "PDNO": "005930",
                "ORD_UNPR": "65500",
                "ORD_DVSN": "01",
                "CMA_EVLU_AMT_ICLD_YN": "Y",
                "OVRS_ICLD_YN": "Y"
            }
            res = requests.get(URL, headers=headers, params=params)
            cash = res.json()['output']['ord_psbl_cash']
            send_message(f"주문 가능 현금 잔고: {cash}원")
            return int(cash)

        def buy(market="NASD", code="AAPL", qty="1", price="0"):
            """미국 주식 지정가 매수"""
            PATH = "uapi/overseas-stock/v1/trading/order"
            URL = f"{URL_BASE}/{PATH}"
            data = {
                "CANO": CANO,
                "ACNT_PRDT_CD": ACNT_PRDT_CD,
                "OVRS_EXCG_CD": market,
                "PDNO": code,
                "ORD_DVSN": "00",
                "ORD_QTY": str(int(qty)),
                "OVRS_ORD_UNPR": f"{round(price,2)}",
                "ORD_SVR_DVSN_CD": "0"
            }
            headers = {"Content-Type":"application/json", 
                "authorization":f"Bearer {ACCESS_TOKEN}",
                "appKey":APP_KEY,
                "appSecret":APP_SECRET,
                "tr_id":"JTTT1002U",
                "custtype":"P",
                "hashkey" : hashkey(data)
            }
            res = requests.post(URL, headers=headers, data=json.dumps(data))
            if res.json()['rt_cd'] == '0':
                send_message(f"[매수 성공]{str(res.json())}")
                return True
            else:
                send_message(f"[매수 실패]{str(res.json())}")
                return False

        def sell(market="NASD", code="AAPL", qty="1", price="0"):
            """미국 주식 지정가 매도"""
            PATH = "uapi/overseas-stock/v1/trading/order"
            URL = f"{URL_BASE}/{PATH}"
            data = {
                "CANO": CANO,
                "ACNT_PRDT_CD": ACNT_PRDT_CD,
                "OVRS_EXCG_CD": market,
                "PDNO": code,
                "ORD_DVSN": "00",
                "ORD_QTY": str(int(qty)),
                "OVRS_ORD_UNPR": f"{round(price,2)}",
                "ORD_SVR_DVSN_CD": "0"
            }
            headers = {"Content-Type":"application/json", 
                "authorization":f"Bearer {ACCESS_TOKEN}",
                "appKey":APP_KEY,
                "appSecret":APP_SECRET,
                "tr_id":"JTTT1006U",
                "custtype":"P",
                "hashkey" : hashkey(data)
            }
            res = requests.post(URL, headers=headers, data=json.dumps(data))
            if res.json()['rt_cd'] == '0':
                send_message(f"[매도 성공]{str(res.json())}")
                return True
            else:
                send_message(f"[매도 실패]{str(res.json())}")
                return False

        def get_exchange_rate():
            """환율 조회"""
            PATH = "uapi/overseas-stock/v1/trading/inquire-present-balance"
            URL = f"{URL_BASE}/{PATH}"
            headers = {"Content-Type":"application/json", 
                    "authorization": f"Bearer {ACCESS_TOKEN}",
                    "appKey":APP_KEY,
                    "appSecret":APP_SECRET,
                    "tr_id":"CTRP6504R"}
            params = {
                "CANO": CANO,
                "ACNT_PRDT_CD": ACNT_PRDT_CD,
                "OVRS_EXCG_CD": "NASD",
                "WCRC_FRCR_DVSN_CD": "01",
                "NATN_CD": "840",
                "TR_MKET_CD": "01",
                "INQR_DVSN_CD": "00"
            }
            res = requests.get(URL, headers=headers, params=params)
            exchange_rate = 1270.0
            if len(res.json()['output2']) > 0:
                exchange_rate = float(res.json()['output2'][0]['frst_bltn_exrt'])
            return exchange_rate

        # 자동매매 시작
        try:
            ACCESS_TOKEN = get_access_token()
            nasd_symbol_list = ["AAPL", "MSFT", "NVDA", "PYPL", "ADBE", "CSCO", "AMZN", "TSLA", "SBUX", "BKNG", "META", "GOOG", "CHTR", "TMUS", "CMCSA", "NFLX", \
            "HON", "PEP", "COST", "MDLZ", "EQIX"] # 매수 희망 종목 리스트 (NASD)
            nyse_symbol_list = ["V", "MA", "JNJ", "UNH", "PFE", "ABBV", "ABT", "CRM", "TMO", "MRK", "LLY", "DHR", "MDT", "HD", "NKE", "MCD", "LOW", "TGT", "TJX", \
            "JPM", "BAC", "WFC", "MS", "C", "GS", "BLK", "RTX", "AXP", "SPGI", "T", "DIS", "VZ", "UNP","BA", "CAT", "GE", "UPS", "DE", "MMM", "LMT", "PG", "WMT", \
            "KO", "MO", "PM", "CL", "KMB", "XOM", "CVX", "EOG", "SLB", "COP", "PXD", "MPC", "PSX", "AMT", "CCI", "LIN", "SHW", "APD", "NEE", "DUK"] # 매수 희망 종목 리스트 (NYSE)
            amex_symbol_list = ["LNG", "IMO", "CQP", "CBOE"] # 매수 희망 종목 리스트 (AMEX)
            symbol_list = nasd_symbol_list + nyse_symbol_list + amex_symbol_list
            bought_list = [] # 매수 완료된 종목 리스트
            total_cash = get_balance() # 보유 현금 조회
            exchange_rate = get_exchange_rate() # 환율 조회
            stock_dict = get_stock_balance() # 보유 주식 조회
            for sym in stock_dict.keys():
                bought_list.append(sym)
            target_buy_count = 3 # 매수할 종목 수
            buy_percent = 0.33 # 종목당 매수 금액 비율
            buy_amount = total_cash * buy_percent / exchange_rate # 종목별 주문 금액 계산 (달러)
            soldout = False

            send_message("===해외 주식 자동매매 프로그램을 시작합니다===")
            while self.power:
                t_now = datetime.datetime.now(timezone('America/New_York')) # 뉴욕 기준 현재 시간
                t_9 = t_now.replace(hour=9, minute=30, second=0, microsecond=0)
                t_start = t_now.replace(hour=9, minute=35, second=0, microsecond=0)
                t_sell = t_now.replace(hour=15, minute=40, second=0, microsecond=0)
                t_exit = t_now.replace(hour=15, minute=50, second=0,microsecond=0)
                today = t_now.weekday()
                if t_9 < t_now < t_start and soldout == False: # 잔여 수량 매도
                    for sym, qty in stock_dict.items():
                        market1 = "NASD"
                        market2 = "NAS"
                        if sym in nyse_symbol_list:
                            market1 = "NYSE"
                            market2 = "NYS"
                        if sym in amex_symbol_list:
                            market1 = "AMEX"
                            market2 = "AMS"
                        sell(market=market1, code=sym, qty=qty, price=get_current_price(market=market2, code=sym))
                    soldout == True
                    bought_list = []
                    time.sleep(1)
                    stock_dict = get_stock_balance()
                if t_start < t_now < t_sell :  # AM 09:35 ~ PM 03:40 : 매수
                    for sym in symbol_list:
                        if len(bought_list) < target_buy_count:
                            if sym in bought_list:
                                continue
                            market1 = "NASD"
                            market2 = "NAS"
                            if sym in nyse_symbol_list:
                                market1 = "NYSE"
                                market2 = "NYS"
                            if sym in amex_symbol_list:
                                market1 = "AMEX"
                                market2 = "AMS"
                            target_price = get_target_price(market2, sym)
                            current_price = get_current_price(market2, sym)
                            movingaverage5 = get_movingaverage5(market2, sym)
                            movingaverage20 = get_movingaverage20(market2, sym)
                            noiseratio = get_noiseratio(market2, sym)
                            if target_price < current_price and movingaverage5 < current_price and movingaverage20 < current_price and noiseratio < 0.5 :
                                buy_qty = 0  # 매수할 수량 초기화
                                buy_qty = int(buy_amount // current_price)
                                if buy_qty > 0:
                                    send_message(f"{sym} 목표가 달성({target_price} < {current_price}) 매수를 시도합니다.")
                                    market = "NASD"
                                    if sym in nyse_symbol_list:
                                        market = "NYSE"
                                    if sym in amex_symbol_list:
                                        market = "AMEX"
                                    result = buy(market=market1, code=sym, qty=buy_qty, price=get_current_price(market=market2, code=sym))
                                    time.sleep(1)
                                    if result:
                                        soldout = False
                                        bought_list.append(sym)
                                        get_stock_balance()
                            time.sleep(1)
                    time.sleep(1)
                    if t_now.minute == 30 and t_now.second <= 5: 
                        get_stock_balance()
                        time.sleep(5)
                if t_sell < t_now < t_exit:  # PM 03:40 ~ PM 03:50 : 일괄 매도
                    if soldout == False:
                        stock_dict = get_stock_balance()
                        for sym, qty in stock_dict.items():
                            market1 = "NASD"
                            market2 = "NAS"
                            if sym in nyse_symbol_list:
                                market1 = "NYSE"
                                market2 = "NYS"
                            if sym in amex_symbol_list:
                                market1 = "AMEX"
                                market2 = "AMS"
                            sell(market=market1, code=sym, qty=qty, price=get_current_price(market=market2, code=sym))
                        soldout = True
                        bought_list = []
                        time.sleep(1)
                if t_exit < t_now:  # PM 03:50 ~ :프로그램 종료
                    send_message("프로그램을 종료합니다.")
                    break
        except Exception as e:
            send_message(f"[오류 발생]{e}")
            time.sleep(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    app.exec_()