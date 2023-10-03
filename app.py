from flask import Flask, render_template, request, jsonify
import creds
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db_settings = {
    'dbname': creds.DB_NAME,
    'user': creds.DB_USER,
    'password': creds.DB_PASS,
    'host': creds.DB_HOST,
    'port': creds.DB_PORT,
}

POSITIONS = {
    "Skater": ('C', 'L', 'R', 'D'),
    "Forward": ('C', 'L', 'R'),
    "Defenceman": ('D',),
    "Goalie": None
}

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/players', methods=['GET'])
def players():

    # Establish a connection to the PostgreSQL database
    conn = psycopg2.connect(**db_settings)
    cursor = conn.cursor()

    # Execute a query to retrieve data from the database
    

    query = """
    SELECT players.id, players."imageLink", players."lastFirstName", skater_stats.season, players."primaryPosition"
    FROM players
    INNER JOIN skater_stats ON players.id = skater_stats.id
    WHERE skater_stats.season = 20222023
    """
    cursor.execute(query)
    # Fetch data from the cursor
    data = list(cursor.fetchall())
    for row_idx in range(len(data)):
        data[row_idx] = list(data[row_idx])
        data[row_idx][3] = str(data[row_idx][3])[:4]
        

    # Close the database connection
    conn.close()

    return render_template('players.html', data=data)

def build_player_query(table_name, season, min_played_toi, position_query):
    time_as_seconds_query = f'CAST(LEFT({table_name}."timeOnIce", POSITION(\':\' IN {table_name}."timeOnIce") - 1) AS INT)*60 + CAST(SUBSTRING({table_name}."timeOnIce", POSITION(\':\' IN {table_name}."timeOnIce")+1, LENGTH({table_name}."timeOnIce")) AS INT) AS toi_seconds'
    
    # Build the SQL query
    query = f"""
        SELECT * FROM (
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
    
    # Establish a connection to the PostgreSQL database (make sure to import psycopg2 and db_settings)
    conn = psycopg2.connect(**db_settings)
    cursor = conn.cursor()
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    # Close the database connection
    conn.close()

    return jsonify(results)

@app.route('/player/<player_id>')
def player(player_id): 
    conn = psycopg2.connect(**db_settings)
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

    
    
    return render_template('player.html', player_data=player_data, player_stats=player_stats)

@app.route('/goal_data/<player_id>')
def goal_data(player_id):
    conn = psycopg2.connect(**db_settings)
    cursor = conn.cursor()
    
    highlight_type = request.args.get('highlight')
    strength_type = request.args.get('strength')
    # year = request.args.get('year')

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
                    AND {event_type_query}"""

    # Execute a query to retrieve data from the database
    cursor.execute(full_query)
    column_names = [description[0] for description in cursor.description]
    results = [dict(zip(column_names, row)) for row in cursor.fetchall()]
    
    cursor.execute(f"""SELECT * 
                       FROM "percentiles"
                       WHERE "id" = '{player_id}'
                       AND "season" = '20222023'
                    """)
    percentile_column_names = [description[0] for description in cursor.description]
    percentile_stats = [dict(zip(percentile_column_names, row)) for row in cursor.fetchall()]

    # Close the database connection
    cursor.close()
    conn.close()
    

    return jsonify((results, percentile_stats))

@app.route("/video/<play_id>")
def video(play_id):
    game_id, goal_id = play_id.split("-")
    
    
    conn = psycopg2.connect(**db_settings)
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
    
    if video_link != None:
        return render_template('video.html', video_link=video_link, goal_data=goal_data)
    else:
        return render_template('video.html', goal_data=goal_data)
    
@app.route("/about")
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
 
