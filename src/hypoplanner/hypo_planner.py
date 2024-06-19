"""Hypotheek planner module.

MonkeyProof Solutions demo application, for Simian exploration purposes.

Copyright 2020-2024 MonkeyProof Solutions BV.
"""

import copy
import datetime
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from simian.gui import Form, component, utils
from simian.local import Uiformio

if __name__ == "__main__":
    print(os.getcwd())
    Uiformio("hypo_planner", window_title="MonkeyProof Solutions")


def gui_init(meta_data: dict) -> dict:
    # Create the form and load the json builder into it.
    Form.componentInitializer(app_pic_hypo_planner=init_app_toplevel_pic)
    Form.componentInitializer(periode_selector=init_periode_selector)
    Form.componentInitializer(hypo_verloop_table_report=init_hypo_verloop_table_report)
    Form.componentInitializer(plot_verloop_lasten=init_plot_verloop_lasten)
    Form.componentInitializer(plot_verloop_hypotheek=init_plot_verloop_hypotheek)
    Form.componentInitializer(plot_kostenverdeling=init_plot_kostenverdeling)
    Form.componentInitializer(plot_lastenvergelijk=init_plot_lastenvergelijk)
    form = Form(from_file=__file__)

    return {"form": form, "navbar": {"title": "Hypotheek Planner [DEMO PURPOSES]"}}


def init_periode_selector(comp: component.Slider):
    # Define a TriggerHappy event, to immediately process period selections.
    comp.properties = {"triggerHappy": True, "debounceTime": 1000}
    comp.properties = {"triggerHappy": "update_period_selection"}


def init_hypo_verloop_table():
    # Initialize results table.
    today = datetime.date.today()
    looptijd_maanden = 12 * 30
    perioden_n = np.arange(0, looptijd_maanden, 1)
    perioden_m = pd.bdate_range(start=today, periods=looptijd_maanden, freq="MS").to_pydatetime()
    perioden_s = [dt.strftime("%Y-%m") for dt in perioden_m]
    zeros_looptijd = np.zeros(len(perioden_n))

    hypo_verloop_table = pd.DataFrame(
        list(
            zip(
                perioden_n,
                perioden_s,
                zeros_looptijd,
                zeros_looptijd,
                zeros_looptijd,
                zeros_looptijd,
                zeros_looptijd,
                zeros_looptijd,
                zeros_looptijd,
                zeros_looptijd,
            )
        ),
        columns=["id", "datum", "saldo", "woz", "rente", "aflossing", "vt", "ew", "bruto", "netto"],
    )

    return hypo_verloop_table


def init_plot_verloop_lasten(comp: component.Plotly):
    # Initialize maandlasten plot.
    hypo_verloop_table = init_hypo_verloop_table()
    comp.figure = px.scatter(
        hypo_verloop_table,
        x="datum",
        y=["rente", "aflossing", "bruto", "netto"],
        title="Maandlasten",
    )
    comp.figure.update_layout(yaxis_tickprefix="€", yaxis_title="Euro")


def init_plot_verloop_hypotheek(comp: component.Plotly):
    # Initialize hypotheek-verloop plot (saldi).
    hypo_verloop_table = init_hypo_verloop_table()
    comp.figure = px.scatter(
        hypo_verloop_table,
        x="datum",
        y=["rente", "aflossing", "bruto", "netto"],
        title="Uitstaand saldo en WOZ waarde",
    )
    comp.figure.update_layout(yaxis_tickprefix="€", yaxis_title="Euro")


def init_plot_kostenverdeling(comp: component.Plotly):
    # Initialize kosten-breakdown plot.
    comp.figure = make_subplots(rows=1, cols=1, specs=[[{"type": "domain"}]])
    comp.figure.add_trace(
        go.Sunburst(
            labels=[
                "Verdeling",
                "Rente",
                "Aflossing",
                "Fiscaal",
                "Aflosvrij",
                "Lineair ",
                "Annuitair ",
                "Lineair",
                "Annuitair",
                "VT [ontvangen]",
                "EW forfait [betalen]",
            ],
            parents=[
                "",
                "Verdeling",
                "Verdeling",
                "Verdeling",
                "Rente",
                "Rente",
                "Rente",
                "Aflossing",
                "Aflossing",
                "Fiscaal",
                "Fiscaal",
            ],
            values=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ),
        1,
        1,
    )
    comp.figure.update_layout(yaxis_tickprefix="€", title_text="Maandlasten verdeling")


