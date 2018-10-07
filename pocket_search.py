#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import json
import requests
import webbrowser
import argparse
import urllib.request

from readability import Readability
import bs4
import sys
import mmap
import ssl
from multiprocessing import cpu_count
from multiprocessing import Pool


def init_outh(user_consumer_key):
  # ref: https://getpocket.com/developer/docs/authentication

  oauth_url = 'https://getpocket.com/v3/oauth/request'
  comsumer_key = user_consumer_key
  params = {'consumer_key': comsumer_key, 'redirect_uri': 'pocketapp1234:authorizationFinished'}
  oauth_response = requests.post(oauth_url, params=params)
  # print("oauth_resuponse url", oauth_response.url)

  # print(oauth_response.text)
  request_token = str(oauth_response.text).split('=')[-1]
  # print(request_token)  # for debug

  authorize_url = 'https://getpocket.com/v3/oauth/authorize'
  authorize_params = {'consumer_key': comsumer_key, 'code': request_token}
  authorize_response = requests.post(authorize_url, params=authorize_params)

  redirect_url = 'https://getpocket.com/auth/authorize'
  redirect_params = {'request_token': request_token, 'redirect_uri': authorize_response.url}
  redirect_response = requests.post(redirect_url, params=redirect_params)

  webbrowser.open(redirect_response.url, new=2)
  print("redirect_resuponse url", redirect_response.url)
  print("authorize url", authorize_response.url)

  r = requests.get(redirect_response.url)
  print("If you can't download access token, please open authorize url")


def get_pocket_data(access_token, state='all', count=-1):  # state: unread = only return unread items (default),archive = only return archived items,all = return both unread and archived items
  comsumer_key = '80658-bbacd7ab0a54d9473f023d87'
  access_token = access_token

  retrive_url = 'https://getpocket.com/v3/get'

  if count is -1:
    print("Dwonlod Full Item.....")
    params = {'consumer_key': comsumer_key, 'access_token': access_token, 'state': state, 'detailType': 'complete', 'sort': 'newest'}
  else:
    print("Dwonlod "+str(count)+" Item.....")
    params = {'consumer_key': comsumer_key, 'access_token': access_token, 'state': 'all', 'count': str(count)}

  response = requests.post(retrive_url, params=params)

  print("resuponse url", response.url)
  # write JSON data
  f = open('pocket.json', 'w')
  json.dump(response.json(), f, ensure_ascii=False)


def convert_json2csv():
  # ref: https://getpocket.com/developer/docs/v3/retrieve
  with open('pocket.json', 'r') as f:
    x = json.load(f)
    f.close()

  with open("tmp.csv", "w") as csv_file:
    # Write CSV Header, If you dont need that, remove this line
    # csv_file.write("item_id,resolved_id,given_url,favorite,status,resolved_title,favorite,status,is_article,has_image,has_video,html_body\n")

    for l in x['list']:
      try:
        row = [x['list'][l][i] for i in ["item_id", "resolved_id", "given_url", "favorite", "status", "resolved_title", "favorite", "status", "is_article", "has_image", "has_video"]]
      except KeyError:
        continue
      # print(",".join(row))
      csv_file.write(",".join(row) + "\n")


def mapcount(f):
  buf = mmap.mmap(f.fileno(), 0)
  lines = 0
  readline = buf.readline
  while readline():
    lines += 1
  return lines


def mapfunc(line, path_to_output):
  given_url = line.split(",")[2]
  try:
    htmlcode = urllib.request.urlopen(given_url).read().decode()
  except UnicodeDecodeError:
    print("UnicodeDecodeError,", given_url, file=sys.stderr)
    return
  except urllib.error.HTTPError:
    print("urllib.error.HTTPError,", given_url, file=sys.stderr)
    return
  except urllib.error.URLError:
    print("urllib.error.URLError,", given_url, file=sys.stderr)
    return
  except ConnectionResetError:
    print("ConnectionReseterror,", given_url, file=sys.stderr)
    return
  except ssl.CertificateError:
    print("ssl.CertificateError,", given_url, file=sys.stderr)
    return

  try:
    body_html = Readability(htmlcode, given_url).content
  except KeyError:
    print("KeyError,", given_url, file=sys.stderr)
    return
  body_removetag = bs4.BeautifulSoup(body_html, "lxml").text.replace('\n', '').replace(',', '')

  row = [given_url, body_removetag]
  # row = [given_url, body_html, body_removetag]
  # print(",".join(row))

  with open(path_to_output, "a") as output:
    output.write(",".join(row)+"\n")


def wrap_mapfunc(args):
  return mapfunc(*args)


def get_html_body():
  with open("tmp.csv", "r+") as csv_file:
    lc = mapcount(csv_file)
    i = 0

    wrap_args = [[i, "./htmlbody.csv"] for i in csv_file]
    p = Pool(cpu_count())
    p.map(wrap_mapfunc, wrap_args)


def main(access_token):
  parser = argparse.ArgumentParser()
  parser.add_argument('--init', type=str, action='store', metavar='consumer_key', nargs=1, default='None',
                      help='flag for initialize and get access token (default: None)')
  parser.add_argument('--update', '-u', action='store_const', const=True, default='None',
                      help='flag for update pocket data(default: None)')
  parser.add_argument('-c', '--count', metavar='number_of_items', type=int, nargs=1, default='-1',
                      help='number of items (default: all)')

  args = parser.parse_args()
  print(args)  # for debug

  if args.init is not 'None':
    print("Initialize app")
    init_outh(args.init)
  else:
    if args.update is True:
      get_pocket_data(access_token, state=all, count=args.count)
      convert_json2csv()
      get_html_body()
    else:
      convert_json2csv()
      get_html_body()


if __name__ == '__main__':
  access_token = '13716346-2175-3370-6e6a-f8511c'  # Write you own access token
  if access_token is None:
    print("access token is empty")
    quit

  main(access_token)
