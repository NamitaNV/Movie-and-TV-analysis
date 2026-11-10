"""Build a packaged Tableau workbook (.twbx) for the Netflix catalogue.

The script writes a Tableau workbook (XML) plus the CSV data into a
``tableau/`` folder, then zips everything into a portable ``.twbx`` that can be
opened in Tableau Desktop or Tableau Public.

Run with:  python build_tableau_workbook.py
"""

import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

BASE_DIR = Path(__file__).parent
TABLEAU_DIR = BASE_DIR / "tableau"
DATA_DIR = TABLEAU_DIR / "Data" / "Netflix"
WORKBOOK_NAME = "Netflix_Catalogue_Dashboard"
WORKBOOK_PATH = TABLEAU_DIR / f"{WORKBOOK_NAME}.twb"
PACKAGED_PATH = TABLEAU_DIR / f"{WORKBOOK_NAME}.twbx"

VERSION = "18.1"
SOURCE_BUILD = "2021.4.0 (20214.21.1103.1414)"

TITLES = "federated.netflixtitles"
GENRES = "federated.netflixgenres"
COUNTRIES = "federated.netflixcountries"

DS_CAPTIONS = {
    TITLES: "Netflix Titles",
    GENRES: "Netflix Genres",
    COUNTRIES: "Netflix Countries",
}

NO_RECORDS = "Number of Records"

# name: (datatype, role, type, caption)
SCHEMAS = {
    TITLES: {
        "show_id": ("string", "dimension", "nominal", "Show ID"),
        "type": ("string", "dimension", "nominal", None),
        "title": ("string", "dimension", "nominal", None),
        "director": ("string", "dimension", "nominal", None),
        "country": ("string", "dimension", "nominal", None),
        "release_year": ("integer", "dimension", "quantitative", "Release Year"),
        "rating": ("string", "dimension", "nominal", None),
        "duration_value": ("integer", "measure", "quantitative", "Duration"),
        "duration_unit": ("string", "dimension", "nominal", "Duration Unit"),
        "listed_in": ("string", "dimension", "nominal", "Listed In"),
        "primary_genre": ("string", "dimension", "nominal", "Primary Genre"),
        "primary_country": ("string", "dimension", "nominal", "Primary Country"),
        "added_year": ("integer", "dimension", "quantitative", "Added Year"),
        "added_month": ("string", "dimension", "nominal", "Added Month"),
        "decade": ("integer", "dimension", "ordinal", "Decade"),
        "num_cast": ("integer", "measure", "quantitative", "Cast Size"),
        "num_genres": ("integer", "measure", "quantitative", "Genre Count"),
        "content_age": ("integer", "measure", "quantitative", "Content Age"),
    },
    GENRES: {
        "show_id": ("string", "dimension", "nominal", "Show ID"),
        "type": ("string", "dimension", "nominal", None),
        "release_year": ("integer", "dimension", "quantitative", "Release Year"),
        "added_year": ("integer", "dimension", "quantitative", "Added Year"),
        "genre": ("string", "dimension", "nominal", None),
    },
    COUNTRIES: {
        "show_id": ("string", "dimension", "nominal", "Show ID"),
        "type": ("string", "dimension", "nominal", None),
        "release_year": ("integer", "dimension", "quantitative", "Release Year"),
        "added_year": ("integer", "dimension", "quantitative", "Added Year"),
        "country": ("string", "dimension", "nominal", None),
    },
}

PREFIX = {
    "None": "none",
    "Sum": "sum",
    "Count": "cnt",
    "CountD": "ctd",
    "Median": "med",
    "Avg": "avg",
    "Min": "min",
    "Max": "max",
}

SUFFIX = {"nominal": "nk", "ordinal": "ok", "quantitative": "qk"}

REMOTE_TYPE = {
    "string": (129, "WSTR"),
    "integer": (20, "I8"),
    "real": (5, "R8"),
    "date": (7, "DATE"),
    "datetime": (135, "DT"),
}


def ref(ds, instance):
    return f"[{ds}].{instance}"


def column_xml(name, datatype, role, col_type, caption=None):
    cap = f" caption='{escape(caption)}'" if caption else ""
    return (
        f"<column{cap} datatype='{datatype}' name='[{name}]' "
        f"role='{role}' type='{col_type}' />"
    )


