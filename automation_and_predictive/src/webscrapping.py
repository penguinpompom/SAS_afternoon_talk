import os
import pandas as pd
from contextlib import closing
from selenium import webdriver
from selenium.webdriver import Chrome, Firefox
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
from collections import defaultdict
import json
import itertools
import random
from tqdm import tqdm
import requests
import pickle
from datetime import datetime

class GoBear:

    def __init__(self):

        try:

            self.browser = self.get_browser(driver='Firefox', logpath='./src/logs/geckodriver.log')
            self.browser.get('https://www.gobear.com/sg/')

            self.xpath                       = {}
            self.xpath['age_initialize']     = '//*[@id="car-form"]/div[1]/div[1]/div[1]/div[1]/div'
            self.xpath['day_field']          = '//*[@id="car-form"]/div[1]/div[1]/div[1]/div[2]/div[1]/input'
            self.xpath['month_field']        = '//*[@id="car-form"]/div[1]/div[1]/div[1]/div[2]/div[2]/input'
            self.xpath['year_field']         = '//*[@id="car-form"]/div[1]/div[1]/div[1]/div[2]/div[3]/input'
            self.xpath['marital_field']      = '//*[@id="car-form"]/div[1]/div[1]/div[2]/select'
            self.xpath['gender_field']       = '//*[@id="car-form"]/div[1]/div[1]/div[3]/div/select'
            self.xpath['driving_yrs_field']  = '//*[@id="car-form"]/div[1]/div[1]/div[4]/select'
            self.xpath['no_claims_field']    = '//*[@id="car-form"]/div[1]/div[2]/div[1]/div/select'
            self.xpath['car_year_field']     = '//*[@id="carDetails"]/div[1]/div/select'
            self.xpath['car_brand_field']    = '//*[@id="carDetails"]/div[2]/div/select'
            self.xpath['car_type_field']     = '//*[@id="carDetails"]/div[3]/div/select'
            self.xpath['show_result_button'] = '//*[@id="car-form"]/div[2]/div[2]/button[1]'
            self.xpath['results_landmark']   = '//div[@class="ad-column hidden-md hidden-sm hidden-xs"]'
            self.xpath['no_plan_matched']    = '//*[@id="car-quote-list"]/div[3]/div/p[1]'

            self.drop_down_fields            = ['marital_field', 'gender_field', 'driving_yrs_field', 'no_claims_field', 'car_year_field', 'car_brand_field']
            self.droplist                    = ['Make', '-----------------------', 'Model', 'Year']

            self.connected = True

        except:
            self.connected = False

    def exit(self):

        self.browser.quit()

    def get_proxy(self, filepath):

        if not os.path.isfile(filepath):

            response  = requests.get('https://www.sslproxies.org')
            soup      = BeautifulSoup(response.content, "html.parser")
            rows      = soup.findAll("tr")
            IP_list   = []
            PORT_list = []
            
            for row in rows:
                
                if(len(row.findAll("td")) == 8):
                    IP   = row.contents[0].contents[0]
                    PORT = row.contents[1].contents[0]
                    IP_list.append(IP)
                    PORT_list.append(PORT)

            proxy = pd.DataFrame({'IP': IP_list, 'PORT': PORT_list})
            proxy.to_csv(filepath, index=False)

        else:
            
            proxy = pd.read_csv(filepath)

        proxy = proxy.sample(frac=1).reset_index(drop=True)

        return proxy.loc[0, 'IP'], proxy.loc[0, 'PORT']

    def get_browser(self, driver, logpath):
            
        IP, PORT  = self.get_proxy('./config/proxy.csv')

        if driver == 'PhantomJS':

            string_proxy      = str(IP) + ':' + str(PORT)
            browser_headers   = { 'Accept'         :'*/*',
                                  'Accept-Encoding':'gzip, deflate, sdch',
                                  'Accept-Language':'en-US,en;q=0.8',
                                  'Cache-Control'  :'max-age=0',
                                  'User-Agent'     : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'}

            for key, value in enumerate(browser_headers):

                webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.{}'.format(key)] = value

            if len(string_proxy) <= 1:
                print('No Proxy will be used ...')
                browser = webdriver.PhantomJS()

            else:
                print('Using proxy: ', string_proxy)
                service_args = [
                        '--proxy=' + string_proxy + ':9999',
                        '--proxy-type=socks5'
                ]
                
                browser = webdriver.PhantomJS(service_args     = service_args,
                                              service_log_path = logpath)

        elif driver == 'Chrome':
            
            browser = Chrome(executable_path='./src/chromedriver')

        elif driver == 'Firefox':

            profile = webdriver.FirefoxProfile() 
            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.http", str(IP))
            profile.set_preference("network.proxy.http_port", str(PORT))
            profile.update_preferences() 

            browser = Firefox(firefox_profile=profile, log_path=logpath)

        return browser

    def option(self, selected_text):

        return '/option[text()="{0}"]'.format(selected_text)

    def fill_text(self, field, selected_text):

        input_field = self.browser.find_element_by_xpath(self.xpath[field])
        input_field.click()
        input_field.clear()
        input_field.send_keys(selected_text)

    def send_tab(self, field):

        time.sleep(0.5)
        input_field = self.browser.find_element_by_xpath(self.xpath[field])
        input_field.send_keys(Keys.TAB)

    def click_drop_down(self, field, selected_text):

        enter_option = self.xpath[field] + self.option(selected_text)
        self.browser.find_element_by_xpath(enter_option).click()

    def age_enter_DOB(self, day, month, year):

        DOB_option                = {}
        DOB_option['day_field']   = str(day)
        DOB_option['month_field'] = str(month)
        DOB_option['year_field']  = str(year)

        self.browser.find_element_by_xpath(self.xpath['age_initialize']).click()

        for field in DOB_option.keys():
            self.fill_text(field, DOB_option[field])

        self.send_tab('year_field')

    def marital_status(self, selected_text):

        self.click_drop_down('marital_field', 'Single')
        self.click_drop_down('marital_field', selected_text)

    def gender(self, selected_text):

        self.click_drop_down('gender_field', 'Male')
        self.click_drop_down('gender_field', selected_text)

    def driving_years(self, selected_text):

        self.click_drop_down('driving_yrs_field', '0')
        self.click_drop_down('driving_yrs_field', selected_text)

    def no_claims_discount(self, selected_text):

        self.click_drop_down('no_claims_field', '0%')
        self.click_drop_down('no_claims_field', selected_text)

    def car_bought_years(self, selected_text):

        self.click_drop_down('car_year_field', selected_text)

    def car_brand(self, selected_text):

        self.click_drop_down('car_brand_field', selected_text)

    def car_type(self, selected_text):

        enter_option = self.xpath['car_type_field'] + self.option(selected_text)

        WebDriverWait(self.browser, timeout=10).until(
            lambda x: x.find_element_by_xpath(enter_option))

        self.click_drop_down('car_type_field', selected_text)

    def submit(self):

        try:
            self.browser.find_element_by_xpath(self.xpath['show_result_button']).click()

            WebDriverWait(self.browser, timeout=10).until(
                lambda x: x.find_elements_by_xpath(self.xpath['results_landmark']) or \
                          x.find_elements_by_xpath(self.xpath['no_plan_matched']))
        except:
            pass

        self.page_source = self.browser.page_source

    def return_page_source(self):

        return self.page_source

    def get_caption(self, xpath_key):

        element       = self.browser.find_element_by_xpath(self.xpath[xpath_key])
        return element.text

    def get_option_caption(self, xpath_key):

        element       = self.browser.find_element_by_xpath(self.xpath[xpath_key])
        ls_parameters = [e.text for e in element.find_elements_by_tag_name('option')]
        ls_parameters = [i for i in ls_parameters if i not in self.droplist]
        ls_parameters = list(set(ls_parameters))

        return ls_parameters

    def get_parameters(self):

        self.parameters       = {}
        self.car_type_mapping = {}

        for field in self.drop_down_fields:
        
            if field == 'car_brand_field':

                self.parameters[field]            = self.get_option_caption(xpath_key=field)
                self.parameters['car_type_field'] = {}

                for f in self.parameters[field]:

                    self.car_brand(f)
                    time.sleep(1)
                    self.parameters['car_type_field'][f] = self.get_option_caption(xpath_key='car_type_field')
                    len_of_car_type                      = len(self.parameters['car_type_field'][f])
                    self.car_type_mapping[f]             = dict(zip(self.parameters['car_type_field'][f], range(len_of_car_type)))

            else:

                self.parameters[field] = self.get_option_caption(xpath_key=field)

        return self.parameters, self.car_type_mapping

def fetch_html(url, xpath):

    with closing(Chrome('./src/chromedriver')) as browser:
        
        browser.get(url)
        WebDriverWait(browser, timeout=10).until(
            lambda x: x.find_element_by_xpath(xpath))

        html = browser.page_source

    return html

def json_save(output, data):

    with open(output, 'w') as file:
        json.dump(data, file)

def json_load(input):

    with open(input, 'r') as file:
        data = json.load(file)

    return data

def get_parameters_file(parameters_filepath, car_type_mapping_filepath):

    if not os.path.isfile(parameters_filepath) or \
       not os.path.isfile(car_type_mapping_filepath):

        user                         = GoBear()
        parameters, car_type_mapping = user.get_parameters()
        json_save(parameters_filepath, parameters)
        json_save(car_type_mapping_filepath, car_type_mapping)

        user.exit()

    else:
        
        parameters       = json_load(parameters_filepath)
        car_type_mapping = json_load(car_type_mapping_filepath)

    return parameters, car_type_mapping

def random_day(month):

    day_dict = {1: 31, 2: 28, 3: 31, 4: 30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
    day      = random.randint(1, day_dict[month])

    return day

def get_policyprice_html(age, marital_status, gender, driving_years, no_claims_discount, car_bought_years, car_brand, car_type):

    user        = GoBear()
    month       = random.randint(1, 12)
    day         = random_day(month)
    today_month = datetime.today().month
    today_day   = datetime.today().day
    adjustment  = ((today_month, today_day) < (month, day))

    user.age_enter_DOB(day, month, 2017 - age - adjustment)
    user.marital_status(marital_status)
    user.gender(gender)
    user.driving_years(driving_years)
    user.no_claims_discount(no_claims_discount)
    user.car_bought_years(car_bought_years)
    user.car_brand(car_brand)
    user.car_type(car_type)
    user.submit()
    
    html = user.return_page_source()
    user.exit()

    return html

def get_all_output(src):

    files = os.listdir(src)
    files = [f for f in files if not f.startswith('.')]
    data  = []

    for f in files:
        
        filepath = os.path.join(src, f)
        data.append(pd.read_csv(filepath))

    data  = pd.concat(data)

    return data

if __name__ == '__main__':

    user_parameters, car_type_mapping = get_parameters_file('./config/parameters.json', './config/car_type_mapping.json')

    age_ls                = range(18, 65 + 1)
    marital_status_ls     = user_parameters['marital_field']
    gender_ls             = user_parameters['gender_field']
    driving_years_ls      = user_parameters['driving_yrs_field']
    no_claims_discount_ls = user_parameters['no_claims_field']
    car_bought_years_ls   = user_parameters['car_year_field']
    car_brand_ls          = user_parameters['car_brand_field']
    car_type_dict         = user_parameters['car_type_field']
    combi_ls              = []
    n_failures            = 0

    for combination in itertools.product(age_ls, marital_status_ls, gender_ls, driving_years_ls, \
                                         no_claims_discount_ls, car_bought_years_ls, car_brand_ls):
        combi_ls.append(combination)

    random.shuffle(combi_ls)

    for combination in tqdm(combi_ls):

        age                = combination[0]
        marital_status     = combination[1]
        gender             = combination[2]
        driving_years      = combination[3]
        no_claims_discount = combination[4]
        car_bought_years   = combination[5]
        car_brand          = combination[6]
        car_type           = random.choice(car_type_dict[car_brand])
        car_type_mapped    = car_type_mapping[car_brand][car_type]

        filepath           = './output/{age}_{marital_status}_{gender}_{driving_years}_' \
                                      '{no_claims_discount}_{car_bought_years}_' \
                                      '{car_brand}_{car_type}.csv'.format(age=age, marital_status=marital_status, 
                                                                          gender=gender, driving_years=driving_years, 
                                                                          no_claims_discount=no_claims_discount,
                                                                          car_bought_years=car_bought_years, 
                                                                          car_brand=car_brand, car_type=car_type_mapped)

        if os.path.isfile(filepath):
            continue

        try: 

            html               = get_policyprice_html(age, marital_status, gender, driving_years, no_claims_discount, 
                                                      car_bought_years, car_brand, car_type)
            soup               = BeautifulSoup(html, 'html.parser')
            content            = soup.find_all('div', {'class': 'col-sm-4 card-full'})
            
            providers, titles, prices, reviews, score = [], [], [], [], []
            benefit_data                              = defaultdict(list)

            for tag in content:

                provider_name  = tag.find('h4',  {'class': 'name'}).getText()
                plan_title     = tag.find('div', {'class': 'card-title text-center'}).getText()
                plan_price     = tag.find('div', {'class': 'policy-price'}).getText()
                n_reviews      = tag.find('p',   {'class': 'card-link'}).getText()
                coverage_score = tag.find('div', {'class': 'coverage-score'}).getText()

                benefits_ls    = tag.find_all('p', {'class': 'col-xs-6 detail-key'})
                benefits_v_ls  = tag.find_all('p', {'class': 'col-xs-6 text-right detail-value'})

                for x, y in zip(benefits_ls, benefits_v_ls):

                    benefit_name = x.getText()
                    benefit_spec = y.getText()
                    benefit_data[benefit_name].append(benefit_spec)

                providers.append(provider_name)
                titles.append(plan_title)
                prices.append(plan_price)
                reviews.append(n_reviews)
                score.append(coverage_score)

            data = pd.DataFrame({'Companies'    : providers, 
                                 'Title'        : titles,
                                 'Prices'       : prices,
                                 'Reviews'      : reviews,
                                 'Cov_Score'    : score})

            for key in benefit_data:
                data[key] = benefit_data[key]

            data['age']                = age
            data['marital_status']     = marital_status
            data['gender']             = gender
            data['driving_years']      = driving_years
            data['no_claims_discount'] = no_claims_discount
            data['car_bought_years']   = car_bought_years
            data['car_brand']          = car_brand
            data['car_type']           = car_type

            data.to_csv(filepath, index=False)

        except:
            
            n_failures += 1
            tqdm.write(str(n_failures) + ':' + filepath)
            time.sleep(random.random() * 5 + n_failures * 2)

    print('done.')

