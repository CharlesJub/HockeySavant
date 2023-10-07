from flask import Flask, render_template, request, jsonify
from datetime import datetime
import sqlite3
import requests
from datetime import datetime, timedelta

app = Flask(__name__)


POSITIONS = {
    "Skater": ('C', 'L', 'R', 'D'),
    "Forward": ('C', 'L', 'R'),
    "Defenceman": ('D',),
    "Goalie": None
}

NHL_TEAMS = {
    'ANA': 'Anaheim Ducks',
    'ARI': 'Arizona Coyotes',
    'BOS': 'Boston Bruins',
    'BUF': 'Buffalo Sabres',
    'CGY': 'Calgary Flames',
    'CAR': 'Carolina Hurricanes',
    'CHI': 'Chicago Blackhawks',
    'COL': 'Colorado Avalanche',
    'CBJ': 'Columbus Blue Jackets',
    'DAL': 'Dallas Stars',
    'DET': 'Detroit Red Wings',
    'EDM': 'Edmonton Oilers',
    'FLA': 'Florida Panthers',
    'LAK': 'Los Angeles Kings',
    'MIN': 'Minnesota Wild',
    'MTL': 'Montreal Canadiens',
    'NSH': 'Nashville Predators',
    'NJD': 'New Jersey Devils',
    'NYI': 'New York Islanders',
    'NYR': 'New York Rangers',
    'OTT': 'Ottawa Senators',
    'PHI': 'Philadelphia Flyers',
    'PIT': 'Pittsburgh Penguins',
    'SEA': 'Seattle Kraken',
    'SJS': 'San Jose Sharks',
    'STL': 'St. Louis Blues',
    'TBL': 'Tampa Bay Lightning',
    'TOR': 'Toronto Maple Leafs',
    'VAN': 'Vancouver Canucks',
    'VGK': 'Vegas Golden Knights',
    'WSH': 'Washington Capitals',
    'WPG': 'Winnipeg Jets'
}

@app.template_filter('abbreviationtofull')
def abbrevaiton_to_full(abbr):
    return NHL_TEAMS[abbr]

def get_db_connection():
    # '/home/CharlieJubera/HockeySavant/hockeysavant_app/hockeysavant.db' for server
    conn = sqlite3.connect('hockeysavant_app/hockeysavant.db')
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

@app.route('/')
def index():
    resp = requests.get('https://api-web.nhle.com/v1/schedule/now')
    json = resp.json()
    todays_date = str((datetime.today() - timedelta(hours=9)).date())
    return render_template('index.html', games_data=json, todays_date=todays_date)