def column_definition(ds, name):
    if name == NO_RECORDS:
        return (
            "<column datatype='integer' name='[Number of Records]' role='measure' "
            "type='quantitative' user:auto-column='numrec'>"
            "<calculation class='tableau' formula='1' />"
            "</column>"
        )
    datatype, role, col_type, caption = SCHEMAS[ds][name]
    return column_xml(name, datatype, role, col_type, caption)


def instance_name(name, derivation="None", inst_type=None):
    if inst_type is None:
        inst_type = SCHEMAS.get(TITLES, {}).get(name, ("string", "dimension", "nominal", None))[2]
    return f"[{PREFIX[derivation]}:{name}:{SUFFIX[inst_type]}]"


def instance_for(ds, name, derivation="None", inst_type=None):
    if inst_type is None:
        if name == NO_RECORDS:
            inst_type = "quantitative"
        else:
            inst_type = SCHEMAS[ds][name][2]
    return instance_name(name, derivation, inst_type)


def dependency_block(ds, used):
    """Build a <datasource-dependencies> block for the fields a sheet uses.

    ``used`` is a list of (column name, derivation, instance type).
    """
    seen_columns = []
    instances = []
    for name, derivation, inst_type in used:
        if name not in seen_columns:
            seen_columns.append(name)
        instance = instance_for(ds, name, derivation, inst_type)
        if instance not in [i[0] for i in instances]:
            instances.append((instance, name, derivation, inst_type))

    lines = [f"<datasource-dependencies datasource='{ds}'>"]
    for name in seen_columns:
        lines.append("  " + column_definition(ds, name))
    for instance, name, derivation, inst_type in instances:
        lines.append(
            f"  <column-instance column='[{name}]' derivation='{derivation}' "
            f"name='{instance}' pivot='key' type='{inst_type}' />"
        )
    lines.append("</datasource-dependencies>")
    return "\n".join(lines)


def filter_member(ds, name, member, inst_type="nominal"):
    instance = instance_for(ds, name, "None", inst_type)
    return (
        f"<filter class='categorical' column='{ref(ds, instance)}'>"
        f"<groupfilter function='member' level='{instance}' "
        f"member='&quot;{escape(member)}&quot;' user:ui-domain='relevant' "
        f"user:ui-enumeration='inclusive' user:ui-marker='enumerate' />"
        f"</filter>"
    )


def filter_top(ds, name, measure_name, top=10):
    instance = instance_for(ds, name)
    return (
        f"<filter class='categorical' column='{ref(ds, instance)}'>"
        f"<groupfilter count='{top}' end='top' function='end' units='records' "
        f"user:ui-marker='end' user:ui-top-by-field='true'>"
        f"<groupfilter direction='DESC' expression='SUM([{measure_name}])' "
        f"function='order' user:ui-marker='order'>"
        f"<groupfilter function='level-members' level='{instance}' "
        f"user:ui-enumeration='all' user:ui-marker='enumerate' />"
        f"</groupfilter></groupfilter></filter>"
    )


def slices_xml(ds, fields):
    if not fields:
        return ""
    columns = "".join(f"<column>{ref(ds, instance_for(ds, name, derivation, inst_type))}</column>"
                      for name, derivation, inst_type in fields)
    return f"<slices>{columns}</slices>"


def sort_xml(ds, dimension, measure, direction="DESC", shelf="rows"):
    return (
        "<shelf-sorts>"
        f"<shelf-sort-v2 dimension-to-sort='{ref(ds, instance_for(ds, dimension))}' "
        f"direction='{direction}' is-on-innermost-dimension='true' "
        f"measure-to-sort-by='{ref(ds, instance_for(ds, measure, 'Sum'))}' "
        f"shelf='{shelf}' />"
        "</shelf-sorts>"
    )


def palette_xml(ds):
    field = ref(ds, instance_for(ds, "type"))
    return f"""<style-rule element='mark'>
        <encoding attr='color' field='{field}' type='palette'>
          <map to='#E50914'><bucket>&quot;Movie&quot;</bucket></map>
          <map to='#00A8E1'><bucket>&quot;TV Show&quot;</bucket></map>
        </encoding>
      </style-rule>"""


def mark_style(color=None, show_labels=False, font_size=None):
    formats = []
    if color:
        formats.append(f"<format attr='color' value='{color}' />")
    if show_labels:
        formats.append("<format attr='mark-labels-show' value='true' />")
        formats.append("<format attr='mark-labels-cull' value='true' />")
    if font_size:
        formats.append(f"<format attr='font-size' value='{font_size}' />")
    if not formats:
        return ""
    return "<style-rule element='mark'>" + "".join(formats) + "</style-rule>"


