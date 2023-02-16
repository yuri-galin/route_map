let routeSocket;
let myMap = null;
let citiesSet = false;
let routesSet = false;
let routeCount = 0;
let selectedCity = null;
let cities = {}; // storing information about city bounds
const mapRoutes = {}; // storing Yandex routes objects to be able to delete them

const citySelect = document.getElementById("city-select");
citySelect.onchange = setCity;

function setCity(e){
    selectedCity = e.target.value;
    if (myMap){
        // changing the viewpoint of the map
        city = cities[selectedCity];
        myMap.setBounds([
            [city.lower_bound_lat, city.lower_bound_lon],
            [city.upper_bound_lat, city.upper_bound_lon]
        ]);
        // getting the routes only of they haven't been previously fetched
        if (!cities[selectedCity].fetched){
            getRoutes(selectedCity);
        }
    }
}

function connectToWebSocket(){
    routeSocket = new WebSocket("ws://" + window.location.host + "/ws/routes/");

    routeSocket.onopen = () => {
      console.log("WebSocket opened");

      // we're checking if cities and routes are set because we don't want
      // to fetch them again in case websocket fails and reconnects
      if (!citiesSet){
        routeSocket.send(JSON.stringify({
            "command": "get_cities"
        }));
      } else if (!routesSet){
        getRoutes(selectedCity);
      }
    };

    routeSocket.onmessage = (e) => {
      const message = JSON.parse(e.data);
      window[message.call](message.data);
    };

    routeSocket.onerror = (e) => {
      console.log("WebSocket error. Uh-oh.");
      console.log(e.message);
    };

    routeSocket.onclose = () => {
      console.log("WebSocket closed, let's reopen");
      connectToWebSocket();
    };
}

connectToWebSocket();


ymaps.ready(init);
function init(){
    myMap = new ymaps.Map("map", {
        center: [55.76, 37.64],
        zoom: 12
    });
}

function setCities(data){
    cities = data;
    selectedCity = Object.keys(cities)[0];
    citiesSet = true;
    getRoutes(selectedCity);
}

function getRoutes(city){
    routeSocket.send(JSON.stringify({
        "city": city,
        "command": "get_routes"
    }));
}

function setRoutes(data){
    for (let id in data.routes){
        const route = data.routes[id];
        addRouteToMap(route);
    }
    routesSet = true;
    cities[data.city].fetched = true;
}

function disableRoute(id){
    if ("id" in mapRoutes){
        const multiRoute = mapRoutes[id];
        myMap.geoObjects.remove(multiRoute);
    }
}

function enableRoute(route){
    addRouteToMap(route);
}

function reloadRoute(route){
    if ("id" in mapRoutes){
        disableRoute(route.id);
        addRouteToMap(route);
    }
}

// I wanted to generate colors that look distinguishable to the human eye,
// found this solution on StackOverflow
function selectUniqueColor(n) {
    const rgb = [0, 0, 0];

    for (let i = 0; i < 24; i++) {
        rgb[i%3] <<= 1;
        rgb[i%3] |= n & 0x01;
        n >>= 1;
    }

    return "#" + rgb.reduce((a, c) => (c > 0x0f ? c.toString(16) : "0" + c.toString(16)) + a, "");
}

function addRouteToMap(route){
    routeCount += 1;
    const color = selectUniqueColor(routeCount);
    let viaIndexes = [];
    for (let i = 1; i < route.stops.length - 1; i++){
        viaIndexes.push(i);
    }

    var multiRoute = new ymaps.multiRouter.MultiRoute(
      {
        referencePoints: route.stops,
        params: (
            {
                routingMode: "auto",
                results: 1,
                viaIndexes: viaIndexes
            }
        )
      },
      {
        boundsAutoApply: false,
        routeActiveStrokeColor: color,
        // start point
        wayPointStartIconFillColor: color,
        wayPointStartIconColor: "white",
        // finish point
        wayPointFinishIconFillColor: color,
        wayPointFinishIconColor: "white",
        // via-points
        viaPointIconRadius: 5,
        viaPointIconFillColor: color,
        viaPointActiveIconFillColor: color,
      }
    );

    myMap.geoObjects.add(multiRoute);
    mapRoutes[route.id] = multiRoute;
}