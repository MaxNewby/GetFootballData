# GetFootballData

This package contains classes to read data from Sofascore, FotMob and Transfermarkt.

To make it easier league naming conventions are derived from other packages such as ScraperFC to make this package more compatible with others.

Created by Max Newby

>[NOTE] about using the 'league_name' parameter
>
>
>To see the format in which the league_name parameter should be entered in, check the dictionary keys in any _map.py file inside scraper_utilities.
> Examples include; 'ENG-Premier League', 'ESP-La Liga', 'GER-Bundesliga'.

## <u>Using the Package:</u>

### Sofascore_scraper.py:

Create a SofascoreScraper object: `ss_scraper = SofascoreScraper()`

The object then comes with the following methods:

`ss_scraper.get_player_id_dicts(self, year: int, league_name: str) -> dict[int, dict[str, str | dict[int, str]]]`

This method returns a dictionary containing {team_id: team_data} pairs. Inside team_data, is the 'team_name' and another dictionary 'player_id_dict' that contains the {player_id, player_name} pairs.

    year: Takes the starting year of the given season.
    league_name: Takes the name of the given league in the given format.
    
    return: a dictionary of team names mapping to dictionaries containing player ids and names in the format {team_id: {name: team_name, player_dict: {player_id: player_name, ...}}, ...}.


`ss_scraper.get_player_metadata_df(self, year: int, league_name: str) -> pd.Dataframe`

This method returns a dataframe containing general data about each player in the league for a given season.

    :param year: starting year of the given season.
    :param league_name: name of the league according to the given format.

    :return: a pd.DataFrame containing general data about each player in a given league (height, preferred foot, etc.).

`ss_scraper.get_player_stat_df(self, year: int, league_name: str, stat_type='total', specific_stats=None, position_list=None, nationality_code_list=None, team_id_list=None, min_appearances=None, age=None, age_bound='EQ', home_or_away_only=None, preferred_foot=None) -> pd.DataFrame:`

This method will return a dataframe containing statistical data for every player in the league for that given season. Responses can be filtered using the parameters.

    year: starting year of the league in the given format
    league_name: name of the league in the wanted format
    stat_type: 'total', 'per90', 'perGame'
    specific_stats: accepts a list of specific stats to return. Stats can be listed as seen on sofascore, in a league->stats->detailed tab
    position_list: accepts a list of positions to return. options ['G', 'D', 'M', 'F']
    nationality_code_list: accepts a list of nationality codes to return.
    team_id_list: enter a list of sofascore's team IDs to return data only from those teams.
    min_appearances: min appearances of a player in the given league/year
    age: age of the player in the given league/year
    age_bound: options: 'LT', 'EQ', 'GT'
    home_or_away_only: 'home', 'away'
    preferred_foot: 'left', 'right'. Returns only players with the given preferred foot.

    return: a dataframe containing all records of stat data of given filters, for players in a given season and league

### fotmob_scraper.py:

Create a FotmobScraper object: `fotmob_scraper = FotmobScraper()`

The object then comes with the following methods:

 `fotmob_scraper.get_player_data_df(self, year: int, league_name: str) -> pd.DataFrame`

This method scrapes statistical player data, for every player in the league for a given season

    year: starting year of the league (ex. 2025)
    league_name: league name in the package's standardised format: (ex. 'ENG-Premier League')
    return: a pd.Dataframe instance containing the player data.



### transfermarkt_scraper.py:

Create a TransfermarktScraper object: `transfermarkt_scraper = TransfermarktScraper()`

The object then comes with the following methods:

`transfermarkt_scraper.get_player_transfer_history(self, player_id: str) -> pd.DataFrame:`

This method returns a dataframe containing a player's transfer history, and data such as fees and contract durations for each transfer.

    player_id: transfermarkt's player id (as seen in the url of a player's profile)
    return: A pandas dataframe containing a row for every recorded transfer a given player has had according to transfermarkt. If there is no history, an empty dataframe is returned. Rows include;


`transfermarkt_scraper.get_player_overview_df(self, year: int, league: str)`

This method scrapes general player data such as transfermarkt ids, nationality and club for every player in the given league

    year: starting year of the league (ex. 2025)
    league: league name according to the package's naming conventions (ex. 'ENG-Premier League', 'FRA-Ligue 1')
    return: a dataframe containing: player_name, player_id, club_name, nation. If data can't be found, an empty dataframe is returned.

