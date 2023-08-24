#!/usr/bin/env python3

import argparse

from src.download_podcast import DownloadPodcast


parser = argparse.ArgumentParser(description='Download podcast from Ivoox.')
parser.add_argument(
    '-p',
    metavar='Podcast name',
    type=str,
    nargs='+',
    help='Alias for podcast name',
    required=True,
)
parser.add_argument(
    '-e',
    metavar='Episode name',
    type=str,
    nargs='+',
    help='Full or partial name of podcast episode, should be in quotation marks',
)
parser.add_argument(
    '-latest',
    action='store_true',
    help='Downloads the latest episode from provided podcast',
)
parser.add_argument(
    '-all',
    action='store_true',
    help='Downloads all episodes from provided podcast',
    default=False,
)

args = parser.parse_args()


def main(podcast_name, episode_name, latest_episode, all_episodes):
    if len(podcast_name) > 1:
        for single_podcast_name in podcast_name:
            dp = DownloadPodcast(single_podcast_name, None, True, False)
            dp.download_episode()
    elif podcast_name[0] == 'all':
        from src.config import Config
        config = Config()
        for podcast_name in config.get_podcast_keys():
            dp = DownloadPodcast(podcast_name, None, True, False)
            dp.download_episode()
    else:
        podcast_name = podcast_name[0] if podcast_name else None
        episode_name = episode_name[0] if episode_name else None
        dp = DownloadPodcast(podcast_name, episode_name, latest_episode, all_episodes)
        dp.download_episode()

main(args.p, args.e, args.latest, args.all)
