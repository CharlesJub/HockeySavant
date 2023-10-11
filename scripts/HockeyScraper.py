import creds
import requests
from datetime import datetime
import pandas as pd
from selectolax.parser import HTMLParser
from sqlalchemy import create_engine, text as sa_text

class HockeyScraper:
    def min_to_sec(self, time_str):
        """
        Convert a time string in the format 'MM:SS' to seconds.

        Parameters:
            time_str (str): The time string to convert.

        Returns:
            int: The time in seconds.
        """
        time_obj = datetime.strptime(time_str, '%M:%S')
        return time_obj.minute * 60 + time_obj.second
    
    def get_plays(self, game_id):
        """
        Retrieve and parse game plays data from the NHL API.

        Args:
            game_id (int): The unique identifier for the NHL game.

        Returns:
            pd.DataFrame: A Pandas DataFrame containing parsed game plays data.
        """
        # Send a GET request to the NHL API to retrieve game data
        plays_resp = requests.get('https://statsapi.web.nhl.com/api/v1/game/{}/feed/live?site=en_nhl'.format(game_id))
        plays_json = plays_resp.json()
        # Extract teams in game
        season = plays_json['gameData']['game']['season']
        homeTeam = plays_json['gameData']['teams']['home']['triCode']
        awayTeam = plays_json['gameData']['teams']['away']['triCode']
        # Extract plays to itterate over
        plays = plays_json['liveData']['plays']['allPlays']
        # Create list of important plays and empty list to keep future play info
        keyEvents = ['Faceoff','Takeaway','Shot','Goal','Blocked Shot','Hit','Missed Shot','Giveaway']
        allPlays = []
        # Loop over all plays
        for event in plays:
            # Extract Event type and check if it is important, skip if not important
            eventType = event['result']['event']

            if eventType not in keyEvents:
                continue
            # Create eventKey that will be used latter to identify events between play df and shift df
            match eventType:
                case "Faceoff":
                    eventKey = "FAC"
                case "Takeaway":
                    eventKey = "TAKE"
                case "Shot":
                    eventKey = "SHOT"
                case "Goal":
                    eventKey = "GOAL"
                case "Blocked Shot":
                    eventKey = "BLOCK"
                case "Hit":
                    eventKey = "HIT"
                case "Missed Shot":
                    eventKey = "MISS"
                case "Giveaway":
                    eventKey = "GIVE"
            # Extract event info
            eventDescription = event['result']['description']
            shotType = event['result']['secondaryType'] if "secondaryType" in event['result'].keys() else None
            players = event['players'] if 'players' in event.keys() else None
            eventPlayer1 = players[0]['player']['id'] if players != None else None
            eventPlayer2 = players[1]['player']['id'] if players != None and len(players) > 1 else None
            eventPlayer3 = players[2]['player']['id'] if players != None and len(players) > 2 else None
            period = event['about']['period']
            periodTime = self.min_to_sec(event['about']['periodTime'])
            homeGoals = event['about']['goals']['home']
            awayGoals = event['about']['goals']['away']
            coordsX = event['coordinates']['x'] if 'x' in event['coordinates'].keys() else None
            coordsY = event['coordinates']['y'] if 'y' in event['coordinates'].keys() else None
            eventTeam = event['team']['triCode'] if 'team' in event.keys() else None
            playId = eventKey + str(period).zfill(2) + str(periodTime).zfill(4)
            # Append event data to the list
            allPlays.append([season, period,periodTime,eventType,coordsX,coordsY,eventDescription,shotType,eventPlayer1,eventPlayer2,eventPlayer3,homeGoals,awayGoals,eventTeam,homeTeam,awayTeam,playId])
            # Create a Pandas DataFrame from the collected data
        return pd.DataFrame(allPlays, columns=["season","period", "periodTime", "eventType", "coordsX", "coordsY", "eventDescription",'shotType', "eventPlayer1", "eventPlayer2", "eventPlayer3", "homeGoals", "awayGoals", "eventTeam", "homeTeam", "awayTeam", "playId"])

    def get_shifts(self, game_id):
        """
        Retrieve and parse player shifts data for an NHL game.

        Args:
            game_id (int): The unique identifier for the NHL game.

        Returns:
            pd.DataFrame: A Pandas DataFrame containing parsed player shifts data.
        """
        # Construct the URL to fetch HTML report
        year = str(game_id)[:4]
        response = requests.get(f"https://www.nhl.com/scores/htmlreports/{year}{int(year)+1}/PL{str(game_id)[4:]}.HTM")
    
        html = HTMLParser(response.text)
        # Extract relevant elements from the HTML report
        text_elements = html.css(".bborder")
        data = {'Column': text_elements}
        df = pd.DataFrame(data)
        # Organize the extracted data into a DataFrame
        df = df.groupby(df.index // 8).apply(lambda x: pd.Series(x['Column'].values))
        df.columns = ['index', 'period', "strength", "time", "event", "description", "awayOnIce", "homeOnIce"]
        # Get text for simple columns and filter df for important events
        df[['index', 'period', 'strength', 'event', 'description']] = df[['index', 'period', 'strength', 'event', 'description']].applymap(lambda x: x.text())
        df = df[df['event'].isin(['GIVE','FAC','SHOT','HIT','BLOCK','MISS','TAKE','GOAL'])]
        # Get time as int instead of XX:XX string
        time_text = df['time'].apply(lambda x: x.text(separator='\n').split("\n")[0])
        time_text = time_text[time_text != 'Time:']
        df['time'] = pd.to_numeric(time_text.apply(self.min_to_sec), errors='coerce')

        # Get home team from page html
        css_nodes_away = ["table.tablewidth:nth-child(6) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(7)",
                 "div.page:nth-child(3) > table:nth-child(1) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(7)",
                 "table.tablewidth:nth-child(3) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(7)"]
        css_nodes_home = ["table.tablewidth:nth-child(6) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(8)",
                    "div.page:nth-child(3) > table:nth-child(1) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(8)",
                    "table.tablewidth:nth-child(3) > tbody:nth-child(1) > tr:nth-child(3) > td:nth-child(8)"]
        
        for css_selector in css_nodes_away:
            node = html.css_first(css_selector)
            if node != None:
                away_team = node.text()[:3]
        for css_selector in css_nodes_home:
            node = html.css_first(css_selector)
            if node != None:
                home_team = node.text()[:3]
        try:
            if home_team == "S.J":
                home_team = "SJS"
            if away_team == "S.J":
                away_team = "SJS"
            if home_team == "L.A":
                home_team = "LAK"
            if away_team == "L.A":
                away_team = "LAK"
            if home_team == "N.J":
                home_team = "NJD"
            if away_team == "N.J":
                away_team = "NJD"
            if home_team == "T.B":
                home_team = "TBL"
            if away_team == "T.B":
                away_team = "TBL"
        except:
            print(f"https://www.nhl.com/scores/htmlreports/{year}{int(year)+1}/PL{str(game_id)[4:]}.HTM")
            print(game_id)


        # Get list of players on ice
        df['awayOnIce'] = df['awayOnIce'].apply(lambda x: x.css("font[style='cursor:hand;']"))
        df['homeOnIce'] = df['homeOnIce'].apply(lambda x: x.css("font[style='cursor:hand;']"))
        # Get dict of players on ice and their player_ids
        player_on_ice_json = requests.get(f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}").json()
        player_id_dict = {(idx['teamAbbrev'], f"{idx['firstName']} {idx['lastName']}".lower()): idx['playerId'] for idx in player_on_ice_json['data']}

        # Fix player name issues
        player_id_dict[('MIN', 'jacob middleton')] = 8478136
        player_id_dict[('DAL', 'jani hakanpaa')] = 8475825
        player_id_dict[('NSH', 'thomas novak')] = 8478438
        player_id_dict[('DAL', 'marian studenic')] = 8480226
        player_id_dict[('FLA', 'alexander petrovic')] = 8475755
        player_id_dict[('LAK', 'calvin petersen')] = 8477361
        player_id_dict[('NYR', 'timothy gettinger')] = 8479364
        player_id_dict[('VAN', 'quintin hughes')] = 8480800
        player_id_dict[('CHI', 'alexander nylander')] = 8479423
        player_id_dict[('BOS', 'christopher wagner')] = 8475780
        player_id_dict[('CBJ', 'elvis merzlikins')] = 8478007
        player_id_dict[('NJD', 'egor sharangovich')] = 8481068
        player_id_dict[('TBL', 'callan foote')] = 8479984
        player_id_dict[('VGK', 'mattias janmark-nylen')] = 8477406
        player_id_dict[('NYR', 'alexis lafreniere')] = 8482109
        player_id_dict[('CBJ', 'joshua dunne')] = 8482623
        player_id_dict[('OTT', 'tim stutzle')] = 8482116
        player_id_dict[('NJD', 'chase de leo')] = 8478029
        player_id_dict[('ARI', 'janis moser')] = 8482655
        player_id_dict[('OTT', 'nick paul')] = 8477426

        home_column_names = ['home1', 'home2', 'home3', 'home4', 'home5', 'home6']
        away_column_names = ['away1', 'away2', 'away3', 'away4', 'away5', 'away6']

        #
        try:
            # Map player names to player IDs
            for idx in range(len(home_column_names)):
                df[home_column_names[idx]] = [str(player_id_dict[(home_team,x[idx].attributes['title'].split("- ")[-1].lower())]) if len(x) > idx and "Goalie" not in x[idx].attributes['title'] else None for x in df['homeOnIce']]

            for idx in range(len(away_column_names)):
                df[away_column_names[idx]] = [str(player_id_dict[(away_team,x[idx].attributes['title'].split("- ")[-1].lower())]) if len(x) > idx and "Goalie" not in x[idx].attributes['title'] else None for x in df['awayOnIce']]
        except KeyError as e:
            print(game_id, repr(e))
        # Extract goalie information
        df['homeGoalie'] = ["".join(player.attributes['title'] if "Goalie" in player.attributes['title'] else "" for player in x).split("- ")[-1].lower() for x in df['homeOnIce']]
        df['awayGoalie'] = ["".join(player.attributes['title'] if "Goalie" in player.attributes['title'] else "" for player in x).split("- ")[-1].lower() for x in df['awayOnIce']]
        # Map goalie names to goalie player IDs
        df['homeGoalie'] = [str(player_id_dict[(home_team,x)]) if x != "" else None for x in df['homeGoalie']]
        df['awayGoalie'] = [str(player_id_dict[(away_team,x)]) if x != "" else None for x in df['awayGoalie']]
        # Create a unique-ish play ID
        df['playId'] = df['event'] + df['period'].str.zfill(2) +  df['time'].astype(str).str.zfill(4)
        # Drop unnecessary columns and reset the index
        return df.drop(columns=['index','awayOnIce', 'homeOnIce'], axis=1).reset_index(drop=True)

    def get_game(self, game_id):
        """
        Retrieve and combine game plays and player shifts data for an NHL game.

        Args:
            game_id (int): The unique identifier for the NHL game.

        Returns:
            pd.DataFrame: A Pandas DataFrame containing combined game data.
        """
       # Retrieve game plays data
        plays = self.get_plays(game_id)
        # Retrieve player shifts data
        try:
            shifts = self.get_shifts(game_id)
        except AttributeError as e:
            repr(e)
            print(game_id)
        # Merge plays and shifts data based on playId
        game_df = pd.merge(plays, shifts, left_on="playId", right_on='playId', how="left")
        
        # Add gameId to the DataFrame
        game_df['gameId'] = game_id
        
        # Drop duplicate entries based on specific columns
        game_df = game_df.drop_duplicates(keep="first", subset=['coordsX', 'coordsY', 'eventDescription', 'playId'])
        
        return game_df
    
    def get_game_ids(self, start_date, end_date):
        """
        Get the game IDs for NHL games within the specified date range.

        Parameters:
            start_date (str): Start date in the format 'YYYY-MM-DD'.
            end_date (str): End date in the format 'YYYY-MM-DD'.

        Returns:
            list: List of game IDs.
        """
        # Retrieve the schedule JSON data from the NHL API
        schedule = requests.get(f"https://statsapi.web.nhl.com/api/v1/schedule?startDate={start_date}&endDate={end_date}&gameType=R").json()
        # Extract the game IDs from the schedule JSON
        game_ids = [game['gamePk'] for day in schedule['dates'] for game in day['games']]
        
        return game_ids

    def scrape_games_to_SQL(self, start_date, end_date):
        """
        Scrape NHL game data for a specified date range and store it in a PostgreSQL database.

        Args:
            start_date (str): The start date in 'YYYY-MM-DD' format.
            end_date (str): The end date in 'YYYY-MM-DD' format.
        """
        # Construct the connection string using your credentials
        con_string = f"postgresql+psycopg2://{creds.DB_USER}:{creds.DB_PASS}@{creds.DB_HOST}/{creds.DB_NAME}"

        # Create a database engine and connect to the database
        engine = create_engine(con_string)
        conn = engine.connect()

        # Get a list of game IDs within the specified date range
        game_ids = self.get_game_ids(start_date, end_date)
        # Check if play_by_play table exists
        table_exists = engine.dialect.has_table(conn, 'play_by_play')

        if table_exists:
            game_ids_parsed = pd.read_sql('SELECT "gameId" FROM play_by_play', conn).gameId.unique()
        else:
            game_ids_parsed = []  # Initialize an empty list if the table doesn't exist
        
        conn.close() # Close connection

        # Iterate through game IDs and scrape data for new games
        for game in game_ids:
        
            if game not in game_ids_parsed:
                # Get game data
                game_df = self.get_game(game)
                # Append the game data to the 'play_by_play' table in the database
                game_df.to_sql('play_by_play', engine, if_exists='append', index=False)

        engine.dispose() # Close engine

    def get_player_info(self, player_id):
        # TODO - Add docstring
        """
        
        """
        # Get descriptive info for each player that is independent of season
        url = "https://statsapi.web.nhl.com/api/v1/people/{}".format(player_id)
        response = requests.get(url)
        
        if response.status_code == 200:
            json_data = response.json()
            player_info = json_data['people'][0]
            birthDate = player_info.get('birthDate', None)
            nationality = player_info.get('nationality', None)
            height = player_info.get('height', None)
            weight = player_info.get('weight', None)
            shootsCatches = player_info.get('shootsCatches', None)
            primaryPosition = player_info['primaryPosition']['name'] if 'primaryPosition' in player_info else None
            primaryPositionCode = player_info['primaryPosition']['code'] if 'primaryPosition' in player_info else None
            return birthDate, nationality, height, weight, shootsCatches, primaryPosition, primaryPositionCode
        else:
            # Handle the case where the request was not successful
            return None, None, None, None, None, None, None
    
    def players_to_SQL(self, season):
        """
        Scrape NHL players with descriptive data to a SQL database

        Args:
            season (int): The years of the season (ex. 20222023)
        """
        # Construct the connection string using your credentials
        con_string = f"postgresql+psycopg2://{creds.DB_USER}:{creds.DB_PASS}@{creds.DB_HOST}/{creds.DB_NAME}"

        # Create a database engine and connect to the database
        engine = create_engine(con_string)
        conn = engine.connect()
        
        table_exists = engine.dialect.has_table(conn, 'players')

        if table_exists:
            parsed_ids = pd.read_sql('SELECT "id" FROM players', conn).id.unique()
        else:
            parsed_ids = []  # Initialize an empty list if the table doesn't exist

        conn.close()
        engine.dispose()

        url = 'https://statsapi.web.nhl.com/api/v1/teams/?expand=team.roster&season={}'.format(season)
        resp = requests.get(url)
        json = resp.json()
        players = []
        for team in json['teams']:
            for player in team['roster']['roster']:
                player_id = player['person']['id']
                player_name = player['person']['fullName']

                players.append([player_id,player_name])
        df = pd.DataFrame(players, columns=['id', 'name'])
        df = df.drop_duplicates()

        df_filtered = df[~(df['id'].isin(parsed_ids))].copy()
        if len(df_filtered) < 1:
            return

        df_filtered[['birthDate', 'nationality', 'height', 'weight', 'shootsCatches', 'primaryPosition', 'primaryPositionCode']] = df_filtered['id'].apply(lambda x: pd.Series(self.get_player_info(x)))
        df_filtered['imageLink'] = df.apply(lambda row: f"https://cms.nhl.bamgrid.com/images/headshots/current/168x168/{row['id']}.jpg", axis=1)
        engine = create_engine(con_string)
        df_filtered.to_sql('players'.format(season), engine, if_exists='append', index=False)
        engine.dispose()
    
    def get_skater_stats(self, skater_id, season):
        url = "https://statsapi.web.nhl.com/api/v1/people/{}/stats?stats=statsSingleSeason&season={}".format(skater_id, season)
        response = requests.get(url)
        # Check if we get right status
        if response.status_code == 200:

            json = response.json()
            # If the player didn't play in the season splits length will be less than 1
            if len(json['stats'][0]['splits']) < 1:
                return [None for _ in range(15)]
            else:
                # Set stats to subsection of json with stats
                stats = json['stats'][0]['splits'][0]['stat']
            
            key_stats = ['games','goals','assists','points','shots','shotPct','pim','timeOnIce','evenTimeOnIce', 'powerPlayTimeOnIce', 'shortHandedTimeOnIce', 'timeOnIcePerGame','evenTimeOnIcePerGame','powerPlayTimeOnIcePerGame','shortHandedTimeOnIcePerGame']
            # return list of key stats or none if can't find value in dict
            return [stats.get(x, None) for x in key_stats]
        else:
            # Handle the case where the request was not successful
            print(f"Request failed for {skater_id}, {season}")
            return [None for _ in range(15)]

    def skater_stats_to_SQL(self, season):
        # Construct the connection string using your credentials
        con_string = f"postgresql+psycopg2://{creds.DB_USER}:{creds.DB_PASS}@{creds.DB_HOST}/{creds.DB_NAME}"

        # Create a database engine and connect to the database
        engine = create_engine(con_string)
        conn = engine.connect()

        # Check if the player database exists to pull player ids
        table_exists = engine.dialect.has_table(conn, 'players')
        # If the table exists then get id and position to use for filtering later
        if table_exists:
            player_ids = pd.read_sql('SELECT "id","primaryPosition" FROM players', conn)
        else:
            print("Can't find players database")
            return
        # Filter out goalies
        skater_stats = player_ids[player_ids['primaryPosition'] != "Goalie"].copy()

        # Create list of stats to scrape
        key_stats = ['games','goals','assists','points','shots','shotPct','pim','timeOnIce','evenTimeOnIce', 'powerPlayTimeOnIce', 'shortHandedTimeOnIce', 'timeOnIcePerGame','evenTimeOnIcePerGame','powerPlayTimeOnIcePerGame','shortHandedTimeOnIcePerGame']
        skater_stats['season'] = season
        # Scrape stats and add them as columns to database
        skater_stats[key_stats] = skater_stats.apply(lambda row: pd.Series(self.get_skater_stats(row['id'], season)), axis=1)
        # Drop rows where the player has no stats for the season
        skater_stats = skater_stats.dropna(subset=key_stats, how='all')
        skater_stats = skater_stats.drop('primaryPosition', axis=1)
        # Grab current skater_stats table
        table_exists = engine.dialect.has_table(conn, 'skater_stats')
        # If the table exists then get id and position to use for filtering later
        if table_exists:
            skater_stats_old = pd.read_sql('SELECT * FROM skater_stats', conn)
            # Drop table of old stats bc replacing in to_sql is slow
            conn.execute(sa_text("DROP TABLE skater_stats"))
            conn.commit()
            # Append new data to skater_stats
            skater_stats = pd.concat([skater_stats_old, skater_stats])
            # Remove duplicates, keeping newest entry
            skater_stats = skater_stats.drop_duplicates(keep='last', subset=['id','season'])
            # Update table with new stats data
            skater_stats.to_sql("skater_stats", if_exists='append', con=engine, index=False, method='multi')
        else:
            # Update table with new stats data
            skater_stats.to_sql("skater_stats", if_exists='append', con=engine, index=False, method='multi')

        conn.close() # Close connection
        engine.dispose() # Close engine

    def get_season_start_end_date(self,season):
        url = f"https://statsapi.web.nhl.com/api/v1/seasons/{season}"
        resp = requests.get(url)

        if resp.status_code == 200:
            json = resp.json()
            start_date = json['seasons'][0]['regularSeasonStartDate']
            end_date = json['seasons'][0]['regularSeasonEndDate']
            return start_date, end_date
        else:
            # Handle the case where the request was not successful
            print(f"Request failed for {season} dates.")
            return

    def get_goalie_stats(self, goalie_id, season):
        url = "https://statsapi.web.nhl.com/api/v1/people/{}/stats?stats=statsSingleSeason&season={}".format(goalie_id, season)
        resp = requests.get(url)
        
        if resp.status_code == 200:
            json = resp.json()
            if len(json['stats'][0]['splits']) < 1:
                return [None for _ in range(10)]
            stats = json['stats'][0]['splits'][0]['stat']
            key_stats = ['games','gamesStarted','timeOnIce','wins','losses','savePercentage','goalAgainstAverage','powerPlaySavePercentage','shortHandedSavePercentage','evenStrengthSavePercentage']
            return [stats.get(x, None) for x in key_stats]
        else:
            print(f"Failed request when retreiving goalie stats for: {goalie_id}, {season}")
            return [None for _ in range(10)]

    def goalie_stats_to_SQL(self, season):
        # Construct the connection string using your credentials
        con_string = f"postgresql+psycopg2://{creds.DB_USER}:{creds.DB_PASS}@{creds.DB_HOST}/{creds.DB_NAME}"

        # Create a database engine and connect to the database
        engine = create_engine(con_string)
        conn = engine.connect()

        # Check if the player database exists to pull player ids
        table_exists = engine.dialect.has_table(conn, 'players')
        # If the table exists then get id and position to use for filtering later
        if table_exists:
            player_ids = pd.read_sql('SELECT "id","primaryPosition" FROM players', conn)
        else:
            print("Can't find players database")
            return
        # Filter out goalies
        goalie_stats = player_ids[player_ids['primaryPosition'] == "Goalie"].copy()

        # Create list of stats to scrape
        key_stats = ['games','gamesStarted','timeOnIce','wins','losses','savePercentage','goalAgainstAverage','powerPlaySavePercentage','shortHandedSavePercentage','evenStrengthSavePercentage']
        goalie_stats['season'] = season
        # Scrape stats and add them as columns to database
        goalie_stats[key_stats] = goalie_stats.apply(lambda row: pd.Series(self.get_goalie_stats(row['id'], season)), axis=1)
        # Drop rows where the player has no stats for the season
        goalie_stats = goalie_stats.dropna(subset=key_stats, how='all')
        goalie_stats = goalie_stats.drop('primaryPosition', axis=1)
        # Grab current skater_stats table
        table_exists = engine.dialect.has_table(conn, 'goalie_stats')
        # If the table exists then get id and position to use for filtering later
        if table_exists:
            goalie_stats_old = pd.read_sql('SELECT * FROM goalie_stats', conn)
            # Drop table of old stats bc replacing in to_sql is slow
            conn.execute(sa_text("DROP TABLE goalie_stats"))
            conn.commit()
            # Append new data to skater_stats
            goalie_stats = pd.concat([goalie_stats_old, goalie_stats])
            # Remove duplicates, keeping newest entry
            goalie_stats = goalie_stats.drop_duplicates(keep='last', subset=['id','season'])
            # Update table with new stats data
            goalie_stats.to_sql("goalie_stats", if_exists='append', con=engine, index=False, method='multi')
        else:
            # Update table with new stats data
            goalie_stats.to_sql("goalie_stats", if_exists='append', con=engine, index=False, method='multi')

        conn.close() # Close connection
        engine.dispose() # Close engine

    def scrape_videos(self):
        con_string = f"postgresql+psycopg2://{creds.DB_USER}:{creds.DB_PASS}@{creds.DB_HOST}/{creds.DB_NAME}"

        # Create a database engine and connect to the database
        engine = create_engine(con_string)
        conn = engine.connect()

        # Check if the player database exists to pull player ids
        table_exists = engine.dialect.has_table(conn, 'play_by_play')
        # If the table exists then get id and position to use for filtering later
        if table_exists:
            goals = pd.read_sql('SELECT * FROM play_by_play WHERE "eventType"= \'Goal\'', conn)
        else:
            print("Can't find players database")

        table_exists = engine.dialect.has_table(conn, 'video_links')
        # If the table exists then get id and position to use for filtering later
        if table_exists:
            videos = pd.read_sql('SELECT * FROM video_links', con=conn)
            goals = goals[~(goals[['gameId', 'playId']].isin(videos[['game_id', 'goal_id']]).all(axis=1))].copy()    
        else:
            print("Can't find video_links database")
        
        conn.close()

        video_data = []
        t1 = datetime.now()

        game_ids = goals['gameId'].unique()
        print(len(game_ids))
        i = 0
        for game_id in game_ids:
            if i % 100 == 0:
                print(i, datetime.now() - t1)

            game_goals = goals[goals['gameId'] == game_id]
            game_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing"
            game_resp = requests.get(game_url)
            game_json = game_resp.json()
            for idx, row in game_goals.iterrows():
                for goal in game_json['summary']['scoring'][row[1]-1]['goals']:
                    video_code = None
                    video_link = None
                    if self.min_to_sec(goal['timeInPeriod']) == row[2]:
                        if "highlightClip" in goal.keys():
                            video_code = goal['highlightClip']
                            video_link = f"https://players.brightcove.net/6415718365001/EXtG1xJ7H_default/index.html?videoId={video_code}"
                        video_data.append([video_code,row[36],row[16],video_link])
            i += 1
        

        video_links = pd.DataFrame(video_data, columns=['video_code', 'game_id', 'goal_id', 'video_link'])

        engine = create_engine(con_string)
        conn = engine.connect()
        
        video_links.to_sql("video_links",if_exists='append', con=conn, index=False)

        conn.close() # Close connection
        engine.dispose() # Close engine





if __name__ == '__main__':
    scraper = HockeyScraper()
    season_codes = [20182019,20192020,20202021,20212022,20222023]
    for season in season_codes:
        print("-"*15 + str(season) + "-"*15)
        season_start, season_end = scraper.get_season_start_end_date(season)
        print(f"Start time: {datetime.now()}")
        print("Scrape Games")
        t1 = datetime.now()
        scraper.scrape_games_to_SQL(season_start, season_end)
        t2 = datetime.now()
        print("Runtime: " + str(t2-t1))

        
        print("Scrape Players")
        t1 = datetime.now()
        scraper.players_to_SQL(season)
        t2 = datetime.now()
        print("Runtime: " + str(t2-t1))


        print("Scrape Skater Stats")
        t1 = datetime.now()
        scraper.skater_stats_to_SQL(season)
        t2 = datetime.now()
        print("Runtime: " + str(t2-t1))

        print("Scrape Goalie Stats")
        t1 = datetime.now()
        scraper.goalie_stats_to_SQL(season)
        t2 = datetime.now()
        print("Runtime: " + str(t2-t1))

    


    

    # links https://statsapi.web.nhl.com/api/v1/game/2022020511/feed/live?site=en_nhl
    # https://www.nhl.com/scores/htmlreports/20222023/PL020511.HTM
    # https://api-web.nhle.com/v1/gamecenter/2022020968/play-by-play
    # https://api-web.nhle.com/v1/gamecenter/2022020968/landing