def init_plot_lastenvergelijk(comp: component.Plotly):
    # Initialize scenario-vergelijk plot.
    hypo_verloop_table = init_hypo_verloop_table()
    comp.figure = px.scatter(
        hypo_verloop_table,
        x="datum",
        y=["rente", "aflossing", "bruto", "netto"],
        title="Voorstel vergelijker",
    )
    comp.figure.update_layout(yaxis_tickprefix="€", yaxis_title="Euro")


def init_hypo_verloop_table_report(comp: component.DataTables):
    # initialize reporting table.
    today = datetime.date.today()
    columnNames = [
        "Index",
        "Datum",
        "Saldo",
        "WOZ waarde",
        "Rente",
        "Aflossing",
        "VT",
        "EW",
        "Brutolast",
        "Nettolast",
    ]
    columnIDs = ["id", "datum", "saldo", "woz", "rente", "aflossing", "vt", "ew", "bruto", "netto"]
    comp.setColumns(columnNames, columnIDs)
    comp.defaultValue = [
        {
            "id": 0,
            "datum": today.month,
            "saldo": 0,
            "woz": 0,
            "rente": 0,
            "aflossing": 0,
            "vt": 0,
            "ew": 0,
            "bruto": 0,
            "netto": 0,
        },
    ]


def init_app_toplevel_pic(comp: component.HtmlElement):
    # Voeg depictie met titel toe in de linker bovenhoek.
    comp.setLocalImage(
        os.path.join(os.path.dirname(__file__), "app_pic.png"), scale_to_parent_width=True
    )


