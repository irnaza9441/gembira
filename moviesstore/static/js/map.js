mapboxgl.accessToken = 'pk.eyJ1IjoicmFodWxhbmQiLCJhIjoiY2x5eWY1bDc2MDBvYzNwcWxwN25zYjZxZyJ9.u4Gp49BkIh-jZI9P99V7dg';

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [-84.3963, 33.7756],
    zoom: 13,
});

map.addControl(new mapboxgl.NavigationControl());
let currentMarkers = [];

function clearMarkers() {
    currentMarkers.forEach(marker => marker.remove());
    currentMarkers = [];
}

function renderPlaces(featureCollection) {
    const list = document.getElementById('list');
    list.innerHTML = '';

    clearMarkers();

    if (!featureCollection || !featureCollection.features || featureCollection.features.length === 0) {
        document.getElementById('status').innerHTML = 'No results found';
        return;
    }

    featureCollection.features.forEach((feat) => {
        const props = feat.properties;
        const coords = feat.geometry.coordinates; // [lng, lat]

        // Sidebar entry
        const div = document.createElement('div');
        div.className = 'place';

        const title = document.createElement('div');
        title.className = 'place-title';
        title.textContent = props.name || 'Unnamed bakery';

        const addr = document.createElement('div');
        addr.className = 'small';
        addr.textContent = props.full_address || props.address || '';

        div.appendChild(title);
        div.appendChild(addr);
        list.appendChild(div);

        const marker = new mapboxgl.Marker()
            .setLngLat(coords)
            .setPopup(new mapboxgl.Popup().setHTML(
                `<strong>${title.textContent}</strong><br>${addr.textContent}`
            ))
            .addTo(map);
        currentMarkers.push(marker);

        marker.getElement().addEventListener('click', () => {
            map.flyTo({center: coords, zoom: 15});
        });
    });

    if (featureCollection.features.length > 0) {
        const bounds = new mapboxgl.LngLatBounds();
        featureCollection.features.forEach(f => bounds.extend(f.geometry.coordinates));
        map.fitBounds(bounds, { padding: 50 });
    }
}

async function searchBakeriesAround(lng, lat) {
    const status = document.getElementById('status');
    status.textContent = 'Searching for bakeries...';

    const params = new URLSearchParams({
        q: 'bakery',
        types: 'poi',
        poi_category: 'bakery',
        limit: '10',
        proximity: `${lng},${lat}`,
        access_token: mapboxgl.accessToken
    });

    const url = `https://api.mapbox.com/search/searchbox/v1/forward?${params.toString()}`;

    try {
        const resp = await fetch(url);
        if (!resp.ok) {
            const text = await resp.text();
            throw new Error(`Search API error ${resp.status}: ${text}`);
        }
        const data = await resp.json();
        renderPlaces(data);
        status.textContent = `Found ${data.features?.length || 0} bakeries nearby.`;
    } catch (err) {
        console.error(err);
        status.textContent = 'Error querying Mapbox Search.';
    }
}

function useBrowserLocation() {
    const status = document.getElementById('status');
    if (!navigator.geolocation) {
        status.textContent = 'Geolocation not supported.';
        return;
    }

    status.textContent = 'Getting your location...';

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;

            map.setCenter([lng, lat]);
            map.setZoom(14);

            searchBakeriesAround(lng, lat);
        },
        (err) => {
            console.error(err);
            status.textContent = 'Could not get location. Using map center instead.';
            const center = map.getCenter();
            searchBakeriesAround(center.lng, center.lat);
        }
    );
}

// Wire up button and initial search
document.getElementById('locate').addEventListener('click', () => {
    useBrowserLocation();
});

map.on('load', () => {
    const center = map.getCenter();
    searchBakeriesAround(center.lng, center.lat);
});