def worksheet(
    name,
    title,
    ds,
    mark,
    rows,
    cols,
    used,
    encodings=(),
    filters=(),
    filter_fields=(),
    sorts="",
    style="",
    pane_style="",
):
    enc = "".join(
        f"<{channel} column='{ref(ds, instance_for(ds, field, derivation, inst_type))}' />"
        for channel, field, derivation, inst_type in encodings
    )
    encoding_block = f"<encodings>{enc}</encodings>" if enc else ""

    filter_block = "".join(filters)

    view = [
        "<view>",
        f"<datasources><datasource caption='{DS_CAPTIONS[ds]}' name='{ds}' /></datasources>",
        dependency_block(ds, [(u[0], u[1], u[2]) for u in used]),
        filter_block,
        sorts,
        slices_xml(ds, filter_fields),
        "<aggregation value='true' />",
        "</view>",
    ]

    rows_xml = f"<rows>{ref(ds, instance_for(ds, *rows))}</rows>" if rows else "<rows />"
    cols_xml = f"<cols>{ref(ds, instance_for(ds, *cols))}</cols>" if cols else "<cols />"
    pane_style_block = f"<style>{pane_style}</style>" if pane_style else ""

    return f"""
    <worksheet name='{escape(name)}'>
      <layout-options>
        <title>
          <formatted-text>
            <run bold='true' fontsize='11'>{escape(title)}</run>
          </formatted-text>
        </title>
      </layout-options>
      <table>
        {''.join(view)}
        <style>{style}</style>
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view><breakdown value='auto' /></view>
            <mark class='{mark}' />
            {encoding_block}
            {pane_style_block}
          </pane>
        </panes>
        {rows_xml}
        {cols_xml}
      </table>
      <simple-id uuid='{{{uuid.uuid4()}}}' />
    </worksheet>"""


def datasource_xml(ds, filename):
    schema = SCHEMAS[ds]
    caption = DS_CAPTIONS[ds]
    conn_name = f"textscan.{ds.split('.')[-1]}"

    relation_columns = "\n".join(
        f"<column datatype='{datatype}' name='{escape(name)}' ordinal='{i}' />"
        for i, (name, (datatype, _, _, _)) in enumerate(schema.items())
    )

    metadata = [
        f"""
          <metadata-record class='capability'>
            <remote-name />
            <remote-type>0</remote-type>
            <parent-name>[{escape(filename)}]</parent-name>
            <remote-alias />
            <aggregation>Count</aggregation>
            <contains-null>true</contains-null>
            <attributes>
              <attribute datatype='string' name='character-set'>&quot;UTF-8&quot;</attribute>
              <attribute datatype='string' name='collation'>&quot;en_US&quot;</attribute>
              <attribute datatype='string' name='field-delimiter'>&quot;,&quot;</attribute>
              <attribute datatype='string' name='header-row'>&quot;true&quot;</attribute>
              <attribute datatype='string' name='locale'>&quot;en_US&quot;</attribute>
              <attribute datatype='string' name='single-char'>&quot;&quot;</attribute>
            </attributes>
          </metadata-record>"""
    ]
    for i, (name, (datatype, _, _, _)) in enumerate(schema.items()):
        remote_type, debug = REMOTE_TYPE[datatype]
        aggregation = "Count" if datatype == "string" else "Sum"
        metadata.append(
            f"""
          <metadata-record class='column'>
            <remote-name>{escape(name)}</remote-name>
            <remote-type>{remote_type}</remote-type>
            <local-name>[{escape(name)}]</local-name>
            <parent-name>[{escape(filename)}]</parent-name>
            <remote-alias>{escape(name)}</remote-alias>
            <ordinal>{i}</ordinal>
            <local-type>{datatype}</local-type>
            <aggregation>{aggregation}</aggregation>
            <contains-null>true</contains-null>
            <attributes>
              <attribute datatype='string' name='DebugRemoteType'>&quot;{debug}&quot;</attribute>
            </attributes>
          </metadata-record>"""
        )

    relation_attrs = (
        f"connection='{conn_name}' name='{escape(filename)}' "
        f"table='[{escape(filename.replace('.csv', '#csv'))}]' type='table'"
    )
    relation_body = f"""<columns character-set='UTF-8' header='yes' locale='en_US' separator=','>
            {relation_columns}
          </columns>"""

    columns = "\n".join(
        column_definition(ds, name) for name in schema
    ) + "\n" + column_definition(ds, NO_RECORDS)

    return f"""
    <datasource caption='{escape(caption)}' inline='true' name='{ds}' version='{VERSION}'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='{escape(filename)}' name='{conn_name}'>
            <connection class='textscan' directory='Data/Netflix' filename='{escape(filename)}' password='' server='' />
          </named-connection>
        </named-connections>
        <relation {relation_attrs}>
          {relation_body}
        </relation>
        <metadata-records>{''.join(metadata)}
        </metadata-records>
      </connection>
      {columns}
      <style />
    </datasource>"""


