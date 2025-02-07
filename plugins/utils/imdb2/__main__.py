""" search movies/tv series in imdb """

# Copyright (C) 2020-2022 by UsergeTeam@Github, < https://github.com/UsergeTeam >.
#
# This file is part of < https://github.com/UsergeTeam/Userge > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/UsergeTeam/Userge/blob/master/LICENSE >
#
# All rights reserved.

import json
import os
from apiclient.discovery import build
from urllib.parse import urlparse
import urllib.request
from pyrogram import enums
from pathlib import Path
import requests
from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from userge import userge, Message, config, pool
from .. import imdb
from pySmartDL import SmartDL

THUMB_PATH = str(Path().cwd())

TMDB_KEY = "5dae31e75ff0f7a0befc272d5deadd73"
api_key = "AIzaSyA3VaZAgxEaGOc0kZJ_Cc40thm4Nha3o_M"
youtube = build('youtube','v3',developerKey = api_key)



@userge.on_cmd("imdb", about={
    'header': "Scrap Movies & Tv Shows from IMDB",
    'description': "Get info about a Movie on IMDB.\n"
                   "[NOTE: To use a custom poster, download "
                   "the poster with name imdb_thumb.jpg]",
    'usage': "{tr}imdb [Movie Name]",
    'use inline': "@botusername imdb [Movie Name]"})
async def _imdb(message: Message):
    if not (imdb.API_ONE_URL or imdb.API_TWO_URL):
        return await message.err(
            "First set [these two vars](https://t.me/UsergePlugins/127) before using imdb",
            disable_web_page_preview=True
        )
    if 'tt' not in message.input_str:
        try:
            movie_name = message.input_str
            await message.edit(f"__searching IMDB for__ : `{movie_name}`")
            response = requests.get("https://www.omdbapi.com/?t="+movie_name.replace(' ', '%20') +'&apikey=fc5c20bd')
            srch_results = response.json()
            mov_imdb_id = srch_results["imdbID"]
            image_link, description = await get_movie_description(
                mov_imdb_id, config.MAX_MESSAGE_LENGTH
            )
        except (IndexError, json.JSONDecodeError, AttributeError):
            await message.edit("check spelling or movie not available on imdb")
            return
    if 'tt' in message.input_str:
        try:
            mov_imdb_id = message.input_str
            image_link, description = await get_movie_description(
                mov_imdb_id, config.MAX_MESSAGE_LENGTH
            )
        except (IndexError, json.JSONDecodeError, AttributeError):
            await message.edit("check spelling or movie not available on imdb")
            return
    if os.path.exists(THUMB_PATH):
        id = SmartDL(image_link, THUMB_PATH, progress_bar=False)
        id.start()
        await message.client.send_photo(
            chat_id=message.chat.id,
            photo=id.get_dest(),
            caption=description,
            parse_mode=enums.ParseMode.HTML
        )
        await message.delete()
        os.remove(id.get_dest())
    elif image_link is not None:
        id = SmartDL(image_link, THUMB_PATH, progress_bar=False)
        id.start()
        await message.client.send_photo(
            chat_id=message.chat.id,
            photo=id.get_dest(),
            caption=description,
            parse_mode=enums.ParseMode.HTML
        )
        await message.delete()
        os.remove(id.get_dest())
    else:
        await message.edit(
            description,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
        )

async def get_movie_description(imdb_id, max_length):
    response = await _get("https://imdb-api.com/en/API/Title/k_fl12vat7/"+imdb_id)
    response2 = await _get("https://imdb-api.com/en/API/YouTubeTrailer/k_fl12vat7/"+imdb_id)
    soup2 = json.loads(response2.text)
    soup = json.loads(response.text)
    try: 
        yt_link = soup2.get("videoUrl")
    except (IndexError, json.JSONDecodeError, AttributeError, TypeError):
        YT_NAME = soup.get('title') + " Official TRAILER" + " Hindi"
        request = youtube.search().list(q=YT_NAME,part='snippet',type='video',maxResults=1)
        YTFIND = request.execute()
        YTID = YTFIND['items'][0]["id"]["videoId"]
        yt_link = f"https://m.youtube.com/watch?v={YTID}"
        
    mov_link = f"https://www.imdb.com/title/{imdb_id}"
    mov_name = soup['title']
    image_link = soup['image']
    genres = soup["genres"]
    duration = soup["runtimeStr"]
    year = soup["year"]
    if year:
        pass  
    else:
        year = "not found"
    mov_rating = soup["imDbRating"]

    mov_country, mov_language = get_countries_and_languages(soup)
    director, writer, stars = get_credits_text(soup)
    story_line = soup["plot"]

    description = f"<b>Title</b><a href='{image_link}'>🎬</a>: <code>{mov_name}</code>"
    description += f"""
<b>>Genres: </b><code>{genres}</code>
<b>Rating⭐: </b><code>{mov_rating}</code>
<b>Country🗺: </b><code>{mov_country}</code>
<b>Language: </b><code>{mov_language}</code>
<b>Duration⏳: </b><code>{duration}</code>
<b>Cast Info🎗: </b>
<b>Director📽: </b><code>{director}</code>
<b>Writer📄: </b><code>{writer}</code>
<b>Stars🎭: </b><code>{stars}</code>
<b>Release Year📅: </b><code>{year}</code>
<b>Resolution : 480,720,1080</b>
<b>IMDB :</b> https://www.imdb.com/title/{imdb_id}
<b>YOUTUBE TRAILER 🎦 : </b> {yt_link}
<b>Story Line : </b><em>{story_line}</em>
<b>Available On : 👇👇👇👇 </b>"""

    povas = await search_jw(mov_name, imdb.WATCH_COUNTRY)
    if len(description + povas) > max_length:
        inc = max_length - len(description + povas)
        description = description[:inc - 3].strip() + "..."
    if povas != "":
        description += f"\n\n{povas}"
    return image_link, description


