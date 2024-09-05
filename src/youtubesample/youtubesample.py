import json
import os

import isodate
import pandas as pd
import plotly.express as px
import requests
from googleapiclient.discovery import build
from plotly.subplots import make_subplots

from simian.gui import Form, component, utils

if __name__ == "__main__":
    from simian.local import Uiformio

    Uiformio("youtubesample", window_title="YouTube Trending Videos")


def gui_init(meta_data: dict) -> dict:
    # Get application data containing secrets and configurables (local mode).
    get_application_data(meta_data)

    # Create the form and load the json builder into it.
    Form.componentInitializer(app_pic_hello_world=init_app_toplevel_pic)
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
        "showChanged": True,
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

    # Remove the "form has changes badge".
    payload["pristine"] = True

    return callback(meta_data, payload)


def process(meta_data: dict, payload: dict) -> dict:
    nr_to_display = 12

    # Fetch trending YouTube videos, based on user selection.
    selection_country, _ = utils.getSubmissionData(payload, "selection_country")
    selection_category, _ = utils.getSubmissionData(payload, "selection_category")
    plot_obj_views_vs_likes, _ = utils.getSubmissionData(payload, "plot_views_vs_likes")
    plot_obj_duration_vs_likes, _ = utils.getSubmissionData(payload, "plot_duration_vs_likes")
    plot_obj_comments_vs_likes, _ = utils.getSubmissionData(payload, "plot_comments_vs_likes")
    plot_obj_duration_vs_comments, _ = utils.getSubmissionData(payload, "plot_duration_vs_comments")

    # Initialize YouTube connection and create results plots.
    youtube = build(
        "youtube", "v3", developerKey=meta_data["application_data"]["youtube_developer_key"]
    )

    try:
        video_df = extractYouTubeData(youtube, selection_country, selection_category)
    except:
        video_df = get_empty_video_df()

    if len(video_df) > 0:
        video_df_top = video_df.iloc[:nr_to_display]
        video_title_array = [video for video in video_df_top["snippet.title"]]
        video_link_array = [
            "https://www.youtube.com/watch?v=" + video for video in video_df_top["id"]
        ]
        video_thumbnail_array = [
            "https://img.youtube.com/vi/" + video + "/mqdefault.jpg" for video in video_df_top["id"]
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
                    '<div class="py-3 mx-auto"><iframe'
                    + ' loading="lazy"'
                    + f' src="{item[0]}"'
                    + f' title="{item[1]}"'
                    + ' loading="lazy"'
                    + ' allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"'
                    + " allowFullScreen></iframe></div>"
                    for item in zip(video_embed_array, video_title_array)
                ]
            )
            + "</div>"
        )

    else:
        no_results_html = '<p class="my-5 py-5 text-danger text-center">No results for this category in this region.</p>'
        full_references_html = no_results_html
        full_embed_html = no_results_html

    video_df["contentDetails.duration"] = video_df["contentDetails.duration"].astype(str)
    video_df["duration"] = video_df["contentDetails.duration"].apply(
        lambda x: isodate.parse_duration(x).total_seconds()
    )

    payload, _ = utils.setSubmissionData(
        payload,
        "plot_views_vs_likes",
        plotVs(
            plot_obj_views_vs_likes,
            video_df,
            "statistics.viewCount",
            "statistics.likeCount",
            "Views vs. likes",
            "Views",
            "Likes",
        ),
    )

    payload, _ = utils.setSubmissionData(
        payload,
        "plot_duration_vs_likes",
        plotVs(
            plot_obj_duration_vs_likes,
            video_df,
            "duration",
            "statistics.likeCount",
            "Duration vs. likes",
            "Duration",
            "Likes",
        ),
    )

    payload, _ = utils.setSubmissionData(
        payload,
        "plot_comments_vs_likes",
        plotVs(
            plot_obj_comments_vs_likes,
            video_df,
            "statistics.commentCount",
            "statistics.likeCount",
            "Comments vs. likes",
            "Comments",
            "Likes",
        ),
    )

    payload, _ = utils.setSubmissionData(
        payload,
        "plot_duration_vs_comments",
        plotVs(
            plot_obj_duration_vs_comments,
            video_df,
            "duration",
            "statistics.commentCount",
            "Duration vs. comments",
            "Comments",
            "Duration",
        ),
    )

    payload, _ = utils.setSubmissionData(payload, "video_list", full_references_html)
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


def plotVs(plotObj, video_df, x_field, y_field, title, x_label, y_label):
    # Hide selection tools and plotly logo
    plotObj.config = dict(modeBarButtonsToRemove=["select", "lasso", "logo"])

    plotObj.figure = px.scatter(
        video_df,
        x=x_field,
        y=y_field,
        title=title,
        labels={
            x_field: x_label,
            y_field: y_label,
        },
        hover_name="snippet.title",
    )

    plotObj.figure.update_traces(
        mode="markers",
        # hovertext="snippet.title",
        # hoverinfo="text",
    )

    plotObj.figure.update_layout(margin={"r": 50, "t": 50, "l": 50, "b": 50}, showlegend=False)

    return plotObj


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