# ---------------------------------------------------------------------------
# Worksheet definitions
# ---------------------------------------------------------------------------

def build_worksheets():
    sheets = []

    # KPI cards ------------------------------------------------------------
    count_used = [(NO_RECORDS, "Sum", "quantitative")]
    count_enc = [("text", NO_RECORDS, "Sum", "quantitative")]

    sheets.append(
        worksheet(
            "KPI Total Titles", "TOTAL TITLES", TITLES, "Text", None, None,
            count_used, count_enc, pane_style=mark_style(font_size="30"),
        )
    )
    sheets.append(
        worksheet(
            "KPI Movies", "MOVIES", TITLES, "Text", None, None,
            count_used + [("type", "None", "nominal")], count_enc,
            filters=[filter_member(TITLES, "type", "Movie")],
            filter_fields=[("type", "None", "nominal")],
            pane_style=mark_style(font_size="30"),
        )
    )
    sheets.append(
        worksheet(
            "KPI TV Shows", "TV SHOWS", TITLES, "Text", None, None,
            count_used + [("type", "None", "nominal")], count_enc,
            filters=[filter_member(TITLES, "type", "TV Show")],
            filter_fields=[("type", "None", "nominal")],
            pane_style=mark_style(font_size="30"),
        )
    )
    sheets.append(
        worksheet(
            "KPI Movie Runtime", "MEDIAN RUNTIME (MIN)", TITLES, "Text", None, None,
            [("duration_value", "Median", "quantitative"), ("type", "None", "nominal")],
            [("text", "duration_value", "Median", "quantitative")],
            filters=[filter_member(TITLES, "type", "Movie")],
            filter_fields=[("type", "None", "nominal")],
            pane_style=mark_style(font_size="30"),
        )
    )
    sheets.append(
        worksheet(
            "KPI Countries", "COUNTRIES", COUNTRIES, "Text", None, None,
            [("country", "CountD", "quantitative")],
            [("text", "country", "CountD", "quantitative")],
            pane_style=mark_style(font_size="30"),
        )
    )

    # Trend ----------------------------------------------------------------
    sheets.append(
        worksheet(
            "Titles Added per Year", "TITLES ADDED PER YEAR", TITLES, "Line",
            ("Number of Records", "Sum", "quantitative"),
            ("added_year", "None", "quantitative"),
            count_used + [("added_year", "None", "quantitative")],
            style=mark_style(color="#E50914"),
        )
    )

    # Content mix pie ------------------------------------------------------
    sheets.append(
        worksheet(
            "Movies vs TV Shows", "MOVIES VS TV SHOWS", TITLES, "Pie", None, None,
            count_used + [("type", "None", "nominal")],
            [("color", "type", "None", "nominal"),
             ("wedge-size", NO_RECORDS, "Sum", "quantitative")],
            style=palette_xml(TITLES),
            pane_style=mark_style(show_labels=True),
        )
    )

    # Top 10 countries -----------------------------------------------------
    sheets.append(
        worksheet(
            "Top 10 Countries", "TOP 10 COUNTRIES", COUNTRIES, "Bar",
            ("country", "None", "nominal"),
            ("Number of Records", "Sum", "quantitative"),
            count_used + [("country", "None", "nominal")],
            [("text", NO_RECORDS, "Sum", "quantitative")],
            filters=[filter_top(COUNTRIES, "country", NO_RECORDS, 10)],
            filter_fields=[("country", "None", "nominal")],
            sorts=sort_xml(COUNTRIES, "country", NO_RECORDS),
            style=mark_style(color="#E50914"),
            pane_style=mark_style(show_labels=True),
        )
    )

    # Top 10 genres --------------------------------------------------------
    sheets.append(
        worksheet(
            "Top 10 Genres", "TOP 10 GENRES", GENRES, "Bar",
            ("genre", "None", "nominal"),
            ("Number of Records", "Sum", "quantitative"),
            count_used + [("genre", "None", "nominal")],
            [("text", NO_RECORDS, "Sum", "quantitative")],
            filters=[filter_top(GENRES, "genre", NO_RECORDS, 10)],
            filter_fields=[("genre", "None", "nominal")],
            sorts=sort_xml(GENRES, "genre", NO_RECORDS),
            style=mark_style(color="#E50914"),
            pane_style=mark_style(show_labels=True),
        )
    )

    # Ratings --------------------------------------------------------------
    sheets.append(
        worksheet(
            "Ratings Mix", "RATINGS", TITLES, "Bar",
            ("rating", "None", "nominal"),
            ("Number of Records", "Sum", "quantitative"),
            count_used + [("rating", "None", "nominal")],
            [("text", NO_RECORDS, "Sum", "quantitative")],
            sorts=sort_xml(TITLES, "rating", NO_RECORDS),
            style=mark_style(color="#E50914"),
            pane_style=mark_style(show_labels=True),
        )
    )

    # Decade mix -----------------------------------------------------------
    sheets.append(
        worksheet(
            "Titles by Decade", "TITLES BY DECADE", TITLES, "Bar",
            ("Number of Records", "Sum", "quantitative"),
            ("decade", "None", "ordinal"),
            count_used + [("decade", "None", "ordinal"), ("type", "None", "nominal")],
            [("color", "type", "None", "nominal")],
            style=palette_xml(TITLES),
        )
    )

    return "\n".join(sheets)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def zone_style(margin=6, bg="#FFFFFF", border="#E8E8E8"):
    return f"""
        <zone-style>
          <format attr='background-color' value='{bg}' />
          <format attr='border-color' value='{border}' />
          <format attr='border-style' value='solid' />
          <format attr='border-width' value='1' />
          <format attr='margin' value='{margin}' />
        </zone-style>"""


