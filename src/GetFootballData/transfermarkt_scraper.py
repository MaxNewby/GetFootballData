import pandas as pd
import numpy as np
import requests
import time
import random
from tqdm import tqdm
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from GetFootballData.scraper_utilities.league_to_tm_map import league_to_tm_dict

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

root_site = 'www.transfermarkt.com'

class TransfermarktScraper:

    def __init__(self):

        self._session = None

        self.universal_sleep_value = 0.1

    def warm_up(self):
        """Request fotmob page to familiarise session with fotmob."""
        try:
            self.session.get(f"https://{root_site}/", timeout=5)
            time.sleep(random.uniform(1.5, 3.0))
        except Exception as e:
            print(f"Warm-up handshake warning: {e}")

    @property
    def session(self):
        if self._session is None:

            self._session = cffi_requests.Session(impersonate='chrome124')

            self._session.headers.update({"accept": "application/json", "referer": f"https://{root_site}/"})

            self.warm_up()

        return self._session

    def close_session(self):
        """Closes the cffi session when you don't need to use the object anymore."""
        if self._session is not None:
            self._session.close()
            self._session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()

    def __get_player_id_df(self, year: int, league: str) -> pd.DataFrame:

        '''
        This method scrapes the transfermarkt ids, nationality and club for every player in the given league

        :param year: starting year of the league (ex. 2025)
        :param league: league name according to the package's naming conventions (ex. 'ENG-Premier League', 'FRA-Ligue 1')
        :return: a dataframe containing: player_name, player_id, club_name, nation. If data can't be found, an empty dataframe is returned.
        '''

        league_dict = league_to_tm_dict[league]
        league_name = league_dict[0]
        league_code = league_dict[1]

        url = f'https://{root_site}/{league_name}/tabelle/wettbewerb/{league_code}/saison_id/{str(year)}'

        r = self.session.get(url, timeout=5)
        time.sleep(self.universal_sleep_value)

        if not r:
            return pd.DataFrame()

        soup = BeautifulSoup(r.text, "html.parser")

        club_acronym_list = []

        table = soup.find('table', {'class': 'items'})

        for row in table.find_all('tr'):
            link = row.find('a', href=True)
            if not link:
                continue
            href = link['href']
            club_acronym = href.split('/')[1]
            club_id = href.split('/')[4]
            club_name = link['title']
            club_acronym_list.append([club_acronym, club_id, club_name])

        name_id_list = []

        progressbar = tqdm(club_acronym_list, desc='Teams read', unit=' teams')
        for club_acronym in progressbar:

            club_name = club_acronym[2]
            squad_url = f'https://{root_site}/{club_acronym[0]}/kader/verein/{club_acronym[1]}/saison_id/{year}'
            r = self.session.get(squad_url, timeout=5)
            time.sleep(self.universal_sleep_value)

            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find('table', {'class': 'items'})

            for row in table.find_all('table', {'class': 'inline-table'}):
                link_area = row.find('td', {'class': 'hauptlink'})
                if not link_area:
                    continue
                link = link_area.find('a', href=True)
                href = link['href']
                player_id = href.split('/')[4]
                player_name = link_area.get_text(strip=True)

                parent_row = row.find_parent('tr')

                nation = None
                for area in parent_row.find_all('td', {'class': 'zentriert'}):
                    nation_image = area.find('img', class_='flaggenrahmen')
                    if not nation_image:
                        continue
                    nation = nation_image['title']

                name_id_list.append((player_name, player_id, club_name, nation))

        name_id_df = pd.DataFrame(name_id_list, columns=['player_name', 'player_id', 'club_name', 'nation']).set_index('player_name')

        return name_id_df



    def get_player_overview_df(self, year: int, league: str) -> pd.DataFrame:

        dataframe = self.__get_player_id_df(year, league)

        base_players_url = f'https://tmapi.transfermarkt.technology/players?'

        team_list = dataframe['club_name'].unique().tolist()

        final_player_dataframe = pd.DataFrame()

        player_progress_bar = tqdm(team_list, desc="Squads overviews read", unit="squads")
        for team in player_progress_bar:

            team_player_ids = dataframe[dataframe['club_name'] == team]['player_id'].tolist()

            team_players_url = base_players_url

            for player_id in team_player_ids:

                team_players_url = team_players_url + f'ids[]={player_id}&'

            team_players_url = team_players_url[:-1]

            if team_players_url == base_players_url:
                raise Exception(f'No team player ids found for {team}')

            r = self.session.get(team_players_url, timeout=5)
            time.sleep(self.universal_sleep_value)

            player_data = r.json()['data']

            team_data_list = []

            for player in player_data:

                club_assignment_list = [{}, {}]
                for index, club_dict in enumerate(player['clubAssignments'][:2]): # Only go through first two assignments
                    club_assignment_list[index] = club_dict

                data_dict = {
                    'player_name': player['name'],
                    'player_id': player['id'],
                    'age': player['lifeDates'].get('age', None),
                    'date_of_birth': player['lifeDates'].get('dateOfBirth', None),
                    'birth_place': player['birthPlaceDetails'].get('placeOfBirth', None),
                    'position': player['attributes'].get('position', {}).get('name', None),
                    'team': team,
                    'general_position': player['attributes'].get('position', {}).get('category', None),
                    'preferred_foot': player['attributes'].get('preferredFoot', {}).get('name', None),
                    'height': player['attributes'].get('height', None),
                    'contractEnd':player['attributes'].get('contractUntil', None),
                    'sponsor': player['attributes'].get('outfitter', {}).get('name', None),
                    'agent': player['attributes'].get('consultantAgency', {}).get('name', None),
                    'market_value': player.get('marketValueDetails', {}).get('current', {}).get('value', None),
                    'previous_market_value': player.get('marketValueDetails', {}).get('previous', {}).get('value', None),
                    'highest_market_value': player.get('marketValueDetails', {}).get('highest', {}).get('value', None),
                    'shirt_number': club_assignment_list[0].get('shirtNumber', None),
                    'debut': club_assignment_list[0].get('debut', None),
                    'is_captain': club_assignment_list[0].get('isCaptain', None),
                    'nt_shirt_number': club_assignment_list[1].get('shirtNumber', None),
                    'nt_debut': club_assignment_list[1].get('debut', None),
                    'is_nt_captain': club_assignment_list[1].get('isCaptain', None),
                }

                team_data_list.append(data_dict)

            team_stats_df = pd.DataFrame(team_data_list)
            final_player_dataframe = pd.concat([final_player_dataframe, team_stats_df])

        final_player_dataframe.set_index('player_id', inplace=True)

        #Set Nationality
        final_player_dataframe = final_player_dataframe.merge(dataframe.reset_index()[['player_id', 'nation']], on='player_id', how='left')

        return final_player_dataframe


    def get_player_transfer_history(self, player_id: str) -> pd.DataFrame:

        '''
        :param player_id: transfermarkt's player id (as seen in the url of a player's profile)
        :return: A pandas dataframe containing a row for every recorded transfer a given player has had according to transfermarkt. If there is no history, an empty dataframe is returned. Rows include;


        Columns:
        - source_name: source club
        - destination_name: destination club
        - source_club_id: source club transfermarkt id
        - destination_club_id: destination club transfermarkt id
        - source_competition: league code of source team
        - destination_competition: league code of destination team
        - contract_start_date: start of contract date
        - contract_end_date: end of contract date
        - season: year of the beginning of the season
        - market_value_at_time: market value at the time of the transfer
        - age: age of the player at the time of the transfer
        - fee: fee of the transfer in euros (€)
        - transfer_type: description of the nature of the transfer ex. loan. Column will not contain data if it is a normal transfer.
        - fee_description: Extra description of the nature of the attached fee, ex. loan fee. Column will not contain data if it is a normal transfer.
        '''

        url = f"https://tmapi.transfermarkt.technology/transfer/history/player/{player_id}"

        r = self.session.get(url, timeout=5) #Fetch transfer history page via URL
        time.sleep(self.universal_sleep_value)

        print(player_id)

        try:
            transfer_history = r.json()["data"]['history']['terminated']
        except:
            return pd.DataFrame()



        club_id_set = set()

        source_data = transfer_history[0]["transferSource"]
        club_id_set.add(source_data["clubId"])

        for row in transfer_history:
            source_data = row["transferSource"]
            destination_data = row["transferDestination"]
            club_id_set.add(source_data["clubId"])
            club_id_set.add(destination_data["clubId"])

        club_url = f'https://tmapi.transfermarkt.technology/clubs?'
        for club_id in club_id_set:
            club_url = club_url + f'ids[]={club_id}&'
        club_url = club_url[:-1]


        for i in range(1,5):
            try:
                club_r = self.session.get(club_url, timeout=5)  # Fetch club name data from transfermarkt api
                time.sleep(self.universal_sleep_value)
                club_data = club_r.json()["data"]
                break
            except requests.exceptions.RequestException as e:
                print(e)
                if i == 5:
                    print(f'Could not access transfermarkt club data from api.')
                    exit()
                print(f'Request failed, retrying {i+1}/5 after 10 seconds')
                time.sleep(10)



        id_to_club_dict = {}
        for row in club_data:
            id_to_club_dict.update({row['id']:row['name']})

        transfer_history_list = []

        for row in transfer_history:
            source_data = row["transferSource"]
            destination_data = row["transferDestination"]
            details_data = row["details"]
            transfer_type_data = row['typeDetails']
            entry = {'player_id': player_id,
                     'source_name': id_to_club_dict[source_data['clubId']],
                     'destination_name': id_to_club_dict[destination_data['clubId']],
                     'source_club_id': source_data['clubId'],
                     'destination_club_id': destination_data['clubId'],
                     'source_competition': source_data['competitionId'],
                     'destination_competition': destination_data['competitionId'],
                     'contract_start_date': details_data["date"],
                     'contract_end_date': details_data["contractUntilDate"],
                     'season': details_data.get("season").get('id'),
                     'market_value_at_time': details_data.get('marketValue', {}).get('value', np.nan),
                     'age': details_data["age"],
                     'fee': details_data.get('fee', {}).get('value', np.nan),
                     'transfer_type': transfer_type_data.get('name', np.nan),
                     'fee_description': transfer_type_data.get('feeDescription', np.nan),
                     }

            transfer_history_list.append(entry)

        transfer_history_df = pd.DataFrame(transfer_history_list).set_index('player_id')

        return transfer_history_df