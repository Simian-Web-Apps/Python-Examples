function fillTreemap(data, year) {
    console.log("Year: " + year);

    var idx = data.years.map((y, i) => y == year ? i : false).filter(Boolean);

    var countries = idx.map((i) => data.countries[i]);
    var parents = idx.map((i) => data.parents[i]);
    var ids = idx.map((i) => data.ids[i]);
    var lifeExp = idx.map((i) => data.lifeExp[i]);
    var pop = idx.map((i) => data.pop[i]);

    var layout = {
        coloraxis: {
            colorbar: {
                title: {
                    "text": "lifeExp"
                }
            },
            colorscale: getColorScale(),
            cmid: lifeExp.slice(-1)[0]
        },
        legend: {
            tracegroupgap: 0
        },
        margin: {
            t: 50,
            l: 25,
            r: 25,
            b: 25
        }
    };

    var trace = {
        branchvalues: "total",
        domain: {
            x: [0.0, 1.0],
            y: [0.0, 1.0]
        },
        hovertemplate: "Country: %{label}<br>Population: %{value}<br>Continent: %{parent}<br>Life expectancy: %{color}",
        ids: ids,
        labels: countries,
        marker: {
            coloraxis: "coloraxis",
            colors: lifeExp
        },
        name: "",
        parents: parents,
        values: pop,
        type: "treemap"
    };

    return {
        layout: layout,
        data: [trace]
    };
}

function getColorScale() {
    var cmap = [
        [103, 0, 31],
        [178, 24, 43],
        [214, 96, 77],
        [244, 165, 130],
        [253, 219, 199],
        [247, 247, 247],
        [209, 229, 240],
        [146, 197, 222],
        [67, 147, 195],
        [33, 102, 172],
        [5, 48, 97],
    ];

    var nCmap = cmap.length - 1;

    return cmap.map((c, i) => [1.0 * i / nCmap, 'rgb(' + c[0] + ', ' + c[1] + ', ' + c[2] + ')']);
}