def gui_event(meta_data: dict, payload: dict) -> dict:
    # Application event handler.
    Form.eventHandler(calculate_button=calc_update, update_period_selection=calc_update)
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def calc_update(meta_data: dict, payload: dict) -> dict:
    # Update both numerical and graph results.
    # 1. Start updating the tool:
    # 1A. Fetch output variables.
    hold_netto_maandlast, _ = utils.getSubmissionData(payload, key="hold_netto_maandlast")
    hold_netto_maandlast = np.array(hold_netto_maandlast)

    # 1B. Fetch graph objects.
    plot_verloop_lasten, _ = utils.getSubmissionData(payload, "plot_verloop_lasten")
    plot_verloop_hypotheek, _ = utils.getSubmissionData(payload, "plot_verloop_hypotheek")
    plot_kostenverdeling, _ = utils.getSubmissionData(payload, "plot_kostenverdeling")
    plot_lastenvergelijk, _ = utils.getSubmissionData(payload, "plot_lastenvergelijk")

    # 1C. Fetch the input variables.
    koopsom, _ = utils.getSubmissionData(payload, key="koopsom")
    woz_waarde, _ = utils.getSubmissionData(payload, key="woz_waarde")
    kosten_advies, _ = utils.getSubmissionData(payload, key="kosten_advies")
    kosten_hypotheekakte, _ = utils.getSubmissionData(payload, key="kosten_hypotheekakte")
    kosten_keuring, _ = utils.getSubmissionData(payload, key="kosten_keuring")
    eigen_middelen, _ = utils.getSubmissionData(payload, key="eigen_middelen")
    looptijd_jaren, _ = utils.getSubmissionData(payload, key="looptijd_jaren")
    looptijd_fiscaal_aftrekbaar, _ = utils.getSubmissionData(
        payload, key="looptijd_fiscaal_aftrekbaar"
    )
    period_select, _ = utils.getSubmissionData(payload, key="periode_selector")
    toggle_nhg, _ = utils.getSubmissionData(payload, key="toggle_nhg")
    toggle_inflatie_woz, _ = utils.getSubmissionData(payload, key="toggle_inflatie_woz")
    perc_hypotheekrente, _ = utils.getSubmissionData(payload, key="perc_hypotheekrente")
    perc_aflosvorm_annuitair, _ = utils.getSubmissionData(payload, key="perc_aflosvorm_annuitair")
    perc_aflosvrij, _ = utils.getSubmissionData(payload, key="perc_aflosvrij")
    perc_overdrachtsbelasting, _ = utils.getSubmissionData(payload, key="perc_overdrachtsbelasting")
    perc_forfait, _ = utils.getSubmissionData(payload, key="perc_forfait")
    perc_voorlopigeteruggaaf, _ = utils.getSubmissionData(payload, key="perc_voorlopigeteruggaaf")
    perc_tarief_nhg, _ = utils.getSubmissionData(payload, key="perc_tarief_nhg")
    perc_inflatie_woz, _ = utils.getSubmissionData(payload, key="perc_inflatie_woz")

    looptijd_max_jaren = 30
    looptijd_maanden = 12 * looptijd_jaren

    # Corrigeer periode-selector voor user-gedefinieerde looptijd.
    if period_select > looptijd_maanden:
        # De selector overschrijdt de looptijd - breng terug naar laatste maand.
        period_select = looptijd_maanden
        payload, _ = utils.setSubmissionData(payload, "periode_selector", period_select)

    period_select -= 1

    # 2. Bepaal benodigde hypotheek:
    # 2A. Bepaal overdrachtsbelasting en daarna kosten koper.
    overdrachtsbelasting = perc_overdrachtsbelasting / 100 * koopsom
    kosten_koper = kosten_advies + kosten_hypotheekakte + kosten_keuring + overdrachtsbelasting

    # 2B. Bepaal hoogte financiering en kosten NHG.
    hypotheek_ex_nhg = koopsom + kosten_koper - eigen_middelen

    if toggle_nhg == True:
        hypo_benodigd = hypotheek_ex_nhg / (1 - perc_tarief_nhg / 100)
        kosten_nhg = perc_tarief_nhg / 100 * hypo_benodigd
    else:
        hypo_benodigd = hypotheek_ex_nhg
        kosten_nhg = 0

    hypo_aflossend = (1 - perc_aflosvrij / 100) * hypo_benodigd
    hypo_niet_aflossend = hypo_benodigd - hypo_aflossend

    # 3. Bepaal hypotheekverloop en maandlasten:
    # 3A. Bepaal hypotheekrente op maandbasis.
    # im : interest per month.
    today = datetime.date.today()
    perioden_n = np.arange(0, looptijd_maanden, 1)
    perioden_m = pd.bdate_range(start=today, periods=looptijd_maanden, freq="MS").to_pydatetime()
    perioden_s = [dt.strftime("%Y-%m") for dt in perioden_m]
    im = perc_hypotheekrente / 100 / 12

    # 3B. Bereken saldi en lasten.
    zeros_perioden_n = np.zeros(len(perioden_n))
    ones_perioden_n = np.ones(len(perioden_n))
    hypo_saldo_aflossend_ann, hypo_saldo_aflossend_lin, aflossing_annuitair, aflossing_lineair = [
        zeros_perioden_n for _ in range(4)
    ]

    if perc_aflosvorm_annuitair == 100:
        # Zuiver annuitair.
        # Bepaal de mensualiteit (mst) en het saldo over de perioden.
        mst = hypo_aflossend * im / (1 - (1 + im) ** -looptijd_maanden)
        hypo_saldo_aflossend_ann = ((1 + im) ** perioden_n) * hypo_aflossend + mst / im * (
            1 - (1 + im) ** perioden_n
        )
        hypo_saldo_aflossend = hypo_saldo_aflossend_ann
        aflossing_annuitair = mst - (im * hypo_saldo_aflossend_ann)

    elif perc_aflosvorm_annuitair == 0:
        # Zuiver lineair.
        aflos_lin_maand = hypo_aflossend / looptijd_maanden
        hypo_saldo_aflossend_lin = hypo_aflossend - (aflos_lin_maand * perioden_n)
        hypo_saldo_aflossend = hypo_saldo_aflossend_ann + hypo_saldo_aflossend_lin
        aflossing_lineair = aflos_lin_maand * ones_perioden_n

    else:
        # Mix lineair en annuitair.
        hypo_aflossend_ann = perc_aflosvorm_annuitair / 100 * hypo_aflossend
        hypo_aflossend_lin = hypo_aflossend - hypo_aflossend_ann

        # Annuitair: mensualiteit, saldo en aflossing.
        mst = hypo_aflossend_ann * im / (1 - (1 + im) ** -looptijd_maanden)
        hypo_saldo_aflossend_ann = ((1 + im) ** perioden_n) * hypo_aflossend_ann + mst / im * (
            1 - (1 + im) ** perioden_n
        )
        aflossing_annuitair = mst - (im * hypo_saldo_aflossend_ann)

        # Lineair: aflossing en saldo.
        aflos_lin_maand = hypo_aflossend_lin / looptijd_maanden
        hypo_saldo_aflossend_lin = hypo_aflossend_lin - (aflos_lin_maand * perioden_n)
        aflossing_lineair = aflos_lin_maand * ones_perioden_n

        # Totaal aflossend saldo en aflossing.
        hypo_saldo_aflossend = hypo_saldo_aflossend_ann + hypo_saldo_aflossend_lin

    saldo = hypo_saldo_aflossend + hypo_niet_aflossend
    rente = saldo * im

    # 3C. Berekening fiscaliteiten: voorlopige teruggaaf en eigenwoningforfait, op basis van aflossende hypotheekdelen.
    # Bepaal WOZ waarde over de looptijd: constant, of gecorrigeerd voor (instelbare) inflatie.
    if toggle_inflatie_woz == True:
        woz_waarde_array = woz_waarde * (1 + perc_inflatie_woz / 100 / 12) ** perioden_n
    else:
        woz_waarde_array = woz_waarde * ones_perioden_n

    # Bereken de voorlopige teruggaaf en eigenwoningforfait (ex aftrek Hillen) op maandbasis.
    fiscaal_vt = (
        perc_voorlopigeteruggaaf
        / 100
        * hypo_saldo_aflossend
        * im
        * (perioden_n <= 12 * looptijd_fiscaal_aftrekbaar)
    )
    fiscaal_ew = woz_waarde_array * perc_forfait / 100 / 12 * perc_voorlopigeteruggaaf / 100

    # Wordt minder rente betaald dan het eigenwoningforfait dat bijgeteld moet bijtellen? Dan bestaat recht op
    # een aftrek vanwege geen of een kleine eigenwoningschuld (wet Hillen).
    toepassen_wet_hillen = fiscaal_ew > fiscaal_vt

    # Uitwerking afbouw Wet Hillen [2024 - 2048].
    hillen_init_year = 2024
    hillen_end_year = 2048
    aftrek_hillen_init_year = 80
    aftrek_hillen_end_year = 0
    afbouw_per_jaar = (aftrek_hillen_init_year - aftrek_hillen_end_year) / (
        hillen_end_year - hillen_init_year
    )
    aftrek_curr_year = aftrek_hillen_init_year - (today.year - hillen_init_year) * afbouw_per_jaar
    perioden_array_max_looptijd = np.arange(0, 12 * (looptijd_max_jaren + 1), 1)
    afbouw_hillen_array_max_looptijd = np.maximum(
        aftrek_curr_year - np.floor(perioden_array_max_looptijd / 12) * afbouw_per_jaar,
        np.zeros(len(perioden_array_max_looptijd)),
    )

    # Afbouw wet Hillen werkt op jaarbasis, van januari tot januari - corrigeer hiervoor.
    offset_huidige_maand = today.month - 1
    afbouw_hillen_array = afbouw_hillen_array_max_looptijd[
        offset_huidige_maand : offset_huidige_maand + looptijd_maanden
    ]

    # Toepassen aftrek voor kleine- of geen eigenwoningschuld (Hillen).
    fiscaal_ew_korting_wet_hillen = fiscaal_ew - np.multiply(
        (fiscaal_ew - fiscaal_vt), afbouw_hillen_array / 100
    )
    fiscaal_ew[toepassen_wet_hillen] = fiscaal_ew_korting_wet_hillen[toepassen_wet_hillen]

    # 3D. Bepaling bruto en netto maandlasten:
    bruto = rente + aflossing_annuitair + aflossing_lineair
    netto = rente + aflossing_annuitair + aflossing_lineair + fiscaal_ew - fiscaal_vt

    # 4. Bepalen numerieke uitkomsten en updaten graphs.
    # 4A. Definitie hypotheek-verloop-tabel.
    hypo_verloop_table = pd.DataFrame(
        list(
            zip(
                perioden_n,
                perioden_s,
                saldo,
                woz_waarde_array,
                rente,
                (aflossing_annuitair + aflossing_lineair),
                fiscaal_vt,
                fiscaal_ew,
                bruto,
                netto,
            )
        ),
        columns=["id", "datum", "saldo", "woz", "rente", "aflossing", "vt", "ew", "bruto", "netto"],
    )

    # 4B. Definitie voorstel-vergelijkings-tabel.
    # Ingepast in de maximale looptijd van 30 jaren.
    perioden_n_max_range = np.arange(0, 12 * looptijd_max_jaren, 1)
    perioden_m_max_range = pd.bdate_range(
        start=today, periods=12 * looptijd_max_jaren, freq="MS"
    ).to_pydatetime()

    if hold_netto_maandlast.size > 1:
        netto_hold = hold_netto_maandlast
    else:
        netto_hold = netto

    netto_base_plot, netto_hold_plot = [np.zeros(12 * looptijd_max_jaren) for _ in range(2)]
    netto_base_plot[0 : len(netto)] = netto
    netto_hold_plot[0 : len(netto_hold)] = netto_hold
    hypo_lasten_vergelijk_table = pd.DataFrame(
        list(zip(perioden_n_max_range, perioden_m_max_range, netto_base_plot, netto_hold_plot)),
        columns=["id", "datum", "huidig", "bewaard"],
    )

    # 4C. Updaten van result graphs:
    # 4C1. Maandlasten plot.
    plot_verloop_lasten.figure = px.scatter(
        hypo_verloop_table,
        x="datum",
        y=["rente", "aflossing", "bruto", "netto"],
        title="Maandlasten",
    )
    plot_verloop_lasten.figure.update_layout(yaxis_tickprefix="€", yaxis_title="Euro")

    # 4C2. Uitstaand saldo plot.
    plot_verloop_hypotheek.figure = px.scatter(
        hypo_verloop_table, x="datum", y=["saldo", "woz"], title="Uitstaand saldo en WOZ waarde"
    )
    plot_verloop_hypotheek.figure.update_layout(yaxis_tickprefix="€", yaxis_title="Euro")

    # 4C3. Sunburst plot van kostenverdeling.
    # Create subplots: use "domain" type for Pie subplot.
    plot_kostenverdeling.figure = make_subplots(rows=1, cols=1, specs=[[{"type": "domain"}]])
    plot_kostenverdeling.figure.add_trace(
        go.Sunburst(
            labels=[
                "Verdeling",
                "Rente",
                "Aflossing",
                "Fiscaal",
                "Aflosvrij",
                "Lineair ",
                "Annuitair ",
                "Lineair",
                "Annuitair",
                "VT [ontvangen]",
                "EW forfait [betalen]",
            ],
            parents=[
                "",
                "Verdeling",
                "Verdeling",
                "Verdeling",
                "Rente",
                "Rente",
                "Rente",
                "Aflossing",
                "Aflossing",
                "Fiscaal",
                "Fiscaal",
            ],
            values=[
                np.round(hypo_verloop_table["bruto"][period_select]),
                np.round(rente[period_select]),
                np.round(aflossing_annuitair[period_select] + aflossing_lineair[period_select]),
                np.round(fiscaal_vt[period_select] + fiscaal_ew[period_select]),
                np.round(hypo_niet_aflossend * im),
                np.round(hypo_saldo_aflossend_lin[period_select] * im),
                np.round(hypo_saldo_aflossend_ann[period_select] * im),
                np.round(aflossing_lineair[period_select]),
                np.round(aflossing_annuitair[period_select]),
                np.round(fiscaal_vt[period_select]),
                np.round(fiscaal_ew[period_select]),
            ],
        ),
        1,
        1,
    )
    plot_kostenverdeling.figure.update_layout(
        yaxis_tickprefix="€", title_text="Maandlasten verdeling"
    )

    # 4C4. Maandlasten vergelijk: vorige status versus huidig.
    plot_lastenvergelijk.figure = px.scatter(
        hypo_lasten_vergelijk_table,
        x="datum",
        y=["bewaard", "huidig"],
        title="Voorstel vergelijker",
    )
    plot_lastenvergelijk.figure.update_layout(yaxis_tickprefix="€", yaxis_title="Euro")

    # 5. Updaten van output sections en weergave prep:
    # 5A. Update plots.
    payload, _ = utils.setSubmissionData(payload, "plot_verloop_lasten", plot_verloop_lasten)
    payload, _ = utils.setSubmissionData(payload, "plot_verloop_hypotheek", plot_verloop_hypotheek)
    payload, _ = utils.setSubmissionData(payload, "plot_kostenverdeling", plot_kostenverdeling)
    payload, _ = utils.setSubmissionData(payload, "plot_lastenvergelijk", plot_lastenvergelijk)

    # 5B. Update numerical outputs. Format and update hypotheek verloop table (reporting).
    payload, _ = utils.setSubmissionData(payload, "hypo_verloop_table", hypo_verloop_table)
    payload, _ = utils.setSubmissionData(payload, "hypo_benodigd", hypo_benodigd)
    payload, _ = utils.setSubmissionData(payload, "overdrachtsbelasting", overdrachtsbelasting)
    payload, _ = utils.setSubmissionData(payload, "kosten_nhg", kosten_nhg)
    payload, _ = utils.setSubmissionData(payload, "brutolast", sum(hypo_verloop_table["bruto"]))
    payload, _ = utils.setSubmissionData(payload, "nettolast", sum(hypo_verloop_table["netto"]))

    # Create monthly report table.
    hypo_verloop_table_report = prep_report_table(
        hypo_verloop_table, ["saldo", "woz", "rente", "aflossing", "vt", "ew", "bruto", "netto"]
    )

    payload, _ = utils.setSubmissionData(
        payload, "hypo_verloop_table_report", hypo_verloop_table_report
    )

    return payload


