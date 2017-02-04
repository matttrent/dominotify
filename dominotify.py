#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import glob
import time
import json
import subprocess

import requests


DOMINO_API_URL = (
    'https://api.dominodatalab.com/v1/projects/{user_name}/{project_name}/runs')

DOMINO_RESULTS_URL = (
    'https://app.dominodatalab.com/u/{user_name}/{project_name}/results/{id}')

INCOMPLETE_RUNS = {}


class DominoRun(object):

    def __init__(self, rdict):
        self._rdict = rdict

    def __getitem__(self, arg):
        return self._rdict[arg]

    def update(self):

        api_key = os.environ['DOMINO_API_KEY']
        headers = {
            'X-Domino-Api-Key': api_key
        }

        url = DOMINO_API_URL.format(**self._rdict) + '/' + self['id']
        r = requests.get(url, headers=headers)

        rdict = r.json()
        rdict['user_name'] = self['user_name']
        rdict['project_name'] = self['project_name']

        self._rdict = rdict


    def display_notification(self):
        
        title   = 'Domino {user_name}/{project_name}'.format(**self._rdict)
        message = 'Run #{number} {status}'.format(**self._rdict)
        url     = DOMINO_RESULTS_URL.format(**self._rdict)

        cl_call = [
            'terminal-notifier', 
            '-title', title,
            '-message', message,
            '-open', url
        ]

        if self['title'] is not None:
            cl_call += ['-subtitle', self['title']]

        subprocess.run(cl_call)


def find_domino_projects(paths=['.']):

    config_files = []
    for path in paths:
        glob_path = os.path.join(path, '**', '.domino', 'config.json' )
        files = glob.glob(glob_path, recursive=True)
        config_files += files

    local_config = os.path.join('.', '.domino', 'config.json')
    if os.path.isfile(local_config):
        config_files.append(local_config)

    config_files = list(set(config_files))

    projects = []
    for filename in config_files:
        with open(filename) as f:
            projects.append(json.load(f))

    return projects


def fetch_domino_runs(user_name, project_name):

    api_key = os.environ['DOMINO_API_KEY']
    headers = {
        'X-Domino-Api-Key': api_key
    }
    payload  = {
        'page': 1,
    }
    url = DOMINO_API_URL.format(
        user_name=user_name,
        project_name=project_name
    )
    r = requests.get(url, headers=headers, params=payload)
    j = r.json()

    runs = j['data']
    for run in runs:
        run['user_name'] = user_name
        run['project_name'] = project_name

    runs = [DominoRun(r) for r in runs]

    return runs


def add_new_incomplete(runs):

    incomplete = [
        r 
        for r in runs
        if not r['isCompleted']
    ]

    for run in incomplete:
        run_id = run['id']
        if run_id not in INCOMPLETE_RUNS:
            INCOMPLETE_RUNS[run_id] = run


def update_current_runs():

    to_remove = []
    for run_id in INCOMPLETE_RUNS.keys():
        run = INCOMPLETE_RUNS[run_id]
        run.update()

        completed = run['isCompleted']
        if completed:
            to_remove.append(run_id)
            run.display_notification()

    for key in to_remove:
        del INCOMPLETE_RUNS[key]


if __name__ == '__main__':

    if 'DOMINO_API_KEY' not in os.environ:
        print('DOMINO_API_KEY must be set.')
        sys.exit()

    paths = ['.']
    if len(sys.argv) > 1:
        paths = sys.argv[1:]

    projects = find_domino_projects(paths)

    print('watching projects:')
    for proj in projects:
        print('    {owner}/{project_name}'.format(**proj))
    
    while True:

        runs = []
        for p in projects:
            runs += fetch_domino_runs(p['owner'], p['project_name'])
        
        add_new_incomplete(runs)
        update_current_runs()
        time.sleep(60)