def get_countries_and_languages(soup):
    try:
        lg_text = soup["languages"]
        lg_text = lg_text if 'hindi' in lg_text.lower() else 'Hindi'
    except:
        lg_text = 'Hindi'
    try:
        ct_text = soup["countries"]
    except:
        ct_text = 'Not Found'
    return ct_text, lg_text


def get_credits_text(soup):
    try:
        director = soup["directors"]
    except:
        director = 'Not Found'
    try:
        writers = soup["writers"]
    except:
        writers = "Not Found"
    try: 
        actors = soup["stars"]
    except:
        actors= "Not Found"
    
    return director, writers, actors


@pool.run_in_thread
def _get(url: str, attempts: int = 0) -> requests.Response:
    while True:
        abc = requests.get(url)
        if attempts > 10:
            return abc
        if abc.status_code == 200:
            break
        attempts += 1
    return abc


if userge.has_bot:

    @userge.bot.on_callback_query(filters=filters.regex(pattern=r"imdb\((.+)\)"))
    async def imdb_callback(_, c_q: CallbackQuery):
        if c_q.from_user and c_q.from_user.id in config.OWNER_ID:
            imdb_id = str(c_q.matches[0].group(1))
            _, description = await get_movie_description(
                imdb_id, config.MAX_MESSAGE_LENGTH
            )
            await c_q.edit_message_text(
                text=description,
                disable_web_page_preview=False,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Open IMDB!",
                                url=f"https://imdb.com/title/{imdb_id}"
                            )
                        ]
                    ]
                )
            )
        else:
            await c_q.answer("This is not for you", show_alert=True)

    @userge.bot.on_inline_query(
        filters.create(
            lambda _, __, inline_query: (
                inline_query.query
                and inline_query.query.startswith("imdb ")
                and inline_query.from_user
                and inline_query.from_user.id in config.OWNER_ID
            ),
            # https://t.me/UserGeSpam/359404
            name="ImdbInlineFilter"
        ),
        group=-1
    )
    async def inline_fn(_, inline_query: InlineQuery):
        movie_name = inline_query.query.split("imdb ")[1].strip()
        search_results = await _get(imdb.API_ONE_URL.format(theuserge=movie_name))
        srch_results = json.loads(search_results.text)
        asroe = srch_results.get("d")
        oorse = []
        for sraeo in asroe:
            title = sraeo.get("l", "")
            description = sraeo.get("q", "")
            stars = sraeo.get("s", "")
            imdb_url = f"https://imdb.com/title/{sraeo.get('id')}"
            year = sraeo.get("yr", "").rstrip('-')
            image_url = sraeo.get("i").get("imageUrl")
            message_text = f"<a href='{image_url}'>🎬</a>"
            message_text += f"<a href='{imdb_url}'>{title} {year}</a>"
            oorse.append(
                InlineQueryResultArticle(
                    title=f" {title} {year}",
                    input_message_content=InputTextMessageContent(
                        message_text=message_text,
                        parse_mode=enums.ParseMode.HTML,
                        disable_web_page_preview=False
                    ),
                    url=imdb_url,
                    description=f" {description} | {stars}",
                    thumb_url=image_url,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="Get IMDB details",
                                    callback_data=f"imdb({sraeo.get('id')})"
                                )
                            ]
                        ]
                    )
                )
            )
        resfo = srch_results.get("q")
        await inline_query.answer(
            results=oorse,
            cache_time=300,
            is_gallery=False,
            is_personal=False,
            next_offset="",
            switch_pm_text=f"Found {len(oorse)} results for {resfo}",
            switch_pm_parameter="imdb"
        )
        inline_query.stop_propagation()


async def search_jw(movie_name: str, locale: str):
    m_t_ = ""
    if not imdb.API_THREE_URL:
        return m_t_
    response = await _get(imdb.API_THREE_URL.format(
        q=movie_name,
        L=locale
    ))
    soup = json.loads(response.text)
    items = soup["items"]
    try:
        for item in items:
            if movie_name.lower() == item.get("title", "").lower():
                offers = item.get("offers", [])
                t_m_ = []
                for offer in offers:
                    url = offer.get("urls").get("standard_web")
                    if url not in t_m_:
                        p_o = get_provider(url)
                        m_t_ += f"<a href='{url}'>{p_o}</a> | "
                    t_m_.append(url)
                if m_t_ != "":
                    m_t_ = m_t_[:-2].strip()
                break
        return m_t_
    except:
        return " "
        


def get_provider(url):

    def pretty(names):
        name = names[1]
        if names[0] == "play":
            name = "Google Play Movies"
        return name.title()

    netloc = urlparse(url).netloc
    return pretty(netloc.split('.'))
