import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class input_predict:
    '''
    This class is using to predict the input of the airport based on the check 
    in information of the airport.
    '''
    def __init__(self, category, directory):
        self.directory = directory
        path = directory + 'airport_gz_flights_chusai.csv'
        sdata = pd.read_csv(path)
        del sdata['actual_flt_time']
        sdata.columns = ['fid', 'sft', 'gate']
        sdata['fid'] = sdata['fid'].str.upper()
        sdata['fid'] = sdata['fid'].str.replace(' ', '')
        sdata['sft'] = pd.to_datetime(sdata['sft'])
        sdata['sft'] = sdata['sft'].add(pd.DateOffset(hours=8))
        sdata['gate'] = sdata['gate'].str.upper()
        sdata['gate'] = sdata['gate'].str.replace(' ', '')
        sdata['gate'] = sdata['gate'].astype(str)
        sdata['gate'] = sdata['gate'].apply(lambda x: x.split(',')[-1])
        self.sdata = sdata
        self.__bind_area_for_fid()
        del self.sdata['gate']

        # init the predict base data
        if category == 0:
            self.rst_file_name = './info/checkin_predict.csv'
            self.cdata = self.__init_checkin_data()
        else:
            self.rst_file_name = './info/security_predict.csv'
            self.cdata = self.__init_security_data()

        pdata = pd.read_csv('./info/flight_passenger_num.csv')
        pdata.columns = ['fid', 'num']
        pdata['fid'] = pdata['fid'].str.replace(' ', '')
        pdata = pdata.set_index('fid')
        self.pdata = pdata

        # get the mean and the std of the flight passenger num to fill the blank
        self.pstd = pdata.std()[0]
        self.pmean = pdata.mean()[0]

    def __init_security_data(self):
        print('init the security data')
        path = directory + 'airport_gz_security_check_chusai.csv'
        data = pd.read_csv(path)
        del data['passenger_ID']
        data.columns = ['ct', 'fid']
        data['ct'] = pd.to_datetime(data['ct'])
        data['fid'] = data['fid'].str.upper()
        data['fid'] = data['fid'].str.replace(' ', '')

        sdata = self.sdata.copy()

        data = data[data['fid'].isin(sdata['fid'])]

        sdata = sdata.set_index('fid')
        sdata = sdata.sort_values('sft')
        
        def func(x):
            val = tmp.loc[x['fid'], 'sft']
            if type(val) is pd.tslib.Timestamp:
                return val
            eles = val.values
            for ele in eles:
                if x['ct'] <= pd.to_datetime(ele) + pd.DateOffset(hours=5):
                    return pd.to_datetime(ele)
            return pd.to_datetime(eles[-1])

        data['ft'] = data.apply(func, axis=1)

        return data[['fid', 'ft', 'ct']]

    def __init_checkin_data(self):
        print('init the checkin data')
        path = directory + 'airport_gz_departure_chusai.csv'
        data = pd.read_csv(path)
        del data['passenger_ID2']
        data.columns = ['fid', 'ft', 'ct']
        data['fid'] = data['fid'].str.upper()
        data['fid'] = data['fid'].str.replace(' ', '')
        data['ft'] = pd.to_datetime(data['ft'])
        data['ct'] = pd.to_datetime(data['ct'])
        data = data[pd.notnull(data['ft'])]
        data = data[pd.notnull(data['ct'])]

        return data


    # start/end: YYYY/MM/DD HH:MM:SS
    def get_predict_area(self, start, end, gran=10):
        print('get the predict data base area')
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)

        tmp = self.rst[
                self.rst['timeStamp'] >= start & self.rst['timeStamp'] <= end
                ]
        tmp = tmp.groupby(
                [pd.Grouper(key='timeStamp', freq=gran), 'area']
                ).sum()

        tmp = tmp.reset_index()
        return tmp


    def get_predict_sum(self, start, end, gran=10):
        print('get the sum predict data')
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
        gran = str(gran) + 'Min'

        tmp = self.rst.copy()
        del tmp['area']

        tmp = tmp[tmp['timeStamp'] >= start & tmp['timeStamp'] <= end]

        tmp = tmp.groupby(pd.Grouper(key='timeStamp', freq=gran)).sum()
        
        tmp = tmp.reset_index()

        return tmp


    def train(self, start, end):
        print('training')
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)

        train_data = self.__get_train_data()
        train_result = [[train_data[co].mean(), train_data[co].std()] 
                for co in train_data.columns]
        
        self.train_result = train_result
        self.train_data = train_data
        self.train_std = train_data.std()
        self.train_mean = train_data.mean()

        rst = self.__init_rst(start, end)

        for idx, row in self.sdata.iterrows():
            p_num = np.random.randn() * self.pstd + self.pmean
            if row['fid'] in self.pdata.index:
                p_num = self.pdata.loc[row['fid'], 'num']

            tmp = self.__spread(row['sft'], row['area'], p_num)
            rst = rst.append(tmp)

        rst['timeStamp'] = pd.to_datetime(rst['timeStamp'])
        rst = rst.groupby(['timeStamp', 'area']).sum()
        rst = rst.sort_index()
        rst = rst.reset_index()
        rst = rst[(rst['timeStamp'] >= start) & (rst['timeStamp'] <= end)]
        rst.to_csv(
                self.rst_file_name,
                columns=['timeStamp', 'area', 'num'], 
                index=True
                )
        self.rst = rst
        print('finish training')

    def __init_rst(self, start, end):
        print('init rst content')
        data = pd.DataFrame()

        time_rng = pd.date_range(start, end, freq='1Min')
        eles = ['E1', 'E2', 'E3', 'W1', 'W2', 'W3', 'EC', 'WC']
        for ele in eles:
            tmp = pd.DataFrame(
                    np.array([
                        time_rng,
                        [ele for i in range(len(time_rng))],
                        [0 for i in range(len(time_rng))]
                        ]).transpose()
                    )
            data = data.append(tmp)
        return data

    def __spread(self, sft, area, p_num):
        # print(str(p_num) + ' ' + str(type(p_num)))
        # print(str(sft))
        # print(str(area))
        before = pd.DateOffset(hours=-5)
        after = pd.DateOffset(hours=2)

        num = np.array([
            np.random.randn() * self.train_std[i] + self.train_mean[i]
            for i in range(len(self.train_std))
            ])
        num = num * p_num

        time = pd.date_range(sft + before, sft + after, freq='1Min').values
        
        areas = pd.Series([area for i in range(len(self.train_std))]).values

        columns = ['timeStamp', 'area', 'num']

        rst = pd.DataFrame(
            np.array([time, areas, num]).transpose(), 
            columns=columns
            )

        return rst


    def __get_train_data(self):
        print('get train data')
        data = self.cdata.copy()

        idx = 0

        before = pd.DateOffset(hours=-5)
        after = pd.DateOffset(hours=2)
        data = data.groupby(['fid', 'ft'])

        rst = pd.DataFrame()

        for fid, ft in data.groups:
            sub_data = data.get_group((fid, ft))
            sub_data = sub_data[sub_data['ct'] >= ft + before]
            sub_data = sub_data[sub_data['ct'] <= ft + after]

            tmp_idx = pd.date_range(ft + before, ft + after, freq='1Min')
            tmp = pd.Series([0 for i in range(len(tmp_idx))], index=tmp_idx)

            del sub_data['ft']
            del sub_data['fid']

            total = sub_data.shape[0]
            if total == 0:
                continue

            sub_data = sub_data.groupby(pd.Grouper(key='ct', freq='1Min')).size()
            del sub_data.index.name

            sub_data = tmp.add(sub_data)
            sub_data = sub_data.fillna(0)
            sub_data = sub_data.divide(total)

            sub_data = pd.DataFrame([sub_data.values], index=[idx])

            rst = pd.concat([rst, sub_data])
            idx += 1

        return rst
    
    def __bind_area_for_fid(self):
        print('fill area according to the flight gate')
        gate = pd.read_csv(self.directory + './airport_gz_gates.csv')
        gate.columns = ['gate', 'area']
        gate['gate'] = gate['gate'].str.upper()
        gate['gate'] = gate['gate'].str.replace(' ', '')
        gate['area'] = gate['area'].str.upper()
        gate['area'] = gate['area'].str.replace(' ', '')
        gate = gate.set_index('gate')

        tmp = ['E1', 'E2']
        def func(x):
            if x in gate.index:
                return gate.loc[x, 'area']
            else:
                return tmp[np.random.randint(2)]
        self.sdata['area'] = self.sdata['gate'].apply(func)

if __name__ == '__main__':
    ip = input_predict(0, './data1/')
    ip.train('2015/09/10 00:00:00', '2015/09/15 00:00:00')
