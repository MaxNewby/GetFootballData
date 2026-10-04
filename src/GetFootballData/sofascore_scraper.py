import time
import pandas as pd
import numpy as np
import random
import json
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from scraper_utilities.league_to_sofascore_map import league_to_sofascore_dict
from scraper_utilities.year_maps import year_to_sofascore_season

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

root_site = 'www.sofascore.com'

class SofascoreScraper:

    def __init__(self):
        self.session = cffi_requests.Session()

        self.session.headers.update({
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://sofascore.com",
            "Referer": "https://sofascore.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        })

        self.warm_up()

        self.stat_name_dict = {
            "Accurate crosses": "accurateCrosses",
            "Accurate crosses %": "accurateCrossesPercentage",
            "Accurate final third passes": "accurateFinalThirdPasses",
            "Long balls (accurate)": "accurateLongBalls",
            "Accurate long balls %": "accurateLongBallsPercentage",
            "Passes in opposition half (acc.)": "accurateOppositionHalfPasses",
            "Passes in own half (acc.)": "accurateOwnHalfPasses",
            "Accurate passes": "accuratePasses",
            "Accurate passes %": "accuratePassesPercentage",
            "Aerial duels won": "aerialDuelsWon",
            "Aerial duels won %": "aerialDuelsWonPercentage",
            "Appearances": "appearances",
            "Assists": "assists",
            "Big chances created": "bigChancesCreated",
            "Big chances missed": "bigChancesMissed",
            "Blocked shots": "blockedShots",
            "Clean sheets": "cleanSheet",
            "Clearances": "clearances",
            "Crosses not claimed": "crossesNotClaimed",
            "Dispossessed": "dispossessed",
            "Dribbled past": "dribbledPast",
            "Errors leading to goal": "errorLeadToGoal",
            "Errors leading to shot": "errorLeadToShot",
            "Expected goals (xG)": "expectedGoals",
            "Fouls": "fouls",
            "Free kick goals": "freeKickGoal",
            "Goal conversion %": "goalConversionPercentage",
            "Goals": "goals",
            "Goals conceded inside the box": "goalsConcededInsideTheBox",
            "Goals conceded outside the box": "goalsConcededOutsideTheBox",
            "Goals from inside the box": "goalsFromInsideTheBox",
            "Goals from outside the box": "goalsFromOutsideTheBox",
            "Ground duels (won)": "groundDuelsWon",
            "Ground duels won %": "groundDuelsWonPercentage",
            "Headed goals": "headedGoals",
            "High claims": "highClaims",
            "Hit woodwork": "hitWoodwork",
            "Inaccurate passes": "inaccuratePasses",
            "Interceptions": "interceptions",
            "Key passes": "keyPasses",
            "Left-footed goals": "leftFootGoals",
            "Started": "matchesStarted",
            "Minutes played": "minutesPlayed",
            "Offsides": "offsides",
            "Own goals": "ownGoals",
            "Passes to assist": "passToAssist",
            "Penalties taken": "penaltiesTaken",
            "Penalties committed": "penaltyConceded",
            "Penalty conversion": "penaltyConversion",
            "Penalties faced (saved)": "penaltyFaced",
            "Penalty goals": "penaltyGoals",
            "Penalties saved": "penaltySave",
            "Penalties won": "penaltyWon",
            "Possession lost": "possessionLost",
            "Punches": "punches",
            "Sofascore Rating": "rating",
            "Red cards": "redCards",
            "Right-footed goals": "rightFootGoals",
            "Runs out": "runsOut",
            "Saves from inside box": "savedShotsFromInsideTheBox",
            "Saved shots from outside the box": "savedShotsFromOutsideTheBox",
            "Total saves": "saves",
            "Set piece conversion %": "setPieceConversion",
            "Shots from set piece": "shotFromSetPiece",
            "Shots off target": "shotsOffTarget",
            "Shots on target": "shotsOnTarget",
            "Succ. dribbles": "successfulDribbles",
            "Successful dribbles %": "successfulDribblesPercentage",
            "Successful runs out": "successfulRunsOut",
            "Tackles": "tackles",
            "Total duels won": "totalDuelsWon",
            "Total duels won %": "totalDuelsWonPercentage",
            "Total passes": "totalPasses",
            "Total shots": "totalShots",
            "Was fouled": "wasFouled",
            "Yellow cards": "yellowCards",
            'Accurate chip passes': 'accurateChippedPasses',
            'Aerial duels lost': 'aerialLost',
            'Penalty misses': 'attemptPenaltyMiss',
            'Penalty post hits': 'attemptPenaltyPost',
            'Penalties on target': 'attemptPenaltyTarget',
            'Balls recovered': 'ballRecovery',
            'Matches rated': 'countRating',
            'Red': 'directRedCards',
            'Duels lost': 'duelLost',
            'Expected assists (xA)': 'expectedAssists',
            'Goal kicks': 'goalKicks',
            'Goal involvements': 'goalsAssistsSum',
            'Goals conceded': 'goalsConceded',
            'Goals prevented': 'goalsPrevented',
            'Outfield blocks': 'outfielderBlocks',
            'Possession won (final third)': 'possessionWonAttThird',
            'Saves caught': 'savesCaught',
            'Saves parried': 'savesParried',
            'Scoring frequency': 'scoringFrequency',
            'Shots from inside the box': 'shotsFromInsideTheBox',
            'Shots from outside the box': 'shotsFromOutsideTheBox',
            'Tackles won': 'tacklesWon',
            'Tackles won percentage': 'tacklesWonPercentage',
            'Top speed': 'topSpeed',
            'Total attempted assists': 'totalAttemptAssist',
            'Total chipped passes': 'totalChippedPasses',
            'Total contest': 'totalContest',
            'Total cross': 'totalCross',
            'Total long balls': 'totalLongBalls',
            'Total opposition half passes': 'totalOppositionHalfPasses',
            'Total own half passes': 'totalOwnHalfPasses',
            'Total rating': 'totalRating',
            'TOTW Appearances': 'totwAppearances',
            'Touches': 'touches'
            }

        self.concatenated_stat_names = "%2C".join(self.stat_name_dict.values())

    def warm_up(self):
        """Request sofascore page to familiarise session with sofascore."""
        try:
            self.session.get("https://sofascore.com/", timeout=5)
            time.sleep(random.uniform(1.5, 3.0))
        except Exception as e:
            print(f"Warm-up handshake warning: {e}")


    def __get_team_id_dict(self, year: int, league_name: str):

        '''
        :param year: Takes the starting year of the given season.
        :param league_name: Takes the name of the given league in the given format.
        :return *team_id_dict: a dict containing {player_id: player_name, ...} combinations that sofascore uses.
                 *league_id: The league id of the given league.
                 *season_id: The season id of the given season in that league. Used to find the specific season in the given league.
        '''

        league_info_list = league_to_sofascore_dict[league_name]
        country = league_info_list[0]
        league = league_info_list[1]
        league_id = league_info_list[2]

        url = f'https://{root_site}/football/tournament/{country}/{league}/{league_id}?page=1'


        r = self.session.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        next_data = soup.find("script", id="__NEXT_DATA__")
        data = json.loads(next_data.string)
        seasons = data["props"]["pageProps"]['seasons']

        season_id = ''
        for season in seasons:
            if season['year'] == year_to_sofascore_season[year]:
                season_id = season['id']

        if season_id == '':
            raise Exception('No season ID found for given year')

        url = f'https://{root_site}/api/v1/unique-tournament/{league_id}/season/{season_id}/statistics/info'

        r = self.session.get(url, timeout=5)

        team_id_dict = {}

        team_data = r.json()
        team_data = team_data['teams']

        for team in team_data:
            team_id_dict.update({team['id']: team['name']})

        return team_id_dict, league_id, season_id



    def get_player_id_dicts(self, year: int, league_name: str) -> dict[int, dict[str, str | dict[int, str]]]:

        '''
        :param year: Takes the starting year of the given season.
        :param league_name: Takes the name of the given league in the given format.
        :return: a dictionary of team names mapping to dictionaries containing player ids and names in the format {team_id: {name: team_name, player_dict: {player_id: player_name, ...}}, ...}.
        '''

        team_id_dict, league_id, season_id = self.__get_team_id_dict(year=year, league_name=league_name)

        player_id_dicts = {}

        for team_id, team_name in team_id_dict.items():

            player_stats_url = f'https://{root_site}/api/v1/team/{team_id}/unique-tournament/{league_id}/season/{season_id}/top-players/overall'

            r = self.session.get(player_stats_url, timeout=5)

            data = r.json()
            data = data['topPlayers']['rating']

            team_player_dict = {}

            for player_dict in data:
                player_name = player_dict['player']['name']
                player_id = player_dict['player']['id']

                team_player_dict.update({player_id: player_name})
                player_id_dicts[team_id] = {'team_name': team_name, 'player_id_dict': team_player_dict}

        return player_id_dicts


    def get_player_metadata_df(self, year: int, league_name: str) -> pd.DataFrame:

        '''
        :param year: starting year of the given season.
        :param league_name: name of the league according to the given format.
        :return: a pd.DataFrame containing general data about each player in a given league (height, preferred foot, etc.).
        '''

        player_id_dicts = self.get_player_id_dicts(year=year, league_name=league_name)

        player_data_list = []

        for team_id, player_dict in player_id_dicts.items():

            team_name = player_dict['team_name']
            player_id_dict = player_dict['player_id_dict']

            for player_id, player_name in player_id_dict.items():

                player_metadata_url = f'https://{root_site}/api/v1/player/{player_id}'

                r = self.session.get(player_metadata_url, timeout=5)
                metadata = r.json()

                player = metadata.get('player', {})
                country = player.get('country', {})

                player_info = {
                    'player_name': player.get('name', None),
                    'sofascore_id': player.get('id', None),
                    'dateOfBirth': player.get('dateOfBirth', None),
                    'country_name': country.get('name', None),
                    'league': league_name,
                    'team_name': team_name,
                    'team_id': team_id,
                    'shirtNumber': player.get('jerseyNumber', None),
                    'height': player.get('height', None),
                    'weight': player.get('weight', None),
                    'general_position': player.get('position', None),
                    'position': player.get('positionsDetailed', [None])[0],
                    'preferredFoot': player.get('preferredFoot', None),
                    'marketValue': player.get('proposedMarketValue', None)
                }

                player_data_list.append(player_info)

        player_metadata_df = pd.DataFrame(player_data_list)

        return player_metadata_df


    def get_player_stat_df(self, year: int, league_name: str, stat_type='total', specific_stats=None, position_list=None, nationality_code_list=None, team_id_list=None, min_appearances=None, age=None, age_bound='EQ', home_or_away_only=None, preferred_foot=None) -> pd.DataFrame:

        '''
        :param year: starting year of the league in the given format
        :param league_name: name of the league in the wanted format
        :param stat_type: 'total', 'per90', 'perGame'
        :param specific_stats: accepts a list of specific stats to return. Stats can be listed as seen on sofascore, in a league->stats->detailed tab
        :param position_list: accepts a list of positions to return. options ['G', 'D', 'M', 'F']
        :param nationality_code_list: accepts a list of nationality codes to return.
        :param team_id_list: enter a list of sofascore's team IDs to return data only from those teams.
        :param min_appearances: min appearances of a player in the given league/year
        :param age: age of the player in the given league/year
        :param age_bound: options: 'LT', 'EQ', 'GT'
        :param home_or_away_only: 'home', 'away'
        :param preferred_foot: 'left', 'right'. Returns only players with the given preferred foot.
        :return: a dataframe containing all records of stat data for players in a given season and league
        '''

        try:
            league_data = league_to_sofascore_dict[league_name]
        except:
            print(f'league {league_name} not found in sofascore dict.')
            league_data = None

        if league_data is None:
            return pd.DataFrame()

        league_id = league_data[2]

        player_data_list = []

        #f'https://www.sofascore.com/api/v1/unique-tournament/17/season/96668/statistics?limit=20&order=-rating&accumulation=per90&group=summary&minApps=yes'
        #f'https://www.sofascore.com/api/v1/unique-tournament/17/season/96668/statistics?limit=20&order=-rating&accumulation=per90&fields=goals%2CsuccessfulDribbles%2Ctackles%2Cassists%2CaccuratePassesPercentage%2Crating&filters=position.in.G~D~M~F'
        #f'https://www.sofascore.com/api/v1/unique-tournament/17/season/96668/statistics?limit=20&order=-rating&accumulation=per90&fields=goals%2CsuccessfulDribbles%2Ctackles%2Cassists%2CaccuratePassesPercentage%2Crating&filters=type.EQ.home%2Cappearances.GT.5%2Cage.GT.10%2Cposition.in.G~D~F~M%2CpreferredFoot.EQ.Right%2Cteam.in.35~42~40~33%2Cnationality.in.EN~AR~BR~DE~FR~US~UY~SX~PT~IT'

        #Get season_id

        season_url = f'https://www.sofascore.com/api/v1/unique-tournament/{league_id}/seasons'

        r = self.session.get(season_url, timeout=5)

        season_data = r.json()

        season_id = ''

        # need to get in format '26\/27'
        shortened_year = str(year)[-2:]
        season_in_sofascore_format = f'{shortened_year}/{int(shortened_year)+1}'

        for season in season_data['seasons']:
            if season_in_sofascore_format == season['year'] or str(year) == season['year']:
                season_id = season['id']
                break

        if season_id == '':
            print(f'No season ID found for {league_name} in {year}')
            return pd.DataFrame()

        limit = 100
        offset = 0

        player_counter = 0

        last_page_complete = False

        while not last_page_complete:


            base_player_stat_url = f"https://www.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/statistics?limit={limit}&offset={offset}&order=-rating"

            if stat_type in ['total', 'per90', 'perGame']:
                stat_type_string = f'&accumulation={stat_type}'
            else:
                print(f'stat type {stat_type} not in the list. Options include: "total", "per90", "perGame" Defaulting to "total"')
                stat_type_string = f'&accumulation=total'
            base_player_stat_url += stat_type_string

            if specific_stats is not None:
                stat_list = [self.stat_name_dict[x] + '%2C' for x in specific_stats]
                stat_string = ''.join(stat_list)
                stat_string = stat_string[:-3]
                base_player_stat_url += f'&fields={stat_string}'
            else:
                stat_list = [x + '%2C' for x in self.stat_name_dict.values()]
                stat_string = ''.join(stat_list)
                stat_string = stat_string[:-3]
                base_player_stat_url += f'&fields={stat_string}'

            #FILTERS

            #positions

            base_player_stat_url += f'&filters=' #Filters is needed by default for the position_string, so the guaranteed %2C needs removing at the end


            if home_or_away_only is not None:
                if home_or_away_only in ['home', 'away']:
                    home_or_away_only_string = f'type.EQ.{home_or_away_only}%2C'
                    base_player_stat_url += home_or_away_only_string

            if min_appearances is not None:
                min_appearances_string = f'appearances.GT.{min_appearances}%2C'
                base_player_stat_url += min_appearances_string

            if age is not None:
                if age_bound in ['LT', 'EQ', 'GT']:
                    age_string = f'age.{age_bound}.{age}%2C'
                    base_player_stat_url += age_string
                else:
                    raise Exception(f'Invalid age bound {age_bound}. Must be "LT" or "EQ" or "GT"')

            if position_list is None:
                position_string = f'position.in.G~D~F~M%2C'
            else:
                position_string = [pos + '~' for pos in position_list]
                position_string = position_string[:-1]
                position_string = f'position.in.{position_string}%2C'

            base_player_stat_url += position_string

            if preferred_foot is not None:
                if preferred_foot in ['left', 'right']:
                    preferred_foot_string = f'type.EQ.{preferred_foot}%2C'
                    base_player_stat_url += preferred_foot_string

            #nationalities

            if nationality_code_list is not None:
                nationality_string = [nat + '~' for nat in nationality_code_list]
                nationality_string = nationality_string[:-1]
                nationality_string = f'nationality.in.{nationality_string}%2C'
                base_player_stat_url += nationality_string

            #teams

            if team_id_list is not None:
                team_string = [nat + '~' for nat in team_id_list]
                team_string = team_string[:-1]
                team_string = f'team.in.{team_string}%2C'
                base_player_stat_url += team_string

            base_player_stat_url = base_player_stat_url[:-3]

            '''
            player_stats_url = "https://api.sofascore.com/api/v1" + \
                          f"/unique-tournament/{league_id}/season/{'96668'}/statistics" + \
                          f"?limit=100&offset='0'" + \
                          f"&accumulation=total" + \
                          f"&fields={self.concatenated_stat_names}" + \
                          f"&filters=position.in.G~D~M~F"
    
            #print(player_stats_url)
            '''

            r = self.session.get(base_player_stat_url, timeout=5)

            stat_data = r.json()
            stat_data = stat_data['results']

            stat_names = self.stat_name_dict.values()

            for player in stat_data:

                player_dict = {field: player.get(field, None) for field in stat_names}
                player_dict['player_name'] = player.get('player', {}).get('name', None)
                player_dict['player_id'] = player.get('player', {}).get('id', None)
                player_dict['team_name'] = player.get('team', {}).get('name', None)
                player_dict['team_id'] = player.get('team', {}).get('id', None)

                player_data_list.append(player_dict)

            time.sleep(5)

            player_counter += len(stat_data)
            print(f'Total {player_counter} players read')

            if len(stat_data) < limit: #Break the while loop when the last page has been read, which will happen when less results are returned than the maximum
                last_page_complete=True

            offset += limit

        player_data_dataframe = pd.DataFrame(player_data_list)

        return player_data_dataframe