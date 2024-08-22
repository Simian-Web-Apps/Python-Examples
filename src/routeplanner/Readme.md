# EV Truck route "planner"
this example uses openstreetmap.org, openrouteservice.org, and here.com for maps, routes, and destinations.

    * [Create a (free) https://openrouteservice.org/ account](https://openrouteservice.org/dev/#/signup) and get your API key (token).
    * [Create a (free) https://here.com/ account](https://platform.here.com/portal/) and get your API key. 
    * Copy the `local_application_data.json.sample` to `local_application_data.json`.
    * Store your `openstreetroute.org` API key (token) as `open_route_service_api_key` in `local_application_data.json`.
    * Store your `here.com` API key as `here_api_key` in `local_application_data.json`.
    * Optionally set `here_frontend_autocomplete_delay` (max 1) and `here_backend_lookup_interval` values to higher values to reduce request rates to here.com.


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