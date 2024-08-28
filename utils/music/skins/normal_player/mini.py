# -*- coding: utf-8 -*-
import itertools
from os.path import basename

import disnake

from utils.music.converters import (
    time_format,
    fix_characters,
    get_button_style,
    music_source_image,
)
from utils.music.models import LavalinkPlayer
from utils.others import PlayerControls


class MiniSkin:

    __slots__ = ("name", "preview")

    def __init__(self):
        self.name = basename(__file__)[:-3]
        self.preview = "https://i.ibb.co/ZBTbdvT/mini.png"

    def setup_features(self, player: LavalinkPlayer):
        player.mini_queue_feature = True
        player.controller_mode = True
        player.auto_update = 0
        player.hint_rate = player.bot.config["HINT_RATE"]
        player.static = False

    def load(self, player: LavalinkPlayer) -> dict:

        data = {
            "content": None,
            "embeds": [],
        }

        embed_color = player.bot.get_color(player.guild.me)

        embed = disnake.Embed(
            color=embed_color,
            description=f"-# [`{player.current.single_title}`]({player.current.uri or player.current.search_uri})",
        )
        embed_queue = None
        queue_size = len(player.queue)

        if not player.paused:
            embed.set_author(
                name="Now Playing:",
                icon_url=music_source_image(player.current.info["sourceName"]),
            )

        else:
            embed.set_author(
                name="Em Pausa:",
                icon_url="https://cdn.discordapp.com/attachments/480195401543188483/896013933197013002/pause.png",
            )

        if player.current.track_loops:
            embed.description += f" `[🔂 {player.current.track_loops}]`"

        elif player.loop:
            if player.loop == "current":
                embed.description += " `[🔂 música atual]`"
            else:
                embed.description += " `[🔁 fila]`"

        if not player.current.autoplay:
            embed.description += f" `[`<@{player.current.requester}>`]`"
        else:
            try:
                embed.description += f" [`[Recomendada]`]({player.current.info['extra']['related']['uri']})"
            except:
                embed.description += "` [Recomendada]`"

        duration = (
            "🔴 Livestream"
            if player.current.is_stream
            else time_format(player.current.duration)
        )

        embed.add_field(
            name="⏰ **⠂Duração:**", value=f"```ansi\n[34;1m{duration}[0m\n```"
        )
        embed.add_field(
            name="💠 **⠂Uploader/Artista:**",
            value=f"```ansi\n[34;1m{fix_characters(player.current.author, 18)}[0m\n```",
        )

        if player.command_log:
            embed.add_field(
                name=f"{player.command_log_emoji} **⠂Última Interação:**",
                value=f"{player.command_log}",
                inline=False,
            )

        if queue_size:

            embed.description += f" `({queue_size})`"

            if player.mini_queue_enabled:
                embed_queue = disnake.Embed(
                    color=embed_color,
                    description="\n".join(
                        f"`{(n + 1):02}) [{time_format(t.duration) if not t.is_stream else '🔴 Livestream'}]` [`{fix_characters(t.title, 38)}`]({t.uri})"
                        for n, t in (enumerate(itertools.islice(player.queue, 5)))
                    ),
                )
                embed_queue.set_image(
                    url="https://cdn.discordapp.com/attachments/554468640942981147/1082887587770937455/rainbow_bar2.gif"
                )

        embed.set_thumbnail(url=player.current.thumb)
        embed.set_image(
            url="https://cdn.discordapp.com/attachments/554468640942981147/1082887587770937455/rainbow_bar2.gif"
        )

        if player.current_hint:
            embed.set_footer(text=f"💡 Dica: {player.current_hint}")

        data["embeds"] = [embed_queue, embed] if embed_queue else [embed]

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

        if player.mini_queue_feature:
            data["components"][5].options.append(
                disnake.SelectOption(
                    label="Mini-fila do player",
                    emoji="<:music_queue:703761160679194734>",
                    value=PlayerControls.miniqueue,
                    description="Activate/Disable a mini-fila do player.",
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
    return MiniSkin()
