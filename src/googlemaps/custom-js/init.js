if (!(typeof google === 'object' && typeof google.maps === 'object')) {
  (g=>{var h,a,k,p="The Google Maps JavaScript API",c="google",l="importLibrary",q="__ib__",m=document,b=window;b=b[c]||(b[c]={});var d=b.maps||(b.maps={}),r=new Set,e=new URLSearchParams,u=()=>h||(h=new Promise(async(f,n)=>{await (a=m.createElement("script"));e.set("libraries",[...r]+"");for(k in g)e.set(k.replace(/[A-Z]/g,t=>"_"+t[0].toLowerCase()),g[k]);e.set("callback",c+".maps."+q);a.src=`https://maps.${c}apis.com/maps/api/js?`+e;d[q]=f;a.onerror=()=>h=n(Error(p+" could not load."));a.nonce=m.querySelector("script[nonce]")?.nonce||"";m.head.append(a)}));d[l]?console.warn(p+" only loads once. Ignoring:",g):d[l]=(f,...n)=>r.add(f)&&u().then(()=>d[l](f,...n))})({
    v: "weekly",
    key: "[google_maps_frontend_api_key]"
  });
}

var map;
var markerObjects = [];

// initMap is now async
async function initMap(form) {
    if (!form.form) return;
    // Request libraries when needed, not in the script tag.
    const { Map } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    latlng = await new google.maps.LatLng(getSimianComponent("centers").getValue()[getSimianComponent("latlng").getValue()]);

    map = await new Map(document.getElementsByName("[google_maps_map_name]")[0], {
        center: latlng,
        zoom: 8,
        mapId: "[google_maps_map_mapid]"
    });

    markers = FormioUtils.getComponent(form.form.components, "markers").defaultValue;

    if (markers) {
        markers.forEach(function (item) {
            markerObjects.push(
                new AdvancedMarkerElement({
                    position: item,
                    map: map // put the handle of your map here
                })
            );
        });
    }

    google.maps.event.addListener(map, "click", addMarker);
}

subscribeInitFcn(initMap);

async function addMarker( event ) {
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    if (getSimianComponent("add_marker_on_click_toggle").getValue()) {
        markerObjects.push(
            new AdvancedMarkerElement({
                position: event.latLng,
                map: map // put the handle of your map here
            })
        );

        markersComponent = getSimianComponent("markers");
        markersComponent.getValue().push(event.latLng);
        markersComponent.triggerChange(); // array or object value by reference
    }
}

function updateMap(latlng) {
    latlng = getSimianComponent("centers").getValue()[getSimianComponent("latlng").getValue()];
    if (latlng && map) {
        map.setCenter(latlng);
    }
}

function purgeMarker() {
    if (markerObjects.length) {
        removedMarkerObject = markerObjects.pop();
        removedMarkerObject.setMap(null);
    }
}

function getSimianComponent(key) {
    return window.angularComponentReference.component.currentForm.getComponent(key);
}

function getSimianData() {
    return window.angularComponentReference.component.currentForm.submission.data;
}

function subscribeInitFcn(customFcn) {
    out = window.angularComponentReference.component;
    if (out) {
        if (!out.refreshForm.observers.find((x) => x.destination.partialObserver.next.toString() === '(form) => initFcn(form, customFcn)')) {
            out.refreshForm.subscribe((form) => initFcn(form, customFcn));
        }
    } else {
        requestAnimationFrame(() => subscribeInitFcn())
    }
}
 
function initFcn(form, customFcn) {
    if (form.form) {
        customFcn(form);
    }
}

function stringifyMarkers(markers) {
    out = "";
    if (markers) {
        markers.forEach(marker => out += JSON.stringify(marker) + "\n");
    }
    return out;
}