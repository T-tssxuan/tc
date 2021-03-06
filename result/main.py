import sys
import pandas as pd
import numpy as np
from generate_predict import generate_predict
from generate_ap_ratio_info import  generate_ap_ratio_info
from generate_base_data import generate_base_data
from generate_flight_passenger import generate_flight_passenger
from generate_pure_variation import generate_pure_variation
from output_predict import output_predict
from input_predict import input_predict
from log import log
from multiprocessing import Process

def p_generate_output_predict(range_start, range_end, directory):
    log('start p_generate_output_predict process')
    log('range_start: ' + range_start + ' range_end: ' + range_end +
            ' directory: ' + directory)
    op = output_predict(range_start, range_end, directory)

def p_generate_input_predict(range_start, range_end, directory, category):
    log('start p_generate_input_predict process')
    log('range_start: ' + range_start + ' range_end: ' + range_end +
            ' directory: ' + directory + ' category: ' + str(category))
    ip = input_predict(0, directory)
    ip.train(range_start, range_end)

def p_generate_base_data(directory, start):
    log('start p_generate_base_data')
    log('directory: ' + directory + ' start: ' + str(start))
    generate_base_data(directory, start)



if __name__ == '__main__':
    directory = './data1/'
    fmt = '%Y-%m-%d-%H-%M-%S'

    # get the dirtory of source data need to predicting
    if len(sys.argv) >= 2:
        directory = sys.argv[1]

    if directory == './data1/':
        range_start = '2016/09/10 00:00:00'
        range_end = '2016/09/15 00:00:00'
        start = '2016-09-14-15-00-00'
        end = '2016-09-14-18-00-00'
    else:
        range_start = '2016/09/10 00:00:00'
        range_end = '2016/09/26 00:00:00'
        start = '2016-09-25-15-00-00'
        end = '2016-09-25-18-00-00'


    # get the prediction range 
    if len(sys.argv) >= 4:
        if pd.notnull(pd.to_datetime(sys.argv[2], format=fmt)) \
                and pd.notnull(pd.to_datetime(sys.argv[3], format=fmt)):
            start = sys.argv[2]
            end = sys.argv[3]
        else:
            print('Please input time in the form: YYYY-MM-DD-HH-MM-SS')

    log('directory: ' + directory)
    log('start: ' + start + ' end: ' + end)
    log('range_start: ' + range_start + ' range_end: ' + range_end)

    start = pd.to_datetime(start, format=fmt)
    end = pd.to_datetime(end, format=fmt)

    # generate the pasenger number stastistic info for each flight id
    log('generate the passenger number')
    generate_flight_passenger(directory)

    # generate airport output predict for each area
    log('genrate output predict for each area')
    p_out = Process(
            target=p_generate_output_predict, 
            args=(range_start, range_end, directory)
            )
    p_out.start()

    # generate airport checkin input predict for each area
    log('generate checkin predict')
    p_cip = Process(
            target=p_generate_input_predict,
            args=(range_start, range_end, directory, 0)
            )
    p_cip.start()

    # generate airport security predict for each area
    log('generate security predict')
    p_sip = Process(
            target=p_generate_input_predict,
            args=(range_start, range_end, directory, 1)
            )
    p_sip.start()

    # generate the base data for prediction
    log('generate the base data')
    p_base_data = Process(
            target=p_generate_base_data,
            args=(directory, start)
            )
    p_base_data.start()

    p_out.join()
    p_cip.join()
    p_sip.join()
    p_base_data.join()

    log('finish processes')

    # generate purely variation for each area
    log('generate pure variation predict')
    generate_pure_variation()


    log('predict the result')
    generate_predict(directory, start, end)

    log('finish')
