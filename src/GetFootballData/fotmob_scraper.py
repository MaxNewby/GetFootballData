import pandas as pd
import numpy as np
import time
import random
from curl_cffi import requests as cffi_requests
from scraper_utilities.league_to_fotmob_map import league_to_fotmob_dict
from scraper_utilities.year_maps import year_to_fotmob_season

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

root_site = 'www.fotmob.com'

class FotmobScraper:

    def __init__(self):

        self.session = cffi_requests.Session(impersonate='chrome124')

        self.session.headers.update({"accept": "application/json", "referer": f"https://{root_site}/"})

        self.warm_up()

    def warm_up(self):
        """Request fotmob page to familiarise session with fotmob."""
        try:
            self.session.get(f"https://{root_site}/", timeout=5)
            time.sleep(random.uniform(1.5, 3.0))
        except Exception as e:
            print(f"Warm-up handshake warning: {e}")

    def __get_team_id_dict(self, year=int, league_name=str):

        '''
        :param year: the year that the season begun
        :param league_name: The name of the league in the standardised format of the package
        :return: A dictionary containing {'id': 'team_name', ...} pairs for the given league in the given season starting year
        '''

        league_country_to_find = league_to_fotmob_dict[league_name]

        url = f'https://{root_site}/api/data/allLeagues?locale=en&country=GBR'
        print(url)

        r = self.session.get(url)
        league_list_data = r.json()['countries']

        league_page_url = ''
        league_id = ''

        for country in league_list_data:
            if country['name'] == league_country_to_find[1]:
                league_list = country['leagues']
                for league in league_list:
                    if league['name'] == league_country_to_find[0]:
                        league_page_url = f'https://{root_site}/api/data/leagues?id={league["id"]}&ccode3=GBR&season={year}%2F{int(year)+1}'
                        league_id = league['id']
                        break

        if len(league_page_url) == 0:
            raise Exception('No leagues found')
        if league_id == '':
            raise Exception('No league_id found')

        r = self.session.get(league_page_url)
        league_data = r.json()

        #Get tournament id for given year
        tournament_id_list = league_data.get('stats').get('seasonStatLinks')
        tournament_id = ''
        for season in tournament_id_list:
            if season.get('Name') == year_to_fotmob_season[year]:
                tournament_id = season.get('TournamentId')
        if tournament_id == '':
            raise Exception('No tournament ID found for that year')


        #Get dictionary of {id, team_name}
        team_dict = {}

        team_list = league_data['table'][0]['data']['table']['all']
        no_of_teams = len(team_list)
        for index, team in enumerate(team_list):
            team_dict.update({team['id']: {
                'name': team['name'],
                'deduction': team['deduction'],
                'ongoing': team['ongoing'],
                'played': team['played'],
                'wins': team['wins'],
                'draws': team['draws'],
                'losses': team['losses'],
                'scored-conceded': team['scoresStr'],
                'goal_dif': team['goalConDiff'],
                'points': team['pts'],
            }})
            print(f'{index + 1}/{no_of_teams} teams read')
        print('all teams read successfully')

        return team_dict, league_id, tournament_id



    def __get_player_id_dict(self, year, league_name):

        '''
        :param year: the year that the season begun
        :param league_name: The name of the league in the standardised format of the package
        :return: A dictionary containing {'id': ('player_name', 'player_mins'), ...} pairs for the given league in the given year
        '''

        team_dict, league_id, tournament_id = self.__get_team_id_dict(year, league_name)

        player_dict = {}

        for team_id, team_name in team_dict.items():

            team_url = f'https://{root_site}/api/data/leagueseasondeepstats?lng=en-GB&id={league_id}&season={tournament_id}&type=players&stat=mins_played&teamId={team_id}'
            r = self.session.get(team_url)
            minutes_played_data = r.json()

            played_players = minutes_played_data['statsData']

            for player in played_players:
                player_dict.update({player['id']: (player['name'], player['statValue']['value'])})

        return player_dict



    def get_player_data_df(self, year, league_name) -> pd.DataFrame:

        '''
        This method scrapes the fotmob player data, for every player in the given league

        :param year: starting year of the league (ex. 2025)
        :param league_name: league name in the package's standardised format: (ex. 'ENG-Premier League')
        :return: a pd.Dataframe instance containing the player data.
        '''

        league_country_to_find = league_to_fotmob_dict[league_name]
        year_to_find = year_to_fotmob_season[year]


        player_dict = self.__get_player_id_dict(year, league_name)

        # All player rows will be added to this list before being assembled into a dataframe
        player_data_list = []

        for player_id, player_name_mins_array in player_dict.items():

            player_name = player_name_mins_array[0]
            player_mins_played = player_name_mins_array[1]

            player_url = f'https://www.fotmob.com/api/data/playerData?id={player_id}'
            r = self.session.get(player_url)
            player_data = r.json()
            stat_seasons = player_data.get('statSeasons')
            if stat_seasons is None:
                continue

            entry_id = '' #Find the entryId to put in the URL to get data for the correct league
            for season in stat_seasons:
                leagues = season['tournaments']
                for league in leagues:
                    if league['name'] == league_country_to_find[0] and season['seasonName'] == year_to_find:
                        entry_id = league['entryId']
                        break

            if entry_id == '':
                continue

            player_stats_url = f'https://www.fotmob.com/api/data/playerStats?playerId={player_id}&seasonId={entry_id}&isFirstSeason=false'
            r = self.session.get(player_stats_url)
            player_stats_data = r.json()

            print(player_name)
            print(player_id)
            print(player_stats_data.keys())
            print(player_stats_url)
            print(' ')



            player_data_dicts = player_stats_data.get('statsSection', {}).get('items', {})
            player_data_metadata_dict = player_stats_data.get('topStatCard', {}).get('items', {})
            combined_stat_dict = {}


            for stat_dict in player_data_metadata_dict:
                combined_stat_dict.update({stat_dict['title']: stat_dict['statValue']})

            for player_stat_category_dict in player_data_dicts:
                player_stat_dict = player_stat_category_dict['items']
                for stat_dict in player_stat_dict:
                    combined_stat_dict.update({stat_dict['title']: stat_dict['statValue']})


            player_info_list = player_data.get('playerInformation', [])
            player_info_dict = {}
            for info in player_info_list:
                title = info.get('title')
                if title:
                    player_info_dict[title] = info.get('value', {})

            #Get correct club
            club_name = ''
            for season in player_data.get('careerHistory', {}).get('careerItems', {}).get('senior', {}).get('seasonEntries', []):
                if season.get('seasonName', '') == year_to_fotmob_season[year] and season.get('tournamentStats', [{}])[0].get('leagueName') == league_country_to_find[0]:
                    club_name = season.get('team', '')
                    break

            #Get main position
            main_position = ''
            for position in player_data.get('positionDescription', {}).get('positions', []):
                if position.get('isMainPosition', False):
                    main_position = position.get('strPosShort', {}).get('label', '')
                    break
            if main_position == '':
                main_position = player_data.get('positionDescription', {}).get('positions', [{}])[0].get('strPosShort', {}).get('label', None)


            #Ensure primaryTeam exists
            if player_data['primaryTeam'] is None:
                player_data['primaryTeam'] = {}



            player_data_dict = {
                #Metadata
                'id': player_data.get('id', None),
                'name': player_data.get('name', None),
                'club': club_name,
                'isCaptain': player_data.get('isCaptain', None),
                'teamColour': player_data.get('primaryTeam', {}).get('teamColors', {}).get('color', None),
                'position': main_position,
                'height': player_info_dict.get('Height', {}).get('numberValue', None),
                'shirtNumber': player_info_dict.get('Shirt', {}).get('numberValue', None),
                'Age': player_info_dict.get('Age', {}).get('numberValue', None),
                'preferredFoot': player_info_dict.get('Preferred foot', {}).get('key', None),
                'nation': player_info_dict.get('Country', {}).get('fallback', None),
                'marketValue': player_info_dict.get('Market value', {}).get('numberValue', None),
                'contractEnd': player_info_dict.get('Contract end', {}).get('dateValue', None),
                'league': league_to_fotmob_dict[league_name][0],
                'minutesPlayed': player_mins_played,
                'appearances': combined_stat_dict.get('Matches', None),
                'started': combined_stat_dict.get('Started', None),
                #Goalkeeping
                'saves': combined_stat_dict.get('Saves', None),
                'savePercentage': combined_stat_dict.get('Save percentage', None),
                'goalsConceded': combined_stat_dict.get('Goals conceded', None),
                'goalsPrevented': combined_stat_dict.get('Goals prevented', None),
                'penaltySaves': combined_stat_dict.get('Penalty saves', None),
                'penaltySavePercentage': combined_stat_dict.get('Penalty save %', None),
                'errorLedToGoal': combined_stat_dict.get('Error led to goal', None),
                'actedAsSweeper': combined_stat_dict.get('Acted as sweeper', None),
                'highClaims': combined_stat_dict.get('High claims', None),
                'goals': combined_stat_dict.get('Goals', None),
                'expectedGoals': combined_stat_dict.get('xG', None),
                'expectedGoalsOnTarget': combined_stat_dict.get('xGOT', None),
                'nonPenaltyxG': combined_stat_dict.get('xG excl. penalty', None),
                'shots': combined_stat_dict.get('Shots', None),
                'shotsOnTarget': combined_stat_dict.get('Shots on target', None),
                'shotsHeaded': combined_stat_dict.get('Headed shots', None),
                #Passing
                'assists': combined_stat_dict.get('Assists', None),
                'xA': combined_stat_dict.get('xA', None),
                'accuratePasses': combined_stat_dict.get('Accurate passes', None),
                'passAccuracy': combined_stat_dict.get('Pass accuracy', None),
                'accurateLongBalls': combined_stat_dict.get('Accurate long balls', None),
                'accurateLongBallsPercentage': combined_stat_dict.get('Long ball accuracy', None),
                'lineBreakingPasses': combined_stat_dict.get('Line-breaking passes', None),
                'chancesCreated': combined_stat_dict.get('Chances created', None),
                'bigChancesCreated': combined_stat_dict.get('Big chances created', None),
                'successfulCrosses': combined_stat_dict.get('Successful crosses', None),
                'crossAccuracy': combined_stat_dict.get('Cross accuracy', None),
                #Possession
                'dribbles': combined_stat_dict.get('Dribbles', None),
                'dribblesSuccessRate': combined_stat_dict.get('Dribbles success rate', None),
                'duelsWon': combined_stat_dict.get('Duels won', None),
                'duelsWonPercentage': combined_stat_dict.get('Duels won %', None),
                'aerialsWon': combined_stat_dict.get('Aerials won', None),
                'aerialsWonPercentage': combined_stat_dict.get('Aerials won %', None),
                'touches': combined_stat_dict.get('Touches', None),
                'touchesInOppositionBox': combined_stat_dict.get('Touches in opposition box', None),
                'dispossessed': combined_stat_dict.get('Dispossessed', None),
                'foulsWon': combined_stat_dict.get('Fouls won', None),
                #Defensive
                'defensiveActions': combined_stat_dict.get('Defensive actions', None),
                'tackles': combined_stat_dict.get('Tackles', None),
                'interceptions': combined_stat_dict.get('Interceptions', None),
                'blockedScoringAttempts': combined_stat_dict.get('Blocked scoring attempt', None),
                'foulsCommitted': combined_stat_dict.get('Fouls committed', None),
                'penaltiesConceded': combined_stat_dict.get('Penalties conceded', None),
                'recoveries': combined_stat_dict.get('Recoveries', None),
                'dribbledPast': combined_stat_dict.get('Dribbled past', None),
                'clearances': combined_stat_dict.get('Clearances', None),
                'cleanSheets': combined_stat_dict.get('Clean sheets', None),
                'goalsConcededWhileOnPitch': combined_stat_dict.get('Goals conceded while on pitch', None),
                'xGAgainstWhileOnPitch': combined_stat_dict.get('xG against while on pitch', None),
                #Physical
                'topSpeed': combined_stat_dict.get('Top Speed', None),
                'totalDistanceCovered': combined_stat_dict.get('Total Distance Covered', None),
                'distanceRun': combined_stat_dict.get('Running', None),
                'distanceSprinted': combined_stat_dict.get('Sprinting', None),
                'totalSprints': combined_stat_dict.get('Number of Sprints', None),
                #Misc
                'yellowCards': combined_stat_dict.get('Yellow cards', None),
                'redCards': combined_stat_dict.get('Red cards', None),
            }

            player_data_list.append(player_data_dict)

            #time.sleep(0.5)

        player_data_dataframe = pd.DataFrame(data=player_data_list)

        return player_data_dataframe