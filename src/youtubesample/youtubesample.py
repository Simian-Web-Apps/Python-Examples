import json
import os

import isodate
import pandas as pd
import plotly.express as px
import pycountry
import requests
from deep_translator import GoogleTranslator
from googleapiclient.discovery import build
from plotly.subplots import make_subplots

from simian.gui import Form, component, utils

if __name__ == "__main__":
    from simian.local import Uiformio

    Uiformio("youtubesample", window_title="YouTube Trending Videos", debug=True)


def gui_init(meta_data: dict) -> dict:
    # Get application data containing secrets and configurables (local mode).
    get_application_data(meta_data)

    # Create the form and load the json builder into it.
    Form.componentInitializer(app_pic_hello_world=init_app_toplevel_pic)
    #    Form.componentInitializer(selection_country=init_selection_country)
    Form.componentInitializer(
        selection_country=get_init_selection_country(
            meta_data["application_data"]["youtube_developer_key"]
        )
    )
    Form.componentInitializer(
        selection_category=get_init_selection_category(
            meta_data["application_data"]["youtube_developer_key"]
        )
    )
    # Form.componentInitializer(selection_tag_count=init_selection_tag_count)
    # Form.componentInitializer(selection_translation=init_selection_translation)
    Form.componentInitializer(video_list=init_video_list)
    Form.componentInitializer(iframe=init_video_iframe)
    Form.componentInitializer(showVideo=init_show_video)

    form = Form(from_file=__file__)
    examples_url = "https://github.com/Simian-Web-Apps/Python-Examples/"
    payload = {
        "form": form,
        "navbar": {
            "title": (
                f'<a class="text-white" href="{examples_url}" target="_blank">'
                '<i class="fa fa-github"></i></a>&nbsp;YouTube Trending Videos'
            )
        },
        "showChanged": False,
    }

    # And do the initial query
    payload["followUp"] = "process"

    return payload


def init_video_list(comp: component.Html):
    comp.sanitizeOptions = {"USE_PROFILES": {"html": True}, "ADD_ATTR": ["target"]}


def init_video_iframe(comp: component.Html):
    comp.sanitizeOptions = {
        "USE_PROFILES": {"html": True},
        "ADD_TAGS": ["iframe"],
        "ADD_ATTR": ["src", "allow", "allowFullScreen", "loading"],
    }


def init_show_video(comp: component.Toggle):
    comp.defaultValue = False


def get_init_selection_country(youtube_developer_key: str):
    def init_selection_country(comp: component.Select):
        # Add trigger-happy event handler to this component.
        # Populate component with list of ISO 3166 Country Codes, using the pycountry module.
        # comp.properties = {"debounceTime": 1000, "triggerHappy": "process"}
        url = f"https://www.googleapis.com/youtube/v3/i18nRegions?part=snippet&hl=en_US&key={youtube_developer_key}"
        response = requests.get(url)
        datajson = response.json()
        labels = [item["snippet"]["name"] for item in datajson["items"]]
        values = [item["snippet"]["gl"] for item in datajson["items"]]
        comp.setValues(labels, values, "NL")

    return init_selection_country


def get_init_selection_category(youtube_developer_key: str):
    def init_selection_category(comp: component.Select):
        # Add trigger-happy event handler to this component.
        # Populate component with list of categories, fetched from YouTube API.
        # comp.properties = {"debounceTime": 1000, "triggerHappy": "process"}
        url = f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode=NL&key={youtube_developer_key}"
        response = requests.get(url)
        datajson = response.json()
        labels = [item["snippet"]["title"] for item in datajson["items"]]
        values = [item["id"] for item in datajson["items"]]
        comp.setValues(labels, values, "28")

    return init_selection_category


# def init_selection_tag_count(comp: component.Slider):
# Add trigger-happy event handler to this component.
# comp.properties = {"debounceTime": 1000, "triggerHappy": "process"}


# def init_selection_translation(comp: component.Toggle):
# Add trigger-happy event handler to this component.
# comp.properties = {"debounceTime": 1000, "triggerHappy": "process"}


def init_app_toplevel_pic(comp: component.HtmlElement):
    # Voeg depictie met titel toe in de linker bovenhoek.
    comp.setLocalImage(
        os.path.join(os.path.dirname(__file__), "app_pic.png"), scale_to_parent_width=True
    )
    comp.customClass = "px-5"