def sheet_zone(zid, name, x, y, w, h):
    return (
        f"<zone h='{h}' id='{zid}' name='{escape(name)}' w='{w}' x='{x}' y='{y}'>"
        f"{zone_style()}</zone>"
    )


def text_zone(zid, x, y, w, h, text, size, color="#141414", bold=False,
              align="0", bg=None, margin=0):
    weight = " bold='true'" if bold else ""
    zone_style_xml = ""
    formats = []
    if bg:
        formats.append(f"<format attr='background-color' value='{bg}' />")
    if margin:
        formats.append(f"<format attr='margin' value='{margin}' />")
    if formats:
        zone_style_xml = "<zone-style>" + "".join(formats) + "</zone-style>"
    return (
        f"<zone h='{h}' id='{zid}' type-v2='text' w='{w}' x='{x}' y='{y}'>"
        f"<formatted-text><run{weight} fontcolor='{color}' fontsize='{size}' "
        f"fontalignment='{align}'>{escape(text)}</run></formatted-text>"
        f"{zone_style_xml}</zone>"
    )


def build_dashboard():
    zones = []
    zid = 1

    # Header
    zones.append(text_zone(
        zid, 0, 0, 65000, 7800, "NETFLIX CATALOGUE ANALYSIS", 24,
        color="#FFFFFF", bold=True, bg="#141414", margin=20,
    ))
    zid += 1
    zones.append(text_zone(
        zid, 65000, 0, 35000, 7800,
        "8,807 titles  |  1925-2021  |  Kaggle snapshot, Sept 2021", 10,
        color="#B3B3B3", align="2", bg="#141414", margin=20,
    ))
    zid += 1

    # KPI row
    kpis = [
        ("KPI Total Titles", 800),
        ("KPI Movies", 20640),
        ("KPI TV Shows", 40480),
        ("KPI Movie Runtime", 60320),
        ("KPI Countries", 80160),
    ]
    for name, x in kpis:
        zones.append(sheet_zone(zid, name, x, 8600, 19040, 14300))
        zid += 1

    # Main charts - row 1
    zones.append(sheet_zone(zid, "Titles Added per Year", 800, 23700, 45000, 36000))
    zid += 1
    zones.append(sheet_zone(zid, "Movies vs TV Shows", 46400, 23700, 22000, 36000))
    zid += 1
    zones.append(sheet_zone(zid, "Top 10 Countries", 69000, 23700, 30200, 36000))
    zid += 1

    # Main charts - row 2
    zones.append(sheet_zone(zid, "Top 10 Genres", 800, 60500, 30000, 36500))
    zid += 1
    zones.append(sheet_zone(zid, "Ratings Mix", 31400, 60500, 30000, 36500))
    zid += 1
    zones.append(sheet_zone(zid, "Titles by Decade", 62000, 60500, 37200, 36500))
    zid += 1

    # Footer
    zones.append(text_zone(
        zid, 800, 97600, 98400, 1600,
        "Source: Netflix Movies and TV Shows (Kaggle, Shivam Bansal)  |  "
        "Built with Tableau", 8, color="#8C8C8C", align="1",
    ))

    zone_xml = "\n".join(zones)
    return f"""
  <dashboards>
    <dashboard name='Netflix Catalogue Dashboard'>
      <style />
      <size maxheight='900' maxwidth='1400' minheight='900' minwidth='1400' />
      <zones>
        <zone h='100000' id='0' type-v2='layout-basic' w='100000' x='0' y='0'>
          {zone_xml}
          <zone-style>
            <format attr='background-color' value='#F4F4F4' />
            <format attr='margin' value='0' />
          </zone-style>
        </zone>
      </zones>
      <simple-id uuid='{{{uuid.uuid4()}}}' />
    </dashboard>
  </dashboards>"""


