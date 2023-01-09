import pandas as pd
import numpy as np

import lzma
import json

import requests
import os

"""
The `awpy` package provides data parsing, analytics and visualization capabilities for Counter-Strike: Global Offensive (CSGO) demo data [1].
It can be installed by `!pip install awpy`.
GitHub page: https://github.com/pnxenopoulos/awpy
"""
from awpy.visualization.plot import plot_round
from IPython.display import Image


def aggregate_players_info(df_original):
    """
    This function takes in the original dataset and aggregates the player information into team-based information
    input: pandas DataFrame
    returns: pandas DataFrame
    """

    df = df_original.copy()

    df['ctDefusers'] = 0
    df['tHasBomb'] = 0

    for team in ['t', 'ct']:

        df[f'{team}Alive'] = 0
        df[f'{team}Hp'] = 0
        df[f'{team}Armor'] = 0
        df[f'{team}Helmet'] = 0
        df[f'{team}EquipmentValue'] = 0
        df[f'{team}Utility'] = 0
        df[f'{team}PlayersInBombZone'] = 0

        for ax in ['x', 'y', 'z']:
            # It is possible to have RuntimeWarning when team is 't', since
            # the round continues even if all T players are eliminated when the bomb is already planted
            df[f'{team}MeanPos_{ax}'] = np.nanmean(
                [df[f'{team}_p{i}_{ax}'] for i in range(5)], axis=0)
            df[f'{team}StdDevPos_{ax}'] = np.nanstd(
                [df[f'{team}_p{i}_{ax}'] for i in range(5)], axis=0)

        for i in range(5):

            # If the player is alive, add it to the number of players alive on the team
            df[f"{team}Alive"] += df[f'{team}_p{i}_isAlive']

            # For all the features below, if the player is eliminated, the value will be NaN.
            # Use np.nan_to_num to convert NaN to zero.
            if team == 'ct':
                df['ctDefusers'] += np.nan_to_num(df[f'ct_p{i}_hasDefuse'])
                df.drop(f'ct_p{i}_hasDefuse', axis=1, inplace=True)

            if team == 't':
                df['tHasBomb'] += np.nan_to_num(df[f't_p{i}_hasBomb'])
                df.drop(f't_p{i}_hasBomb', axis=1, inplace=True)

            df[f'{team}Hp'] += np.nan_to_num(df[f'{team}_p{i}_hp'])
            df[f'{team}Armor'] += np.nan_to_num(df[f'{team}_p{i}_armor'])
            df[f'{team}Helmet'] += np.nan_to_num(df[f'{team}_p{i}_hasHelmet'])
            df[f'{team}EquipmentValue'] += np.nan_to_num(
                df[f'{team}_p{i}_equipmentValue'])
            df[f'{team}Utility'] += np.nan_to_num(
                df[f'{team}_p{i}_totalUtility'])
            df[f'{team}PlayersInBombZone'] += np.nan_to_num(
                df[f'{team}_p{i}_isInBombZone'])

            # Drop the original variables
            df.drop(f'{team}_p{i}_hp', axis=1, inplace=True)
            df.drop(f'{team}_p{i}_armor', axis=1, inplace=True)
            df.drop(f'{team}_p{i}_hasHelmet', axis=1, inplace=True)
            df.drop(f'{team}_p{i}_equipmentValue', axis=1, inplace=True)
            df.drop(f'{team}_p{i}_totalUtility', axis=1, inplace=True)
            df.drop(f'{team}_p{i}_isInBombZone', axis=1, inplace=True)
            df.drop(f'{team}_p{i}_isAlive', axis=1, inplace=True)

            for ax in ['x', 'y', 'z']:
                df.drop(f'{team}_p{i}_{ax}', axis=1, inplace=True)

    return df


# Function to read .xz archives from ESTA
def read_parsed_demo(filename):
    with lzma.LZMAFile(filename, "rb") as f:
        d = json.load(f)
        return d


# Function to download the demo file from the ESTA dataset
def download_demo(demoId, replace=False):

    isExist = os.path.exists('demos/')
    if not isExist:
        os.makedirs('demos/')
        print('Created the directory ./demos/')

    directory = os.getcwd()
    filename = directory + '/demos/{}.json.xz'.format(demoId)

    if (os.path.exists(filename)) and (replace == False):
        print('File already exists. No need to download again.')
        return None

    url = "https://github.com/pnxenopoulos/esta/blob/main/data/online/{}.json.xz?raw=true".format(
        demoId)
    r = requests.get(url)

    # If it is not in the online data folder, try the lan data folder
    if r.status_code == 404:
        url = "https://github.com/pnxenopoulos/esta/blob/main/data/lan/{}.json.xz?raw=true".format(
            demoId)
        r = requests.get(url)

    # If the file is found
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(r.content)

    return r.status_code


def render_and_display_round(demo, demoId, round_num, replace=False):
    """
    Requires the awpy package.
    params:
        replace: whether to render and replace the gif if it already exists
    returns:
        Image() object
    """
    isExist = os.path.exists('./rendered_gifs/')
    if not isExist:
        os.makedirs('rendered_gifs/')
        print('Created the directory rendered_gifs/')

    image_path = "rendered_gifs/{}-{}.gif".format(demoId, round_num)

    # Render the gif of the round if it does not exist yet, and replace == True
    if (replace == True) or (not os.path.exists(image_path)):
        plot_round(image_path, demo["gameRounds"][round_num - 1]
                   ["frames"], map_name=demo["mapName"], map_type="original")

    # Draw the gif
    return Image(filename=image_path, width=500)


# Prints out the metadata about the demo
def print_demo_info(demo):
    print('Match information:')
    for k in ['mapName', 'demoId', 'competitionName', 'hltvUrl', 'matchDate', 'matchName']:
        if k != "gameRounds":
            print(k + ": " + str(demo[k]))