def get_application_data(meta_data: dict):
    # In local mode, add application_data from file.
    # In deployed mode, this informtion is set in App config in Simian Portal.
    if meta_data["mode"] == "local":
        application_data_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "local_application_data.json"
        )

        if os.path.isfile(application_data_file):
            with open(application_data_file) as f:
                meta_data["application_data"] = json.load(f)
        else:
            raise Exception(
                'No file "local_application_data.json" exists. Please copy or remame '
                '"local_application_data.json.sample" to "local_application_data.json", and '
                "edit to set your YouTube API key from https://console.cloud.google.com/apis/library."
            )


def gui_event(meta_data: dict, payload: dict) -> dict:
    # Get application data containing secrets and configurables (local mode).
    get_application_data(meta_data)
    callback = utils.getEventFunction(meta_data, payload)

    return callback(meta_data, payload)


def process(meta_data: dict, payload: dict) -> dict:
    nr_to_display = 10

    # Fetch trending YouTube videos, based on user selection.
    selection_country, _ = utils.getSubmissionData(payload, "selection_country")
    selection_category, _ = utils.getSubmissionData(payload, "selection_category")
    selection_tag_count, _ = utils.getSubmissionData(payload, "selection_tag_count")
    selection_translation, _ = utils.getSubmissionData(payload, "selection_translation")
    plot_obj_video_stats, _ = utils.getSubmissionData(payload, "plot_video_stats")

    # Initialize YouTube connection and create results plots.
    youtube = build(
        "youtube", "v3", developerKey=meta_data["application_data"]["youtube_developer_key"]
    )

    try:
        video_df = extractYouTubeData(youtube, selection_country, selection_category)
        base_message = "Results found."
        tags = []
    except:
        video_df = get_empty_video_df()
        payload = utils.addAlert(payload, "No results found for this selection.", "danger")
    #        return payload

    if len(video_df) > 0:
        video_df_top = video_df.iloc[:nr_to_display]
        if selection_translation:
            try:
                video_title_array = [video for video in video_df_top["snippet.title"]]
                video_title_array = GoogleTranslator(source="auto", target="en").translate_batch(
                    video_title_array
                )
                base_message += " Titles translated to English."
            except:
                base_message += " Title translation failed."
        else:
            video_title_array = [video for video in video_df_top["snippet.title"]]
            base_message += " No title translation applied."

        for items in video_df_top["snippet.tags"]:
            if type(items) != float:
                if selection_translation:
                    # tags.extend(GoogleTranslator(source="auto", target="en").translate_batch(items))
                    tags.extend(items)
                else:
                    tags.extend(items)

        video_link_array = [
            "https://www.youtube.com/watch?v=" + video for video in video_df_top["id"]
        ]
        video_thumbnail_array = [
            "https://img.youtube.com/vi/" + video + "/default.jpg" for video in video_df_top["id"]
        ]
        video_embed_array = [
            "https://www.youtube.com/embed/" + video for video in video_df_top["id"]
        ]
        full_references = [
            f'<a href="{x[0]}/" target="_blank"><img src="{x[2]}" title="{x[1]}"></a>'
            for x in zip(video_link_array, video_title_array, video_thumbnail_array)
        ]
        full_references_html = (
            '<div class="d-flex flex-row flex-wrap">'
            + "".join(['<div class="p-2 mx-auto">' + item + "</div>" for item in full_references])
            + "</div>"
        )
        video_embed_array = [
            "https://www.youtube.com/embed/" + video for video in video_df_top["id"]
        ]
        full_embed_html = (
            '<div class="d-flex flex-row flex-wrap">'
            + "".join(
                [
                    "<iframe"
                    + ' class="p-2 mx-auto"'
                    + ' loading="lazy"'
                    + f' src="{item[0]}"'
                    + f' title="{item[1]}"'
                    + ' loading="lazy"'
                    + ' allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"'
                    + " allowFullScreen></iframe>"
                    for item in zip(video_embed_array, video_title_array)
                ]
            )
            + "</div>"
        )

    else:
        full_references_html = ""
        base_message = ""
        tags = []

    plot_obj_video_stats = plotVideoStats(video_df, plot_obj_video_stats, selection_tag_count, tags)

    payload, _ = utils.setSubmissionData(payload, "plot_video_stats", plot_obj_video_stats)
    payload, _ = utils.setSubmissionData(payload, "video_list", full_references_html)
    payload, _ = utils.setSubmissionData(payload, "appmessages", base_message)
    payload, _ = utils.setSubmissionData(
        payload,
        "iframe",
        full_embed_html,
    )

    return payload


