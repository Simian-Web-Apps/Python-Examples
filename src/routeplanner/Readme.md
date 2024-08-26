# EV Truck route "planner"
This example uses `openstreetmap.org`, `openrouteservice.org`, and `here.com` for maps, routes, and destinations.

* Create a (free) [openrouteservice.org](https://openrouteservice.org/dev/#/signup) account and get your API key (token).
* Create a (free) [here.com](https://platform.here.com/portal/) account and get your API key(s).  
  During development the same api key can be used for both front- and backend.  
  When deployed on a public server it is wise to restrict the frontend api key to a specific domain such that it can not be abused by others. The backend api key is used from the server only so there less need to restrict its usage.
* Copy the `local_application_data.json.sample` to `local_application_data.json`.
* Store your `openstreetroute.org` API key (token) as `open_route_service_api_key` in `local_application_data.json`.
* Store your `here.com` API key(s) as respectively `here_frontend_api_key` and `here_backend_api_key` in `local_application_data.json`.
* Optionally set `here_frontend_autocomplete_delay_ms` (max 1000) and `here_backend_lookup_interval_ms` values to higher values in milliseconds to reduce request rates to here.com.


* Run the application:  
```
python -m run routeplanner.route_planner.py
```

***Note***:  
This app uses images & services from:
* `https://downloads.simiansuite.com` (GUI/browser frontend)  
* `https://api.openrouteservice.org` (Python backend)
* `https://autocomplete.search.hereapi.com` (GUI/browser frontend)
* `https://lookup.search.hereapi.com` (Python backend)

Make sure these are reachable.