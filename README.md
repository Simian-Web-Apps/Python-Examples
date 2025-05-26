# Simian Examples for Python

Simian GUI offers a low-code solution for creating web apps using Python, MATLAB, and Julia, expediting development and ensuring a smooth journey from concept to production. By leveraging accessible web technologies such as form.io, DataTables, and Plotly, it facilitates the creation of apps for complex tasks like calculations and data visualization.
 
With an intuitive two-pillar approach to app development, Simian GUI simplifies the process of building and adding interaction, offering options like an app builder or low-code programmatic approach. It also provides utilities to easily manage web events and backend functionalities, eliminating the need for tailored API definitions.
 
During runtime, the Simian frontend renders the defined web app directly from Python, MATLAB, or Julia code in the web browser, without requiring front-end developer involvement. This streamlined workflow allows users to craft and deploy apps locally with ease, making Simian GUI a comprehensive solution for web app development from inception to production.

## Getting Started

### Dependencies

* Simian GUI runs and is tested on Python `3.8` to `3.12`.

### Installing

* Simian GUI consists of four packages that can be installed via pip:

    * `simian-gui` contains the core functionality, with optional dependency on Redis

    * `simian-local` allows running locally using pywebview

    * `simian-examples` contains the the same examples available in the `simian/examples` folder in this repository

    * `simian-builder` contains the builder

    ```
    pip install --extra-index-url https://pypi.simiansuite.com/simple/ simian-gui[redis] simian-local simian-examples simian-builder
    ```

### Running Examples

#### Online

