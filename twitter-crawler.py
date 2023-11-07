from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import time
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import pickle
from kafka import KafkaProducer
import json 
import os
from tqdm import tqdm
import argparse
CHROME_BINARY_LOCATION = "/usr/bin/chrome-linux64/chrome"
CHROMEDRIVER_BINARY_LOCATION = "/usr/bin/chromedriver-linux64/chromedriver"

def add_driver_options(options):
    """
    Add configurable options
    """
    chrome_options = Options()
    for opt in options:
        chrome_options.add_argument(opt)
    return chrome_options

def initialize_driver():
    """
    Initialize the web driver
    """
    driver_config = {
        "options": [
            "--headless",
            "--no-sandbox",
            "--allow-insecure-localhost",
            "--disable-dev-shm-usage",
            "--incognito",
            "--window-size=1920x1080"
            "user-agent=Chrome/116.0.5845.96"
        ],
    }
    options = add_driver_options(driver_config["options"])
    options.binary_location = CHROME_BINARY_LOCATION
    driver = webdriver.Chrome(
        executable_path=CHROMEDRIVER_BINARY_LOCATION,
        options=options)
    return driver

class TwitterCrawler:
    def __init__(self, producer: KafkaProducer = None, hashtags: list = None, kaggle = 0):
        if kaggle == 0:
            chrome_options = Options()
            chrome_options.add_argument("--incognito")
            chrome_options.add_argument("--window-size=1920x1080")
            self.driver = webdriver.Chrome(ChromeDriverManager().install(), options = chrome_options)
        else:
            self.driver = initialize_driver()
        self.hashtags = hashtags
        self.producer = producer
        self.groups = []
        self.save_file = f"./crawled_data" 
        os.makedirs(f"{self.save_file}/all_users", exist_ok=True)
        os.makedirs(f"{self.save_file}/groups", exist_ok=True)
        os.makedirs(f"{self.save_file}/user_info", exist_ok=True)

    def log_in(self, username, password):
        self.driver.get("https://twitter.com/")
        time.sleep(2)
        self.driver.find_element("xpath","//a[@href='/login']").click()
        time.sleep(2)
        self.driver.find_element("xpath","//label").click()
        self.driver.find_element("xpath","//label").send_keys(username)
        self.driver.find_element("xpath",'//div[@role="button" and contains(@style,"background-color")]').click()
        time.sleep(2)
        self.driver.find_elements("xpath",'//input')[1].send_keys(password)
        self.driver.find_element("xpath",'//div[@data-testid="LoginForm_Login_Button"]').click()
        time.sleep(3)
        
    def crawl_username_from_hashtag(self,hashtag):
        list_users = []
        self.driver.get(f'https://twitter.com/search?q=%23{hashtag}&src=hashtag_click&f=user')
        time.sleep(3)
        for i in range(70):
            self.driver.execute_script(f"window.scrollTo(0,{600*i})")
            time.sleep(1)
            users = self.driver.find_elements("xpath", f'//a[starts-with(@href,"/") and contains (@role,"link") and contains (@tabindex,"-1") and contains (@aria-hidden,"true")]')
            for user in users:
                try:
                    list_users.append(user.get_attribute('href').split('/')[3])
                except:
                    continue
        
        return list(set(list_users))
    
    def get_users_name_from_an_account(self, url, crawl_type = 'both', windows = 'main',steps = 10, step_size = 3000):
        '''
        url: link to the account
        crawl_type: 'followers' or 'following' or 'both'
        windows: 'main' or 'popup'
        '''
        if crawl_type == 'both':    
            types = ['followers', 'following']
        else:
            types = [crawl_type]
        
        name_list = []
        for type in types:
            if url is not None:
                self.driver.get(f'{url}/{type}')
                time.sleep(2)
            
            for i in range(steps):
                if windows == 'main':
                    self.driver.execute_script(f"window.scrollTo(0,{step_size*i})")
                else:
                    actions = ActionChains(self.driver)
                    actions.scroll(550, 550, 0, step_size).perform() 
                time.sleep(1)  # Adjust this value as needed
                users = self.driver.find_elements("xpath", '//a[starts-with(@href,"/") and contains (@role,"link") and contains (@tabindex,"-1") and not(@aria-hidden)]')#elem = list(set(elem))
                for user in users:
                    try:
                        name_list.append(user.get_attribute('href').split('/')[3])
                    except:
                        continue
        return (name_list)

    def process_number(self,number):
        if 'K' in number:
            return int(float(number.replace('K',''))*1000)
        elif 'M' in number:
            return int(float(number.replace('M',''))*1000000)
        else:
            return int(number)
        
    def get_all_users_from_groups(self, keyword):
        self.driver.get(f"https://twitter.com/search?q={keyword}&src=typed_query&f=list")
        time.sleep(7)
        actions = ActionChains(self.driver)
        groups_dict = {}
        iter = 0
        request = 0
        crawled_groups = self.load_crawled_groups(keyword)
        all_users = self.load_username(keyword)
        while iter < 40:
            users = []
            members = []
            #scroll down a bit
            if iter != 0:
                self.driver.execute_script(f"window.scrollTo(0,{2000*iter})")
