# -*- coding: utf-8 -*-
import datetime
import re
from os.path import basename

import disnake

from utils.music.converters import time_format, fix_characters, get_button_style
from utils.music.models import LavalinkPlayer
from utils.others import PlayerControls


class EmbedLinkSkin:

    __slots__ = ("name", "preview")

    def __init__(self):
        self.name = basename(__file__)[:-3]
        self.preview = "https://media.discordapp.net/attachments/554468640942981147/1101330475164893244/Discord_N1QhBDXtar.png"

    def setup_features(self, player: LavalinkPlayer):
        player.mini_queue_feature = False
        player.controller_mode = True
        player.auto_update = 0
        player.hint_rate = player.bot.config["HINT_RATE"]
        player.static = False

    def load(self, player: LavalinkPlayer) -> dict:

        data = {"content": None, "embeds": []}

        txt = ""

        if player.current_hint:
            txt += f"> -# `💡` **⠂Dica:** `{player.current_hint}`"

        if player.current.is_stream:
            duration_txt = f"\n> -# `🔴` **⠂Duração:** `Livestream`"
        else:
            duration_txt = (
                f"\n> -# `⏰` **⠂Duração:** `{time_format(player.current.duration)}`"
            )

        title = (
            f"`{fix_characters(player.current.title)}`"
            if not player.current.uri
            else f"[`{fix_characters(player.current.title, 40)}`]({player.current.uri})"
        )

        if player.paused:
            txt += f"\n> -# ⏸️ **⠂Em Pausa:** {title}{duration_txt}"

        else:
            txt += f"\n> -# ▶️ **⠂Now Playing:** {title}{duration_txt}"
            if not player.current.is_stream:
                txt += (
                    f" `[`<t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=player.current.duration - player.position)).timestamp())}:R>`]`"
                    if not player.paused
                    else ""
                )

        if q := len(player.queue):
            txt += f" `[Na fila: {q}]`"

        if not player.current.autoplay:
            txt += f" <@{player.current.requester}>\n"
        else:
            try:
                txt += f" [`[Música Recomendada]`](<{player.current.info['extra']['related']['uri']}>)"
            except:
                txt += " `[Música Recomendada]`"

        if player.command_log:

            log = re.sub(
                r"\[(.+)]\(.+\)", r"\1", player.command_log.replace("`", "")
            )  # remover links do command_log p/ evitar gerar mais de uma preview.

            txt += f"> -# {player.command_log_emoji} **⠂Última Interação:** {log}\n"

        data["content"] = txt

        data["components"] = [
            disnake.ui.Button(
                emoji="⏯️",
                custom_id=PlayerControls.pause_resume,
                style=get_button_style(player.paused),
            ),
            disnake.ui.Button(emoji="⏮️", custom_id=PlayerControls.back),
            disnake.ui.Button(emoji="⏹️", custom_id=PlayerControls.stop),
            disnake.ui.Button(emoji="⏭️", custom_id=PlayerControls.skip),
            disnake.ui.Button(
                emoji="<:music_queue:703761160679194734>",
                custom_id=PlayerControls.queue,
                disabled=not (player.queue or player.queue_autoplay),
            ),
            disnake.ui.Select(
                placeholder="More options:",
                custom_id="musicplayer_dropdown_inter",
                min_values=0,
                max_values=1,
                options=[
                    disnake.SelectOption(
                        label="Add music",
                        emoji="<:add_music:588172015760965654>",
                        value=PlayerControls.add_song,
                        description="Add a song/playlist to the queue./playlist na fila.",
                    ),
                    disnake.SelectOption(
                        label="Add favorite to queue",
                        emoji="⭐",
                        value=PlayerControls.enqueue_fav,
                        description="Add one of your favorites to the queue.",
                    ),
                    disnake.SelectOption(
                        label="Add to your favorites",
                        emoji="💗",
                        value=PlayerControls.add_favorite,
                        description="Add the current song to your favorites.",
                    ),
                    disnake.SelectOption(
                        label="Play from beginning",
                        emoji="⏪",
                        value=PlayerControls.seek_to_start,
                        description="Return the current song's tempo to the beginning.",
                    ),
                    disnake.SelectOption(
                        label=f"Volume: {player.volume}%",
                        emoji="🔊",
                        value=PlayerControls.volume,
                        description="Adjust volume.",
                    ),
                    disnake.SelectOption(
                        label="Mix",
                        emoji="🔀",
                        value=PlayerControls.shuffle,
                        description="Mix the songs in the queue.",
                    ),
                    disnake.SelectOption(
                        label="Re-add",
                        emoji="🎶",
                        value=PlayerControls.readd,
                        description="Re-add re-add played songs back to the queue.",
                    ),
                    disnake.SelectOption(
                        label="Repetition",
                        emoji="🔁",
                        value=PlayerControls.loop_mode,
                        description="Enable/Disable song/queue repetition.",
                    ),
                    disnake.SelectOption(
                        label=("Disable" if player.nightcore else "Activate")
                        + " the nightcore effect",
                        emoji="🇳",
                        value=PlayerControls.nightcore,
                        description="Efeito que aumenta velocidade e tom da música.",
                    ),
                    disnake.SelectOption(
                        label=("Disable" if player.autoplay else "Activate")
                        + " autoplay",
                        emoji="🔄",
                        value=PlayerControls.autoplay,
                        description="Sistema de adição de música automática quando a fila estiver vazia.",
                    ),
                    disnake.SelectOption(
                        label=("Disable" if player.restrict_mode else "Activate")
                        + " restricted mode",
                        emoji="🔐",
                        value=PlayerControls.restrict_mode,
                        description="Only DJ's/Staff's can use restricted commands.",
                    ),
                ],
            ),
        ]

        if player.current.ytid and player.node.lyric_support:
            data["components"][5].options.append(
                disnake.SelectOption(
                    label="Visualizar letras",
                    emoji="📃",
                    value=PlayerControls.lyrics,
                    description="Obter letra da música atual.",
                )
            )

        if isinstance(player.last_channel, disnake.VoiceChannel):
            data["components"][5].options.append(
                disnake.SelectOption(
                    label="Status automático",
                    emoji="📢",
                    value=PlayerControls.set_voice_status,
                    description="Configurar o status automático do voice channel.",
                )
            )

        if not player.static and not player.has_thread:
            data["components"][5].options.append(
                disnake.SelectOption(
                    label="Song-Request Thread",
                    emoji="💬",
                    value=PlayerControls.song_request_thread,
                    description="Criar uma thread/conversa temporária para pedir músicas usando apenas o nome/link.",
                )
            )

        return data


def load():
    return EmbedLinkSkin()