Example web apps are deployed at the [Simian Web Apps Demo portal](https://demo01.simiansuite.com/)

#### Local

For running apps locally, we assume that the `src` folder is on the Python path. The most straightforward way to achieve this, is to make it the current folder before running Python.

* **All components**: this example contains all components that can be used in Simian GUI.
    ```
    python -m run simian.examples.all_components
    ```

* **Ball Thrower**: this example uses the `scipy.integrate.solve_ivp` solver to calculate the trajectory of a ball being thrown. Hence, the `scipy` package must be installed as a dependency.
    * Install additional dependencies
        ```
        pip install scipy
        ```
    * Then start the app using the `run` module
        ```
        python -m run simian.examples.ballthrower
        ```
    See [Example](https://doc.simiansuite.com/simian-gui/example.html) in the documentation for more details.

* **Plot types**: this example showcases the Plotly integration in Simian GUI.
    ```
    python -m run simian.examples.plottypes
    ```

* **Hypotheek planner**: this example is an (indicative) mortgage planner. Available in Dutch only.
    ```
    python -m run hypoplanner.hypo_planner
    ```

* **Bird swarm**: this example uses a particle swarm optimization to simulate bird feeding behavior.
    * Install additional dependencies
        ```
        pip install cython setuptools matplotlib scipy noise
        ```
    * Use Cython to build the `.pyx` modules
        ```
        cd birdswarm
        python setup.py build_ext --inplace
        cd ..
        ```
    * Then start the app using the `run` module
        ```
        python -m run birdswarm.bird_swarm
        ```

* **Route planner**: this example uses openstreetmap.org, openrouteservice.org, and here.com for maps, routes, and destinations.
    * Create a (free) [openrouteservice.org](https://openrouteservice.org/dev/#/signup) account and get your API key (token).
    * Create a (free) [here.com](https://platform.here.com/portal/) account and get your API key(s).  
    During development the same api key can be used for both front- and backend.  
    When deployed on a public server it is wise to restrict the frontend api key to a specific domain such that it can not be abused by others. The backend api key is used from the server only so there less need to restrict its usage.
    * Copy the `local_application_data.json.sample` to `local_application_data.json`.
    * Store your `openstreetroute.org` API key (token) as `open_route_service_api_key` in `local_application_data.json`.
    * Store your `here.com` API key(s) as respectively `here_frontend_api_key` and `here_backend_api_key` in `local_application_data.json`.
    * Optionally set `here_frontend_autocomplete_delay_ms` (max 1000) and `here_backend_lookup_interval_ms` values to higher values in milliseconds to reduce request rates to here.com.
    * Then start the app using the `run` module
        ```
        python -m run routeplanner.route_planner
        ```

    ***Note***:  
	This app uses images & services from:
	* `https://downloads.simiansuite.com` (GUI/browser frontend)  
	* `https://api.openrouteservice.org` (Python backend)
	* `https://autocomplete.search.hereapi.com` (GUI/browser frontend)
	* `https://lookup.search.hereapi.com` (Python backend)

    Make sure these are reachable.

* **Trending on YouTube**: Find out what's trending in your favourite countries.
    * Install additional dependencies
        ```
        pip install google-api-python-client deep-translator pycountry isodate
        ```
    * Obtain a (free) API key from [Google Cloud](https://console.cloud.google.com/apis/library).
    * Copy the `local_application_data.json.sample` to `local_application_data.json`.
    * Store your API key as `youtube_developer_key` in `local_application_data.json`.
    * Then start the app using the `run` module
        ```
        python -m run youtubesample.youtubesample
        ```

* **Hello world with coffee**: Find out what happened on a particular date.
    * Install additional dependencies
        ```
        pip install scikit-image json2html
        ```
    * Obtain a (free) API key from [Wikimedia](https://api.wikimedia.org/wiki/Getting_started_with_Wikimedia_APIs).
    * Copy the `local_application_data.json.sample` to `local_application_data.json`.
    * Store your user agent as `wikimedia_service_user_agent` and API key as `wikimedia_service_api_key` in `local_application_data.json`.
    * Then start the app using the `run` module
        ```
        python -m run python -m run helloworldwithcoffee.hello_world_with_coffee
        ```

* **Image processing**: apps for modifying and generating images. [All apps](./src/imageprocessing/README.md) allow for downloading the created figure. When an input image is used, this can be uploaded.
    * Install additional dependencies
        ```
        pip install -r imageprocessing/requirements.txt
        ```
    * Optionally, install image generation dependencies for inpainting and image generation actions.
        ```
        pip install imageprocessing/requirements-imagegen.txt
        ```
    * Then start the apps using the `run` module
        ```
        python -m run imageprocessing.image_processor
        python -m run imageprocessing.image_inpainter
        python -m run imageprocessing.image_generator
        ```
        
* **PDF merger**: app for merging (parts of) uploaded PDF files.
    * Install additional dependencies
        ```
        pip install -r pdfprocessor/requirements.txt
        ```
    * Then start the apps using the `run` module
        ```
        python -m run pdfprocessor.prd_processor
        ```

### Running Builder

* Start the Builder by running
    ```
    python -m simian.builder
    ```

* Fill in the fields in the *Options* section and click *Create module* to create the module.

* Add, remove and modify components and click *Save JSON* to save your changes.

* Click *Preview application* to run your Simian Web App.

* See [Simian Form Builder](https://doc.simiansuite.com/simian-gui/builder.html) for more information.

### Building an App

* A Simian Web App is a module containing two functions: `gui_init` to define the form and `gui_event` to handle events.
    ```python
    from simian.gui import Form, component, utils
    
    def gui_init(meta_data: dict) -> dict:
        # Create a form and set a logo and title.
        form = Form()

        payload = {
            "form": form,
            "navbar": {
                "logo": "favicon.ico",
                "title": "Hello, World!",
            },
        }

        return payload

    def gui_event(meta_data: dict, payload: dict) -> dict:
        # Process the events.
        return payload
    ```

* See the [Hello world](https://doc.simiansuite.com/simian-gui/setup/hello.html) example in the documentation for how to program a Simian Web App.

## Help

In case of issues or questions, please see the [issue tracker](https://github.com/Simian-Web-Apps/Issue-Tracker).

## Contributing

Any contributions to the examples are greatly appreciated.

If you have an example that you would like to share, please fork the repo and create a pull request. Don't forget to give the project a star! Thanks again!

1. Fork the Project

2. Create your Feature Branch (git checkout -b feature/AmazingExample)

3. Commit your Changes (git commit -m 'Add some Amazing Example')

4. Push to the Branch (git push origin feature/AmazingExample)

5. Open a Pull Request

## Authors

* [MonkeyProof Solutions](https://monkeyproofsolutions.nl)

## Version History

See the [Release notes](https://doc.simiansuite.com/simian-gui/release_notes.html) in the documentation for the version history.

## License

The Simian Examples are licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

* [Form.io](https://form.io)
* [Plotly](https://plotly.com)
* [DataTables](https://datatables.net/)
* [Pywebview](https://pywebview.flowrl.com/)