def prep_report_table(results_table, format_col_names) -> component.DataTables:
    # Prep formatting of reporting table.
    def format_report_col(x):
        return "€ {:.2f}".format(x)

    report_table = copy.deepcopy(results_table)

    # Tweak formatting of selected columns.
    for name in format_col_names:
        report_table[name] = np.round(results_table[name]).apply(format_report_col)

    return report_table


def capture_hold_scenario(meta_data: dict, payload: dict) -> dict:
    # Store the current submission data as "hold scenario".
    # Define and capture "hold" maandlasten array.
    hypo_verloop_table, _ = utils.getSubmissionData(payload, key="hypo_verloop_table")

    if hypo_verloop_table:
        hypo_verloop_table = pd.DataFrame(hypo_verloop_table)
        netto_maandlast = np.array(hypo_verloop_table.netto)

        # Create a deep-copy of the submission data.
        submission_copy = copy.deepcopy(payload["submission"])

        # Propagate and invoke update().
        payload, _ = utils.setSubmissionData(payload, "hold_submission_data", submission_copy)
        payload, _ = utils.setSubmissionData(payload, "hold_netto_maandlast", netto_maandlast)
        payload = calc_update(meta_data, payload)

    return payload


def restore_hold_scenario(meta_data: dict, payload: dict) -> dict:
    # Fetch stored payload and restore hold-scenario data.
    hold_submission_data, _ = utils.getSubmissionData(payload, key="hold_submission_data")

    if hold_submission_data:
        # Call update method and re-invoke hold().
        payload["submission"] = hold_submission_data
        payload = capture_hold_scenario(meta_data, payload)

    return payload


def clear_hold_scenario(meta_data: dict, payload: dict) -> dict:
    # Clear the stored "hold" submission data and netto maandlast. Invoke update().
    hold_submission_data, _ = utils.getSubmissionData(payload, key="hold_submission_data")

    if hold_submission_data:
        payload, _ = utils.setSubmissionData(payload, "hold_submission_data", [])
        payload, _ = utils.setSubmissionData(payload, "hold_netto_maandlast", np.array([]))
        payload = calc_update(meta_data, payload)

    return payload
