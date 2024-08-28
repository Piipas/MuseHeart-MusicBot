# -*- coding: utf-8 -*-
import datetime
from os.path import basename

import disnake

from utils.music.converters import (
    fix_characters,
    time_format,
    get_button_style,
    music_source_image,
)
from utils.music.models import LavalinkPlayer
from utils.others import ProgressBar, PlayerControls


class DefaultProgressbarStaticSkin:

    __slots__ = ("name", "preview")

    def __init__(self):
        self.name = basename(__file__)[:-3] + "_static"
        self.preview = "https://i.ibb.co/WtyW264/progressbar-static-skin.png"

    def setup_features(self, player: LavalinkPlayer):
        player.mini_queue_feature = False
        player.controller_mode = True
        player.auto_update = 15
        player.hint_rate = player.bot.config["HINT_RATE"]
        player.static = True

    def load(self, player: LavalinkPlayer) -> dict:

        data = {"content": None, "embeds": []}

        embed = disnake.Embed(color=player.bot.get_color(player.guild.me))
        embed_queue = None

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

        if player.current_hint:
            embed.set_footer(text=f"💡 Dica: {player.current_hint}")
        else:
            embed.set_footer(
                text=str(player), icon_url="https://i.ibb.co/QXtk5VB/neon-circle.gif"
            )

        if player.current.is_stream:
            duration = "```ansi\n🔴 [31;1m Livestream[0m```"
        else:

            progress = ProgressBar(
                player.position, player.current.duration, bar_count=17
            )

            duration = (
                f"```ansi\n[34;1m[{time_format(player.position)}] {('='*progress.start)}[0m🔴️[36;1m{'-'*progress.end} "
                f"[{time_format(player.current.duration)}][0m```\n"
            )

        vc_txt = ""
        queue_img = ""

        txt = (
            f"-# [`{player.current.single_title}`]({player.current.uri or player.current.search_uri})\n\n"
            f"> -# 💠 **⠂Por:** {player.current.authors_md}"
        )

        if not player.current.autoplay:
            txt += f"\n> -# ✋ **⠂Pedido por:** <@{player.current.requester}>"
        else:
            try:
                mode = f" [`Recomendação`]({player.current.info['extra']['related']['uri']})"
            except:
                mode = "`Recomendação`"
            txt += f"\n> -# 👍 **⠂Adicionado via:** {mode}"

        try:
            vc_txt = (
                f"\n> -# *️⃣ **⠂Voice channel:** {player.guild.me.voice.channel.mention}"
            )
        except AttributeError:
            pass

        if player.current.track_loops:
            txt += f"\n> -# 🔂 **⠂Repetições restante:** `{player.current.track_loops}`"

        if player.loop:
            if player.loop == "current":
                e = "🔂"
                m = "Música atual"
            else:
                e = "🔁"
                m = "Fila"
            txt += f"\n> -# {e} **⠂Modo de repetition:** `{m}`"

        if player.current.album_name:
            txt += f"\n> -# 💽 **⠂Álbum:** [`{fix_characters(player.current.album_name, limit=20)}`]({player.current.album_url})"

        if player.current.playlist_name:
            txt += f"\n> -# 📑 **⠂Playlist:** [`{fix_characters(player.current.playlist_name, limit=20)}`]({player.current.playlist_url})"

        if player.keep_connected:
            txt += "\n> -# ♾️ **⠂Modo 24/7:** `Ativado`"

        txt += f"{vc_txt}\n"

        if player.command_log:
            txt += f"> -# {player.command_log_emoji} **⠂Última Interação:** {player.command_log}\n"

        txt += duration

        if qlenght := len(player.queue):

            queue_txt = ""

            has_stream = False

            current_time = disnake.utils.utcnow() - datetime.timedelta(
                milliseconds=player.position + player.current.duration
            )

            queue_duration = 0

            for n, t in enumerate(player.queue):

                if t.is_stream:
                    has_stream = True

                elif n != 0:
                    queue_duration += t.duration

                if n > 7:
                    if has_stream:
                        break
                    continue

                if has_stream:
                    duration = (
                        time_format(t.duration) if not t.is_stream else "🔴 Ao vivo"
                    )

                    queue_txt += (
                        f"`┌ {n + 1})` [`{fix_characters(t.title, limit=34)}`]({t.uri})\n"
                        f"`└ ⏲️ {duration}`"
                        + (f" - `Repetições: {t.track_loops}`" if t.track_loops else "")
                        + f" **|** `✋` <@{t.requester}>\n"
                    )

                else:
                    duration = f"<t:{int((current_time + datetime.timedelta(milliseconds=queue_duration)).timestamp())}:R>"

                    queue_txt += (
                        f"`┌ {n + 1})` [`{fix_characters(t.title, limit=34)}`]({t.uri})\n"
                        f"`└ ⏲️` {duration}"
                        + (f" - `Repetições: {t.track_loops}`" if t.track_loops else "")
                        + f" **|** `✋` <@{t.requester}>\n"
                    )

            embed_queue = disnake.Embed(
                title=f"Músicas na fila: {qlenght}",
                color=player.bot.get_color(player.guild.me),
                description=f"\n{queue_txt}",
            )

            if (
                not has_stream
                and not player.loop
                and not player.keep_connected
                and not player.paused
                and not player.current.is_stream
            ):
                embed_queue.description += f"\n`[ ⌛ As músicas acabam` <t:{int((current_time + datetime.timedelta(milliseconds=queue_duration + player.current.duration)).timestamp())}:R> `⌛ ]`"

            embed_queue.set_image(url=queue_img)

        elif len(player.queue_autoplay):

            queue_txt = ""

            has_stream = False

            current_time = disnake.utils.utcnow() - datetime.timedelta(
                milliseconds=player.position + player.current.duration
            )

            queue_duration = 0

            for n, t in enumerate(player.queue_autoplay):

                if t.is_stream:
                    has_stream = True

                elif n != 0:
                    queue_duration += t.duration

                if n > 7:
                    if has_stream:
                        break
                    continue

                if has_stream:
                    duration = (
                        time_format(t.duration) if not t.is_stream else "🔴 Ao vivo"
                    )

                    queue_txt += (
                        f"-# `┌ {n+1})` [`{fix_characters(t.title, limit=34)}`]({t.uri})\n"
                        f"-# `└ ⏲️ {duration}`"
                        + (f" - `Repetições: {t.track_loops}`" if t.track_loops else "")
                        + f" **|** `👍⠂Recomendada`\n"
                    )

                else:
                    duration = f"<t:{int((current_time + datetime.timedelta(milliseconds=queue_duration)).timestamp())}:R>"

                    queue_txt += (
                        f"-# `┌ {n+1})` [`{fix_characters(t.title, limit=34)}`]({t.uri})\n"
                        f"-# `└ ⏲️` {duration}"
                        + (f" - `Repetições: {t.track_loops}`" if t.track_loops else "")
                        + f" **|** `👍⠂Recomendada`\n"
                    )

            embed_queue = disnake.Embed(
                title="Próximas músicas recomendadas:",
                color=player.bot.get_color(player.guild.me),
                description=f"\n{queue_txt}",
            )

            embed_queue.set_image(url=queue_img)

        embed.description = txt
        embed.set_image(url=player.current.thumb)

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
    return DefaultProgressbarStaticSkin()
