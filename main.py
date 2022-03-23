"""
Script to archive all Slack messages
You have to create a Slack Bot and invite him to private channels.
View https://github.com/docmarionum1/slack-archive-bot for how to configure your account.
Then provide the bot token to this script with the list of channels.
"""


import argparse
from datetime import datetime
from http.client import IncompleteRead
import json
import time
from typing import Optional
import os

from slack_sdk.web.client import WebClient
from slack_sdk.errors import SlackApiError


class SlackExporter:
    def __init__(self, token: str) -> None:
        self.client = WebClient(token=token)
        self.folder_root = self._generate_backup_folder_name()
        self.message_per_file = 1000
        try:
            os.makedirs(self.folder_root)
        except FileExistsError:
            print(f"remove folder {self.folder_root} before start script")
            exit(1)

    def _generate_backup_folder_name(self) -> str:
        now = datetime.now()
        postfix = now.strftime("%Y-%m-%d")
        return f"backup_{postfix}"

    def _save_to_file(
        self, filename: str, body: object, foldername: Optional[str] = None
    ) -> None:
        if foldername:
            os.makedirs(
                os.path.join(self.folder_root, foldername), exist_ok=True
            )
            filename = os.path.join(self.folder_root, foldername, filename)
        else:
            filename = os.path.join(self.folder_root, filename)

        with open(filename, "w") as outfile:
            json.dump(body, outfile)

    def _conversations_with_reconnect(
        self, channel_id: str, cursor: str, sleep_seconds: int, limit: int
    ):
        if sleep_seconds > 20:
            raise ValueError("too many reconnects")
        try:
            if cursor:
                return self.client.conversations_history(
                    channel=channel_id, cursor=cursor, limit=limit
                )
            else:
                return self.client.conversations_history(
                    channel=channel_id, limit=limit
                )
        except:
            time.sleep(sleep_seconds)
            return self._conversations_with_reconnect(
                channel_id, cursor, sleep_seconds + 1, limit
            )

    def _backup_channel(self, channel_name: str, channel_id: str) -> None:
        try:
            print("Getting messages from", channel_name)
            result = self._conversations_with_reconnect(
                channel_id=channel_id, cursor="", sleep_seconds=1, limit=500
            )
            iter_counter = 1
            message_counter = len(result["messages"])
            all_message = []
            all_message += result["messages"]
            while result["has_more"]:
                if message_counter:
                    print(f"\tRead {message_counter}\tGetting more...")
                result = self._conversations_with_reconnect(
                    channel_id=channel_id,
                    cursor=result["response_metadata"]["next_cursor"],
                    sleep_seconds=1,
                    limit=500,
                )
                message_counter += len(result["messages"])
                all_message += result["messages"]
                if len(all_message) >= self.message_per_file:
                    iter_counter += 1
                    self._save_to_file(
                        f"{iter_counter}.json",
                        all_message,
                        foldername=channel_name,
                    )
                    all_message = []
            if len(all_message) > 0:
                iter_counter += 1
                self._save_to_file(
                    f"{iter_counter}.json",
                    all_message,
                    foldername=channel_name,
                )
            print(
                f"  We have downloaded {message_counter} messages from {channel_name}."
            )
        except SlackApiError as e:
            print("Error using conversation: {}".format(e))

    def get_users(self, to_file: Optional[bool] = True) -> dict:
        result = self.client.users_list()
        users = result["members"]
        filename = "users.json"
        if to_file:
            self._save_to_file(filename, users)
        users_store = {elm["id"]: elm["name"] for elm in users}
        return users_store

    def get_list_channels(self, to_file: Optional[bool] = True) -> dict:
        all_channel_types = ["public_channel", "private_channel", "mpim"]
        result = self.client.conversations_list(types=all_channel_types)
        if to_file:
            self._save_to_file("channels.json", result["channels"])
        channels = {elm["name"]: elm["id"] for elm in result["channels"]}
        return channels

    def get_list_dm_channels(
        self, users_store: dict, to_file: Optional[bool] = True
    ) -> dict:
        result = self.client.conversations_list(types="im")
        channels = result["channels"]
        channel_store = {}
        dms = []
        for elm in channels:
            ch_name = users_store.get(elm["user"])
            if ch_name is None:
                continue
            channel_store[ch_name] = elm["id"]
            dm = {"id": ch_name, "members": [elm["user"]]}
            dms.append(dm)
        if to_file:
            self._save_to_file("dms.json", dms)

        return channel_store

    def backup(self, only_dm: bool):
        if not only_dm:
            channels = self.get_list_channels()
            for chan_name, chan_id in channels.items():
                self._backup_channel(chan_name, chan_id)

        users_store = self.get_users()
        dms = self.get_list_dm_channels(users_store)
        for chan_name, chan_id in dms.items():
            self._backup_channel(chan_name, chan_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SlackExporter")
    parser.add_argument(
        "-t",
        "--token",
        help="Slack oauth token: Example: xoxp-****",
        required=True,
    )
    parser.add_argument(
        "-dm",
        "--only_dm",
        help="If set 1 exports only direct messages, otherwise exports all",
        default=False,
    )
    args = vars(parser.parse_args())
    slack_exporter = SlackExporter(token=args["token"])
    slack_exporter.backup(only_dm=args["only_dm"])