def extractYouTubeData(youtube, selection_country, selection_category):
    # Extract YouTube data, using API key.
    video_request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        chart="mostPopular",
        regionCode=selection_country,
        videoCategoryId=str(selection_category),
        maxResults=25,
    )

    response = video_request.execute()
    video_df = pd.json_normalize(response["items"])

    return video_df


def plotVideoStats(video_df, plot_obj_duration_vs_likes, topN, tags):
    # Create duration/likes results plot.
    fig = make_subplots(
        rows=3,
        cols=2,
        specs=[[{}, {}], [{}, {}], [{"colspan": 2}, None]],
        subplot_titles=(
            "Views vs. likes",
            "Duration vs. likes",
            "Comments vs. likes",
            "Duration vs. comments",
            "Top tags vs. frequency",
        ),
    )

    video_df["contentDetails.duration"] = video_df["contentDetails.duration"].astype(str)
    video_df["duration"] = video_df["contentDetails.duration"].apply(
        lambda x: isodate.parse_duration(x).total_seconds()
    )

    fig.add_scatter(
        x=video_df["statistics.viewCount"],
        y=video_df["statistics.likeCount"],
        mode="markers",
        row=1,
        col=1,
        hovertext=video_df["snippet.title"],
        hoverinfo="text",
    )
    fig.add_scatter(
        x=video_df["duration"],
        y=video_df["statistics.likeCount"],
        mode="markers",
        row=1,
        col=2,
        hovertext=video_df["snippet.title"],
        hoverinfo="text",
    )
    fig.add_scatter(
        x=video_df["statistics.commentCount"],
        y=video_df["statistics.likeCount"],
        mode="markers",
        row=2,
        col=1,
        hovertext=video_df["snippet.title"],
        hoverinfo="text",
    )
    fig.add_scatter(
        x=video_df["duration"],
        y=video_df["statistics.commentCount"],
        mode="markers",
        row=2,
        col=2,
        hovertext=video_df["snippet.title"],
        hoverinfo="text",
    )

    tags_df = pd.DataFrame(tags)
    tags_freq_df = (
        tags_df.value_counts().iloc[:topN].rename_axis("tag").reset_index(name="frequency")
    )
    fig.add_bar(x=tags_freq_df["tag"], y=tags_freq_df["frequency"], row=3, col=1)

    fig.update_layout(showlegend=False)
    plot_obj_duration_vs_likes.figure = fig

    return plot_obj_duration_vs_likes


def get_empty_video_df():
    return pd.DataFrame(
        columns=[
            "kind",
            "etag",
            "id",
            "snippet.publishedAt",
            "snippet.channelId",
            "snippet.title",
            "snippet.description",
            "snippet.thumbnails.default.url",
            "snippet.thumbnails.default.width",
            "snippet.thumbnails.default.height",
            "snippet.thumbnails.medium.url",
            "snippet.thumbnails.medium.width",
            "snippet.thumbnails.medium.height",
            "snippet.thumbnails.high.url",
            "snippet.thumbnails.high.width",
            "snippet.thumbnails.high.height",
            "snippet.thumbnails.standard.url",
            "snippet.thumbnails.standard.width",
            "snippet.thumbnails.standard.height",
            "snippet.thumbnails.maxres.url",
            "snippet.thumbnails.maxres.width",
            "snippet.thumbnails.maxres.height",
            "snippet.channelTitle",
            "snippet.tags",
            "snippet.categoryId",
            "snippet.liveBroadcastContent",
            "snippet.localized.title",
            "snippet.localized.description",
            "snippet.defaultAudioLanguage",
            "contentDetails.duration",
            "contentDetails.dimension",
            "contentDetails.definition",
            "contentDetails.caption",
            "contentDetails.licensedContent",
            "contentDetails.regionRestriction.blocked",
            "contentDetails.projection",
            "statistics.viewCount",
            "statistics.likeCount",
            "statistics.favoriteCount",
            "statistics.commentCount",
            "snippet.defaultLanguage",
            "contentDetails.regionRestriction.allowed",
        ]
    )
