# -*- coding: utf-8 -*-
import datetime
import itertools
from os.path import basename

import disnake

from utils.music.converters import time_format, fix_characters, get_button_style
from utils.music.models import LavalinkPlayer
from utils.others import PlayerControls


class EmbedLinkStaticSkin:
    __slots__ = ("name", "preview")

    def __init__(self):
        self.name = basename(__file__)[:-3] + "_static"
        self.preview = "https://media.discordapp.net/attachments/554468640942981147/1101328287466274816/image.png"

    def setup_features(self, player: LavalinkPlayer):
        player.mini_queue_feature = False
        player.controller_mode = True
        player.auto_update = 0
        player.hint_rate = player.bot.config["HINT_RATE"]
        player.static = True

    def load(self, player: LavalinkPlayer) -> dict:

        txt = ""

        if player.current_hint:
            txt += f"\n> -# `💡 Dica: {player.current_hint}`\n"

        if player.current.is_stream:
            duration_txt = f"\n> -# 🔴 **⠂Duração:** `Livestream`"
        else:
            duration_txt = (
                f"\n> -# ⏰ **⠂Duração:** `{time_format(player.current.duration)}`"
            )

        title = (
            fix_characters(player.current.title)
            if not player.current.uri
            else f"[{fix_characters(player.current.title)}]({player.current.uri})"
        )

        if player.paused:
            txt += f"\n> ### ⏸️ ⠂Em Pausa: {title}\n{duration_txt}"

        else:
            txt += f"\n> ### ▶️ ⠂Now Playing: {title}\n{duration_txt}"
            if not player.current.is_stream and not player.paused:
                txt += f" `[`<t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=player.current.duration - player.position)).timestamp())}:R>`]`"

        vc_txt = ""

        if not player.current.autoplay:
            txt += f"\n> -# ✋ **⠂Pedido por:** <@{player.current.requester}>\n"
        else:
            try:
                mode = f" [`Música Recomendada`](<{player.current.info['extra']['related']['uri']}>)"
            except:
                mode = "`Música Recomendada`"
            txt += f"\n> -# 👍 **⠂Adicionado via:** {mode}\n"

        try:
            vc_txt += (
                f"> -# *️⃣ **⠂Voice channel:** {player.guild.me.voice.channel.mention}\n"
            )
        except AttributeError:
            pass

        if player.current.playlist_name:
            txt += f"> -# 📑 **⠂Playlist:** [`{fix_characters(player.current.playlist_name) or 'Visualizar'}`](<{player.current.playlist_url}>)\n"

        if player.current.track_loops:
            txt += (
                f"> -# 🔂 **⠂Repetições restantes:** `{player.current.track_loops}`\n"
            )

        elif player.loop:
            if player.loop == "current":
                txt += "> -# 🔂 **⠂Repetition:** `música atual`\n"
            else:
                txt += "> -# 🔁 **⠂Repetition:** `fila`\n"

        txt += vc_txt

        if player.command_log:

            txt += f"> -# {player.command_log_emoji} **⠂Última Interação:** {player.command_log}\n"

        if qsize := len(player.queue):

            qtext = "> -# **Músicas na lista"

            if qsize > 4:
                qtext += f" [{qsize}]:"

            qtext += "**\n" + "\n".join(
                f"> -# `{(n + 1)} [{time_format(t.duration) if not t.is_stream else '🔴 stream'}]` [`{fix_characters(t.title, 30)}`](<{t.uri}>)"
                for n, t in enumerate(itertools.islice(player.queue, 4))
            )

            txt = f"{qtext}\n{txt}"

        elif len(player.queue_autoplay):

            txt = (
                "**Próximas músicas recomendadas:**\n"
                + "\n".join(
                    f"-# `{(n + 1)} [{time_format(t.duration) if not t.is_stream else '🔴 stream'}]` [`{fix_characters(t.title, 30)}`](<{t.uri}>)"
                    for n, t in enumerate(itertools.islice(player.queue_autoplay, 4))
                )
                + f"\n{txt}"
            )

        data = {
            "content": txt,
            "embeds": [],
            "components": [
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
            ],
        }

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
    return EmbedLinkStaticSkin()