def window_cards():
    return """
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'><card type='columns' /></strip>
          <strip size='2147483647'><card type='rows' /></strip>
          <strip size='31'><card type='title' /></strip>
        </edge>
      </cards>"""


def build_windows():
    sheet_names = [
        "KPI Total Titles", "KPI Movies", "KPI TV Shows", "KPI Movie Runtime",
        "KPI Countries", "Titles Added per Year", "Movies vs TV Shows",
        "Top 10 Countries", "Top 10 Genres", "Ratings Mix", "Titles by Decade",
    ]
    windows = []
    for name in sheet_names:
        windows.append(
            f"""
    <window class='worksheet' name='{escape(name)}'>
      {window_cards()}
      <simple-id uuid='{{{uuid.uuid4()}}}' />
    </window>"""
        )

    viewpoints = "\n".join(
        f"<viewpoint name='{escape(name)}'><zoom type='entire-view' /></viewpoint>"
        for name in sheet_names
    )
    windows.append(
        f"""
    <window class='dashboard' maximized='true' name='Netflix Catalogue Dashboard'>
      <viewpoints>
        {viewpoints}
      </viewpoints>
      <active id='0' />
      <simple-id uuid='{{{uuid.uuid4()}}}' />
    </window>"""
    )
    return "<windows source-height='30'>" + "".join(windows) + "</windows>"


def build_workbook():
    datasource_xmls = "\n".join(
        datasource_xml(ds, filename)
        for ds, filename in [
            (TITLES, "titles.csv"),
            (GENRES, "genres.csv"),
            (COUNTRIES, "countries.csv"),
        ]
    )

    return f"""<?xml version='1.0' encoding='utf-8' ?>

<!-- build {SOURCE_BUILD} -->
<workbook original-version='{VERSION}' source-build='{SOURCE_BUILD}' source-platform='win' version='{VERSION}' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <SheetIdentifierTracking />
    <SortTagCleanup />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
  <datasources>
{datasource_xmls}
  </datasources>
  <worksheets>
{build_worksheets()}
  </worksheets>
{build_dashboard()}
{build_windows()}
  <thumbnails />
  <explain-data enabled-for-viewer='false' extreme-values-enabled-for-all='false'>
    <explanation-types />
  </explain-data>
</workbook>
"""


def main():
    if not (DATA_DIR / "titles.csv").exists():
        raise SystemExit("Missing CSVs. Run: python prepare_tableau_data.py")

    workbook_xml = build_workbook()
    WORKBOOK_PATH.write_text(workbook_xml, encoding="utf-8")
    print(f"workbook -> {WORKBOOK_PATH}")

    with zipfile.ZipFile(PACKAGED_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WORKBOOK_PATH, f"{WORKBOOK_NAME}.twb")
        for csv_name in ["titles.csv", "genres.csv", "countries.csv"]:
            zf.write(DATA_DIR / csv_name, f"Data/Netflix/{csv_name}")
    print(f"packaged -> {PACKAGED_PATH}  ({PACKAGED_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