@app.route('/players', methods=['GET'])
def players():    

    query = """
    SELECT players.id, players."imageLink", players."lastFirstName", skater_stats.season, players."primaryPosition"
    FROM players
    INNER JOIN skater_stats ON players.id = skater_stats.id
    WHERE skater_stats.season = 20222023
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(query)
    # Fetch data from the cursor
    data = list(cursor.fetchall())
    for row_idx in range(len(data)):
        data[row_idx] = list(data[row_idx])
        data[row_idx][3] = str(data[row_idx][3])[:4]

    cursor.close()
    conn.close()

    return render_template('players.html', data=data)

def build_player_query(table_name, season, min_played_toi, position_query):
    time_as_seconds_query = f"""
        CAST(SUBSTR({table_name}."timeOnIce", 1, INSTR({table_name}."timeOnIce", ':') - 1) AS INTEGER) * 60
        + CAST(SUBSTR({table_name}."timeOnIce", INSTR({table_name}."timeOnIce", ':') + 1) AS INTEGER) AS toi_seconds
    """
    
    # Build the SQL query
    query = f"""
        SELECT *
        FROM (
            SELECT *, {time_as_seconds_query}
            FROM players
            INNER JOIN {table_name} ON {table_name}.id = players.id
            WHERE {table_name}.season = {season}
            {" AND " + position_query if position_query else ''}
        ) AS subquery
        WHERE subquery.toi_seconds > {min_played_toi}
    """
    return query

@app.route('/players_data', methods=['GET'])
def players_data():
    position = request.args.get('position')
    season = request.args.get('season')
    min_played_toi = request.args.get('min_played_toi')
    
    # Check if the position is in the mapping
    if position not in POSITIONS:
        return jsonify({"error": "Invalid position"}), 400
    
    table_name = "skater_stats" if position != "Goalie" else "goalie_stats"
    position_query = (
        f'players."primaryPositionCode" = \'{POSITIONS[position][0]}\'' 
        if position != "Goalie" and len(POSITIONS[position]) == 1 
        else f'players."primaryPositionCode" IN {POSITIONS[position]}' if position != "Goalie" else None
    )

    query = build_player_query(table_name, season, min_played_toi, position_query)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()

    return jsonify(results)

@app.route('/player/<player_id>')
def player(player_id): 

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Execute a query to retrieve data from the database
    cursor.execute(f'SELECT * FROM "players" WHERE id = {player_id}')

    # Fetch data from the cursor
    player_data = list(cursor.fetchone())

    # Get player age from birthdate
    age_timedelta  = datetime.now() - datetime.strptime(player_data[2], "%Y-%m-%d")
    player_data[2] = age_timedelta.days // 365

    if player_data[7] !="Goalie":
        cursor.execute(f'SELECT * FROM "skater_stats" WHERE id={player_id}')
    elif player_data[7] == "Goalie":
        cursor.execute(f'SELECT * FROM "goalie_stats" WHERE id={player_id}')
    player_stats = cursor.fetchall()

    resp = requests.get(f"https://api-web.nhle.com/v1/player/{player_id}/landing")
    player_json = resp.json()
    cursor.close()
    conn.close()
    
    return render_template('player.html', player_data=player_data, player_stats=player_stats, player_info=player_json)


@app.template_filter('predraftteam')
def preDraftTeam(season_drafted, seasons):
    games_played = 0
    main_team = None
    main_league = None
    draft_year = str(season_drafted - 1) + str(season_drafted)
    for season_info in seasons:  
        if str(season_info['season']) == draft_year:  
            
            if games_played < season_info['gamesPlayed']:  
                games_played = season_info['gamesPlayed']
                main_team = season_info['teamName']  
                main_league = season_info['leagueAbbrev']  

    return f"{main_team}, {main_league}"


@app.route('/skater_percentile/<player_id>')
def skater_percentile(player_id):
    year = request.args.get('year')
    print(year)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"""SELECT * 
                       FROM "percentiles"
                       WHERE "id" = '{player_id}'
                       AND "season" = '{year}'
                    """)
    percentile_column_names = [description[0] for description in cursor.description]
    percentile_stats = [dict(zip(percentile_column_names, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify(percentile_stats)

@app.route('/goal_data/<player_id>')
def goal_data(player_id):
    
    highlight_type = request.args.get('highlight')
    strength_type = request.args.get('strength')
    year = request.args.get('year')

    strength_type_query = ""
    event_type_query = ""
    if highlight_type == 'all_events':
        strength_type_query = '"strength" IN (\'EV\', \'PP\', \'SH\')'
    if highlight_type == 'ev_events':
        strength_type_query = '"strength" = \'EV\''
    if highlight_type == 'pp_events':
        strength_type_query = '"strength" = \'PP\''
    if highlight_type == 'sh_events':
        strength_type_query = '"strength" = \'SH\''

    if strength_type == 'goals':
        event_type_query = f'"eventType" = \'Goal\' AND "eventPlayer1" = {player_id}'
    if strength_type == 'assists':
        event_type_query = f'"eventType" = \'Goal\' AND ("eventPlayer2" = {player_id} OR "eventPlayer3" = {player_id})'
    if strength_type == 'goals_for':
        event_type_query = f""" "eventType" = \'Goal\' AND 
                                (("homeTeam" = "eventTeam" AND ("home1" = '{player_id}' OR "home2" = '{player_id}' OR "home3" = '{player_id}' OR "home4" = '{player_id}' OR "home5" = '{player_id}' OR "home6" = '{player_id}')) OR
                                ("awayTeam" = "eventTeam" AND ("away1" = '{player_id}' OR "away2" = '{player_id}' OR "away3" = '{player_id}' OR "away4" = '{player_id}' OR "away5" = '{player_id}' OR "away6" = '{player_id}')))
                                """
    if strength_type == 'goals_against':
        event_type_query = f""" "eventType" = \'Goal\' AND 
                                (("homeTeam" != "eventTeam" AND ("home1" = '{player_id}' OR "home2" = '{player_id}' OR "home3" = '{player_id}' OR "home4" = '{player_id}' OR "home5" = '{player_id}' OR "home6" = '{player_id}')) OR
                                ("awayTeam" != "eventTeam" AND ("away1" = '{player_id}' OR "away2" = '{player_id}' OR "away3" = '{player_id}' OR "away4" = '{player_id}' OR "away5" = '{player_id}' OR "away6" = '{player_id}')))
                                """
    
    full_query = f"""SELECT *
                    FROM play_by_play
                    WHERE {strength_type_query}
                    AND {event_type_query}
                    AND "season"={year}"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Execute a query to retrieve data from the database
    cursor.execute(full_query)
    column_names = [description[0] for description in cursor.description]
    results = [dict(zip(column_names, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jsonify((results))

@app.route("/video/<play_id>")
def video(play_id):
    game_id, goal_id = play_id.split("-")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"""SELECT * 
                    FROM video_links
                    WHERE game_id = {game_id}
                    AND goal_id = '{goal_id}'""")
    video_link = cursor.fetchone()[3]
    cursor.execute(f"""SELECT * 
                    FROM play_by_play
                    WHERE "gameId" = {game_id}
                    AND "playId" = '{goal_id}'""")
    goal_data = cursor.fetchone()

    cursor.close()
    conn.close()
    
    if video_link != None:
        return render_template('video.html', video_link=video_link, goal_data=goal_data)
    else:
        return render_template('video.html', goal_data=goal_data)
    
@app.route("/about")
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
 