#            else:
#                self.driver.execute_script(f"window.scrollTo(0,500)")
            time.sleep(4)
            #get all groups in this frame
            groups = self.driver.find_elements("xpath", '//img[@draggable="true" and starts-with(@src,"https://pbs.twimg.com/list_banner_img")]')
            groups.extend(self.driver.find_elements("xpath","//img[@draggable='true' and starts-with(@src,'https://pbs.twimg.com/media')]"))
            for group in groups:
                try:
                    actions.move_to_element(group).perform()
                    time.sleep(1)

                    group_owner = self.driver.find_elements("xpath",'//a[starts-with(@href,"/") and contains(@role,"link") and contains(@tabindex,"-1")]')[1].get_attribute('href').split('/')[3]
                    if group_owner in crawled_groups:
                        print(f"Group already crawled: {keyword}-{group_owner}")
                        actions.move_to_element(self.driver.find_elements("xpath",'//a[@href="/home"]')[0]).perform()
                        time.sleep(2)
                        continue
                    
                    group_name = keyword + '-'+  group_owner
                    
                    if group_name not in groups_dict.keys():
                        #return 2 elements: members and followers
                        elements = self.driver.find_elements("xpath",f'//a[starts-with(@href,"/i/lists")]')
                        
                        #get members
                        num_member = self.driver.find_elements("xpath",'//a[starts-with(@href,"/i/lists")]/*/*')[0].text
                                        
                        elements[0].click()
                        time.sleep(1)
                        steps = self.process_number(num_member)//20
                        request += steps
                        members.extend(self.get_users_name_from_an_account(None, 'both', 'popup', steps))
                        
                        self.driver.find_element("xpath",f'//div[@aria-label="Close"]').click()
                        
                        #get followers
                        num_followers = self.driver.find_elements("xpath", '//a[contains(@href,"/followers")]/*/*')[0].text
                        elements[1].click()
                        time.sleep(1)
                        num_followers = self.process_number(num_followers)
                        steps = num_followers//40 if num_followers < 2000 else 50
                        request += steps
                        users.extend(self.get_users_name_from_an_account(None, 'both', 'popup', steps))
                        
                        self.driver.find_element("xpath",f'//div[@aria-label="Close"]').click()

                        
                        actions.move_to_element(self.driver.find_elements("xpath",'//a[@href="/home"]')[0]).perform()
                        
                        groups_dict[group_name] = {'num_member': num_member, 'num_followers': num_followers, 'members': members, 'followers': users}
                        all_users.extend(users)
                        all_users.extend(members)
                        all_users = list(set(all_users))
                        
                        print('Finish crawling group: ', group_name)
                        
                        #Write to file
                        with open(f"{self.save_file}/groups/{group_name}.pkl", "wb") as f:
                            pickle.dump(groups_dict[group_name], f)
                            
                        #Write to kafka
                        self.producer.send(f"{keyword}_{group_name}", pickle.dumps(groups_dict[group_name]))
                        with open(f"{self.save_file}/all_users/{keyword}.pkl", "wb") as f:
                            pickle.dump(all_users, f)

                        if request > 70:
                            time.sleep(60*3)
                            request = 0

                        

                except:
                    continue
            iter += 1
            print(iter)
        return all_users, groups_dict
    
    def extract_to_dictionary(self,text):
        data_dict = {'replies': 0, 'reposts': 0, 'likes': 0, 'views': 0, 'bookmarks': 0}
        data = text.split(',')
        for item in data:
            item = item.strip()
            if 'repl' in item:
                data_dict['replies'] = int(item.split()[0])
            elif 'repost' in item:
                data_dict['reposts'] = int(item.split()[0])
            elif 'like' in item:
                data_dict['likes'] = int(item.split()[0])
            elif 'bookmark' in item:
                data_dict['bookmarks'] = int(item.split()[0])

            elif 'views' in item:
                data_dict['views'] = int(item.split()[0])

        return data_dict
    
    def retrieve_tweets(self, username):
        count = 0
        iter = 1
        tweet_dict = {}
        while iter < 6 and count < 20:
            tweets = self.driver.find_elements("xpath","//article[@tabindex='0']")
            for i in range(len(tweets)):
                tweet_time = tweets[i].find_element("xpath",".//time[@datetime and @datetime!='none']")
                tweet_time = tweet_time.get_attribute('datetime') + ''
                if tweet_time in tweet_dict.keys():
                    continue
                else:
                    if tweets[i].find_elements("xpath",f'.//a[@href="/{username}" and contains(@dir,"ltr")]') != []:
                        repost = "True" 
                    else:
                        repost = "False"
                    try:    
                        interacts = tweets[i].find_elements("xpath",f'.//div[@role="group"]')[0].get_attribute('aria-label')

                        interacts = self.extract_to_dictionary(interacts)
                    except:
                        interacts = {'replies': 0, 'reposts': 0, 'likes': 0, 'views': 0, 'bookmarks': 0}
                    try:
                        langs = tweets[i].find_element("xpath", f'.//div[@lang and @lang!="none"]')
                        try:
                            tweet_content = ' '.join([line.text for line in langs.find_elements("xpath",f".//*")])
                        except:
                            tweet_content = 'Video'
                    except:
                        langs = "NA"
                        tweet_content = 'Video'

                    tweet_dict.update({tweet_time: {'repost': repost,'content': tweet_content, 'language': langs.get_attribute('lang') if langs != "NA" else "NA",
                                                    'interacts': interacts}})
                    count += 1
                    if count == 20:
                        break
            #Scroll down
            self.driver.execute_script(f"window.scrollTo(0,{3000*iter})")
            time.sleep(1)
            iter+= 1
        
        return tweet_dict
    
    def retrieve_basic_user_info(self,username):
        self.driver.get(f'https://twitter.com/{username}')
        time.sleep(2)
        user_info = self.driver.find_elements("xpath",f'//script[@type="application/ld+json"]')
        jsontext = json.loads(user_info[0].get_attribute('innerHTML'))
        try:
            job = self.driver.find_element("xpath", "//span[@data-testid ='UserProfessionalCategory']/*[2]/*").text
        except:
            job = "NA"
            
        verified = self.driver.find_elements("xpath", '//div[@aria-label ="Provides details about verified accounts."]/*/*/*')
        if len(verified) == 0:
            type_account = 'normal'
        elif len(verified) == 1:
            if verified[0].get_attribute('clip-rule') == 'evenodd':
                type_account = 'government'
            else:
                type_account = 'verified'
        else:
            type_account = 'company'
        if len(self.driver.find_elements("xpath",'//div[@aria-label="Provides details about protected accounts."]')) > 0:
            tweets = {}
            protected = 'True' 
        else:
            protected = 'False'
            if len(self.driver.find_elements("xpath",'//div[@data-testid="emptyState"]')) > 0:
                tweets = {}
            else: 
                tweets = self.retrieve_tweets(username)
                

        return_dict = {'type':jsontext['author']['@type'],
                        'name':jsontext['author']['givenName'],
                    'location':jsontext['author']['homeLocation']['name'],
                    'description':jsontext['author']['description'],
                    'date_created': jsontext['dateCreated'],
                    'num_followers': jsontext['author']['interactionStatistic'][0]['userInteractionCount'],
                    'num_following': jsontext['author']['interactionStatistic'][1]['userInteractionCount'],
                    'num_tweets': jsontext['author']['interactionStatistic'][2]['userInteractionCount'],
                    'job': job, 'type_account': type_account, 'protected': protected, 'all_tweets': tweets}
        return return_dict
    
    def load_username(self, keyword):
        try:
            with open(f"{self.save_file}/all_users/{keyword}.pkl", "rb") as f:
                return pickle.load(f)
        except:
            return []
    def load_crawled_username(self, keyword):
        return [x.split(".")[0] for x in os.listdir(f"{self.save_file}/user_info/{keyword}")]
    def load_crawled_groups(self, keyword):
        return [x.split(".")[0].split('-')[1] for x in os.listdir(f"{self.save_file}/groups") if x.split(".")[0].split('-')[0] == keyword]
    
    def write_username_to_file(self, keyword, groups_dict, user_name):

        with open(f"{self.save_file}/all_users/{keyword}.pkl", "wb") as f:
            pickle.dump(user_name, f)

    def write_username_to_kafka(self, keyword, groups_dict, user_name):
        self.producer.send(keyword, pickle.dumps(user_name))

    def write_user_info_to_file(self, keyword, user_info, user_name):
        with open(f"{self.save_file}/user_info/{keyword}/{user_name}.pkl", "wb") as f:
            pickle.dump(user_info, f)
            
    def write_user_info_to_kafka(self, keyword, user_info, user_name):
        self.producer.send(f"{keyword}_{user_name}", pickle.dumps(user_info))
    
    def crawl_all_username(self):
        for hashtag in self.hashtags:
            user_names, groups_dict = self.get_all_users_from_groups(hashtag)


            self.write_username_to_kafka(hashtag, groups_dict, user_names)
            print('Finish crawling hashtag: ', hashtag)
            time.sleep(30*1)
        
    def crawl_all_users(self, hashtag, start, end):
        user_names = self.load_username(hashtag)
        wait_idx = 0
        os.makedirs(f"{self.save_file}/user_info/{hashtag}", exist_ok=True)

        crawled_users = self.load_crawled_username(hashtag)
        if start == None: 
            start = 0
        if end == None:
            end = len(user_names)
        for idx in tqdm(range(start,end)):
            if user_names[idx] in crawled_users:
                print("Already crawled user: ", user_names[idx])
                continue
            #user_info = self.retrieve_basic_user_info(user)
            
            try:
                user_info = self.retrieve_basic_user_info(user_names[idx])
            except:
                print("Error when crawling user: ", user_names[idx])
                continue
            
            self.write_user_info_to_file(hashtag, user_info, user_names[idx])
            self.write_user_info_to_kafka(hashtag, user_info, user_names[idx])
            print('Finish crawling user: ', user_names[idx])
            wait_idx += 1
            if wait_idx % 15 == 0:
                time.sleep(60*3)
        print('Finish crawling users from hashtag: ', hashtag)
                
if __name__ == "__main__":

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument('--tag', type = str, help='Hashtag you want to crawl', default='DeFi')
    parser.add_argument('--kaggle', type = int, help='Crawl mode, 0 is local, 1 is kaggle', default=0)
    parser.add_argument('--start', type = int, help='start index in hashtag list (default 0)', default=None)
    parser.add_argument('--end', type = int, help='end index in hashtag list (default max)', default=None)
    parser.add_argument('--username', type = str, help='Twitter username', default=None)
    parser.add_argument('--password', type = str, help='Twitter password', default=None)

    # Parse the arguments
    args = parser.parse_args()

    producer = KafkaProducer(bootstrap_servers=['34.142.194.212:29092'])
    hashtags = ["btc"]

    crawler = TwitterCrawler(producer, hashtags, kaggle = args.kaggle)
    crawler.log_in(args.username,args.password)
    #crawler.crawl_all_username()
    crawler.crawl_all_users(args.tag,args.start,args.end)
    print('Finish crawling all hashtags')
    crawler.driver.close()
    crawler.driver.quit()
    
    
