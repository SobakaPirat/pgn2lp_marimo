import marimo

__generated_with = "0.15.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Converter pgn to liquipedia format""")
    return


@app.cell(hide_code=True)
def _(mo):
    pgn_file = mo.ui.file(filetypes=[".pgn"], kind="area")

    mo.md(f"""
    ### Upload your pgn file here
    {pgn_file}
    """)
    return (pgn_file,)


@app.cell(hide_code=True)
def _(mo):
    win_points_selector = mo.ui.number(start=0, value=1, label="Win")
    draw_points_selector = mo.ui.number(start=0, value=0.5, label="Draw")
    loss_points_selector = mo.ui.number(start=0, value=0, label="Lose")
    points_changed = mo.ui.switch(label="Use custom points system")
    round_selector = mo.ui.number(start=0, step=1, label="Round to filter")
    players_to_filter_selector = mo.ui.text_area(
        placeholder="Smyslov, Vassily\nGeller, Efim\nDueckstein, Andreas\nVassily Smyslov\nEfim Geller\nAndreas Dueckstein",
        label="Players to filter",
        full_width=True,
    )

    point_selectors = mo.hstack(
        [win_points_selector, draw_points_selector, loss_points_selector],
        align="center",
        justify="space-around",
        gap=0.25,
    )

    points_tab = mo.vstack([points_changed, point_selectors])


    mo.ui.tabs(
        {
            "🔹 Rounds": round_selector,
            "🔹 Points": points_tab,
            "🔹 Players": players_to_filter_selector,
        }
    )
    return (
        draw_points_selector,
        loss_points_selector,
        players_to_filter_selector,
        points_changed,
        round_selector,
        win_points_selector,
    )


@app.cell(hide_code=True)
def _(mo, output_text):
    copy_result = mo.ui.code_editor(
        value=output_text, 
        max_height=300
        )

    mo.md(f"""
    -----
    **Matches for Round Robbin**
    {copy_result}
    """)
    return


@app.cell
def _(games_info, mo):
    participant_table = generate_participant_table(games_info)
    copy_participants = mo.ui.code_editor(
        value=participant_table, 
        max_height=300
        )

    mo.md(f"""
    **Participant Table**
    {copy_participants}
    """)
    return


@app.cell
def _(
    draw_points_selector,
    loss_points_selector,
    players_to_filter_selector,
    round_selector,
    win_points_selector,
):
    draw_points = draw_points_selector.value
    loss_points = loss_points_selector.value
    win_points = win_points_selector.value
    round_to_filter = round_selector.value
    players_to_filter = players_to_filter_selector.value.splitlines()
    #[win_points, draw_points, loss_points, round_to_filter, players_to_filter]
    return (
        draw_points,
        loss_points,
        players_to_filter,
        round_to_filter,
        win_points,
    )


@app.cell
def _(draw_points, loss_points, points_changed, re, read_game, win_points):
    def swap_name_surname(full_name):
        parts = full_name.split(',')
        if len(parts) < 2:
            return full_name
        surname = parts[0].strip()
        name = parts[1].strip()
        return f'{name} {surname}'

    def format_result(result):
        return {'1-0': 1, '0-1': 2}.get(result, 0)

    def custom_score(result, white):
        if result == 1:
            return win_points if white else loss_points
        elif result == 2:
            return loss_points if white else win_points
        else:
            return draw_points

    def parse_pgn(pgn):
        matches = []
        while True:
            game_info = {}
            game = read_game(pgn)
            if game is None:
                break
            game_info['white'] = game.headers.get('White', '')
            game_info['white_formated'] = swap_name_surname(re.sub('\\b[A-Z]{3}\\b', '', game_info['white']))
            game_info['white_team'] = game.headers.get('WhiteTeam', '')
            game_info['black'] = game.headers.get('Black', '')
            game_info['black_formated'] = swap_name_surname(re.sub('\\b[A-Z]{3}\\b', '', game_info['black']))
            game_info['black_team'] = game.headers.get('BlackTeam', '')
            game_info['date'] = game.headers.get('UTCDate', '') or game.headers.get('Date', '')
            game_info['date_formated'] = re.sub('-\\?\\?|\\?{4}', '', game_info['date'].replace('.', '-'))
            game_info['time'] = game.headers.get('UTCTime', '') or game.headers.get('Time', '')
            game_info['time_formated'] = f' - {game_info['time']}' if game_info.get('time') else ''
            game_info['result'] = game.headers.get('Result', '')
            game_info['result_formated'] = format_result(game_info['result'])
            game_info['round'] = game.headers.get('Round', '').replace(',', '.').split('.')[0]
            game_info['eco'] = game.headers.get('ECO', '')
            game_info['moves'] = game.end().board().fullmove_number
            if points_changed.value:
                game_info['white_score'] = custom_score(game_info['result_formated'], True)
                game_info['black_score'] = custom_score(game_info['result_formated'], False)
            matches.append(game_info)
        return matches
    return (parse_pgn,)


@app.cell
def _(StringIO, codecs, parse_pgn, pgn_file):
    try:
        pgn_decoded = StringIO(codecs.decode(pgn_file.value[0].contents, encoding="utf-8"))
        games_info = parse_pgn(pgn_decoded)
        print("file has been successfully read.")
    except:
        games_info = ""
        print("Unable to read your file.")
    return (games_info,)


@app.cell
def _(games_info, players_to_filter, round_to_filter):
    output_text = ""
    if games_info:
        for game_info in games_info:
          #filter players
          if players_to_filter and all(
            player not in players_to_filter
            for player in (
                game_info["white"],
                game_info["black"],
                game_info["white_formated"],
                game_info["black_formated"])):
            continue
          #filter round
          if (round_to_filter == 0) or (str(round_to_filter) == game_info["round"]):
            output_text += (f'''|{{{{Match
        |finished=true
        |date={game_info["date_formated"]}{f'{game_info["time_formated"]} {{{{abbr/UTC}}}}'if game_info.get('time_formated') else ''}
        |opponent1={{{{1Opponent|flag=|{game_info["white_formated"]}{f'|score={game_info["white_score"]}'if game_info.get('white_score') else ''}}}}}
        |opponent2={{{{1Opponent|flag=|{game_info["black_formated"]}{f'|score={game_info["black_score"]}'if game_info.get('black_score') else ''}}}}}
        |map1={{{{Map|winner={game_info["result_formated"]}|white=1|eco={game_info["eco"]}|length={game_info["moves"]}}}}}
    }}}}
    ''')
    return (output_text,)


@app.function
def generate_participant_table(games):
    participants = {}
    for game in games:
        if game['white_formated'] not in participants:
            participants[game['white_formated']] = game['white_team']
        if game['black_formated'] not in participants:
            participants[game['black_formated']] = game['black_team']
    participants_output = []
    for participant_name, participant_team in participants.items():
        participants_output.append(f"|{{{{1Opponent|{participant_name}|flag={participant_team}|team=}}}}\n")
    participants_joined = "".join(participants_output)
    participants_formated = f"==Participants==\n{{{{ParticipantTable|count=1|colspan=|entrywidth=|title=|onlyNotable=\n{participants_joined}}}}}"

    return participants_formated


@app.cell
def _():
    import marimo as mo
    import codecs
    import re
    from chess.pgn import read_game
    from io import StringIO
    return StringIO, codecs, mo, re, read_game


if __name__ == "__main__":
    app.run()
