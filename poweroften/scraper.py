# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
import re
import numpy as np

root_url = 'http://www.thepowerof10.info'

class PowerOfTen():
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        
    def urlopen(self, url):
        if self.verbose:
            print('Loading', url)
        page = urlopen(url)
        if self.verbose:
            print('Loaded.')
        return page

    def search(self, first_name='', surname='', club=''):
        """
            Search for athletes with the given name and club.
            
            # Parameters
            first_name : string
            surname    : string
            club       : string
            
            # Returns
            search_results : DataFrame, search results indexed by athlete id.
        """
        page = self.urlopen(root_url + '/athletes/athleteslookup.aspx?surname={}&firstname={}&club={}'
                       .format(surname, first_name , club))
        
        soup = BeautifulSoup(page.read(), 'html.parser')
        
        search = soup.find('table', {'id': 'cphBody_dgAthletes'})
        df = pd.read_html(str(search), header=0)[0]
        df = df.drop(['runbritain', 'Profile'], axis=1)
        df.index = [int(re.findall(r'\d+', x.get('href'))[0]) for x in search.find_all('a', {'href': re.compile('^((?!run).)*$')})]
        return df
            
    def get_athlete(self, athlete_id):
        """
            Gets information about an athlete.
            
            # Parameters
            athlete_id : int
            
            # Returns
            athlete_info  : dict, Athlete information
            yearly_info   : DataFrame, Age group and club per year
            seasons_bests : DataFrame, Seasons bests per year, indexed per event
            results       : DataFrame, Historical performances
        """
        page = self.urlopen(root_url + '/athletes/profile.aspx?athleteid={}'.format(athlete_id))
        soup = BeautifulSoup(page.read(), 'html.parser')
        
        athlete_info_soup = soup.find('div', {'id': 'cphBody_pnlAthleteDetails'})
        df = pd.concat(pd.read_html(str(athlete_info_soup))[1:])
        athlete_info = dict(zip([x.strip(':') for x in df[0]], df[1]))
        athlete_info['Club'] = athlete_info['Club'].split('/')
        athlete_info['Name'] = soup.find('h2').text.strip()
        
        seasons_bests_soup = soup.find('div', {'id': 'cphBody_divBestPerformances'})
        seasons_bests = pd.read_html(str(seasons_bests_soup), header=0)[0]
        seasons_bests.Event = seasons_bests.Event.astype(str)
        seasons_bests = seasons_bests[seasons_bests.Event != 'Event'] # Strip refresher rows
        seasons_bests.index = seasons_bests.Event # Set index to Event 
        seasons_bests = seasons_bests.drop(seasons_bests.columns[['Event' in x for x in seasons_bests.columns]], axis=1) # Drop event columns
        seasons_bests = seasons_bests[~seasons_bests.index.duplicated(keep='first')] # Some events are duplicated
        
        results_soup = soup.find('div', {'id': 'cphBody_pnlPerformances'})
        results_soup_table = results_soup.find_all('table')[1]
        results = pd.read_html(str(results_soup_table))[0]
        results.columns = ['Event', 'Perf', 'Notes', 'Wind', 'Chip', 'Pos', 'Race', 
                           'Unknown', 'CatPos', 'Venue', 'Meeting', 'Date'] # Set columns manually
        
        # Get meeting ids
        meeting_ids = []
        for row in results_soup_table.find_all('tr'):
            a = row.find('a')
            if a is None:
                meeting_ids.append(-1)
                continue
            url = a.get('href', '')
            match = re.findall(r'meetingid=\d+', url)
            
            if len(match) == 0:
                meeting_ids.append(-1)
            else:
                meeting_ids.append(int(match[0][10:]))
                
        results['MeetingId'] = meeting_ids
        
        # Columns where date is null contain the age group and club for the year
        yearly_info = results[results.Date.isnull()].Event
        years = [int(x.split()[0]) for x in yearly_info]
        ags = [x.split()[1] for x in yearly_info]
        clubs = [' '.join(x.split()[2:]).split('/') for x in yearly_info]
        yearly_info = dict(zip(years, [{'age_group': a, 'clubs': c} for a,c in zip(ags, clubs)]))
        
        # Strip refresher rows and header rows
        results = results[np.logical_not(np.logical_or(results.Date.isnull(), results.Date == 'Date'))]    
        results = results.reset_index(drop=True)
        
        return athlete_info, yearly_info, seasons_bests, results
        
    def get_rankings(self, event, age_group, sex, year):
        """
        Get rankings
        
        # Parameters
        event     : string
        age_group : string
        sex       : string
        year      : string or int
        
        # Returns
        rankings : DataFrame, rankings indexed by athlete id.
        """
        page = self.urlopen(root_url + '/rankings/rankinglist.aspx?event={}&agegroup={}&sex={}&year={}'.format(event, age_group, sex, year))
        soup = BeautifulSoup(page.read(), 'html.parser')
        
        rankings = soup.find('span', {'id': 'cphBody_lblCachedRankingList'})
        df = pd.read_html(str(rankings))[0] 
        
        # Header row has first column 'Rank'
        header_row = df.index[df[0] == 'Rank'][0]
        df.columns = ['Rank', 'Perf', 'Notes', 'Wind', 'PB', 'IsPB',  'Name', 'AgeGroup',
            'Year', 'Coach',  'Club', 'Venue',  'Date', 'Notify']
        df = df.iloc[header_row+1:]
        
        df = df[~df.Perf.isnull()] # Drop rows without a performance
        df = df[~df.Rank.isnull()] # Drop non-UK table (unranked)
        df = df.drop('Notify', axis=1) # Drop last column
        df.Rank = df.Rank.astype(int) 
    
        # Find athlete_ids
        rows = [x.find('a') for x in rankings.find_all('tr')]
        links = [x.get('href') for x in rows if x is not None]
        athlete_ids = [int(re.findall(r'\d+', x)[0]) for x in links if 'athleteid=' in x]
        athlete_ids = athlete_ids[:len(df)]
        df.index = athlete_ids
        
        return df
    
    
    def get_results(self, meeting_id):
        """
        Get results from a meeting
        
        # Parameters
        meeting_id : string or int
        
        # Returns
        results : dict of DataFrames, results by event.
        """
        page = self.urlopen(root_url + '/results/results.aspx?meetingid={}&top=5000&pagenum=1'.format(meeting_id))
        soup = BeautifulSoup(page.read(), 'html.parser')
        
        # Get the number of pages
        num_pages = 1
        num_pages_soup = soup.find('span', {'id': 'cphBody_lblTopPageLinks'})
        if num_pages_soup is not None:
            links = num_pages_soup.find_all('a')
            if len(links) > 0:
                num_pages = max([int(a.text) for a in links])
        
        results = {}
        for i in range(1, num_pages+1):
            # Load the next page if appropriate.
            if i > 1:
                page = self.urlopen(root_url + '/results/results.aspx?meetingid={}&top=5000&pagenum={}'.format(meeting_id, i))
                soup = BeautifulSoup(page.read(), 'html.parser')
                
            results_soup = soup.find('table', {'id': 'cphBody_dgP'})
            df = pd.read_html(str(results_soup), header=None)[0]
            
            # Attach athlete ids
            athlete_ids = []
            for row in results_soup.find_all('tr'):
                a = row.find('a')
                if a is None:
                    athlete_ids.append(-1)
                    continue
                url = a.get('href', '')
                match = re.findall(r'athleteid=\d+', url)
                
                if len(match) == 0:
                    athlete_ids.append(-1)
                else:
                    athlete_ids.append(int(match[0][10:]))
            df['AthleteId'] = athlete_ids
            
            # Drop rows which are blank (excl. athlete_id)
            df = df[~((~df.isnull()).sum(axis=1) == 1)]
            
            # Those with rows with only one entry (excl. athlete_id) are the 
            # header rows containing the age group and distance.
            ix = np.where((~df.isnull()).sum(axis=1) == 2)[0]
            ix = np.append(ix, len(df))
            
            
            # Split based on header rows
            dfs = [df[ix[j]:ix[j+1]] for j in range(len(ix)-1)]
            
            for df in dfs:
                race = df.iloc[0,0]
                df.columns = list(df.iloc[1, :-1]) + ['AthleteId'] # Often a variable number of columns so don't set manually
                df = df.iloc[2:]
                
                if race in results:
                    results[race] = pd.concat((results[race], df))
                else:
                    results[race] = df
                
            for name, df in results.items():
                results[name] = df.reset_index(drop=True)
                
        return results
    

